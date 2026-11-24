import * as THREE from 'three'
import { INDEX } from './skelett'

// Motorns egen syn: det analysens Se-steg skulle ha sett, räknat direkt ur 3D-scenen.
// Samma format som analys/runner.js lämnar ut per ruta, så att samma tolkning (analys/tolka.mjs)
// kan köras på båda. Bryggan jämför den här synen med Se på en rendering av samma manus.
//
// Format per ruta: { t, personer: [{ lm: [[x,y,v]×33], varld: [[x,y,z]×33], bbox }],
//                    hander: [{ lm: [x,y]×21, sida }], saker: [{ k, s, b }], kamera: { dx, dy, rot, skala } }

// MediaPipe Pose, 33 punkter: varifrån i skelettet (led) och med vilken förskjutning i ledens rum (meter, före skala).
const H = 'head'
const PUNKTER = [
  [H, [0, 0.06, 0.12]], // 0 näsa
  [H, [0.02, 0.095, 0.1]], [H, [0.038, 0.095, 0.1]], [H, [0.056, 0.095, 0.094]], // 1–3 vänster öga
  [H, [-0.02, 0.095, 0.1]], [H, [-0.038, 0.095, 0.1]], [H, [-0.056, 0.095, 0.094]], // 4–6 höger öga
  [H, [0.1, 0.075, 0.0]], [H, [-0.1, 0.075, 0.0]], // 7–8 öron
  [H, [0.02, 0.03, 0.098]], [H, [-0.02, 0.03, 0.098]], // 9–10 mun
  ['left_shoulder', [0, 0, 0]], ['right_shoulder', [0, 0, 0]],
  ['left_elbow', [0, 0, 0]], ['right_elbow', [0, 0, 0]],
  ['left_wrist', [0, 0, 0]], ['right_wrist', [0, 0, 0]],
  ['left_wrist', [0.085, 0, -0.03]], ['right_wrist', [-0.085, 0, -0.03]], // 17–18 lillfinger
  ['left_wrist', [0.095, 0, 0.03]], ['right_wrist', [-0.095, 0, 0.03]], // 19–20 pekfinger
  ['left_wrist', [0.045, 0, 0.05]], ['right_wrist', [-0.045, 0, 0.05]], // 21–22 tumme
  ['left_hip', [0, 0, 0]], ['right_hip', [0, 0, 0]],
  ['left_knee', [0, 0, 0]], ['right_knee', [0, 0, 0]],
  ['left_ankle', [0, 0, 0]], ['right_ankle', [0, 0, 0]],
  ['left_ankle', [0, -0.05, -0.05]], ['right_ankle', [0, -0.05, -0.05]], // 29–30 häl
  ['left_ankle', [0, -0.06, 0.17]], ['right_ankle', [0, -0.06, 0.17]], // 31–32 tå
]

// MediaPipe Hand, 21 punkter i handledens rum (vänster hand pekar längs +X).
const FINGRAR = [[0.02, 0.05], [0.045, 0.026], [0.048, 0.006], [0.045, -0.014], [0.04, -0.032]] // [bas x, z] tumme … lillfinger
const HAND = [[0, 0, 0], ...FINGRAR.flatMap(([x, z], f) => [1, 2, 3, 4].map(k => [x + k * (f === 0 ? 0.018 : 0.022), 0, z * (f === 0 ? 1 + k * 0.15 : 1)]))]

const v3 = new THREE.Vector3()
const ndc = (p, cam) => v3.copy(p).project(cam)
const inne = n => n.z > -1 && n.z < 1

function iVarlden(docka, led, off) {
  const b = docka.bones[INDEX[led]]
  return new THREE.Vector3(...off).multiplyScalar(docka.skala).applyMatrix4(b.matrixWorld)
}

// 2D-likformighet (skala, rotation, förflyttning) med minsta kvadrat, som OpenCV:s affina anpassning
// gör på bakgrundspunkter. Returnerar samma tal som runner.js tolkaAffin: bildmittens förflyttning.
export function likformighet(fran, till, W, H) {
  const n = fran.length
  if (n < 6) return null
  let mx = 0, my = 0, nx = 0, ny = 0
  for (let i = 0; i < n; i++) { mx += fran[i][0]; my += fran[i][1]; nx += till[i][0]; ny += till[i][1] }
  mx /= n; my /= n; nx /= n; ny /= n
  let a = 0, b = 0, d = 0
  for (let i = 0; i < n; i++) {
    const xs = fran[i][0] - mx, ys = fran[i][1] - my, xd = till[i][0] - nx, yd = till[i][1] - ny
    a += xs * xd + ys * yd
    b += xs * yd - ys * xd
    d += xs * xs + ys * ys
  }
  if (d < 1e-9) return null
  const sc = a / d, ss = b / d
  const s = Math.hypot(sc, ss)
  const cx = W / 2, cy = H / 2
  const px = nx + sc * (cx - mx) - ss * (cy - my)
  const py = ny + ss * (cx - mx) + sc * (cy - my)
  const r3 = v => Math.round(v * 1000) / 1000
  return { dx: r3((px - cx) / W), dy: r3((py - cy) / H), rot: r3((Math.atan2(ss, sc) * 180) / Math.PI), skala: r3(s), inl: 1, n }
}

// Statiska punkter i lokalen för kamerans rörelse (väggar, golv, disk), plockade en gång.
export function bakgrundspunkter(lokal) {
  const pts = []
  lokal.updateMatrixWorld(true)
  lokal.traverse(o => {
    if (!o.isMesh || o.userData.kontur) return
    const pos = o.geometry.attributes.position
    const steg = Math.max(1, Math.floor(pos.count / 40))
    for (let i = 0; i < pos.count; i += steg) pts.push(new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld))
  })
  // Plana ytor har få hörn: täta rutnät på allt som har textur (golv, väggar, disk, ugn), så att
  // även närbilder har tillräckligt många bakgrundspunkter. Med glesa punkter föll motorns egen
  // kamera under tillförlitlighetsgränsen (30 punkter) i närbilder, som analysens gör på slät yta.
  const steg = 0.12
  for (let x = -2.6; x <= 4; x += steg) for (let z = -2.55; z <= 3; z += steg) pts.push(new THREE.Vector3(x, 0, z)) // golv
  for (let x = -2.6; x <= 4; x += steg) for (let y = 0.05; y <= 3.3; y += steg) pts.push(new THREE.Vector3(x, y, -2.6)) // bakvägg
  for (let z = -2.55; z <= 3; z += steg) for (let y = 0.05; y <= 3.3; y += steg) pts.push(new THREE.Vector3(-2.64, y, z)) // sidovägg
  for (let x = 0.1; x <= 2.0; x += steg / 2) for (let y = 0.02; y <= 0.92; y += steg / 2) pts.push(new THREE.Vector3(x, y, -1.14)) // diskens front
  for (let x = 0.06; x <= 2.04; x += steg / 2) for (let z = -1.79; z <= -1.11; z += steg / 2) pts.push(new THREE.Vector3(x, 0.97, z)) // diskskivan
  for (let x = 2.0; x <= 3.1; x += steg / 2) for (let y = 0.02; y <= 0.78; y += steg / 2) pts.push(new THREE.Vector3(x, y, -1.64)) // ugnens front
  return pts
}

// Saker som COCO-detektorn känner igen: userData.coco på lokalens och dockornas föremål.
function saker(scene, cam, dockor) {
  const ut = []
  const box = new THREE.Box3()
  const hornen = b => [0, 1].flatMap(i => [0, 1].flatMap(j => [0, 1].map(k => new THREE.Vector3(i ? b.max.x : b.min.x, j ? b.max.y : b.min.y, k ? b.max.z : b.min.z))))
  const ruta = punkter => {
    const n = punkter.map(p => ndc(p, cam).clone())
    if (n.some(p => !inne(p))) return null
    const xs = n.map(p => (p.x + 1) / 2)
    const ys = n.map(p => (1 - p.y) / 2)
    const b = [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]
    const k = [Math.max(0, b[0]), Math.max(0, b[1]), Math.min(1, b[2]), Math.min(1, b[3])]
    return (k[2] - k[0]) * (k[3] - k[1]) >= 0.003 ? k : null
  }
  scene.traverse(o => {
    if (!o.userData.coco) return
    let synlig = true
    o.traverseAncestors(p => { if (p.visible === false) synlig = false })
    if (!synlig || !o.visible) return
    box.setFromObject(o)
    const b = ruta(hornen(box))
    if (b) ut.push({ k: o.userData.coco, s: 0.8, b: b.map(v => Math.round(v * 1000) / 1000) })
  })
  return ut
}

// Alternativ för snabb mätning av många uttryck:
//   bakgrund  färdiga bakgrundspunkter (räknas annars ut här, dyrt)
//   gles      använd var n:e bakgrundspunkt (kamerans skattning blir densamma, snabbare)
//   enkel     hoppa över saker (COCO) och händer, som inte behövs för kamerans egenskaper
export function skapaSyn(sp, { bakgrund: fardig, gles = 1, enkel = false } = {}) {
  const W = 360
  const Hpx = Math.round(W * 16 / 9)
  const bakgrund = (fardig ?? bakgrundspunkter(sp.lokal)).filter((_, k) => k % gles === 0)
  // Skymmande föremål (disk, ugn) som lådor; en led är skymd om strålen från kameran träffar en låda
  // före leden. Utan det såg motorn fötterna genom disken och kallade halvtotal för total.
  const lador = []
  sp.lokal.updateMatrixWorld(true)
  sp.lokal.traverse(o => { if (o.userData.skymmer) lador.push(new THREE.Box3().setFromObject(o)) })
  const ray = new THREE.Ray()
  const traff = new THREE.Vector3()
  const skymd = (fran, p) => {
    const avst = fran.distanceTo(p)
    ray.origin.copy(fran)
    ray.direction.copy(p).sub(fran).normalize()
    return lador.some(b => !b.containsPoint(p) && ray.intersectBox(b, traff) && fran.distanceTo(traff) < avst - 0.02)
  }
  let forra = null
  return function syn(t) {
    const w = sp.where(t)
    const i = w.b !== null && w.f >= 0.5 ? w.b : w.a
    sp.stage(i, Math.max(0, Math.min(sp.manus.scener[i].tid, t - sp.tl[i].start)))
    const cam = sp.cam
    cam.updateMatrixWorld(true)
    cam.updateProjectionMatrix()
    const camInv = cam.matrixWorldInverse
    const personer = []
    const hander = []
    const ansikten = []
    for (const [roll, d] of Object.entries(sp.dockor)) {
      if (!d.root.visible) continue
      d.root.updateMatrixWorld(true)
      const varld = PUNKTER.map(([led, off]) => iVarlden(d, led, off))
      // synlighet som MediaPipe: utanför bild eller bakom kameran 0, skymd (bakom disk eller ugn) 0,2
      const lm = varld.map(p => { const n = ndc(p, cam); return [(n.x + 1) / 2, (1 - n.y) / 2, !inne(n) ? 0 : skymd(cam.position, p) ? 0.2 : 1] })
      const syns = lm.filter(p => p[2] > 0.3 && p[0] > -0.2 && p[0] < 1.2 && p[1] > -0.2 && p[1] < 1.2)
      if (syns.filter(p => p[0] >= 0 && p[0] <= 1 && p[1] >= 0 && p[1] <= 1).length < 4) continue
      const xs = syns.map(p => p[0])
      const ys = syns.map(p => p[1])
      const r3 = v => Math.round(v * 1000) / 1000
      // 3D i kamerans riktning med höften som origo: x höger, y ned, z bort från kameran (som MediaPipe)
      const kam = varld.map(p => p.clone().applyMatrix4(camInv))
      const hm = kam[23].clone().add(kam[24]).multiplyScalar(0.5)
      personer.push({
        lm: lm.map(p => p.map(r3)),
        varld: kam.map(p => [r3(p.x - hm.x), r3(-(p.y - hm.y)), r3(-(p.z - hm.z))]),
        bbox: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)].map(r3),
        roll,
      })
      // ansikte: rutan från panna till haka, bara när ansiktet är vänt mot kameran (som BlazeFace)
      const huvud = d.bones[INDEX.head]
      const hp = new THREE.Vector3().setFromMatrixPosition(huvud.matrixWorld)
      const fram = new THREE.Vector3(0, 0, 1).transformDirection(huvud.matrixWorld)
      const motKamera = cam.position.clone().sub(hp).normalize()
      if (fram.dot(motKamera) > 0.2) {
        const horn = [[-0.08, -0.02], [0.08, -0.02], [-0.08, 0.17], [0.08, 0.17]].map(([x, y]) => { const q = ndc(iVarlden(d, 'head', [x, y, 0.1]), cam); return [(q.x + 1) / 2, (1 - q.y) / 2, inne(q)] })
        if (horn.every(p => p[2])) {
          const xs = horn.map(p => p[0]); const ys = horn.map(p => p[1])
          const b = [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]
          const k = [Math.max(0, b[0]), Math.max(0, b[1]), Math.min(1, b[2]), Math.min(1, b[3])]
          if (k[2] - k[0] > 0.02 && k[3] - k[1] > 0.02 && (k[2] - k[0]) * (k[3] - k[1]) >= 0.5 * (b[2] - b[0]) * (b[3] - b[1])) ansikten.push({ s: 0.9, b: k.map(r3) })
        }
      }
      // händer: bara när handen syns och är stor nog för handdetektorn
      for (const [sida, led, sx] of enkel ? [] : [['Left', 'left_wrist', 1], ['Right', 'right_wrist', -1]]) {
        const pts = HAND.map(([x, y, z]) => iVarlden(d, led, [sx * x, y, z]))
        const n = pts.map(p => { const q = ndc(p, cam); return [(q.x + 1) / 2, (1 - q.y) / 2, inne(q)] })
        if (!n.every(p => p[2] && p[0] >= 0 && p[0] <= 1 && p[1] >= 0 && p[1] <= 1)) continue
        const storlek = Math.hypot(n[12][0] - n[0][0], (n[12][1] - n[0][1]) * Hpx / W)
        if (storlek < HAND_MIN) continue
        hander.push({ lm: n.flatMap(p => [r3(p[0]), r3(p[1])]), sida, s: 0.9 })
      }
    }
    // personer som COCO-detektorn skulle se
    const sak = enkel ? [] : saker(sp.scene, cam, sp.dockor)
    for (const p of personer) sak.push({ k: 'person', s: 0.9, b: [Math.max(0, p.bbox[0]), Math.max(0, p.bbox[1]), Math.min(1, p.bbox[2]), Math.min(1, p.bbox[3])] })
    // kamerans rörelse sedan förra rutan, på bakgrundspunkter som syns i båda
    const nu = bakgrund.map(p => { const n = ndc(p, cam); return inne(n) ? [((n.x + 1) / 2) * W, ((1 - n.y) / 2) * Hpx] : null })
    let kamera = null
    if (forra) {
      const a = []
      const b = []
      nu.forEach((p, k) => { const q = forra[k]; if (p && q && p[0] >= 0 && p[0] <= W && p[1] >= 0 && p[1] <= Hpx && q[0] >= 0 && q[0] <= W && q[1] >= 0 && q[1] <= Hpx) { a.push(q); b.push(p) } })
      kamera = likformighet(a, b, W, Hpx)
    }
    forra = nu
    return { t: Math.round(t * 1000) / 1000, personer, hander, saker: sak, ansikten, kamera, scen: i }
  }
}

// Minsta handstorlek (handled till långfingertopp, andel av bildbredden) för att handdetektorn ska se handen.
// Startvärde; bryggan kalibrerar det mot vad MediaPipe faktiskt hittar i renderingarna.
export let HAND_MIN = 0.05
export const sattHandMin = v => { HAND_MIN = v }
