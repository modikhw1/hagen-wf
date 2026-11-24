// Pass 6 (4 nov 2026): låst test av harnessen v5 med tre nya kunder och en korsad design.
//   4 delade klipp visas för alla tre kunderna (matchningen inom klipp), valda där v5 spår störst skillnad
//   mellan kunderna, bland klipp med grundvärde ≥ 1, med minst en sketch och en visning eller ett tilltal.
//   1 eget klipp per kund: v5:s förstahandsval för kunden bland resten.
//   3 omtest: (kund, klipp) ur pass 4–5, för ägarens eget brus.
// Poolen är biblioteket (Pro) och E6-urvalet (Flash) utom de klipp ägaren sett och kundens egna klipp.
// Prognoserna (v5 total och Pro som CM) låses i data/format/harness/pass6/forregistrering.json innan passet.
//   LOVABLE_KONTO=3 node format/h-pass6.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
import { poang } from './h-match5.mjs'
import { LETREND, GRUNDVARDE, LINJE } from './doktrin.mjs'

const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), P = path.join(H, 'pass6'); fs.mkdirSync(P, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const KUNDER = ['fratelli.stockhol', 'blubnan.liljeholm', 'cafepomflora']
const sett = new Set(fs.readFileSync(path.join(F, 'e5', 'ids.txt'), 'utf8').split(/\r?\n/).filter(Boolean))
const pool = {}
for (const [d, kalla] of [[path.join(H, 'v5'), 'bibliotek'], [path.join(F, 'e6', 'kort'), 'e6']]) for (const f of fs.readdirSync(d)) { const c = las(path.join(d, f)); if (!sett.has(c.id) && !pool[c.id]) pool[c.id] = { ...c, kalla_pool: kalla } }
const L = Object.fromEntries(KUNDER.map(k => [k, las(path.join(H, 'linje', `${k}.json`))]))
const kand = Object.values(pool).filter(c => !KUNDER.includes(c.konto))
const tab = kand.map(c => { const p = Object.fromEntries(KUNDER.map(k => [k, poang(c, L[k])])); const t = KUNDER.map(k => p[k].total); return { c, p, grund: p[KUNDER[0]].grund, spann: Math.max(...t) - Math.min(...t), mojlig: KUNDER.every(k => p[k].mojlig) } })

// 4 delade: störst spann bland grund ≥ 1, olika avsändare, minst en sketchvarld och en visning/tilltal.
const delade = []
const kv = tab.filter(r => r.grund >= 1 && r.mojlig).sort((a, b) => b.spann - a.spann)
const tag = pred => { const r = kv.find(r => pred(r) && !delade.includes(r) && !delade.some(d => d.c.konto === r.c.konto)); if (r) delade.push(r) }
tag(r => r.c.sprak.strategi === 'sketchvarld'); tag(r => ['visning', 'tilltal', 'premium_stamning'].includes(r.c.sprak.strategi))
while (delade.length < 4) tag(() => true)
// 1 eget per kund: högst total bland resten, olika avsändare.
const egna = {}
for (const k of KUNDER) { const r = tab.filter(r => !delade.includes(r) && !Object.values(egna).includes(r) && r.p[k].mojlig && !delade.some(d => d.c.konto === r.c.konto)).sort((a, b) => b.p[k].total - a.p[k].total)[0]; egna[k] = r }
// Omtest ur pass 4–5 (spridda betyg).
const omtest = [{ konto: 'babulsofficial', pos: 4 }, { konto: 'chickenstreet.canada', pos: 2 }, { konto: 'kebabbabes', pos: 1 }]

const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const kompakt = c => ({ helhet: c.helhet, karna: c.karna, premiss: c.grundvarde.premiss, bars_av: c.grundvarde.bars_av, utan_efterarbete: c.grundvarde.utan_efterarbete, hylla: c.grundvarde.hylla, sprak: c.sprak, bunden_till: c.forlaga.bunden_till })
async function proCM(konto, klipp) {
  const Lk = L[konto], koder = klipp.map((_, i) => `K${i + 1}`)
  const schema = obj({ bedomning: { type: 'array', minItems: klipp.length, maxItems: klipp.length, items: obj({ kod: s('', koder), passform: n(1, 5, 'Hur väl klippet passar kunden som nästa klipp.'), skal: s('Varför, en mening.') }) } })
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Du är content manager på LeTrend och bedömer hur väl varje biblioteksklipp passar kunden @${konto} som nästa klipp.\n\n${LETREND}\n\n${GRUNDVARDE}\n\n${LINJE}\n\nKundens linje:\n${JSON.stringify({ linje: Lk.linje, strategi: Lk.strategi, strategi_sekundar: Lk.strategi_sekundar, kantighet: Lk.kantighet, tempo: Lk.tempo, frontfigurer: Lk.frontfigurer.map(({ etikett, funktion, styrka }) => ({ etikett, funktion, styrka })), personal_spelar: Lk.personal_spelar, verksamhet: Lk.verksamhet, segment: Lk.segment, produkter: Lk.produkter, sjalvbild: Lk.sjalvbild, sticker_ut: Lk.sticker_ut })}\n\nKandidater:\n${klipp.map((c, i) => `K${i + 1} ${JSON.stringify(kompakt(c))}`).join('\n')}\n\nBedöm först klippets eget värde och sedan om det fortsätter kundens linje. Svara på svenska.`
  const r = await analyseraVideo({ fil: path.join(F, 'tom.mp4'), prompt, schema, temperatur: 0.2, modell: 'google/gemini-3.1-pro-preview' })
  return Object.fromEntries(r.data.bedomning.map(x => [klipp[koder.indexOf(x.kod)].id, { passform: x.passform, skal: x.skal }]))
}
const reg = path.join(P, 'forregistrering.json')
if (fs.existsSync(reg)) { console.log('pass 6 är redan låst'); process.exit(0) }
const prognos = {}
for (const k of KUNDER) {
  const klipp = [...delade.map(r => r.c), egna[k].c]
  const pro = await proCM(k, klipp)
  prognos[k] = klipp.map(c => ({ id: c.id, url: c.url, avsandare: c.konto, kalla: c.kalla_pool, typ: delade.some(d => d.c.id === c.id) ? 'delad' : 'egen', v5_total: +poang(c, L[k]).total.toFixed(2), v5_grund: +poang(c, L[k]).grund.toFixed(2), skal: poang(c, L[k]).skal, pro_passform: pro[c.id]?.passform ?? null, pro_skal: pro[c.id]?.skal ?? null, karna: c.karna, helhet: c.helhet }))
  console.log(`${k}: ${prognos[k].map(x => `${x.typ[0]}:${x.avsandare} v5 ${x.v5_total} pro ${x.pro_passform}`).join(' | ')}`)
}
fs.writeFileSync(reg, JSON.stringify({
  last: new Date().toISOString() + ' (innan ägaren sett något klipp i pass 6)',
  kunder: KUNDER, delade: delade.map(r => r.c.id), egna: Object.fromEntries(KUNDER.map(k => [k, egna[k].c.id])), omtest, prognos,
  HP6a: 'v5 total korrelerar positivt med ägarens passform över de 15 nya paren (Spearman, ensidigt p < 0,05 med permutation).',
  HP6b: 'Inom de 4 delade klippen ordnar v5 total kunderna rätt i mer än hälften av paren med olika betyg från ägaren (teckentest).',
  HP6c: 'Pro som CM korrelerar positivt med ägarens passform över de 15 nya paren.',
  HP6d: 'Minst 2 av 3 anpassningar v5 bedöms som skicka som den är eller med små ändringar.',
  HP6e: 'Beskrivande: ägarens omtest av 3 par ur pass 4–5, avvikelse i betyg.',
}, null, 1))
console.log('låst:', reg)
