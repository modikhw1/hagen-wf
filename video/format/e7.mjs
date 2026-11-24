// E7: en enda skarp fråga mot de många lagren (förregistrerat i data/format/e7/forregistrering.json).
// Textkedja: kort v5 → Pro på text, 12 klipp per anrop, bara beskrivningen (inte värdelagren).
//   LOVABLE_KONTO=3 node format/e7.mjs --kort <katalog> --ut <fil>
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
import { LETREND } from './doktrin.mjs'
const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const KD = varde('--kort'), UT = varde('--ut'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const kort = fs.readdirSync(KD).filter(f => f.endsWith('.json')).map(f => las(path.join(KD, f)))
const res = fs.existsSync(UT) ? las(UT) : {}
const kvar = kort.filter(c => !res[c.id])
const s = (d, e) => ({ type: 'string', description: d, ...(e ? { enum: e } : {}) }), n = (a, b, d) => ({ type: 'integer', minimum: a, maximum: b, description: d })
const obj = p => ({ type: 'object', properties: p, required: Object.keys(p), additionalProperties: false })
const kompakt = c => ({ helhet: c.helhet, handling: c.handling, karna: c.karna, beats: c.beats?.map(b => b.vad).join(' / ') })
for (let i = 0; i < kvar.length; i += 12) {
  const g = kvar.slice(i, i + 12), koder = g.map((_, j) => `K${j + 1}`)
  const schema = obj({ bedomning: { type: 'array', minItems: g.length, maxItems: g.length, items: obj({ kod: s('', koder), varde: n(1, 10, 'Hur mycket värde som finns kvar när en annan verksamhet gör sin version med telefon och vanlig personal, utan polering. 10 = en stark fristående idé som bär även när den görs klumpigt. 1 = inget kvar.'), skal: s('Varför, en mening.') }) } })
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från.\n\n${LETREND}\n\nFör varje klipp nedan: hur mycket värde finns kvar när en annan verksamhet gör sin egen version med telefon och vanlig personal, utan polering?\n\n${g.map((c, j) => `K${j + 1} ${JSON.stringify(kompakt(c))}`).join('\n')}\n\nSvara på svenska.`
  const r = await analyseraVideo({ fil: path.join(DATA, 'format', 'tom.mp4'), prompt, schema, temperatur: 0.2, modell: 'google/gemini-3.1-pro-preview' })
  for (const x of r.data.bedomning) { const c = g[koder.indexOf(x.kod)]; if (c) res[c.id] = { varde: x.varde, skal: x.skal } }
  fs.writeFileSync(UT, JSON.stringify(res, null, 1)); console.log(`${Math.min(i + 12, kvar.length)}/${kvar.length}`)
}
