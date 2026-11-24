// E24 (17 nov 2026): neutral logg utan tankar, tre läsningar vid hög temperatur. data/format/e24/forregistrering.json
//   LOVABLE_KONTO=beacon node format/e24.mjs [--prov 1,2,3] [--par 6]
// Resultat: data/format/e24/p<n>/<id>.json
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'

const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PROV = varde('--prov', '1,2,3').split(','), PAR = Number(varde('--par', 6))
const E = path.join(DATA, 'format', 'e24'), ids = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'e23', 'ids.json'), 'utf8'))
const liten = id => path.join(os.homedir(), 'Downloads', 'letrend-e13', `${id}.mp4`)
const f = (n, beskr) => ({ type: 'string', maxLength: n, ...(beskr ? { description: beskr } : {}) })
const schema = { type: 'object', required: ['logg'], properties: { logg: { type: 'array', items: { type: 'object', required: ['t', 'vem', 'gor', 'med', 'sags'], properties: {
  t: { type: 'integer' }, vem: f(20), gor: f(24), med: f(24), sags: f(140),
} } } } }
const PROMPT = 'Logg över klippet. En rad per sak som syns eller hörs, med sekund. Fält får vara tomma.'
const jobb = PROV.flatMap(p => ids.filter(id => !fs.existsSync(path.join(E, `p${p}`, `${id}.json`))).map(id => ({ p, id })))
for (const p of PROV) fs.mkdirSync(path.join(E, `p${p}`), { recursive: true })
console.log(`${jobb.length} läsningar, ${PAR} samtidigt`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => { while (i < jobb.length) { const { p, id } = jobb[i++]; try {
  const r = await beaconDelar({ modell: 'google/gemini-3.8-flash', schema, temperatur: 1.3, extra: { thinkingConfig: { thinkingBudget: 0 } }, delar: [{ fil: liten(id) }, { text: PROMPT }] })
  fs.writeFileSync(path.join(E, `p${p}`, `${id}.json`), JSON.stringify({ id, prov: p, ...r.data })); ny++
} catch (e) { fel++ } } }))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.usd.toFixed(2)} USD`)
