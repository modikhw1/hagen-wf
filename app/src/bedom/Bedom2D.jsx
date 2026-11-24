import { useEffect, useMemo, useRef, useState } from 'react'
import { fonster, sammanhang, parse2d, ar2d } from '../forandring/manus/kamera2d'
import { beskriv2d } from '../forandring/Forandring2D.jsx'
import { modellFor, placeraAlla, INBYGGD } from '../../kalibrering/placering.mjs'
import { overens, korsvalidera } from '../../kalibrering/modell.mjs'
import { valjPar, bedomningsRad, VERTIKAL_UTTRYCK } from '../../kalibrering/par.mjs'
import './bedom.css'

// Bedömning av rörlighet på riktig video: samma scen ur originalklippet, sedd genom två virtuella
// kameror (2D), sida vid sida i loop. Du väljer vilken som är mer rörlig och expansiv.
// Tangenter: ← vänster, → höger, ↓ lika, mellanslag hoppa.

const W = 270
const H = 480
const VERSION_2D = 1

// Utan klipp: de klipp som har mätta 2D-uttryck.
function Lista() {
  const [lista, setLista] = useState(null)
  useEffect(() => { fetch('/__uttryck2d').then(r => r.json()).then(setLista).catch(() => setLista([])) }, [])
  return (
    <div className="bd">
      <h1>Bedöm rörlighet på riktig video</h1>
      <p>Samma scen ur originalklippet, sedd genom två virtuella kameror. Välj den som är mer rörlig och expansiv: ← vänster, → höger, ↓ lika, mellanslag hoppa.</p>
      {lista == null ? <p>läser …</p> : lista.length === 0 ? <p>Inga klipp har mätta 2D-uttryck än (node uttryck/kor2d.mjs &lt;id&gt;).</p> : (
        <ul>{lista.map(x => <li key={x.id}><a href={`#bedom2d/${x.id}`} onClick={() => setTimeout(() => location.reload(), 0)}>{x.id}</a> <span className="dim">· {x.scener} scener</span></li>)}</ul>
      )}
    </div>
  )
}

function Duk({ id, sc, uttryck, seed }) {
  const ref = useRef(null)
  const vid = useRef(null)
  useEffect(() => {
    const v = vid.current, c = ref.current, g = c.getContext('2d')
    let raf
    const rita = () => {
      if (v.readyState >= 2) {
        if (v.currentTime < sc.start || v.currentTime >= sc.slut - 0.02) v.currentTime = sc.start
        const u = v.currentTime - sc.start
        const w = ar2d(uttryck) ? fonster(parse2d(uttryck), u, sc.dur, sc.ctx, seed) : { cx: 0.5, cy: 0.5, z: 1, rot: 0 }
        g.save(); g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height)
        g.translate(c.width / 2, c.height / 2); g.rotate((-w.rot * Math.PI) / 180); g.scale(w.z, w.z); g.translate(-w.cx * c.width, -w.cy * c.height)
        g.drawImage(v, 0, 0, c.width, c.height); g.restore()
      }
      raf = requestAnimationFrame(rita)
    }
    v.currentTime = sc.start
    v.play().catch(() => {})
    raf = requestAnimationFrame(rita)
    return () => cancelAnimationFrame(raf)
  }, [sc, uttryck])
  return (
    <>
      <canvas ref={ref} width={W * 2} height={H * 2} style={{ width: W, height: H }} />
      <video ref={vid} src={`/__video/${id}`} style={{ display: 'none' }} muted playsInline crossOrigin="anonymous" />
    </>
  )
}

export default function Bedom2D() {
  const id = decodeURIComponent(location.hash.split('/')[1] ?? '')
  if (!id) return <Lista />
  const [data, setData] = useState(null)
  const [rader, setRader] = useState([])
  const [par, setPar] = useState(null)
  const [visa, setVisa] = useState(false)
  const t0 = useRef(0)

  useEffect(() => {
    const j = u => fetch(u).then(r => (r.ok ? r.json() : null))
    Promise.all([j(`/__data/analys/${id}.json`), j(`/__data/ra/${id}.json`), j(`/__data/uttryck2d/${id}.json`), j('/__data/brygga/korrektion.json'), j('/__kalib'), j('/__bedomningar/rorlighet'), j(`/__bedomningar/${VERTIKAL_UTTRYCK}`), j(`/__data/typer/forslag/${id}.json`)])
      .then(([an, ra, ut, korr, kal, bed, bu, fs]) => {
        if (!an || !ra || !ut) { setData({ fel: `2D-uttrycken saknas (node uttryck/kor2d.mjs ${id})` }); return }
        const fps = ra.fps
        const scener = an.scener.map((s, i) => {
          const k0 = Math.round(s.start * fps), k1 = Math.min(ra.sett.ramar.length, Math.max(k0 + 2, Math.round(s.slut * fps)))
          return { i, start: s.start, slut: s.slut, dur: (k1 - k0) / fps, ctx: sammanhang(ra.sett.ramar.slice(k0, k1), fps), text: fs?.scener?.[i]?.vad ?? `Scen ${i + 1}` }
        })
        const ingen = INBYGGD // 2D: analysens egna mått, alla gäller
        setRader(bu ?? [])
        setData({ scener, ut, kal, bed: bed ?? [], korr: ingen })
      })
  }, [id])

  const modell = useMemo(() => {
    if (!data?.ut) return null
    const vertikal = data.kal.vertikaler.find(v => v.id === 'rorlighet')
    // bara människans bedömningar tränar modellen; maskindomarens används först när den kontrollerats mot dina
    const manniska = rader.filter(r => !String(r.bedomare ?? '').startsWith('gemini'))
    const m = modellFor({ vertikal, korr: data.korr, bibliotek: data.kal.items.scen, bedomningar: data.bed, uttryck: manniska })
    const listor = placeraAlla(data.scener.map((_, i) => (data.ut.scener[i]?.version === VERSION_2D ? data.ut.scener[i] : null)), { mod: m.mod, namn: m.namn, korr: data.korr })
    const mina = manniska.filter(r => r.val !== 'hoppa')
    const o = mina.length ? overens(m.mod, m.items, mina) : null
    const kv = mina.length >= 20 ? korsvalidera({ items: m.items, bedomningar: mina, namn: m.namn, start: Object.fromEntries(m.namn.map(n => [n, vertikal.start?.[n] ?? 0])) }) : null
    return { ...m, listor, o, kv, mina }
  }, [data, rader])

  const nytt = () => {
    if (!modell) return
    const gjorda = new Set(rader.map(r => `${r.a.split('#')[1]}:${[r.a.split('#')[2], r.b.split('#')[2]].sort().join('|')}`))
    // 2D har bara kameraspakar: par av sorten kamera och ankare
    setPar(valjPar(modell.listor, { gjorda, sort: Math.random() < 0.75 ? 'kamera' : 'ankare' }))
    setVisa(false)
    t0.current = performance.now()
  }
  useEffect(() => { if (modell && !par) nytt() }, [modell])

  const svara = async val => {
    if (!par) return
    const rad = bedomningsRad({ klipp: id, par, val, korr: data.korr, namn: modell.namn, ms: Math.round(performance.now() - t0.current) })
    const r = await fetch(`/__bedom/${VERTIKAL_UTTRYCK}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(rad) })
    if (!r.ok) return
    setRader(x => [...x, rad])
    nytt()
  }
  useEffect(() => {
    const k = e => {
      if (e.key === 'ArrowLeft') svara('a')
      else if (e.key === 'ArrowRight') svara('b')
      else if (e.key === 'ArrowDown') svara('lika')
      else if (e.key === ' ') { e.preventDefault(); svara('hoppa') }
    }
    addEventListener('keydown', k)
    return () => removeEventListener('keydown', k)
  })

  if (data?.fel) return <div className="bd"><p className="bd-fel">{data.fel}</p></div>
  if (!modell) return <div className="bd"><p>läser …</p></div>
  const pct = x => (x == null ? '–' : `${Math.round(x * 100)} %`)
  const sc = par ? data.scener[par.scen] : null
  return (
    <div className="bd">
      <header>
        <h1>Vilken är mer rörlig och expansiv?</h1>
        <span className="bd-stat">{modell.mina.length} bedömningar · modellen håller med dig om {pct(modell.o?.andel)}{modell.kv ? ` · på klipp den inte tränats på: ${pct(modell.kv.andel)}` : ' · korsvalidering från 20 bedömningar'}</span>
      </header>
      {par ? (
        <>
          <p className="bd-scen">{id} · scen {par.scen + 1}: {sc.text}</p>
          <div className="bd-par">
            <figure><Duk id={id} sc={sc} uttryck={par.a.id} seed={par.scen + 1} /><button onClick={() => svara('a')}>← den här</button></figure>
            <div className="bd-mitt">
              <button onClick={() => svara('lika')}>↓ lika</button>
              <button className="dim" onClick={() => svara('hoppa')}>hoppa (mellanslag)</button>
              <button className="dim" onClick={() => setVisa(v => !v)}>{visa ? 'dölj' : 'visa'} vad som skiljer</button>
            </div>
            <figure><Duk id={id} sc={sc} uttryck={par.b.id} seed={par.scen + 1} /><button onClick={() => svara('b')}>den här →</button></figure>
          </div>
          {visa && (
            <div className="bd-varfor">
              <p><b>Vänster:</b> {beskriv2d(par.a.id)} · steg {par.a.steg.toFixed(1)}</p>
              <p><b>Höger:</b> {beskriv2d(par.b.id)} · steg {par.b.steg.toFixed(1)}</p>
              <p className="dim">Modellen tror att {par.a.u > par.b.u ? 'vänster' : 'höger'} är mer rörlig.</p>
            </div>
          )}
        </>
      ) : <p>Inga fler par.</p>}
    </div>
  )
}
