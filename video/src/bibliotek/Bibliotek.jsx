import { useEffect, useMemo, useRef, useState } from 'react'
import './bibliotek.css'

// Biblioteket: varje klipp nedbrutet av den lokala analysen (analys/kor.mjs), granskat mot videon.
// Rättelser sparas i data/rattelser/<id>.json och är facit när analysens gränser kalibreras.

const UTSNITT = ['total', 'halvtotal', 'halvbild', 'nara', 'extrem', 'objekt']
const KLIPPTYPER = ['scen', 'overgang', 'hopp', 'zoomryck', 'inskott', 'svag', 'fel']
const KLIPPNAMN = { scen: 'scenbyte', overgang: 'övergång', hopp: 'hoppklipp', zoomryck: 'zoomryck', inskott: 'inskott', svag: 'svag kandidat', fel: 'inget klipp' }
const PERSONFARG = ['#2f6bff', '#f26a2e', '#1f9d63', '#9b4dca']
// MediaPipe Pose: kroppens linjer
const LINJER = [[11, 12], [11, 13], [13, 15], [12, 14], [14, 16], [11, 23], [12, 24], [23, 24], [23, 25], [25, 27], [27, 31], [24, 26], [26, 28], [28, 32], [9, 10]]
const fmt = t => `${Math.floor(t / 60)}:${(t % 60).toFixed(1).padStart(4, '0')}`

const idFranHash = () => decodeURIComponent(location.hash.split('/')[1] ?? '') || null

export default function Bibliotek() {
  const [lista, setLista] = useState(null)
  const [valt, setValt] = useState(idFranHash)
  const [sort, setSort] = useState('konto')
  useEffect(() => { fetch('/__index').then(r => r.json()).then(setLista) }, [])
  const valj = id => { setValt(id); history.replaceState(null, '', id ? `#bibliotek/${encodeURIComponent(id)}` : '#bibliotek') }
  const sorterad = useMemo(() => {
    if (!lista) return []
    const nyckel = {
      konto: a => a.id,
      scener: a => -a.sammanfattning.scener,
      dynamik: a => -a.sammanfattning.dynamikPerMin,
      kamera: a => -a.sammanfattning.aktivitet.kamera,
      motiv: a => -a.sammanfattning.aktivitet.motiv,
    }[sort]
    return lista.slice().sort((a, b) => (nyckel(a) < nyckel(b) ? -1 : nyckel(a) > nyckel(b) ? 1 : 0))
  }, [lista, sort])

  return (
    <div className="bib">
      <header className="bib-top">
        <b>Bibliotek</b>
        <span className="bib-meta">{lista ? `${lista.length} klipp · analys v${lista[0]?.version ?? '–'} · ${lista.filter(a => a.rattad).length} granskade` : 'läser …'}</span>
        <label className="bib-sort">sortera
          <select value={sort} onChange={e => setSort(e.target.value)}>
            <option value="konto">konto</option>
            <option value="scener">antal scener</option>
            <option value="dynamik">dynamik per minut</option>
            <option value="kamera">kamerans rörelse</option>
            <option value="motiv">motivets rörelse</option>
          </select>
        </label>
        {valt && <button className="bib-btn" onClick={() => valj(null)}>spridning</button>}
      </header>
      <div className="bib-main">
        <aside className="bib-lista">
          {sorterad.map(a => (
            <button key={a.id} className={`bib-kort ${valt === a.id ? 'valt' : ''}`} onClick={() => valj(a.id)}>
              <div className="bib-remsa">
                {a.scener.slice(0, 6).map(s => <img key={s.i} src={`/__data/${s.bild}`} alt="" loading="lazy" style={{ flexGrow: s.langd }} />)}
              </div>
              <div className="bib-rad">
                <b>@{a.konto ?? a.id}</b>
                {a.rattad && <span className="bib-ok" title="Granskad">✓</span>}
              </div>
              <div className="bib-rad dim">
                <span>{a.meta.langd.toFixed(0)} s</span>
                <span>{a.sammanfattning.scener} sc</span>
                <span>{a.sammanfattning.dynamikPerMin.toFixed(0)} dyn/min</span>
                <span>{a.sammanfattning.utsnitt}</span>
              </div>
            </button>
          ))}
        </aside>
        {valt ? <Inspektor key={valt} id={valt} rattad={lista?.find(a => a.id === valt)?.rattad} /> : <Spridning lista={lista ?? []} valj={valj} />}
      </div>
    </div>
  )
}

// Hur biblioteket sprider sig: kamerans rörelse mot motivets, storlek efter antal scener.
// Visar var det finns klipp och var det saknas.
function Spridning({ lista, valj }) {
  const W = 620
  const H = 460
  const M = 44
  const xs = lista.map(a => Math.sqrt(a.sammanfattning.aktivitet.kamera))
  const ys = lista.map(a => Math.sqrt(a.sammanfattning.aktivitet.motiv))
  const mx = Math.max(0.1, ...xs) * 1.1
  const my = Math.max(0.1, ...ys) * 1.1
  const X = v => M + (v / mx) * (W - M * 1.5)
  const Y = v => H - M - (v / my) * (H - M * 1.5)
  const farg = { total: '#8c877f', halvtotal: '#1f9d63', halvbild: '#2f6bff', nara: '#9b4dca', extrem: '#f26a2e', objekt: '#1f1f1f' }
  const [hov, setHov] = useState(null)
  return (
    <section className="bib-sprid">
      <h2>Spridning</h2>
      <p className="dim">Varje punkt är ett klipp. Åt höger rör sig kameran mer, uppåt rör sig personerna mer (i bilden, kamerans rörelse bortdragen). Storlek är antal scener, färg är vanligaste utsnitt.</p>
      <svg width={W} height={H} className="bib-plot">
        <line x1={M} y1={H - M} x2={W - M / 2} y2={H - M} />
        <line x1={M} y1={H - M} x2={M} y2={M / 2} />
        <text x={W - M / 2} y={H - M + 28} textAnchor="end">kamera →</text>
        <text x={M - 8} y={M / 2} textAnchor="end" transform={`rotate(-90 ${M - 30} ${M / 2})`}>motiv →</text>
        {lista.map((a, i) => (
          <circle key={a.id} cx={X(xs[i])} cy={Y(ys[i])} r={4 + Math.sqrt(a.sammanfattning.scener) * 3}
            fill={farg[a.sammanfattning.utsnitt] ?? '#999'} fillOpacity={0.75} stroke="#1f1f1f" strokeWidth={hov === a.id ? 2.5 : 1}
            onMouseEnter={() => setHov(a.id)} onMouseLeave={() => setHov(null)} onClick={() => valj(a.id)} style={{ cursor: 'pointer' }} />
        ))}
        {hov && (() => { const i = lista.findIndex(a => a.id === hov); return <text x={X(xs[i]) + 12} y={Y(ys[i]) - 10} className="bib-hov">@{lista[i].konto}</text> })()}
      </svg>
      <div className="bib-legend">{Object.entries(farg).map(([k, c]) => <span key={k}><i style={{ background: c }} />{k}</span>)}</div>
    </section>
  )
}

function Inspektor({ id, rattad }) {
  const [a, setA] = useState(null)
  const [ratt, setRatt] = useState({ klipp: {}, nya: [], scener: {} })
  const [sparat, setSparat] = useState(null)
  const [andrad, setAndrad] = useState(false)
  const [t, setT] = useState(0)
  const [spelar, setSpelar] = useState(false)
  const video = useRef(null)
  const canvas = useRef(null)

  useEffect(() => {
    fetch(`/__data/analys/${id}.json`).then(r => r.json()).then(setA)
    if (rattad) fetch(`/__data/rattelser/${id}.json`).then(r => (r.ok ? r.json() : null)).then(r => r && (setRatt({ klipp: r.klipp ?? {}, nya: r.nya ?? [], scener: r.scener ?? {} }), setSparat(r.sparad)))
  }, [id, rattad])

  // Följ videon bildruta för bildruta.
  useEffect(() => {
    const v = video.current
    if (!v) return
    let h
    const tick = () => { setT(v.currentTime); h = v.requestVideoFrameCallback ? v.requestVideoFrameCallback(tick) : requestAnimationFrame(tick) }
    h = v.requestVideoFrameCallback ? v.requestVideoFrameCallback(tick) : requestAnimationFrame(tick)
    const upd = () => setT(v.currentTime)
    v.addEventListener('seeked', upd)
    return () => { v.cancelVideoFrameCallback?.(h); cancelAnimationFrame(h); v.removeEventListener('seeked', upd) }
  }, [a])

  // Tangenter: mellanslag spelar, pilar stegar en analysruta.
  useEffect(() => {
    const k = e => {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return
      const v = video.current
      if (!v) return
      if (e.key === ' ') { e.preventDefault(); v.paused ? v.play() : v.pause() }
      if (e.key === 'ArrowRight') { v.pause(); v.currentTime = Math.min(v.duration, v.currentTime + 0.1) }
      if (e.key === 'ArrowLeft') { v.pause(); v.currentTime = Math.max(0, v.currentTime - 0.1) }
    }
    addEventListener('keydown', k)
    return () => removeEventListener('keydown', k)
  }, [])

  const fps = a?.analys.fps ?? 10
  const ruta = a ? a.ramar[Math.max(0, Math.min(a.ramar.length - 1, Math.round(t * fps)))] : null
  const scenNu = a ? a.scener.findIndex(s => t >= s.start && t < s.slut) : -1

  // Rita personerna ovanpå videon.
  useEffect(() => {
    const c = canvas.current
    if (!c || !ruta) return
    const g = c.getContext('2d')
    const W = c.width
    const H = c.height
    g.clearRect(0, 0, W, H)
    for (const p of ruta.p) {
      const col = PERSONFARG[p.id % PERSONFARG.length]
      const pt = i => [p.lm[i * 3] * W, p.lm[i * 3 + 1] * H, p.lm[i * 3 + 2]]
      g.lineWidth = 3
      g.strokeStyle = col
      g.lineCap = 'round'
      for (const [i, j] of LINJER) {
        const A = pt(i)
        const B = pt(j)
        if (A[2] < 0.5 || B[2] < 0.5) continue
        g.beginPath(); g.moveTo(A[0], A[1]); g.lineTo(B[0], B[1]); g.stroke()
      }
      g.fillStyle = col
      for (let i = 0; i < 33; i++) { const P = pt(i); if (P[2] >= 0.5) { g.beginPath(); g.arc(P[0], P[1], i === 0 ? 5 : 2.5, 0, 7); g.fill() } }
      const [x0, y0, x1, y1] = p.b
      g.setLineDash([4, 4]); g.lineWidth = 1
      g.strokeRect(x0 * W, y0 * H, (x1 - x0) * W, (y1 - y0) * H)
      g.setLineDash([])
    }
    // kamerans rörelse: pil från mitten (förstärkt), cirkel för zoom
    if (ruta.k) {
      const [dx, dy, , s] = ruta.k
      g.strokeStyle = '#ffffff'
      g.lineWidth = 3
      g.beginPath(); g.moveTo(W / 2, H / 2); g.lineTo(W / 2 - dx * W * 8, H / 2 - dy * H * 8); g.stroke()
      g.beginPath(); g.arc(W / 2, H / 2, 6 + Math.abs(Math.log(s)) * 600, 0, 7); g.stroke()
    }
  }, [ruta])

  if (!a) return <section className="bib-insp"><p className="dim">läser analysen …</p></section>

  const L = a.meta.langd
  const TW = 600
  const X = tt => (tt / L) * TW
  const kurva = a.scener.flatMap(s => s.kurva)
  const kMax = Math.max(0.2, ...kurva.map(k => Math.max(k[0], k[1])))
  const kurvaPath = n => kurva.map((k, i) => `${i ? 'L' : 'M'}${X(i / fps).toFixed(1)} ${(40 - Math.min(1, k[n] / kMax) * 38).toFixed(1)}`).join(' ')
  const typFor = k => ratt.klipp[k.t] ?? k.typ
  const sok = tt => { const v = video.current; if (v) { v.currentTime = Math.max(0, Math.min(L - 0.01, tt)) } }
  const andra = f => { setRatt(r => f(structuredClone(r))); setAndrad(true) }
  const spara = async () => {
    const r = await fetch(`/__ratta/${id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id, analysversion: a.version, ...ratt }) })
    if (r.ok) { setSparat(new Date().toISOString()); setAndrad(false) }
  }
  const s = a.scener[scenNu]

  return (
    <section className="bib-insp">
      <div className="bib-insp-top">
        <h2>@{a.konto ?? a.id}</h2>
        <span className="dim">{a.meta.langd.toFixed(1)} s · {a.meta.bredd}×{a.meta.hojd} · {a.meta.fps} fps · {a.motor?.pose}</span>
        <span className="bib-spara">
          {sparat && !andrad && <span className="dim">sparat {new Date(sparat).toLocaleString('sv-SE')}</span>}
          <button className="bib-btn" disabled={!andrad} onClick={spara}>{andrad ? 'spara rättelser' : 'inga ändringar'}</button>
        </span>
      </div>

      <div className="bib-insp-main">
        <div className="bib-video">
          <div className="bib-skarm">
            <video ref={video} src={`/__video/${encodeURIComponent(id)}`} width={315} height={560} playsInline
              onPlay={() => setSpelar(true)} onPause={() => setSpelar(false)} />
            <canvas ref={canvas} width={315} height={560} />
            {s && <span className="bib-scenetikett">scen {s.i + 1} · {ratt.scener[s.i]?.utsnitt ?? s.utsnitt.varde}</span>}
          </div>
          <div className="bib-kontroll">
            <button className="bib-btn" onClick={() => (video.current.paused ? video.current.play() : video.current.pause())}>{spelar ? 'paus' : 'spela'}</button>
            <span className="tab">{fmt(t)}</span>
            {[0.25, 0.5, 1].map(r => <button key={r} className="bib-btn liten" onClick={() => { video.current.playbackRate = r }}>{r}×</button>)}
          </div>
          {ruta && (
            <dl className="bib-ruta">
              <dt>personer</dt><dd>{ruta.p.length}</dd>
              <dt>kamera</dt><dd>{ruta.k ? `→ ${(-ruta.k[0] * 100).toFixed(1)} · ↑ ${(-ruta.k[1] * 100).toFixed(1)} · zoom ${((ruta.k[3] - 1) * 100).toFixed(1)} %` : '–'}</dd>
            </dl>
          )}
        </div>

        <div className="bib-tid">
          <svg width={TW} height={150} className="bib-tidslinje" onClick={e => { const r = e.currentTarget.getBoundingClientRect(); sok(((e.clientX - r.left) / TW) * L) }}>
            {a.scener.map(sc => (
              <g key={sc.i}>
                <rect x={X(sc.start)} y={0} width={X(sc.slut) - X(sc.start)} height={46} className={`sc ${sc.i % 2 ? 'b' : 'a'} ${sc.i === scenNu ? 'nu' : ''}`} />
                <text x={X(sc.start) + 4} y={14}>{sc.i + 1}</text>
                <text x={X(sc.start) + 4} y={30} className="u">{ratt.scener[sc.i]?.utsnitt ?? sc.utsnitt.varde}</text>
              </g>
            ))}
            {a.klipp.map(k => {
              const ty = typFor(k)
              const rattad = ratt.klipp[k.t] != null
              return (
                <g key={k.t} className={`kl ${ty} ${rattad ? 'r' : ''}`} onClick={e => {
                  e.stopPropagation()
                  andra(r => { const i = KLIPPTYPER.indexOf(ty); const nytt = KLIPPTYPER[(i + 1) % KLIPPTYPER.length]; if (nytt === k.typ) delete r.klipp[k.t]; else r.klipp[k.t] = nytt; return r })
                }}>
                  <title>{`${k.t.toFixed(2)} s · ${KLIPPNAMN[ty]} · styrka ${k.styrka} · likhet ${k.likhet.andel}${k.likhet.skala ? ` · skala ${k.likhet.skala}` : ''}${rattad ? ` · analysen sa ${KLIPPNAMN[k.typ]}` : ''} — klicka för att ändra`}</title>
                  <rect x={X(k.t) - 6} y={0} width={12} height={58} fill="transparent" />
                  <line x1={X(k.t)} y1={ty === 'scen' ? 0 : 34} x2={X(k.t)} y2={ty === 'scen' ? 52 : 52} />
                  {ty === 'zoomryck' && <circle cx={X(k.t)} cy={52} r={4} />}
                  {ty === 'fel' && <text x={X(k.t)} y={56} textAnchor="middle">×</text>}
                </g>
              )
            })}
            {ratt.nya.map((nt, n) => (
              <g key={`n${n}`} className="kl scen r" onClick={e => { e.stopPropagation(); andra(r => { r.nya.splice(n, 1); return r }) }}>
                <title>{`${nt.toFixed(2)} s · tillagt scenbyte — klicka för att ta bort`}</title>
                <rect x={X(nt) - 6} y={0} width={12} height={58} fill="transparent" />
                <line x1={X(nt)} y1={0} x2={X(nt)} y2={52} strokeDasharray="3 3" />
              </g>
            ))}
            <g transform="translate(0 70)">
              <path d={kurvaPath(0)} className="kurva kam" />
              <path d={kurvaPath(1)} className="kurva mot" />
              <text x={TW} y={52} textAnchor="end" className="dim">blå = kamera, svart = motiv (bildhöjder/s, max {kMax.toFixed(2)})</text>
            </g>
            <line x1={X(t)} y1={0} x2={X(t)} y2={150} className="spelhuvud" />
          </svg>
          <div className="bib-tidrad">
            <button className="bib-btn liten" onClick={() => andra(r => { r.nya.push(Math.round(t * 1000) / 1000); return r })}>+ scenbyte vid {t.toFixed(2)} s</button>
            <span className="dim">Klicka på ett klipp i tidslinjen för att byta typ: {KLIPPTYPER.map(k => KLIPPNAMN[k]).join(' → ')}.</span>
          </div>

          <div className="bib-scener">
            {a.scener.map(sc => {
              const rs = ratt.scener[sc.i] ?? {}
              return (
                <div key={sc.i} className={`bib-scen ${sc.i === scenNu ? 'nu' : ''}`} onClick={() => sok(sc.start + 0.01)}>
                  <img src={`/__data/${sc.bild}`} alt="" />
                  <div className="bib-scen-info">
                    <div className="rad"><b>{sc.i + 1}</b><span className="dim">{sc.start.toFixed(1)}–{sc.slut.toFixed(1)} s</span>{sc.montage && <span className="chip">montage</span>}</div>
                    <label className={rs.utsnitt ? 'rattad' : ''} onClick={e => e.stopPropagation()}>
                      <select value={rs.utsnitt ?? sc.utsnitt.varde} onChange={e => andra(r => { const v = e.target.value; r.scener[sc.i] = { ...(r.scener[sc.i] ?? {}), utsnitt: v === sc.utsnitt.varde ? undefined : v }; return r })}>
                        {UTSNITT.map(u => <option key={u} value={u}>{u}</option>)}
                      </select>
                      <span className="dim">{Math.round(sc.utsnitt.andel * 100)} %</span>
                    </label>
                    <div className="rad dim">{sc.personer} pers{sc.placering ? ` · ${sc.placering.sida}` : ''}{sc.vridning ? ` · ${sc.vridning.ord}` : ''}</div>
                    <div className="rad">{sc.kamera.ord.map(o => <span key={o} className="chip kam">{o}</span>)}</div>
                    <div className="rad dim">kamera {sc.aktivitet.kamera ?? "–"} · motiv {sc.aktivitet.motiv ?? "–"}{sc.dynamik.length ? ` · ${sc.dynamik.length} dyn` : ''}</div>
                    <textarea placeholder="anteckning" value={rs.anteckning ?? ''} onClick={e => e.stopPropagation()}
                      onChange={e => andra(r => { r.scener[sc.i] = { ...(r.scener[sc.i] ?? {}), anteckning: e.target.value || undefined }; return r })} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
