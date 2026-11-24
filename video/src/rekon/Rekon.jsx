import { useEffect, useRef, useState } from 'react'
import { Spelare } from '../forandring/motor/spelare'
import './rekon.css'

// Rekonstruktionen sida vid sida: originalet (video) och manuset som motorn spelar, synkade.
// #rekon/<id> visar ett klipp; utan id en lista över rekonstruerade klipp.
// Rekonstruktionsgraden (rekon/mat.mjs) visas om den är mätt.

const W = 300
const H = 534

export default function Rekon() {
  const id = decodeURIComponent(location.hash.split('/')[1] ?? '')
  const [lista, setLista] = useState(null)
  const [manus, setManus] = useState(null)
  const [grad, setGrad] = useState(null)
  const [fel, setFel] = useState(null)
  const [t, setT] = useState(0)
  const [spelar, setSpelar] = useState(false)
  const canvas = useRef(null)
  const video = useRef(null)
  const sp = useRef(null)

  useEffect(() => {
    if (!id) { fetch('/__rekon').then(r => r.json()).then(setLista).catch(e => setFel(e.message)); return }
    fetch(`/__data/rekon/${id}/manus.json`).then(r => (r.ok ? r.json() : Promise.reject(new Error('manus saknas: npm run rekon -- ' + id)))).then(setManus).catch(e => setFel(e.message))
    fetch(`/__data/rekon/${id}/grad.json`).then(r => (r.ok ? r.json() : null)).then(setGrad).catch(() => {})
  }, [id])

  useEffect(() => {
    if (!manus) return
    const s = new Spelare(canvas.current, { bredd: W, hojd: H })
    sp.current = s
    window.__spelare = s
    s.load(manus)
    s.seek(0)
    return () => s.dispose()
  }, [manus])

  // videon är klockan; motorn följer den
  useEffect(() => {
    if (!manus) return
    let raf
    const loop = () => {
      const v = video.current
      if (v && sp.current) {
        const tt = Math.min(v.currentTime, sp.current.dur - 1e-3)
        sp.current.seek(tt)
        setT(tt)
      }
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [manus])

  const spela = () => {
    const v = video.current
    if (v.paused) { v.play(); setSpelar(true) } else { v.pause(); setSpelar(false) }
  }
  window.__rekonSok = tt => { if (video.current) video.current.currentTime = tt }

  if (!id) {
    return (
      <div className="rk">
        <h1>Rekonstruktioner</h1>
        {fel && <p className="rk-fel">{fel}</p>}
        <ul>{(lista ?? []).map(x => <li key={x.id}><a href={`#rekon/${x.id}`}>{x.id}</a> {x.grad != null && <span>· {Math.round(x.grad * 100)} %</span>}</li>)}</ul>
      </div>
    )
  }
  const scen = manus ? manus.scener.findIndex((_, i) => { let a = 0; for (let k = 0; k <= i; k++) a += manus.scener[k].tid; return t < a }) : -1
  return (
    <div className="rk">
      <header>
        <a href="#rekon">← alla</a>
        <h1>{id}</h1>
        {grad && <span className="rk-grad">rekonstruktionsgrad {Math.round(grad.total * 100)} %</span>}
        <a href={`#v/${id}`} onClick={() => setTimeout(() => location.reload(), 0)}>dra i reglaget →</a>
      </header>
      {fel && <p className="rk-fel">{fel}</p>}
      <div className="rk-par">
        <figure>
          <video ref={video} src={`/__video/${id}`} width={W} height={H} playsInline muted onEnded={() => setSpelar(false)} />
          <figcaption>original</figcaption>
        </figure>
        <figure>
          <canvas ref={canvas} style={{ width: W, height: H }} />
          <figcaption>rekonstruktion</figcaption>
        </figure>
        <aside>
          <button onClick={spela}>{spelar ? 'paus' : 'spela'}</button>
          <span className="rk-tid">{t.toFixed(1)} s · scen {scen + 1}</span>
          <input type="range" min="0" max={manus ? manus.scener.reduce((a, s) => a + s.tid, 0) : 1} step="0.05" value={t} onChange={e => { video.current.currentTime = +e.target.value }} />
          {grad && (
            <table>
              <tbody>{Object.entries(grad.matt).map(([k, v]) => <tr key={k} className={v.varde >= 0.9 ? 'bra' : v.varde >= 0.75 ? '' : 'svag'}><td>{v.namn}</td><td>{v.varde == null ? '–' : `${Math.round(v.varde * 100)} %`}</td></tr>)}</tbody>
            </table>
          )}
          {manus?.antaget?.length > 0 && <details><summary>antaget ({manus.antaget.length})</summary><ul>{manus.antaget.map((a, i) => <li key={i}>{a}</li>)}</ul></details>}
          {manus && <p className="rk-text">{manus.scener[Math.max(0, scen)]?.text}</p>}
        </aside>
      </div>
    </div>
  )
}
