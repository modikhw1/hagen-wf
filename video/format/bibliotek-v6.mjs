// Bibliotekskandidater v6 (4 nov 2026): ur E6 och E6-R (597 klipp ägaren inte sett), sorterade på de två
// måtten. Kärnhyllan i v0 var för liten (samma sketcher hos alla kunder). Ingen urvalsregel använder utfallen.
//   node format/bibliotek-v6.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { grund } from './h-match5.mjs'
import { nytta6 } from './h-v6.mjs'
const F = path.join(DATA, 'format'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const bib = new Set(las(path.join(F, 'harness', 'urval.json')).bibliotek.map(k => k.id))
const k = ['e6', 'e6r'].flatMap(d => fs.readdirSync(path.join(F, d, 'kort')).map(f => las(path.join(F, d, 'kort', f)))).filter(c => !bib.has(c.id))
const rad = c => ({ id: c.id, url: c.url, konto: c.konto, hylla: c.grundvarde.hylla, strategi: c.sprak.strategi, grund: grund(c).p, nytta6: +nytta6(c).toFixed(2), karna: c.karna })
const alla = k.map(rad)
const karna = alla.filter(x => x.hylla === 'karna' && x.grund >= 5).sort((a, b) => b.grund + b.nytta6 - a.grund - a.nytta6)
const mitten = alla.filter(x => x.hylla === 'mitten' && x.grund >= 3.5).sort((a, b) => b.nytta6 - a.nytta6)
const situation = alla.filter(x => x.hylla === 'situation').sort((a, b) => b.grund - a.grund)
fs.writeFileSync(path.join(F, 'harness', 'bibliotek-v6-kandidater.json'), JSON.stringify({ kalla: 'E6 + E6-R, formatkort v5 med Flash 3.8', karna, mitten, situation }, null, 1))
const st = l => { const r = {}; for (const x of l) r[x.strategi] = (r[x.strategi] ?? 0) + 1; return JSON.stringify(r) }
console.log(`${alla.length} klipp. Kärnkandidater (kärna, grund ≥ 5): ${karna.length} från ${new Set(karna.map(x => x.konto)).size} konton ${st(karna)}`)
console.log(`Mittenkandidater (grund ≥ 3,5): ${mitten.length} ${st(mitten)}. Situation: ${situation.length}`)
console.log('Hyllorna i hela urvalet:', JSON.stringify(alla.reduce((r, x) => (r[x.hylla] = (r[x.hylla] ?? 0) + 1, r), {})))
