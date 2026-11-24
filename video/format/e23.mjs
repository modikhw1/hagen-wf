// E23 (17 nov 2026): register och temperatur. Förregistrering: data/format/e23/forregistrering.json
//   LOVABLE_KONTO=beacon node format/e23.mjs --urval          (slumpar 400 replikeringsklipp, fast frö)
//   LOVABLE_KONTO=beacon node format/e23.mjs --villkor B|C|D [--par 4]
// Resultat: data/format/e23/<villkor>/<id>.json
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'

const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const E = path.join(DATA, 'format', 'e23'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const liten = id => path.join(os.homedir(), 'Downloads', 'letrend-e13', `${id}.mp4`)

if (args.includes('--urval')) {
  const R = fs.readFileSync(path.join(DATA, 'format', 'e15', 'motorer-flash.jsonl'), 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l))
  const nya = new Set(las(path.join(DATA, 'format', 'e19', 'ids.json')))
  const ok = R.filter(r => nya.has(r.id) && r.u !== null && fs.existsSync(liten(r.id))).map(r => r.id).sort()
  let s = 23; const slump = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296 }
  const val = ok.map(id => [slump(), id]).sort((a, b) => a[0] - b[0]).slice(0, 400).map(x => x[1])
  fs.writeFileSync(path.join(E, 'ids.json'), JSON.stringify(val)); console.log(val.length, 'av', ok.length); process.exit(0)
}

const V = varde('--villkor', 'B'), PAR = Number(varde('--par', 4))
const INST = { B: { temperatur: 0.1, extra: {} }, C: { temperatur: 1.0, extra: {} }, D: { temperatur: 1.8, extra: { topP: 0.98 } } }[V]
const s = (description, en) => ({ type: 'string', description, ...(en ? { enum: en } : {}) })
const schema = { type: 'object', required: ['vad', 'sags', 'vem', 'anstrangning', 'varfor_anstrangning'], properties: {
  vad: s('Vad som händer i klippet, som om du skrev ett sms till en kompis: rakt, konkret, vardagliga ord, i den ordning det händer. Högst tre meningar.'),
  sags: s('Vad som sägs eller står i text, ungefär ordagrant, eller "inget".'),
  vem: s('Vem som syns och vad de gör, rakt.'),
  anstrangning: { type: 'integer', minimum: 1, maximum: 5, description: 'Hur mycket arbete som syns ha lagts på klippet. 1 = slängt ihop på en minut, 5 = planerat, flera tagningar, klippt med omsorg.' },
  varfor_anstrangning: s('En mening, rakt.'),
} }
const PROMPT = `Beskriv klippet rakt och bokstavligt, som när du berättar för en kompis vad du just såg. Inga omdömen, inga tolkningar av syfte, ingen säljande eller "snygg" ton. Om två personer kastar en boll, skriv att två personer kastar en boll.
Använd inte ord som: engagera, skapa, förmedla, lyfta, upplevelse, dynamik, gestalta, iscensätta, förvandla, sensorisk, tillfredsställande, aptitretande, inbjudande, autentisk, kontrast, utmaning, verksamhet, medarbetare, representant, hantverk, presentera, visa upp.
Om klippet är slarvigt, tomt eller lågt ansträngt, säg det rakt. Skriv på svenska.`

const ids = las(path.join(E, 'ids.json')), UT = path.join(E, V); fs.mkdirSync(UT, { recursive: true })
const kvar = ids.filter(id => !fs.existsSync(path.join(UT, `${id}.json`)))
console.log(`villkor ${V} (temperatur ${INST.temperatur}): ${kvar.length} kvar, ${PAR} samtidigt`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => { while (i < kvar.length) { const id = kvar[i++]; try {
  const r = await beaconDelar({ modell: 'google/gemini-3.8-flash', schema, temperatur: INST.temperatur, extra: INST.extra, delar: [{ fil: liten(id) }, { text: PROMPT }] })
  fs.writeFileSync(path.join(UT, `${id}.json`), JSON.stringify({ id, villkor: V, ...r.data })); ny++
} catch (e) { fel++ } } }))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.usd.toFixed(2)} USD`)
