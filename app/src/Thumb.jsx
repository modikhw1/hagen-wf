import { useEffect, useState } from 'react'
import { motion } from 'motion/react'
import { on } from './step'

const P = {
  pizza: <><circle cx="24" cy="24" r="15" /><path d="M24 9v30M11 17l26 14M11 31l26-14" /><circle cx="19" cy="20" r="1.5" /><circle cx="29" cy="27" r="1.5" /></>,
  nonna: <><circle cx="24" cy="15" r="6" /><circle cx="24" cy="7.5" r="2.5" /><path d="M14 40c0-9 4-15 10-15s10 6 10 15" /><path d="M33 26l6-5" /></>,
  person: <><circle cx="24" cy="14" r="6" /><path d="M24 20v12M24 24l-8 5M24 24l8-6M24 32l-6 9M24 32l6 9" /></>,
  duo: <><circle cx="16" cy="15" r="5" /><circle cx="32" cy="15" r="5" /><path d="M16 20v12M32 20v12M16 25l8-3M32 25l-8-3M16 32l-4 8M32 32l4 8" /></>,
  clock: <><circle cx="24" cy="24" r="15" /><path d="M24 14v10l7 5" /></>,
  plate: <><ellipse cx="24" cy="30" rx="16" ry="5" /><path d="M14 28c2-7 18-7 20 0" /><path d="M35 12l-3 6M38 15l-5 4" /></>,
  box: <><path d="M10 18l14-7 14 7v14l-14 7-14-7z" /><path d="M10 18l14 7 14-7M24 25v14" /></>,
  mirror: <><ellipse cx="24" cy="20" rx="10" ry="13" /><path d="M24 33v8M17 41h14" /><path d="M19 14l4-3" /></>,
  scissors: <><circle cx="15" cy="33" r="5" /><circle cx="33" cy="33" r="5" /><path d="M18 29l16-20M30 29L14 9" /></>,
  cup: <><path d="M12 18h20v8a10 10 0 0 1-20 0z" /><path d="M32 20h4a4 4 0 0 1 0 8h-4M18 8c0 3 3 3 3 6M24 8c0 3 3 3 3 6" /></>,
  bread: <><path d="M9 26c0-8 7-12 15-12s15 4 15 12v8H9z" /><path d="M17 20l3 6M24 19v7M31 20l-3 6" /></>,
  knife: <><path d="M10 38l20-20 6 2-22 22z" /><path d="M30 18l6-6" /><circle cx="36" cy="30" r="3" /><circle cx="31" cy="36" r="2" /></>,
  phone: <><rect x="16" y="8" width="16" height="30" rx="3" /><path d="M22 33h4" /><path d="M36 12q3 3 0 6M39 9q5 6 0 12" /></>,
}

export function Picto({ name }) {
  return (
    <svg viewBox="0 0 48 48" className="picto" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {P[name]}
    </svg>
  )
}

const LockGlyph = () => (
  <svg viewBox="0 0 12 12" width="9" height="9" fill="none" stroke="currentColor" strokeWidth="1.6"><rect x="2" y="5.5" width="8" height="5.5" rx="1" /><path d="M4 5.5V4a2 2 0 0 1 4 0v1.5" /></svg>
)

// Bilden på ett kort: piktogram + scenremsa. Under ingest syns hämtning, sedan klippning.
export default function Thumb({ c, small }) {
  const queued = c.status === 'queued'
  const fetching = c.status === 'fetch'
  const cutting = c.status === 'cut'
  const ready = c.status === 'ready' || c.status === 'review'
  const locks = on(6)
  return (
    <div className={`thumb ${small ? 'small' : ''}`}>
      {queued && <div className="queued"><span>i kö</span><b>{c.qpos || ''}</b></div>}
      {fetching && <div className="shimmer" />}
      {(fetching || cutting) && c.t0 && <Eta c={c} />}
      {!fetching && !queued && (
        <motion.div className="picto-wrap" initial={false} animate={{ opacity: ready ? 1 : 0.15, scale: ready ? 1 : 0.9 }} transition={{ duration: 0.4 }}>
          <Picto name={c.picto} />
        </motion.div>
      )}
      {!fetching && !queued && (
        <div className="strip">
          {c.scenes.map((sc, i) => (
            <motion.div
              key={i}
              className={`seg ${sc.lock && ready && locks ? 'locked' : ''} ${ready && c.touched && c.changed?.includes(i) ? 'mine' : ''}`}
              style={{ flexGrow: sc.dur, transformOrigin: 'left' }}
              initial={cutting ? { scaleX: 0, opacity: 0 } : false}
              animate={{ scaleX: 1, opacity: 1 }}
              transition={{ delay: cutting ? 0.25 + i * 0.4 : 0, duration: 0.25 }}
            >
              {sc.lock && ready && locks && <LockGlyph />}
            </motion.div>
          ))}
        </div>
      )}
      {cutting && (
        <motion.div
          className="scan"
          initial={{ left: '0%' }}
          animate={{ left: '100%' }}
          transition={{ duration: 0.4 + c.scenes.length * 0.4, ease: 'linear' }}
        />
      )}
    </div>
  )
}

// Kvarvarande tid för ingesten, i verklig tid (prototypen spelar upp den 10× snabbare).
function Eta({ c }) {
  const [, tick] = useState(0)
  useEffect(() => { const t = setInterval(() => tick(x => x + 1), 200); return () => clearInterval(t) }, [])
  const left = Math.max(0, Math.round(c.eta - (Date.now() - c.t0) / 100))
  const pct = Math.min(100, ((c.eta - left) / c.eta) * 100)
  return (
    <div className="eta-wrap">
      <span className="eta-time">0:{String(left).padStart(2, '0')}</span>
      <span className="eta-bar"><i style={{ width: pct + '%' }} /></span>
    </div>
  )
}
