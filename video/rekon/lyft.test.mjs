import { test as prova } from 'node:test'
import kontroll from 'node:assert/strict'
import { readFile as lasFil } from 'node:fs/promises'
import { PerspectiveCamera as Perspektivkamera } from 'three/src/cameras/PerspectiveCamera.js'
import { Vector3 as Vektor } from 'three/src/math/Vector3.js'
import { ASPEKT, F, FOV_V, kamQuat } from './geometri.mjs'
import { lyftScen } from './lyft.mjs'

const kamera = { pos: [0, 1.4, 0], q: kamQuat(0, -10, 0).toArray() }
const rakKamera = { pos: [0, 1.45, 0], q: kamQuat(0, 0, 0).toArray() }
const nara = (verkligt, vantat, tolerans = 1e-8) => {
  kontroll.ok(Math.abs(verkligt - vantat) <= tolerans, `${verkligt} ska vara nära ${vantat} (±${tolerans})`)
}
const scen = (element, avstand = 4) => ({
  golv: { farg: '#888888', material: 'betong', synligt: true },
  vagg: { farg: '#eeeeee', material: 'puts', avstand },
  element,
})
const foremal = (andringar = {}) => ({
  namn: 'låda',
  kategori: 'ovrigt',
  ruta: [400, 300, 700, 700],
  form: 'lada',
  farg: '#aa8866',
  material: 'tra',
  lyser: false,
  placering: 'golv',
  storlek: [1, 1, 0.6],
  framfor_personer: false,
  ...andringar,
})

// Projicera samtliga åtta hörn med Three.js kamera, oberoende av lyftets strålberäkning.
function projiceraRuta(pos, storlek, kam = kamera, gir = 0) {
  const bildkamera = new Perspektivkamera(FOV_V, ASPEKT, 0.01, 100)
  bildkamera.position.fromArray(kam.pos)
  bildkamera.quaternion.fromArray(kam.q)
  bildkamera.updateMatrixWorld(true)
  const punkter = []
  for (const x of [-0.5, 0.5]) {
    for (const y of [-0.5, 0.5]) {
      for (const z of [-0.5, 0.5]) {
        const p = new Vektor(x * storlek[0], y * storlek[1], z * storlek[2])
          .applyQuaternion(kamQuat(gir, 0, 0)).add(new Vektor(...pos)).project(bildkamera)
        punkter.push([(p.x + 1) * 500, (1 - p.y) * 500])
      }
    }
  }
  return [
    Math.min(...punkter.map(p => p[1])),
    Math.min(...punkter.map(p => p[0])),
    Math.max(...punkter.map(p => p[1])),
    Math.max(...punkter.map(p => p[0])),
  ]
}

function golvlada() {
  return foremal({ ruta: projiceraRuta([0, 0.5, -2.3], [1, 1, 0.6]) })
}

function rimligt(resultat) {
  kontroll.ok(Number.isFinite(resultat.vagg.z))
  for (const e of resultat.element) {
    kontroll.equal(e.pos.length, 3)
    kontroll.equal(e.storlek.length, 3)
    kontroll.ok(e.pos.every(Number.isFinite), `${e.namn}: ändlig position`)
    kontroll.ok(Number.isFinite(e.rotY), `${e.namn}: ändlig vridning`)
    kontroll.ok(e.storlek.every(matt => Number.isFinite(matt) && matt >= 0.02 && matt <= 12), `${e.namn}: rimliga mått`)
    kontroll.ok(e.pos[2] > resultat.vagg.z, `${e.namn}: mittpunkten framför väggen`)
    const halvDjup = e.form === 'platta' ? 0 : e.storlek[2] / 2
    kontroll.ok(e.pos[2] - halvDjup >= resultat.vagg.z - 1e-8, `${e.namn}: hela kroppen framför väggen`)
  }
  kontroll.ok(resultat.antaget.every(rad => typeof rad === 'string'))
}

prova('golvlådans läge och mått återvinns inom fem procent med lutad kamera', () => {
  const ut = lyftScen(scen([golvlada()]), kamera)
  const e = ut.element[0]
  nara(e.pos[0], 0)
  nara(e.pos[1], 0.5, 0.5 * 0.05)
  nara(e.pos[2], -2.3, 2.3 * 0.05)
  for (const [i, vantat] of [1, 1, 0.6].entries()) nara(e.storlek[i], vantat, vantat * 0.05)
  nara(e.pos[1] - e.storlek[1] / 2, 0)
  nara(e.pos[2] + e.storlek[2] / 2, -2)
  rimligt(ut)
})

prova('flaskan lyfts efter sitt underlag även om den står först i indatan', () => {
  const flaska = foremal({
    namn: 'flaska',
    kategori: 'flaska',
    form: 'cylinder',
    placering: 'pa_element',
    pa: 1,
    storlek: [0.12, 0.3, 0.12],
    ruta: projiceraRuta([0, 1.15, -2.3], [0.12, 0.3, 0.12]),
  })
  const ut = lyftScen(scen([flaska, golvlada()]), kamera)
  const [lyftFlaska, lada] = ut.element
  kontroll.equal(lyftFlaska.namn, 'flaska')
  kontroll.equal(lyftFlaska.coco, 'bottle')
  nara(lyftFlaska.pos[1] - lyftFlaska.storlek[1] / 2, lada.pos[1] + lada.storlek[1] / 2, 0.02)
  rimligt(ut)
})

prova('väggskylten hamnar tre centimeter framför väggen på rätt höjd', () => {
  const skylt = foremal({
    namn: 'lysande skylt',
    kategori: 'skylt',
    form: 'cylinder',
    placering: 'vagg',
    storlek: [1, 0.5, 0.2],
    ruta: projiceraRuta([0.25, 2.1, -4], [1, 0.5, 0], rakKamera),
    lyser: true,
  })
  const ut = lyftScen(scen([skylt]), rakKamera)
  const e = ut.element[0]
  nara(ut.vagg.z, -4)
  nara(e.pos[0], 0.25)
  nara(e.pos[1], 2.1)
  nara(e.pos[2], -4 + 0.03)
  nara(e.storlek[0], 1)
  nara(e.storlek[1], 0.5)
  kontroll.ok(e.storlek[2] <= 0.05)
  kontroll.equal(e.form, 'platta')
  kontroll.equal(e.rotY, 0)
  kontroll.equal(e.lyser, true)
  kontroll.equal(e.farg, skylt.farg)
  kontroll.equal(e.material, skylt.material)
  kontroll.ok(!Object.hasOwn(e, 'coco'))
  kontroll.equal(lyftScen(scen([{ ...skylt, form: 'lada' }]), rakKamera).element[0].form, 'lada')
  rimligt(ut)
})

prova('avskuren nederkant använder storleken och ger ett rimligt djup', () => {
  const e = foremal({ ruta: [700, 250, 1000, 750] })
  const ut = lyftScen(scen([e], 10), rakKamera)
  const lyft = ut.element[0]
  nara(lyft.storlek[1], 1)
  nara(lyft.pos[2], -(F / 0.3 + 0.6 / 2))
  nara(lyft.pos[1], 0.5)
  kontroll.ok(ut.antaget.some(rad => rad.includes('djup ur storleken')))
  kontroll.ok(-lyft.pos[2] >= 0.3 && -lyft.pos[2] <= 15)
  rimligt(ut)
})

prova('alla scener i exempeldata har ändliga lägen, rimliga mått och föremål framför väggen', async () => {
  const fil = new URL('../../data/rekon/b.b.kebab-1779386335747/lokal-2d.json', import.meta.url)
  const data = JSON.parse(await lasFil(fil, 'utf8'))
  kontroll.ok(data.scener.length > 0)
  for (const sc of data.scener) {
    const fore = structuredClone(sc)
    const ut = lyftScen(sc, rakKamera)
    kontroll.equal(ut.element.length, sc.element.length)
    kontroll.deepEqual(ut.golv, { farg: sc.golv.farg, material: sc.golv.material })
    kontroll.equal(ut.vagg.farg, sc.vagg.farg)
    kontroll.equal(ut.vagg.material, sc.vagg.material)
    kontroll.deepEqual(sc, fore, 'indatan ska inte ändras')
    rimligt(ut)
  }
})

prova('okända beroenden, självberoenden och hela cykler behandlas som fritt', () => {
  const element = [
    foremal({ namn: 'okänt', placering: 'pa_element', pa: 99 }),
    foremal({ namn: 'själv', placering: 'pa_element', pa: 1 }),
    foremal({ namn: 'cykel ett', placering: 'pa_element', pa: 3 }),
    foremal({ namn: 'cykel två', placering: 'pa_element', pa: 4 }),
    foremal({ namn: 'cykel tre', placering: 'pa_element', pa: 2 }),
  ]
  const ut = lyftScen(scen(element), rakKamera)
  const fritt = lyftScen(scen(element.map(e => ({ ...e, placering: 'fritt' }))), rakKamera)
  kontroll.deepEqual(ut.element, fritt.element)
  kontroll.equal(ut.antaget.filter(rad => rad.includes('cykliskt pa')).length, element.length)
  rimligt(ut)
})

prova('väggen läggs bakom den djupaste personen men aldrig längre bort än femton meter', () => {
  nara(lyftScen(scen([]), rakKamera, { personer: [{ djup: 2 }, { djup: 6 }] }).vagg.z, -6.8)
  nara(lyftScen(scen([], 30), rakKamera, { personer: [{ djup: 20 }] }).vagg.z, -15)
  nara(lyftScen(scen([], 8), rakKamera).vagg.z, -8)
})

prova('gir och förskjuten kamera ger rätt väggplan och orientering för plattor', () => {
  const kam = { pos: [2, 1.45, 3], q: kamQuat(30, 0, 0).toArray() }
  const framat = new Vektor(0, 0, -1).applyQuaternion(kamQuat(30, 0, 0))
  const vaggmitt = new Vektor(...kam.pos).addScaledVector(framat, 4)
  const skylt = foremal({
    placering: 'vagg',
    form: 'platta',
    ruta: projiceraRuta(vaggmitt.toArray(), [1, 0.5, 0], kam, 30),
    storlek: [1, 0.5, 0.02],
  })
  const ut = lyftScen(scen([skylt]), kam)
  const vantat = new Vektor(...kam.pos).addScaledVector(framat, 3.97)
  nara(ut.vagg.z, vaggmitt.z)
  ut.element[0].pos.forEach((tal, i) => nara(tal, vantat.toArray()[i]))
  nara(ut.element[0].rotY, 30)
  kontroll.ok(ut.antaget.some(rad => rad.includes('gir')))
})

prova('uppåtriktad golvstråle får djup ur storleken och sidoklippning bevarar angiven bredd', () => {
  const e = foremal({ ruta: [100, 0, 300, 400], storlek: [3, 0.5, 0.2] })
  const ut = lyftScen(scen([e]), rakKamera)
  nara(ut.element[0].storlek[0], 3)
  nara(ut.element[0].pos[1], 0.25)
  kontroll.ok(ut.antaget.some(rad => rad.includes('djup ur storleken')))
  rimligt(ut)
})

prova('tak, fritt och okänd placering använder bildstrålen och storleksdjupet', () => {
  for (const placering of ['tak', 'fritt', 'annat']) {
    const e = foremal({ placering, ruta: [250, 550, 350, 650], storlek: [0.2, 0.4, 0.2] })
    const ut = lyftScen(scen([e], 10), rakKamera)
    const djup = F * 0.4 / 0.1
    nara(ut.element[0].pos[0], 0.1 * ASPEKT * djup / F)
    nara(ut.element[0].pos[1], 1.45 + 0.2 * djup / F)
    nara(ut.element[0].pos[2], -djup)
    rimligt(ut)
  }
})

prova('mått och avstånd begränsas även för försvinnande små rutor', () => {
  const element = [
    foremal({ placering: 'fritt', ruta: [0, 0, 1000, 1000], storlek: [100, 100, 100] }),
    foremal({ placering: 'fritt', ruta: [500, 500, 500, 500], storlek: [0, 0, 0] }),
    foremal({ placering: 'fritt', ruta: [450, 450, 550, 550], storlek: [0, 0, 0] }),
  ]
  const ut = lyftScen(scen(element, 15), rakKamera)
  kontroll.deepEqual(ut.element[0].storlek, [12, 12, 12])
  kontroll.deepEqual(ut.element[1].storlek, [0.02, 0.02, 0.02])
  nara(-ut.element[2].pos[2], 0.3)
  kontroll.ok(ut.element.every(e => -e.pos[2] >= 0.3 && -e.pos[2] <= 15))
  rimligt(ut)
})

prova('kategorier ger rätt COCO-namn och disk eller förgrund markeras som skymmande', () => {
  const kategorier = ['disk', 'bord', 'stol', 'flaska', 'skarm', 'vaxt', 'ovrigt']
  const namn = ['dining table', 'dining table', 'chair', 'bottle', 'tv', 'potted plant', undefined]
  const ut = lyftScen(scen(kategorier.map(kategori => foremal({ kategori, placering: 'fritt' }))), rakKamera)
  ut.element.forEach((e, i) => {
    kontroll.equal(e.coco, namn[i])
    kontroll.equal(e.skymmer, i === 0)
  })
  kontroll.ok(!Object.hasOwn(ut.element.at(-1), 'coco'))
  kontroll.equal(lyftScen(scen([foremal({ framfor_personer: true })]), rakKamera).element[0].skymmer, true)
})
