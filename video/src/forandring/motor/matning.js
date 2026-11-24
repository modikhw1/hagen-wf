import * as THREE from 'three'
import { kameraOk } from './lokal'
import { ORIGINAL_STEG } from '../manus/regissor'

// Mätmotorn (första versionen): hur mycket rör sig bilden, mätt på det tittaren ser.
// Lederna projiceras genom kameran vid u och u+du. Förflyttningen i bild delas i
//  - kamera: samma leder, bara kameran har rört sig
//  - motiv: resten, alltså det personerna gör (förstärkt av utsnittet: liten gest i närbild blir stor)
// Ger en kurva per scen och ett värde. Samma kod kan köras på originalets rekonstruktion och på varianter.

const N = 14
const DU = 1 / 15

function project(points, cam) {
  return points.map(p => p.clone().project(cam))
}
// Bara leder som syns i bild (framför kameran, inom ramen) räknas, och varje leds förflyttning
// får ett tak. Annars ger leder precis vid kameran (närbilder) orimliga tal.
const syns = p => p.z > -1 && p.z < 1 && Math.abs(p.x) < 1.2 && Math.abs(p.y) < 1.2
const TAK = 0.25
// En bild är giltig när kameran står i rummet (inte i en vägg eller i disken) och minst tre leder syns.
// Kameran får inte heller stå inne i en person (närmare än 22 cm en led).
const giltigBild = (pts, camPos, lokal, world) =>
  kameraOk(lokal, camPos) && pts.filter(syns).length >= 3 && world.every(w => w.distanceTo(camPos) > 0.22)
const disp = (a, b) => {
  let s = 0, n = 0
  a.forEach((p, i) => { if (syns(p) && syns(b[i])) { s += Math.min(TAK, Math.hypot(p.x - b[i].x, p.y - b[i].y)); n++ } })
  return n ? s / n : 0
}

// I en närbild på en person ska ansiktet vara vänt mot kameran, annars är det en bild av ett bakhuvud.
const _h = new THREE.Vector3()
const _d = new THREE.Vector3()
function ansiktetSyns(sp, sc, camPos) {
  const k = sc.kamera
  if (!['nara', 'extrem'].includes(k.utsnitt) || !k.mal.roll) return true
  const head = sp.dockor[k.mal.roll].bones[15]
  head.getWorldPosition(_h)
  head.getWorldDirection(_d)
  return _d.dot(camPos.clone().sub(_h).normalize()) > 0.15
}

export function matScen(sp, manus, i) {
  const keep = sp.manus
  sp.manus = manus
  const sc = manus.scener[i]
  const kurva = []
  for (let n = 0; n < N; n++) {
    const u = (n / (N - 1)) * Math.max(0, sc.tid - DU)
    const a = sp.stage(i, u)
    sp.cam.updateMatrixWorld()
    const ptsA = Object.values(a.joints).flat()
    const camA = sp.cam.clone()
    const fovA = sp.cam.fov
    const b = sp.stage(i, u + DU)
    sp.cam.updateMatrixWorld()
    const ptsB = Object.values(b.joints).flat()
    const pa = project(ptsA, camA)
    const pbCam = project(ptsA, sp.cam) // samma leder, ny kamera
    const pb = project(ptsB, sp.cam)
    const kamera = disp(pa, pbCam) / DU + Math.abs(sp.cam.fov - fovA) / DU / 30
    const total = disp(pa, pb) / DU
    const motiv = Math.max(0, total - kamera) + disp(pbCam, pb) / DU * 0.5
    kurva.push({ u, kamera, motiv, syns: giltigBild(pa, camA.position, manus.lokal, ptsA) && ansiktetSyns(sp, sc, camA.position) ? 1 : 0 })
  }
  sp.manus = keep
  const medel = k => kurva.reduce((s, x) => s + x[k], 0) / kurva.length
  return { kurva, kamera: medel('kamera'), motiv: medel('motiv'), syns: medel('syns'), raw: medel('kamera') + medel('motiv') + overgangVikt(sc) }
}

// Övergången in i scenen räknas också som scenografi.
const overgangVikt = sc => ({ klipp: 0, mjuk: 0.05, whip: 0.35, zoom: 0.3 }[sc.in?.typ ?? 'klipp'])

// Mät alla verkligheter. Skalan kalibreras per scen i tre punkter: lugnaste versionen 1, originalet 5,
// mest rörliga 10 (roten ur, så att enstaka extremer inte trycker ihop resten). Det mätta värdet är
// alltså var versionen ligger bland scenens egna möjligheter. Att verklighet 9 kan mäta lägre än 6
// i en scen är data: det är det väljaren använder, inte regissörens avsikt.
export function matAlla(sp, verkligheter) {
  const raw = {}
  for (const [k, m] of Object.entries(verkligheter)) raw[k] = m.scener.map((_, i) => matScen(sp, m, i))
  const steg = Object.keys(raw)
  const n = raw[steg[0]].length
  const varde = Object.fromEntries(steg.map(k => [k, []]))
  for (let i = 0; i < n; i++) {
    const r = steg.map(k => Math.sqrt(raw[k][i].raw))
    // ändarna sätts bara av versioner där motivet syns
    const ok = steg.map(k => k === String(ORIGINAL_STEG) || raw[k][i].syns >= 0.7)
    const lo = Math.min(...r.filter((_, j) => ok[j]))
    const hi = Math.max(...r.filter((_, j) => ok[j]))
    const o = r[steg.indexOf(String(ORIGINAL_STEG))] // originalet är ground truth: det definierar 5
    const skala = x => x <= o
      ? 1 + (4 * (x - lo)) / Math.max(1e-6, o - lo)
      : 5 + (5 * (x - o)) / Math.max(1e-6, hi - o)
    steg.forEach((k, j) => { varde[k][i] = { ...raw[k][i], v: Math.max(0.5, Math.min(10.5, skala(r[j]))) } })
  }
  return varde
}
