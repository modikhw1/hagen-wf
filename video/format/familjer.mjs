// Ägarens formatfamiljer på hela banken, klassade på text ur sållningen (6 nov 2026).
// Förregistrering: data/format/familjer/forregistrering.json (definitionerna är låsta).
//   LOVABLE_KONTO=5 node format/familjer.mjs [--max <antal satser>] [--samtidigt 8]
// Resultat: data/format/familjer/sats/<n>.json  ({ id: familj }), sammanslaget i familjer.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'

const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const F = path.join(DATA, 'format', 'familjer'), SATS = path.join(F, 'sats'), SAL = path.join(DATA, 'bank', 'sallning')
fs.mkdirSync(SATS, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const REG = las(path.join(F, 'forregistrering.json')), FAM = Object.keys(REG.familjer)
const MODELL = process.env.FAMILJ_MODELL ?? 'google/gemini-3.8-flash', STORLEK = 60

// Prioritet: kunderna i pass 4–6 och deras kandidatklipp först
const H = path.join(DATA, 'format', 'harness')
const prio = new Set()
const U = las(path.join(H, 'validering', 'urval.json'))
for (const [k, v] of Object.entries(U)) { prio.add(k); v.klipp.forEach(c => prio.add(c.id)) }
for (const [k, ids] of Object.entries(las(path.join(H, 'pass6', 'ordning.json')))) { prio.add(k); ids.forEach(id => prio.add(id)) }
for (const f of fs.readdirSync(path.join(H, 'linje'))) prio.add(f.replace(/\.json$/, ''))

const alla = fs.readdirSync(SAL).map(f => f.replace(/\.json$/, '')).sort()
const vikt = id => prio.has(id) ? 0 : prio.has(id.replace(/-\d+$/, '')) ? 1 : 2
alla.sort((a, b) => vikt(a) - vikt(b) || a.localeCompare(b))
const satser = []; for (let i = 0; i < alla.length; i += STORLEK) satser.push(alla.slice(i, i + STORLEK))

const schema = { type: 'object', properties: { klipp: { type: 'array', items: { type: 'object', properties: { nr: { type: 'integer' }, familj: { type: 'string', enum: FAM } }, required: ['nr', 'familj'], additionalProperties: false } } }, required: ['klipp'], additionalProperties: false }
const definitioner = Object.entries(REG.familjer).map(([k, v]) => `- ${k}: ${v}`).join('\n')

async function klassa(n) {
  const ut = path.join(SATS, `${n}.json`); if (fs.existsSync(ut)) return 0
  const ids = satser[n], rader = ids.map((id, i) => { const s = las(path.join(SAL, id + '.json')); return `${i + 1}. ${s.innehall} | typ ${s.typ} | ${s.skal ?? ''} | personer ${s.personer_max}, andel med person ${s.andel_med_person}, text_tung ${s.text_tung}, montage ${s.montage}, inne ${s.inne_i_verksamheten}` })
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Nedan beskrivs ${ids.length} TikTok-klipp från restauranger, barer och kaféer, ett per rad (en mening om innehållet, en grov typ, ett skäl om hur lätt det är att återskapa, och flaggor). Ge varje klipp exakt en formatfamilj ur listan. Välj den familj som bäst beskriver vad som bär klippet.

Familjer:
${definitioner}

Klipp:
${rader.join('\n')}`
  const r = await analyseraVideo({ fil: path.join(DATA, 'format', 'tom.mp4'), prompt, schema, temperatur: 0, modell: MODELL })
  const m = {}; for (const k of r.data.klipp) if (ids[k.nr - 1]) m[ids[k.nr - 1]] = k.familj
  fs.writeFileSync(ut, JSON.stringify({ modell: r.modell, tokens: r.usage?.total_tokens, familjer: m }))
  return r.usage?.total_tokens ?? 0
}

const max = +varde('--max', satser.length), samtidigt = +varde('--samtidigt', 8)
let nasta = 0, tokens = 0, klara = 0, fel = 0
async function arbetare() {
  while (nasta < Math.min(max, satser.length)) {
    const n = nasta++
    try { tokens += await klassa(n); klara++ } catch (e) { fel++; console.log(`sats ${n}: ${e.message.slice(0, 200)}`); if (/402|credit|payment/i.test(e.message)) { nasta = 1e9 } }
    if (klara % 10 === 0) console.log(`${klara} satser klara, ${tokens} tokens, ${fel} fel`)
  }
}
console.log(`${alla.length} klipp i ${satser.length} satser om ${STORLEK}, ${alla.filter(id => vikt(id) < 2).length} prioriterade, modell ${MODELL}`)
await Promise.all(Array.from({ length: samtidigt }, arbetare))
const allt = {}; for (const f of fs.readdirSync(SATS)) Object.assign(allt, las(path.join(SATS, f)).familjer)
fs.writeFileSync(path.join(F, 'familjer.json'), JSON.stringify(allt))
console.log(`klart: ${Object.keys(allt).length} klipp klassade, ${tokens} tokens denna körning, ${fel} fel`)
