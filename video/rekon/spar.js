// Personspår för rekonstruktionen (webbläsardelen, körs av rekon/kor.mjs i Edge).
//
// Analysens Pose körs på hela rutan och slår ihop personer som står nära varandra (två bakom en disk
// blir en kropp). Här körs den uppifrån och ner: först hittas personerna (COCO-person och ansikten),
// sedan körs Pose på en utskuren bild per person. Varje person får 33 punkter i bilden, 33 i 3D
// (meter, med höften som origo) och färger provtagna ur bilden (överdel, underdel, hud, hår), så att
// dockan kan klä sig som personen. Följningen över tid görs i Node (rekon/spar.mjs).
import { FilesetResolver, PoseLandmarker, ObjectDetector, FaceDetector } from '@mediapipe/tasks-vision'

const status = t => { document.getElementById('status').textContent = t }
const r3 = v => Math.round(v * 1000) / 1000

let pose, objekt, ansikte, delegat

async function init() {
  const fileset = await FilesetResolver.forVisionTasks('/node_modules/@mediapipe/tasks-vision/wasm')
  for (const d of ['GPU', 'CPU']) {
    try {
      pose = await PoseLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: '/modeller/pose_landmarker_full.task', delegate: d },
        runningMode: 'IMAGE', numPoses: 1,
        minPoseDetectionConfidence: 0.4, minPosePresenceConfidence: 0.4,
      })
      objekt = await ObjectDetector.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: '/modeller/efficientdet_lite2.tflite', delegate: d },
        runningMode: 'IMAGE', maxResults: 15, scoreThreshold: 0.25,
      })
      ansikte = await FaceDetector.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: '/modeller/blaze_face_full_range.tflite', delegate: d },
        runningMode: 'IMAGE', minDetectionConfidence: 0.5,
      })
      delegat = d
      break
    } catch (e) { console.warn('delegat', d, e) }
  }
  status(`redo · ${delegat}`)
  return { delegat }
}
const redo = init()

async function bild(url) {
  for (let f = 0; f < 4; f++) {
    try {
      const r = await fetch(url, { cache: 'no-store' })
      if (!r.ok) throw new Error('http ' + r.status)
      return await createImageBitmap(await r.blob())
    } catch (e) {
      if (f === 3) return null
      await new Promise(res => setTimeout(res, 150 * (f + 1)))
    }
  }
}

const iou = (a, b) => {
  const x0 = Math.max(a[0], b[0]), y0 = Math.max(a[1], b[1]), x1 = Math.min(a[2], b[2]), y1 = Math.min(a[3], b[3])
  const i = Math.max(0, x1 - x0) * Math.max(0, y1 - y0)
  const u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
  return u > 0 ? i / u : 0
}

// Median av färgen i en uppsättning punkter (bildkoordinater 0–1), som hex.
function farg(px, W, H, punkter) {
  const r = [], g = [], b = []
  for (const [x, y] of punkter) {
    const X = Math.round(x * W), Y = Math.round(y * H)
    if (X < 0 || Y < 0 || X >= W || Y >= H) continue
    const k = (Y * W + X) * 4
    r.push(px[k]); g.push(px[k + 1]); b.push(px[k + 2])
  }
  if (r.length < 6) return null
  const med = a => a.sort((p, q) => p - q)[a.length >> 1]
  return '#' + [med(r), med(g), med(b)].map(v => v.toString(16).padStart(2, '0')).join('')
}
// Punkter i en fyrhörning (a, b, c, d i ordning), krympt mot mitten.
function iFyrhorning([a, b, c, d], krymp = 0.25, n = 7) {
  const ut = []
  const mx = (a[0] + b[0] + c[0] + d[0]) / 4, my = (a[1] + b[1] + c[1] + d[1]) / 4
  const k = p => [mx + (p[0] - mx) * (1 - krymp), my + (p[1] - my) * (1 - krymp)]
  const [A, B, C, D] = [a, b, c, d].map(k)
  for (let i = 0; i <= n; i++) for (let j = 0; j <= n; j++) {
    const u = i / n, v = j / n
    const top = [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u]
    const bot = [D[0] + (C[0] - D[0]) * u, D[1] + (C[1] - D[1]) * u]
    ut.push([top[0] + (bot[0] - top[0]) * v, top[1] + (bot[1] - top[1]) * v])
  }
  return ut
}
const synlig = (lm, i, min = 0.5) => lm[i] && lm[i][2] >= min

// Färger för en person ur dess punkter.
function personFarger(px, W, H, lm, ruta) {
  const P = i => [lm[i][0], lm[i][1]]
  const f = {}
  if (synlig(lm, 11) && synlig(lm, 12) && synlig(lm, 23, 0.3) && synlig(lm, 24, 0.3)) f.overdel = farg(px, W, H, iFyrhorning([P(12), P(11), P(23), P(24)], 0.35))
  else if (synlig(lm, 11) && synlig(lm, 12)) {
    // bara axlarna: ta bröstet strax under
    const d = Math.hypot(lm[11][0] - lm[12][0], lm[11][1] - lm[12][1])
    const a = P(12), b = P(11)
    f.overdel = farg(px, W, H, iFyrhorning([a, b, [b[0], b[1] + d * 0.8], [a[0], a[1] + d * 0.8]], 0.3))
  }
  if (synlig(lm, 23) && synlig(lm, 24) && synlig(lm, 25) && synlig(lm, 26)) f.underdel = farg(px, W, H, iFyrhorning([P(24), P(23), P(25), P(26)], 0.4))
  if (synlig(lm, 0) && synlig(lm, 2) && synlig(lm, 5)) {
    // hud: kinderna under ögonen
    const e = Math.hypot(lm[2][0] - lm[5][0], lm[2][1] - lm[5][1])
    const pts = []
    for (const s of [2, 5]) for (let k = 0; k < 9; k++) pts.push([lm[s][0] + ((k % 3) - 1) * e * 0.12, lm[s][1] + e * (0.35 + Math.floor(k / 3) * 0.1)])
    f.hud = farg(px, W, H, pts)
    // hår: ovanför pannan
    const hp = []
    for (let k = 0; k < 15; k++) hp.push([lm[0][0] + ((k % 5) - 2) * e * 0.25, lm[0][1] - e * (1.25 + Math.floor(k / 5) * 0.12)])
    f.har = farg(px, W, H, hp)
  }
  return f
}

// En ruta: personer med pose i 2D och 3D, och färger. Rutor (bbox) i bildkoordinater 0–1.
async function personer(bmp) {
  const W = bmp.width, H = bmp.height
  const c = new OffscreenCanvas(W, H)
  const g = c.getContext('2d', { willReadFrequently: true })
  g.drawImage(bmp, 0, 0)
  const px = g.getImageData(0, 0, W, H).data
  const det = objekt.detect(c)
  const saker = det.detections.map(d => ({ k: d.categories[0].categoryName, s: r3(d.categories[0].score), b: [d.boundingBox.originX / W, d.boundingBox.originY / H, (d.boundingBox.originX + d.boundingBox.width) / W, (d.boundingBox.originY + d.boundingBox.height) / H].map(r3) }))
  const ans = ansikte.detect(c).detections.map(d => ({ s: r3(d.categories[0].score), b: [d.boundingBox.originX / W, d.boundingBox.originY / H, (d.boundingBox.originX + d.boundingBox.width) / W, (d.boundingBox.originY + d.boundingBox.height) / H].map(r3) }))
  // personrutor: COCO-personer, plus ansikten som ingen personruta täcker (delvis synliga personer)
  const rutor = saker.filter(s => s.k === 'person' && s.s >= 0.3).map(s => ({ b: s.b, s: s.s, kalla: 'coco' }))
  for (const a of ans) {
    const inne = rutor.some(r => a.b[0] >= r.b[0] - 0.02 && a.b[2] <= r.b[2] + 0.02 && a.b[1] >= r.b[1] - 0.02 && a.b[3] <= r.b[3] + 0.02)
    if (inne) continue
    const w = a.b[2] - a.b[0], h = a.b[3] - a.b[1]
    rutor.push({ b: [a.b[0] - w * 1.6, a.b[1] - h * 0.6, a.b[2] + w * 1.6, a.b[3] + h * 5].map((v, i) => Math.max(0, Math.min(1, v))), s: a.s, kalla: 'ansikte' })
  }
  // dubbletter
  rutor.sort((a, b) => b.s - a.s)
  const valda = []
  for (const r of rutor) if (!valda.some(v => iou(v.b, r.b) > 0.6)) valda.push(r)
  const ut = []
  for (const r of valda) {
    // utskärning med marginal, kvadratisk nog för Pose
    const bw = r.b[2] - r.b[0], bh = r.b[3] - r.b[1]
    let x0 = (r.b[0] - bw * 0.15) * W, x1 = (r.b[2] + bw * 0.15) * W, y0 = (r.b[1] - bh * 0.08) * H, y1 = (r.b[3] + bh * 0.08) * H
    const s = Math.max(x1 - x0, y1 - y0)
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2
    x0 = cx - s / 2; x1 = cx + s / 2; y0 = cy - s / 2; y1 = cy + s / 2
    const S = 256
    const crop = new OffscreenCanvas(S, S)
    const cg = crop.getContext('2d')
    cg.fillStyle = '#808080'
    cg.fillRect(0, 0, S, S)
    cg.drawImage(c, x0, y0, s, s, 0, 0, S, S)
    const p = pose.detect(crop)
    const lm0 = p.landmarks?.[0]
    if (!lm0) { ut.push({ b: r.b, s: r.s, kalla: r.kalla, lm: null }); continue }
    const lm = lm0.map(l => [r3((x0 + l.x * s) / W), r3((y0 + l.y * s) / H), r3(l.visibility ?? 0)])
    const varld = p.worldLandmarks?.[0]?.map(l => [r3(l.x), r3(l.y), r3(l.z)]) ?? null
    // en pose som hamnat på grannen: de flesta synliga punkterna ska ligga i personens ruta
    const syn = lm.filter(l => l[2] > 0.5)
    const inom = syn.filter(l => l[0] >= r.b[0] - bw * 0.2 && l[0] <= r.b[2] + bw * 0.2 && l[1] >= r.b[1] - bh * 0.15 && l[1] <= r.b[3] + bh * 0.15).length / Math.max(1, syn.length)
    ut.push({ b: r.b, s: r.s, kalla: r.kalla, lm, varld, inom: r3(inom), farger: personFarger(px, W, H, lm, r.b) })
  }
  return { personer: ut, saker: saker.filter(s => s.k !== 'person'), ansikten: ans }
}

window.spara = async ({ bas, ramar, fps }) => {
  await redo
  const ut = []
  for (const [n, f] of ramar.entries()) {
    const bmp = await bild(`${bas}/${f}`)
    if (!bmp) { ut.push({ t: r3(n / fps), saknas: true, personer: [], saker: [], ansikten: [] }); continue }
    ut.push({ t: r3(n / fps), ...(await personer(bmp)) })
    bmp.close()
    if (n % 20 === 0) status(`${n + 1}/${ramar.length}`)
  }
  return { delegat, ramar: ut }
}
window.sparRedo = redo
