// Urval av träningsdata ur banken (klipp från bank/hamta.mjs eller bank/importera.mjs).
//
//   node bank/urval.mjs [--mal 300] [--per-konto 0.3]
//
// Förutsätter att klippen är analyserade (npm run analysera -- --kallor) och har Geminis typer
// (npm run typer -- forslag, och marka när typlistan finns). Varje klipp får:
//   rekonbar    0–1: går det att rekonstruera? personer i bild, högst fyra samtidigt, inte bara
//               montage (snittscen ≥ 0,8 s), inte mest föremål, längd 5–90 s
//   engagemang  0–1 eller null: visningar och gillanden relativt kontots egna klipp (percentil),
//               alltså vad profilen själv uppnått, inte hur stor den är
//   poang       medel av de två (engagemang 0,5 om okänt)
// Urvalet: en kvot per typ (lika många per typ, högst --mal totalt), högst --per-konto av en typ från
// samma konto (bredd), bäst poäng först. Resultat: data/bank/urval.json, med skäl per klipp.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MAL = Number(varde('--mal', 300))
const PER_KONTO = Number(varde('--per-konto', 0.3))
const lasJson = f => (fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null)
const r2 = v => (v == null ? null : Math.round(v * 100) / 100)

export function rekonbarhet(a) {
  const L = a.meta?.langd ?? a.scener.reduce((s, x) => Math.max(s, x.slut), 0)
  const skal = []
  const vikt = s => (s.slut - s.start) / Math.max(0.01, L)
  const medPerson = a.scener.reduce((s, x) => s + (x.personer > 0 ? vikt(x) : 0), 0)
  const forManga = a.scener.reduce((s, x) => s + (x.personer > 4 ? vikt(x) : 0), 0)
  const objekt = a.scener.reduce((s, x) => s + (x.utsnitt?.varde === 'objekt' ? vikt(x) : 0), 0)
  const snitt = L / Math.max(1, a.scener.length)
  let v = 1
  if (L < 5 || L > 90) { v *= 0.4; skal.push(`längd ${L.toFixed(0)} s`) }
  v *= 0.3 + 0.7 * medPerson
  if (medPerson < 0.6) skal.push(`personer i bild ${Math.round(medPerson * 100)} %`)
  if (forManga > 0.2) { v *= 1 - forManga * 0.7; skal.push('fler än fyra personer') }
  if (objekt > 0.4) { v *= 1 - objekt * 0.5; skal.push(`mest föremål (${Math.round(objekt * 100)} %)`) }
  if (snitt < 0.8) { v *= 0.5; skal.push(`montage (snittscen ${snitt.toFixed(1)} s)`) }
  return { varde: r2(v), skal }
}

// Före den lokala analysen: Geminis sållning (bank/sallning.mjs) ger en grövre rekonstruerbarhet.
export function rekonbarSallning(x) {
  const skal = []
  let v = x.rekonbar / 5
  if (x.bildspel) { v = 0; skal.push('bildspel') }
  if (x.montage) { v *= 0.5; skal.push('montage') }
  if (x.text_tung) { v *= 0.6; skal.push('skärmtexten bär') }
  if (!x.inne_i_verksamheten) { v *= 0.5; skal.push('inte i verksamheten') }
  if (x.personer_max > 4) { v *= 0.6; skal.push('fler än fyra personer') }
  v *= 0.5 + 0.1 * x.bildkvalitet
  v *= 0.3 + 0.7 * Math.max(0, Math.min(1, x.andel_med_person))
  if (x.bildkvalitet <= 2) skal.push(`bildkvalitet ${x.bildkvalitet}`)
  return { varde: r2(v), skal }
}

// Användbarhet för 2D-spåret (plan.md, 31 okt): varianter görs på originalvideon, så mat, föremål och
// montage är lika användbara som personer. Bara bildspel, låg bildkvalitet och klipp som inte är
// filmade i verksamheten drar ner. Utan sållning: 0,7 (okänt). Rekonstruerbarheten (3D) står kvar.
export function anvandbar2d(x) {
  if (!x) return { varde: 0.7, skal: [] }
  const skal = []
  let v = 0.4 + 0.12 * x.bildkvalitet
  if (x.bildspel) { v = 0; skal.push('bildspel') }
  if (!x.inne_i_verksamheten) { v *= 0.6; skal.push('inte i verksamheten') }
  if (x.bildkvalitet <= 2) skal.push(`bildkvalitet ${x.bildkvalitet}`)
  return { varde: r2(Math.min(1, v)), skal }
}

// Lämplighet för LeTrends träningsdata, kalibrerad mot ägarens första 54 bedömningar i #bank (1 nov):
// det som togs med var rekonstruerbart (sållningens rekonbar 4,1 mot 1,9), med personer i bild nästan
// hela tiden och oftast sketcher; det som valdes bort var "annat", montage, texttungt, grafiska layouter
// och klipp för knutna till en verksamhet för att kunna överföras. Matporr är användbart men sekundärt.
const TYPVIKT = { relaterbar_sketch: 1, direkt_tilltal: 0.9, vardens_provsmakning: 0.9, matporr_och_process: 0.7, annat: 0.35 }
export function lamplighet(x, typ) {
  if (!x) return { varde: 0.5, skal: [] }
  const skal = []
  let v = (x.rekonbar / 5) * (0.4 + 0.6 * Math.max(0, Math.min(1, x.andel_med_person)))
  if (x.bildspel) { v = 0; skal.push('bildspel') }
  if (x.montage) { v *= 0.6; skal.push('montage') }
  if (x.text_tung) { v *= 0.6; skal.push('texttungt') }
  if (!x.inne_i_verksamheten) { v *= 0.5; skal.push('inte i verksamheten') }
  if (x.bildkvalitet <= 2) { v *= 0.7; skal.push(`bildkvalitet ${x.bildkvalitet}`) }
  v *= TYPVIKT[typ] ?? 0.6
  if ((TYPVIKT[typ] ?? 1) < 0.8) skal.push(`typen ${typ} är sekundär`)
  return { varde: r2(v), skal }
}

// percentil inom kontot (0–1), eller null om värdet saknas
function percentil(varden, v) {
  if (v == null || varden.length < 3) return null
  const under = varden.filter(x => x < v).length, lika = varden.filter(x => x === v).length
  return (under + lika / 2) / varden.length
}

if (import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const kallor = lasJson(path.join(DATA, 'kallor.json')) ?? {}
  const bedomningar = lasJson(path.join(DATA, 'bank', 'bedomningar.json')) ?? {}
  const bank = Object.entries(kallor).filter(([, k]) => k.kalla === 'bank' || k.kalla === 'import')
  const perKonto = {}
  for (const [, k] of bank) (perKonto[k.konto] ||= []).push(k)
  const klipp = []
  const saknar = { analys: 0, typ: 0, sallning: 0 }
  for (const [id, k] of bank) {
    const a = lasJson(path.join(DATA, 'analys', `${id}.json`))
    const sall = lasJson(path.join(DATA, 'bank', 'sallning', `${id}.json`))
    if (!a) saknar.analys++
    if (!a && !sall) { saknar.sallning++; continue }
    const mark = lasJson(path.join(DATA, 'typer', 'markning', `${id}.json`))
    const forslag = lasJson(path.join(DATA, 'typer', 'forslag', `${id}.json`))
    const typ = mark?.typ ?? sall?.typ ?? forslag?.typ?.namn ?? null
    if (!typ) saknar.typ++
    const rb = a ? rekonbarhet(a) : rekonbarSallning(sall)
    const egna = perKonto[k.konto]
    const pv = percentil(egna.map(x => x.visningar).filter(x => x != null), k.visningar)
    const gr = k.visningar ? k.gillanden / k.visningar : null
    const pg = percentil(egna.map(x => (x.visningar ? x.gillanden / x.visningar : null)).filter(x => x != null), gr)
    const eng = pv == null ? null : pg == null ? pv : 0.6 * pv + 0.4 * pg
    const a2 = anvandbar2d(sall)
    const lp = lamplighet(sall, typ)
    klipp.push({ id, konto: k.konto, anvandbar: a2.varde, typ: typ ?? 'okand', intent: forslag?.primary_intent ?? null, grund: a ? 'analys' : 'sallning', innehall: sall?.innehall ?? null, langd: r2(a?.meta?.langd ?? k.langd), scener: a?.scener.length ?? null, visningar: k.visningar ?? null, rekonbar: rb.varde, engagemang: r2(eng), lamplig: lp.varde, poang: r2(0.6 * lp.varde + 0.4 * (eng ?? 0.5)), skal: lp.skal, rekonSkal: rb.skal })
  }
  // kvot per typ, tak per konto inom typen
  const typer = [...new Set(klipp.map(k => k.typ))]
  const vikt = t => TYPVIKT[t] ?? 0.6
  const kvotFor = t => Math.ceil((MAL * vikt(t)) / typer.reduce((a, x) => a + vikt(x), 0))
  const kvot = Math.ceil(MAL / Math.max(1, typer.length))
  const valda = new Set()
  for (const t of typer) {
    const av = klipp.filter(k => k.typ === t && k.lamplig >= 0.4).sort((a, b) => b.poang - a.poang)
    const tak = Math.max(2, Math.floor(kvot * PER_KONTO))
    const perK = {}
    for (const k of av) {
      if ([...valda].filter(id => klipp.find(x => x.id === id).typ === t).length >= kvotFor(t)) break
      if ((perK[k.konto] ?? 0) >= tak) continue
      perK[k.konto] = (perK[k.konto] ?? 0) + 1
      valda.add(k.id)
    }
  }
  // Jämför med det automatiska urvalet innan de egna besluten får företräde.
  const bedomda = klipp.filter(k => ['med', 'inte'].includes(bedomningar[k.id]?.beslut))
  const overens = bedomda.filter(k => (bedomningar[k.id].beslut === 'med') === valda.has(k.id)).length
  const osakra = klipp.filter(k => bedomningar[k.id]?.beslut === 'osaker').length
  for (const k of klipp) {
    const beslut = bedomningar[k.id]?.beslut
    if (beslut === 'med') valda.add(k.id)
    if (beslut === 'inte') valda.delete(k.id)
    k.valt = valda.has(k.id)
    k.nasta = k.valt ? (k.grund === 'sallning' ? 'analysera' : 'rekonstruera') : null
    if (beslut === 'med' || beslut === 'inte') k.skal.unshift('bedömd av dig')
    else if (!k.valt && k.lamplig < 0.4) k.skal.unshift('passar inte träningsdatan')
    else if (!k.valt) k.skal.unshift('kvoten för typen eller kontot full')
  }
  const ut = { skapad: new Date().toISOString(), mal: MAL, kvotPerTyp: kvot, saknar, typer: Object.fromEntries(typer.map(t => [t, { klipp: klipp.filter(k => k.typ === t).length, valda: klipp.filter(k => k.typ === t && k.valt).length }])), klipp: klipp.sort((a, b) => b.poang - a.poang) }
  fs.mkdirSync(path.join(DATA, 'bank'), { recursive: true })
  fs.writeFileSync(path.join(DATA, 'bank', 'urval.json'), JSON.stringify(ut, null, 1))
  console.log(`Överensstämmelse med automatiskt urval: ${bedomda.length ? `${overens}/${bedomda.length} (${Math.round(100 * overens / bedomda.length)} %)` : 'inga tydliga bedömningar ännu'} · ${osakra} osäkra räknas inte`)
  console.log(`${klipp.length} klipp (${saknar.analys} utan lokal analys, ${saknar.sallning} varken analys eller sållning, ${saknar.typ} utan typ) → ${valda.size} valda, ${klipp.filter(k => k.nasta === 'analysera').length} ska analyseras`)
  for (const [t, v] of Object.entries(ut.typer)) console.log(`  ${t}: ${v.valda} av ${v.klipp}`)
}
