// Placering av uttryck på en vertikal, och val av uttryck när reglaget dras.
//
// 1. Modellen tränas på bibliotekets scener (riktiga klipp, analysens egenskaper) och dina
//    bedömningar, men bara med egenskaper som bryggan har godkänt (korrektion giltig).
// 2. Varje uttryck har mätts med motorns syn; dess egenskaper översätts till analysens skala med
//    bryggans korrektion (a + b · motor) och får en nytta i modellen.
// 3. Skalan per scen förankras i tre punkter: lugnaste uttrycket 1, originalet 5, mest 10.
//    Mellan punkterna fördelas uttrycken efter rang, så att varje steg har kandidater.
import { trana, nytta } from './modell.mjs'
import { delaId } from '../src/forandring/manus/uttryck.js'
import { uttrycksItems } from './par.mjs'

// Mätningens version. 2: täckning (rekonstruktioner) och energi med analysens tidssteg (0,1 s).
// Rekonstruerade klipp använder bara scener mätta med denna version; äldre mätningar saknar
// täckningskontrollen och skulle släppa igenom vyer som rekonstruktionen inte bär.
export const MATNING_VERSION = 2
export function aktuellaScener(ut, antal, { rekon = false } = {}) {
  const scener = Array.from({ length: antal }, (_, i) => ut?.scener?.[i] ?? null)
  if (!rekon) return { scener, gamla: 0 }
  const gamla = scener.filter(s => s && s.version !== MATNING_VERSION).length
  return { scener: scener.map(s => (s && s.version === MATNING_VERSION ? s : null)), gamla }
}

// korr.inbyggd: egenskaperna kommer direkt ur analysen av riktig video (2D-uttryck), inte ur motorns syn,
// så alla gäller och ingen korrektion behövs.
export const INBYGGD = { inbyggd: true, egenskaper: {} }
export function giltigaEgenskaper(vertikal, korr) {
  if (korr?.inbyggd) return [...(vertikal.egenskaper ?? [])]
  const ok = new Set(Object.entries(korr?.egenskaper ?? {}).filter(([, v]) => v.giltig).map(([k]) => k))
  return (vertikal.egenskaper ?? []).filter(n => ok.has(n))
}

export const korrigera = (e, korr, namn) => Object.fromEntries(namn.map(n => {
  const k = korr.egenskaper[n]
  return [n, k?.giltig ? k.a + k.b * (e[n] ?? 0) : e[n] ?? 0]
}))

// uttryck: bedömningar av två sätt att filma samma scen (kalibrering/par.mjs); raderna bär egenskaperna
// i analysens skala, så de blir items bredvid bibliotekets scener.
export function modellFor({ vertikal, korr, bibliotek, bedomningar, uttryck = [] }) {
  const namn = giltigaEgenskaper(vertikal, korr)
  const start = Object.fromEntries(namn.map(n => [n, vertikal.start?.[n] ?? 0]))
  const items = [...bibliotek, ...uttrycksItems(uttryck)]
  const alla = [...bedomningar, ...uttryck].filter(b => b.val !== 'hoppa')
  const mod = trana({ items, bedomningar: alla, namn, start })
  return { mod, namn, items, bedomningar: alla }
}

// Placera alla giltiga uttryck i en scen. Returnerar [{ id, u, steg, p, ord, utsnitt }].
export function placeraScen(scen, { mod, namn, korr }) {
  const lista = scen.uttryck.filter(x => x.giltig || x.id === 'original').map(x => ({ ...x, u: nytta(mod, korrigera(x.e, korr, namn)) }))
  const orig = lista.find(x => x.id === 'original')
  const under = lista.filter(x => x.u < orig.u).sort((a, b) => a.u - b.u)
  const over = lista.filter(x => x.u > orig.u).sort((a, b) => a.u - b.u)
  under.forEach((x, k) => { x.steg = 1 + (4 * k) / Math.max(1, under.length) })
  over.forEach((x, k) => { x.steg = 5 + (5 * (k + 1)) / Math.max(1, over.length) })
  lista.filter(x => x.u === orig.u).forEach(x => { x.steg = 5 })
  return lista.map(x => ({ ...x, ...pa(x.id) }))
}

// ---------- kedjan ----------
// En gemensam skala för alla scener: originalets scener får då olika steg (en profil) i stället
// för att varje scen tvingas till 5. Skalan förankras i tre punkter över alla uttryck: lugnast 1,
// medel av originalens nytta 5, mest 10, och uttrycken fördelas efter rang mellan punkterna.
export function placeraAlla(scener, { mod, namn, korr }) {
  const listor = scener.map(sc => (sc?.uttryck?.length ? sc.uttryck.filter(x => x.giltig || x.id === 'original').map(x => ({ ...x, u: nytta(mod, korrigera(x.e, korr, namn)), ...pa(x.id) })) : null))
  const alla = listor.flatMap(l => l ?? [])
  const orig = listor.map(l => l?.find(x => x.id === 'original')).filter(Boolean)
  const mitt = orig.reduce((s, x) => s + x.u, 0) / Math.max(1, orig.length)
  const under = alla.filter(x => x.u < mitt).sort((a, b) => a.u - b.u)
  const over = alla.filter(x => x.u >= mitt).sort((a, b) => a.u - b.u)
  under.forEach((x, k) => { x.steg = 1 + (4 * k) / Math.max(1, under.length) })
  over.forEach((x, k) => { x.steg = 5 + (5 * k) / Math.max(1, over.length - 1) })
  return listor
}

// Kedjans mål: originalets profil flyttad med reglaget, utplattad mot ändarna (på 1 och 10 är
// alla scener lika), så att formen bevaras nära originalet och försvinner i ytterlägena.
export function malProfil(profil, mal) {
  const span = mal < 5 ? 4 : 5
  const f = Math.min(1, ((mal - 5) / span) ** 2)
  return profil.map(p => Math.max(1, Math.min(10, p + (mal - 5) - (p - 5) * f)))
}

// Välj uttryck för hela kedjan på en gång (dynamisk programmering över scenerna):
//   avvikelse från målet i varje scen
// + tröghet: att byta bort scenens nuvarande uttryck kostar efter hur olika det nya är
// + grannar: lågt mål vill ha enhetliga grannar (samma sätt att filma), högt mål vill ha variation
// tillat(i, x) är skyddsräckena: ett uttryck som inte är tillåtet för scenens plats väljs aldrig.
// hem: originalet är facit på 5; nära 5 dras varje scen tillbaka till originalets kamera, även
// efter en omväg (1 och sedan 5 ska ge originalet, inte ett grannuttryck på samma steg).
export function valjKedja({ mal, nu, listor, tolerans = 1, antal = 40, tillat = () => true, vikt: v = {} }) {
  const vikt = { trog: 1.2, granne: 0.6, hem: 1, ...v }
  // på 5 (±0,5) är originalet facit och vinner alltid, även över trögheten
  const hem = vikt.hem * Math.max(0, 1 - Math.abs(mal - 5) / 1.5) + (Math.abs(mal - 5) < 0.5 ? 4 : 0)
  const profil = listor.map(l => l?.find(x => x.id === 'original')?.steg ?? 5)
  const mals = malProfil(profil, mal)
  const forra = listor.map((l, i) => l?.find(x => x.id === nu[i]) ?? l?.find(x => x.id === 'original'))
  // kandidater per scen: nuvarande om det håller, plus de närmaste målet
  const kand = listor.map((l, i) => {
    if (!l) return null
    const ok = l.filter(x => tillat(i, x))
    const nara = ok.slice().sort((a, b) => Math.abs(a.steg - mals[i]) - Math.abs(b.steg - mals[i])).slice(0, antal)
    if (forra[i] && !nara.includes(forra[i]) && tillat(i, forra[i])) nara.push(forra[i])
    return nara
  })
  const kostnad = (i, x) => {
    const avv = Math.abs(x.steg - mals[i])
    const trog = x === forra[i] ? 0 : (Math.abs(forra[i].steg - mals[i]) <= tolerans ? 2 : 0) + vikt.trog * olikhet(x, forra[i])
    return avv + trog - (x.id === 'original' ? hem : 0)
  }
  const granne = (a, b) => {
    const o = olikhet(a, b)
    const enhet = Math.max(0, 5 - mal) / 4 // lågt mål: straffa skillnad
    const variation = Math.max(0, mal - 5) / 5 // högt mål: straffa likhet
    return vikt.granne * (enhet * o + variation * (1 - o))
  }
  // Viterbi över scener som har kandidater; scener utan behåller sitt nuvarande
  const idx = kand.map((k, i) => (k?.length ? i : -1)).filter(i => i >= 0)
  if (!idx.length) return listor.map((l, i) => ({ scen: i, val: nu[i] ?? 'original', mal: mals[i], profil: profil[i], beslut: 'saknas', kandidater: [] }))
  let bast = kand[idx[0]].map(x => ({ c: kostnad(idx[0], x), vag: [x] }))
  for (let j = 1; j < idx.length; j++) {
    const i = idx[j]
    bast = kand[i].map(x => {
      let b = null
      for (const p of bast) { const c = p.c + granne(p.vag[p.vag.length - 1], x); if (!b || c < b.c) b = { c, p } }
      return { c: b.c + kostnad(i, x), vag: [...b.p.vag, x] }
    })
  }
  const vinnare = bast.reduce((a, b) => (b.c < a.c ? b : a))
  const val = nu.slice()
  idx.forEach((i, j) => { val[i] = vinnare.vag[j].id })
  return listor.map((l, i) => ({
    scen: i, val: val[i], mal: mals[i], profil: profil[i],
    beslut: !l ? 'saknas' : val[i] === nu[i] ? 'stanna' : 'byt',
    kandidater: kand[i] ?? [],
  }))
}

// p: kamerans parametrar (null = originalets kamera), amp: agerandet (1 = originalets)
const pa = id => { const d = delaId(id); return { p: d.kamera, amp: d.amp, bakgrund: d.bakgrund, tva: d.tva } }
// 2D: zoom, bana (med mängd), skak och ankare; olika fält / 4
const delar2d = id => { const [, z, b, s, a] = id.split('|'); return [z, b, s, a] }

// Hur olika två uttryck är (0–1): antal parametrar som skiljer, plus agerandet. Mindre = mindre ryck.
export function olikhet(a, b) {
  const da = Math.min(1, Math.abs(Math.log((a?.amp ?? 1) / (b?.amp ?? 1))) / Math.log(2)) * 0.35 + ((a?.bakgrund ?? 0) !== (b?.bakgrund ?? 0) ? 0.25 : 0)
  if (a?.tva || b?.tva) {
    if (!a?.tva || !b?.tva) return Math.min(1, 0.5 + da) // 2D mot originalet
    const x = delar2d(a.tva), y = delar2d(b.tva)
    return Math.min(1, x.filter((v, i) => v !== y[i]).length / 4 + da)
  }
  if (!a?.p || !b?.p) return Math.min(1, (!a?.p && !b?.p ? 0 : 0.5) + da)
  const n = ['utsnitt', 'vinkel', 'hojd', 'rorelse', 'skak'].filter(k => a.p[k] !== b.p[k]).length + (a.p.mangd !== b.p.mangd ? 0.5 : 0)
  return Math.min(1, n / 5.5 + da)
}

// Nytt mål på reglaget: per scen, stanna om nuvarande uttryck ligger inom trögheten, annars
// kandidaterna närmast målet (minst ryck först). Returnerar beslut och kandidater, så att Jev kan
// välja bland dem med helheten i texten.
export function valjUttryck({ mal, nu, placerade, tolerans = 1, antal = 24 }) {
  // en scen per plats i nu; scener som saknar mätta uttryck ligger kvar som de är
  return nu.map((id, i) => {
    const lista = placerade[i]
    if (!lista?.length) return { scen: i, val: id ?? 'original', beslut: 'saknas', kandidater: [] }
    const forra = lista.find(x => x.id === id) ?? lista.find(x => x.id === 'original')
    if (Math.abs(forra.steg - mal) <= tolerans) return { scen: i, val: forra.id, beslut: 'stanna', kandidater: [] }
    const kand = lista
      .map(x => ({ x, poang: Math.abs(x.steg - mal) + 0.8 * olikhet(x, forra) }))
      .sort((a, b) => a.poang - b.poang)
      .slice(0, antal)
      .map(k => k.x)
    return { scen: i, val: kand[0].id, beslut: 'byt', fran: forra.id, kandidater: kand }
  })
}

// Uttrycket i ord, för Jev och för människor.
const UTS = { total: 'helbild', halvtotal: 'halvtotal', halvbild: 'halvbild', nara: 'närbild', extrem: 'extrem närbild' }
const ROR = { static: 'stillastående kamera', dolly: 'kameran åker in mot motivet', pan: 'kameran panorerar', truck: 'kameran glider i sidled', arc: 'kameran går i en båge runt motivet', zoom: 'zoomar in', tilt: 'kameran tiltar', pedestal: 'kameran höjs' }
export function beskriv(x) {
  const ag = ((x.amp ?? 1) === 1 ? '' : `, agerandet ${x.amp > 1 ? '+' : '−'}${Math.round(Math.abs(x.amp - 1) * 100)} %`) + (x.bakgrund ? ', en statist går förbi i bakgrunden' : '')
  if (!x.p) return `originalets kamera (${(x.ord ?? []).join(', ')})${ag}`
  const p = x.p
  const vinkel = p.vinkel === 0 ? 'rakt framifrån' : `${Math.abs(p.vinkel)}° från ${p.vinkel < 0 ? 'vänster' : 'höger'}`
  const hojd = p.hojd > 4 ? `högt (${p.hojd}°)` : p.hojd < -4 ? `lågt (${-p.hojd}°)` : 'i ögonhöjd'
  const skak = p.skak >= 0.6 ? ', tydligt handhållen' : p.skak > 0 ? ', lite handhållen' : ''
  return `${UTS[p.utsnitt]}, ${vinkel}, ${hojd}, ${ROR[p.rorelse]}${p.rorelse !== 'static' && p.mangd ? ` (${p.mangd})` : ''}${skak}${ag}`
}
