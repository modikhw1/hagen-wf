// Geometri: från bildkoordinater till meter i scenens värld.
//
// Kameran: en mobil i stående format, huvudkameran (26 mm motsvarande) ger ungefär 68° på höjden.
// Varje scen får en egen scen-värld (scenen ställs upp för sig, se manus.mjs): kameran står i x = 0,
// z = 0 och tittar mot −z vid scenens början. Höjd och lutning skattas ur personerna (axlarna sitter
// på ungefär 1,42 m hos en stående vuxen, anklarna på 0,08 m), med svaga antaganden när underlaget
// är tunt. Kamerans rörelse under scenen tas ur analysens bakgrundsföljning per ruta.
//
// Djup: MediaPipes 3D-punkter är i meter (en standardkropp). Längden mellan två punkter i 3D,
// projicerad på bildplanet, delat med längden i bilden ger avståndet: d = f · L3D / L2D.
import * as THREE from 'three'

export const FOV_V = 68
export const ASPEKT = 9 / 16 // bredd / höjd
export const F = 0.5 / Math.tan((FOV_V / 2) * Math.PI / 180) // brännvidd i bildhöjder
export const FOV_H = 2 * Math.atan(Math.tan((FOV_V / 2) * Math.PI / 180) * ASPEKT) * 180 / Math.PI
export const AXEL_HOJD = 1.42
export const ANKEL_HOJD = 0.08

const PAR = [[11, 12], [11, 23], [12, 24], [23, 24], [11, 13], [12, 14], [13, 15], [14, 16], [7, 8], [0, 11], [0, 12], [23, 25], [24, 26], [25, 27], [26, 28]]
const median = a => { const s = a.slice().sort((x, y) => x - y); return s.length ? s[s.length >> 1] : null }

// Avstånd till en person (meter längs kamerans axel) ur en pose, eller null.
export function djup(lm, varld, min = 0.6) {
  if (!lm || !varld) return null
  const d = []
  for (const [i, j] of PAR) {
    if (lm[i][2] < min || lm[j][2] < min) continue
    const l2 = Math.hypot((lm[i][0] - lm[j][0]) * ASPEKT, lm[i][1] - lm[j][1])
    if (l2 < 0.025) continue
    const l3 = Math.hypot(varld[i][0] - varld[j][0], varld[i][1] - varld[j][1])
    if (l3 < 0.05) continue
    d.push((F * l3) / l2)
  }
  return d.length >= 2 ? median(d) : null
}
// Avstånd ur rutans höjd, när posen saknas: en synlig överkropp ~0,9 m, hel kropp ~1,75 m.
export function djupUrRuta(b) {
  const h = b[3] - b[1]
  const hel = b[3] < 0.97 && b[1] > 0.03
  return (F * (hel ? 1.7 : 0.9)) / Math.max(0.05, h)
}

// Bildpunkt (u, v) och avstånd d → punkt i kamerans eget rum (x höger, y upp, kameran tittar mot −z).
export const iKamera = (u, v, d) => new THREE.Vector3(((u - 0.5) * d) / (F / ASPEKT) * 1, (-(v - 0.5) * d) / F, -d)

// Kamerans orientering ur gir (yaw), lutning (pitch, upp positiv) och roll, i grader.
export function kamQuat(yaw, pitch, roll) {
  return new THREE.Quaternion().setFromEuler(new THREE.Euler(pitch * Math.PI / 180, yaw * Math.PI / 180, roll * Math.PI / 180, 'YXZ'))
}

// Höjd och lutning för en scen ur observationer { p: punkt i kamerarummet, y: förväntad höjd, w }.
// Rutnätssökning med svaga antaganden (höjd 1,45 ± 0,3 m, lutning 0 ± 14°): stabilt även med en
// enda person, där höjd och lutning annars inte går att skilja åt.
export function hojdOchLutning(obs) {
  let bast = { h: 1.45, pitch: 0, c: Infinity }
  for (let h = 0.5; h <= 2.3; h += 0.02) for (let p = -40; p <= 40; p += 0.5) {
    const s = Math.sin(p * Math.PI / 180), c = Math.cos(p * Math.PI / 180)
    let k = ((h - 1.45) / 0.3) ** 2 + (p / 14) ** 2
    for (const o of obs) {
      const y = h + o.p.y * c - o.p.z * s
      k += o.w * ((y - o.y) / (o.sigma ?? 0.12)) ** 2
    }
    if (k < bast.c) bast = { h, pitch: p, c: k }
  }
  return bast
}

// Kamerabanan i en scen: start (höjd, lutning) plus analysens rörelse per ruta, summerad.
// ramar: analysens sett.ramar för scenens rutor ({ kamera: { dx, dy, rot, skala, inl, n } }).
// dRef: typiskt avstånd till motivet (för att göra skalbyten till förflyttning framåt).
export function kameraBana(ramar, { h, pitch }, dRef, { minInl = 0.4, minN = 30 } = {}) {
  let yaw = 0, pt = pitch, roll = 0, fram = 0
  const ut = []
  for (const [k, r] of ramar.entries()) {
    const m = r?.kamera
    if (k > 0 && m && (m.inl ?? 0) >= minInl && (m.n ?? 0) >= minN) {
      // bildens innehåll flyttas åt höger när kameran vrids åt vänster
      yaw += Math.max(-6, Math.min(6, (m.dx ?? 0) * FOV_H))
      pt += Math.max(-6, Math.min(6, (m.dy ?? 0) * FOV_V))
      roll -= Math.max(-3, Math.min(3, m.rot ?? 0))
      const s = m.skala ?? 1
      if (Math.abs(s - 1) > 0.002) fram += Math.max(-0.15, Math.min(0.15, dRef * (1 - 1 / s)))
    }
    const q = kamQuat(yaw, pt, roll)
    const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(kamQuat(yaw, 0, 0))
    const pos = new THREE.Vector3(0, h, 0).addScaledVector(fwd, fram)
    ut.push({ pos, q, yaw, pitch: pt, roll })
  }
  return ut
}

export { median }
