// Perceptionsexperiment (3 nov 2026): ser modellerna tid och klippning bättre med en annan videotyp?
// orig: originalet (Gemini tar 1 bild/s). lang: 4× nedsaktat (4 bilder/s verklig tid, 4× tokens).
// rutnat: 2×2-rutnät med fyra tidpunkter per bild (4 bilder/s verklig tid till originalets tokenkostnad).
// Samma lagerschema (format/lager.mjs, prompt 1) och en mening om videotypen.
//   node format/perc.mjs [--modeller a,b] [--par 24]
// Resultat: data/format/perc/svar/<typ>-<modell>-k<körning>/<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { schema, PROMPTER } from './lager.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MODELLER = varde('--modeller', 'google/gemini-3.1-flash-lite,google/gemini-3.8-flash').split(',')
const PAR = Number(varde('--par', 24))
const P = path.join(DATA, 'format', 'perc')
const urval = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'kalib', 'urval.json'), 'utf8'))
const TYPER = {
  orig: { fil: k => k.fil, not: '' },
  lang: { fil: k => path.join(P, `${k.id}.lang.mp4`), not: ' Videon är nedsaktad fyra gånger, ljudet också, så att du ska se detaljer. Bedöm klippet som det är i normal fart.' },
  rutnat: { fil: k => path.join(P, `${k.id}.rutnat.mp4`), not: ' Varje bild i videon är ett rutnät 2×2 med fyra tidpunkter i följd, en kvarts sekund isär (uppe till vänster, uppe till höger, nere till vänster, nere till höger). Bedöm klippet som det är, inte rutnätet: ett rutnät är inte en effekt i klippet.' },
}
const jobb = []
for (const [typ, t] of Object.entries(TYPER)) for (const m of MODELLER) for (const k of [1, 2]) for (const kl of urval) {
  const ut = path.join(P, 'svar', `${typ}-${m.split('/').pop()}-k${k}`, `${kl.id}.json`)
  if (!fs.existsSync(ut)) jobb.push({ typ, t, m, kl, ut })
}
for (let i = jobb.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [jobb[i], jobb[j]] = [jobb[j], jobb[i]] }
console.log(`${jobb.length} anrop`)
let i = 0, ok = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => {
  while (i < jobb.length) {
    const { typ, t, m, kl, ut } = jobb[i++]
    try {
      const r = await analyseraVideo({ fil: t.fil(kl), prompt: PROMPTER[0](kl.konto) + t.not, schema, temperatur: 0.2, modell: m })
      fs.mkdirSync(path.dirname(ut), { recursive: true })
      fs.writeFileSync(ut, JSON.stringify({ id: kl.id, nr: kl.nr, typ, modell: r.modell, tokens: r.usage?.total_tokens, ...r.data }))
      ok++
    } catch (e) { fel++; console.warn(`${typ} ${m} ${kl.id}: ${e.message.slice(0, 160)}`); if (/ 402:/.test(e.message)) process.exit(1) }
  }
}))
console.log(`klart: ${ok} ok, ${fel} fel`)
