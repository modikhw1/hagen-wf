// Formatkort v1 på text: läser en beskrivning (beskriv.mjs) i stället för videon. Endpointen kräver
// en video, så en tom platshållare på en sekund skickas med och modellen får veta att den ska bortses från.
//
//   node format/doma.mjs --beskrivning beskrivning-gemini-3.1-flash-lite --modell google/gemini-3.1-pro-preview [--variant konst] [--tagg x]
// Resultat: data/format/text-<variant>-<modell>-fran-<beskrivning>[-<tagg>]/<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { schema, prompt as promptFor } from './v1.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MODELL = varde('--modell', 'google/gemini-3.1-pro-preview')
const VARIANT = varde('--variant', 'konst')
const BESK = varde('--beskrivning', 'beskrivning-gemini-3.1-flash-lite')
const TAGG = varde('--tagg', '')
const PAR = Number(varde('--par', 8))
const URVAL = varde('--urval', path.join(DATA, 'format', 'kalib', 'urval.json'))
process.env.LOVABLE_MODELL = MODELL
const { analyseraVideo } = await import('../typer/lovable.mjs')

const TOM = path.join(DATA, 'format', 'tom.mp4')
if (!fs.existsSync(TOM)) await kor(verktyg.ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=64x64:d=1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', TOM])

const namn = `text-${VARIANT}-${MODELL.split('/').pop()}-fran-${BESK.replace('beskrivning-', '')}${TAGG ? `-${TAGG}` : ''}`
const UT = path.join(DATA, 'format', namn)
fs.mkdirSync(UT, { recursive: true })

const urval = JSON.parse(fs.readFileSync(URVAL, 'utf8'))
let i = 0
await Promise.all(Array.from({ length: Math.min(PAR, urval.length) }, async () => {
  while (i < urval.length) {
    const k = urval[i++]
    const ut = path.join(UT, `${k.id}.json`)
    const bf = path.join(DATA, 'format', BESK, `${k.id}.json`)
    if (fs.existsSync(ut) || !fs.existsSync(bf)) continue
    const { id, konto, modell, tokens, ...besk } = JSON.parse(fs.readFileSync(bf, 'utf8'))
    const p = `${promptFor(k.konto, VARIANT)}\n\nDu ser inte klippet: videon är en tom platshållare och ska bortses från. Bedöm i stället utifrån den här beskrivningen av klippet:\n${JSON.stringify(besk, null, 1)}`
    try {
      const r = await analyseraVideo({ fil: TOM, prompt: p, schema, temperatur: 0.2 })
      fs.writeFileSync(ut, JSON.stringify({ id: k.id, konto: k.konto, modell: r.modell, variant: VARIANT, fran: BESK, tokens: r.usage?.total_tokens, ...r.data }, null, 1))
    } catch (e) { console.warn(`${k.id}: ${e.message.slice(0, 300)}`) }
  }
}))
console.log(`${namn}: ${fs.readdirSync(UT).length}/${urval.length}`)
