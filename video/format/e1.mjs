// E1 (3 nov 2026): vilka lager är verkliga? 30 kalibreringsklipp × 3 modeller × 3 promptformuleringar
// × 2 körningar med lagerschemat (format/lager.mjs). Analysen i format/e1-analys.mjs skiljer klippets
// varians från modellens, promptens och slumpens.
//
//   node format/e1.mjs [--par 24] [--modeller a,b,c]
// Resultat: data/format/e1/<modell>/p<prompt>-k<körning>/<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { schema, PROMPTER } from './lager.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PAR = Number(varde('--par', 24))
const MODELLER = varde('--modeller', 'google/gemini-3.1-pro-preview,google/gemini-3.8-flash,google/gemini-3.1-flash-lite').split(',')
const URVAL = varde('--urval', path.join(DATA, 'format', 'kalib', 'urval.json'))
const UT = path.join(DATA, 'format', 'e1')

const { analyseraVideo } = await import('../typer/lovable.mjs')
const urval = JSON.parse(fs.readFileSync(URVAL, 'utf8'))

// Alla jobb, blandade så att en modell eller prompt inte hamnar sist om något stoppar.
const jobb = []
for (const modell of MODELLER) for (let p = 0; p < PROMPTER.length; p++) for (let k = 1; k <= 2; k++) for (const kl of urval) {
  const fil = path.join(UT, modell.split('/').pop(), `p${p + 1}-k${k}`, `${kl.id}.json`)
  if (!fs.existsSync(fil)) jobb.push({ modell, p, kl, fil })
}
for (let i = jobb.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [jobb[i], jobb[j]] = [jobb[j], jobb[i]] }
console.log(`${jobb.length} anrop`)

let i = 0, ok = 0, fel = 0
const t0 = Date.now()
await Promise.all(Array.from({ length: PAR }, async () => {
  while (i < jobb.length) {
    const { modell, p, kl, fil } = jobb[i++]
    try {
      // Modellen väljs per anrop: lovable.mjs läser LOVABLE_MODELL vid import, så den skickas med här.
      const r = await analyseraVideo({ fil: kl.fil, prompt: PROMPTER[p](kl.konto), schema, temperatur: 0.2, modell })
      fs.mkdirSync(path.dirname(fil), { recursive: true })
      fs.writeFileSync(fil, JSON.stringify({ id: kl.id, nr: kl.nr, modell: r.modell, tokens: r.usage?.total_tokens, ...r.data }))
      ok++
    } catch (e) { fel++; console.warn(`${modell} p${p + 1} ${kl.id}: ${e.message.slice(0, 200)}`) }
    if ((ok + fel) % 60 === 0) console.log(`${ok + fel}/${jobb.length}: ${ok} ok, ${fel} fel, ${((Date.now() - t0) / 1000 / (ok + fel)).toFixed(2)} s/anrop`)
  }
}))
console.log(`klart: ${ok} ok, ${fel} fel`)
