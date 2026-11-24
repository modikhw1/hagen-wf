// Analys av pass 8 enligt data/format/harness/pass8/forregistrering.json.
// Ägarens svar kodas i data/format/harness/pass8/agare.json:
//   { "val": { "<kund>": 1 | 2 },                          // vilken version ägaren hellre skickar
//     "andra_skickas": { "<kund>": true | false },
//     "scener": { "<kund>": { "<beat nr>": "behall" | "andra" } },  // ägarens val per scen
//     "fel_pastaenden": { "<kund>": ["påstående", ...] } }   // punkter under "att bekräfta" som är fel
//   node format/h-pass8-analys.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const P = path.join(DATA, 'format', 'harness', 'pass8'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const R = las(path.join(P, 'forregistrering.json')), A = las(path.join(P, 'agare.json'))
const v5 = R.rader.filter(r => A.val?.[r.kund]).filter(r => (A.val[r.kund] === 1 ? r.version1 : r.version2) === 'v5').length
const n = R.rader.filter(r => A.val?.[r.kund]).length
console.log(`HP8a ägaren föredrar v5 hos ${v5} av ${n} kunder (låst: minst 4 av 6)`)
let lika = 0, tot = 0
for (const r of R.rader) { const s = A.scener?.[r.kund]; if (!s) continue; for (const b of r.scenplan) { const agare = s[b.nr]; if (!agare) continue; const plan = ['behall', 'fritt'].includes(b.atgard) ? 'behall' : 'andra'; tot++; if (agare === plan) lika++ } }
console.log(`HP8b scenplanen stämmer med ägaren för ${lika} av ${tot} beats (${tot ? Math.round(100 * lika / tot) : 0} %, låst: minst 70 %)`)
const alla = Object.values(A.fel_pastaenden ?? {}).flat().length
console.log(`HP8c påståenden under "att bekräfta" som är fel: ${alla} (fördelat: ${JSON.stringify(Object.fromEntries(Object.entries(A.fel_pastaenden ?? {}).map(([k, v]) => [k, v.length])))})`)
console.log(`den andra versionen skickas också: ${Object.values(A.andra_skickas ?? {}).filter(Boolean).length} av ${Object.keys(A.andra_skickas ?? {}).length}`)
