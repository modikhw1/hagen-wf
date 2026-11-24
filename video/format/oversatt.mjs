// Översätter formatkortens textfält till engelska för Miles (Sesame talar inte svenska).
//   node format/oversatt.mjs [--variant v1-konst-gemini-3.1-pro-preview]
// Resultat: data/format/<variant>-en/<id>.json med handling, karna, mall och skal på engelska.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'

const args = process.argv.slice(2)
const VARIANT = args[args.indexOf('--variant') + 1] && args.includes('--variant') ? args[args.indexOf('--variant') + 1] : 'v1-konst-gemini-3.1-pro-preview'
const IN = path.join(DATA, 'format', VARIANT), UT = `${IN}-en`, TOM = path.join(DATA, 'format', 'tom.mp4')
fs.mkdirSync(UT, { recursive: true })
const s = { type: 'string' }
const schema = { type: 'object', properties: { handling: s, karna: s, mall: s, skal: s }, required: ['handling', 'karna', 'mall', 'skal'], additionalProperties: false }
const filer = fs.readdirSync(IN)
let i = 0
await Promise.all(Array.from({ length: 10 }, async () => {
  while (i < filer.length) {
    const f = filer[i++]; if (fs.existsSync(path.join(UT, f))) continue
    const x = JSON.parse(fs.readFileSync(path.join(IN, f), 'utf8'))
    const text = { handling: x.handling, karna: x.karna, mall: x.mall, skal: x.bartest.skal }
    const r = await analyseraVideo({ fil: TOM, prompt: `Ignore the video, it is an empty placeholder. Translate each field to plain, natural spoken English. Keep [placeholders] in brackets, translated. Keep quoted lines in their original language.\n${JSON.stringify(text, null, 1)}`, schema, temperatur: 0 })
    fs.writeFileSync(path.join(UT, f), JSON.stringify(r.data, null, 1))
  }
}))
console.log(`${fs.readdirSync(UT).length}/${filer.length}`)
