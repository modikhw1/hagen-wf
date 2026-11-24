// Jev-prov på ryggradens yta. Ett Choice per mening bland hela drag. Tre omgångar, i tur och ordning.
// Meningar och facit låses (hash) före första anropet. Nyckeln läses som i app/kalibrering/jev.mjs och skrivs aldrig ut.
// Tak: 80 anrop. Kör: node jevprov.mjs
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const FIL = process.argv[2] ?? 'jev_meningar.json'
const UT = path.join(HERE, 'ut', process.argv[3] ?? 'jevprov')
const TAK = 80, OMGANGAR = 3, PRIS = 0.04 / 1e6
const m = JSON.parse(fs.readFileSync(path.join(HERE, FIL), 'utf8'))
const yta = JSON.parse(fs.readFileSync(path.join(HERE, 'ut', `jev_${m.klipp}.json`), 'utf8'))
const drag = Object.keys(yta.questions.drag.criteria)
for (const x of m.meningar) for (const f of x.facit) if (!drag.includes(f)) throw new Error(`facit ${f} finns inte bland dragen (${x.id})`)

const env = fs.readFileSync(path.join(HERE, '..', '..', 'app', '.env.local'), 'utf8').split(/\r?\n/).find(l => l.startsWith('TYPESAFE_API_KEY='))
const key = process.env.TYPESAFE_API_KEY ?? env?.slice('TYPESAFE_API_KEY='.length).trim()
if (!key) throw new Error('ingen nyckel')

fs.mkdirSync(UT, { recursive: true })
const las = crypto.createHash('sha256').update(JSON.stringify({ m, yta })).digest('hex')
fs.writeFileSync(path.join(UT, 'forregistrering.json'), JSON.stringify({ last: new Date().toISOString(), hash: las, meningar: m.meningar.length, drag: drag.length, omgangar: OMGANGAR,
  prognos: process.argv[4] ?? 'Fable: minst 16 av 22 rätt per omgång, samma svar i alla tre omgångar för minst 18 av 22. Svårast väntas ingen_passar och gränsen mellan manus och byt_produkt.' }, null, 1))

let anrop = 0, tokens = 0
const rader = []
for (let o = 1; o <= OMGANGAR; o++) {
  for (const x of m.meningar) {
    if (++anrop > TAK) throw new Error('tak nått')
    const t0 = performance.now()
    const r = await fetch('https://api.typesafe.ai/v1/systemone', { method: 'POST', headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'jev-latest', state: `${yta.state}\n\nCM skriver: "${x.text}"`, questions: yta.questions }) })
    const ms = performance.now() - t0
    if (!r.ok) throw new Error(`Jev ${r.status}: ${(await r.text()).slice(0, 200)}`)
    const j = await r.json(), a = j.answers.drag
    tokens += j.usage?.input_tokens ?? 0
    const p = Object.entries(a.probabilities ?? {}).sort((u, v) => v[1] - u[1])
    rader.push({ omgang: o, id: x.id, text: x.text, facit: x.facit, val: a.choice, ratt: x.facit.includes(a.choice), konfidens: a.confidence,
      marginal: p.length > 1 ? +(p[0][1] - p[1][1]).toFixed(2) : null, tvaa: p[1]?.[0], ms: Math.round(ms), modell: j.model })
  }
}
fs.writeFileSync(path.join(UT, 'svar.json'), JSON.stringify(rader, null, 1))
const per = id => rader.filter(r => r.id === id)
const sorterad = rader.map(r => r.ms).sort((a, b) => a - b)
const res = { hash: las, anrop, input_tokens: tokens, usd: +(tokens * PRIS).toFixed(5), modell: rader[0].modell,
  ratt_per_omgang: [1, 2, 3].map(o => rader.filter(r => r.omgang === o && r.ratt).length),
  stabila: m.meningar.filter(x => new Set(per(x.id).map(r => r.val)).size === 1).length,
  median_ms: sorterad[sorterad.length >> 1], p90_ms: sorterad[Math.floor(sorterad.length * 0.9)],
  marginal_ratt: +(rader.filter(r => r.ratt).reduce((s, r) => s + r.marginal, 0) / Math.max(1, rader.filter(r => r.ratt).length)).toFixed(2),
  marginal_fel: +(rader.filter(r => !r.ratt).reduce((s, r) => s + r.marginal, 0) / Math.max(1, rader.filter(r => !r.ratt).length)).toFixed(2),
  fel: m.meningar.map(x => ({ id: x.id, text: x.text, facit: x.facit, val: per(x.id).map(r => r.val) })).filter(x => x.val.some(v => !x.facit.includes(v))) }
fs.writeFileSync(path.join(UT, 'resultat.json'), JSON.stringify(res, null, 1))
console.log(JSON.stringify(res, null, 1))
