import { useEffect, useMemo, useRef, useState } from 'react'
import { Spelare } from '../forandring/motor/spelare'
import { enScen } from '../forandring/manus/variant'
import { modellFor, placeraAlla, beskriv, aktuellaScener } from '../../kalibrering/placering.mjs'
import { overens, korsvalidera } from '../../kalibrering/modell.mjs'
import { valjPar, bedomningsRad, VERTIKAL_UTTRYCK } from '../../kalibrering/par.mjs'
import './bedom.css'

// Bedömning av rörlighet: samma scen ur ett rekonstruerat klipp, filmad och spelad på två sätt,
// sida vid sida i loop. Du väljer vilken som är mer rörlig och expansiv. Allt annat är lika, så svaret
// gäller bara vertikalen. Varje svar tränar modellen; överensstämmelsen visas löpande.
// Tangenter: ← vänster, → höger, ↓ lika, mellanslag hoppa.

const W = 270
const H = 480

function Duk({ manus }) {
  const ref = useRef(null)
  useEffect(() => {
    if (!manus) return
    const s = new Spelare(ref.current, { bredd: W, hojd: H })
    s.load(manus)
    s.play()
    return () => s.dispose()
  }, [manus])
  return <canvas ref={ref} style={{ width: W, height: H }} />
}

export default function Bedom() {
  const klipp = decodeURIComponent(location.hash.split('/')[1] ?? '')
  const [lista, setLista] = useState(null)
  const [bas, setBas] = useState(null)
  const [data, setData] = useState(null)
  const [rader, setRader] = useState([])
  const [par, setPar] = useState(null)
  const [visaVarfor, setVisaVarfor] = useState(false)
  const t0 = useRef(0)

  useEffect(() => {
    if (!klipp) { fetch('/__rekon').then(r => r.json()).then(setLista); return }
    const j = u => fetch(u).then(r => (r.ok ? r.json() : null))
    Promise.all([j(klipp.endsWith('~modell') ? `/__data/rekon/${klipp.slice(0, -7)}/manus-modell.json` : `/__data/rekon/${klipp}/manus.json`), j(`/__data/uttryck/${klipp}.json`), j('/__data/brygga/korrektion.json'), j('/__kalib'), j('/__bedomningar/rorlighet'), j(`/__bedomningar/${VERTIKAL_UTTRYCK}`)])
      .then(([m, ut, korr, kal, bed, bu]) => {
        if (!m || !ut) { setData({ fel: !m ? `ingen rekonstruktion (npm run rekon -- ${klipp})` : `inget uttrycksrum (npm run uttrycksrum -- --klipp ${klipp})` }); return }
        setBas(m)
        setRader(bu ?? [])
        setData({ ut, korr, kal, bed: bed ?? [] })
      })
  }, [klipp])

  // modellen och placeringen med alla bedömningar hittills
  const modell = useMemo(() => {
    if (!data?.ut) return null
    const vertikal = data.kal.vertikaler.find(v => v.id === 'rorlighet')
    const manniska = rader.filter(r => !String(r.bedomare ?? '').startsWith('gemini'))
    const m = modellFor({ vertikal, korr: data.korr, bibliotek: data.kal.items.scen, bedomningar: data.bed, uttryck: manniska })
    const listor = placeraAlla(aktuellaScener(data.ut, bas.scener.length, { rekon: true }).scener, { mod: m.mod, namn: m.namn, korr: data.korr })
    const mina = manniska.filter(r => r.val !== 'hoppa')
    const o = mina.length ? overens(m.mod, m.items, mina) : null
    const kv = mina.length >= 20 ? korsvalidera({ items: m.items, bedomningar: mina, namn: m.namn, start: Object.fromEntries(m.namn.map(n => [n, vertikal.start?.[n] ?? 0])) }) : null
    return { ...m, listor, o, kv, mina }
  }, [data, rader, bas])

  const nytt = () => {
    if (!modell) return
    const gjorda = new Set(rader.map(r => { const [, s] = r.a.split('#'); return `${s}:${[r.a.split('#')[2], r.b.split('#')[2]].sort().join('|')}` }))
    setPar(valjPar(modell.listor, { gjorda }))
    setVisaVarfor(false)
    t0.current = performance.now()
  }
  useEffect(() => { if (modell && !par) nytt() }, [modell])

  const svara = async val => {
    if (!par) return
    const rad = bedomningsRad({ klipp, par, val, korr: data.korr, namn: modell.namn, ms: Math.round(performance.now() - t0.current) })
    const r = await fetch(`/__bedom/${VERTIKAL_UTTRYCK}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(rad) })
    if (!r.ok) return
    setRader(x => [...x, rad])
    nytt()
  }
  useEffect(() => {
    const k = e => {
      if (e.target.tagName === 'INPUT') return
      if (e.key === 'ArrowLeft') svara('a')
      else if (e.key === 'ArrowRight') svara('b')
      else if (e.key === 'ArrowDown') svara('lika')
      else if (e.key === ' ') { e.preventDefault(); svara('hoppa') }
    }
    addEventListener('keydown', k)
    return () => removeEventListener('keydown', k)
  })

  const manusA = useMemo(() => (par && bas ? enScen(bas, par.scen, par.a.id) : null), [par, bas])
  const manusB = useMemo(() => (par && bas ? enScen(bas, par.scen, par.b.id) : null), [par, bas])

  if (!klipp) {
    return (
      <div className="bd">
        <h1>Bedöm rörlighet</h1>
        <p>Välj ett rekonstruerat klipp. Du ser samma scen filmad på två sätt och väljer vilken som är mer rörlig och expansiv.</p>
        <ul>{(lista ?? []).map(x => <li key={x.id}><a href={`#bedom/${x.id}`} onClick={() => setTimeout(() => location.reload(), 0)}>{x.id}</a></li>)}</ul>
      </div>
    )
  }
  if (data?.fel) return <div className="bd"><p className="bd-fel">{data.fel}</p></div>
  if (!modell) return <div className="bd"><p>läser …</p></div>
  const pct = x => (x == null ? '–' : `${Math.round(x * 100)} %`)
  return (
    <div className="bd">
      <header>
        <h1>Vilken är mer rörlig och expansiv?</h1>
        <span className="bd-stat">
          {modell.mina.length} bedömningar · modellen håller med dig om {pct(modell.o?.andel)}
          {modell.kv ? ` · på bedömningar den inte tränats på: ${pct(modell.kv.andel)}` : ' · korsvalidering från 20 bedömningar'}
        </span>
      </header>
      {par ? (
        <>
          <p className="bd-scen">Scen {par.scen + 1}: {bas.scener[par.scen].text}</p>
          <div className="bd-par">
            <figure><Duk manus={manusA} /><button onClick={() => svara('a')}>← den här</button></figure>
            <div className="bd-mitt">
              <button onClick={() => svara('lika')}>↓ lika</button>
              <button className="dim" onClick={() => svara('hoppa')}>hoppa (mellanslag)</button>
              <button className="dim" onClick={() => setVisaVarfor(v => !v)}>{visaVarfor ? 'dölj' : 'visa'} vad som skiljer</button>
            </div>
            <figure><Duk manus={manusB} /><button onClick={() => svara('b')}>den här →</button></figure>
          </div>
          {visaVarfor && (
            <div className="bd-varfor">
              <p><b>Vänster:</b> {beskriv(par.a)} · steg {par.a.steg.toFixed(1)}</p>
              <p><b>Höger:</b> {beskriv(par.b)} · steg {par.b.steg.toFixed(1)}</p>
              <p className="dim">Parets sort: {par.sort}. Modellen tror att {par.a.u > par.b.u ? 'vänster' : 'höger'} är mer rörlig.</p>
            </div>
          )}
        </>
      ) : <p>Inga fler par i det här klippet.</p>}
    </div>
  )
}
