import { test as prova } from 'node:test'
import kontroll from 'node:assert/strict'
import * as THREE from 'three'
import { JOINTS, PARENT, OFFSET, INDEX } from '../src/forandring/motor/skelett.js'
import { retarget, retargetSpar, LYFT } from './rorelse.mjs'

// rorelse.mjs har redan läst motormodulen med dess filändelse korrigerad för Node.
const { NEUTRAL, toQuats } = await import('../src/forandring/motor/pose.js')
const grader = 180 / Math.PI
const benleder = ['left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle', 'left_foot', 'right_foot']
const riktningar = [
  ['left_shoulder', 'left_elbow'], ['right_shoulder', 'right_elbow'],
  ['left_elbow', 'left_wrist'], ['right_elbow', 'right_wrist'],
  ['left_hip', 'left_knee'], ['right_hip', 'right_knee'],
  ['left_knee', 'left_ankle'], ['right_knee', 'right_ankle'],
  ['left_ankle', 'left_foot'], ['right_ankle', 'right_foot'],
]

// Samma transformkedja som docka.setPose, men utan scen, material eller DOM.
function framAt(quats, { skala = 1, x = 0, z = 0, lift = 0 } = {}) {
  const positioner = [], globala = []
  for (const [i, led] of JOINTS.entries()) {
    const foralder = PARENT[i]
    const lokal = new THREE.Vector3(...OFFSET[led]).multiplyScalar(skala)
    if (foralder < 0) {
      positioner[i] = lokal.add(new THREE.Vector3(x, lift, z))
      globala[i] = quats[i].clone()
    } else {
      positioner[i] = lokal.applyQuaternion(globala[foralder]).add(positioner[foralder])
      globala[i] = globala[foralder].clone().multiply(quats[i])
    }
  }
  return { positioner, globala }
}

function syntetisera(pose = {}, { skala = 1, x = 0, z = 0, lift = 0, rotation = [0, 0, 0] } = {}) {
  const quats = toQuats({ ...NEUTRAL, ...pose })
  quats[INDEX.pelvis].premultiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(...rotation.map(v => v / grader), 'YXZ')))
  const original = framAt(quats, { skala, x, z, lift })
  const punkter = Array.from({ length: 33 }, () => [0, 0, 0])
  for (const [i, led] of [
    [11, 'left_shoulder'], [12, 'right_shoulder'], [13, 'left_elbow'], [14, 'right_elbow'],
    [15, 'left_wrist'], [16, 'right_wrist'], [23, 'left_hip'], [24, 'right_hip'],
    [25, 'left_knee'], [26, 'right_knee'], [27, 'left_ankle'], [28, 'right_ankle'],
    [31, 'left_foot'], [32, 'right_foot'],
  ]) punkter[i] = original.positioner[INDEX[led]].toArray()
  const vidLed = (led, lokal) => new THREE.Vector3(...lokal).multiplyScalar(skala)
    .applyQuaternion(original.globala[INDEX[led]]).add(original.positioner[INDEX[led]]).toArray()
  for (const [i, lokal] of [
    [7, [0.07, 0.08, 0]], [8, [-0.07, 0.08, 0]], [0, [0, 0.08, 0.12]],
    [2, [0.035, 0.08, 0.06]], [5, [-0.035, 0.08, 0.06]],
  ]) punkter[i] = vidLed('head', lokal)
  for (const [armbage, handled, lillfinger, pekfinger] of [[13, 15, 17, 19], [14, 16, 18, 20]]) {
    const hand = new THREE.Vector3(...punkter[handled])
    const riktning = hand.clone().sub(new THREE.Vector3(...punkter[armbage])).normalize()
    hand.addScaledVector(riktning, 0.08 * skala)
    punkter[lillfinger] = hand.toArray()
    punkter[pekfinger] = hand.toArray()
  }
  punkter[29] = vidLed('left_ankle', [0, -0.04, -0.04])
  punkter[30] = vidLed('right_ankle', [0, -0.04, -0.04])
  return { ruta: { punkter, synlighet: Array(33).fill(1) }, original, quats }
}

const riktning = (pose, a, b) => pose.positioner[INDEX[b]].clone().sub(pose.positioner[INDEX[a]]).normalize()
const franRam = (spar, i, skala = 1) => framAt(spar.ramar[i].map(q => new THREE.Quaternion(...q).normalize()), {
  x: spar.bana[i][0], z: spar.bana[i][1], lift: spar.bana[i][3], skala,
})
const standardavvikelse = varden => {
  const medel = varden.reduce((a, b) => a + b, 0) / varden.length
  return Math.sqrt(varden.reduce((summa, v) => summa + (v - medel) ** 2, 0) / varden.length)
}
const nara = (a, b, tolerans = 1e-9) => kontroll.ok(Math.abs(a - b) < tolerans, `${a} skiljer sig från ${b}`)
const sammaRotation = (a, b, grans = 1e-5) => kontroll.ok(a.angleTo(b) * grader < grans, `rotationsfel ${a.angleTo(b) * grader}°`)
const flytta = (ruta, x, y = 0, z = 0) => ({
  punkter: ruta.punkter.map(p => [p[0] + x, p[1] + y, p[2] + z]),
  synlighet: ruta.synlighet.slice(),
})

function kontrolleraSpar(spar, antal) {
  kontroll.equal(spar.ramar.length, antal)
  kontroll.equal(spar.bana.length, antal)
  for (const ram of spar.ramar) {
    kontroll.equal(ram.length, 22)
    for (const q of ram) {
      kontroll.equal(q.length, 4)
      kontroll.ok(q.every(Number.isFinite))
      nara(Math.hypot(...q), 1, 0.00011)
      for (const v of q) kontroll.equal(v, Number(v.toFixed(4)))
    }
  }
  for (const punkt of spar.bana) {
    kontroll.equal(punkt.length, 4)
    kontroll.ok(punkt.every(Number.isFinite))
    kontroll.equal(punkt[2], 0)
  }
}

prova('rundtur via FK bevarar benriktningar samt bäckenets och bröstets orientering', () => {
  for (const skala of [0.83, 1, 1.24]) for (const vridning of [-60, 60]) {
    // En vriden bål prövar även den fördelade ryggradsrotationen. Ledpunkternas
    // fasta förskjutningar gör att bålriktningen bara uppskattar benramarnas uppaxel.
    const { ruta, original } = syntetisera({
      spine: [0, 0, vridning], neck: [10, -3, 18],
      lArm: [145, 35, 12], rArm: [55, -20, -10], lElbow: 65, rElbow: 42,
      lLeg: [28, 8], rLeg: [-15, 5], lKnee: 45, rKnee: 20, lAnkle: 10, rAnkle: -5,
    }, { skala, x: 1.4, z: -2, lift: 0.12, rotation: [7, 32, -5] })
    const ut = retarget(ruta.punkter, ruta.synlighet, { skala })
    const ater = framAt(ut.quats, { ...ut, skala })
    kontroll.deepEqual(ut.saknas, [])
    kontroll.ok(ut.quats.every(q => q instanceof THREE.Quaternion))
    for (const [a, b] of riktningar) {
      const fel = riktning(original, a, b).angleTo(riktning(ater, a, b)) * grader
      kontroll.ok(fel < 3, `${a} → ${b}: ${fel}°`)
    }
    for (const led of ['pelvis', 'spine3']) sammaRotation(original.globala[INDEX[led]], ater.globala[INDEX[led]], 3)
    sammaRotation(original.globala[INDEX.head], ater.globala[INDEX.head])
    sammaRotation(ut.quats[INDEX.spine1], ut.quats[INDEX.spine2])
    sammaRotation(ut.quats[INDEX.spine2], ut.quats[INDEX.spine3])
    sammaRotation(ut.quats[INDEX.neck], ut.quats[INDEX.head])
    for (const led of ['left_collar', 'right_collar']) sammaRotation(ut.quats[INDEX[led]], new THREE.Quaternion())
    for (const [led, handled, lillfinger] of [['left_wrist', 15, 17], ['right_wrist', 16, 18]]) {
      const hand = new THREE.Vector3(...OFFSET[led]).normalize().applyQuaternion(ater.globala[INDEX[led]])
      const mal = new THREE.Vector3(...ruta.punkter[lillfinger]).sub(new THREE.Vector3(...ruta.punkter[handled])).normalize()
      kontroll.ok(hand.angleTo(mal) * grader < 0.001)
    }
    nara(ut.x, (ruta.punkter[23][0] + ruta.punkter[24][0]) / 2)
    nara(ut.z, (ruta.punkter[23][2] + ruta.punkter[24][2]) / 2)
    nara(ut.lift, (ruta.punkter[23][1] + ruta.punkter[24][1]) / 2 - OFFSET.pelvis[1] * skala)
  }
})

prova('osynliga ben blir neutrala och begränsar höjden, med upprätt bäcken från axlarna', () => {
  const neutrala = toQuats(NEUTRAL)
  for (const [lift, vantat] of [[0.1, null], [0.8, LYFT[1]]]) {
    const { ruta } = syntetisera({ lLeg: [25, 8], rKnee: 50 }, { lift, rotation: [0, 35, 0] })
    for (let i = 23; i <= 32; i++) ruta.synlighet[i] = 0
    const ut = retarget(ruta.punkter, ruta.synlighet)
    for (const led of benleder) {
      sammaRotation(ut.quats[INDEX[led]], neutrala[INDEX[led]])
      kontroll.ok(ut.saknas.includes(led), `${led} saknas i saknas`)
    }
    kontroll.ok(ut.lift >= LYFT[0] && ut.lift <= LYFT[1])
    if (vantat != null) nara(ut.lift, vantat)
    const upp = new THREE.Vector3(0, 1, 0).applyQuaternion(ut.quats[INDEX.pelvis])
    nara(upp.y, 1)
    const vanster = new THREE.Vector3(...ruta.punkter[11]).sub(new THREE.Vector3(...ruta.punkter[12]))
    vanster.y = 0
    kontroll.ok(new THREE.Vector3(1, 0, 0).applyQuaternion(ut.quats[INDEX.pelvis]).angleTo(vanster) < 1e-6)
  }
})

prova('låg höftposition med dolda ben ger sittande pose och behåller höjden', () => {
  const { ruta } = syntetisera({}, { lift: -0.35, skala: 1.2 })
  for (let i = 23; i <= 32; i++) ruta.synlighet[i] = 0
  const ut = retarget(ruta.punkter, ruta.synlighet, { skala: 1.2 })
  const sittande = toQuats({ ...NEUTRAL, lLeg: [85, 5], rLeg: [85, 5], lKnee: 90, rKnee: 90 })
  for (const led of ['left_hip', 'right_hip', 'left_knee', 'right_knee']) sammaRotation(ut.quats[INDEX[led]], sittande[INDEX[led]])
  nara(ut.lift, (ruta.punkter[23][1] + ruta.punkter[24][1]) / 2 - OFFSET.pelvis[1] * 1.2)
  kontroll.ok(ut.lift < -0.25)
})

prova('retargetSpar fyller fyra rutor och dämpar punktbrus utan att ändra indata', () => {
  const { ruta } = syntetisera({ lArm: [85, 0, 0], lElbow: 25 })
  const rutor = Array.from({ length: 41 }, (_, i) => flytta(ruta, i * 0.015))
  rutor[20].punkter[15][1] += 0.5
  const ra = rutor.map(r => new THREE.Vector3(...r.punkter[15]).sub(new THREE.Vector3(...r.punkter[13])).normalize().y)
  for (let i = 7; i <= 10; i++) rutor[i] = null
  const fore = structuredClone(rutor)
  const spar = retargetSpar(rutor, { fps: 12 })
  kontrolleraSpar(spar, rutor.length)
  kontroll.equal(spar.fps, 12)
  kontroll.deepEqual(rutor, fore)
  for (let i = 7; i <= 10; i++) {
    nara(spar.bana[i][0], i * 0.015)
    kontroll.ok(spar.bana[i][0] > spar.bana[i - 1][0])
  }
  const jamna = spar.ramar.map((_, i) => riktning(franRam(spar, i), 'left_elbow', 'left_wrist').y)
  const brusFore = standardavvikelse(ra), brusEfter = standardavvikelse(jamna)
  kontroll.ok(brusEfter < brusFore, `brusets standardavvikelse: ${brusFore} → ${brusEfter}`)
  for (let steg = 1; steg <= 2; steg++) nara(jamna[20 - steg], jamna[20 + steg], 0.0005)
})

prova('root får ett starkare centrerat filter och låg synlighet minskar punktens vikt', () => {
  const { ruta } = syntetisera({ lArm: [90, 0, 0], lElbow: 0 })
  const rutor = Array.from({ length: 31 }, (_, i) => flytta(ruta, i === 15 ? 0.4 : 0))
  const spar = retargetSpar(rutor)
  kontrolleraSpar(spar, 31)
  kontroll.equal(spar.fps, 10)
  kontroll.ok(spar.bana[15][0] > 0 && spar.bana[15][0] < 0.1)
  for (let steg = 1; steg <= 6; steg++) nara(spar.bana[15 - steg][0], spar.bana[15 + steg][0])
  nara(spar.bana.reduce((summa, p) => summa + p[0], 0), 0.4)
  const brus = Array.from({ length: 31 }, () => flytta(ruta, 0))
  brus[15].punkter[15][1] += 0.4
  const stark = retargetSpar(brus)
  brus[15].synlighet[15] = 0.1
  const svag = retargetSpar(brus)
  const bas = riktning(franRam(retargetSpar([ruta]), 0), 'left_elbow', 'left_wrist')
  const fel = klipp => bas.angleTo(riktning(franRam(klipp, 15), 'left_elbow', 'left_wrist'))
  kontroll.ok(fel(svag) < fel(stark) * 0.25)
})

prova('tio rutor interpoleras, längre luckor och slutet håller exakt sista pose', () => {
  const a = syntetisera({ lArm: [30, 0, 0] }).ruta
  const b = syntetisera({ lArm: [160, 0, 0] }, { x: 2 }).ruta
  const kort = retargetSpar([a, ...Array(10).fill(null), b])
  kontrolleraSpar(kort, 12)
  kontroll.ok(kort.bana[5][0] > kort.bana[0][0])
  kontroll.ok(kort.bana[5][0] < kort.bana[11][0])
  kontroll.notDeepEqual(kort.ramar[5], kort.ramar[0])
  kontroll.notDeepEqual(kort.ramar[5], kort.ramar[11])
  const lang = retargetSpar([a, ...Array(11).fill(null), b, null, null])
  kontrolleraSpar(lang, 15)
  for (let i = 1; i <= 11; i++) {
    kontroll.deepEqual(lang.ramar[i], lang.ramar[0])
    kontroll.deepEqual(lang.bana[i], lang.bana[0])
  }
  for (const i of [13, 14]) {
    kontroll.deepEqual(lang.ramar[i], lang.ramar[12])
    kontroll.deepEqual(lang.bana[i], lang.bana[12])
  }
  nara(lang.bana[0][0], 0)
  nara(lang.bana[12][0], 2)
})

prova('tomma spår, inledande luckor och degenererade punkter ger ändliga poser', () => {
  kontroll.deepEqual(retargetSpar([]), { fps: 10, ramar: [], bana: [] })
  const tomt = retargetSpar(Array(8).fill(null))
  kontrolleraSpar(tomt, 8)
  kontroll.deepEqual(tomt.ramar[0], toQuats(NEUTRAL).map(q => q.toArray().map(v => Number(v.toFixed(4)))))
  kontroll.deepEqual(tomt.bana[0], [0, 0, 0, 0])
  const { ruta } = syntetisera({}, { x: 3 })
  const inledning = retargetSpar([null, null, ruta])
  kontroll.deepEqual(inledning.ramar[0], inledning.ramar[2])
  kontroll.deepEqual(inledning.bana[0], inledning.bana[2])
  const punkter = Array.from({ length: 33 }, () => [0, 1, 0])
  punkter[0] = [NaN, 0, 0]
  punkter[25] = [Infinity, 0, 0]
  punkter[28] = null
  const trasig = { punkter, synlighet: Array(33).fill(1) }
  const ut = retarget(trasig.punkter, trasig.synlighet)
  kontroll.ok(ut.quats.every(q => q.toArray().every(Number.isFinite)))
  kontroll.ok(ut.saknas.includes('left_shoulder'))
  kontroll.ok(ut.saknas.includes('neck'))
  kontrolleraSpar(retargetSpar([trasig, null, trasig]), 3)
})

prova('ansiktet använder ögon när öronen saknas, annars neutral nacke och huvud', () => {
  const { ruta, original } = syntetisera({ neck: [20, 10, 30] }, { rotation: [5, -25, 3] })
  ruta.synlighet[7] = ruta.synlighet[8] = 0
  const medOgon = retarget(ruta.punkter, ruta.synlighet)
  sammaRotation(framAt(medOgon.quats).globala[INDEX.head], original.globala[INDEX.head])
  kontroll.ok(!medOgon.saknas.includes('head'))
  ruta.synlighet[0] = 0
  const utanAnsikte = retarget(ruta.punkter, ruta.synlighet)
  for (const led of ['neck', 'head']) {
    sammaRotation(utanAnsikte.quats[INDEX[led]], toQuats(NEUTRAL)[INDEX[led]])
    kontroll.ok(utanAnsikte.saknas.includes(led))
  }
})

prova('min styr neutral reservpose per led och resultaten delar inte kvaternioner', () => {
  const { ruta } = syntetisera({ lArm: [155, 0, 0] })
  ruta.synlighet[13] = 0.5
  const synlig = retarget(ruta.punkter, ruta.synlighet)
  kontroll.ok(!synlig.saknas.includes('left_shoulder'))
  const dold = retarget(ruta.punkter, ruta.synlighet, { min: 0.6 })
  const neutral = toQuats(NEUTRAL)
  for (const led of ['left_shoulder', 'left_elbow']) {
    sammaRotation(dold.quats[INDEX[led]], neutral[INDEX[led]])
    kontroll.ok(dold.saknas.includes(led))
  }
  dold.quats[INDEX.left_shoulder].identity()
  sammaRotation(retarget(ruta.punkter, ruta.synlighet, { min: 0.6 }).quats[INDEX.left_shoulder], neutral[INDEX.left_shoulder])
})

prova('spegling: personens upplyfta vänsterarm styr bara dockans vänsterarm', () => {
  const bas = syntetisera().ruta
  const lyft = syntetisera({ lArm: [170, 0, 0], lElbow: 0 }).ruta
  const fore = retarget(bas.punkter, bas.synlighet)
  const efter = retarget(lyft.punkter, lyft.synlighet)
  kontroll.ok(fore.quats[INDEX.left_shoulder].angleTo(efter.quats[INDEX.left_shoulder]) * grader > 140)
  sammaRotation(fore.quats[INDEX.right_shoulder], efter.quats[INDEX.right_shoulder])
  const ater = framAt(efter.quats)
  kontroll.ok(riktning(ater, 'left_shoulder', 'left_elbow').y > 0.9)
  kontroll.ok(riktning(ater, 'right_shoulder', 'right_elbow').y < -0.9)
})
