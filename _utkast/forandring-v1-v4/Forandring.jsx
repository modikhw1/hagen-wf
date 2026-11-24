import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import Frame from './Scen'
import { CLIP, S0, curve, shotsAt } from './klipp'
import { VSTEP, VSTEPS, von } from './steg'
import './forandring.css'

const FW = 168
const FH = 300
const GAP = 34
const ROW_W = CLIP.scenes.length * FW + (CLIP.scenes.length - 1) * GAP
const colX = i => i * (FW + GAP) + FW / 2
const DUR = 1.8

// Storyboard-tecken för kamerans rörelse, nere i hörnet av rutan.
function MoveGlyph({ m }) {
  if (m === 'still') return null
  const d = {
    drift: <path d="M4 12 H20" strokeDasharray="2 3" />,
    push: <><path d="M3 8 V3 H8 M16 3 H21 V8 M21 16 V21 H16 M8 21 H3 V16" /><path d="M9 9 L15 15 M15 9 L9 15" opacity=".5" /></>,
    pan: <path d="M3 12 H21 M16 7 L21 12 L16 17" />,
    hand: <path d="M2 12 Q5 6 8 12 T14 12 T20 12 T23 10" />,
    orbit: <path d="M4 15 Q12 4 20 15 M16 14 L20 15 L20 11" />,
  }[m]
  return (
    <motion.svg key={m} initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="vf-move" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      {d}
    </motion.svg>
  )
}

// Tecken för övergången in i nästa scen, i glipan mellan rutorna.
function TransGlyph({ t }) {
  const d = {
    rak: <path d="M12 3 V21" />,
    mjuk: <><circle cx="9" cy="12" r="6" /><circle cx="15" cy="12" r="6" opacity=".45" /></>,
    match: <path d="M5 9 H19 M5 15 H19" />,
    whip: <path d="M3 6 L10 12 L3 18 M12 6 L19 12 L12 18" />,
    zoom: <><circle cx="12" cy="12" r="3" /><circle cx="12" cy="12" r="8" opacity=".5" /></>,
  }[t]
  return (
    <motion.svg key={t} initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className={`vf-trans t-${t}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      {d}
    </motion.svg>
  )
}

const Lock = () => (
  <svg viewBox="0 0 12 12" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="1.6"><rect x="2" y="5.5" width="8" height="5.5" rx="1" /><path d="M4 5.5V4a2 2 0 0 1 4 0v1.5" /></svg>
)

function Row({ shots, playing, now }) {
  return (
    <div className="vf-row" style={{ width: ROW_W, gap: GAP }}>
      {CLIP.scenes.map((sc, i) => (
        <div key={i} className={`vf-col ${playing && now === i ? 'now' : ''}`} style={{ width: FW }}>
          <div className="vf-framewrap">
            <span className="vf-num">{i + 1}</span>
            <Frame scene={sc} s={shots[i]} W={FW} H={FH} />
            <MoveGlyph m={shots[i].move} />
            {i > 0 && <div className="vf-gap" style={{ width: GAP, left: -GAP }}><TransGlyph t={shots[i].trans} /></div>}
          </div>
          <div className="vf-text">{sc.text}</div>
        </div>
      ))}
    </div>
  )
}

// Kurvan: varje scens steg. Originalet ligger kvar som spöke.
function Curve({ s }) {
  const H = 96
  const y = v => 10 + ((10 - v) / 9) * (H - 20)
  const path = vs => vs.map((v, i) => `${i ? 'L' : 'M'}${colX(i)} ${y(v)}`).join(' ')
  const now = curve(s)
  return (
    <svg className="vf-curve" width={ROW_W} height={H}>
      {[1, 10].map(v => <path key={v} d={`M0 ${y(v)} H${ROW_W}`} className="vf-curve-rail" />)}
      <path d={path(CLIP.orig)} className="vf-curve-ghost" />
      {CLIP.orig.map((v, i) => <circle key={i} cx={colX(i)} cy={y(v)} r="3.5" className="vf-curve-ghostdot" />)}
      <motion.path initial={false} animate={{ d: path(now) }} transition={{ type: 'spring', stiffness: 260, damping: 30 }} className="vf-curve-line" />
      {now.map((v, i) => (
        <motion.circle key={i} cx={colX(i)} r="5.5" initial={false} animate={{ cy: y(v) }} transition={{ type: 'spring', stiffness: 260, damping: 30 }} className="vf-curve-dot" />
      ))}
    </svg>
  )
}

function Slider({ s, set }) {
  const pct = v => ((v - 1) / 9) * 100
  return (
    <div className="vf-slider" style={{ width: ROW_W }}>
      <span className="vf-end">stilla, rakt fram</span>
      <div className="vf-track">
        <div className="vf-orig" style={{ left: `calc(8px + (100% - 16px) * ${pct(S0) / 100})` }} title="Originalet">original</div>
        <input type="range" min="1" max="10" step="1" value={s} onChange={e => set(+e.target.value)} aria-label="Kreativ scenografi, 1 till 10" />
        <div className="vf-ticks">
          {Array.from({ length: 10 }, (_, i) => (
            <button key={i} style={{ left: pct(i + 1) + '%' }} className={`${s === i + 1 ? 'on' : ''} ${S0 === i + 1 ? 'o' : ''}`} onClick={() => set(i + 1)}>{i + 1}</button>
          ))}
        </div>
      </div>
      <span className="vf-end">eget grepp per scen</span>
    </div>
  )
}

// Telefonen spelar klippet: scen för scen, med rörelse och övergångar. Reglaget slår igenom direkt.
const ENTER = {
  rak: { initial: { opacity: 1 }, animate: { opacity: 1 }, exit: { opacity: 0, transition: { duration: 0 } } },
  mjuk: { initial: { opacity: 0 }, animate: { opacity: 1, transition: { duration: 0.35 } }, exit: { opacity: 0, transition: { duration: 0.35 } } },
  match: { initial: { opacity: 0 }, animate: { opacity: 1, transition: { duration: 0.12 } }, exit: { opacity: 0, transition: { duration: 0.12 } } },
  whip: { initial: { x: '100%', filter: 'blur(8px)' }, animate: { x: 0, filter: 'blur(0px)', transition: { duration: 0.22 } }, exit: { x: '-100%', filter: 'blur(8px)', transition: { duration: 0.22 } } },
  zoom: { initial: { scale: 1.8, opacity: 0 }, animate: { scale: 1, opacity: 1, transition: { duration: 0.28 } }, exit: { scale: 0.5, opacity: 0, transition: { duration: 0.28 } } },
}

function Player({ shots, now, setNow, playing, setPlaying }) {
  const W = 248
  const H = 440
  useEffect(() => {
    if (!playing) return
    const t = setTimeout(() => setNow(n => (n + 1) % CLIP.scenes.length), DUR * 1000)
    return () => clearTimeout(t)
  }, [playing, now, setNow])
  const tr = ENTER[shots[now].trans]
  return (
    <div className="vf-player">
      <div className="vf-phone" style={{ width: W + 16, height: H + 16 }}>
        <div className="vf-screen" style={{ width: W, height: H }}>
          <AnimatePresence initial={false} custom={tr}>
            <motion.div key={now} className="vf-layer" custom={tr} variants={{ i: (c) => c.initial, a: (c) => c.animate, e: (c) => c.exit }} initial="i" animate="a" exit="e">
              <Frame scene={CLIP.scenes[now]} s={shots[now]} W={W} H={H} playing={playing} dur={DUR} />
            </motion.div>
          </AnimatePresence>
          <div className="vf-progress">
            {CLIP.scenes.map((_, i) => (
              <i key={i}>{i === now && playing ? <motion.b key={`${now}-p`} initial={{ width: 0 }} animate={{ width: '100%' }} transition={{ duration: DUR, ease: 'linear' }} /> : <b style={{ width: i < now ? '100%' : 0 }} />}</i>
            ))}
          </div>
        </div>
      </div>
      <button className="vf-play" onClick={() => setPlaying(p => !p)} aria-label={playing ? 'Pausa' : 'Spela'}>
        {playing
          ? <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1" /><rect x="14" y="5" width="4" height="14" rx="1" /></svg>
          : <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M7 5 L19 12 L7 19 Z" /></svg>}
      </button>
    </div>
  )
}

export default function Forandring() {
  const [s, set] = useState(S0)
  const [now, setNow] = useState(0)
  const [playing, setPlaying] = useState(true)
  const level = von(2) ? s : S0
  const shots = shotsAt(level)
  return (
    <div className="vf">
      <header className="vf-top">
        <div className="vf-title">
          <b>Videoförändring</b>
          <span className="vf-vert">Kreativ scenografi</span>
        </div>
        <div className="vf-clip">
          <span className="vf-av">{CLIP.kund[0]}</span>
          <span>{CLIP.kund} · {CLIP.name}</span>
        </div>
        <div className="vf-locks" title="Låst i experimentet">
          {['lokal', 'rekvisita', 'personal', 'handling'].map(l => <span key={l} className="vf-lock"><Lock />{l}</span>)}
        </div>
      </header>

      <main className={`vf-main ${von(4) ? 'with-player' : ''}`}>
        {von(4) && <Player shots={shots} now={now} setNow={setNow} playing={playing} setPlaying={setPlaying} />}
        <div className="vf-board">
          <Row shots={shots} playing={von(4) && playing} now={now} />
          {von(3) && <Curve s={level} />}
          {von(2) && <Slider s={s} set={set} />}
        </div>
      </main>

      <nav className="stepper" aria-label="Iteration">
        {VSTEPS.map((name, i) => (
          <a key={i} href={`#v${i + 1}`} className={VSTEP === i + 1 ? 'on' : VSTEP > i + 1 ? 'done' : ''} title={name}>{i + 1}</a>
        ))}
        <span>{VSTEPS[VSTEP - 1]}</span>
      </nav>
    </div>
  )
}
