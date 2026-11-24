// E21 (17 nov 2026): eget uttryck, oviss utgång, handling som sker. Flash läser bara motortexten.
// Förregistrering: data/format/e21/forregistrering.json
//   LOVABLE_KONTO=beacon node format/e21.mjs [--par 8] [--motorer mekanism-3.8-flash]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'
const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PAR = Number(varde('--par', 8)), MAPP = varde('--motorer', 'mekanism-3.8-flash'), MODELL = varde('--modell', 'google/gemini-3.8-flash')
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const M = path.join(DATA, 'format', 'e14', MAPP), UT = path.join(DATA, 'format', 'e21', varde('--ut','lasning')); fs.mkdirSync(UT, { recursive: true })
const s = (description, en) => ({ type: 'string', description, enum: en })
const schema = { type: 'object', required: ['uttryck', 'utgang', 'handling'], properties: {
  uttryck: s('Vems uttryck bär klippet. eget = människorna säger och gör det själva, med egen röst eller eget agerande. lanat = läppsynk, mim eller agerande till ett färdigt ljud, en känd låt eller en trendmall. ingen_rost = bilder, text på skärmen eller musik bär klippet utan att någon uttrycker något.', ['eget', 'lanat', 'ingen_rost']),
  utgang: s('oviss = klippet visar något vars utgång inte var given på förhand: en utmaning, en tävling, ett prov, en äkta reaktion. spelad = det finns ett skeende men utgången är skriven. ingen = inget skeende med utgång.', ['oviss', 'spelad', 'ingen']),
  handling: s('sker = något görs faktiskt i lokalen under klippet. berattas = någon talar om något. visas = något visas upp.', ['sker', 'berattas', 'visas']),
} }
const ids = (varde('--ids') ? JSON.parse(fs.readFileSync(varde('--ids'), 'utf8')).filter(id => fs.existsSync(path.join(M, id + '.json'))) : fs.readdirSync(M).map(f => f.replace('.json', ''))).filter(id => !fs.existsSync(path.join(UT, `${id}.json`)))
console.log(`${ids.length} motorer att läsa, ${PAR} samtidigt`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => { while (i < ids.length) { const id = ids[i++]; try {
  const { yta, ...m } = las(path.join(M, `${id}.json`)).mekanism
  const r = await beaconDelar({ modell: MODELL, schema, temperatur: 0, delar: [{ text: `Ett klipp från en restaurang, bar eller ett kafé, beskrivet bara genom sin motor:\n${JSON.stringify({ motor: m.motor, forlopp: m.forlopp, hallning: m.hallning, krav: m.krav }, null, 1)}\n\nAnge de tre fälten ur beskrivningen. Gissa inte utöver den.` }] })
  fs.writeFileSync(path.join(UT, `${id}.json`), JSON.stringify({ id, ...r.data })); ny++
} catch (e) { fel++ } } }))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.usd.toFixed(2)} USD`)
