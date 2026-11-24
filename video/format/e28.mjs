// E28, lager 2: semantisk-teknisk läsning. Scen för scen, krok, svårighet, manus. Säljutlopp som i E26.
// Förregistrering: data/format/e28/forregistrering.json
//   LOVABLE_KONTO=beacon node format/e28.mjs [--modell google/gemini-3.8-flash] [--ids fil.json] [--par 5]
// Resultat: data/format/e28/lasning[-<modell>]/<id>.json
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'

const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MODELL = varde('--modell', 'google/gemini-3.8-flash'), PAR = Number(varde('--par', 5))
const SUFF = MODELL.includes('3.8-flash') ? '' : '-' + MODELL.split('gemini-').pop().replace('-preview', '')
const E = path.join(DATA, 'format', 'e28'), UT = path.join(E, 'lasning' + SUFF); fs.mkdirSync(UT, { recursive: true })
const liten = id => path.join(os.homedir(), 'Downloads', 'letrend-e13', `${id}.mp4`)
const ids = JSON.parse(fs.readFileSync(varde('--ids', path.join(DATA, 'format', 'e23', 'ids.json')), 'utf8'))
const s = (d, en) => ({ type: 'string', description: d, ...(en ? { enum: en } : {}) }), heltal = (d, min, max) => ({ type: 'integer', description: d, minimum: min, maximum: max })
const schema = { type: 'object', required: ['scener', 'forsta_sekunderna', 'premiss_klar', 'svarighet', 'svarighet_skal', 'manus', 'saljtext'], properties: {
  scener: { type: 'array', description: 'En rad per scen i ordning. En scen är en sammanhängande plats eller tagning.', items: { type: 'object', required: ['start', 'slut', 'vad', 'repliker', 'tid'], properties: {
    start: { type: 'number', description: 'Sekund.' }, slut: { type: 'number', description: 'Sekund.' },
    vad: s('Vad som händer i scenen, rakt, en mening.'),
    repliker: heltal('Antal repliker eller textrader som bär scenen.', 0, 30),
    tid: s('Bär scenen sin tid? bar = den håller så länge den står; for_lang = den stannar kvar efter att poängen är given eller utan att något händer; for_kort = poängen hinner inte landa.', ['bar', 'for_lang', 'for_kort']),
  } } },
  forsta_sekunderna: s('Vad som händer de första två sekunderna, rakt.'),
  premiss_klar: { type: 'number', description: 'Vid vilken sekund en tittare förstår vad klippet handlar om. 0 om det är klart direkt.' },
  svarighet: heltal('Hur svårt det är för vanlig personal att spela in klippet med en telefon. 1 = en person, en tagning; 5 = flera personer, många tagningar, exakt timing eller avancerad klippning.', 1, 5),
  svarighet_skal: s('Konkreta skäl: antal personer, tagningar, rekvisita, timing, klippning.'),
  manus: s('skrivet = repliker och vändning är skrivna i förväg; improviserat = det finns en idé men orden kommer på plats; inget = inget manus behövs.', ['skrivet', 'improviserat', 'inget']),
  saljtext: s('Skriv till sist som en copywriter vars jobb är att få klippet att låta så bra som möjligt. Två meningar.'),
} }
const kvar = ids.filter(id => fs.existsSync(liten(id)) && !fs.existsSync(path.join(UT, `${id}.json`)))
console.log(`${kvar.length} klipp, ${MODELL}, ${PAR} samtidigt`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => { while (i < kvar.length) { const id = kvar[i++]; try {
  const r = await beaconDelar({ modell: MODELL, schema, temperatur: 0.3, delar: [{ fil: liten(id) }, { text: 'Ett klipp från en restaurang, bar eller ett kafé. Fyll i fälten i ordning. Skriv på svenska.' }] })
  fs.writeFileSync(path.join(UT, `${id}.json`), JSON.stringify({ id, ...r.data })); ny++
} catch (e) { fel++ } } }))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.usd.toFixed(2)} USD`)
