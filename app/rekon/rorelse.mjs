import * as THREE from 'three'
import { JOINTS, PARENT, OFFSET, INDEX } from '../src/forandring/motor/skelett.js'
import { NEUTRAL, toQuats } from '../src/forandring/motor/pose.js'

// Höjd på bäckenet när benen inte syns (bakom en disk): geometrin får bestämma inom rimliga gränser.
// Golvet syns ändå inte, och en låst höjd flyttade hela kroppen några cm fel i bild.
export const LYFT = [-0.35, 0.3]

const neutrala = toQuats(NEUTRAL)
const sittande = toQuats({ ...NEUTRAL, lLeg: [85, 5], rLeg: [85, 5], lKnee: 90, rKnee: 90 })
const upp = new THREE.Vector3(0, 1, 0)
const liten = 1e-12
const begransa = (v, a, b) => Math.max(a, Math.min(b, v))
const giltig = p => p?.length >= 3 && [p[0], p[1], p[2]].every(Number.isFinite)
const vikt = v => Number.isFinite(v) ? begransa(v, 0, 1) : 0
const mitt = (a, b) => a.clone().add(b).multiplyScalar(0.5)

// Led, barnets viloförskjutning, startpunkt och slutpunkt(er).
// Handleden saknar barn: dess fortsättning har samma viloaxel som underarmen.
const lemmar = [
  ['left_shoulder', 'left_elbow', 11, [13]],
  ['right_shoulder', 'right_elbow', 12, [14]],
  ['left_elbow', 'left_wrist', 13, [15]],
  ['right_elbow', 'right_wrist', 14, [16]],
  ['left_wrist', 'left_wrist', 15, [17, 19]],
  ['right_wrist', 'right_wrist', 16, [18, 20]],
  ['left_hip', 'left_knee', 23, [25]],
  ['right_hip', 'right_knee', 24, [26]],
  ['left_knee', 'left_ankle', 25, [27]],
  ['right_knee', 'right_ankle', 26, [28]],
  ['left_ankle', 'left_foot', 27, [31]],
  ['right_ankle', 'right_foot', 28, [32]],
]
const lemPerLed = new Map(lemmar.map(([led, ...mal]) => [led, mal]))
const benleder = lemmar.filter(([, , start]) => start >= 23).map(([led]) => led)

function orientering(vanster, uppat) {
  if (vanster.lengthSq() < liten) return null
  const x = vanster.clone().normalize()
  const y = uppat.clone().addScaledVector(x, -uppat.dot(x))
  if (y.lengthSq() < liten) return null
  y.normalize()
  const z = new THREE.Vector3().crossVectors(x, y).normalize()
  return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z)).normalize()
}

// Punkterna är redan i dockans värld: +X är personens vänster, +Y upp, +Z fram.
export function retarget(punkter, synlighet, { skala = 1, min = 0.5 } = {}) {
  if (!Number.isFinite(skala) || skala <= 0) throw new RangeError('skala måste vara positiv och ändlig')
  if (!Number.isFinite(min) || min < 0 || min > 1) throw new RangeError('min måste ligga mellan 0 och 1')
  const punkter3 = Array.from({ length: 33 }, (_, i) => giltig(punkter?.[i]) ? new THREE.Vector3(...punkter[i]) : null)
  const syns = i => punkter3[i] !== null && Number.isFinite(synlighet?.[i]) && synlighet[i] >= min
  const synsAlla = lista => lista.every(syns)
  const quats = neutrala.map(q => q.clone())
  const saknas = new Set()
  const markera = (...leder) => leder.forEach(led => saknas.add(led))
  const hoftmitt = punkter3[23] && punkter3[24] ? mitt(punkter3[23], punkter3[24]) : null
  const axelmitt = punkter3[11] && punkter3[12] ? mitt(punkter3[11], punkter3[12]) : null
  const balSyns = synsAlla([11, 12, 23, 24])
  const balUpp = balSyns ? axelmitt.clone().sub(hoftmitt) : null

  let backen = balSyns ? orientering(punkter3[23].clone().sub(punkter3[24]), balUpp) : null
  if (!synsAlla([23, 24]) && synsAlla([11, 12])) {
    const vanster = punkter3[11].clone().sub(punkter3[12])
    vanster.y = 0
    backen = orientering(vanster, upp)
    markera('pelvis') // Orienteringen är uppskattad från axlarna.
  }
  if (backen) quats[INDEX.pelvis].copy(backen)
  else markera('pelvis')

  const brost = balSyns ? orientering(punkter3[11].clone().sub(punkter3[12]), balUpp) : null
  if (brost) {
    const relativ = quats[INDEX.pelvis].clone().invert().multiply(brost)
    const del = new THREE.Quaternion().slerp(relativ, 1 / 3)
    for (const led of ['spine1', 'spine2', 'spine3']) quats[INDEX[led]].copy(del)
  } else markera('spine1', 'spine2', 'spine3')
  const brostGlobal = quats[INDEX.pelvis].clone()
  for (const led of ['spine1', 'spine2', 'spine3']) brostGlobal.multiply(quats[INDEX[led]])

  let huvud = null
  for (const [a, b] of [[7, 8], [2, 5]]) {
    if (!synsAlla([0, a, b])) continue
    const vanster = punkter3[a].clone().sub(punkter3[b])
    const fram = punkter3[0].clone().sub(mitt(punkter3[a], punkter3[b]))
    // Fram × vänster ger uppåt i detta högerhänta koordinatsystem.
    huvud = orientering(vanster, new THREE.Vector3().crossVectors(fram, vanster))
    if (huvud) break
  }
  if (huvud) {
    const relativ = brostGlobal.clone().invert().multiply(huvud)
    const del = new THREE.Quaternion().slerp(relativ, 0.5)
    for (const led of ['neck', 'head']) quats[INDEX[led]].copy(del)
  } else markera('neck', 'head')

  const globala = []
  for (const [i, led] of JOINTS.entries()) {
    const foralder = PARENT[i] < 0 ? new THREE.Quaternion() : globala[PARENT[i]]
    const lem = lemPerLed.get(led)
    if (lem) {
      const [barn, start, slut] = lem
      let mal = null
      if (synsAlla([start, ...slut])) {
        mal = slut.reduce((summa, k) => summa.add(punkter3[k]), new THREE.Vector3())
          .multiplyScalar(1 / slut.length).sub(punkter3[start])
      }
      if (mal && mal.lengthSq() >= liten) {
        const vila = new THREE.Vector3(...OFFSET[barn]).normalize().applyQuaternion(foralder)
        const global = new THREE.Quaternion().setFromUnitVectors(vila, mal.normalize()).multiply(foralder)
        quats[i].copy(foralder).invert().multiply(global).normalize()
      } else markera(led)
    }
    // Fotens egen vridning kan inte bestämmas av en enda fottopp, så den är neutral.
    if (led === 'left_foot' && !synsAlla([27, 31])) markera(led)
    if (led === 'right_foot' && !synsAlla([28, 32])) markera(led)
    globala[i] = foralder.clone().multiply(quats[i]).normalize()
  }

  // Även dolda höfter kan ha en användbar positionsskattning från MediaPipe.
  // Utan sådana koordinater placeras ett upprätt bäcken under axlarna.
  const mal = hoftmitt ?? (axelmitt
    ? axelmitt.clone().add(new THREE.Vector3(0, -0.45 * skala, 0.03 * skala))
    : new THREE.Vector3(0, OFFSET.pelvis[1] * skala, 0))
  let lift = mal.y - OFFSET.pelvis[1] * skala
  if (benleder.some(led => saknas.has(led))) {
    if (lift < -0.25) {
      for (const led of ['left_hip', 'right_hip', 'left_knee', 'right_knee']) {
        quats[INDEX[led]].copy(sittande[INDEX[led]])
      }
    } else lift = begransa(lift, ...LYFT)
  }
  return { quats, x: mal.x, z: mal.z, lift, saknas: JOINTS.filter(led => saknas.has(led)) }
}

function interpolera(a, b, andel) {
  const synlighet = []
  const punkter = Array.from({ length: 33 }, (_, i) => {
    const pa = a.punkter?.[i], pb = b.punkter?.[i]
    if (!giltig(pa) || !giltig(pb)) {
      synlighet[i] = 0
      return giltig(pa) ? pa.slice() : giltig(pb) ? pb.slice() : null
    }
    synlighet[i] = vikt(a.synlighet?.[i]) * (1 - andel) + vikt(b.synlighet?.[i]) * andel
    return pa.map((v, k) => v + (pb[k] - v) * andel)
  })
  return { punkter, synlighet }
}

// Endast inre luckor med två ändpunkter interpoleras. Övriga hålls senare
// som färdiga poser, så filtren inte drar in nästa rörelse i en lång lucka.
function fyllLuckor(rutor) {
  const fyllda = rutor.slice()
  let i = 0
  while (i < rutor.length) {
    if (rutor[i] != null) {
      i++
      continue
    }
    const start = i
    while (i < rutor.length && rutor[i] == null) i++
    if (start === 0 || i === rutor.length || i - start > 10) continue
    for (let k = start; k < i; k++) fyllda[k] = interpolera(rutor[start - 1], rutor[i], (k - start + 1) / (i - start + 1))
  }
  return fyllda
}

function jamnaPunkter(rutor, i, start, slut) {
  const synlighet = []
  const punkter = Array.from({ length: 33 }, (_, p) => {
    const summa = new THREE.Vector3()
    let total = 0, fonster = 0
    for (let k = Math.max(start, i - 2); k < Math.min(slut, i + 3); k++) {
      const tyngd = 3 - Math.abs(k - i)
      const punkt = rutor[k].punkter?.[p]
      const v = giltig(punkt) ? vikt(rutor[k].synlighet?.[p]) * tyngd : 0
      fonster += tyngd
      if (v === 0) continue
      summa.addScaledVector(new THREE.Vector3(...punkt), v)
      total += v
    }
    synlighet[p] = total / fonster
    if (total > 0) return summa.divideScalar(total).toArray()
    const punkt = rutor[i].punkter?.[p]
    return giltig(punkt) ? punkt.slice() : null
  })
  return { punkter, synlighet }
}

export function retargetSpar(rutor, { fps = 10, skala = 1 } = {}) {
  if (!Number.isFinite(fps) || fps <= 0) throw new RangeError('fps måste vara positiv och ändlig')
  const tom = retarget([], [], { skala })
  const fyllda = fyllLuckor(rutor)
  const poser = Array(rutor.length).fill(null)
  const banor = Array(rutor.length).fill(null)
  let i = 0
  while (i < fyllda.length) {
    if (fyllda[i] == null) {
      i++
      continue
    }
    const start = i
    while (i < fyllda.length && fyllda[i] != null) i++
    const slut = i
    for (let k = start; k < slut; k++) {
      const ruta = jamnaPunkter(fyllda, k, start, slut)
      poser[k] = retarget(ruta.punkter, ruta.synlighet, { skala })
    }
    for (let k = start; k < slut; k++) {
      const summa = [0, 0, 0, 0]
      let total = 0
      for (let j = Math.max(start, k - 4); j < Math.min(slut, k + 5); j++) {
        const tyngd = 5 - Math.abs(j - k)
        const pose = poser[j]
        summa[0] += pose.x * tyngd
        summa[1] += pose.z * tyngd
        summa[3] += pose.lift * tyngd
        total += tyngd
      }
      banor[k] = summa.map(v => v / total)
    }
  }

  // I början saknas en föregående pose: använd den första kända, annars neutral.
  const forsta = poser.findIndex(p => p !== null)
  let senaste = forsta < 0 ? tom : poser[forsta]
  let senasteBana = forsta < 0 ? [0, 0, 0, 0] : banor[forsta]
  let foregaende = null
  const bana = []
  const ramar = poser.map((pose, k) => {
    if (pose) {
      senaste = pose
      senasteBana = banor[k]
    }
    bana.push(senasteBana.slice())
    const aktuella = senaste.quats.map((q, j) => {
      const kopia = q.clone().normalize()
      // q och -q är samma rotation. Behåll tecknet kontinuerligt mellan rutor.
      if (foregaende && kopia.dot(foregaende[j]) < 0) kopia.set(-kopia.x, -kopia.y, -kopia.z, -kopia.w)
      return kopia
    })
    foregaende = aktuella
    return aktuella.map(q => q.toArray().map(v => Number(v.toFixed(4)) || 0))
  })
  return { fps, ramar, bana }
}
