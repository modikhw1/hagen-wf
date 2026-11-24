// E26 (17 nov 2026): huvudrum mellan återberättelse och säljtext. data/format/e26/forregistrering.json
//   node format/e26.mjs --urval
//   LOVABLE_KONTO=beacon node format/e26.mjs [--par 5]
// Resultat: data/format/e26/lasning/<id>.json
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'

const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const E = path.join(DATA, 'format', 'e26'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const liten = id => path.join(os.homedir(), 'Downloads', 'letrend-e13', `${id}.mp4`)

if (args.includes('--urval')) {
  const bib = Object.values(las(path.join(DATA, 'format', 'harness', 'bibliotek-v6.json')).hyllor).flat()
  let s = 26; const r = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296 }
  const ta = h => bib.filter(k => k.hylla === h && fs.existsSync(liten(k.id))).map(k => [r(), k.id]).sort((a, b) => a[0] - b[0]).slice(0, 100).map(x => x[1])
  const u = { replikering: las(path.join(DATA, 'format', 'e23', 'ids.json')), karna: ta('karna'), ute: ta('ute') }
  fs.writeFileSync(path.join(E, 'urval.json'), JSON.stringify(u)); console.log(u.replikering.length, u.karna.length, u.ute.length); process.exit(0)
}
const s = d => ({ type: 'string', description: d })
const schema = { type: 'object', required: ['aterberattelse', 'saljtext', 'tackning', 'pafyllt'], properties: {
  aterberattelse: s('Återberätta klippet som en recensent som bara berättar vad som händer, i den ordning det händer. Två till fyra meningar.'),
  saljtext: s('Skriv nu som en copywriter vars jobb är att få klippet att låta så bra som möjligt. Två meningar.'),
  tackning: { type: 'integer', minimum: 0, maximum: 100, description: 'Titta på klippet igen. Hur stor del av säljtexten håller klippet faktiskt för, i procent?' },
  pafyllt: s('Det säljtexten lägger till som inte finns i klippet, eller "inget".'),
} }
// E29: --modell google/gemini-4-argon --ids fil.json skriver till lasning-<modell>
const MODELL = varde('--modell', 'google/gemini-3.8-flash'), SUFF = MODELL.includes('3.8-flash') ? '' : '-' + MODELL.split('gemini-').pop().replace('-preview', '')
const U = las(path.join(E, 'urval.json')), ids = varde('--ids') ? las(varde('--ids')) : [...new Set([...U.replikering, ...U.karna, ...U.ute])], UT = path.join(E, 'lasning' + SUFF); fs.mkdirSync(UT, { recursive: true })
const kvar = ids.filter(id => !fs.existsSync(path.join(UT, `${id}.json`)) && fs.existsSync(liten(id))), PAR = Number(varde('--par', 5))
console.log(`${kvar.length} klipp kvar, ${PAR} samtidigt`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => { while (i < kvar.length) { const id = kvar[i++]; try {
  const r = await beaconDelar({ modell: MODELL, schema, temperatur: 0.3, delar: [{ fil: liten(id) }, { text: 'Ett klipp från en restaurang, bar eller ett kafé. Fyll i fälten i ordning. Skriv på svenska.' }] })
  fs.writeFileSync(path.join(UT, `${id}.json`), JSON.stringify({ id, ...r.data })); ny++
} catch (e) { fel++ } } }))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.usd.toFixed(2)} USD`)
