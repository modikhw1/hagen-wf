// Kort + kundlinje -> scenplan (output av scenplan(c, L) i video/format/h-scener.mjs). Inga nätanrop.
//   node scen/3d/kontrakt/bro/gor_scenplan.mjs <kort.json> <linje.json> <ut.json>
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
const [kort, linje, ut] = process.argv.slice(2)
if (!kort || !linje || !ut) { console.error('användning: node gor_scenplan.mjs <kort.json> <linje.json> <ut.json>'); process.exit(2) }
if (fs.existsSync(ut)) { console.error('utfilen finns redan: ' + ut); process.exit(2) }
const rot = path.resolve(import.meta.dirname, '../../../..')
const { scenplan } = await import(pathToFileURL(path.join(rot, 'video/format/h-scener.mjs')).href)
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const plan = scenplan(las(kort), las(linje))
fs.mkdirSync(path.dirname(ut), { recursive: true })
fs.writeFileSync(ut, JSON.stringify(plan, null, 1) + '\n')
console.log(plan.beats.map(b => `${b.nr}:${b.atgard}`).join(' ') + ' | ' + plan.sammanfattning)
