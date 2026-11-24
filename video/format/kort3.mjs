// Formatkort v3 på video via Lovable.
//   node format/kort3.mjs [--exempel] [--tagg x] [--modell google/gemini-3.1-pro-preview] [--urval …]
// --exempel: ägarens omdömen om klipp 1–20 ligger i prompten (tes H19).
// Resultat: data/format/v3[-exempel]-<modell>[-<tagg>]/<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { schema, prompt } from './v3.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MODELL = varde('--modell', 'google/gemini-3.1-pro-preview')
const EXEMPEL = args.includes('--exempel')
const TAGG = varde('--tagg', '')
const PAR = Number(varde('--par', 8))
const URVAL = varde('--urval', path.join(DATA, 'format', 'kalib', 'urval.json'))
process.env.LOVABLE_MODELL = MODELL
const { analyseraVideo } = await import('../typer/lovable.mjs')

const namn = `v3${EXEMPEL ? '-exempel' : ''}-${MODELL.split('/').pop()}${TAGG ? `-${TAGG}` : ''}`
const UT = path.join(DATA, 'format', namn)
fs.mkdirSync(UT, { recursive: true })

const urval = JSON.parse(fs.readFileSync(URVAL, 'utf8'))
let i = 0
await Promise.all(Array.from({ length: Math.min(PAR, urval.length) }, async () => {
  while (i < urval.length) {
    const k = urval[i++]
    const ut = path.join(UT, `${k.id}.json`)
    if (fs.existsSync(ut)) continue
    try {
      const t0 = Date.now()
      const r = await analyseraVideo({ fil: k.fil, prompt: prompt(k.konto, EXEMPEL), schema, temperatur: 0.2 })
      fs.writeFileSync(ut, JSON.stringify({ id: k.id, nr: k.nr, konto: k.konto, modell: r.modell, exempel: EXEMPEL, tokens: r.usage?.total_tokens, ms: Date.now() - t0, ...r.data }, null, 1))
    } catch (e) { console.warn(`${k.id}: ${e.message.slice(0, 300)}`) }
  }
}))
console.log(`${namn}: ${fs.readdirSync(UT).length}/${urval.length}`)
