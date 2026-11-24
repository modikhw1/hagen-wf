import { useEffect, useMemo, useRef, useState } from 'react'
import { fonster, sammanhang, parse2d, ar2d } from './manus/kamera2d'
import { modellFor, placeraAlla, valjKedja, malProfil, aktuellaScener, INBYGGD } from '../../kalibrering/placering.mjs'
import { forklara } from '../../kalibrering/forklaring.mjs'
import './forandring.css'

// Reglaget på originalvideon (2D): varje scen spelas genom en virtuell kamera (zoom, åka in/ut,
// panorera, tilta, följa, skaka, stabilisera) över originalets pixlar. 5 = originalet exakt. Uttrycken
// är mätta genom att analysens rådata transformerats genom kamerans fönster och tolkats med samma kod
// (uttryck/matning2d.js), så reglaget väljer bland riktiga, mätta varianter. Kedjan och förklaringen är
// desamma som i 3D-reglaget.

const PW = 300
const PH = 534
const VERSION_2D = 1

const BANA_SV = { stilla: 'stilla', in: 'åker in', ut: 'åker ut', pan_v: 'panorerar vänster', pan_h: 'panorerar höger', tilt_u: 'tiltar upp', tilt_n: 'tiltar ned', folj: 'följer huvudpersonen', stab: 'stabiliserad' }
export function beskriv2d(id) {
  if (!ar2d(id)) return 'originalet'
  const p = parse2d(id)
  const delar = []
  if (p.zoom !== 1) delar.push(`zoom ${p.zoom.toString().replace('.', ',')}×${p.ankare === 'person' ? ' kring huvudpersonen' : ''}`)
  if (p.bana !== 'stilla') delar.push(`${BANA_SV[p.bana]}${p.mangd ? ` ${Math.round(p.mangd * 100)} %` : ''}`)
  if (p.skak) delar.push(p.skak >= 0.6 ? 'tydligt handhållen' : 'lite handhållen')
  return delar.join(', ') || 'originalets bild'
}

export default function Forandring2D() {
  const id = decodeURIComponent(location.hash.split('/')[1] ?? '')
  const canvas = useRef(null)
  const video = useRef(null)
  const [data, setData] = useState(null)
  const [val, setVal] = useState(null)
  const [beslut, setBeslut] = useState(null)
  const [mal, setMal] = useState(5)
  const [t, setT] = useState(0)

  useEffect(() => {
    const j = u => fetch(u).then(r => (r.ok ? r.json() : null))
    Promise.all([j(`/__data/analys/${id}.json`), j(`/__data/ra/${id}.json`), j(`/__data/uttryck2d/${id}.json`), j('/__data/brygga/korrektion.json'), j('/__kalib'), j('/__bedomningar/rorlighet'), j('/__bedomningar/rorlighet-uttryck'), j(`/__data/typer/forslag/${id}.json`)])
      .then(([an, ra, ut, korr, kal, bed, bu, fs]) => {
        if (!an || !ra || !ut) { setData({ fel: !ut ? `2D-uttrycken är inte mätta (node uttryck/kor2d.mjs ${id})` : 'analysen saknas' }); return }
        const fps = ra.fps
        const scener = an.scener.map((s, i) => {
          const k0 = Math.round(s.start * fps), k1 = Math.min(ra.sett.ramar.length, Math.max(k0 + 2, Math.round(s.slut * fps)))
          return { i, start: s.start, slut: s.slut, dur: (k1 - k0) / fps, ctx: sammanhang(ra.sett.ramar.slice(k0, k1), fps), text: fs?.scener?.[i]?.vad ?? `Scen ${i + 1}` }
        })
        const vertikal = kal.vertikaler.find(v => v.id === 'rorlighet')
        // korrektionen gäller motorns mått; 2D-uttrycken är analysens egna mått, så ingen korrektion
        const ingen = INBYGGD // 2D: analysens egna mått, alla gäller
        const { mod, namn } = modellFor({ vertikal, korr: ingen, bibliotek: kal.items.scen, bedomningar: bed ?? [], uttryck: (bu ?? []).filter(r => !String(r.bedomare ?? '').startsWith('gemini')) })
        const akt = { scener: scener.map((_, i) => (ut.scener[i]?.version === VERSION_2D ? ut.scener[i] : null)) }
        const placerade = placeraAlla(akt.scener, { mod, namn, korr: ingen })
        setData({ scener, placerade, mod, korr: ingen, namn, profil: placerade.map(l => l?.find(x => x.id === 'original')?.steg ?? null) })
        setVal(scener.map(() => 'original'))
      })
  }, [id])

  // rita: videon är klockan; varje ruta ritas genom scenens fönster
  useEffect(() => {
    if (!data?.scener || !val) return
    const c = canvas.current, g = c.getContext('2d')
    let raf
    const rita = () => {
      const v = video.current
      if (v && v.readyState >= 2) {
        const tt = v.currentTime
        const i = Math.max(0, data.scener.findIndex(s => tt < s.slut))
        const sc = data.scener[i]
        const u = tt - sc.start
        const w = ar2d(val[i]) ? fonster(parse2d(val[i]), u, sc.dur, sc.ctx, i + 1) : { cx: 0.5, cy: 0.5, z: 1, rot: 0 }
        g.save()
        g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height)
        g.translate(c.width / 2, c.height / 2)
        g.rotate((-w.rot * Math.PI) / 180)
        g.scale(w.z, w.z)
        g.translate(-w.cx * c.width, -w.cy * c.height)
        g.drawImage(v, 0, 0, c.width, c.height)
        g.restore()
        setT(tt)
      }
      raf = requestAnimationFrame(rita)
    }
    raf = requestAnimationFrame(rita)
    return () => cancelAnimationFrame(raf)
  }, [data, val])

  const valt = i => data?.placerade?.[i]?.find(x => x.id === val?.[i])
  const dra = m => {
    setMal(m)
    if (!data?.placerade) return
    const r = valjKedja({ mal: m, nu: val, listor: data.placerade, tolerans: 1 })
    setBeslut(r)
    setVal(r.map(x => x.val))
  }
  window.__dra2d = dra

  if (data?.fel) return <p className="fv-fel" style={{ padding: 24 }}>{data.fel}</p>
  if (!data) return <p style={{ padding: 24 }}>läser …</p>
  const nu = Math.max(0, data.scener.findIndex(s => t < s.slut))
  const malP = malProfil(data.profil.map(v => v ?? 5), mal)
  return (
    <div className="fv">
      <header className="fv-top">
        <div className="fv-title"><b>Videoförändring</b><span className="fv-vert">Rörlighet · 2D på originalet</span></div>
        <div className="fv-clip"><span>{id}</span></div>
      </header>
      <main className="fv-main">
        <div className="fv-player">
          <div className="fv-phone">
            <canvas ref={canvas} width={PW * 2} height={PH * 2} style={{ width: PW, height: PH }} />
          </div>
          <video ref={video} src={`/__video/${id}`} style={{ display: 'none' }} loop playsInline muted autoPlay crossOrigin="anonymous" />
          <div className="fv-controls">
            <button className="fv-play" onClick={() => { const v = video.current; v.paused ? v.play() : v.pause() }}>⏯</button>
            <span className="fv-time">{t.toFixed(1)} s · scen {nu + 1}</span>
          </div>
        </div>
        <div className="fv-board">
          <div className="fv-slider" style={{ width: 780 }}>
            <span className="fv-end">subtil, lugn</span>
            <div className="fv-track">
              <input type="range" min="1" max="10" step="1" value={mal} onChange={e => dra(+e.target.value)} aria-label="Rörlighet, 1 till 10" />
              <div className="fv-ticks">{Array.from({ length: 10 }, (_, i) => <button key={i} style={{ left: ((i) / 9) * 100 + '%' }} className={`${mal === i + 1 ? 'on' : ''} ${i === 4 ? 'o' : ''}`} onClick={() => dra(i + 1)}>{i + 1}</button>)}</div>
            </div>
            <span className="fv-end">rörlig, expansiv</span>
          </div>
          <div className="fv-rader2d">
            {data.scener.map((s, i) => {
              const x = valt(i)
              const o = data.placerade[i]?.find(y => y.id === 'original')
              const f = x && o && x.id !== 'original' ? forklara({ mod: data.mod, korr: data.korr, fore: { e: o.e, p: null, amp: 1, steg: o.steg }, efter: { e: x.e, p: null, amp: 1, steg: x.steg } }) : null
              const MATT = [['andel_bild', 'personernas andel av bilden'], ['momentum', 'momentum (kroppslängder/s)'], ['fard', 'förflyttning'], ['in_ut', 'in/ut per s'], ['kamera', 'kamerarörelse']]
              const tal = v => (v == null ? '–' : v.toFixed(3).replace('.', ','))
              const ratt = x && o ? MATT.filter(([k]) => o.e?.[k] != null && x.e?.[k] != null && Math.abs(x.e[k] - o.e[k]) > 0.002).map(([k, n]) => `${n} ${tal(o.e[k])} → ${tal(x.e[k])}`) : []
              return (
                <div key={i} className={`fv-rad2d ${nu === i ? 'now' : ''}`}>
                  <div className="fv-text"><b>{i + 1}.</b> {s.text}</div>
                  {!data.placerade[i] ? <div className="fv-besk">inte mätt (version)</div> : (
                    <div className="fv-meas">
                      <span className="fv-v">{x?.steg?.toFixed(1)}</span>
                      <span className="fv-b">mål {malP[i].toFixed(1)}</span>
                      {(() => {
                        // golv och tak: hur lugn och hur vild scenen kan bli utan att handlingen ändras
                        const st = (data.placerade[i] ?? []).map(y => y.steg)
                        if (!st.length) return null
                        const lo = Math.min(...st), hi = Math.max(...st)
                        const utanfor = malP[i] < lo - 0.5 ? ' · lugnare än så går inte utan att ändra handlingen' : malP[i] > hi + 0.5 ? ' · vildare än så går inte med de här spakarna' : ''
                        return <span className="fv-spann" title="Scenens spann: lugnaste och vildaste uttryck som håller">spann {lo.toFixed(1)}–{hi.toFixed(1)}{utanfor}</span>
                      })()}
                      <span className="fv-besk">{beskriv2d(val[i])}{x?.ord ? ` · analysen ser: ${x.ord.join(', ')}` : ''}</span>
                      {f && (
                        <span className="fv-forkl">
                          <b>Ändrat:</b> {beskriv2d(val[i])}<br />
                          {ratt.length > 0 && <><b>Mätt:</b> {ratt.join(', ')}<br /></>}
                          <i>Modellens tolkning:</i> {f.text}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </main>
    </div>
  )
}
