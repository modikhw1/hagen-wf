import * as THREE from 'three'

// Kameran i en scen. Orden kommer ur CameraBench (Lin m.fl. 2025), som togs fram med filmfotografer:
// static, pan, tilt, roll, dolly, truck, pedestal, zoom, arc, tracking. Samma ord som AI:n skriver
// och som biblioteket märker riktiga klipp med, så att varianter och original kan jämföras ord för ord.
//
// En inställning: utsnitt + mål + vinkel + höjd. Sedan läggs operationer på över scenens tid.

// Hur mycket av motivet som syns på höjden (meter) i en stående 9:16-bild.
export const UTSNITT = { total: 3.3, halvtotal: 1.95, halvbild: 1.2, nara: 0.62, extrem: 0.3 }
export const OPS = ['static', 'pan', 'tilt', 'roll', 'dolly', 'truck', 'pedestal', 'zoom', 'arc', 'tracking']

// Dessa går från 0 till mängd; övriga är symmetriska kring inställningen (−mängd/2 … +mängd/2).
const FRAN_NOLL = new Set(['dolly', 'truck', 'pedestal', 'zoom'])

const D = THREE.MathUtils.DEG2RAD
const ease = x => (x < 0.5 ? 2 * x * x : 1 - (-2 * x + 2) ** 2 / 2)
const clamp01 = x => Math.max(0, Math.min(1, x))

// Deterministiskt "handhållet": summa av sinusar, samma t ger samma skak.
const skakv = (t, seed) => [
  Math.sin(t * 7.3 + seed) * 0.6 + Math.sin(t * 13.1 + seed * 2) * 0.3 + Math.sin(t * 2.1 + seed * 3) * 0.5,
  Math.sin(t * 6.1 + seed * 5) * 0.6 + Math.sin(t * 11.7 + seed * 7) * 0.3 + Math.sin(t * 1.7 + seed) * 0.5,
  Math.sin(t * 4.3 + seed * 11) * 0.7 + Math.sin(t * 9.9 + seed * 13) * 0.3,
]

// mal(u) ger målpunkten i världen vid scentiden u (för tracking); mal0 är målet vid scenens början.
// En kamera med bana (rekonstruerad ur ett riktigt klipp): position och orientering per ruta,
// { fps, ramar: [[x, y, z, qx, qy, qz, qw], …], lins }. Ger samma form som evalKamera i övrigt.
const _qa = new THREE.Quaternion(), _qb = new THREE.Quaternion()
function evalBana(b, u, fov) {
  const R = b.ramar
  const x = Math.max(0, Math.min(R.length - 1, u * b.fps))
  const i0 = Math.floor(x), i1 = Math.min(R.length - 1, i0 + 1), f = x - i0
  const pos = new THREE.Vector3(...R[i0].slice(0, 3)).lerp(new THREE.Vector3(...R[i1].slice(0, 3)), f)
  const q = _qa.set(...R[i0].slice(3, 7)).clone().slerp(_qb.set(...R[i1].slice(3, 7)), f)
  const look = pos.clone().add(new THREE.Vector3(0, 0, -1).applyQuaternion(q))
  return { pos, look, fov, roll: 0, quat: q }
}

export function evalKamera(k, u, dur, mal0, malU, seed = 1) {
  if (k.bana) return evalBana(k.bana, u, k.lins ?? 60)
  const fov0 = k.lins ?? 60 // ungefär huvudkameran i en mobil, stående
  const H = UTSNITT[k.utsnitt] ?? UTSNITT.halvbild
  const dist = k.dist ?? H / 2 / Math.tan((fov0 / 2) * D) // dist: relativa uttryck i rekonstruktioner
  const az = (k.vinkel ?? 0) * D
  const el = (k.hojd ?? 0) * D
  const look = mal0.clone()
  const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el))
  const pos = look.clone().addScaledVector(dir, dist)
  let fov = fov0
  let roll = 0
  const fwd = () => look.clone().sub(pos).normalize()
  const right = () => fwd().cross(new THREE.Vector3(0, 1, 0)).normalize()
  const nu = clamp01(u / dur)

  for (const op of k.ops ?? []) {
    const p = ease(clamp01((nu - (op.fran ?? 0)) / Math.max(1e-6, (op.till ?? 1) - (op.fran ?? 0))))
    const m = op.mangd ?? 0
    const v = FRAN_NOLL.has(op.op) ? m * p : m * (p - 0.5)
    switch (op.op) {
      case 'dolly': { const f = fwd(); const vv = Math.min(v, Math.max(0, pos.distanceTo(look) - 0.35)); pos.addScaledVector(f, vv); look.addScaledVector(f, vv); break } // aldrig närmare målet än 35 cm
      case 'truck': { const r = right(); pos.addScaledVector(r, v); look.addScaledVector(r, v); break }
      case 'pedestal': pos.y += v; look.y += v; break
      case 'pan': { const off = look.clone().sub(pos).applyAxisAngle(new THREE.Vector3(0, 1, 0), -v * D); look.copy(pos).add(off); break }
      case 'tilt': { const off = look.clone().sub(pos).applyAxisAngle(right(), v * D); look.copy(pos).add(off); break }
      case 'roll': roll += v; break
      case 'zoom': fov = 2 * Math.atan(Math.tan((fov0 / 2) * D) / (1 + v)) / D; break
      case 'arc': { const off = pos.clone().sub(look).applyAxisAngle(new THREE.Vector3(0, 1, 0), v * D); pos.copy(look).add(off); break }
      case 'tracking': { const d = malU.clone().sub(mal0).multiplyScalar(m || 1); pos.add(d); look.add(d); break }
      default: break
    }
  }
  if (k.skak) {
    const [a, b, c] = skakv(u, seed)
    const r = right()
    const amp = k.skak * dist * 0.012
    pos.addScaledVector(r, a * amp).add(new THREE.Vector3(0, b * amp, 0))
    look.addScaledVector(r, a * amp * 0.4)
    roll += c * k.skak * 1.4
  }
  roll += k.roll ?? 0
  return { pos, look, fov, roll }
}

export function applyKamera(cam, s) {
  cam.position.copy(s.pos)
  if (s.quat) {
    cam.quaternion.copy(s.quat)
    if (cam.fov !== s.fov) { cam.fov = s.fov; cam.updateProjectionMatrix() }
    return
  }
  cam.up.set(0, 1, 0)
  cam.lookAt(s.look)
  if (s.roll) cam.rotateZ(s.roll * D)
  if (cam.fov !== s.fov) { cam.fov = s.fov; cam.updateProjectionMatrix() }
}
