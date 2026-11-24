import * as THREE from 'three'
import { JOINTS, INDEX } from './skelett.js'

// En pose kan skrivas på två sätt:
// 1. Semantiskt: ett fåtal vinklar i grader (arm ut, armbåge böjd, nick …). Lätt för en AI att skriva och rätta.
// 2. Leder: en kvaternion per led, som rå data från GVHMR eller en text-till-rörelse-modell.
// Båda blir till slut 22 kvaternioner, och allt efter det (docka, mätning) ser bara kvaternionerna.

export const NEUTRAL = {
  hips: [0, 0, 0], // framåt, sida, vrid
  spine: [2, 0, 0],
  neck: [0, 0, 0], // nick, sida, vrid
  lArm: [10, 0, 0], rArm: [10, 0, 0], // ut från kroppen (0 = längs sidan, 90 = T, 180 = upp), framåt, vrid
  lElbow: 12, rElbow: 12,
  lWrist: [0, 0], rWrist: [0, 0],
  lLeg: [0, 3], rLeg: [0, 3], // framåt, ut
  lKnee: 2, rKnee: 2,
  lAnkle: 0, rAnkle: 0,
  lift: 0, // höjd på bäckenet i meter (gungning, sättning)
}

// Platta till och tillbaka, så att alla vinklar kan interpoleras och skalas som en vektor.
const KEYS = []
for (const [k, v] of Object.entries(NEUTRAL)) {
  if (Array.isArray(v)) v.forEach((_, i) => KEYS.push([k, i]))
  else KEYS.push([k, -1])
}
export const flat = p => KEYS.map(([k, i]) => {
  const v = p[k] ?? NEUTRAL[k]
  return i < 0 ? v : (v[i] ?? NEUTRAL[k][i])
})
export const unflat = a => {
  const p = {}
  KEYS.forEach(([k, i], n) => {
    if (i < 0) p[k] = a[n]
    else (p[k] ||= [])[i] = a[n]
  })
  return p
}
const NEUTRAL_FLAT = flat(NEUTRAL)

const D = THREE.MathUtils.DEG2RAD
const _e = new THREE.Euler()
const qx = a => new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), a * D)
const qy = a => new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), a * D)
const qz = a => new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), a * D)
const mul = (...qs) => qs.reduce((a, b) => a.multiply(b), new THREE.Quaternion())
const eul = (x, y, z) => new THREE.Quaternion().setFromEuler(_e.set(x * D, y * D, z * D, 'YXZ'))

// Semantisk pose till 22 kvaternioner (lokala, relativt T-pose).
export function toQuats(p) {
  const q = JOINTS.map(() => new THREE.Quaternion())
  const set = (j, v) => q[INDEX[j]].copy(v)
  const [hf, hs, ht] = p.hips
  set('pelvis', eul(hf, ht, hs))
  const [sf, ss, st] = p.spine
  for (const j of ['spine1', 'spine2', 'spine3']) set(j, eul(sf / 3, st / 3, ss / 3))
  const [nn, ns, nt] = p.neck
  set('neck', eul(nn * 0.4, nt * 0.4, ns * 0.4))
  set('head', eul(nn * 0.6, nt * 0.6, ns * 0.6))
  const arm = (side, [abd, flex, tw], elbow, [wf, wd]) => {
    const s = side === 'left' ? 1 : -1
    set(`${side}_shoulder`, mul(qx(-flex), qz(-s * (90 - abd)), qx(tw))) // vridning kring armens axel: samma tecken på båda sidor (spegling)
    set(`${side}_elbow`, qy(-s * elbow))
    set(`${side}_wrist`, mul(qz(-s * wf), qy(-s * wd)))
  }
  arm('left', p.lArm, p.lElbow, p.lWrist)
  arm('right', p.rArm, p.rElbow, p.rWrist)
  const leg = (side, [flex, abd], knee, ankle) => {
    const s = side === 'left' ? 1 : -1
    set(`${side}_hip`, mul(qx(-flex), qz(s * abd)))
    set(`${side}_knee`, qx(knee))
    set(`${side}_ankle`, qx(-ankle))
  }
  leg('left', p.lLeg, p.lKnee, p.lAnkle)
  leg('right', p.rLeg, p.rKnee, p.rAnkle)
  return q
}

const smooth = x => x * x * (3 - 2 * x)

// Ett semantiskt rörelseklipp: nyckelposer över tid, mjuk interpolation mellan dem.
// amp skalar avvikelsen från neutral hållning: 0 = står still, 1 = som skrivet, >1 = överspelat.
export function sampleSemantic(clip, t, amp = 1) {
  const keys = clip.nycklar
  const L = clip.langd
  let u = clip.loop ? ((t % L) + L) % L : Math.max(0, Math.min(L, t))
  let i = keys.findIndex(k => k.t > u)
  let a, b, f
  if (i === -1) {
    if (clip.loop) { a = keys[keys.length - 1]; b = { ...keys[0], t: L }; f = (u - a.t) / Math.max(1e-6, b.t - a.t) }
    else { a = b = keys[keys.length - 1]; f = 0 }
  } else if (i === 0) { a = b = keys[0]; f = 0 } else { a = keys[i - 1]; b = keys[i]; f = (u - a.t) / (b.t - a.t) }
  const A = flat({ ...NEUTRAL, ...a.p })
  const B = flat({ ...NEUTRAL, ...b.p })
  const s = smooth(f)
  const v = A.map((x, n) => {
    const raw = x + (B[n] - x) * s
    return NEUTRAL_FLAT[n] + (raw - NEUTRAL_FLAT[n]) * amp
  })
  return unflat(v)
}

// Ett ledklipp (rådata): kvaternioner per bildruta. amp blandar mot neutral hållning.
const NEUTRAL_Q = toQuats(NEUTRAL)
// Medelpose per led (kvaternioner, tecken i linje med den första), för rekonstruerade rörelser.
function medelpose(clip) {
  if (clip._medel) return clip._medel
  const n = clip.ramar.length
  clip._medel = clip.ramar[0].map((q0, k) => {
    const s = [0, 0, 0, 0]
    for (let i = 0; i < n; i++) {
      const q = clip.ramar[i][k]
      const tecken = q[0] * q0[0] + q[1] * q0[1] + q[2] * q0[2] + q[3] * q0[3] < 0 ? -1 : 1
      for (let j = 0; j < 4; j++) s[j] += tecken * q[j]
    }
    return new THREE.Quaternion(...s).normalize()
  })
  return clip._medel
}

// amp för en rekonstruerad rörelse (liv: false) skalar avvikelsen från personens egen medelpose:
// 0,6 = samma rörelse men lugnare, 1,4 = samma rörelse men större. Tiden ändras inte. För ordbokens
// handgjorda rörelser skalar amp som förut avvikelsen från neutral hållning.
export function sampleJoints(clip, t, amp = 1) {
  const n = clip.ramar.length
  const x = clip.loop ? (((t * clip.fps) % n) + n) % n : Math.max(0, Math.min(n - 1, t * clip.fps))
  const i = Math.floor(x)
  const j = clip.loop ? (i + 1) % n : Math.min(n - 1, i + 1)
  const f = x - i
  return clip.ramar[i].map((qa, k) => {
    const q = new THREE.Quaternion(...qa).slerp(new THREE.Quaternion(...clip.ramar[j][k]), f)
    if (amp === 1) return q
    const bas = clip.liv === false ? medelpose(clip)[k] : NEUTRAL_Q[k]
    return slerpUtan(bas, q, amp)
  })
}

// slerp som också går bortom 1 (förstärkning) och under 0 utan att klampas
function slerpUtan(a, b, t) {
  let d = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w
  const bb = d < 0 ? new THREE.Quaternion(-b.x, -b.y, -b.z, -b.w) : b
  d = Math.abs(d)
  if (d > 0.9995) return new THREE.Quaternion(a.x + (bb.x - a.x) * t, a.y + (bb.y - a.y) * t, a.z + (bb.z - a.z) * t, a.w + (bb.w - a.w) * t).normalize()
  const th = Math.acos(Math.min(1, d)), s = Math.sin(th)
  const wa = Math.sin((1 - t) * th) / s, wb = Math.sin(t * th) / s
  return new THREE.Quaternion(a.x * wa + bb.x * wb, a.y * wa + bb.y * wb, a.z * wa + bb.z * wb, a.w * wa + bb.w * wb).normalize()
}
