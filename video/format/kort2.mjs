// Formatkort v2 på video via Lovable. Med --kontext får modellen kontots övriga klipp, från
// sållningens enradsbeskrivningar, så att rollen i mixen och personan som röd tråd kan bedömas
// mot kontot (tes H15).
//
//   node format/kort2.mjs [--modell google/gemini-3.1-pro-preview] [--kontext] [--tagg x] [--urval …]
// Resultat: data/format/v2[-kontext]-<modell>[-<tagg>]/<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { schema, prompt } from './v2.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MODELL = varde('--modell', 'google/gemini-3.1-pro-preview')
const KONTEXT = args.includes('--kontext')
const TAGG = varde('--tagg', '')
const PAR = Number(varde('--par', 8))
const URVAL = varde('--urval', path.join(DATA, 'format', 'kalib', 'urval.json'))
process.env.LOVABLE_MODELL = MODELL
const { analyseraVideo } = await import('../typer/lovable.mjs')

const namn = `v2${KONTEXT ? '-kontext' : ''}-${MODELL.split('/').pop()}${TAGG ? `-${TAGG}` : ''}`
const UT = path.join(DATA, 'format', namn)
fs.mkdirSync(UT, { recursive: true })

// Kontots övriga sållade klipp, högst 20, i fast ordning (efter id) så att körningar går att jämföra.
const SALLNING = path.join(DATA, 'bank', 'sallning')
const allaSallade = fs.readdirSync(SALLNING)
function kontext(konto, id) {
  const egna = allaSallade.filter(f => f.startsWith(`${konto}-`) && f !== `${id}.json`).sort().slice(-20)
  if (!egna.length) return null
  return egna.map(f => { const x = JSON.parse(fs.readFileSync(path.join(SALLNING, f), 'utf8')); return `- ${x.typ}: ${x.innehall}` }).join('\n')
}

const urval = JSON.parse(fs.readFileSync(URVAL, 'utf8'))
let i = 0
await Promise.all(Array.from({ length: Math.min(PAR, urval.length) }, async () => {
  while (i < urval.length) {
    const k = urval[i++]
    const ut = path.join(UT, `${k.id}.json`)
    if (fs.existsSync(ut)) continue
    const ktx = KONTEXT ? kontext(k.konto, k.id) : null
    try {
      const t0 = Date.now()
      const r = await analyseraVideo({ fil: k.fil, prompt: prompt(k.konto, ktx), schema, temperatur: 0.2 })
      fs.writeFileSync(ut, JSON.stringify({ id: k.id, konto: k.konto, modell: r.modell, kontext: ktx ? ktx.split('\n').length : 0, tokens: r.usage?.total_tokens, ms: Date.now() - t0, ...r.data }, null, 1))
    } catch (e) { console.warn(`${k.id}: ${e.message.slice(0, 300)}`) }
  }
}))
console.log(`${namn}: ${fs.readdirSync(UT).length}/${urval.length}`)
