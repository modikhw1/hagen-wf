// Tes 3 nov: tolka videon en gång (beskrivning, inga omdömen) och gör omdömena på texten (doma.mjs).
// Om det håller räcker det att skicka videon en gång per klipp. Sedan kan prompter och principer
// itereras billigt på text över tusentals klipp.
//
//   node format/beskriv.mjs --modell google/gemini-3.1-flash-lite [--urval …]
// Resultat: data/format/beskrivning-<modell>/<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MODELL = varde('--modell', 'google/gemini-3.1-flash-lite')
const PAR = Number(varde('--par', 8))
const URVAL = varde('--urval', path.join(DATA, 'format', 'kalib', 'urval.json'))
process.env.LOVABLE_MODELL = MODELL
const { analyseraVideo } = await import('../typer/lovable.mjs')
const UT = path.join(DATA, 'format', `beskrivning-${MODELL.split('/').pop()}`)
fs.mkdirSync(UT, { recursive: true })

const s = description => ({ type: 'string', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
export const schema = obj({
  scener: {
    type: 'array', description: 'Varje bildklipp eller tydlig del i ordning.',
    items: obj({
      tid: s('Ungefärlig start–slut i sekunder, t.ex. "0–2,5".'),
      vad: s('Vad som händer och syns.'),
      vem: s('Vilka som syns och deras roll (anställd, gäst, ägare, okänd), med kännetecken så att samma person går att följa.'),
      repliker: s('Det som sägs, ordagrant om det går, annars "inget".'),
      skarmtext: s('Skärmtext ordagrant, annars "ingen".'),
      bild: s('Utsnitt, kamerarörelse, ljus och eventuella effekter eller grafik.'),
    }),
  },
  ljud: s('Tal, musik eller trendljud (namn om det går att känna igen), och hur ljudet bär klippet.'),
  klippning: s('Antal klipp, tempo, montage eller en tagning, och hur bearbetat klippet är.'),
  lokal: s('Var det är filmat och vad av lokalen som syns.'),
  produkter: s('Rätter, drycker eller varor som syns och hur de visas.'),
  poang: s('Vad klippet går ut på och hur det slutar, utan att värdera.'),
})

const prompt = konto => `Ett TikTok-klipp från @${konto}. Beskriv det så noggrant att någon som inte ser klippet kan förstå exakt vad som händer, sägs och syns, och hur det är filmat och klippt. Värdera inte. Svara på svenska.`

const urval = JSON.parse(fs.readFileSync(URVAL, 'utf8'))
let i = 0
await Promise.all(Array.from({ length: Math.min(PAR, urval.length) }, async () => {
  while (i < urval.length) {
    const k = urval[i++]
    const ut = path.join(UT, `${k.id}.json`)
    if (fs.existsSync(ut)) continue
    try {
      const r = await analyseraVideo({ fil: k.fil, prompt: prompt(k.konto), schema, temperatur: 0.1 })
      fs.writeFileSync(ut, JSON.stringify({ id: k.id, konto: k.konto, modell: r.modell, tokens: r.usage?.total_tokens, ...r.data }, null, 1))
    } catch (e) { console.warn(`${k.id}: ${e.message.slice(0, 300)}`) }
  }
}))
console.log(`beskrivning-${MODELL.split('/').pop()}: ${fs.readdirSync(UT).length}/${urval.length}`)
