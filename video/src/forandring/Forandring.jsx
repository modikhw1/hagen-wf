import { useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Spelare, tidslinje, langd } from './motor/spelare'
import { ORDBOK, NAMN } from './motor/ordbok'
import { ORIGINAL } from './manus/nonna-smakar'
import { GALLERI } from './manus/galleri'
import { sattIhop } from './manus/variant'
import { validera } from './manus/schema'
import { modellFor, placeraAlla, valjKedja, malProfil, beskriv, aktuellaScener } from '../../kalibrering/placering.mjs'
import { forklara } from '../../kalibrering/forklaring.mjs'
import './forandring.css'

// Reglaget i uttrycksrummet: varje scen kan filmas på tusentals sätt (bara kameran varierar,
// innehållet är låst). Uttrycken är mätta med motorns syn, översatta till analysens skala med
// bryggan och placerade på en gemensam skala för hela klippet med rörlighetsmodellen.
// Kedjan är enheten: originalets profil (scenernas steg) flyttas med reglaget och plattas ut mot
// ändarna, och alla scener väljs tillsammans (mål, tröghet, grannar). Med Jev på väljer Jev bland
// de närmaste för de scener som byts, med scenens mål och grannarnas kameror i texten.

const PW = 300
const PH = 534
const STRIP = 780
const TW = 120
const TH = 213
const ORIGINAL_STEG = 5

const fmtOp = o => {
  const m = o.mangd ?? 0
  const unit = ['pan', 'tilt', 'roll', 'arc'].includes(o.op) ? '°' : o.op === 'zoom' ? '×' : o.op === 'tracking' ? '' : ' m'
  const v = o.op === 'zoom' ? (1 + m).toFixed(1) : o.op === 'tracking' ? '' : (m > 0 ? '+' : '') + +m.toFixed(2)
  return `${o.op}${v !== '' ? ' ' + v + unit : ''}`
}
const fargSteg = k => `hsl(${222 - (10 - k) * 2}, ${20 + k * 7}%, ${70 - k * 3.5}%)`

function TransGlyph({ t }) {
  const d = {
    klipp: <path d="M12 3 V21" />,
    mjuk: <><circle cx="9" cy="12" r="6" /><circle cx="15" cy="12" r="6" opacity=".45" /></>,
    whip: <path d="M3 6 L10 12 L3 18 M12 6 L19 12 L12 18" />,
    zoom: <><circle cx="12" cy="12" r="3" /><circle cx="12" cy="12" r="8" opacity=".5" /></>,
  }[t]
  return <svg className={`fv-trans t-${t}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">{d}</svg>
}

// Manus av valda uttryck: scen i filmas med uttrycket val[i] (eller originalets kamera).
// Ett saknat eller trasigt id blir originalets kamera, så att en ofullständig mätning aldrig
// kan krascha spelaren.
// #v: originalet Nonna. #v/<klipp>: ett rekonstruerat klipp (data/rekon/<klipp>/manus.json).
export default function Forandring() {
  const klipp = location.hash.startsWith('#v/') ? decodeURIComponent(location.hash.slice(3)) : null
  const [bas, setBas] = useState(klipp ? null : ORIGINAL)
  const [fel, setFel] = useState(null)
  useEffect(() => {
    if (!klipp) return
    fetch(klipp.endsWith('~modell') ? `/__data/rekon/${klipp.slice(0, -7)}/manus-modell.json` : `/__data/rekon/${klipp}/manus.json`).then(r => (r.ok ? r.json() : Promise.reject(new Error(`ingen rekonstruktion för ${klipp} (npm run rekon -- ${klipp})`)))).then(setBas).catch(e => setFel(e.message))
  }, [klipp])
  if (fel) return <p className="fv-fel" style={{ padding: 24 }}>{fel}</p>
  if (!bas) return <p style={{ padding: 24 }}>läser rekonstruktionen …</p>
  return <Vy bas={bas} klipp={klipp ?? 'nonna-smakar'} />
}

function Vy({ bas, klipp }) {
  const ORIGINAL = bas
  const galleri = location.hash === '#vgalleri'
  const canvas = useRef(null)
  const sp = useRef(null)
  const strip = useRef(null)
  const [data, setData] = useState(null)
  const [val, setVal] = useState(() => ORIGINAL.scener.map(() => 'original'))
  const [beslut, setBeslut] = useState(null)
  const [mal, setMal] = useState(ORIGINAL_STEG)
  const [tolerans, setTolerans] = useState(1)
  const [jevPa, setJevPa] = useState(false)
  const [jevInfo, setJevInfo] = useState(null)
  const manus = useMemo(() => (galleri ? GALLERI : sattIhop(bas, val)), [galleri, val, bas])
  const tl = useMemo(() => tidslinje(manus), [manus])
  const dur = langd(manus)
  const fel = useMemo(() => validera(manus, galleri ? null : ORIGINAL), [manus, galleri])
  const [t, setT] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [thumbs, setThumbs] = useState({})
  const [visaManus, setVisaManus] = useState(false)
  const anrop = useRef(0)

  // Uttrycksrummet, bryggans korrektion, vertikalen, biblioteket och dina bedömningar.
  useEffect(() => {
    if (galleri) return
    const j = u => fetch(u).then(r => (r.ok ? r.json() : null))
    Promise.all([j(`/__data/uttryck/${klipp}.json`), j('/__data/brygga/korrektion.json'), j('/__kalib'), j('/__bedomningar/rorlighet'), j('/__bedomningar/rorlighet-uttryck')]).then(([ut, korr, kal, bed, bu]) => {
      if (!ut || !korr || !kal) { setData({ fel: !ut ? 'Uttrycksrummet är inte mätt ännu (npm run uttrycksrum).' : !korr ? 'Bryggan saknas (npm run brygga).' : 'Kunde inte läsa kalibreringen.' }); return }
      const vertikal = kal.vertikaler.find(v => v.id === 'rorlighet')
      const { mod, namn } = modellFor({ vertikal, korr, bibliotek: kal.items.scen, bedomningar: bed ?? [], uttryck: bu ?? [] })
      const akt = aktuellaScener(ut, ORIGINAL.scener.length, { rekon: typeof ORIGINAL.lokal === 'object' })
      const placerade = placeraAlla(akt.scener, { mod, namn, korr })
      const profil = placerade.map(l => l?.find(x => x.id === 'original')?.steg ?? null)
      const matta = placerade.filter(Boolean).length
      setData({
        placerade, profil, namn, mod, korr, bedomningar: (bed ?? []).filter(b => b.val !== 'hoppa').length, jev: kal.jev,
        antal: ut.scener.map(s => s?.antal ?? 0),
        varning: matta < ORIGINAL.scener.length ? `Uttrycksrummet är mätt för ${matta} av ${ORIGINAL.scener.length} scener${akt.gamla ? ` (${akt.gamla} med en äldre mätning utan täckningskontroll räknas inte)` : ''}; övriga ligger kvar på originalet tills npm run uttrycksrum är klar.` : null,
      })
    })
  }, [galleri, klipp])

  useEffect(() => {
    const s = new Spelare(canvas.current, { bredd: PW, hojd: PH })
    sp.current = s
    window.__spelare = s
    s.onTime = tt => setT(tt)
    s.load(manus)
    s.play()
    return () => s.dispose()
  }, [])

  // Nytt manus: byt i spelaren, gör bilder för nya scener.
  useEffect(() => {
    const s = sp.current
    if (!s) return
    s.load(manus)
    setThumbs(prev => {
      const next = { ...prev }
      manus.scener.forEach((sc, i) => {
        const key = galleri ? `g${i}` : `${val[i]}-${i}`
        if (!next[key]) next[key] = s.thumb(i, sc.tumme ?? sc.tid * 0.55, TW, TH)
      })
      return next
    })
  }, [manus])

  const valt = i => data?.placerade?.[i]?.find(x => x.id === val[i])

  const dra = async nyttMal => {
    setMal(nyttMal)
    if (!data?.placerade) return
    const t0 = performance.now()
    const r = valjKedja({ mal: nyttMal, nu: val, listor: data.placerade, tolerans })
    const forsta = r.map(x => x.val)
    setBeslut(r)
    setVal(forsta)
    setJevInfo({ regelMs: performance.now() - t0 })
    if (!jevPa || !data.jev?.nyckel) return
    // Jev väljer bland kandidaterna för de scener som byts, med grannarnas valda kameror som helhet
    const nr = ++anrop.current
    const P = data.placerade
    const text = (i, id) => { const x = P[i]?.find(y => y.id === id); return x ? beskriv(x) : null }
    const scener = r.filter(x => x.beslut === 'byt').map(x => ({
      i: x.scen,
      mal: x.mal,
      profil: x.profil,
      text: ORIGINAL.scener[x.scen].text,
      original: text(x.scen, 'original'),
      fore: x.scen > 0 ? text(x.scen - 1, forsta[x.scen - 1]) : null,
      efter: x.scen < forsta.length - 1 ? text(x.scen + 1, forsta[x.scen + 1]) : null,
      // kedjans val först, sedan de närmaste scenens mål
      kandidater: [x.kandidater.find(k => k.id === x.val), ...x.kandidater.filter(k => k.id !== x.val)].filter(Boolean).slice(0, 24)
        .map(k => ({ id: k.id, text: `${beskriv(k)} (steg ${k.steg.toFixed(1)})` })),
    }))
    if (!scener.length) return
    const svar = await (await fetch('/__jev-uttryck', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mal: nyttMal, scener }) })).json()
    if (nr !== anrop.current || svar.fel) { if (svar.fel) setJevInfo(j => ({ ...j, fel: svar.fel })); return }
    const nytt = forsta.slice()
    for (const s of svar.svar) nytt[s.scen] = s.val
    setVal(nytt)
    setJevInfo(j => ({ ...j, jevMs: svar.ms, valda: svar.svar.length, tokens: svar.svar.reduce((a, s) => a + (s.tokens ?? 0), 0) }))
  }

  const toggle = () => {
    const s = sp.current
    if (s.playing) { s.pause(); setPlaying(false) } else { s.play(); setPlaying(true) }
  }
  const px = tt => (tt / dur) * STRIP
  const seekFrom = e => {
    const r = strip.current.getBoundingClientRect()
    sp.current.seek(Math.max(0, Math.min(dur - 0.001, ((e.clientX - r.left) / r.width) * dur)))
  }
  const dragging = useRef(false)
  const now = Math.max(0, tl.findIndex(s => t < s.slut))
  const steg = data?.placerade ? val.map((_, i) => valt(i)?.steg ?? 5) : null
  const snitt = steg ? steg.reduce((a, b) => a + b, 0) / steg.length : null
  const pct = v => ((v - 1) / 9) * 100

  return (
    <div className="fv">
      <header className="fv-top">
        <div className="fv-title">
          <b>Videoförändring</b>
          <span className="fv-vert">Rörlighet</span>
        </div>
        <div className="fv-clip">
          <span className="fv-av">{manus.kund[0]}</span>
          <span>{manus.kund} · {manus.namn}</span>
        </div>
        {!galleri && data?.placerade && (
          <span className="fv-info" title={`Egenskaper som placerar uttrycken (giltiga i bryggan): ${data.namn.join(', ')}`}>
            {data.antal.reduce((a, b) => a + b, 0).toLocaleString('sv-SE')} uttryck · {data.bedomningar ? `modell tränad på ${data.bedomningar} bedömningar` : 'ordnade efter definitionen (inga bedömningar ännu)'}
          </span>
        )}
        <div className={`fv-check ${fel.length ? 'bad' : ''}`} title={fel.join('\n') || 'Manuset följer formatet och låsningarna'}>
          {fel.length ? `${fel.length} fel i manus` : 'låst ✓'}
        </div>
      </header>

      <main className="fv-main">
        <div className="fv-player">
          <div className="fv-phone">
            <canvas ref={canvas} style={{ width: PW, height: PH }} />
            <div className="fv-progress">
              {tl.map(s => <i key={s.i}><b style={{ width: `${Math.max(0, Math.min(1, (t - s.start) / s.tid)) * 100}%` }} /></i>)}
            </div>
          </div>
          <div className="fv-controls">
            <button className="fv-play" onClick={toggle} aria-label={playing ? 'Pausa' : 'Spela'}>
              {playing
                ? <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1" /><rect x="14" y="5" width="4" height="14" rx="1" /></svg>
                : <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M7 5 L19 12 L7 19 Z" /></svg>}
            </button>
            <span className="fv-time">{t.toFixed(1)} / {dur.toFixed(1)} s</span>
          </div>
        </div>

        <div className="fv-board">
          {data?.fel && <p className="fv-fel">{data.fel}</p>}
          {data?.varning && <p className="fv-fel">{data.varning}</p>}
          <div
            className="fv-strip" ref={strip} style={{ width: STRIP }}
            onPointerDown={e => { dragging.current = true; e.currentTarget.setPointerCapture(e.pointerId); seekFrom(e) }}
            onPointerMove={e => dragging.current && seekFrom(e)}
            onPointerUp={() => { dragging.current = false }}
          >
            {tl.map(s => {
              const key = galleri ? `g${s.i}` : `${val[s.i]}-${s.i}`
              const b = beslut?.[s.i]
              const st = steg?.[s.i]
              const w = Math.min(TW, px(s.tid) - 10)
              return (
                <div key={s.i} className={`fv-scene ${now === s.i ? 'now' : ''}`} style={{ left: px(s.start), width: px(s.tid) }}>
                  <div className="fv-thumb" style={{ width: w, height: (w * TH) / TW }}>
                    <AnimatePresence initial={false} mode="popLayout">
                      {thumbs[key]
                        ? <motion.img key={key} src={thumbs[key]} alt="" draggable={false}
                            initial={{ opacity: 0, scale: 1.08, filter: 'blur(4px)' }} animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }} exit={{ opacity: 0 }}
                            transition={{ duration: 0.25 }} />
                        : <div className="fv-thumb-empty" />}
                    </AnimatePresence>
                    <span className="fv-num">{s.i + 1}</span>
                    {st != null && (
                      <motion.span key={`b${val[s.i]}`} className={`fv-badge ${b?.beslut === 'byt' ? 'byt' : ''}`} style={{ background: fargSteg(Math.round(st)) }}
                        initial={{ scale: 0.4 }} animate={{ scale: 1 }} title={val[s.i] === 'original' ? 'Originalet' : val[s.i]}>
                        {st.toFixed(1)}
                      </motion.span>
                    )}
                  </div>
                  {s.in && <div className="fv-in"><TransGlyph t={s.in.typ} /></div>}
                </div>
              )
            })}
            <div className="fv-head" style={{ left: px(t) }} />
          </div>

          {!galleri && data?.profil && (() => {
            // Kedjan: originalets profil (streckad), målet för reglagets läge (linje) och valda steg (prickar)
            const KH = 64
            const y = v => KH - 4 - ((v - 1) / 9) * (KH - 8)
            const mitt = tl.map(s => px(s.start + s.tid / 2))
            const prof = data.profil.map(v => v ?? 5)
            const malP = malProfil(prof, mal)
            const linje = vs => vs.map((v, i) => `${i ? 'L' : 'M'}${mitt[i].toFixed(1)} ${y(v).toFixed(1)}`).join(' ')
            return (
              <div className="fv-kedja" style={{ width: STRIP }}>
                <svg width={STRIP} height={KH} aria-label="Kedjans profil">
                  {[1, 5, 10].map(v => <line key={v} className="grid" x1="0" x2={STRIP} y1={y(v)} y2={y(v)} />)}
                  <path className="orig" d={linje(prof)} />
                  <motion.path className="mal" initial={false} d={linje(malP)} animate={{ d: linje(malP) }} transition={{ duration: 0.25 }} />
                  {tl.map(s => {
                    const st = steg?.[s.i]
                    if (st == null || data.profil[s.i] == null) return null
                    return (
                      <g key={s.i}>
                        <motion.line className="avv" initial={false} x1={mitt[s.i]} x2={mitt[s.i]} y1={y(malP[s.i])} y2={y(st)} animate={{ x1: mitt[s.i], x2: mitt[s.i], y1: y(malP[s.i]), y2: y(st) }} transition={{ duration: 0.25 }} />
                        <motion.circle className={`val ${beslut?.[s.i]?.beslut === 'byt' ? 'byt' : ''}`} r="5" initial={false} cx={mitt[s.i]} cy={y(st)} animate={{ cx: mitt[s.i], cy: y(st) }} transition={{ duration: 0.25 }}>
                          <title>{`Scen ${s.i + 1}: valt ${st.toFixed(1)}, mål ${malP[s.i].toFixed(1)}, original ${prof[s.i].toFixed(1)}`}</title>
                        </motion.circle>
                      </g>
                    )
                  })}
                </svg>
                <div className="fv-kedja-leg"><span><i className="o" />originalets profil</span><span><i />mål för {mal}</span><span><i className="v" />valt uttryck</span></div>
              </div>
            )
          })()}

          {!galleri && (
            <div className="fv-slider" style={{ width: STRIP }}>
              <span className="fv-end">subtil, lugn</span>
              <div className="fv-track">
                <div className="fv-orig" style={{ left: `calc(8px + (100% - 16px) * ${pct(ORIGINAL_STEG) / 100})` }}>original</div>
                {snitt != null && <motion.div className="fv-mean" animate={{ left: `calc(8px + (100% - 16px) * ${pct(snitt) / 100})` }} title={`Klippets snitt: ${snitt.toFixed(1)}`} />}
                <input type="range" min="1" max="10" step="1" value={mal} onChange={e => dra(+e.target.value)} aria-label="Rörlighet, 1 till 10" disabled={!data?.placerade} />
                <div className="fv-ticks">
                  {Array.from({ length: 10 }, (_, i) => (
                    <button key={i} style={{ left: pct(i + 1) + '%' }} className={`${mal === i + 1 ? 'on' : ''} ${ORIGINAL_STEG === i + 1 ? 'o' : ''}`} onClick={() => dra(i + 1)}>{i + 1}</button>
                  ))}
                </div>
              </div>
              <span className="fv-end">rörlig, expansiv</span>
            </div>
          )}

          {!galleri && (
            <div className="fv-tol">
              <span>tröghet</span>
              <input type="range" min="0" max="3" step="0.25" value={tolerans} onChange={e => setTolerans(+e.target.value)} aria-label="Tröghet" />
              <b>±{tolerans}</b>
              <label className={`fv-jev ${data?.jev?.nyckel ? '' : 'av'}`} title={data?.jev?.nyckel ? 'Jev väljer bland de närmaste uttrycken med grannscenerna som helhet (≈4 500 tokens per scen som byts)' : 'Jev-nyckel saknas'}>
                <input type="checkbox" checked={jevPa} disabled={!data?.jev?.nyckel} onChange={e => setJevPa(e.target.checked)} /> Jev väljer
              </label>
              {beslut && (
                <span className="fv-sum">
                  {beslut.filter(x => x.beslut === 'byt').length} av {val.length} byttes
                  {jevInfo?.regelMs != null && ` · regel ${jevInfo.regelMs.toFixed(0)} ms`}
                  {jevInfo?.jevMs != null && ` · Jev ${jevInfo.jevMs} ms (${jevInfo.valda} scener)`}
                  {jevInfo?.fel && ` · Jev: ${jevInfo.fel}`}
                </span>
              )}
              {!galleri && !data && <span className="fv-sum">läser uttrycksrummet …</span>}
            </div>
          )}

          <div className="fv-rows" style={{ width: STRIP }}>
            {tl.map(s => {
              const sc = manus.scener[s.i]
              const k = sc.kamera
              const x = valt(s.i)
              const b = beslut?.[s.i]
              return (
                <div key={s.i} className={`fv-col ${now === s.i ? 'now' : ''}`} style={{ left: px(s.start), width: px(s.tid) }}>
                  <div className="fv-text">{sc.text}</div>
                  {x && (
                    <div className="fv-meas">
                      <span className="fv-v">{x.steg.toFixed(1)}</span>
                      {(() => {
                        // golv och tak: hur lugn och hur vild scenen kan bli utan att handlingen ändras
                        const st = (data.placerade[s.i] ?? []).map(y => y.steg)
                        if (!st.length) return null
                        const lo = Math.min(...st), hi = Math.max(...st)
                        const utanfor = (beslut?.[s.i]?.mal ?? mal) < lo - 0.5 ? ' · lugnare än så går inte utan att ändra handlingen' : (beslut?.[s.i]?.mal ?? mal) > hi + 0.5 ? ' · vildare än så går inte med de här spakarna' : ''
                        return <span className="fv-spann" title="Scenens spann: lugnaste och vildaste uttryck som håller">spann {lo.toFixed(1)}–{hi.toFixed(1)}{utanfor}</span>
                      })()}
                      {b && <span className={`fv-b ${b.beslut}`}>{b.beslut === 'byt' ? 'byttes' : 'stannar'}</span>}
                      <span className="fv-besk">{beskriv(x)}</span>
                      {x.id !== 'original' && (() => {
                        // förklaringen: vad som ändrats mot originalet och vad varje spak bidrog med
                        const o = data.placerade[s.i]?.find(y => y.id === 'original')
                        if (!o) return null
                        const f = forklara({ mod: data.mod, korr: data.korr, fore: { e: o.e, p: null, amp: 1, steg: o.steg }, efter: { e: x.e, p: x.p, amp: x.amp ?? 1, steg: x.steg } })
                        // fakta först (exakta ändringar och råa mått), modellens tolkning sist och märkt som tolkning:
                        // spakandelarna förklarar modellens poäng, inte vad ändringen orsakar i tittarens upplevelse
                        const MATT = [['andel_bild', 'personernas andel av bilden'], ['momentum', 'momentum (kroppslängder/s)'], ['fard', 'förflyttning'], ['in_ut', 'in/ut per s'], ['kamera', 'kamerarörelse']]
                        const tal = v => (v == null ? '–' : v.toFixed(3).replace('.', ','))
                        const ratt = MATT.filter(([k]) => o.e?.[k] != null && x.e?.[k] != null && Math.abs(x.e[k] - o.e[k]) > 0.002).map(([k, n]) => `${n} ${tal(o.e[k])} → ${tal(x.e[k])}`)
                        return (
                          <span className="fv-forkl" title={f.spakar.map(sp => `${sp.spak}: ${sp.egenskaper.map(e => `${e.namn} ${e.bidrag.toFixed(2)}`).join(', ')}`).join(' · ')}>
                            <b>Ändrat:</b> {f.andringar.join(', ') || 'inget'}<br />
                            {ratt.length > 0 && <><b>Mätt:</b> {ratt.join(', ')}<br /></>}
                            <i>Modellens tolkning:</i> {f.text}
                          </span>
                        )
                      })()}
                    </div>
                  )}
                  <div className="fv-row fv-act">
                    {sc.handling.map((h, n) => (
                      <span key={n} className={`fv-chip r-${h.roll}`} title={ORDBOK[h.rorelse]?.om}>
                        <i />{NAMN[h.rorelse] ?? (h.rorelse.startsWith('rek:') ? `${h.roll}, riktig rörelse${h.amp && h.amp !== 1 ? ` ×${h.amp}` : ''}` : h.rorelse)}
                      </span>
                    ))}
                  </div>
                  <div className="fv-row fv-cam">
                    <span className="fv-chip cam">{k.utsnitt}</span>
                    {(k.ops ?? []).map((o, n) => <span key={n} className="fv-chip cam op">{fmtOp(o)}</span>)}
                    {k.skak ? <span className="fv-chip cam op">skak {+k.skak.toFixed(2)}</span> : null}
                  </div>
                </div>
              )
            })}
          </div>

          <div className="fv-manus">
            <button className="fv-manus-btn" onClick={() => setVisaManus(v => !v)}>{visaManus ? '▾' : '▸'} manus, scen {now + 1}{!galleri ? ` (${val[now]})` : ''}</button>
            {visaManus && <pre>{JSON.stringify(manus.scener[now], null, 2)}</pre>}
          </div>
        </div>
      </main>
    </div>
  )
}
