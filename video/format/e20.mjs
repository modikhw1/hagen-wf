// E20 (17 nov 2026): tjänstemötet som röd tråd. Flash läser bara motortexten och anger relation, friktion, insats, sida.
// Förregistrering: data/format/e20/forregistrering.json
//   LOVABLE_KONTO=beacon node format/e20.mjs [--par 8] [--motorer mekanism-3.8-flash]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'
const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PAR = Number(varde('--par', 8)), MAPP = varde('--motorer', 'mekanism-3.8-flash'), MODELL = varde('--modell', 'google/gemini-3.8-flash')
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const M = path.join(DATA, 'format', 'e14', MAPP), UT = path.join(DATA, 'format', 'e20', varde('--ut','lasning')); fs.mkdirSync(UT, { recursive: true })
const s = (description, en) => ({ type: 'string', description, enum: en })
const schema = { type: 'object', required: ['relation', 'friktion', 'insats', 'sida'], properties: {
  relation: s('Vilken relation klippet spelas ut i. gast_personal = ett möte mellan en gäst eller kund och någon som arbetar där. personal_personal = kollegor eller chef och anställd sinsemellan. avsandare_publik = någon vänder sig till tittaren (berättar, visar, bjuder in, säljer). ingen = ingen relation mellan människor bär klippet (bilder, montage, text).', ['gast_personal', 'personal_personal', 'avsandare_publik', 'ingen']),
  friktion: s('Finns en motsättning, ett missförstånd eller en krock mellan parterna?', ['ingen', 'mild', 'tydlig']),
  insats: s('Vad som står på spel i klippet.', ['pengar', 'tid_arbete', 'status', 'smak', 'inget']),
  sida: s('Vems sida tittaren ställs på eller ser situationen från.', ['gastens', 'personalens', 'verksamhetens']),
} }
const ids = (varde('--ids') ? JSON.parse(fs.readFileSync(varde('--ids'), 'utf8')).filter(id => fs.existsSync(path.join(M, id + '.json'))) : fs.readdirSync(M).map(f => f.replace('.json', ''))).filter(id => !fs.existsSync(path.join(UT, `${id}.json`)))
console.log(`${ids.length} motorer att läsa, ${PAR} samtidigt`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => { while (i < ids.length) { const id = ids[i++]; try {
  const { yta, ...m } = las(path.join(M, `${id}.json`)).mekanism
  const r = await beaconDelar({ modell: MODELL, schema, temperatur: 0, delar: [{ text: `Ett klipp från en restaurang, bar eller ett kafé, beskrivet bara genom sin motor:\n${JSON.stringify({ motor: m.motor, forlopp: m.forlopp, hallning: m.hallning, krav: m.krav }, null, 1)}\n\nAnge de fyra fälten ur beskrivningen. Gissa inte utöver den.` }] })
  fs.writeFileSync(path.join(UT, `${id}.json`), JSON.stringify({ id, ...r.data })); ny++
} catch (e) { fel++ } } }))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.usd.toFixed(2)} USD`)
