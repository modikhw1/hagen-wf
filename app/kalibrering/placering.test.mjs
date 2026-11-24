// node --test kalibrering/placering.test.mjs
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { placeraScen, valjUttryck, olikhet, korrigera, giltigaEgenskaper } from './placering.mjs'
import { trana } from './modell.mjs'

const korr = { egenskaper: { kamera: { giltig: true, a: 0.01, b: 0.9 }, tilt: { giltig: true, a: 0, b: 1 }, pan: { giltig: false, a: 0, b: 1 } } }
const vertikal = { egenskaper: ['kamera', 'tilt', 'pan'], start: { kamera: 1, tilt: 0.5, pan: 1 } }

const VINK = [-20, 0, 20]
function scen() {
  const uttryck = [{ id: 'original', e: { kamera: 0.05, tilt: 0.02, pan: 0 }, giltig: true }]
  VINK.forEach((v, j) => { for (const u of ['total', 'halvbild', 'nara']) for (const kam of [0, 0.02, 0.04, 0.08, 0.12, 0.2]) {
    uttryck.push({ id: `${u}|${v}|0|static:0|${kam}`, e: { kamera: kam + j * 0.001, tilt: kam / 2, pan: 1 }, giltig: true })
  } })
  uttryck.push({ id: 'total|0|0|static:0|0.7', e: { kamera: 9, tilt: 9, pan: 9 }, giltig: false })
  return { uttryck }
}

test('bara egenskaper som bryggan godkänt används', () => {
  assert.deepEqual(giltigaEgenskaper(vertikal, korr), ['kamera', 'tilt'])
})

test('korrektionen översätter motorns tal till analysens skala', () => {
  const k = korrigera({ kamera: 0.1, tilt: 0.2 }, korr, ['kamera', 'tilt'])
  assert.ok(Math.abs(k.kamera - 0.1) < 1e-9)
  assert.equal(k.tilt, 0.2)
})

test('originalet hamnar på 5, ogiltiga uttryck tas bort, skalan går 1–10', () => {
  const namn = giltigaEgenskaper(vertikal, korr)
  const mod = trana({ items: scen().uttryck.map(x => ({ id: x.id, e: x.e })), bedomningar: [], namn, start: { kamera: 1, tilt: 0.5 } })
  const p = placeraScen(scen(), { mod, namn, korr })
  assert.equal(p.find(x => x.id === 'original').steg, 5)
  assert.ok(!p.some(x => x.id.endsWith('0.7') && x.e.kamera === 9))
  assert.equal(Math.min(...p.map(x => x.steg)), 1)
  assert.equal(Math.max(...p.map(x => x.steg)), 10)
})

test('reglaget: stanna inom trögheten, annars närmast målet med minst ryck', () => {
  const namn = ['kamera', 'tilt']
  const mod = trana({ items: scen().uttryck.map(x => ({ id: x.id, e: x.e })), bedomningar: [], namn, start: { kamera: 1, tilt: 0.5 } })
  const p = placeraScen(scen(), { mod, namn, korr })
  const stanna = valjUttryck({ mal: 5.5, nu: ['original'], placerade: [p], tolerans: 1 })
  assert.equal(stanna[0].beslut, 'stanna')
  const byt = valjUttryck({ mal: 10, nu: ['original'], placerade: [p], tolerans: 1 })
  assert.equal(byt[0].beslut, 'byt')
  assert.ok(Math.abs(p.find(x => x.id === byt[0].val).steg - 10) <= 2.5)
  assert.ok(byt[0].kandidater.length > 1)
})

test('olikhet: samma uttryck 0, ett annat utsnitt mindre än allt annat', () => {
  const a = { id: 'a', p: { utsnitt: 'total', vinkel: 0, hojd: 0, rorelse: 'static', mangd: 0, skak: 0 } }
  const b = { id: 'b', p: { ...a.p, utsnitt: 'nara' } }
  const c = { id: 'c', p: { utsnitt: 'nara', vinkel: 50, hojd: 22, rorelse: 'arc', mangd: 45, skak: 0.7 } }
  assert.equal(olikhet(a, a), 0)
  assert.ok(olikhet(a, b) < olikhet(a, c))
})

import { malProfil, valjKedja } from './placering.mjs'

test('kedjans mål: originalets profil på 5, platt på 1 och 10', () => {
  const p = [4, 6, 7, 5, 3]
  assert.deepEqual(malProfil(p, 5), p)
  assert.ok(malProfil(p, 10).every(v => Math.abs(v - 10) < 1e-9))
  assert.ok(malProfil(p, 1).every(v => Math.abs(v - 1) < 1e-9))
  const m7 = malProfil(p, 7)
  assert.ok(m7[2] > m7[4], 'formen ska finnas kvar nära originalet')
})

function kedja() {
  // tre scener, varje med original (steg varierar) och uttryck på alla steg i två sätt att filma
  return [4, 6, 5].map(o => {
    const l = [{ id: 'original', steg: o, p: null }]
    for (let s = 1; s <= 10; s += 0.5) for (const u of ['total', 'nara']) {
      l.push({ id: `${u}|0|0|static:0|${s}`, steg: s, p: { utsnitt: u, vinkel: 0, hojd: 0, rorelse: 'static', mangd: 0, skak: 0 } })
    }
    return l
  })
}

test('kedjan: på originalets nivå stannar allt, högt mål byter och når målet', () => {
  const listor = kedja()
  const nu = ['original', 'original', 'original']
  assert.ok(valjKedja({ mal: 5, nu, listor }).every(x => x.beslut === 'stanna'))
  const hog = valjKedja({ mal: 10, nu, listor })
  assert.ok(hog.every(x => x.beslut === 'byt'))
  hog.forEach((x, i) => assert.ok(Math.abs(listor[i].find(y => y.id === x.val).steg - x.mal) <= 1))
})

test('kedjan: lågt mål ger enhetliga grannar, högt mål variation', () => {
  const listor = kedja()
  const nu = ['original', 'original', 'original']
  const utsnitt = r => r.map((x, i) => listor[i].find(y => y.id === x.val).p?.utsnitt)
  const lag = utsnitt(valjKedja({ mal: 2, nu, listor, vikt: { trog: 0, granne: 3 } }))
  const hog = utsnitt(valjKedja({ mal: 9, nu, listor, vikt: { trog: 0, granne: 3 } }))
  assert.equal(new Set(lag).size, 1)
  assert.ok(new Set(hog).size > 1)
})

test('kedjan: skyddsräcken väljs aldrig bort', () => {
  const listor = kedja()
  const r = valjKedja({ mal: 9, nu: ['original', 'original', 'original'], listor, tillat: (i, x) => x.p?.utsnitt !== 'nara' })
  r.forEach((x, i) => assert.notEqual(listor[i].find(y => y.id === x.val).p?.utsnitt, 'nara'))
})

test('kedjan: tillbaka till 5 efter en omväg ger originalen', () => {
  const listor = kedja()
  let nu = ['original', 'original', 'original']
  for (const m of [9, 1, 5]) nu = valjKedja({ mal: m, nu, listor }).map(x => x.val)
  assert.deepEqual(nu, ['original', 'original', 'original'])
})

test('kedjan: på 5 vinner originalet även när nuvarande ligger inom trögheten', () => {
  const listor = kedja()
  // nuvarande: ett uttryck nära originalets steg (inom toleransen), inte originalet
  const nu = listor.map(l => l.find(x => x.id !== 'original' && Math.abs(x.steg - l[0].steg) <= 0.5).id)
  assert.deepEqual(valjKedja({ mal: 5, nu, listor }).map(x => x.val), ['original', 'original', 'original'])
})
