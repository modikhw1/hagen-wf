import { useEffect, useMemo, useRef, useState } from 'react'
import './bank.css'

const BESLUT = [
  { id: 'med', text: 'ta med', tangent: '1' },
  { id: 'osaker', text: 'osäker', tangent: '2' },
  { id: 'inte', text: 'ta inte med', tangent: '3' },
]
const antal = v => v == null ? '–' : v.toLocaleString('sv-SE')
const procent = v => v == null ? '–' : `${Math.round(v * 100)} %`
const poang = v => v == null ? '–' : v.toLocaleString('sv-SE', { maximumFractionDigits: 2 })
const typnamn = typ => typ === 'okand' ? 'Okänd typ' : typ.replaceAll('_', ' ')
const jaNej = v => v == null ? '–' : v ? 'Ja' : 'Nej'
const tydlig = bed => bed?.beslut === 'med' || bed?.beslut === 'inte'
const oenig = (k, bed) => tydlig(bed) && (bed.beslut === 'med') !== k.valt

async function hamtaJson(url, signal, saknas) {
  const svar = await fetch(url, { signal, cache: 'no-store' })
  if (svar.status === 404 && saknas !== undefined) return saknas
  if (!svar.ok) throw new Error('Kunde inte läsa bankens data. Försök igen.')
  if (!svar.headers.get('content-type')?.includes('application/json')) {
    throw new Error('Bankens lokala endpoints är inte tillgängliga. Servern behöver laddas om.')
  }
  return svar.json()
}

function BankKort({ klipp: k, kalla, bedomning, status, aktiv, registrera, aktivera, spara, version }) {
  const kort = useRef(null)
  const video = useRef(null)
  const [synlig, setSynlig] = useState(false)
  const [sallning, setSallning] = useState(null)
  const [sallStatus, setSallStatus] = useState('laddar')
  const [videofel, setVideofel] = useState(false)
  const [reservvideo, setReservvideo] = useState(false)
  const [videoladdar, setVideoladdar] = useState(false)

  // Ladda video och sållning nära skärmen, även när banken växer under natten.
  useEffect(() => {
    const observator = new IntersectionObserver(poster => {
      for (const post of poster) {
        if (post.isIntersecting) setSynlig(true)
        else video.current?.pause()
      }
    }, { rootMargin: '300px' })
    observator.observe(kort.current)
    return () => observator.disconnect()
  }, [])

  useEffect(() => {
    if (!synlig) return
    const kontroll = new AbortController()
    setSallStatus('laddar')
    hamtaJson(`/__data/bank/sallning/${encodeURIComponent(k.id)}.json`, kontroll.signal, null)
      .then(data => {
        setSallning(data)
        setSallStatus(data ? 'klar' : 'saknas')
      })
      .catch(e => {
        if (e.name !== 'AbortError') setSallStatus('fel')
      })
    return () => kontroll.abort()
  }, [k.id, synlig, version])

  const spela = () => {
    if (video.current && !videofel) video.current.play().catch(() => {})
  }
  const bytVideo = () => {
    if (reservvideo) {
      setVideofel(true)
      setVideoladdar(false)
    } else {
      setReservvideo(true)
      setVideoladdar(true)
    }
  }
  const oenighet = oenig(k, bedomning)

  return (
    <article
      ref={element => {
        kort.current = element
        registrera(k.id, element)
      }}
      className={`bk-kort${aktiv ? ' bk-aktiv' : ''}`}
      tabIndex={aktiv ? 0 : -1}
      data-klipp-id={k.id}
      aria-label={`Klipp ${k.id}`}
      aria-keyshortcuts="ArrowLeft ArrowRight ArrowUp ArrowDown 1 2 3"
      onFocus={() => aktivera(k.id)}
      onClick={e => {
        aktivera(k.id)
        if (!e.target.closest('button, input, a, video, label')) kort.current.focus({ preventScroll: true })
      }}
      onMouseEnter={spela}
      onMouseLeave={() => video.current?.pause()}
    >
      <div className="bk-korttopp">
        <div className="bk-video">
          <video
            ref={video}
            src={synlig ? `${reservvideo ? '/__bank/video/' : '/__video/'}${encodeURIComponent(k.id)}` : undefined}
            preload="metadata"
            muted
            loop
            playsInline
            controls
            aria-label={`Video från @${k.konto}`}
            onError={bytVideo}
            onLoadedMetadata={e => {
              // H.265 kan ge ett spelbart ljudspår utan bild i vissa webbläsare.
              if (!e.currentTarget.videoWidth) bytVideo()
              else {
                setVideoladdar(false)
                e.currentTarget.currentTime = Math.min(0.1, e.currentTarget.duration / 2)
              }
            }}
            onLoadedData={() => {
              if (kort.current?.matches(':hover')) spela()
            }}
          />
          {videoladdar && <span className="bk-videofel" role="status">Förbereder förhandsvisning…</span>}
          {videofel && <span className="bk-videofel">Videon kunde inte laddas</span>}
        </div>
        <div className="bk-intro">
          <span className={`bk-urval ${k.valt ? 'bk-vald' : ''}`}>{k.valt ? 'Valt av urvalet' : 'Ej valt av urvalet'}</span>
          <h2>@{k.konto || 'okänt konto'}</h2>
          <span className="bk-typ">{typnamn(k.typ)}</span>
          <p>{sallning?.innehall || k.innehall || 'Beskrivning saknas ännu.'}</p>
          <div className="bk-kallinfo">
            <span>{k.langd == null ? 'Okänd längd' : `${antal(Math.round(k.langd))} s`}</span>
            {kalla?.datum && <time dateTime={kalla.datum}>{kalla.datum}</time>}
            {kalla?.url?.startsWith('https://') && <a href={kalla.url} target="_blank" rel="noreferrer">Källklipp ↗</a>}
          </div>
        </div>
      </div>

      <dl className="bk-matt">
        <div><dt>Poäng</dt><dd>{poang(k.poang)}</dd></div>
        <div><dt>Rekonbar</dt><dd>{procent(k.rekonbar)}</dd></div>
        <div title="Percentil inom kontot, baserad på visningar och gillanden"><dt>Engagemang</dt><dd>{procent(k.engagemang)}</dd></div>
        <div><dt>Visningar</dt><dd>{antal(k.visningar ?? kalla?.visningar)}</dd></div>
      </dl>
      <p className="bk-mattnot">Rekonbar: {k.grund === 'analys' ? 'lokal analys' : 'Geminis sållning'} · Engagemang: percentil inom kontot</p>

      <div className="bk-sallning">
        <h3>Geminis sållning</h3>
        {sallStatus === 'laddar' && <p className="bk-dim">Läser sållning…</p>}
        {sallStatus === 'saknas' && <p className="bk-dim">Sållning saknas ännu.</p>}
        {sallStatus === 'fel' && <p className="bk-fel">Kunde inte läsa sållningen. Använd Uppdatera.</p>}
        {sallning && <>
          <dl className="bk-egenskaper">
            <div><dt>Personer</dt><dd>max {antal(sallning.personer_max)} · {procent(sallning.andel_med_person)} av tiden</dd></div>
            <div><dt>I verksamheten</dt><dd>{jaNej(sallning.inne_i_verksamheten)}</dd></div>
            <div><dt>Bildkvalitet</dt><dd>{antal(sallning.bildkvalitet)} / 5</dd></div>
            <div><dt>Montage</dt><dd>{jaNej(sallning.montage)}</dd></div>
            <div><dt>Bildspel</dt><dd>{jaNej(sallning.bildspel)}</dd></div>
            <div><dt>Texttyngd</dt><dd>{sallning.text_tung == null ? '–' : sallning.text_tung ? 'Texten bär' : 'Låg'}</dd></div>
          </dl>
          <p className="bk-skal">{sallning.skal}</p>
        </>}
      </div>

      <div className="bk-nasta">
        <p><b>Nästa steg</b> {k.nasta || 'Inget planerat'}</p>
        {k.skal?.length > 0 && <p className="bk-dim">{k.skal.join(' · ')}</p>}
      </div>

      <div className="bk-bedomning">
        <div className="bk-bedomhuvud"><h3>Min bedömning</h3>{oenighet && <span className="bk-oenig">Oenig med urvalet</span>}</div>
        <div className="bk-beslut" role="group" aria-label="Min bedömning">
          {BESLUT.map(b => <button
            key={b.id}
            className={`bk-${b.id}`}
            aria-pressed={bedomning?.beslut === b.id}
            onClick={() => spara(k.id, { beslut: b.id })}
          ><kbd>{b.tangent}</kbd>{b.text}</button>)}
        </div>
        <label className="bk-kommentar">
          <span>Kommentar <span className="bk-dim">(valfri)</span></span>
          <input
            type="text"
            maxLength={500}
            value={bedomning?.kommentar ?? ''}
            disabled={!bedomning}
            placeholder={bedomning ? 'Vad avgjorde din bedömning?' : 'Välj en bedömning först'}
            onChange={e => spara(k.id, { kommentar: e.target.value })}
          />
        </label>
        <div className="bk-sparstatus" role="status" aria-live="polite">
          {status === 'sparar' ? 'Sparar…' : status === 'fel' ? <span className="bk-fel">Inte sparat. <button onClick={() => spara(k.id, {})}>Försök igen</button></span> : bedomning ? 'Sparat' : 'Sparas direkt när du väljer'}
        </div>
      </div>
    </article>
  )
}

export default function Bank() {
  const [urval, setUrval] = useState(null)
  const [kallor, setKallor] = useState({})
  const [bedomningar, setBedomningar] = useState({})
  const [sparstatus, setSparstatus] = useState({})
  const [laddar, setLaddar] = useState(true)
  const [fel, setFel] = useState('')
  const [version, setVersion] = useState(0)
  const [typ, setTyp] = useState('alla')
  const [konto, setKonto] = useState('alla')
  const [filter, setFilter] = useState('alla')
  const [sortering, setSortering] = useState('poang')
  const [aktiv, setAktiv] = useState(null)
  const [sokId, setSokId] = useState(null)
  const aktuella = useRef({})
  const statusRef = useRef({})
  const koer = useRef({})
  const kort = useRef(new Map())
  const rutnat = useRef(null)

  async function ladda(signal) {
    const fore = aktuella.current
    setLaddar(true)
    setFel('')
    try {
      const [u, b, k] = await Promise.all([
        hamtaJson('/__data/bank/urval.json', signal, { klipp: [] }),
        hamtaJson('/__bank/bedomningar', signal),
        hamtaJson('/__data/kallor.json', signal, {}),
      ])
      // En uppdatering får inte skriva över en lokal ändring som väntar på att sparas.
      for (const [id, bedomning] of Object.entries(aktuella.current)) {
        if ((statusRef.current[id] && statusRef.current[id] !== 'sparad') || bedomning !== fore[id]) b[id] = bedomning
      }
      aktuella.current = b
      setBedomningar(b)
      setUrval(u)
      setKallor(k)
      setVersion(v => v + 1)
    } catch (e) {
      if (e.name !== 'AbortError') setFel(e.message)
    } finally {
      if (!signal?.aborted) setLaddar(false)
    }
  }

  useEffect(() => {
    const kontroll = new AbortController()
    ladda(kontroll.signal)
    return () => kontroll.abort()
  }, [])

  function sattStatus(id, status) {
    statusRef.current = { ...statusRef.current, [id]: status }
    setSparstatus(statusRef.current)
  }

  function spara(id, andring) {
    const bedomning = { kommentar: '', ...aktuella.current[id], ...andring }
    aktuella.current = { ...aktuella.current, [id]: bedomning }
    setBedomningar(aktuella.current)
    sattStatus(id, 'sparar')
    // Samma klipp sparas i ordning. Snabba ändringar ersätter sådant som ännu inte skickats.
    koer.current[id] = (koer.current[id] ?? Promise.resolve()).then(async () => {
      if (aktuella.current[id] !== bedomning) return
      try {
        const svar = await fetch('/__bank/bedom', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id, beslut: bedomning.beslut, kommentar: bedomning.kommentar }),
          keepalive: true,
        })
        if (!svar.ok) throw new Error('Kunde inte spara')
        const data = await svar.json()
        if (!data.ok || !data.bedomning) throw new Error('Ogiltigt svar')
        if (aktuella.current[id] === bedomning) {
          aktuella.current = { ...aktuella.current, [id]: data.bedomning }
          setBedomningar(aktuella.current)
          sattStatus(id, 'sparad')
        }
      } catch {
        if (aktuella.current[id] === bedomning) sattStatus(id, 'fel')
      }
    })
  }

  const klipp = urval?.klipp ?? []
  const typer = [...new Set(klipp.map(k => k.typ))].sort((a, b) => a.localeCompare(b, 'sv'))
  const konton = [...new Set(klipp.map(k => k.konto))].filter(Boolean).sort((a, b) => a.localeCompare(b, 'sv'))
  const bedomda = klipp.filter(k => bedomningar[k.id])
  const jamforbara = bedomda.filter(k => tydlig(bedomningar[k.id]))
  const oeniga = jamforbara.filter(k => oenig(k, bedomningar[k.id]))
  const osakra = bedomda.filter(k => bedomningar[k.id].beslut === 'osaker').length
  const overens = jamforbara.length - oeniga.length
  const synliga = useMemo(() => (urval?.klipp ?? []).filter(k => {
    if (typ !== 'alla' && k.typ !== typ) return false
    if (konto !== 'alla' && k.konto !== konto) return false
    if (filter === 'valda') return k.valt
    if (filter === 'ejvalda') return !k.valt
    if (filter === 'bedomda') return Boolean(bedomningar[k.id])
    if (filter === 'obedomda') return !bedomningar[k.id]
    if (filter === 'oeniga') return oenig(k, bedomningar[k.id])
    return true
  }).sort((a, b) => (b[sortering] ?? -1) - (a[sortering] ?? -1) || a.id.localeCompare(b.id, 'sv')), [urval, typ, konto, filter, sortering, bedomningar])
  const aktivId = synliga.some(k => k.id === aktiv) ? aktiv : synliga[0]?.id

  useEffect(() => {
    if (!sokId || !kort.current.has(sokId)) return
    const element = kort.current.get(sokId)
    element.focus({ preventScroll: true })
    element.scrollIntoView({ block: 'center' })
    setSokId(null)
  }, [sokId, synliga])

  function visaKlipp(id) {
    setTyp('alla')
    setKonto('alla')
    setFilter('alla')
    setAktiv(id)
    setSokId(id)
  }

  function tangent(e) {
    if (e.ctrlKey || e.metaKey || e.altKey || e.isComposing || e.target.closest('input, textarea, select, video, [contenteditable="true"]')) return
    const id = e.target.closest('[data-klipp-id]')?.dataset.klippId
    if (!id) return
    const beslut = BESLUT.find(b => b.tangent === e.key)
    if (beslut) {
      e.preventDefault()
      spara(id, { beslut: beslut.id })
      return
    }
    const kolumner = getComputedStyle(rutnat.current).gridTemplateColumns.split(' ').length
    const steg = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -kolumner, ArrowDown: kolumner }[e.key]
    if (!steg) return
    e.preventDefault()
    const index = synliga.findIndex(k => k.id === id)
    const nasta = synliga[Math.max(0, Math.min(synliga.length - 1, index + steg))]
    kort.current.get(nasta.id)?.focus({ preventScroll: true })
    kort.current.get(nasta.id)?.scrollIntoView({ block: 'nearest' })
  }

  return (
    <main className="bk">
      <div className="bk-inre">
        <header className="bk-topp">
          <div><p className="bk-overrubrik">Träningsdata / restauranger</p><h1>Klippbanken</h1><p className="bk-dim">Granska urvalet och välj vilka klipp som ska tas vidare.</p></div>
          <nav aria-label="Bankens navigering">
            <a href="#bibliotek">Bibliotek</a><a href="#rekon">Rekonstruktioner</a>
            <button className="bk-knapp" disabled={laddar || Object.values(sparstatus).includes('sparar')} onClick={() => ladda()}>{laddar ? 'Läser…' : 'Uppdatera'}</button>
          </nav>
        </header>

        {fel && <p className="bk-fel bk-felruta" role="alert">{fel}</p>}
        <section className="bk-sammanfattning" aria-label="Sammanfattning">
          <dl className="bk-tal">
            <div><dt>Klipp i banken</dt><dd>{urval ? antal(klipp.length) : '–'}</dd></div>
            <div><dt>Valda av urvalet</dt><dd>{urval ? antal(klipp.filter(k => k.valt).length) : '–'}</dd></div>
            <div><dt>Bedömda av mig</dt><dd>{antal(bedomda.length)}<small> / {antal(klipp.length)}</small></dd></div>
            <div className="bk-overens"><dt>Överens med urvalet</dt><dd>{jamforbara.length ? procent(overens / jamforbara.length) : '–'}</dd><span>{overens} av {jamforbara.length} tydliga beslut · {osakra} osäkra räknas inte</span></div>
          </dl>
          {typer.length > 0 && <div className="bk-typer"><span>Valda / alla per typ</span>{typer.map(t => <span className="bk-typantal" key={t}>{typnamn(t)} <b>{klipp.filter(k => k.typ === t && k.valt).length} / {klipp.filter(k => k.typ === t).length}</b></span>)}</div>}
        </section>

        {oeniga.length > 0 && <details className="bk-oenigheter">
          <summary>Oenigheter <b>{oeniga.length}</b></summary>
          <ul>{oeniga.map(k => <li key={k.id}><button onClick={() => visaKlipp(k.id)}><b>@{k.konto}</b> · {k.innehall || k.id}<span>Du: {bedomningar[k.id].beslut === 'med' ? 'ta med' : 'ta inte med'} · Urvalet: {k.valt ? 'valt' : 'ej valt'} →</span></button></li>)}</ul>
        </details>}

        <section className="bk-filter" aria-label="Filtrera klipp">
          <label>Typ<select aria-label="Typ" value={typ} onChange={e => setTyp(e.target.value)}><option value="alla">Alla typer</option>{typer.map(t => <option key={t} value={t}>{typnamn(t)}</option>)}</select></label>
          <label>Konto<select aria-label="Konto" value={konto} onChange={e => setKonto(e.target.value)}><option value="alla">Alla konton</option>{konton.map(k => <option key={k} value={k}>@{k}</option>)}</select></label>
          <label>Urval / bedömning<select aria-label="Urval / bedömning" value={filter} onChange={e => setFilter(e.target.value)}><option value="alla">Alla klipp</option><option value="valda">Valt</option><option value="ejvalda">Ej valt</option><option value="bedomda">Bedömt av mig</option><option value="obedomda">Inte bedömt av mig</option><option value="oeniga">Oenigheter</option></select></label>
          <label>Sortering<select aria-label="Sortering" value={sortering} onChange={e => setSortering(e.target.value)}><option value="poang">Poäng, högst först</option><option value="rekonbar">Rekonbar, högst först</option><option value="engagemang">Engagemang, högst först</option></select></label>
          <button className="bk-nollstall" onClick={() => {
            setTyp('alla')
            setKonto('alla')
            setFilter('alla')
          }}>Rensa filter</button>
        </section>

        <div className="bk-listtopp">
          <h2>{antal(synliga.length)} av {antal(klipp.length)} klipp</h2>
          <p>Hovra för att spela · <kbd>←</kbd> <kbd>↑</kbd> <kbd>↓</kbd> <kbd>→</kbd> byter kort · <kbd>1</kbd> ta med · <kbd>2</kbd> osäker · <kbd>3</kbd> ta inte med</p>
        </div>
        {laddar && !urval && <p className="bk-tomt" role="status">Läser klippbanken…</p>}
        {urval && !synliga.length && <p className="bk-tomt">{klipp.length ? 'Inga klipp matchar filtren.' : 'Inga klipp i urvalet ännu. Uppdatera när fler har sållats.'}</p>}
        <div className="bk-rutnat" ref={rutnat} onKeyDown={tangent}>
          {synliga.map(k => <BankKort
            key={k.id}
            klipp={k}
            kalla={kallor[k.id]}
            bedomning={bedomningar[k.id]}
            status={sparstatus[k.id]}
            aktiv={aktivId === k.id}
            registrera={(id, element) => {
              if (element) kort.current.set(id, element)
              else kort.current.delete(id)
            }}
            aktivera={setAktiv}
            spara={spara}
            version={version}
          />)}
        </div>
        <p className="bk-fot">Bedömningar sparas direkt. Dina ja/nej-beslut får företräde nästa gång urvalet körs.{urval?.skapad && <> Urvalet uppdaterades <time dateTime={urval.skapad}>{new Date(urval.skapad).toLocaleString('sv-SE')}</time>.</>}</p>
      </div>
    </main>
  )
}
