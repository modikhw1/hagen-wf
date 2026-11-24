import { motion } from 'motion/react'

// Lokalen. Ritas likadant i varje scen; bara personerna gör olika saker.
function Lokal() {
  return (
    <g className="vf-env">
      <rect x="-300" y="-200" width="1000" height="430" className="vf-wall" />
      <rect x="-300" y="230" width="1000" height="300" className="vf-floor" />
      {Array.from({ length: 14 }, (_, i) => <path key={i} d={`M${-260 + i * 70} 230 L${-420 + i * 110} 520`} className="vf-tile" />)}
      <path d="M-300 230 H700" className="vf-line" />
      {/* lampa */}
      <path d="M205 -200 V30" className="vf-line" />
      <path d="M188 42 Q205 22 222 42 Z" className="vf-line vf-fill" />
      {/* meny på väggen */}
      <rect x="150" y="56" width="110" height="40" rx="3" className="vf-line vf-fill" />
      <path d="M160 68 H210 M160 77 H236 M160 86 H200" className="vf-line thin" />
      {/* dörr */}
      <rect x="124" y="108" width="54" height="122" className="vf-line vf-fill" />
      <circle cx="170" cy="172" r="2.5" className="vf-line" />
      <rect x="132" y="118" width="38" height="40" className="vf-line thin" />
      {/* ugn */}
      <path d="M302 230 V150 Q335 112 368 150 V230" className="vf-line vf-fill" />
      <path d="M318 196 Q335 176 352 196 Z" className="vf-line vf-dark" />
      <path d="M335 112 V60 M328 60 H342" className="vf-line" />
    </g>
  )
}

const Head = ({ x, y }) => <circle cx={x} cy={y} r="11" className="vf-body vf-fill" />

// Marco står bakom disken: axlar, förkläde och armar med armbåge, så att armarna inte läses som ben.
function Marco({ x, arms }) {
  const L = [x - 12, 137]
  const R = [x + 12, 137]
  const A = {
    knead: [[[x - 22, 156], [x - 8, 170]], [[x + 22, 156], [x + 8, 170]]],
    rest: [[[x - 17, 156], [x - 15, 174]], [[x + 17, 156], [x + 15, 174]]],
    offer: [[[x - 22, 146], [x - 36, 150]], [[x + 17, 156], [x + 15, 174]]],
    up: [[[x - 22, 120], [x - 20, 98]], [[x + 22, 120], [x + 20, 98]]],
  }[arms]
  return (
    <g className="vf-marco">
      <path d={`M${L[0]} ${L[1]} Q${x} 130 ${R[0]} ${R[1]} L${x + 10} 200 H${x - 10} Z`} className="vf-body vf-fill" />
      <path d={`M${x - 7} 148 H${x + 7} V170 H${x - 7} Z`} className="vf-body thin" />
      {A.map(([e, h], i) => <path key={i} d={`M${(i ? R : L).join(' ')} L${e.join(' ')} L${h.join(' ')}`} className="vf-body" />)}
      <Head x={x} y={118} />
      <path d={`M${x - 10} 108 V96 Q${x - 12} 88 ${x - 4} 90 Q${x} 82 ${x + 4} 90 Q${x + 12} 88 ${x + 10} 96 V108 Z`} className="vf-body vf-fill" />
      {arms === 'offer' && <path d={`M${x - 36} 150 l-14 -4 l6 12 Z`} className="vf-body vf-slice" />}
    </g>
  )
}

function Nonna({ x, arms }) {
  const sh = [x, 142]
  const A = {
    rest: [[x - 13, 178], [x + 13, 178]],
    cross: [[x + 9, 160], [x - 9, 157]],
    eat: [[x - 13, 178], [x + 3, 127]],
    thumb: [[x - 13, 178], [x + 22, 140]],
  }[arms]
  return (
    <g className="vf-nonna">
      <path d={`M${x} 131 V150 M${x} 150 L${x - 17} 214 H${x + 17} Z`} className="vf-body vf-fill" />
      <path d={`M${x - 6} 214 V230 M${x + 6} 214 V230`} className="vf-body" />
      {arms === 'cross'
        ? <path d={`M${x - 8} 143 L${x - 10} 158 L${x + 10} 155 M${x + 8} 143 L${x + 10} 161 L${x - 9} 158`} className="vf-body" />
        : A.map(([hx, hy], i) => <path key={i} d={`M${sh[0]} ${sh[1]} L${hx} ${hy}`} className="vf-body" />)}
      <Head x={x} y={120} />
      <circle cx={x} cy={105} r="5.5" className="vf-body vf-fill" />
      {arms === 'eat' && <path d={`M${x + 3} 127 l12 -3 l-7 10 Z`} className="vf-body vf-slice" />}
      {arms === 'thumb' && <path d={`M${x + 22} 140 V130`} className="vf-body" />}
    </g>
  )
}

export function World({ pose }) {
  return (
    <g>
      <Lokal />
      {pose.marco && <Marco {...pose.marco} />}
      {/* disken framför Marco: deg och pizza ligger alltid där */}
      <rect x="186" y="175" width="118" height="55" className="vf-line vf-fill" />
      <ellipse cx="245" cy="173" rx="13" ry="4" className="vf-line vf-dough" />
      <ellipse cx="282" cy="172" rx="15" ry="4" className="vf-line vf-pizza" />
      {pose.nonna && <Nonna {...pose.nonna} />}
    </g>
  )
}

// Kamerans läge: utsnittet som en viewBox (skarpt i alla zoomnivåer) och lutningen som 3D på lagret.
// Utsnittet räknas mot en fast 9:16-ram i världen, så att rutan och telefonen visar samma bild.
const REF = { w: 168, h: 300 }
const vb = (s) => {
  const w = REF.w / s.z
  const h = REF.h / s.z
  return `${(s.cx - w / 2).toFixed(2)} ${(s.cy - h / 2).toFixed(2)} ${w.toFixed(2)} ${h.toFixed(2)}`
}
export function camPose(s, W, H) {
  return { view: { viewBox: vb(s) }, cam: { rotateX: s.rx, rotateY: s.ry, rotateZ: s.dutch } }
}

// Rörelsen under en scen, som nyckelbilder från start till slut.
export function camMove(s, W, H) {
  const a = s.amp
  const at = o => camPose({ ...s, ...o }, W, H)
  const m = s.move
  const frames =
    m === 'drift' ? [at({ z: s.z }), at({ z: s.z * 1.06 })]
    : m === 'push' ? [at({ z: s.z }), at({ z: s.z * (1 + 0.4 * a) })]
    : m === 'pan' ? [at({ cx: s.cx - 30 * a }), at({ cx: s.cx + 30 * a })]
    : m === 'orbit' ? [at({ ry: s.ry - 22 * a }), at({ ry: s.ry + 22 * a })]
    : m === 'hand' ? [0, 1, 2, 3, 4].map(k => at({ cx: s.cx + [0, 4, -3, 5, -2][k] * a, cy: s.cy + [0, -3, 4, -2, 3][k] * a, dutch: s.dutch + [0, 1.5, -1.2, 1, -1.5][k] * a }))
    : [at({}), at({})]
  const pick = key => Object.fromEntries(Object.keys(frames[0][key]).map(k => [k, frames.map(f => f[key][k])]))
  return { view: pick('view'), cam: pick('cam') }
}

const springy = { type: 'spring', stiffness: 260, damping: 30 }
const first = o => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, v[0]]))

// En bildruta. Stillbild: kameran glider till sitt nya läge när reglaget dras.
// Spelar: kameran rör sig under scenens längd.
export default function Frame({ scene, s, W, H, playing, dur }) {
  const still = camPose(s, W, H)
  const moving = playing ? camMove(s, W, H) : null
  const t = playing ? { duration: dur, ease: s.move === 'hand' ? 'linear' : 'easeInOut' } : springy
  return (
    <div className="vf-frame" style={{ width: W, height: H }}>
      <motion.div className="vf-cam" initial={moving ? first(moving.cam) : false} animate={moving ? moving.cam : still.cam} transition={t}>
        <motion.svg
          width={W} height={H} className="vf-world-svg" preserveAspectRatio="xMidYMid slice"
          initial={moving ? first(moving.view) : false} animate={moving ? moving.view : still.view} transition={t}
        >
          <World pose={scene.pose} />
        </motion.svg>
      </motion.div>
    </div>
  )
}
