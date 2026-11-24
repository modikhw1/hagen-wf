// Analysens webbläsardel. Körs i Edge (headless) av analys/kor.mjs, men kan också öppnas för hand.
// Kroppar: MediaPipe Pose Landmarker (33 punkter i bild och i 3D, flera personer).
// Händer: MediaPipe Hand Landmarker (21 punkter per hand). Händer som hanterar mat och produkter
// är ofta själva motivet i restaurangklipp, och Pose ser dem inte när kroppen är utanför bild.
// Objekt: MediaPipe Object Detector (EfficientDet-Lite2, COCO). Bekräftar att en kropp är en person
// (Pose hittar falska kroppar i mat med hög säkerhet) och säger vad objektscenerna innehåller.
// Ansikten: MediaPipe Face Detector (BlazeFace full range). Andra beviset för en person när
// objektdetektorn missar (delvis synliga personer, grupper på avstånd).
// Kamera: OpenCV.js, rörelsen i bakgrunden mellan rutor (personerna maskas bort), som en affin
// transform: förflyttning, rotation och skala. Över ett klipp: ORB-matchning före/efter, för att
// avgöra om det är samma bild (hopp, zoomryck) eller en ny scen.
import { FilesetResolver, PoseLandmarker, HandLandmarker, ObjectDetector, FaceDetector } from '@mediapipe/tasks-vision'
import cvModule from '@techstark/opencv-js'
import { forbered, pixelmatt } from './pixlar.js'

const status = t => { document.getElementById('status').textContent = t }
const r3 = v => Math.round(v * 1000) / 1000

let cv
let pose
let hand
let objekt
let ansikte
let delegat
let gftt
let klocka = 0 // MediaPipe i videoläge vill ha stigande tider över alla klipp

async function init() {
  cv = cvModule instanceof Promise ? await cvModule : cvModule
  if (!cv.Mat) await new Promise(res => { cv.onRuntimeInitialized = res })
  const fileset = await FilesetResolver.forVisionTasks('/node_modules/@mediapipe/tasks-vision/wasm')
  for (const d of ['GPU', 'CPU']) {
    try {
      pose = await PoseLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: '/modeller/pose_landmarker_full.task', delegate: d },
        runningMode: 'VIDEO', numPoses: 4,
        minPoseDetectionConfidence: 0.5, minPosePresenceConfidence: 0.5, minTrackingConfidence: 0.5,
      })
      hand = await HandLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: '/modeller/hand_landmarker.task', delegate: d },
        runningMode: 'VIDEO', numHands: 4,
        minHandDetectionConfidence: 0.5, minHandPresenceConfidence: 0.5, minTrackingConfidence: 0.5,
      })
      objekt = await ObjectDetector.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: '/modeller/efficientdet_lite2.tflite', delegate: d },
        runningMode: 'VIDEO', maxResults: 12, scoreThreshold: 0.3,
      })
      ansikte = await FaceDetector.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: '/modeller/blaze_face_full_range.tflite', delegate: d },
        runningMode: 'VIDEO', minDetectionConfidence: 0.5,
      })
      delegat = d
      break
    } catch (e) { console.warn('delegat', d, e) }
  }
  const saknas = ['ORB', 'BFMatcher', 'calcOpticalFlowPyrLK', 'GFTTDetector', 'estimateAffine2D'].filter(f => !cv[f])
  if (saknas.length) throw new Error('OpenCV saknar ' + saknas.join(', '))
  gftt = new cv.GFTTDetector(300, 0.01, 8, 5)
  status(`redo · pose ${delegat}`)
  return { delegat }
}
const redo = init()

// Hämta en ruta. Nytt försök vid nätverksfel; en ruta som ändå inte går att läsa blir null.
async function bild(url) {
  for (let f = 0; f < 4; f++) {
    try {
      const r = await fetch(url, { cache: 'no-store' })
      if (!r.ok) throw new Error('http ' + r.status)
      return await createImageBitmap(await r.blob())
    } catch (e) {
      if (f === 3) { console.warn('ruta saknas', url, e.message); return null }
      await new Promise(res => setTimeout(res, 150 * (f + 1)))
    }
  }
}
function gra(bmp) {
  const c = new OffscreenCanvas(bmp.width, bmp.height)
  const g = c.getContext('2d', { willReadFrequently: true })
  g.drawImage(bmp, 0, 0)
  const rgba = cv.matFromImageData(g.getImageData(0, 0, c.width, c.height))
  const m = new cv.Mat()
  cv.cvtColor(rgba, m, cv.COLOR_RGBA2GRAY)
  rgba.delete()
  return m
}

// Personer: punkter i bild (x, y i 0–1, synlighet), i 3D (meter, höften som origo) och ruta.
function personer(res) {
  return (res.landmarks ?? []).map((lm, i) => {
    const syns = lm.filter(p => (p.visibility ?? 1) > 0.3)
    const xs = syns.map(p => p.x)
    const ys = syns.map(p => p.y)
    const bbox = syns.length ? [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)].map(r3) : null
    return {
      lm: lm.map(p => [r3(p.x), r3(p.y), r3(p.visibility ?? 1)]),
      varld: (res.worldLandmarks?.[i] ?? []).map(p => [r3(p.x), r3(p.y), r3(p.z)]),
      bbox,
    }
  })
}

// Mask för bakgrunden: personernas rutor (lite större) tas bort.
function bakgrundsmask(w, h, pers) {
  const m = new cv.Mat(h, w, cv.CV_8UC1, new cv.Scalar(255))
  for (const p of pers) {
    if (!p.bbox) continue
    const [x0, y0, x1, y1] = p.bbox
    const px = (x1 - x0) * 0.15
    const py = (y1 - y0) * 0.1
    const a = new cv.Point(Math.max(0, (x0 - px) * w), Math.max(0, (y0 - py) * h))
    const b = new cv.Point(Math.min(w - 1, (x1 + px) * w), Math.min(h - 1, (y1 + py) * h))
    cv.rectangle(m, a, b, new cv.Scalar(0), -1)
  }
  return m
}

// Affin transform → hur bildens mitt flyttas (andel av bredd/höjd), rotation (grader), skala.
function tolkaAffin(M, w, h) {
  const d = M.data64F
  const [a, b, tx, c, dd, ty] = d
  const cx = w / 2
  const cy = h / 2
  const nx = a * cx + b * cy + tx
  const ny = c * cx + dd * cy + ty
  return {
    dx: r3((nx - cx) / w),
    dy: r3((ny - cy) / h),
    rot: r3((Math.atan2(c, a) * 180) / Math.PI),
    skala: r3(Math.sqrt(Math.abs(a * dd - b * c))),
  }
}

function kamerarorelse(fore, nu, mask) {
  const w = fore.cols
  const h = fore.rows
  // OpenCV.js 5 har GFTTDetector som klass (goodFeaturesToTrack finns inte som funktion).
  const kp = new cv.KeyPointVector()
  gftt.detect(fore, kp, mask)
  if (kp.size() < 12) { kp.delete(); return null }
  const pts = []
  for (let i = 0; i < kp.size(); i++) { const p = kp.get(i).pt; pts.push(p.x, p.y) }
  kp.delete()
  const horn = cv.matFromArray(pts.length / 2, 1, cv.CV_32FC2, pts)
  const nasta = new cv.Mat()
  const st = new cv.Mat()
  const fel = new cv.Mat()
  cv.calcOpticalFlowPyrLK(fore, nu, horn, nasta, st, fel, new cv.Size(21, 21), 3)
  const fran = []
  const till = []
  for (let i = 0; i < st.rows; i++) {
    if (st.data[i] !== 1) continue
    fran.push(horn.data32F[i * 2], horn.data32F[i * 2 + 1])
    till.push(nasta.data32F[i * 2], nasta.data32F[i * 2 + 1])
  }
  horn.delete(); nasta.delete(); st.delete(); fel.delete()
  const n = fran.length / 2
  if (n < 10) return null
  const A = cv.matFromArray(n, 1, cv.CV_32FC2, fran)
  const B = cv.matFromArray(n, 1, cv.CV_32FC2, till)
  const inl = new cv.Mat()
  const M = cv.estimateAffine2D(A, B, inl, cv.RANSAC, 2.0)
  let ut = null
  if (!M.empty()) {
    let k = 0
    for (let i = 0; i < inl.rows; i++) k += inl.data[i] ? 1 : 0
    ut = { ...tolkaAffin(M, w, h), inl: r3(k / n), n }
  }
  A.delete(); B.delete(); inl.delete(); M.delete()
  return ut
}

// Samma bild före och efter ett klipp? ORB-punkter, kvotest, RANSAC.
function likhet(a, b) {
  const orb = new cv.ORB(600)
  const ka = new cv.KeyPointVector()
  const kb = new cv.KeyPointVector()
  const da = new cv.Mat()
  const db = new cv.Mat()
  const tom = new cv.Mat()
  orb.detectAndCompute(a, tom, ka, da)
  orb.detectAndCompute(b, tom, kb, db)
  let ut = { n: 0, inl: 0 }
  if (da.rows >= 8 && db.rows >= 8) {
    const bf = new cv.BFMatcher(cv.NORM_HAMMING, false)
    const mm = new cv.DMatchVectorVector()
    bf.knnMatch(da, db, mm, 2)
    const fran = []
    const till = []
    for (let i = 0; i < mm.size(); i++) {
      const m = mm.get(i)
      if (m.size() < 2) continue
      const m0 = m.get(0)
      const m1 = m.get(1)
      if (m0.distance < 0.75 * m1.distance) {
        const p = ka.get(m0.queryIdx).pt
        const q = kb.get(m0.trainIdx).pt
        fran.push(p.x, p.y)
        till.push(q.x, q.y)
      }
    }
    const n = fran.length / 2
    ut = { n, inl: 0, matchningar: n, punkter: Math.min(ka.size(), kb.size()) }
    if (n >= 8) {
      const A = cv.matFromArray(n, 1, cv.CV_32FC2, fran)
      const B = cv.matFromArray(n, 1, cv.CV_32FC2, till)
      const inl = new cv.Mat()
      const M = cv.estimateAffine2D(A, B, inl, cv.RANSAC, 3.0)
      if (!M.empty()) {
        let k = 0
        for (let i = 0; i < inl.rows; i++) k += inl.data[i] ? 1 : 0
        ut = { ...ut, ...tolkaAffin(M, a.cols, a.rows), inliers: k, inl: r3(k / Math.max(1, ut.punkter)) }
      }
      A.delete(); B.delete(); inl.delete(); M.delete()
    }
    bf.delete(); mm.delete()
  }
  orb.delete(); ka.delete(); kb.delete(); da.delete(); db.delete(); tom.delete()
  return ut
}

// Hela klippet: alla rutor i ordning, plus jämförelser runt klippkandidaterna.
window.analysera = async ({ bas, ramar, fps, kandidater }) => {
  await redo
  klocka += 10_000
  const ut = []
  let fore = null
  let foreLiten = null
  let forePers = []
  const t0 = performance.now()
  for (const [n, namn] of ramar.entries()) {
    const bmp = await bild(`${bas}/${namn}`)
    if (!bmp) { fore?.delete(); fore = null; foreLiten?.delete(); foreLiten = null; forePers = []; ut.push({ t: r3(n / fps), personer: [], kamera: null, saknas: true }); continue }
    const ts = klocka + Math.round((n / fps) * 1000)
    // objektdetektorn först och på en egen kopia: efter Pose/Hand var bitmappen tom för den
    const kopia = new OffscreenCanvas(bmp.width, bmp.height)
    kopia.getContext('2d').drawImage(bmp, 0, 0)
    const sakerRes = objekt.detectForVideo(kopia, ts)
    const ansikten = ansikte.detectForVideo(kopia, ts).detections.map(d => {
      const b = d.boundingBox
      return { s: r3(d.categories[0]?.score ?? 0), b: [r3(b.originX / kopia.width), r3(b.originY / kopia.height), r3((b.originX + b.width) / kopia.width), r3((b.originY + b.height) / kopia.height)] }
    })
    const pers = personer(pose.detectForVideo(bmp, ts))
    const hr = hand.detectForVideo(bmp, ts)
    const hander = (hr.landmarks ?? []).map((lm, i) => ({
      lm: lm.flatMap(p => [r3(p.x), r3(p.y)]),
      sida: hr.handedness?.[i]?.[0]?.categoryName ?? null,
      s: r3(hr.handedness?.[i]?.[0]?.score ?? 0),
    }))
    const g = gra(kopia) // kopian: bitmappen kan vara förbrukad efter MediaPipe
    // bildens egna egenskaper (energi, kanter, symmetri, entropi, balans), samma mått överallt
    const liten = forbered(cv, g)
    const pix = pixelmatt(cv, liten, foreLiten)
    foreLiten?.delete()
    foreLiten = liten
    let kamera = null
    if (fore) {
      // händer maskas också bort: de rör sig mest av allt i bild och är inte kameran
      const handrutor = hander.map(h => { const xs = h.lm.filter((_, i) => i % 2 === 0); const ys = h.lm.filter((_, i) => i % 2 === 1); return { bbox: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] } })
      const mask = bakgrundsmask(g.cols, g.rows, [...forePers, ...pers, ...handrutor])
      kamera = kamerarorelse(fore, g, mask)
      mask.delete()
      fore.delete()
    }
    fore = g
    forePers = pers
    bmp.close()
    const saker = sakerRes.detections.map(d => {
      const b = d.boundingBox
      return { k: d.categories[0]?.categoryName, s: r3(d.categories[0]?.score ?? 0), b: [r3(b.originX / kopia.width), r3(b.originY / kopia.height), r3((b.originX + b.width) / kopia.width), r3((b.originY + b.height) / kopia.height)] }
    })
    ut.push({ t: r3(n / fps), personer: pers, hander, saker, ansikten, kamera, pix })
    if (n % 20 === 0) status(`ruta ${n + 1}/${ramar.length}`)
  }
  fore?.delete()
  foreLiten?.delete()
  klocka += Math.round((ramar.length / fps) * 1000)
  const jamf = []
  for (const k of kandidater) {
    const ba = await bild(`${bas}/${k.a}`)
    const bb = await bild(`${bas}/${k.b}`)
    if (!ba || !bb) { jamf.push({ t: k.t, n: 0, inl: 0, saknas: true }); continue }
    const a = gra(ba)
    const b = gra(bb)
    const nara = likhet(a, b)
    a.delete(); b.delete(); ba.close(); bb.close()
    // längre ifrån: före och efter en övergång (tona, whip), som sträcker sig över flera rutor
    let vid = null
    if (k.c && k.d) {
      const bc = await bild(`${bas}/${k.c}`)
      const bd = await bild(`${bas}/${k.d}`)
      if (bc && bd) { const c = gra(bc); const d = gra(bd); vid = likhet(c, d); c.delete(); d.delete(); bc.close(); bd.close() }
    }
    jamf.push({ t: k.t, ...nara, vid })
  }
  return { ramar: ut, kandidater: jamf, delegat, ms: Math.round(performance.now() - t0) }
}
window.analysRedo = redo
