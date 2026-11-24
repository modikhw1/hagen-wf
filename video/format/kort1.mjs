// Formatkort v1: bygger på ägarens svar 3 nov (karta/videoforandring/harness.md). Nytt mot v0:
// bärtestet (bär idén med en ovan person, vad den hänger på), visningsgrad och vad rätten bär,
// roll i serien, ton (självdistans, inside, varumärkesrisk) och förlust per verksamhetstyp
// i stället för överföringsbetyg och seriefältet, som inte skilde klippen åt i v0.
//
//   node format/kort1.mjs --modell google/gemini-3.1-pro-preview --variant konst [--tagg b] [--urval data/format/kalib/urval.json]
// --variant konst: prompten innehåller LeTrends principer. neutral: samma schema utan principer.
// Resultat: data/format/v1-<variant>-<modell>[-<tagg>]/<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MODELL = varde('--modell', 'google/gemini-3.1-pro-preview')
const VARIANT = varde('--variant', 'konst')
const TAGG = varde('--tagg', '')
const PAR = Number(varde('--par', 8))
const URVAL = varde('--urval', path.join(DATA, 'format', 'kalib', 'urval.json'))
process.env.LOVABLE_MODELL = MODELL
const { analyseraVideo } = await import('../typer/lovable.mjs')

const namn = `v1-${VARIANT}-${MODELL.split('/').pop()}${TAGG ? `-${TAGG}` : ''}`
const UT = path.join(DATA, 'format', namn)
fs.mkdirSync(UT, { recursive: true })

import { schema, prompt as promptFor } from './v1.mjs'
const prompt = konto => promptFor(konto, VARIANT)

const urval = JSON.parse(fs.readFileSync(URVAL, 'utf8'))
let i = 0
await Promise.all(Array.from({ length: Math.min(PAR, urval.length) }, async () => {
  while (i < urval.length) {
    const k = urval[i++]
    const ut = path.join(UT, `${k.id}.json`)
    if (fs.existsSync(ut)) continue
    try {
      const t0 = Date.now()
      const r = await analyseraVideo({ fil: k.fil, prompt: prompt(k.konto), schema, temperatur: 0.2 })
      fs.writeFileSync(ut, JSON.stringify({ id: k.id, konto: k.konto, modell: r.modell, variant: VARIANT, tokens: r.usage?.total_tokens, ms: Date.now() - t0, ...r.data }, null, 1))
    } catch (e) { console.warn(`${k.id}: ${e.message.slice(0, 300)}`) }
  }
}))
console.log(`${namn}: ${fs.readdirSync(UT).length}/${urval.length}`)
