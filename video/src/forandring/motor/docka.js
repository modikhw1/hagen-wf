import * as THREE from 'three'
import { JOINTS, PARENT, OFFSET, INDEX } from './skelett'

// En docka: 22 ben enligt skelettet, kroppsdelar som stela former på benen.
// Inte skinnad mesh än. Utseendet kan bytas mot en VRM-avatar på samma skelett senare.

let gradient
export function toonGradient() {
  if (gradient) return gradient
  const data = new Uint8Array([90, 90, 90, 255, 175, 175, 175, 255, 255, 255, 255, 255])
  gradient = new THREE.DataTexture(data, 3, 1, THREE.RGBAFormat)
  gradient.minFilter = gradient.magFilter = THREE.NearestFilter
  gradient.needsUpdate = true
  return gradient
}
export const toon = color => new THREE.MeshToonMaterial({ color, gradientMap: toonGradient() })
const toonFarg = toon

const UP = new THREE.Vector3(0, 1, 0)

// En kapsel från en led till en punkt i ledens eget rum.
function limb(to, r, mat) {
  const v = new THREE.Vector3(...to)
  const len = v.length()
  const g = new THREE.CapsuleGeometry(r, Math.max(0.001, len - r * 0.4), 6, 12)
  const m = new THREE.Mesh(g, mat)
  m.position.copy(v).multiplyScalar(0.5)
  m.quaternion.setFromUnitVectors(UP, v.clone().normalize())
  m.castShadow = true
  return m
}
function blob(pos, scale, mat) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), mat)
  m.position.set(...pos)
  m.scale.set(...scale)
  m.castShadow = true
  return m
}

export const FIGURER = {
  marco: {
    skala: 1.04,
    hud: '#e3b08a', overdel: '#f6f3ec', underdel: '#3b3d48', skor: '#2a2a2a', har: '#3a2a20',
    tillbehor: ['kockmossa', 'forklade'],
  },
  nonna: {
    skala: 0.92,
    hud: '#eec7a6', overdel: '#7c4d6b', underdel: '#4a5160', skor: '#3a2f2a', har: '#d7d2ca',
    tillbehor: ['knut', 'kjol'], // glasögonen skymde ögonen för ansiktsdetektorn (bryggan)
  },
}

// stil 'foto': fysiskt material (ljus och skugga som i ett foto) i stället för tecknat, för
// rekonstruktioner där bakgrunden är originalets rena skiva. Analysens detektorer känner då igen
// dockan som en människa mycket oftare (bryggan för rekonstruktioner mäter det).
export function buildDocka(spec, { stil } = {}) {
  const s = spec.skala
  const toon = stil === 'foto' ? farg => new THREE.MeshStandardMaterial({ color: farg, roughness: 0.78, metalness: 0 }) : toonFarg
  const M = {
    hud: toon(spec.hud), over: toon(spec.overdel), under: toon(spec.underdel),
    skor: toon(spec.skor), har: toon(spec.har), vit: toon('#ffffff'), mork: toon('#1f1f1f'),
  }
  const root = new THREE.Group()
  const bones = JOINTS.map(j => {
    const b = new THREE.Group()
    b.name = j
    b.position.set(...OFFSET[j]).multiplyScalar(s)
    return b
  })
  bones.forEach((b, i) => (PARENT[i] < 0 ? root : bones[PARENT[i]]).add(b))
  const B = j => bones[INDEX[j]]
  const off = j => OFFSET[j].map(x => x * s)
  const has = t => spec.tillbehor.includes(t)

  // ben
  for (const side of ['left', 'right']) {
    B(`${side}_hip`).add(limb(off(`${side}_knee`), 0.068 * s, has('kjol') ? M.hud : M.under))
    B(`${side}_knee`).add(limb(off(`${side}_ankle`), 0.052 * s, has('kjol') ? M.hud : M.under))
    const foot = new THREE.Mesh(new THREE.BoxGeometry(0.09 * s, 0.07 * s, 0.22 * s), M.skor)
    foot.position.set(0, -0.035 * s, 0.06 * s)
    foot.castShadow = true
    B(`${side}_ankle`).add(foot)
    // armar
    B(`${side}_collar`).add(limb(off(`${side}_shoulder`), 0.05 * s, M.over))
    B(`${side}_shoulder`).add(limb(off(`${side}_elbow`), 0.047 * s, M.over))
    B(`${side}_elbow`).add(limb(off(`${side}_wrist`), 0.04 * s, has('forklade') ? M.hud : M.over))
    const dir = side === 'left' ? 1 : -1
    B(`${side}_wrist`).add(blob([dir * 0.06 * s, 0, 0], [0.06 * s, 0.035 * s, 0.045 * s], M.hud))
  }
  // bål
  B('pelvis').add(blob([0, 0.0, 0], [0.16 * s, 0.11 * s, 0.11 * s], M.under))
  B('spine1').add(blob([0, 0.06 * s, 0.01], [0.15 * s, 0.12 * s, 0.11 * s], M.over))
  B('spine3').add(blob([0, 0.06 * s, 0.0], [0.19 * s, 0.17 * s, 0.12 * s], M.over))
  B('neck').add(limb(off('head'), 0.045 * s, M.hud))
  // huvud
  const head = B('head')
  head.add(blob([0, 0.08 * s, 0.01 * s], [0.1 * s, 0.12 * s, 0.11 * s], M.hud))
  head.add(blob([0, 0.06 * s, 0.11 * s], [0.018 * s, 0.025 * s, 0.022 * s], M.hud)) // näsa: visar vart hen tittar
  // ansikte: ögonvitor med iris, bryn, öron, näsa och läppar. Tillräckligt mänskligt för att
  // ansikts- och persondetektorerna i analysen ska känna igen dockan (bryggan mäter hur ofta).
  const vit = toon('#fbf8f2')
  const iris = toon('#3b2a20')
  const lapp = toon(spec.lappar ?? '#b5615a')
  for (const x of [-0.038, 0.038]) {
    head.add(blob([x * s, 0.095 * s, 0.097 * s], [0.022 * s, 0.014 * s, 0.01 * s], vit))
    head.add(blob([x * s, 0.094 * s, 0.105 * s], [0.009 * s, 0.01 * s, 0.006 * s], iris))
    const bryn = new THREE.Mesh(new THREE.BoxGeometry(0.036 * s, 0.008 * s, 0.01 * s), M.har)
    bryn.position.set(x * s, 0.123 * s, 0.099 * s)
    bryn.rotation.z = x > 0 ? -0.12 : 0.12
    head.add(bryn)
    head.add(blob([x * 2.6 * s, 0.075 * s, 0.0], [0.014 * s, 0.028 * s, 0.02 * s], M.hud)) // öra
  }
  head.add(blob([0, 0.065 * s, 0.112 * s], [0.016 * s, 0.03 * s, 0.02 * s], M.hud)) // näsrygg
  head.add(blob([0, 0.032 * s, 0.1 * s], [0.026 * s, 0.009 * s, 0.01 * s], lapp)) // läppar
  head.add(blob([0, 0.13 * s, -0.02 * s], [0.105 * s, 0.08 * s, 0.11 * s], M.har))

  if (has('kockmossa')) {
    const hat = new THREE.Mesh(new THREE.CylinderGeometry(0.1 * s, 0.09 * s, 0.13 * s, 18), M.vit)
    hat.position.set(0, 0.25 * s, -0.01 * s)
    hat.castShadow = true
    head.add(hat)
    head.add(blob([0, 0.33 * s, -0.01 * s], [0.13 * s, 0.07 * s, 0.13 * s], M.vit))
  }
  if (has('forklade')) {
    const ap = new THREE.Mesh(new THREE.BoxGeometry(0.28 * s, 0.62 * s, 0.02 * s), M.vit)
    ap.position.set(0, -0.12 * s, 0.165 * s)
    ap.castShadow = true
    B('spine1').add(ap)
  }
  if (has('knut')) head.add(blob([0, 0.19 * s, -0.08 * s], [0.06 * s, 0.06 * s, 0.06 * s], M.har))
  if (has('glasogon')) {
    for (const x of [-0.04, 0.04]) {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.03 * s, 0.0032 * s, 6, 20), M.mork)
      ring.position.set(x * s, 0.095 * s, 0.112 * s)
      head.add(ring)
    }
  }
  if (has('kjol')) {
    const sk = new THREE.Mesh(new THREE.CylinderGeometry(0.15 * s, 0.27 * s, 0.6 * s, 20, 1, true), M.under)
    sk.material = M.under.clone()
    sk.material.side = THREE.DoubleSide
    sk.position.set(0, -0.26 * s, 0)
    sk.castShadow = true
    B('pelvis').add(sk)
  }

  // Rekvisita i höger hand. Byggs en gång och visas när manuset säger det.
  const props = {}
  const handProp = kind => {
    if (props[kind]) return props[kind]
    const g = new THREE.Group()
    if (kind === 'pizzabit') {
      const shape = new THREE.Shape()
      shape.moveTo(0, 0)
      shape.lineTo(-0.075, 0.16)
      shape.quadraticCurveTo(0, 0.18, 0.075, 0.16)
      shape.lineTo(0, 0)
      const geo = new THREE.ExtrudeGeometry(shape, { depth: 0.012, bevelEnabled: false })
      const bit = new THREE.Mesh(geo, toon('#e8b27a'))
      bit.castShadow = true
      g.add(bit)
      for (const [x, y] of [[-0.02, 0.09], [0.025, 0.12], [0, 0.05]]) {
        const p = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.006, 10), toon('#c4472f'))
        p.rotation.x = Math.PI / 2
        p.position.set(x, y, 0.014)
        g.add(p)
      }
      g.userData.coco = 'pizza' // så som objektdetektorn (COCO) kallar den
      g.rotation.set(0, 0, Math.PI / 2)
      g.position.set(-0.09 * s, 0.0, 0.0)
    }
    g.visible = false
    B('right_wrist').add(g)
    props[kind] = g
    return g
  }

  handProp('pizzabit') // byggs direkt, så att den får kontur som allt annat

  // fotostil: mänskliga proportioner. Det tecknade huvudet är för stort (24 cm brett) och bålen är
  // tre separata klot; en riktig kropp har ett huvud på ~15 × 23 cm och en sammanhängande bål.
  if (stil === 'foto') {
    const f = new THREE.Vector3(0.78, 0.9, 0.85)
    for (const c of head.children) { c.position.multiply(f); c.scale.multiply(f) }
    const bal = limb([0, 0.36 * s, -0.01 * s], 0.135 * s, M.over)
    bal.scale.set(1.2, 1, 0.78) // bredare än djup
    B('spine1').add(bal)
    B('pelvis').add(limb([0, 0.14 * s, 0], 0.13 * s, M.under))
  }

  const tmp = new THREE.Vector3()
  return {
    root,
    bones,
    skala: s,
    // Visa en sak i höger hand, eller ingen (null).
    setProp(kind) {
      for (const [k, g] of Object.entries(props)) g.visible = k === kind
      if (kind && !props[kind]) handProp(kind).visible = true
    },
    // Sätt pose: 22 lokala kvaternioner, plats (x, z), riktning i grader, höjd på bäckenet.
    setPose(quats, x, z, yaw, lift = 0) {
      root.position.set(x, 0, z)
      root.rotation.set(0, yaw * THREE.MathUtils.DEG2RAD, 0)
      bones.forEach((b, i) => b.quaternion.copy(quats[i]))
      B('pelvis').position.set(OFFSET.pelvis[0] * s, OFFSET.pelvis[1] * s + lift, OFFSET.pelvis[2] * s)
    },
    // Ledernas plats i världen, för kameran och mätningen.
    joints() {
      root.updateMatrixWorld(true)
      return bones.map(b => b.getWorldPosition(tmp).clone())
    },
  }
}
