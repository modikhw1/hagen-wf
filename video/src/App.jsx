import { useEffect, useRef, useState } from 'react'
import {
  DndContext, DragOverlay, KeyboardSensor, PointerSensor, TouchSensor,
  pointerWithin, rectIntersection, useDraggable, useDroppable, useSensor, useSensors,
} from '@dnd-kit/core'
import { AnimatePresence, LayoutGroup, motion } from 'motion/react'
import { makeCustomers, newId, POOL } from './data'
import Thumb from './Thumb'
import { STEP, STEPS, on } from './step'
import { BASE, KINDS, balance, fp } from './mix'

const MIN_SLOTS = 6
const SLOT = 140
const GAP = 16
const slotX = i => i * (SLOT + GAP) + SLOT / 2
const spring = { type: 'spring', stiffness: 420, damping: 34 }

const insertAt = (list, i, c) => { const k = Math.max(0, Math.min(i, list.length)); return [...list.slice(0, k), c, ...list.slice(k)] }
const altsOf = c => (c.alts ? [c.alts[1], c.alts[3]].filter(Boolean) : [])
const allClips = s => [...s.history, ...s.plan, ...s.plan.flatMap(altsOf), ...s.bench, ...(s.loose || [])]
const mapClip = (s, id, f) => {
  const m = c => (c && c.id === id ? f(c) : c)
  return {
    ...s,
    history: s.history.map(m),
    plan: s.plan.map(h => { const x = m(h); return x.alts ? { ...x, alts: { 1: m(x.alts[1]), 3: m(x.alts[3]) } } : x }),
    bench: s.bench.map(m),
    loose: (s.loose || []).map(m),
  }
}

// Plocka ut ett klipp var det än ligger. Ett klipp i planen tar med sig sina alternativ.
function take(s, id) {
  const i = s.plan.findIndex(c => c.id === id)
  if (i > -1) return { s: { ...s, plan: s.plan.filter(c => c.id !== id) }, c: s.plan[i], from: i }
  const b = s.bench.find(c => c.id === id)
  if (b) return { s: { ...s, bench: s.bench.filter(c => c.id !== id) }, c: b, from: -1 }
  const l = (s.loose || []).find(c => c.id === id)
  if (l) return { s: { ...s, loose: s.loose.filter(c => c.id !== id) }, c: l, from: -1 }
  for (const host of s.plan) for (const n of [1, 3]) {
    if (host.alts?.[n]?.id === id) {
      return { s: { ...s, plan: s.plan.map(h => (h.id === host.id ? { ...h, alts: { ...h.alts, [n]: null } } : h)) }, c: host.alts[n], from: -1 }
    }
  }
  return { s, c: null, from: -1 }
}
const strip = c => ({ ...c, alts: null })

// Alla flyttar, både drag och högerklick, går genom samma funktion. Förhandsvisningen använder den också.
function nextState(s0, op) {
  if (op.kind === 'autoPlace') return { ...s0, plan: [...s0.plan, ...(s0.loose || [])], loose: [] }
  if (op.kind === 'swapUp') {
    const h = s0.plan.find(x => x.id === op.host)
    const n = [1, 3].find(k => h?.alts?.[k]?.id === op.id)
    return n ? nextState(s0, { kind: 'promote', host: op.host, n }) : s0
  }
  if (op.kind === 'rotate') {
    // Dubbelklick: trion roterar, så att framsidan går 2 → 3 → 1 → 2.
    return { ...s0, plan: s0.plan.map(h => {
      if (h.id !== op.host) return h
      const keys = [3, 1].filter(k => h.alts?.[k])
      if (!keys.length) return h
      const seq = [strip(h), ...keys.map(k => h.alts[k])]
      const next = [...seq.slice(1), seq[0]]
      const alts = { 1: null, 3: null }
      keys.forEach((k, i) => { alts[k] = next[i + 1] })
      return { ...next[0], alts, chosen: null }
    }) }
  }
  if (op.kind === 'promote') {
    return { ...s0, plan: s0.plan.map(h => {
      if (h.id !== op.host || !h.alts?.[op.n]) return h
      const alt = h.alts[op.n]
      return { ...alt, alts: { ...h.alts, [op.n]: strip(h) }, chosen: op.chosen ?? null, mark: op.chosen ? 'chose' : alt.mark }
    }) }
  }
  const { s, c, from } = take(s0, op.id)
  if (!c) return s0
  switch (op.kind) {
    case 'insert': return { ...s, plan: insertAt(s.plan, op.i, from > -1 ? c : strip(c)) }
    case 'earlier': return { ...s, plan: insertAt(s.plan, from - 1, c) }
    case 'later': return { ...s, plan: insertAt(s.plan, from + 1, c) }
    case 'toPlan': return { ...s, plan: [...s.plan, strip(c)] }
    // 2 går till bänken. Alternativen går inte tillbaka till bänken: de blir lösa och ska in i planen igen.
    case 'bench': return { ...s, bench: [strip(c), ...s.bench], loose: [...(s.loose || []), ...altsOf(c)] }
    case 'library': return s
    case 'alt': {
      if (op.host === c.id) return nextState(s0, { kind: 'promote', host: c.id, n: op.n })
      const back = altsOf(c)
      let bumped = null
      const plan = s.plan.map(h => {
        if (h.id !== op.host) return h
        bumped = h.alts?.[op.n] || null
        return { ...h, alts: { 1: null, 3: null, ...h.alts, [op.n]: strip(c) } }
      })
      return { ...s, plan, bench: [...back, ...(bumped ? [bumped] : []), ...s.bench] }
    }
    default: return s0
  }
}

function applyEvent(s, ev) {
  if (ev.type === 'chose') {
    const host = s.plan.find(h => h.id === ev.id)
    if (!host) return s
    return nextState(s, { kind: 'promote', host: ev.id, n: ev.n, chosen: ev.n })
  }
  const c = allClips(s).find(x => x.id === ev.id)
  if (!c) return s
  const plan = s.plan.filter(x => x.id !== ev.id)
  if (ev.type === 'published') return { ...s, plan, history: [...s.history, { ...strip(c), mark: 'new' }], bench: [...altsOf(c), ...s.bench] }
  if (ev.type === 'back') return { ...s, plan, bench: [{ ...strip(c), mark: 'back' }, ...altsOf(c), ...s.bench] }
  if (ev.type === 'no') return { ...s, plan, bench: [{ ...strip(c), mark: 'no' }, ...altsOf(c), ...s.bench] }
  return s
}

const opFromTarget = (target, id) => {
  if (!target) return null
  if (target === 'bench') return { kind: 'bench', id }
  const [k, a, b] = target.split(':')
  if (k === 'slot') return { kind: 'insert', id, i: +a }
  if (k === 'alt' && b === 'main') return { kind: 'swapUp', id, host: a }
  if (k === 'alt') return { kind: 'alt', id, host: a, n: +b }
  return null
}

// Kortets kanter (1 och 3) går före platsen runt dem.
function collision(args) {
  const p = pointerWithin(args)
  const pri = p.filter(c => /^alt:/.test(String(c.id)))
  if (pri.length) return pri
  return p.length ? p : rectIntersection(args)
}

const shortUrl = u => u.replace(/^https?:\/\/(www\.|vm\.)?/, '').slice(0, 22)
const handleFrom = u => (u.match(/@[\w.]+/) || ['@okänd'])[0]

export default function App() {
  const [customers] = useState(makeCustomers)
  const [cid, setCid] = useState(null)
  const [states, setStates] = useState({})
  const [flash, setFlash] = useState([])
  const [target, setTarget] = useState(null)
  const [activeId, setActiveId] = useState(null)
  const [dropped, setDropped] = useState(null)
  const [overId, setOverId] = useState(null)
  const [menu, setMenu] = useState(null)
  const [hoverOp, setHoverOp] = useState(null)
  const [pinMix, setPinMix] = useState(false)
  const [peekMix, setPeekMix] = useState(false)
  const replayTimers = useRef([])
  const poolI = useRef(0)
  const laneRef = useRef(null)

  const cust = customers.find(c => c.id === cid)
  const st = states[cid]

  const updFor = (id, f) => setStates(p => ({ ...p, [id]: f(p[id]) }))

  function replay(id) {
    replayTimers.current.forEach(clearTimeout)
    replayTimers.current = []
    const c = customers.find(x => x.id === id)
    if (!on(2)) {
      // Steg 1: läget efter ankomsten, utan att visa vad som hänt.
      const after = c.events.reduce(applyEvent, structuredClone(c.before))
      const clean = l => l.map(x => ({ ...x, mark: null, chosen: null }))
      setStates(p => ({ ...p, [id]: { history: clean(after.history), plan: clean(after.plan), bench: clean(after.bench) } }))
      return
    }
    setStates(p => ({ ...p, [id]: structuredClone(c.before) }))
    c.events.forEach((ev, k) => {
      const t0 = 1200 + k * 1900
      replayTimers.current.push(setTimeout(() => setFlash([ev.id]), t0))
      replayTimers.current.push(setTimeout(() => updFor(id, s => applyEvent(s, ev)), t0 + 750))
    })
    replayTimers.current.push(setTimeout(() => setFlash([]), 1200 + c.events.length * 1900 + 500))
  }

  function open(id) {
    setCid(id)
    setTarget(null)
    if (!states[id]) replay(id)
  }

  // Ett nytt klipp landar alltid på bänken. Ingest tar 50–70 s (här uppspelat 10× snabbare),
  // sedan väntar den neutrala versionen på godkännande innan klippet kan användas i planen.
  // Kön: ett klipp ingestas i taget. De andra står på bänken som "i kö".
  const queue = useRef([])
  const running = useRef(false)
  function pump() {
    if (running.current || !queue.current.length) return
    running.current = true
    const { id, forCid, p, eta } = queue.current.shift()
    const patch = (x, ms) => setTimeout(() => updFor(forCid, s => mapClip(s, id, c => ({ ...c, ...x }))), ms)
    patch({ status: 'fetch', t0: Date.now() }, 0)
    patch({ status: 'cut' }, eta * 100 * 0.55)
    setTimeout(() => {
      updFor(forCid, s => mapClip(s, id, c => ({ ...c, status: 'review', title: p.title })))
      running.current = false
      pump()
    }, eta * 100)
  }

  function ingest(url) {
    const forCid = cid
    const p = POOL[poolI.current++ % POOL.length]
    const eta = 50 + Math.round(Math.random() * 20)
    const c = {
      id: newId(), status: 'queued', url, title: shortUrl(url), picto: p.picto, format: p.format, scenes: p.scenes,
      alts: null, chosen: null, mark: null, note: '', cmNote: '', fresh: true, series: null, views: null,
      touched: false, changed: [], handle: handleFrom(url), eta, queuedAt: Date.now() + queue.current.length,
    }
    updFor(forCid, s => ({ ...s, bench: [c, ...s.bench] }))
    queue.current.push({ id: c.id, forCid, p, eta })
    setTimeout(pump, 50)
  }
  // En länk blir ett klipp; en spellista blir flera.
  const ingestAll = text => parseLinks(text).forEach(l => (l.list
    ? Array.from({ length: PLAYLIST_SIZE }, (_, k) => ingest(`${l.u}#${k + 1}`))
    : ingest(l.u)))
  const approve = id => updFor(cid, s => mapClip(s, id, x => ({ ...x, status: 'ready' })))

  // Popup för inklistring. Plus, Ctrl/⌘V och länkar som dras in landar alla här.
  const [intake, setIntake] = useState(null)

  const noteFor = id => (v, done) => updFor(cid, s => mapClip(s, id, x => ({
    ...x, cmNote: v, touched: !!v.trim(), fresh: done && v.trim() ? false : x.fresh,
  })))

  // Klistra in var som helst: öppnar popupen med det inklistrade.
  useEffect(() => {
    const h = e => {
      if (!on(5) || !cid || intake) return
      const el = document.activeElement
      if (el && (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT')) return
      const t = e.clipboardData?.getData('text')?.trim()
      if (!t) return
      e.preventDefault()
      setIntake(t)
    }
    window.addEventListener('paste', h)
    return () => window.removeEventListener('paste', h)
  })

  // En länk som dras in från webbläsaren: fäll ut alla mål medan den är i luften.
  const [linkDrag, setLinkDrag] = useState(false)
  useEffect(() => {
    if (!on(5)) return
    let depth = 0
    const isLink = e => [...(e.dataTransfer?.types || [])].some(t => t === 'text/uri-list' || t === 'text/plain')
    const enter = e => { if (isLink(e)) { depth++; setLinkDrag(true) } }
    const leave = e => { if (isLink(e) && --depth <= 0) { depth = 0; setLinkDrag(false) } }
    const end = () => { depth = 0; setLinkDrag(false) }
    const over = e => { if (isLink(e)) e.preventDefault() }
    window.addEventListener('dragenter', enter)
    window.addEventListener('dragleave', leave)
    window.addEventListener('dragover', over)
    window.addEventListener('drop', end)
    window.addEventListener('dragend', end)
    return () => {
      window.removeEventListener('dragenter', enter); window.removeEventListener('dragleave', leave)
      window.removeEventListener('dragover', over); window.removeEventListener('drop', end); window.removeEventListener('dragend', end)
    }
  }, [])

  useEffect(() => {
    if (!menu) return
    const close = () => { setMenu(null); setHoverOp(null) }
    const key = e => e.key === 'Escape' && close()
    window.addEventListener('pointerdown', close)
    window.addEventListener('keydown', key)
    window.addEventListener('scroll', close, true)
    return () => { window.removeEventListener('pointerdown', close); window.removeEventListener('keydown', key); window.removeEventListener('scroll', close, true) }
  }, [menu])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 150, tolerance: 6 } }),
    useSensor(KeyboardSensor),
  )

  function run(op) {
    if (!op) return
    updFor(cid, s => nextState(s, op))
    if (op.id) { setDropped(op.id); setTimeout(() => setDropped(null), 450) }
  }

  function onDragEnd({ active, over }) {
    setActiveId(null)
    setOverId(null)
    if (over) run(opFromTarget(String(over.id), active.id))
  }

  function act(op) { setMenu(null); setHoverOp(null); updFor(cid, s => nextState(s, op)) }
  const openMenu = (e, c, where, extra = {}) => { e.preventDefault(); e.stopPropagation(); setMenu({ x: e.clientX, y: e.clientY, id: c.id, where, ...extra }) }

  if (!cid) return (
    <div className="app">
      <Entry customers={customers} onPick={open} />
      <Stepper />
    </div>
  )
  if (!st) return null

  const slots = Math.max(MIN_SLOTS, st.plan.length + 1)
  const active = activeId ? allClips(st).find(c => c.id === activeId) : null
  const activeFrom = activeId ? st.plan.findIndex(c => c.id === activeId) : -1

  // Förhandsvisning: planen som den blir om man släpper eller klickar här.
  const previewOp = (active && opFromTarget(overId, active.id)) || hoverOp
  const preview = previewOp ? nextState(st, previewOp).plan : st.plan
  const movingId = previewOp ? (previewOp.kind === 'promote' ? st.plan.find(h => h.id === previewOp.host)?.alts?.[previewOp.n]?.id : previewOp.id) : null
  const loose = st.loose || []
  // Mixspåret är dolt tills det behövs: när man drar, förhandsvisar, har lösa klipp, eller har fäst det.
  const showMix = on(3)
  const rotate = host => { run({ kind: 'rotate', host }); const h = st.plan.find(x => x.id === host); const k = [3, 1].find(n => h?.alts?.[n]); if (k) { setDropped(h.alts[k].id); setTimeout(() => setDropped(null), 450) } }

  return (
    <div className="app">
      <header className="top">
        <div className="brand">LeTrend</div>
        <button className="who" onClick={() => setCid(null)} title="Byt kund">
          <span className="av big">{cust.initial}</span>
          <span className="who-name">{cust.name}</span>
          <span className="chev">▾</span>
        </button>
        {on(3) && <Balance plan={preview} history={st.history} live={!!previewOp} open={pinMix || peekMix || !!previewOp} onToggle={() => setPinMix(v => !v)} pinned={pinMix} onPeek={setPeekMix} />}
      </header>

      <DndContext sensors={sensors} collisionDetection={collision}
        onDragStart={e => setActiveId(e.active.id)} onDragCancel={() => { setActiveId(null); setOverId(null) }}
        onDragOver={e => setOverId(e.over ? String(e.over.id) : null)} onDragEnd={onDragEnd}>
        <LayoutGroup id={cid}>
          <div className="work">
            <Bench bench={st.bench} flash={flash} dropped={dropped} dragging={!!activeId || linkDrag} onMenu={(e, c) => openMenu(e, c, 'bench')}
              onLink={ingestAll} onAdd={() => setIntake('')} noteFor={noteFor} onApprove={approve} />

            <main className="lane" ref={laneRef}>
              <section className="history" aria-label="Publicerat">
                <AnimatePresence initial={false}>
                  {st.history.slice(-3).map(c => (
                    <motion.div key={c.id} layoutId={c.id} layout className="hcard" transition={spring}>
                      <CardFace c={c} tiny flash={flash.includes(c.id)} />
                      {on(3) && <MixCol c={c} tiny />}
                    </motion.div>
                  ))}
                </AnimatePresence>
              </section>

              <div className="nowline"><span>nu</span></div>

              <section className="plan" style={{ width: slots * (SLOT + GAP) }}>
                {on(6) && <Overlays plan={st.plan} />}
                <div className="slots">
                  {Array.from({ length: slots }, (_, i) => {
                    const c = st.plan[i]
                    return (
                      <Slot key={i} i={i} activeFrom={activeFrom} dragging={!!activeId} beckon={loose.length > 0 && !c}
                        alts={c && on(4) && (
                          <Alts host={c} dragging={!!activeId} activeId={activeId}
                            onHover={n => setHoverOp(n ? { kind: 'promote', host: c.id, n } : null)}
                            onMenu={(e, alt, n) => openMenu(e, alt, 'alt', { host: c.id, n })} />
                        )}>
                        {c && (
                          <MainDrop key={c.id} host={c} activeId={activeId}>
                            <DraggableCard c={c} flash={flash.includes(c.id)} dropped={dropped === c.id} onMenu={e => openMenu(e, c, 'plan')}
                              onDoubleClick={on(4) ? () => rotate(c.id) : undefined}
                              onNote={noteFor(c.id)} />
                          </MainDrop>
                        )}
                      </Slot>
                    )
                  })}
                </div>
                <AnimatePresence>
                  {loose.length > 0 && (
                    <motion.div className="loose" initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={spring}>
                      <span className="loose-arrow">↑</span>
                      {loose.map(c => <DraggableCard key={c.id} c={c} small />)}
                      <button className="pill sk" onClick={() => run({ kind: 'autoPlace' })} onMouseEnter={() => setHoverOp({ kind: 'autoPlace' })} onMouseLeave={() => setHoverOp(null)}>Lägg sist</button>
                    </motion.div>
                  )}
                </AnimatePresence>
                <AnimatePresence initial={false}>
                  {showMix && (
                    <motion.div key="mix" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.25 }} style={{ overflow: 'hidden' }}>
                      <MixRow plan={preview} slots={slots} movingId={movingId} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </section>
            </main>
          </div>
        </LayoutGroup>

        <DragOverlay dropAnimation={null}>
          {active && <div className="lifted"><CardFace c={active} /></div>}
        </DragOverlay>
      </DndContext>
      <AnimatePresence>
        {menu && <Menu menu={menu} st={st} onAct={act} onPreview={setHoverOp} />}
      </AnimatePresence>
      <AnimatePresence>
        {intake != null && (
          <Intake key="intake" initial={intake} onClose={() => setIntake(null)}
            onFetch={urls => { urls.forEach(u => ingest(u)); setIntake(null) }} />
        )}
      </AnimatePresence>
      <Stepper />
    </div>
  )
}

/* ---------- Ingången: vem jobbar du med i dag ---------- */
function Entry({ customers, onPick }) {
  return (
    <main className="entry">
      <div className="brand">LeTrend</div>
      <div className="entry-row">
        {customers.map((c, k) => {
          const after = c.events.reduce(applyEvent, structuredClone(c.before))
          return (
            <motion.button key={c.id} className="ecard sk" onClick={() => onPick(c.id)}
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ ...spring, delay: k * 0.06 }}
              whileHover={{ y: -4, rotate: k % 2 ? 0.6 : -0.6 }}>
              <span className="av huge">{c.initial}</span>
              <span className="ename">{c.name}</span>
              <span className="slots-mini" aria-label={`${after.plan.length} av ${MIN_SLOTS} platser fyllda`}>
                {Array.from({ length: MIN_SLOTS }, (_, i) => <i key={i} className={i < after.plan.length ? 'f' : ''} />)}
              </span>
            </motion.button>
          )
        })}
      </div>
    </main>
  )
}

/* ---------- Balansen: blandningen i planen mot baslinjen ---------- */
// Tyst som standard: en tunn remsa. Klick fäster den och mixspåret under planen.
function Balance({ plan, history, live, open, pinned, onToggle, onPeek }) {
  const now = balance(plan)
  const was = balance(history)
  const edges = [BASE.ent, BASE.ent + BASE.info]
  return (
    <button className={`balance ${live ? 'live' : ''} ${open ? 'open' : 'quiet'} ${pinned ? 'pinned' : ''}`} onClick={onToggle}
      onMouseEnter={() => onPeek(true)} onMouseLeave={() => onPeek(false)}
      aria-pressed={pinned} aria-label="Blandningen i planen. Klicka för att fästa mixspåret.">
      <span className="pin" aria-hidden="true">{pinned ? '●' : '○'}</span>
      <div className="bal-bars">
        <div className="bal-bar">
          {KINDS.map(([k]) => <motion.i key={k} className={`k-${k}`} animate={{ width: `${now[k] * 100}%` }} transition={spring} />)}
          {edges.map((x, i) => <span key={i} className="base-tick" style={{ left: `${x * 100}%` }} />)}
        </div>
        <div className="bal-bar thin" title="Det som publicerats hittills">
          {KINDS.map(([k]) => <i key={k} className={`k-${k}`} style={{ width: `${was[k] * 100}%` }} />)}
        </div>
      </div>
      <div className="bal-legend">
        {KINDS.map(([k, name]) => (
          <span key={k}><i className={`k-${k}`} />{name} <b>{Math.round(now[k] * 100)}</b><em>/{Math.round(BASE[k] * 100)}</em></span>
        ))}
      </div>
    </button>
  )
}

/* ---------- Mixspåret under planen ---------- */
function MixCol({ c, tiny, moving }) {
  if (!c) return <div className="mixcol empty" />
  const f = fp(c)
  return (
    <motion.div layout className={`mixcol ${tiny ? 'tiny' : ''} ${moving ? 'incoming' : ''}`} transition={spring}>
      <i className={`fam k-${f.kind}`} />
      <span className="cast">{Array.from({ length: f.cast }, (_, k) => <b key={k} />)}</span>
    </motion.div>
  )
}

function MixRow({ plan, slots, movingId }) {
  return (
    <div className="mixrow">
      {Array.from({ length: slots }, (_, i) => (
        <MixCol key={plan[i]?.id || 'e' + i} c={plan[i]} moving={plan[i] && plan[i].id === movingId} />
      ))}
    </div>
  )
}

/* ---------- Serier och upprepat format, ritat ovanför planen ---------- */
function Overlays({ plan }) {
  const arcs = []
  plan.forEach((c, i) => {
    if (c.series || c.status !== 'ready') return
    for (let j = i + 1; j <= Math.min(i + 4, plan.length - 1); j++) {
      if (plan[j].format === c.format && !plan[j].series && plan[j].status === 'ready') arcs.push([i, j])
    }
  })
  const series = {}
  plan.forEach((c, i) => { if (c.series) (series[c.series] ||= []).push(i) })
  return (
    <svg className="overlays" width="100%" height="56" aria-hidden="true">
      {Object.entries(series).map(([name, idx]) => {
        const a = Math.min(...idx), b = Math.max(...idx)
        const gaps = b - a + 1 - idx.length
        return (
          <motion.g key={name} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <motion.line animate={{ x1: slotX(a) - SLOT / 2 + 8, x2: slotX(b) + SLOT / 2 - 8 }} y1="30" y2="30"
              className={`series ${gaps ? 'broken' : ''}`} transition={spring} />
            {idx.map(i => <motion.circle key={i} animate={{ cx: slotX(i) }} cy="30" r="4" className="series-dot" transition={spring} />)}
            <motion.text animate={{ x: slotX(a) - SLOT / 2 + 8 }} y="22" className="series-name" transition={spring}>{name}</motion.text>
          </motion.g>
        )
      })}
      <AnimatePresence>
        {arcs.map(([i, j]) => {
          const x1 = slotX(i), x2 = slotX(j), h = 14 + (j - i) * 6
          return (
            <motion.path key={`${plan[i].id}-${plan[j].id}`} className="arc"
              d={`M ${x1} 54 Q ${(x1 + x2) / 2} ${54 - h * 2} ${x2} 54`}
              initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }} exit={{ opacity: 0 }}
              transition={{ duration: 0.6 }} />
          )
        })}
      </AnimatePresence>
    </svg>
  )
}

/* ---------- Plats i planen ---------- */
// Planen tar bara emot godkända klipp, så länkar släpps aldrig här: de går via bänken.
function Slot({ i, children, alts, activeFrom, dragging, beckon }) {
  const { setNodeRef, isOver } = useDroppable({ id: `slot:${i}` })
  const empty = !children
  const side = activeFrom > -1 && activeFrom < i ? 'right' : 'left'
  return (
    <div className={`slot ${i < 2 ? 'near' : ''} ${empty ? 'empty' : ''} ${dragging ? 'dragging' : ''} ${beckon ? 'beckon' : ''} ${isOver && dragging ? 'over' : ''}`}>
      <span className="pos">{i === 0 ? 'nu' : `+${i}`}</span>
      <div ref={setNodeRef} className="slot-drop">
        {isOver && dragging && !empty && <motion.span layoutId="insert" className={`insert ${side}`} />}
        {empty ? <div className="hole sk off" aria-label={`Tom plats ${i}`} /> : children}
      </div>
      {alts}
    </div>
  )
}

/* ---------- Trion: 1 och 3 i en ram under kortet. Fälls ut vid hovring och drag, dras in snabbt. ---------- */
function Alts({ host, dragging, activeId, onHover, onMenu, onLink }) {
  return (
    <div className="alts">
      {[1, 3].map(n => {
        const alt = host.alts?.[n]
        return alt
          ? <AltCard key={n} n={n} c={alt} hostId={host.id} onHover={onHover} onMenu={onMenu} />
          : <AltHole key={n} n={n} hostId={host.id} show={dragging && activeId !== host.id} />
      })}
    </div>
  )
}

// Tar emot en länk som dras in från webbläsaren.
const linkDrop = (onLink, setOver) => ({
  onDragOver: e => { if ([...e.dataTransfer.types].some(t => t === 'text/uri-list' || t === 'text/plain')) { e.preventDefault(); e.stopPropagation(); setOver(true) } },
  onDragLeave: () => setOver(false),
  onDrop: e => { e.preventDefault(); setOver(false); const u = e.dataTransfer.getData('text/uri-list') || e.dataTransfer.getData('text/plain'); if (u) onLink(u.trim()) },
})

// Ett alternativ går både att dra och att släppa på.
function AltCard({ n, c, hostId, onHover, onMenu }) {
  const { attributes, listeners, setNodeRef: dragRef, isDragging } = useDraggable({ id: c.id })
  const { setNodeRef: dropRef, isOver } = useDroppable({ id: `alt:${hostId}:${n}` })
  return (
    <motion.div ref={el => { dragRef(el); dropRef(el) }} {...listeners} {...attributes} layoutId={c.id} layout transition={spring}
      className={`alt dcard ${n === 3 ? 'wild' : ''} ${isDragging ? 'ghosted' : ''} ${isOver ? 'over' : ''}`}
      onMouseEnter={() => onHover(n)} onMouseLeave={() => onHover(null)}
      onContextMenu={e => onMenu(e, c, n)} title={c.title}>
      <span className="altnum">{n}</span>
      <CardFace c={c} tiny />
    </motion.div>
  )
}

function AltHole({ n, hostId, show }) {
  const { setNodeRef, isOver } = useDroppable({ id: `alt:${hostId}:${n}` })
  return (
    <div ref={setNodeRef} className={`alt hole-alt ${n === 3 ? 'wild' : ''} ${show ? 'show' : ''} ${isOver ? 'over' : ''}`}>
      <span className="altnum">{n}</span>
    </div>
  )
}

// Huvudkortet tar emot sina egna 1 och 3: släpp upp så byter de plats.
function MainDrop({ host, activeId, children }) {
  const own = [1, 3].some(n => host.alts?.[n]?.id === activeId)
  const { setNodeRef, isOver } = useDroppable({ id: `alt:${host.id}:main`, disabled: !own })
  return <div ref={setNodeRef} className={`maindrop ${isOver ? 'over' : ''}`}>{children}</div>
}

/* ---------- Kort ---------- */
function DraggableCard({ c, flash, dropped, onNote, small, onMenu, onDoubleClick, onApprove }) {
  const usable = !c.status || c.status === 'ready'
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id: c.id, disabled: !on(3) || !usable })
  return (
    <motion.div ref={setNodeRef} {...listeners} {...(usable ? attributes : {})}
      layoutId={dropped ? undefined : c.id} layout={!dropped}
      initial={dropped ? { scale: 0.92, rotate: 3, x: 8 } : false} animate={{ scale: 1, rotate: 0, x: 0 }}
      transition={spring}
      onDoubleClick={onDoubleClick}
      onContextMenu={on(3) && onMenu ? onMenu : undefined}
      className={`dcard ${on(3) && usable ? '' : 'still'} ${isDragging ? 'ghosted' : ''}`}>
      <CardFace c={c} flash={flash} small={small} />
      {c.status === 'review' && (
        <motion.button className="review sk" initial={{ scale: 0.6, rotate: -8 }} animate={{ scale: 1, rotate: -4 }} transition={spring}
          onPointerDown={e => e.stopPropagation()} onClick={() => onApprove?.(c.id)} title="Godkänn den neutrala versionen">
          att granska
        </motion.button>
      )}
      {onNote && c.fresh && c.status === 'ready' && (
        <motion.textarea className="note sk" rows={2} placeholder="✎ din tanke" value={c.cmNote}
          initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
          onPointerDown={e => e.stopPropagation()} onKeyDown={e => { e.stopPropagation(); if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); e.currentTarget.blur() } }}
          onChange={e => onNote(e.target.value)} onBlur={e => onNote(e.target.value, true)} />
      )}
    </motion.div>
  )
}

// Ett orört klipp ser ut som originalet (någon annans video). Ett klipp CM har tänkt på bär CM:s handstil.
function CardFace({ c, small, tiny, flash }) {
  const orig = !c.touched
  const backs = on(4) && !tiny && !small && c.alts ? [1, 3].filter(n => c.alts[n]) : []
  return (
    <div className={`card ${small ? 'small' : ''} ${tiny ? 'tiny' : ''} ${orig ? 'orig' : ''} ${flash ? 'flash' : ''}`}>
      <div className="stack">
      <AnimatePresence>
        {backs.map(n => (
          <motion.div key={n} className={`ghost sk ${n === 3 ? 'wildback' : ''}`}
            initial={{ opacity: 0, rotate: 0, x: 0 }} animate={{ opacity: 1, rotate: n === 1 ? -5 : 5, x: n === 1 ? -7 : 7, y: -3 }}
            exit={{ opacity: 0, rotate: 0, x: 0 }} transition={spring}>
            <span className={`famtab k-${fp(c.alts[n]).kind}`} />
            <span className={`gnum ${n === 1 ? 'l' : 'r'}`}>{n}</span>
          </motion.div>
        ))}
      </AnimatePresence>
      <div className="face sk">
        <Thumb c={c} small={small || tiny} />
        {on(3) && (!c.status || c.status === 'ready' || c.status === 'review') && <span className={`famtab k-${fp(c).kind}`} />}
        {on(3) && !tiny && (
          <span className="fpo" aria-hidden="true">
            <i className={`k-${fp(c).kind}`} />{KINDS.find(([k]) => k === fp(c).kind)[1]}
            <span className="fpo-cast">{Array.from({ length: fp(c).cast }, (_, k) => <b key={k} />)}</span>
          </span>
        )}
        {orig && !tiny && c.handle && c.status !== 'fetch' && c.status !== 'cut' && c.status !== 'queued' && <span className="handle">{c.handle}</span>}
        {on(2) && c.chosen && !tiny && (
          <motion.span key={c.chosen} className="front cust" initial={{ scale: 0.4 }} animate={{ scale: 1 }} transition={spring}>{c.chosen}</motion.span>
        )}
        <AnimatePresence>
          {on(2) && !tiny && c.mark && c.mark !== 'chose' && (
            <motion.span key={c.mark} className={`mark m-${c.mark}`} initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }} transition={spring}>
              {{ back: '↩', no: '✕', new: '✓', reused: '↻' }[c.mark]}
            </motion.span>
          )}
        </AnimatePresence>
        {on(2) && tiny && c.mark === 'new' && <span className="mark m-new mini">✓</span>}
      </div>
      </div>
      {!tiny && <div className="title">{c.title}</div>}
      {!tiny && !c.fresh && c.touched && c.cmNote && <div className="hand">{c.cmNote}</div>}
    </div>
  )
}

/* ---------- Bänken: CM:s klipp för just den här kunden ---------- */
function Bench({ bench, flash, dropped, dragging, onMenu, onLink, onAdd, noteFor, onApprove }) {
  const { setNodeRef, isOver } = useDroppable({ id: 'bench' })
  const [linkOver, setLinkOver] = useState(false)
  return (
    <aside ref={setNodeRef} {...(on(5) ? linkDrop(onLink, setLinkOver) : {})}
      className={`bench ${(isOver && dragging) || linkOver ? 'over' : ''} ${dragging ? 'dragging' : ''}`} aria-label="Bänken">
      <div className="bench-grid">
        {on(5) && <button className="benchadd sk" onClick={onAdd} aria-label="Lägg in klipp"><span className="plus">+</span></button>}
        <AnimatePresence>
          {bench.map(c => (
            <DraggableCard key={c.id} c={c.status === 'queued' ? { ...c, qpos: queuePos(bench, c.id) } : c} small flash={flash.includes(c.id)} dropped={dropped === c.id} onMenu={e => onMenu(e, c)}
              onNote={noteFor(c.id)} onApprove={onApprove} />
          ))}
        </AnimatePresence>
      </div>
    </aside>
  )
}

const queuePos = (bench, id) => bench.filter(c => c.status === 'queued').sort((a, b) => a.queuedAt - b.queuedAt).findIndex(c => c.id === id) + 1

// Popupen: klistra in en eller flera länkar, eller en spellista som blir flera hämtningar.
const isPlaylist = u => /playlist|\/collection\//i.test(u)
const PLAYLIST_SIZE = 5
function parseLinks(text) {
  return text.split(/\s+/).filter(t => /^https?:\/\//.test(t) || t.includes('tiktok')).map(u => ({ u, list: isPlaylist(u) }))
}

function Intake({ initial, onClose, onFetch }) {
  const [text, setText] = useState(initial)
  const links = parseLinks(text)
  const urls = links.flatMap(l => (l.list ? Array.from({ length: PLAYLIST_SIZE }, (_, k) => `${l.u}#${k + 1}`) : [l.u]))
  useEffect(() => {
    const k = e => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [])
  return (
    <motion.div className="scrim" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onPointerDown={onClose}>
      <motion.div className="intake sk" onPointerDown={e => e.stopPropagation()}
        initial={{ y: 16, scale: 0.97, rotate: -0.5 }} animate={{ y: 0, scale: 1, rotate: 0 }} exit={{ y: 10, scale: 0.98 }} transition={spring}>
        <textarea id="intake-text" autoFocus rows={3} value={text} onChange={e => setText(e.target.value)}
          placeholder="Klistra in TikTok-länkar eller en spellista"
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && urls.length) { e.preventDefault(); onFetch(urls) } }} />
        <ul className="intake-list">
          {links.map(l => (
              <li key={l.u}>
                <span className={`ico ${l.list ? 'list' : ''}`}>{l.list ? '≣' : '▶'}</span>
                <span className="u">{shortUrl(l.u)}</span>
                {l.list && <span className="n">{PLAYLIST_SIZE} klipp</span>}
              </li>
            ))}
        </ul>
        <div className="intake-foot">
          <span className="eta">{urls.length ? `ca 1 min per klipp · landar på bänken` : ''}</span>
          <button className="btn-go sk" disabled={!urls.length} onClick={() => onFetch(urls)}>Hämta{urls.length ? ` ${urls.length}` : ''}</button>
        </div>
      </motion.div>
    </motion.div>
  )
}

/* ---------- Högerklicksmeny. Hovra ett val så visar mixen följden. ---------- */
function Menu({ menu, st, onAct, onPreview }) {
  const i = st.plan.findIndex(x => x.id === menu.id)
  let items
  const host = st.plan[i]
  if (menu.where === 'plan') items = [
    on(4) && host?.alts && (host.alts[1] || host.alts[3]) && [{ kind: 'rotate', host: menu.id }, '⟳', 'Nästa i trion'],
    i > 0 && [{ kind: 'earlier', id: menu.id }, '←', 'Tidigare'],
    i < st.plan.length - 1 && [{ kind: 'later', id: menu.id }, '→', 'Senare'],
    [{ kind: 'bench', id: menu.id }, '↙', 'Till bänken'],
    ...(on(4) ? [1, 3].filter(n => host?.alts?.[n]).map(n => [{ kind: 'bench', id: host.alts[n].id }, String(n), `${n} till bänken`]) : []),
  ]
  else if (menu.where === 'alt') items = [
    [{ kind: 'promote', host: menu.host, n: menu.n }, '★', 'Gör till 2'],
    [{ kind: 'bench', id: menu.id }, '↙', 'Till bänken'],
  ]
  else items = [
    [{ kind: 'toPlan', id: menu.id }, '↗', 'Till planen'],
    [{ kind: 'library', id: menu.id }, '✕', 'Tillbaka till biblioteket'],
  ]
  return (
    <motion.div className="cmenu sk" style={{ left: Math.min(menu.x, innerWidth - 220), top: Math.min(menu.y, innerHeight - 150) }}
      initial={{ opacity: 0, scale: 0.94, y: -4 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.12 }} onPointerDown={e => e.stopPropagation()} onMouseLeave={() => onPreview(null)}>
      {items.filter(Boolean).map(([op, g, label]) => (
        <button key={label} onClick={() => onAct(op)} onMouseEnter={() => onPreview(op)} onFocus={() => onPreview(op)}>
          <span className="g">{g}</span>{label}
        </button>
      ))}
    </motion.div>
  )
}

/* ---------- Iterationsväljare (utvecklarstöd, inte en del av designen) ---------- */
function Stepper() {
  return (
    <nav className="stepper" aria-label="Iteration">
      {STEPS.map((name, i) => (
        <a key={i} href={`#${i + 1}`} className={STEP === i + 1 ? 'on' : STEP > i + 1 ? 'done' : ''} title={name}>{i + 1}</a>
      ))}
      <span>{STEPS[STEP - 1]}</span>
    </nav>
  )
}
