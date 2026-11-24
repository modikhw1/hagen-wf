// Mät uttrycksrummet: för varje scen och varje uttryck, motorns syn (inget renderas) genom samma
// tolkning som analysen av riktiga klipp, och samma egenskaper. Körs av uttryck/kor.mjs.
import * as THREE from 'three'
import { Spelare } from '../src/forandring/motor/spelare'
import { skapaSyn, bakgrundspunkter } from '../src/forandring/motor/syn'
import { kameraOk, MARKERA, MAGENTA } from '../src/forandring/motor/lokal'
import { INDEX } from '../src/forandring/motor/skelett'
import { ORIGINAL } from '../src/forandring/manus/nonna-smakar'
import { allaUttryck, rekonUttryck, kameraFor, originalUttryck, uttryckId, AMP } from '../src/forandring/manus/uttryck'
import { scenMed } from '../src/forandring/manus/variant'
import { tolka } from '../analys/tolka.mjs'
import { scenEgenskaper } from '../kalibrering/egenskaper.mjs'
import cvModule from '@techstark/opencv-js'
import { forbered, pixelmatt } from '../analys/pixlar.js'

// OpenCV för pixelmåtten (samma funktion som analysen av riktiga klipp använder)
let cv
const cvRedo = (async () => {
  cv = cvModule instanceof Promise ? await cvModule : cvModule
  if (!cv.Mat) await new Promise(res => { cv.onRuntimeInitialized = res })
})()
const yta = new OffscreenCanvas(90, 160)
const ytaG = yta.getContext('2d', { willReadFrequently: true })
// Rendera rutan och mät pixlarna; kanvasen läses i samma uppgift som renderingen.
// Energin (bildskillnad) mäts mot en ruta 0,1 s tidigare, samma tidssteg som analysen av riktiga
// klipp (10 rutor/s), fast uttrycken mäts med 5 rutor/s: annars får samma rörelse dubbel energi.
const ANALYS_DT = 0.1
function litenAv(s, t) {
  s.renderAt(t)
  ytaG.drawImage(document.getElementById('c'), 0, 0, 90, 160)
  const rgba = cv.matFromImageData(ytaG.getImageData(0, 0, 90, 160))
  const gra = new cv.Mat()
  cv.cvtColor(rgba, gra, cv.COLOR_RGBA2GRAY)
  rgba.delete()
  const liten = forbered(cv, gra)
  gra.delete()
  return liten
}
function pixlarFor(s, t) {
  const fore = t >= ANALYS_DT ? litenAv(s, t - ANALYS_DT) : null
  const liten = litenAv(s, t)
  const pix = pixelmatt(cv, liten, fore)
  fore?.delete()
  return { pix, liten }
}

// Täckning: hur stor del av bilden som originalet faktiskt såg (projicerad ren skiva). En kamera som
// ser tomrum eller baksidor visar inte ett annat sätt att filma scenen utan rekonstruktionens kanter.
const MIN_TACKNING = 0.88
function tackning(s, tider) {
  const bak = s.scene.background
  s.scene.background = new THREE.Color(MAGENTA)
  MARKERA.value = 1
  let tackt = 0, alla = 0
  for (const t of tider) {
    s.renderAt(t)
    ytaG.drawImage(document.getElementById('c'), 0, 0, 90, 160)
    const d = ytaG.getImageData(0, 0, 90, 160).data
    for (let k = 0; k < d.length; k += 4) { alla++; if (!(d[k] > 200 && d[k + 1] < 60 && d[k + 2] > 200)) tackt++ }
  }
  MARKERA.value = 0
  s.scene.background = bak
  return tackt / Math.max(1, alla)
}

const FPS = 5
const status = t => { document.getElementById('status').textContent = t }
const r3 = v => Math.round(v * 1000) / 1000

let sp
let bakgrund
let MANUS = ORIGINAL // originalet (Nonna) eller ett rekonstruerat klipp (matScen({ url }))
function spelare() {
  if (!sp) {
    sp = new Spelare(document.getElementById('c'), { bredd: 90, hojd: 160, pixelRatio: 1 })
    sp.pause()
  }
  return sp
}
async function laddaManus(url) {
  const nytt = url ? await (await fetch(url, { cache: 'no-store' })).json() : ORIGINAL
  if (nytt.id === MANUS.id && bakgrund) return
  MANUS = nytt
  const s = spelare()
  s.load(MANUS)
  await s.redo
  bakgrund = bakgrundspunkter(s.lokal)
}

// Mät ett uttryck för scen i: egenskaper, kameraord, utsnitt, och om bilden är giltig
// (kameran i rummet och inte i en person, huvudpersonen i bild).
function matUttryck(i, kamera, amp = 1, id = null) {
  const s = spelare()
  const sc = MANUS.scener[i]
  // med id: hela uttrycket via scenMed (kamera, agerande, statist), samma som reglaget spelar
  const variant = id ? scenMed(sc, id, MANUS.lokal?.scener?.[i]) : { ...sc, kamera, handling: amp === 1 ? sc.handling : sc.handling.map(h => ({ ...h, amp })) }
  const m = { ...MANUS, scener: [{ ...variant, in: undefined }] }
  s.sattManus(m)
  const syn = skapaSyn(s, { bakgrund, gles: 4, enkel: true })
  const n = Math.max(3, Math.floor(sc.tid * FPS))
  const ramar = []
  let giltig = true
  const tmp = new THREE.Vector3()
  for (let k = 0; k < n; k++) {
    const { pix, liten } = pixlarFor(s, k / FPS)
    liten.delete()
    const f = syn(k / FPS)
    ramar.push({ ...f, personer: f.personer.map(({ roll, ...p }) => p), hander: [], pix })
    const pos = s.cam.position
    if (!kameraOk(MANUS.lokal, pos)) giltig = false
    for (const d of Object.values(s.dockor)) {
      if (!d.root.visible) continue
      for (const b of d.bones) if (b.getWorldPosition(tmp).distanceTo(pos) < 0.22) giltig = false
    }
  }
  // täckningen räknas bara där lokalen är en projicerad skiva (rekonstruktioner)
  // bara för fotoprojektionen: i den modellerade scenen (stil modell) är väggar och golv giltiga från alla håll
  const tack = MANUS.stil !== 'modell' && MANUS.lokal?.scener?.some(x => x.platta) ? tackning(s, [0, (n - 1) / FPS / 2, (n - 1) / FPS]) : 1
  if (tack < MIN_TACKNING) giltig = false
  const a = tolka({ id: 'u', meta: { langd: sc.tid, bredd: 360, hojd: 640, fps: FPS }, kandidater: [], sett: { ramar, kandidater: [] }, fps: FPS })
  const scen = a.scener[0]
  if (scen.utsnitt.varde === 'objekt') giltig = false // huvudpersonen syns inte
  // en närbild ska visa ansiktet, inte bakhuvudet (motorns syn ger ansikte bara när det är vänt mot kameran)
  const medAnsikte = ramar.filter(r => r.ansikten?.length).length / ramar.length
  if (['nara', 'extrem'].includes(variant.kamera?.utsnitt) && medAnsikte < 0.4) giltig = false
  return { e: scenEgenskaper(scen), ord: scen.kamera.ord, utsnitt: scen.utsnitt.varde, giltig, tackning: Math.round(tack * 1000) / 1000 }
}

// Urvalet för rekonstruerade klipp (längre scener, fler personer): kameror utan de yttersta
// vinklarna och det kraftigaste skaket (2 250), originalets kamera med varje agerande, och ett
// deterministiskt urval av kameror med lugnare och större agerande.
// Urvalet för rekonstruerade klipp: kameror relativa originalets (2 250), originalets kamera med varje
// agerande, och ett deterministiskt urval av kameror med lugnare och större agerande.
function* rekonUrval() {
  const bred = MANUS.stil === 'modell'
  for (const p of rekonUttryck({ bred })) yield [p, 1, 0]
  let n = 0
  for (const p of rekonUttryck({ bred })) {
    const k = (n++ * 7919) % 11
    if (k === 0) for (const a of [0.7, 1.4]) yield [p, a, 0] // ungefär var 11:e: annat agerande
    if (k === 5 && MANUS.roller?.statist) yield [p, 1, 1] // ungefär var 11:e: statist i bakgrunden
  }
}

window.matScen = async ({ i, max = Infinity, url = null }) => {
  await laddaManus(url)
  const sc = MANUS.scener[i]
  const ut = []
  const t0 = performance.now()
  const o = sc.kamera.bana ? null : originalUttryck(sc)
  ut.push({ id: 'original', p: o, ...matUttryck(i, sc.kamera) })
  if (url) for (const a of AMP) if (a !== 1) ut.push({ id: uttryckId(null, a), p: null, ...matUttryck(i, sc.kamera, a) })
  // statisten (bara där rollen finns, den modellerade scenen): originalets kamera med och utan ändrat agerande
  if (MANUS.roller?.statist) for (const a of [1, 0.7, 1.4]) { const sid = uttryckId(null, a, 1); ut.push({ id: sid, p: null, ...matUttryck(i, null, 1, sid) }) }
  let k = 0
  for (const [p, a, b] of url ? rekonUrval() : [...allaUttryck()].map(p => [p, 1, 0])) {
    if (k++ >= max) break
    const uid = uttryckId(p, a, b)
    ut.push({ id: uid, p, ...(b ? matUttryck(i, null, 1, uid) : matUttryck(i, kameraFor(sc, p), a)) })
    if (k % 250 === 0) { status(`scen ${i + 1}: ${k}`); await new Promise(r => setTimeout(r, 0)) }
  }
  const kompakt = ut.map(x => ({ id: x.id, e: Object.fromEntries(Object.entries(x.e).map(([n, v]) => [n, r3(v)])), ord: x.ord, utsnitt: x.utsnitt, giltig: x.giltig || x.id === 'original', tackning: x.tackning }))
  return { i, scen: sc.id, text: sc.text, antal: kompakt.length, ms: Math.round(performance.now() - t0), uttryck: kompakt }
}
window.matningRedo = cvRedo.then(() => Object.keys(INDEX).length > 0)
window.antalScener = async url => { await laddaManus(url); return MANUS.scener.length }
