// E4-märkning: lagerschemat (prompt 1) på E4-urvalet med den modell E1 valde. Filer i
// Downloads/letrend-e4 raderas när klippet är märkt. Filer i den vanliga banken rörs inte.
//
//   node format/e4.mjs --modell google/gemini-3.8-flash [--par 24]
// Resultat: data/format/e4/lager-<modell>/<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { schema, PROMPTER } from './lager.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MODELL = varde('--modell', 'google/gemini-3.8-flash')
const PAR = Number(varde('--par', 24))
const E4 = path.join(DATA, 'format', 'e4')
const UT = path.join(E4, `lager-${MODELL.split('/').pop()}`)
fs.mkdirSync(UT, { recursive: true })
const urval = JSON.parse(fs.readFileSync(path.join(E4, 'urval.json'), 'utf8'))
const ko = urval.filter(k => !fs.existsSync(path.join(UT, `${k.id}.json`)) && fs.existsSync(k.fil)).slice(0, Number(varde('--max', 1e9)))
console.log(`${ko.length} klipp att märka med ${MODELL}`)

let i = 0, ok = 0, fel = 0
const t0 = Date.now()
await Promise.all(Array.from({ length: PAR }, async () => {
  while (i < ko.length) {
    const k = ko[i++]
    for (let forsok = 1; ; forsok++) {
      try {
        const r = await analyseraVideo({ fil: k.fil, prompt: PROMPTER[0](k.konto), schema, temperatur: 0.2, modell: MODELL })
        fs.writeFileSync(path.join(UT, `${k.id}.json`), JSON.stringify({ id: k.id, konto: k.konto, modell: r.modell, tokens: r.usage?.total_tokens, ...r.data }))
        if (k.fil.includes('/letrend-e4/')) fs.rmSync(k.fil, { force: true })
        ok++
        break
      } catch (e) {
        if (/ 40[12]:/.test(e.message)) { console.error(`nyckel eller krediter: ${e.message.slice(0, 200)}`); process.exit(1) }
        if (forsok < 3 && /fetch failed|ECONNRESET| 5\d\d:/.test(e.message)) { await new Promise(r => setTimeout(r, 5000 * forsok)); continue }
        fel++; console.warn(`${k.id}: ${e.message.slice(0, 200)}`); break
      }
    }
    if ((ok + fel) % 100 === 0) console.log(`${ok + fel}/${ko.length}: ${ok} ok, ${fel} fel, ${((Date.now() - t0) / 1000 / (ok + fel)).toFixed(2)} s/klipp`)
  }
}))
console.log(`klart: ${ok} ok, ${fel} fel`)
