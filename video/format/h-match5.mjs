// Harness v5 steg 4 (4 nov 2026): matchning som FORTSÄTTNING på kundens linje, med klippets grundvärde
// först. Ersätter v0:s grindar och mjuka passform (h-match.mjs), där luckor gav poäng.
//
// Poängen är handsatt ur doktrinen (format/doktrin.mjs), inte anpassad till ägarens svar:
//   grund   = premiss + värde utan efterarbete + krok + vändning, minus hyllan ute och Instagram-språk
//   linje   = samma strategi som kunden, kantighet (strängare uppåt), tempo, klippberoende,
//             personen som fokus kräver en frontfigur med fokus, tilltal där kunden aldrig talar till kameran
//   forlaga = bilder bundna till en annan sorts verksamhet
// Grindar bara för det omöjliga: fler personer än kunden har (+1).
// Med --pro bedömer Pro som CM (doktrinen, linjen och korten) kandidaterna 1–5.
//
//   node format/h-match5.mjs [--pro] [--konton a,b]
// Resultat: data/format/harness/match5/<konto>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
import { LETREND, GRUNDVARDE, LINJE } from './doktrin.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const H = path.join(DATA, 'format', 'harness'), UT = path.join(H, 'match5')
fs.mkdirSync(UT, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const kort = Object.fromEntries(fs.readdirSync(path.join(H, 'v5')).map(f => [f.replace(/\.json$/, ''), las(path.join(H, 'v5', f))]))
const konton = varde('--konton') ? varde('--konton').split(',') : fs.readdirSync(path.join(H, 'linje')).map(f => f.replace(/\.json$/, ''))

const KANT = { familjar: 0, lekfull: 1, kantig: 2, vuxen: 3 }, TEMPO = { lugnt: 0, medel: 1, hogt: 2 }, KB = { lite: 0, en_del: 1, mycket: 2 }
export function grund(c) {
  const g = c.grundvarde, d = []
  let p = { stark: 3, medel: 2, svag: 1, ingen: 0 }[g.premiss]; d.push(`premiss ${g.premiss}`)
  p += { ja: 1, delvis: 0.5, nej: 0 }[g.utan_efterarbete]; if (g.utan_efterarbete !== 'ja') d.push(`utan efterarbete: ${g.utan_efterarbete}`)
  p += { stark: 0.5, svag: 0.25, ingen: 0 }[g.krok]
  if (g.vandning) p += 0.5
  if (g.hylla === 'ute') { p -= 2; d.push('hyllan ute') } else if (g.hylla === 'capcut_referens') { p -= 1; d.push('capcut-referens') }
  if (c.sprak.plattform !== 'tiktok') { p -= 0.5; d.push(`plattform ${c.sprak.plattform}`) }
  return { p, d }
}
export function linje(c, L) {
  const s = c.sprak, d = []; let p = 0
  // Kärnklipp bär överallt (doktrinen), så strategin väger lätt för dem och tungt för mitten och situation.
  // Justerat en gång efter att pizzeriamums utvecklingsdata setts (sketcher 4–4,5 hos ett tilltalskonto).
  const vikt = c.grundvarde.hylla === 'karna' ? 0.5 : 2
  if (s.strategi === L.strategi) { p += vikt; d.push(`samma strategi (${s.strategi})`) } else if (s.strategi === L.strategi_sekundar) { p += vikt / 2; d.push(`kundens andra strategi (${s.strategi})`) } else d.push(`annan strategi (${s.strategi} mot ${L.strategi})`)
  const dk = KANT[s.kantighet] - KANT[L.kantighet]
  // Justering 2 (efter pass 4–5 inom klipp): ägaren sänkte aldrig ett klipp för att det var snällare än
  // kunden, bara för att det var kantigare. Ett lugnare klipp hos en snabbare kund är däremot en miss
  // ("too simple ... to fit within the general flow", kebabbabes).
  if (dk > 0) { const straff = s.kantighet === 'lekfull' ? 0.25 : dk; p -= straff; d.push(`kantigare än kunden (${s.kantighet} mot ${L.kantighet})`) }
  const dt = TEMPO[L.tempo] - TEMPO[s.tempo]
  if (dt > 0) { p -= 0.75 * dt; d.push(`lugnare än kunden (${s.tempo} mot ${L.tempo})`) } else if (dt < 0) { p += 0.25 * dt; d.push(`snabbare än kunden (${s.tempo} mot ${L.tempo})`) }
  if (s.klippberoende === 'mycket') { p -= 1; d.push('värdet sitter i klippningen') }
  const dkb = KB[s.klippberoende] - KB[L.klippberoende]; if (dkb > 0) p -= 0.5 * dkb
  if (s.person === 'fokus') {
    // Justering 2: en frontfigur räcker (blackstonesteakhouse 4,5 med en servitris som behållare). Att
    // kunden sällan talar till kameran fångas av tilltalsregeln nedan.
    if (!L.frontfigurer?.length) { p -= 2; d.push('kräver en frontfigur, kunden har ingen') } else d.push('kunden har en frontfigur')
  }
  const k = L.klipp?.length || 10
  if (s.tilltal === 'till_kamera' && L.tilltal_antal / k < 0.2) { p -= 1; d.push('tilltal till kameran, som kunden sällan gör') }
  // "Ingen förväntar sig stordåd av en sketch": ovan personal är ett litet hinder, inte en grind.
  if (s.tilltal === 'spelad_scen' && L.personal_spelar <= 1 && c.krav.skadespel >= 3) { p -= 0.5; d.push('spelad scen som kräver timing, kundens personal spelar sällan') }
  return { p, d }
}
export function forlaga(c, L) {
  const d = []; let p = 0
  if (c.forlaga.bundna_bilder === 'nastan_alla') { p -= 1; d.push(`bilderna bundna till ${c.forlaga.bunden_till}`) } else if (c.forlaga.bundna_bilder === 'halften') p -= 0.25
  if (c.krav?.verksamheter?.length && L.verksamhet && !c.krav.verksamheter.includes(L.verksamhet) && c.forlaga.bundna_bilder !== 'fa') { p -= 0.5; d.push(`förlagan gjord för ${c.krav.verksamheter.join('/')}`) }
  return { p, d }
}
export function poang(c, L) {
  const g = grund(c), l = linje(c, L), f = forlaga(c, L)
  const mojlig = !(c.krav?.personer_min > (L.max_personer ?? 2) + 1)
  return { id: c.id, mojlig, grund: g.p, linje: l.p, forlaga: f.p, total: g.p + l.p + f.p, skal: [...g.d, ...l.d, ...f.d] }
}

const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const kort_ = (t, n) => (t ?? '').length > n ? t.slice(0, n - 1) + '…' : t
const kompakt = c => ({ helhet: kort_(c.helhet, 260), karna: c.karna, premiss: c.grundvarde.premiss, bars_av: c.grundvarde.bars_av, klumpigt: kort_(c.grundvarde.klumpigt, 160), utan_efterarbete: c.grundvarde.utan_efterarbete, hylla: c.grundvarde.hylla, sprak: c.sprak, bunden_till: c.forlaga.bunden_till, personer_min: c.krav.personer_min, skadespel: c.krav.skadespel })
const linjeKompakt = L => ({ linje: L.linje, strategi: L.strategi, strategi_sekundar: L.strategi_sekundar, kantighet: L.kantighet, tempo: L.tempo, klippberoende: L.klippberoende, tilltal_i_klipp: `${L.tilltal_antal} av ${L.klipp.length}`, frontfigurer: L.frontfigurer.map(({ etikett, funktion, styrka }) => ({ etikett, funktion, styrka })), personal_spelar: L.personal_spelar, max_personer: L.max_personer, format: L.format.map(f => f.namn), verksamhet: L.verksamhet, segment: L.segment, produkter: L.produkter, sjalvbild: L.sjalvbild, sticker_ut: L.sticker_ut, kursandring: L.kursandring })

async function proBedom(konto, L, kand) {
  const koder = kand.map((c, i) => ({ kod: `K${i + 1}`, id: c.id }))
  const schema = obj({ bedomning: { type: 'array', minItems: kand.length, maxItems: kand.length, items: obj({ kod: s('Klippets kod.', koder.map(k => k.kod)), passform: n(1, 5, 'Hur väl klippet passar kunden som nästa klipp. 1 = passar inte alls, 3 = går men känns annorlunda, 5 = självklart nästa klipp.'), rek: s('Rekommendation: som_den_ar, andringar (praktiska byten) eller nej.', ['som_den_ar', 'andringar', 'nej']), skal: s('Varför, en mening, med koppling till klippets värde och kundens linje.') }) } })
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Du är content manager på LeTrend och ska bedöma hur väl varje biblioteksklipp passar kunden @${konto} som nästa klipp.

${LETREND}

${GRUNDVARDE}

${LINJE}

Kundens linje:
${JSON.stringify(linjeKompakt(L))}

Kandidater:
${kand.map((c, i) => `K${i + 1} ${JSON.stringify(kompakt(c))}`).join('\n')}

Bedöm först klippets eget värde och sedan om det fortsätter kundens linje. Ett starkt klipp på kundens eget språk passar bäst. Ett klipp som fyller en lucka men bryter linjen passar sämre. Svara på svenska.`
  if (prompt.length > 19800) throw new Error(`prompten är för lång (${prompt.length})`)
  const r = await analyseraVideo({ fil: path.join(DATA, 'format', 'tom.mp4'), prompt, schema, temperatur: 0.2, modell: 'google/gemini-3.1-pro-preview' })
  return { tokens: r.usage?.total_tokens, bedomning: r.data.bedomning.map(x => ({ ...x, id: koder.find(k => k.kod === x.kod)?.id })) }
}

if (process.argv[1] && import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const valid = fs.existsSync(path.join(H, 'validering', 'urval.json')) ? las(path.join(H, 'validering', 'urval.json')) : {}
  for (const konto of konton) {
    const L = las(path.join(H, 'linje', `${konto}.json`))
    const res = Object.values(kort).map(c => poang(c, L)).sort((a, b) => b.total - a.total)
    const ut = { konto, kort: Object.keys(kort).length, resultat: res }
    if (args.includes('--pro')) {
      // Pro bedömer de bedömda klippen (för utvärdering) plus de bästa efter poängen, högst 20.
      const bedomda = (valid[konto]?.klipp ?? []).map(k => k.id).filter(id => kort[id])
      // Bryggan tar högst 20 000 tecken: de bedömda plus de bästa efter poängen, så många som ryms (högst 12).
      let ids = [...new Set([...bedomda, ...res.filter(r => r.mojlig).map(r => r.id)])].slice(0, 12), p
      for (;;) { try { p = await proBedom(konto, L, ids.map(id => kort[id])); break } catch (e) { if (!/för lång/.test(e.message) || ids.length <= bedomda.length) throw e; ids = ids.slice(0, -1) } }
      ut.pro = p.bedomning; ut.pro_tokens = p.tokens
    }
    fs.writeFileSync(path.join(UT, `${konto}.json`), JSON.stringify(ut, null, 1))
    console.log(`${konto}: topp ${res.slice(0, 5).map(r => `${r.total.toFixed(1)}:${kort[r.id].konto}`).join(', ')}${ut.pro ? `; Pro ${ut.pro_tokens} tokens` : ''}`)
  }
}
