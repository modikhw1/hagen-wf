// Bedömningspar inom en scen: två sätt att filma och spela samma scen i ett rekonstruerat klipp, och
// frågan vilket som är mer rörligt och expansivt. Allt annat (handling, lokal, personer) är lika, så
// svaret handlar bara om vertikalen.
//
// Paren väljs där de lär modellen mest:
//   kamera   samma agerande, olika kamera, nära varandra i modellens nytta (osäkert)
//   agerande samma kamera, olika agerande (amp): isolerar den spaken
//   ankare   långt isär i nytta: kontroll av att modellen och bedömaren är överens om det uppenbara
// Varje bedömning sparar båda uttryckens korrigerade egenskaper, så att modellen kan tränas på dem
// tillsammans med bibliotekets scener (modellFor).
import { korrigera } from './placering.mjs'

export const VERTIKAL_UTTRYCK = 'rorlighet-uttryck'
export const parId = (klipp, scen, id) => `${klipp}#${scen}#${id}`

function rng(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646 }

// listor: placeraAlla(...) för klippet; gjorda: Set av 'a|b' redan bedömda; returnerar { scen, a, b, sort }
export function valjPar(listor, { gjorda = new Set(), slump = Math.random, sort } = {}) {
  const scener = listor.map((l, i) => (l?.length > 3 ? i : -1)).filter(i => i >= 0)
  if (!scener.length) return null
  for (let forsok = 0; forsok < 60; forsok++) {
    const i = scener[Math.floor(slump() * scener.length)]
    const l = listor[i].filter(x => x.u != null)
    const s = sort ?? (slump() < 0.45 ? 'kamera' : slump() < 0.55 ? 'agerande' : 'ankare')
    const a = l[Math.floor(slump() * l.length)]
    let kand
    if (s === 'agerande') kand = l.filter(x => x !== a && sammaKamera(x, a) && x.amp !== a.amp)
    else if (s === 'kamera') kand = l.filter(x => x !== a && (x.amp ?? 1) === (a.amp ?? 1) && !sammaKamera(x, a)).sort((x, y) => Math.abs(x.u - a.u) - Math.abs(y.u - a.u)).slice(0, 25)
    else kand = l.filter(x => x !== a && Math.abs(x.steg - a.steg) >= 5)
    if (!kand?.length) continue
    const b = kand[Math.floor(slump() * kand.length)]
    const nyckel = [a.id, b.id].sort().join('|')
    if (gjorda.has(`${i}:${nyckel}`)) continue
    // slumpa sida, så att bedömaren inte lär sig att den högra brukar vara mer rörlig
    return slump() < 0.5 ? { scen: i, a, b, sort: s } : { scen: i, a: b, b: a, sort: s }
  }
  return null
}
const sammaKamera = (x, y) => String(x.id).split('~a')[0] === String(y.id).split('~a')[0]

// Bedömningsraden (POST /__bedom/rorlighet-uttryck): id:n och korrigerade egenskaper.
export function bedomningsRad({ klipp, par, val, korr, namn, ms, bedomare = 'cm' }) {
  return {
    a: parId(klipp, par.scen, par.a.id), b: parId(klipp, par.scen, par.b.id), val, ms, bedomare, sort: par.sort,
    ea: korrigeradeRa(par.a.e, korr, namn), eb: korrigeradeRa(par.b.e, korr, namn),
  }
}
// Egenskaperna i analysens skala (bryggans korrektion), som modellen tränas i.
function korrigeradeRa(e, korr, namn) {
  const k = korrigera(e, korr, namn)
  return Object.fromEntries(Object.entries(k).map(([n, v]) => [n, Math.round(v * 10000) / 10000]))
}

// Items och bedömningar för träningen ur bedömningsraderna (egenskaperna följer med i raderna).
export function uttrycksItems(rader) {
  const items = new Map()
  for (const r of rader) {
    if (r.ea && !items.has(r.a)) items.set(r.a, { id: r.a, e: r.ea })
    if (r.eb && !items.has(r.b)) items.set(r.b, { id: r.b, e: r.eb })
  }
  return [...items.values()]
}

export { rng }
