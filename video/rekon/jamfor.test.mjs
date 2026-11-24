import { test as prova } from 'node:test'
import kontroll from 'node:assert/strict'
import { readFileSync as lasFil } from 'node:fs'
import { jamforRekon } from './jamfor.mjs'
import { identiteter } from './spar.mjs'
import { FOV_H, FOV_V } from './geometri.mjs'

const LEDER = [0, 11, 12, 13, 14, 15, 16, 23, 24]
const BILDFALT = ['energi', 'kant', 'symmetri', 'entropi', 'balans']
const nara = (varde, vantat, tolerans = 1e-10) => {
  kontroll.ok(Math.abs(varde - vantat) < tolerans, `${varde} ska vara nära ${vantat}`)
}
const scen = (start, slut, extra = {}) => ({
  start,
  slut,
  utsnitt: { varde: 'halvbild' },
  personer: 1,
  kamera: { pan: 0.02, tilt: -0.01, roll: 1, zoom: 1.01, sekunder: slut - start },
  bildmatt: { energi: 0.04, kant: 0.2, symmetri: 0.8, entropi: 0.9, balans: 0.06 },
  ...extra,
})

function ruta(i, extra = {}) {
  const lm = Array.from({ length: 33 }, () => [0.5, 0.5, 1])
  const punkter = [
    [0.5, 0.2], [0.3, 0.35], [0.7, 0.35], [0.25, 0.5], [0.75, 0.5],
    [0.2, 0.65], [0.8, 0.65], [0.4, 0.7], [0.6, 0.7],
  ]
  for (const [j, k] of LEDER.entries()) lm[k] = [...punkter[j], 1]
  return { i, b: [0.1, 0.1, 0.9, 0.9], lm, varld: null, ...extra }
}

const person = (ramar, id = 'p1') => ({
  id,
  spar: [{ scen: 0, forst: ramar[0].i, sist: ramar.at(-1).i, ramar }],
})

function projicera(personer, n) {
  const projektioner = Array.from({ length: n }, () => ({}))
  for (const p of personer) {
    for (const s of p.spar) {
      for (const r of s.ramar) {
        if (r.fylld || !r.lm) continue
        projektioner[r.i][p.id] = {
          synlig: true,
          punkter: Object.fromEntries(LEDER.map(k => [k, r.lm[k].slice(0, 2)])),
        }
      }
    }
  }
  return projektioner
}

const bild = (offset = 0) => Float32Array.from({ length: 18 * 32 }, (_, i) => ((i + offset) % 576) / 1024)

function underlag(n = 6) {
  const original = { scener: [scen(0, n / 10)], ramar: Array.from({ length: n }, () => ({})) }
  const personer = [person(Array.from({ length: n }, (_, i) => ruta(i)))]
  const originalbilder = Array.from({ length: n }, (_, i) => bild(i))
  return {
    original,
    rendering: original,
    personer,
    projektioner: projicera(personer, n),
    bilder: { original: originalbilder, rendering: originalbilder.map(b => b.slice()) },
  }
}

const scenresultat = (original, rendering) => jamforRekon({
  original: { scener: original },
  rendering: { scener: rendering },
})

prova('identiska indata ger åtta fulla mått och total 1 utan att ändra indata', () => {
  const data = underlag()
  const fore = structuredClone(data)
  const resultat = jamforRekon(data)
  const vantade = {
    pose: ['Rörelser (pose)', 2],
    narvaro: ['Personer på plats', 1],
    granser: ['Scengränser', 1],
    utsnitt: ['Utsnitt per scen', 1],
    antal: ['Antal personer', 1],
    kamera: ['Kamerarörelse', 1],
    bildmatt: ['Bildens rörlighet', 1.5],
    bild: ['Bildens uppbyggnad', 1.5],
  }
  kontroll.deepEqual(Object.keys(resultat.matt), Object.keys(vantade))
  for (const [nyckel, [namn, vikt]] of Object.entries(vantade)) {
    kontroll.equal(resultat.matt[nyckel].varde, 1, nyckel)
    kontroll.equal(resultat.matt[nyckel].namn, namn)
    kontroll.equal(resultat.matt[nyckel].vikt, vikt)
    kontroll.ok(resultat.matt[nyckel].detalj)
  }
  kontroll.equal(resultat.total, 1)
  kontroll.equal(resultat.matt.pose.detalj.punkter, 54)
  kontroll.equal(resultat.matt.pose.detalj.medianAvstand, 0)
  kontroll.deepEqual(data, fore)
  kontroll.deepEqual(jamforRekon(data), resultat)
})

prova('en förskjutning på 0,5 bildhöjd ger pose 0 och medianavstånd 0,5', () => {
  const data = underlag()
  for (const proj of data.projektioner) {
    for (const p of Object.values(proj.p1.punkter)) p[1] += 0.5
  }
  const { pose } = jamforRekon(data).matt
  kontroll.equal(pose.varde, 0)
  nara(pose.detalj.medianAvstand, 0.5)
})

prova('pose mäter horisontella avstånd i bildhöjder', () => {
  const data = underlag(1)
  for (const p of Object.values(data.projektioner[0].p1.punkter)) p[0] += 0.25
  const { pose } = jamforRekon(data).matt
  kontroll.equal(pose.varde, 1)
  nara(pose.detalj.medianAvstand, 0.140625)
})

prova('PCK använder varje rutas höjd och en strikt avståndsgräns', () => {
  const data = underlag(2)
  const ramar = data.personer[0].spar[0].ramar
  for (const r of ramar) {
    for (const p of r.lm) p[2] = 0
    r.lm[0] = [0.5, 0.25, 1]
  }
  ramar[0].b = [0, 0, 1, 0.5]
  ramar[1].b = [0, 0, 1, 1]
  data.projektioner = projicera(data.personer, 2)
  for (const proj of data.projektioner) proj.p1.punkter[0][1] += 0.125
  const { pose } = jamforRekon(data).matt
  kontroll.equal(pose.varde, 0.5)
  nara(pose.detalj.medianAvstand, 0.125)

  ramar[0].b = [0, 0, 1, 1]
  ramar[0].lm[0][1] = 0
  data.projektioner[0].p1.punkter[0][1] = 0.2
  data.projektioner[1].p1.synlig = false
  kontroll.equal(jamforRekon(data).matt.pose.varde, 0)
})

prova('pose använder rimlig synlighet och tar med synlighet exakt 0,6', () => {
  const data = underlag(1)
  const lm = data.personer[0].spar[0].ramar[0].lm
  lm[23][1] = 1.1 // Hög rå synlighet trots att höften ligger nedanför personrutan.
  lm[24][2] = 0.59
  lm[0][2] = 0.6
  data.projektioner[0].p1.punkter[0][1] += 0.5
  const { pose } = jamforRekon(data).matt
  kontroll.equal(pose.detalj.punkter, 7)
  nara(pose.varde, 6 / 7)
})

prova('en saknad projekterad led räknas som fel medan en osynlig docka saknar posemått', () => {
  const data = underlag(1)
  delete data.projektioner[0].p1.punkter[15]
  const { pose } = jamforRekon(data).matt
  nara(pose.varde, 8 / 9)
  kontroll.equal(pose.detalj.saknadePunkter, 1)
  data.projektioner[0].p1.synlig = false
  kontroll.equal(jamforRekon(data).matt.pose.varde, null)
  kontroll.equal(jamforRekon(data).matt.narvaro.varde, 0)
})

prova('närvaro räknar F1 med ofyllda rutor och synliga huvud- eller axelpunkter', () => {
  const data = underlag(5)
  data.personer = [person([
    ruta(0, { lm: null }),
    ruta(1, { lm: null, fylld: true }),
    ruta(2, { lm: null }),
    ruta(3, { lm: null }),
  ])]
  data.projektioner = [
    { p1: { synlig: true, punkter: { 11: [0, 1] } } },
    { p1: { synlig: true, punkter: { 0: [0.5, 0.5] } } },
    { p1: { synlig: true, punkter: { 0: [1.01, 0.5], 11: [0.5, 1.01], 12: [-0.01, 0.5], 15: [0.5, 0.5] } } },
    { p1: { synlig: false, punkter: { 0: [0.5, 0.5] } } },
    { p2: { synlig: true, punkter: { 12: [1, 0] } } },
  ]
  const { narvaro, pose } = jamforRekon(data).matt
  nara(narvaro.varde, 1 / 3)
  kontroll.deepEqual(narvaro.detalj, { rutor: 5, traffar: 1, extra: 2, missade: 2 })
  kontroll.equal(pose.varde, null)
})

prova('två uppmätta rutor utan personer ger full närvarolikhet', () => {
  const data = underlag(2)
  data.personer = []
  data.projektioner = [{}, {}]
  kontroll.equal(jamforRekon(data).matt.narvaro.varde, 1)
})

prova('en extra scengräns sänker F1 och varje gräns får bara matchas en gång', () => {
  const original = [scen(0, 1), scen(1, 2)]
  const rendering = [scen(0, 0.9), scen(0.9, 1.1), scen(1.1, 2)]
  const { granser } = scenresultat(original, rendering).matt
  nara(granser.varde, 2 / 3)
  kontroll.equal(granser.detalj.traffar, 1)
  kontroll.equal(granser.detalj.extra, 1)
  nara(scenresultat(rendering, original).matt.granser.varde, 2 / 3)
})

prova('gränsmatchningen maximerar antalet par och inkluderar exakt 0,2 sekunder', () => {
  const original = [scen(0, 1), scen(1, 1.2), scen(1.2, 2)]
  const rendering = [scen(0, 0.81), scen(0.81, 1.01), scen(1.01, 2)]
  kontroll.equal(scenresultat(original, rendering).matt.granser.varde, 1)
  const a = [scen(0, 1), scen(1, 2)]
  kontroll.equal(scenresultat(a, [scen(0, 1.2), scen(1.2, 2)]).matt.granser.varde, 1)
  kontroll.equal(scenresultat(a, [scen(0, 1.20001), scen(1.20001, 2)]).matt.granser.varde, 0)
  kontroll.equal(scenresultat([scen(0, 2)], [scen(0, 2)]).matt.granser.varde, 1)
  kontroll.equal(scenresultat([scen(0, 2)], a).matt.granser.varde, 0)
})

prova('scenpar väljs efter största överlapp och utsnitt samt personantal längdviktas', () => {
  const original = [
    scen(0, 1, { utsnitt: { varde: 'nara' }, personer: 1 }),
    scen(1, 4, { utsnitt: { varde: 'total' }, personer: 4 }),
  ]
  const rendering = [
    scen(0, 0.4, { utsnitt: { varde: 'total' }, personer: 99 }),
    scen(0.4, 1.2, { utsnitt: { varde: 'nara' }, personer: 1 }),
    scen(1.2, 4, { utsnitt: { varde: 'halvtotal' }, personer: 2 }),
  ]
  const { utsnitt, antal } = scenresultat(original, rendering).matt
  kontroll.equal(utsnitt.varde, 0.625)
  kontroll.equal(antal.varde, 0.625)
  kontroll.deepEqual(utsnitt.detalj, { scener: 2, sekunder: 4 })
})

prova('utsnitt följer hela skalan och objekt räknas som saknat', () => {
  const ordning = ['extrem', 'nara', 'halvbild', 'halvtotal', 'total']
  for (const [i, varde] of ordning.entries()) {
    const a = [scen(0, 1, { utsnitt: { varde: 'extrem' } })]
    const b = [scen(0, 1, { utsnitt: { varde } })]
    kontroll.equal(scenresultat(a, b).matt.utsnitt.varde, [1, 0.5, 0, 0, 0][i])
  }
  const a = [scen(0, 1), scen(1, 10, { utsnitt: { varde: 'objekt' }, personer: null })]
  const { utsnitt, antal } = scenresultat(a, [scen(0, 1), scen(1, 10)]).matt
  kontroll.equal(utsnitt.varde, 1)
  kontroll.equal(utsnitt.detalj.scener, 1)
  kontroll.equal(antal.varde, 1)
  kontroll.equal(antal.detalj.scener, 1)
  kontroll.equal(scenresultat([scen(0, 1, { utsnitt: null })], [scen(0, 1)]).matt.utsnitt.varde, null)
})

prova('antal hanterar noll personer och scenmått kräver tidsöverlapp', () => {
  kontroll.equal(scenresultat([scen(0, 1, { personer: 0 })], [scen(0, 1, { personer: 0 })]).matt.antal.varde, 1)
  kontroll.equal(scenresultat([scen(0, 1, { personer: 0 })], [scen(0, 1, { personer: 2 })]).matt.antal.varde, 0)
  const { matt } = scenresultat([scen(0, 1)], [scen(1, 2)])
  for (const k of ['utsnitt', 'antal', 'kamera', 'bildmatt']) kontroll.equal(matt[k].varde, null, k)
})

prova('kameran normaliserar bildandelar till grader per uppmätt sekund och zoom kring 1', () => {
  const a = scen(0, 10, { kamera: { pan: 4 / FOV_H, tilt: -1 / FOV_V, roll: 1, zoom: 1.03, sekunder: 2 } })
  const b = scen(0, 10, { kamera: { pan: 1 / FOV_H, tilt: 0, roll: 0, zoom: 1, sekunder: 1 } })
  // Likheterna är 0,5 för pan, 0,75 för tilt och roll samt 0 för zoom.
  nara(scenresultat([a], [b]).matt.kamera.varde, 0.5)
  const c = scen(0, 1, { kamera: { zoom: 1.01 } })
  const d = scen(0, 1, { kamera: { zoom: 0.99 } })
  nara(scenresultat([c], [d]).matt.kamera.varde, 1 / 3)
})

prova('kameramåttet använder kända fält, tidsreserv och scenlängder', () => {
  const a = scen(0, 2, { kamera: { roll: 4 } })
  const b = scen(0, 1, { kamera: { roll: 2 } })
  kontroll.equal(scenresultat([a], [b]).matt.kamera.varde, 1)
  kontroll.equal(scenresultat([scen(0, 1, { kamera: { ord: ['okänd'] } })], [b]).matt.kamera.varde, null)
  kontroll.equal(scenresultat([scen(0, 1, { kamera: { roll: 2, sekunder: 0 } })], [b]).matt.kamera.varde, null)

  const kamera = { pan: 0.1, tilt: 0.1, roll: 6, zoom: 1.1, sekunder: 1 }
  const motsatt = { pan: -0.1, tilt: -0.1, roll: -6, zoom: 0.9, sekunder: 1 }
  const original = [scen(0, 1, { kamera }), scen(1, 4, { kamera })]
  const rendering = [scen(0, 1, { kamera }), scen(1, 4, { kamera: motsatt })]
  nara(scenresultat(original, rendering).matt.kamera.varde, 0.25)
})

prova('bildmåtten använder golv 0,05, vanligt scenmedel och hoppar över ofullständiga scener', () => {
  const matt = tal => Object.fromEntries(BILDFALT.map(k => [k, tal]))
  const original = [
    scen(0, 1, { bildmatt: matt(0.02) }),
    scen(1, 4, { bildmatt: matt(0) }),
    scen(4, 20, { bildmatt: { ...matt(1), energi: null } }),
  ]
  const rendering = [scen(0, 1, { bildmatt: matt(0.01) }), scen(1, 4, { bildmatt: matt(0) }), scen(4, 20)]
  const { bildmatt } = scenresultat(original, rendering).matt
  nara(bildmatt.varde, 0.9)
  kontroll.deepEqual(bildmatt.detalj, { scener: 2, sekunder: 4 })
  delete original[0].bildmatt.kant
  original[1].bildmatt = null
  kontroll.equal(scenresultat(original, rendering).matt.bildmatt.varde, null)
})

prova('bildkorrelationen tål ljus och kontrast, klipper negativa värden och hoppar över konstanta bilder', () => {
  const a = bild()
  const konstant = new Float32Array(18 * 32).fill(0.5)
  const data = underlag(4)
  data.bilder = {
    original: [a, a, konstant, a],
    rendering: [a.map(v => v * 0.5 + 0.25), a.map(v => 1 - v), a, konstant],
  }
  const resultat = jamforRekon(data).matt.bild
  nara(resultat.varde, 0.5)
  kontroll.deepEqual(resultat.detalj, { rutor: 2, overhoppade: 2 })
  data.bilder = { original: [konstant], rendering: [konstant] }
  kontroll.equal(jamforRekon(data).matt.bild.varde, null)
})

prova('oberoende slumpbilder ger bildmått nära 0 med reproducerbar slump', () => {
  let tillstand = 123456789
  const slump = () => {
    tillstand = (Math.imul(1664525, tillstand) + 1013904223) >>> 0
    return tillstand / 2 ** 32
  }
  const serie = () => Array.from({ length: 64 }, () => Float32Array.from({ length: 18 * 32 }, slump))
  const { bild: resultat } = jamforRekon({ original: {}, rendering: {}, bilder: { original: serie(), rendering: serie() } }).matt
  kontroll.ok(resultat.varde >= 0 && resultat.varde < 0.05, `slumpkorrelation ${resultat.varde}`)
  kontroll.equal(resultat.detalj.rutor, 64)
})

prova('alla rutmått begränsas av den kortaste analysen även vid två extra rutor', () => {
  for (const kortare of ['original', 'rendering']) {
    const data = underlag(6)
    data.rendering = structuredClone(data.original)
    data[kortare].ramar = data[kortare].ramar.slice(0, 4)
    for (const i of [4, 5]) {
      for (const p of Object.values(data.projektioner[i].p1.punkter)) p[1] += 0.5
      data.bilder.rendering[i] = data.bilder.original[i].map(v => 1 - v)
    }
    const { pose, narvaro, bild: resultat } = jamforRekon(data).matt
    kontroll.equal(pose.varde, 1)
    kontroll.equal(pose.detalj.punkter, 36)
    kontroll.equal(narvaro.detalj.rutor, 4)
    kontroll.equal(resultat.varde, 1)
    kontroll.equal(resultat.detalj.rutor, 4)
  }
})

prova('kortare projektioner och bildserier begränsar sina egna mått', () => {
  const data = underlag(6)
  data.projektioner = data.projektioner.slice(0, 4)
  data.bilder.rendering = data.bilder.rendering.slice(0, 5)
  const { pose, narvaro, bild: resultat } = jamforRekon(data).matt
  kontroll.equal(pose.detalj.punkter, 36)
  kontroll.equal(narvaro.detalj.rutor, 4)
  kontroll.equal(resultat.detalj.rutor, 5)
  kontroll.equal(jamforRekon(data).total, 1)
})

prova('fps avgör gemensamt rutantal när analyserna bara anger tider', () => {
  const data = underlag(6)
  data.fps = 20
  data.original = { meta: { langd: 0.2 }, scener: [scen(0, 0.2)] }
  data.rendering = { meta: { langd: 0.3 }, scener: [scen(0, 0.3)] }
  kontroll.equal(jamforRekon(data).matt.pose.detalj.punkter, 36)
  kontroll.equal(jamforRekon(data).matt.bild.detalj.rutor, 4)
  delete data.original.meta
  delete data.rendering.meta
  kontroll.equal(jamforRekon(data).matt.narvaro.detalj.rutor, 4)
})

prova('saknat underlag ger null och totalen viktar endast mätbara mått inklusive nollor', () => {
  const tomt = jamforRekon({ original: {}, rendering: {} })
  kontroll.equal(tomt.total, null)
  for (const m of Object.values(tomt.matt)) kontroll.equal(m.varde, null)
  const a = bild()
  const resultat = jamforRekon({
    original: { scener: [{ start: 0, slut: 1, personer: 2 }] },
    rendering: { scener: [{ start: 0, slut: 1, personer: 1 }] },
    bilder: { original: [a], rendering: [a.map(v => 1 - v)] },
  })
  kontroll.equal(resultat.matt.granser.varde, 1)
  kontroll.equal(resultat.matt.antal.varde, 0.5)
  kontroll.equal(resultat.matt.bild.varde, 0)
  nara(resultat.total, 3 / 7)
})

prova('tomma rutserier och ogiltiga mätvärden blir aldrig NaN', () => {
  const data = underlag(1)
  data.original = { ...data.original, ramar: [] }
  for (const k of ['pose', 'narvaro', 'bild']) kontroll.equal(jamforRekon(data).matt[k].varde, null)
  data.original = { scener: [scen(0, 1, { personer: NaN, kamera: { roll: Infinity }, bildmatt: null })] }
  data.bilder.original[0][0] = NaN
  const resultat = jamforRekon(data)
  for (const k of ['antal', 'kamera', 'bildmatt', 'bild']) kontroll.equal(resultat.matt[k].varde, null)
  kontroll.ok(Number.isFinite(resultat.total))
  for (const fps of [0, -1, NaN, Infinity]) kontroll.throws(() => jamforRekon({ original: {}, rendering: {}, fps }), RangeError)
})

prova('riktig analysfil jämför scenmått och pose med identiska observationer', () => {
  const original = JSON.parse(lasFil(new URL('../../data/analys/b.b.kebab-1779386335747.json', import.meta.url), 'utf8'))
  const fps = original.analys.fps
  const packa = lista => lista && Array.from({ length: lista.length / 3 }, (_, i) => lista.slice(i * 3, i * 3 + 3))
  const ramar = original.ramar.map(r => ({
    personer: r.p.map(p => ({ b: p.b, lm: packa(p.lm), varld: packa(p.v) })),
  }))
  const personer = identiteter(ramar, original.scener.map(s => ({
    i0: Math.round(s.start * fps),
    i1: Math.min(ramar.length, Math.round(s.slut * fps)),
  })))
  const bilder = Array.from({ length: ramar.length }, (_, i) => bild(i))
  const resultat = jamforRekon({
    original,
    rendering: original,
    personer,
    projektioner: projicera(personer, ramar.length),
    bilder: { original: bilder, rendering: bilder.map(b => b.slice()) },
    fps,
  })
  kontroll.ok(personer.length > 0)
  kontroll.ok(resultat.matt.pose.detalj.punkter > 100)
  for (const k of ['pose', 'granser', 'utsnitt', 'antal', 'kamera', 'bildmatt', 'bild']) {
    kontroll.equal(resultat.matt[k].varde, 1, k)
  }
  // Ett riktigt spår kan ha både huvud och axlar utanför bild trots en detekterad personruta.
  const observerade = personer.flatMap(p => p.spar.flatMap(s => s.ramar)).filter(r => !r.fylld)
  const synliga = observerade.filter(r => r.lm && [0, 11, 12].some(k => {
    const [u, v] = r.lm[k]
    return u >= 0 && u <= 1 && v >= 0 && v <= 1
  })).length
  nara(resultat.matt.narvaro.varde, 2 * synliga / (observerade.length + synliga))
  kontroll.equal(resultat.matt.narvaro.detalj.extra, 0)
  nara(resultat.total, (9 + resultat.matt.narvaro.varde) / 10)
})
