import { useEffect, useMemo, useState } from 'react'
import './brygga.css'

// Bryggan: motorns egen mätning jämförd med analysen av samma manus, renderat och analyserat
// med exakt samma pipeline som riktiga klipp (npm run brygga). Visar vad som håller, vad som
// inte gör det och varför, och korrektionen som gör motorns tal jämförbara med biblioteket.

const pct = x => (x == null ? '–' : `${Math.round(x * 100)} %`)
const fx = (x, d = 2) => (x == null ? '–' : Number(x).toFixed(d))

function Kort({ titel, varde, under, bra }) {
  return (
    <div className={`br-kort ${bra === true ? 'bra' : bra === false ? 'svag' : ''}`}>
      <span className="titel">{titel}</span>
      <b>{varde}</b>
      {under && <span className="under">{under}</span>}
    </div>
  )
}

function Spridning({ e }) {
  const W = 300
  const H = 300
  const M = 30
  const par = e.par ?? []
  if (!par.length) return <p className="dim">Inga par.</p>
  const max = Math.max(1e-6, ...par.flat().filter(Number.isFinite))
  const min = Math.min(0, ...par.flat().filter(Number.isFinite))
  const X = v => M + ((v - min) / (max - min)) * (W - M * 1.5)
  const Y = v => H - M - ((v - min) / (max - min)) * (H - M * 1.5)
  return (
    <svg width={W} height={H} className="br-plot">
      <line x1={X(min)} y1={Y(min)} x2={X(max)} y2={Y(max)} className="lika" />
      {e.b != null && <line x1={X(min)} y1={Y(e.a + e.b * min)} x2={X(max)} y2={Y(e.a + e.b * max)} className="anp" />}
      {par.map(([n, a], i) => <circle key={i} cx={X(n)} cy={Y(a)} r={3.2} />)}
      <text x={W - M / 2} y={H - 8} textAnchor="end">motorn →</text>
      <text x={8} y={M - 10}>↑ analysen</text>
    </svg>
  )
}

export default function Brygga() {
  const [rap, setRap] = useState(null)
  const [korr, setKorr] = useState(null)
  const [vald, setVald] = useState('kamera')
  const [manus, setManus] = useState(null)
  useEffect(() => {
    fetch('/__data/brygga/rapport.json').then(r => (r.ok ? r.json() : null)).then(setRap)
    fetch('/__data/brygga/korrektion.json').then(r => (r.ok ? r.json() : null)).then(setKorr)
  }, [])
  const egenskaper = useMemo(() => {
    if (!rap || !korr) return []
    const par = Object.fromEntries(rap.egenskaper.map(e => [e.namn, e.par]))
    return Object.entries(korr.egenskaper).map(([namn, k]) => ({ namn, ...k, par: k.kalla === 'matchad' ? null : par[namn] }))
      .sort((a, b) => Number(b.giltig) - Number(a.giltig) || (b.r ?? -1) - (a.r ?? -1))
  }, [rap, korr])
  if (!rap) return <div className="br"><p className="dim pad">Ingen rapport ännu. Kör <code>npm run brygga</code> i app/.</p></div>
  const valdE = egenskaper.find(e => e.namn === vald)
  const m = manus && rap.manus.find(x => x.id === manus)

  return (
    <div className="br">
      <header className="br-top">
        <b>Bryggan</b>
        <span className="dim">motorns mätning ↔ analysen av samma manus, renderat · {rap.manus.length} manus, {rap.scener.n} scenpar · {new Date(rap.skapad).toLocaleString('sv-SE')}</span>
        <nav><a href="#kalibrering">kalibrering</a> · <a href="#bibliotek">bibliotek</a> · <a href="#v">reglaget</a></nav>
      </header>

      <section className="br-sektion">
        <h2>Mäter de samma sak?</h2>
        <div className="br-kortrad">
          <Kort titel="Kameran, per scen" varde={`r ${fx(rap.matchad.kamera.r)}`} under={`lutning ${fx(rap.matchad.kamera.b)} · ${rap.matchad.kamera.n} scener`} bra={rap.matchad.kamera.r >= 0.8} />
          <Kort titel="Kameran, per ruta" varde={`r ${fx(rap.rutor.kamera.dx.r)}`} under={`dx · dy ${fx(rap.rutor.kamera.dy.r)} · skala ${fx(rap.rutor.kamera.skala.r)}`} bra={rap.rutor.kamera.dx.r >= 0.8} />
          <Kort titel="Personernas rörelse" varde={`r ${fx(rap.matchad.motiv.r)}`} under={`lutning ${fx(rap.matchad.motiv.b)} · där båda ser personen`} bra={rap.matchad.motiv.r >= 0.5} />
          <Kort titel="Scengränser" varde={pct(rap.scener.granserHittade)} under="klipp och övergångar som analysen hittar" bra={rap.scener.granserHittade >= 0.85} />
          <Kort titel="Utsnitt lika" varde={pct(rap.scener.utsnittLika)} under="motorns utsnitt = analysens" bra={rap.scener.utsnittLika >= 0.7} />
        </div>
        <h2>Ser analysen dockorna?</h2>
        <p className="dim">Det här mäter hur realistisk renderingen är, inte om måtten stämmer. Där analysen inte ser dockan kan bryggan inte jämföra.</p>
        <div className="br-kortrad">
          <Kort titel="Kropp (Pose)" varde={pct(rap.detektion.pose)} bra={rap.detektion.pose >= 0.8} />
          <Kort titel="Ansikte" varde={pct(rap.detektion.ansikte)} bra={rap.detektion.ansikte >= 0.8} />
          <Kort titel="Person (COCO)" varde={pct(rap.detektion.coco)} bra={rap.detektion.coco >= 0.8} />
          <Kort titel="Räknas som person" varde={pct(rap.detektion.efterFilter)} under="kropp + ansikte eller COCO" bra={rap.detektion.efterFilter >= 0.8} />
          <Kort titel="Punkternas fel" varde={fx(rap.rutor.punktFel, 3)} under="bildhöjder, där båda ser kroppen" />
        </div>
      </section>

      <section className="br-sektion br-korr">
        <div>
          <h2>Korrektionen</h2>
          <p className="dim">Motorns tal översätts till analysens skala som <code>a + b · motor</code>, bara där sambandet håller (r ≥ {korr?.gräns.minR}, minst {korr?.gräns.minN} par). Klicka för att se paren.</p>
          <table className="br-tabell">
            <thead><tr><th>egenskap</th><th>r</th><th>n</th><th>a</th><th>b</th><th /></tr></thead>
            <tbody>
              {egenskaper.map(e => (
                <tr key={e.namn} className={`${e.giltig ? 'giltig' : ''} ${vald === e.namn ? 'vald' : ''}`} onClick={() => setVald(e.namn)}>
                  <td className="namn">{e.namn}</td>
                  <td>{fx(e.r)}</td>
                  <td>{e.n}</td>
                  <td>{fx(e.a, 3)}</td>
                  <td>{fx(e.b)}</td>
                  <td>{e.giltig ? <span className="ok">giltig</span> : <span className="dim">{e.orsak}</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="br-plotyta">
          <h3>{vald}</h3>
          {valdE?.par ? <Spridning e={valdE} /> : <p className="dim">Mätt på rutor där båda ser samma sak; paren per scen finns i rapporten under <code>matchad</code>.</p>}
          <p className="dim">Grå linje: lika. Blå: anpassningen.</p>
        </div>
      </section>

      <section className="br-sektion">
        <h2>Manusen</h2>
        <div className="br-manuslista">
          {rap.manus.map(x => (
            <button key={x.id} className={manus === x.id ? 'on' : ''} onClick={() => setManus(manus === x.id ? null : x.id)}>
              {x.id.replace('nonna-', '')}<span className="dim"> · {x.scenerAnalys}/{x.scenerMotor} sc · {pct(x.personHittad)}</span>
            </button>
          ))}
        </div>
        {m && (
          <div className="br-manus">
            <video src={`/__video/${encodeURIComponent(m.id)}`} controls muted loop playsInline width={180} height={320} />
            <table className="br-tabell">
              <thead><tr><th /><th>tid</th><th>utsnitt motor → analys</th><th>kamera motor</th><th>kamera analys</th><th>motiv motor → analys</th></tr></thead>
              <tbody>
                {m.scener.map(s => (
                  <tr key={s.i}>
                    <td>{s.bild && <img src={`/__data/${s.bild}`} alt="" />}</td>
                    <td>{s.start.toFixed(1)}–{s.slut.toFixed(1)}</td>
                    <td className={s.utsnitt[0] === s.utsnitt[1] ? 'lika' : 'olika'}>{s.utsnitt.join(' → ')}</td>
                    <td>{s.kamera[0].join(', ')}</td>
                    <td>{s.kamera[1].join(', ')}</td>
                    <td>{fx(s.aktivitet[0].motiv, 3)} → {fx(s.aktivitet[1].motiv, 3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="dim">Gränser: {m.granser.map(g => `${g.t} s ${g.typ} ${g.hittad ? '✓' : `✗ (${g.typAnalys ?? 'inget'})`}`).join(' · ')}</div>
          </div>
        )}
      </section>
    </div>
  )
}
