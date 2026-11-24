import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { trana, overens, korsvalidera, skala, nastaPar } from '../../kalibrering/modell.mjs'
import { EGENSKAPER, KLIPP_NAMN } from '../../kalibrering/egenskaper.mjs'
import { GRIND } from '../../kalibrering/vertikaler.mjs'
import './kalibrering.css'

// Kalibrering: varje central vertikal tränas för sig på parvisa bedömningar av riktiga scener,
// innan kombinerade vertikaler låses upp. Jev jämförs mot samma bedömningar.
//   Bedöm  två riktiga scener sida vid sida, vilken har mer av X?
//   Skala  biblioteket ordnat efter modellen, så att ordningen kan synas av
//   Modell vikterna (varför) och hur väl modellen håller på klipp den inte sett
//   Jev    samma fråga till Jev, och hur ofta Jev och människan är överens

const FORKLARING = Object.fromEntries([...EGENSKAPER, ['scener_per_s', 'scener per sekund'], ['utsnittsbyten', 'andel scenbyten med nytt utsnitt']])

export default function Kalibrering() {
  const [kal, setKal] = useState(null)
  const [vid, setVid] = useState(() => location.hash.split('/')[1] || 'rorlighet')
  const [flik, setFlik] = useState('bedom')
  const [bed, setBed] = useState({})
  const ladda = useCallback(() => fetch('/__kalib').then(r => r.json()).then(setKal), [])
  useEffect(() => { ladda() }, [ladda])
  useEffect(() => {
    if (!kal) return
    Promise.all(kal.vertikaler.map(v => fetch(`/__bedomningar/${v.id}`).then(r => r.json()).then(b => [v.id, b]))).then(x => setBed(Object.fromEntries(x)))
  }, [kal])
  const valjV = id => { setVid(id); history.replaceState(null, '', `#kalibrering/${id}`) }

  // Modell och mått per central vertikal
  const status = useMemo(() => {
    if (!kal) return {}
    const ut = {}
    for (const v of kal.vertikaler.filter(x => x.niva === 'central')) {
      const items = kal.items[v.enhet] ?? []
      const namn = v.egenskaper?.length ? v.egenskaper : v.enhet === 'klipp' ? KLIPP_NAMN : EGENSKAPER.map(e => e[0])
      const b = (bed[v.id] ?? []).filter(x => x.val !== 'hoppa')
      const start = trana({ items, bedomningar: [], namn, start: v.start })
      const mod = trana({ items, bedomningar: b, namn, start: v.start })
      const cv = b.length >= 20 ? korsvalidera({ items, bedomningar: b, namn, start: v.start }) : { andel: null, n: 0 }
      const klipp = new Set(b.flatMap(x => [x.a.split('#')[0], x.b.split('#')[0]])).size
      const klar = b.length >= GRIND.minBedomningar && (cv.andel ?? 0) >= GRIND.minOverens && klipp >= GRIND.minKlipp
      ut[v.id] = { v, items, namn, b, start, mod, cv, startOverens: overens(start, items, b), klipp, klar }
    }
    return ut
  }, [kal, bed])

  if (!kal) return <div className="kal"><p className="dim pad">läser biblioteket …</p></div>
  const v = kal.vertikaler.find(x => x.id === vid) ?? kal.vertikaler[0]
  const st = status[v.id]
  const last = x => x.niva === 'kombinerad' && !(x.byggerPa ?? []).every(id => status[id]?.klar)

  return (
    <div className="kal">
      <header className="kal-top">
        <b>Kalibrering</b>
        <span className="dim">{kal.items.scen.length} scener · {kal.items.klipp.length} klipp</span>
        <nav className="kal-vert">
          {kal.vertikaler.map(x => (
            <button key={x.id} className={`${x.id === v.id ? 'on' : ''} ${last(x) ? 'last' : ''}`} onClick={() => valjV(x.id)} title={last(x) ? `Låst tills ${x.byggerPa.join(', ')} är kalibrerade${x.kraver ? `. Kräver också ${x.kraver}` : ''}` : x.fraga}>
              {last(x) && <span className="las">🔒</span>}{x.namn}
              {status[x.id] && <span className={`bricka ${status[x.id].klar ? 'klar' : ''}`}>{status[x.id].b.length}</span>}
            </button>
          ))}
        </nav>
        <a className="kal-lank" href="#bibliotek">bibliotek</a>
      </header>

      {v.niva === 'kombinerad' ? <Kombinerad v={v} status={status} last={last(v)} /> : (
        <div className="kal-main">
          <aside className="kal-status">
            <h3>{v.namn}</h3>
            <p className="dim">{v.fraga}</p>
            <div className="kal-andar"><span>{v.andar[0]}</span><span>{v.andar[1]}</span></div>
            <Matare namn="bedömningar" varde={st.b.length} mal={GRIND.minBedomningar} />
            <Matare namn="klipp med i bedömningarna" varde={st.klipp} mal={GRIND.minKlipp} />
            <Matare namn="modellen överens på osedda klipp" varde={st.cv.andel} mal={GRIND.minOverens} procent />
            <dl className="kal-tal">
              <dt>startvikterna överens</dt><dd>{fmtP(st.startOverens.andel)} <span className="dim">({st.startOverens.n} par)</span></dd>
              <dt>tränad, på allt</dt><dd>{fmtP(overens(st.mod, st.items, st.b).andel)}</dd>
              <dt>korsvaliderad</dt><dd>{fmtP(st.cv.andel)} {st.cv.n ? <span className="dim">({st.cv.n} par)</span> : <span className="dim">(från 20 bedömningar)</span>}</dd>
            </dl>
            <p className={`kal-grind ${st.klar ? 'klar' : ''}`}>{st.klar ? 'Kalibrerad: får ingå i kombinerade vertikaler.' : `Grind: ${GRIND.minBedomningar} bedömningar, ${GRIND.minKlipp} klipp och minst ${Math.round(GRIND.minOverens * 100)} % överens på osedda klipp.`}</p>
            <nav className="kal-flikar">
              {[['bedom', 'Bedöm'], ['skala', 'Skala'], ['modell', 'Modell'], ['jev', 'Jev']].map(([k, n]) => <button key={k} className={flik === k ? 'on' : ''} onClick={() => setFlik(k)}>{n}</button>)}
            </nav>
          </aside>
          <section className="kal-yta">
            {flik === 'bedom' && <Bedom st={st} laggTill={b => setBed(x => ({ ...x, [v.id]: [...(x[v.id] ?? []), b] }))} />}
            {flik === 'skala' && <Skala st={st} />}
            {flik === 'modell' && <Modell st={st} />}
            {flik === 'jev' && <Jev st={st} jev={kal.jev} ladda={ladda} />}
          </section>
        </div>
      )}
    </div>
  )
}

const fmtP = x => (x == null ? '–' : `${Math.round(x * 100)} %`)
function Matare({ namn, varde, mal, procent }) {
  const andel = varde == null ? 0 : Math.min(1, varde / mal)
  return (
    <div className="kal-matare">
      <div className="rad"><span>{namn}</span><b>{procent ? fmtP(varde) : varde ?? '–'} <span className="dim">/ {procent ? fmtP(mal) : mal}</span></b></div>
      <i><b style={{ width: `${andel * 100}%` }} className={andel >= 1 ? 'klar' : ''} /></i>
    </div>
  )
}

// En scen (eller ett klipp) som spelas i loop, ljudlöst.
function Spelare({ it, etikett, vald }) {
  const ref = useRef(null)
  useEffect(() => {
    const v = ref.current
    if (!v) return
    const borja = () => { v.currentTime = it.start + 0.02; v.play().catch(() => {}) }
    const tid = () => { if (v.currentTime >= it.slut - 0.05 || v.currentTime < it.start - 0.1) borja() }
    v.addEventListener('loadedmetadata', borja)
    v.addEventListener('timeupdate', tid)
    if (v.readyState >= 1) borja()
    return () => { v.removeEventListener('loadedmetadata', borja); v.removeEventListener('timeupdate', tid) }
  }, [it])
  return (
    <figure className={`kal-spelare ${vald ? 'vald' : ''}`}>
      <div className="skarm">
        <video ref={ref} src={`/__video/${encodeURIComponent(it.klipp)}`} muted playsInline poster={it.bild ? `/__data/${it.bild}` : undefined} />
        <span className="etikett">{etikett}</span>
      </div>
      <figcaption>
        <a href={`#bibliotek/${encodeURIComponent(it.klipp)}`} target="_blank" rel="noreferrer">@{it.konto}</a>
        {it.i != null && <span className="dim"> · scen {it.i + 1} · {(it.slut - it.start).toFixed(1)} s</span>}
      </figcaption>
    </figure>
  )
}

function Bedom({ st, laggTill }) {
  const [par, setPar] = useState(null)
  const [vald, setVald] = useState(null)
  const t0 = useRef(performance.now())
  const byId = useMemo(() => new Map(st.items.map(it => [it.id, it])), [st.items])
  const nytt = useCallback(() => {
    setPar(nastaPar(st.mod, st.items, st.b))
    setVald(null)
    t0.current = performance.now()
  }, [st])
  useEffect(() => { if (!par) nytt() }, [par, nytt])
  const svara = useCallback(async val => {
    if (!par || vald) return
    setVald(val)
    const b = { a: par.a, b: par.b, val, ms: Math.round(performance.now() - t0.current) }
    await fetch(`/__bedom/${st.v.id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) })
    if (val !== 'hoppa') laggTill(b)
    setTimeout(() => setPar(null), 180)
  }, [par, vald, st.v.id, laggTill])
  useEffect(() => {
    const k = e => {
      if (e.key === 'ArrowLeft') svara('a')
      else if (e.key === 'ArrowRight') svara('b')
      else if (e.key === 'ArrowDown') svara('lika')
      else if (e.key === ' ') { e.preventDefault(); svara('hoppa') }
    }
    addEventListener('keydown', k)
    return () => removeEventListener('keydown', k)
  }, [svara])
  if (!par) return <p className="dim">väljer par …</p>
  const A = byId.get(par.a)
  const B = byId.get(par.b)
  return (
    <div className="kal-bedom">
      <p className="kal-fraga">{st.v.fraga}</p>
      <div className="kal-par">
        <Spelare it={A} etikett="A" vald={vald === 'a'} />
        <div className="kal-knappar">
          <button onClick={() => svara('a')}>← A har mer</button>
          <button onClick={() => svara('lika')}>↓ lika</button>
          <button onClick={() => svara('b')}>B har mer →</button>
          <button className="hoppa" onClick={() => svara('hoppa')}>hoppa (mellanslag)</button>
          <p className="dim">Valt för att modellen är osäker på just det här paret.</p>
        </div>
        <Spelare it={B} etikett="B" vald={vald === 'b'} />
      </div>
    </div>
  )
}

function Skala({ st }) {
  const sk = useMemo(() => skala(st.mod, st.items), [st])
  const sorterad = st.items.slice().sort((a, b) => sk.get(a.id).u - sk.get(b.id).u)
  return (
    <div className="kal-skala">
      <p className="dim">Biblioteket i modellens ordning, från {st.v.andar[0]} till {st.v.andar[1]}. Syns ordningen fel någonstans är det ett bra par att bedöma.</p>
      <div className="kal-rutnat">
        {sorterad.map(it => (
          <a key={it.id} className="kal-ruta" href={`#bibliotek/${encodeURIComponent(it.klipp)}`} target="_blank" rel="noreferrer" title={it.text}>
            {it.bild && <img src={`/__data/${it.bild}`} alt="" loading="lazy" />}
            <span className="steg">{sk.get(it.id).steg.toFixed(1)}</span>
          </a>
        ))}
      </div>
    </div>
  )
}

function Modell({ st }) {
  const vikter = st.namn.map((n, j) => ({ n, w: st.mod.w[j], w0: st.start.w[j] })).sort((a, b) => Math.abs(b.w) - Math.abs(a.w))
  const max = Math.max(0.1, ...vikter.map(x => Math.abs(x.w)), ...vikter.map(x => Math.abs(x.w0)))
  return (
    <div className="kal-modell">
      <p className="dim">Vad modellen lägger vikt vid, i standardiserade enheter. Ljus stapel är startvikten (vertikalens definition), mörk är den tränade. Bedömningarna flyttar vikterna bort från definitionen när människan ser något annat.</p>
      <table>
        <tbody>
          {vikter.map(x => (
            <tr key={x.n}>
              <td className="namn" title={FORKLARING[x.n]}>{x.n}</td>
              <td className="stapel">
                <span className="noll" />
                <i className="start" style={x.w0 >= 0 ? { left: '50%', width: `${(x.w0 / max) * 50}%` } : { right: '50%', width: `${(-x.w0 / max) * 50}%` }} />
                <i className="tranad" style={x.w >= 0 ? { left: '50%', width: `${(x.w / max) * 50}%` } : { right: '50%', width: `${(-x.w / max) * 50}%` }} />
              </td>
              <td className="tal">{x.w.toFixed(2)}</td>
              <td className="dim">{FORKLARING[x.n]}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {st.cv.delar?.length > 0 && <p className="dim">Korsvalidering per del: {st.cv.delar.map(d => fmtP(d)).join(' · ')}</p>}
    </div>
  )
}

function Jev({ st, jev, ladda }) {
  const [kriterier, setKriterier] = useState(st.v.kriterier.join('\n'))
  const [kor, setKor] = useState(null)
  const [res, setRes] = useState(null)
  const spara = async () => {
    await fetch(`/__vertikal/${st.v.id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ kriterier: kriterier.split('\n').map(s => s.trim()).filter(Boolean) }) })
    ladda()
  }
  const korJev = async typ => {
    setKor(typ)
    const r = await (await fetch(`/__jev/${st.v.id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ typ }) })).json()
    setKor(null)
    setRes({ typ, ...r })
  }
  // överens med människan
  let matt = null
  if (res?.svar && !res.fel) {
    if (res.typ === 'par') {
      const m = new Map(st.b.map(b => [`${b.a}|${b.b}`, b.val]))
      const jamf = res.svar.filter(s => m.has(`${s.a}|${s.b}`) && m.get(`${s.a}|${s.b}`) !== 'lika' && s.val !== 'lika')
      matt = { andel: jamf.filter(s => s.val === m.get(`${s.a}|${s.b}`)).length / Math.max(1, jamf.length), n: jamf.length }
    } else {
      const S = new Map(res.svar.map(s => [s.id, s.score]))
      const jamf = st.b.filter(b => b.val !== 'lika' && S.has(b.a) && S.has(b.b) && S.get(b.a) !== S.get(b.b))
      matt = { andel: jamf.filter(b => (S.get(b.a) > S.get(b.b)) === (b.val === 'a')).length / Math.max(1, jamf.length), n: jamf.length }
    }
  }
  return (
    <div className="kal-jev">
      {!jev.nyckel && (
        <div className="kal-info">
          <b>Jev är inte anslutet.</b> Lägg nyckeln i <code>app/.env.local</code> som <code>TYPESAFE_API_KEY=…</code> (filen läses bara av servern, nyckeln når aldrig webbläsaren). Modell: <code>{jev.modell}</code>.
        </div>
      )}
      <p className="dim">Jev får scenen som text (det som mätts) och vertikalens nivåer. Formuleringen av nivåerna är det som kalibreras: ändra, kör igen och se om Jev och människan blir mer överens. Svar sparas per formulering, så samma fråga betalas inte två gånger.</p>
      <label className="kal-kriterier">
        <span>Nivåer, lägst först, en per rad (2–10){st.v.andrad && <em> · ändrade</em>}</span>
        <textarea rows={Math.max(5, st.v.kriterier.length + 1)} value={kriterier} onChange={e => setKriterier(e.target.value)} />
      </label>
      <div className="kal-jev-knappar">
        <button onClick={spara} disabled={kriterier === st.v.kriterier.join('\n')}>spara nivåerna</button>
        <button onClick={() => korJev('par')} disabled={!jev.nyckel || !st.b.length || kor}>{kor === 'par' ? 'kör …' : `Jev på bedömda par (${Math.min(200, st.b.length)})`}</button>
        <button onClick={() => korJev('score')} disabled={!jev.nyckel || !st.b.length || kor}>{kor === 'score' ? 'kör …' : 'Jev-score på bedömda scener'}</button>
      </div>
      {res?.fel && <p className="fel">{res.fel}</p>}
      {matt && <p className="kal-res">Jev och människan överens: <b>{fmtP(matt.andel)}</b> <span className="dim">({matt.n} jämförelser, {res.svar.filter(s => s.cache).length} ur sparat)</span>. Tränad modell, korsvaliderad: <b>{fmtP(st.cv.andel)}</b>.</p>}
      <details>
        <summary>Exempel på vad Jev får se</summary>
        <pre>{st.items[0]?.text}</pre>
      </details>
    </div>
  )
}

function Kombinerad({ v, status, last }) {
  return (
    <div className="kal-komb">
      <h3>{v.namn}</h3>
      <p>{v.fraga}</p>
      {last ? (
        <>
          <p><b>Låst.</b> Kombinerade vertikaler öppnas när de centrala de bygger på är kalibrerade, så att det går att se vad som kommer från vilken.</p>
          <ul>{v.byggerPa.map(id => <li key={id}>{status[id]?.v.namn}: {status[id]?.klar ? 'kalibrerad' : `${status[id]?.b.length ?? 0} bedömningar, ${fmtP(status[id]?.cv.andel)} överens`}</li>)}</ul>
          {v.kraver && <p>Kräver också: {v.kraver}.</p>}
        </>
      ) : <p>Öppen. Bedömning av kombinationen byggs när den första låses upp.</p>}
    </div>
  )
}
