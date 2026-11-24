// node --test kalibrering/forklaring.test.mjs
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { forklara, SPAKAR } from './forklaring.mjs'
import { trana, nytta } from './modell.mjs'
import { korrigera } from './placering.mjs'
import { parseId } from '../src/forandring/manus/uttryck.js'

function modell(start, skalor = {}) {
  const namn = Object.keys(start)
  const items = [-1, 1].map(v => ({
    id: String(v),
    e: Object.fromEntries(namn.map(n => [n, v * (skalor[n] ?? 1)])),
  }))
  return trana({ items, bedomningar: [], namn, start })
}

const korr = { egenskaper: {} }
const grund = modell({ kamera: 1, motiv: 1 })
const fore = {
  e: { kamera: 0, motiv: 0 },
  p: parseId('halvbild|0|0|static:0|0'),
  amp: 1,
  steg: 5,
}
const forklaring = (efter, fran = fore, mod = grund) => forklara({ mod, korr, fore: fran, efter: { ...fran, ...efter } })
const nara = (a, b) => assert.ok(Math.abs(a - b) < 1e-6, `${a} ska vara nära ${b}`)

test('korrigerade bidrag följer modellens ordning och summerar till stegskillnaden', () => {
  const mod = modell(
    { energi: 0.5, kamera: 2, egen: 1, pan: -1, motiv: 3, dynamik: 0.25 },
    { energi: 10, kamera: 2, pan: 4, motiv: 3 },
  )
  const korrektion = { egenskaper: {
    kamera: { giltig: true, a: 4, b: 2 },
    motiv: { giltig: true, a: -3, b: 0.5 },
    pan: { giltig: false, a: 50, b: 100 },
  } }
  const fran = { ...fore, e: {}, steg: 2 }
  const efter = {
    ...fore,
    e: { kamera: 2, pan: 4, motiv: 3, energi: 20, dynamik: 4, egen: 1, utanfor: 999999 },
    steg: 5.75,
  }
  const svar = forklara({ mod, korr: korrektion, fore: fran, efter })
  nara(svar.nytta, 7.5)
  nara(svar.nytta, nytta(mod, korrigera(efter.e, korrektion, mod.namn)) - nytta(mod, korrigera(fran.e, korrektion, mod.namn)))
  nara(svar.spakar.reduce((summa, x) => summa + x.bidrag, 0), svar.steg)
  nara(svar.spakar.reduce((summa, x) => summa + x.andel, 0), 1)
  const vantat = { energi: 0.5, kamera: 2, egen: 0.5, pan: -0.5, motiv: 0.75, dynamik: 0.5 }
  for (const spak of svar.spakar) {
    nara(spak.egenskaper.reduce((summa, x) => summa + x.bidrag, 0), spak.bidrag)
    for (const x of spak.egenskaper) nara(x.bidrag, vantat[x.namn])
  }
  assert.equal(svar.spakar.flatMap(x => x.egenskaper).length, 6)
  assert.equal(svar.spakar[0].spak, 'kamera')
  assert.ok(svar.spakar.every((x, i, lista) => i === 0 || Math.abs(lista[i - 1].bidrag) >= Math.abs(x.bidrag)))
  assert.deepEqual(svar.spakar.find(x => x.spak === 'ovrigt').egenskaper, [{ namn: 'egen', bidrag: 0.5 }])
  for (const namn of ['kameran', 'agerandet', 'bilden', 'rytmen', 'övrigt']) assert.ok(svar.text.includes(namn))
})

test('bara ändrade kameraegenskaper ger bara kamerans spak', () => {
  const mod = modell({ ...Object.fromEntries(SPAKAR.kamera.map(n => [n, 1])), motiv: 1, energi: 1 })
  const e = Object.fromEntries(SPAKAR.kamera.map(n => [n, 1]))
  const svar = forklaring({ e, steg: 6.8 }, fore, mod)
  assert.deepEqual(svar.spakar.map(x => x.spak), ['kamera'])
  assert.deepEqual(svar.spakar[0].egenskaper.map(x => x.namn), SPAKAR.kamera)
  nara(svar.spakar[0].bidrag, 1.8)
  nara(svar.spakar[0].andel, 1)
})

test('ändrat motiv och förstärkning förklaras som agerande', () => {
  const svar = forklaring({ e: { kamera: 0, motiv: 1 }, amp: 1.25, steg: 5.5 })
  assert.deepEqual(svar.spakar.map(x => x.spak), ['agerande'])
  nara(svar.spakar[0].bidrag, 0.5)
  assert.match(svar.text, /agerandet \+0,5 \(rörelserna 25 % större/)
  assert.equal(svar.andringar.length, 1)
  assert.ok(!svar.text.includes('kameran'))
})

test('originalets kamera kan bytas till närbild med båge och mängd', () => {
  const p = parseId('nara|20|0|arc:20|0')
  const svar = forklaring({ e: { kamera: 1 }, p, steg: 6.8 }, { ...fore, p: null })
  assert.ok(svar.andringar.some(x => x.includes('närbild')))
  assert.ok(svar.andringar.some(x => x.includes('båge 20°')))
  assert.ok(svar.andringar.includes('från höger 20°'))
  assert.match(svar.text, /kameran \+1,8 \(närbild i stället för originalets kamera,.*båge 20°\)/)
})

test('kameran beskriver bara ändrade utsnitt, vinklar, höjder och skak', () => {
  const p = { ...fore.p, utsnitt: 'total', vinkel: -35, hojd: 10, skak: 0.7 }
  const svar = forklaring({ p })
  assert.deepEqual(svar.andringar, ['helbild i stället för halvbild', 'från vänster 35°', '10° högre', 'handhållen'])
  const tillbaka = forklaring({ p: fore.p }, { ...fore, p })
  assert.deepEqual(tillbaka.andringar, ['halvbild i stället för helbild', 'rakt framifrån', '10° lägre', 'lugnare hand'])
  assert.deepEqual(forklaring({ p: { ...fore.p } }).andringar, [])
})

test('alla utsnitt beskrivs på svenska och originalets kamera kan återställas', () => {
  for (const [utsnitt, namn] of Object.entries({ total: 'helbild', halvtotal: 'halvtotal', halvbild: 'halvbild', nara: 'närbild', extrem: 'extrem närbild' })) {
    const svar = forklaring({ p: { ...fore.p, utsnitt } }, { ...fore, p: null })
    assert.ok(svar.andringar.includes(`${namn} i stället för originalets kamera`))
  }
  assert.deepEqual(forklaring({ p: null }).andringar, ['originalets kamera'])
  assert.deepEqual(forklaring({ p: null }, { ...fore, p: null }).andringar, [])
})

test('kamerarörelser beskrivs med mängd och rätt enhet', () => {
  const fall = [
    ['dolly', 0.2, 'kameran åker in 0,2 m'],
    ['pan', 12, 'kameran panorerar 12°'],
    ['truck', 0.15, 'kameran glider i sidled 0,15 m'],
    ['arc', 20, 'kameran går i en båge 20°'],
    ['zoom', 0.2, 'kameran zoomar 20 %'],
    ['tilt', 8, 'kameran tiltar 8°'],
    ['pedestal', 0.35, 'kameran höjs 0,35 m'],
  ]
  for (const [rorelse, mangd, text] of fall) {
    const p = { ...fore.p, rorelse, mangd }
    assert.deepEqual(forklaring({ p }).andringar, [text])
    assert.deepEqual(forklaring({ p: fore.p }, { ...fore, p }).andringar, ['stillastående kamera'])
  }
})

test('ändrad mängd tas med även när rörelsetypen är densamma', () => {
  const fran = { ...fore, p: { ...fore.p, rorelse: 'arc', mangd: 20 } }
  assert.deepEqual(forklaring({ p: { ...fran.p, mangd: 45 } }, fran).andringar, ['kameran går i en båge 45°'])
  assert.deepEqual(forklaring({ p: { ...fran.p } }, fran).andringar, [])
  assert.deepEqual(forklaring({ p: { ...fore.p, mangd: 20 } }).andringar, [])
})

test('förstärkning beskriver mindre rörelser och återgång till originalet', () => {
  assert.deepEqual(forklaring({ amp: 0.75 }).andringar, ['rörelserna 25 % mindre än i originalet'])
  assert.deepEqual(forklaring({ amp: 1 }, { ...fore, amp: 1.25 }).andringar, ['agerandet som i originalet'])
  assert.deepEqual(forklaring({ amp: 1.25 }, { ...fore, amp: 1.25 }).andringar, [])
  assert.deepEqual(forklaring({ amp: 1.25 }, { ...fore, amp: 1.5 }).andringar, ['rörelserna 25 % större än i originalet'])
})

test('kamera och agerande får var sin parentes med rätt ändringar', () => {
  const svar = forklaring({ e: { kamera: 2, motiv: 1 }, p: { ...fore.p, utsnitt: 'nara' }, amp: 1.25, steg: 8 })
  assert.equal(svar.text, '+3,0 steg: kameran +2,0 (närbild i stället för halvbild), agerandet +1,0 (rörelserna 25 % större än i originalet)')
})

test('texten använder decimal-komma och riktigt minustecken', () => {
  const upp = forklaring({ e: { kamera: 1 }, steg: 6.8 })
  const ner = forklaring({ e: { kamera: -1 }, steg: 3.2 })
  assert.equal(upp.text, '+1,8 steg: kameran +1,8')
  assert.equal(ner.text, '−1,8 steg: kameran −1,8')
  assert.ok(!ner.text.includes('-'))
  assert.doesNotMatch(ner.text, /\d\.\d/)
})

test('motverkande spakar behåller tecknen och delar på absolutbeloppet', () => {
  const mod = modell({ kamera: 2, motiv: -1 })
  const svar = forklaring({ e: { kamera: 1, motiv: 1 }, steg: 6 }, fore, mod)
  assert.deepEqual(svar.spakar.map(x => x.bidrag), [2, -1])
  nara(svar.spakar[0].andel, 2 / 3)
  nara(svar.spakar[1].andel, 1 / 3)
  assert.equal(svar.text, '+1,0 steg: kameran +2,0, agerandet −1,0')
})

test('visningsgränsen gäller spakens summa och ändrar inte dess andel', () => {
  const mod = modell({ kamera: 0.03, pan: 0.03, motiv: 0.85, energi: 0.05, egen: 0.04 })
  const e = { kamera: 1, pan: 1, motiv: 1, energi: 1, egen: 1 }
  const svar = forklaring({ e, steg: 6 }, fore, mod)
  assert.deepEqual(svar.spakar.map(x => x.spak), ['agerande', 'kamera', 'bild'])
  nara(svar.spakar.find(x => x.spak === 'kamera').bidrag, 0.06)
  nara(svar.spakar.find(x => x.spak === 'bild').bidrag, 0.05)
  nara(svar.spakar.reduce((summa, x) => summa + x.andel, 0), 0.96)
})

test('noll eller nästan noll nytta fördelar inga steg', () => {
  const mod = modell({ kamera: 1, motiv: -1 })
  for (const motiv of [1, 1 + 1e-12]) {
    const svar = forklaring({ e: { kamera: 1, motiv }, steg: 7 }, fore, mod)
    nara(svar.nytta, 0)
    assert.equal(svar.steg, 2)
    assert.deepEqual(svar.spakar, [])
    assert.equal(svar.text, '+2,0 steg')
  }
})

test('noll eller nästan noll steg beskrivs som ingen ändring', () => {
  for (const steg of [5, 5 + 1e-12]) {
    const svar = forklaring({ e: { kamera: 1 }, steg })
    assert.equal(svar.text, 'ingen ändring')
    assert.deepEqual(svar.spakar, [])
  }
})
