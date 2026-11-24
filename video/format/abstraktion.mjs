// Abstraktionslagret (4 nov 2026), en textkedja ovanpå formatkort v5: video → kort → omdöme på text.
// Upptäckt i residualerna mot ägaren (klipp 1–27): ägaren skiljer på tre sorters överföring som v5 slår ihop.
//   ide:   premissen går att flytta (sketcher, situationer)
//   form:  kompositionen går att flytta som mall, villkorat av meny, segment och kapacitet (CapCut-delen,
//          montage, visningar): "not deserve to throw out", "neither here or there", ett beslut för CM
//   ingen: klippet bärs av kontots egen värld, en persona, ett event eller en unik produkt
// Pro bedömer 12 kort per anrop på text (bryggan tar högst 20 000 tecken).
//   LOVABLE_KONTO=3 node format/abstraktion.mjs [--kort <katalog>] [--ut <fil>]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
import { LETREND } from './doktrin.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const KD = varde('--kort', path.join(DATA, 'format', 'harness', 'v5'))
const UT = varde('--ut', path.join(DATA, 'format', 'harness', 'abstraktion.json'))
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const kort = fs.readdirSync(KD).filter(f => f.endsWith('.json')).map(f => las(path.join(KD, f)))
const klart = fs.existsSync(UT) ? las(UT) : {}
const kvar = kort.filter(c => !klart[c.id])

export const ABSTRAKTION = `Tre sorters överföring. När en CM rekommenderar ett biblioteksklipp till en annan verksamhet flyttas något:
- ide: premissen flyttas. En situation eller ett skämt som går att spela upp var som helst, med vem som helst. Utförandet får vara klumpigt.
- form: kompositionen flyttas som mall: bildföljd, scenlängder, rörelser, takt. Det gäller montage, visningar och CapCut-liknande klipp. Formen är inte värdelös, men den flyttar bara under villkor: liknande meny eller produkt, ett segment som bär polering, någon som kan filma. Ju mer bilderna måste abstraheras, desto svårare blir det att nå samma kvalitet.
- ingen: det som bär klippet stannar hos avsändaren: kontots egen värld och publikrelation (löpande dialog, quiz, inside-skämt som kräver att man följt kontot), en viss persons karisma, ett event som redan händer, eller en unik produkt eller lokal.`

const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const kompakt = c => ({ helhet: c.helhet, handling: c.handling, karna: c.karna, bars_av: c.grundvarde?.bars_av, beats: c.beats?.map(b => `${b.funktion}/${b.bar}/${b.bunden}`).join(', '), bunden_till: c.forlaga?.bunden_till })

const res = { ...klart }
for (let i = 0; i < kvar.length; i += 12) {
  const grupp = kvar.slice(i, i + 12), koder = grupp.map((c, j) => `K${j + 1}`)
  const schema = obj({ bedomning: { type: 'array', minItems: grupp.length, maxItems: grupp.length, items: obj({
    kod: s('Klippets kod.', koder),
    abstraktion: s('Vad som flyttas: ide, form eller ingen.', ['ide', 'form', 'ingen']),
    vad_flyttar: s('Det som flyttar till en annan verksamhet, en mening.'),
    villkor: s('När det flyttar: vilka verksamheter, menyer, segment eller vilken kapacitet som krävs. "inga" om det flyttar överallt.'),
    stannar: s('Det som stannar hos avsändaren och inte går att flytta, en mening.'),
  }) } })
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Du är content manager på LeTrend och avgör vad som går att abstrahera ur biblioteksklipp.

${LETREND}

${ABSTRAKTION}

Klipp:
${grupp.map((c, j) => `K${j + 1} ${JSON.stringify(kompakt(c))}`).join('\n')}

Svara på svenska.`
  if (prompt.length > 19800) throw new Error(`prompten är för lång (${prompt.length})`)
  const r = await analyseraVideo({ fil: path.join(DATA, 'format', 'tom.mp4'), prompt, schema, temperatur: 0.2, modell: varde('--modell', 'google/gemini-3.1-pro-preview') })
  for (const x of r.data.bedomning) { const c = grupp[koder.indexOf(x.kod)]; if (c) res[c.id] = { abstraktion: x.abstraktion, vad_flyttar: x.vad_flyttar, villkor: x.villkor, stannar: x.stannar } }
  fs.writeFileSync(UT, JSON.stringify(res, null, 1))
  console.log(`${Math.min(i + 12, kvar.length)}/${kvar.length} (${r.usage?.total_tokens} tokens)`)
}
const n = v => Object.values(res).filter(x => x.abstraktion === v).length
console.log(`ide ${n('ide')}, form ${n('form')}, ingen ${n('ingen')}`)
