// Ingest i två pass med en prompt som byggs ur distinktioner.json.
//
//   node kor.mjs <id> <video.mp4>            visar prompterna och en kostnadsuppskattning. Gör inga anrop.
//   node kor.mjs <id> <video.mp4> --kor      kör pass 1 och pass 2 (två anrop)
//   node kor.mjs <id> <video.mp4> --kor --omgang b    en andra, oberoende läsning (för stabilitet)
//
// Anropet går genom kedjans egen hjälpare (video/typer/lovable.mjs), som läser sin nyckel ur video/.env.local.
// Allt skrivs under byggsten/hand/ingest/ut/<id>/. Prompten sparas bredvid resultatet.
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { protokoll, tolkning } from './schema.mjs'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const arg = process.argv.slice(2)
const flagga = n => arg.includes(n)
const varde = (n, d) => { const i = arg.indexOf(n); return i >= 0 ? arg[i + 1] : d }
const [id, fil] = arg.filter(a => !a.startsWith('--') && a !== varde('--omgang') && a !== varde('--modell'))
const MODELL = varde('--modell', 'google/gemini-3.8-flash')
const OMGANG = varde('--omgang', 'a')
if (!id || !fil) { console.log('node kor.mjs <id> <video.mp4> [--kor] [--omgang b] [--modell m]'); process.exit(1) }

const lig = JSON.parse(fs.readFileSync(path.join(HERE, 'distinktioner.json'), 'utf8'))
const regler = pass => lig.distinktioner.filter(d => d.pass === pass && d.status !== 'struken').map(d => `- (${d.id}) ${d.regel}`).join('\n')

export const PROMPT1 = `You are logging a short restaurant or cafe video for a production team that will rebuild it as a staged scene.
This pass is a protocol only: what is visible and audible, with timestamps in seconds.

Rules:
${regler(1)}

Fill in the schema. Leave nothing to interpretation.`

export const prompt2 = p => `You are reading a short restaurant or cafe video for a production team. A content manager will adapt it for another business: change the product, the place, the length, the number of scenes and the script, while keeping what makes the clip work.

A protocol of what is visible and audible has already been written. Use it as your evidence, and watch the video again to check it.

PROTOCOL:
${JSON.stringify(p)}

Rules:
${regler(2)}

Fill in the schema. Where a field does not apply, use its neutral value.`

const ut = path.join(HERE, 'ut', id)
const hash = crypto.createHash('sha256').update(JSON.stringify({ lig, protokoll, tolkning })).digest('hex').slice(0, 12)

if (!flagga('--kor')) {
  const mb = fs.existsSync(fil) ? fs.statSync(fil).size / 1e6 : null
  console.log(`# Torrkörning (${MODELL}, liggare v${lig.version}, hash ${hash})\n`)
  console.log('## Pass 1\n' + PROMPT1 + '\n')
  console.log('## Pass 2\n' + prompt2({ '...': 'protokollet ur pass 1' }) + '\n')
  console.log(`Schema: protokoll ${JSON.stringify(protokoll).length} tecken, tolkning ${JSON.stringify(tolkning).length} tecken.`)
  console.log(mb === null ? `Videon ${fil} finns inte.` : `Video: ${mb.toFixed(1)} MB. Två anrop. Tidigare kort i banken kostade 0,3–1,5 öre per klipp och anrop på Flash; räkna med 2–4 öre per klipp här.`)
  process.exit(0)
}

const { analyseraVideo } = await import('../../../video/typer/lovable.mjs')
fs.mkdirSync(ut, { recursive: true })
const spara = (namn, o) => fs.writeFileSync(path.join(ut, namn), typeof o === 'string' ? o : JSON.stringify(o, null, 1))
spara(`prompt1_${hash}.txt`, PROMPT1)
const r1 = await analyseraVideo({ fil, prompt: PROMPT1, schema: protokoll, temperatur: 0.1, modell: MODELL })
spara(`protokoll_${OMGANG}.json`, { id, modell: r1.modell, liggare: lig.version, hash, usage: r1.usage, ms: r1.ms, data: r1.data })
const p2 = prompt2(r1.data)
spara(`prompt2_${hash}_${OMGANG}.txt`, p2)
const r2 = await analyseraVideo({ fil, prompt: p2, schema: tolkning, temperatur: 0.1, modell: MODELL })
spara(`tolkning_${OMGANG}.json`, { id, modell: r2.modell, liggare: lig.version, hash, usage: r2.usage, ms: r2.ms, data: r2.data })
console.log(`${id} omgång ${OMGANG}: pass 1 ${r1.ms} ms, pass 2 ${r2.ms} ms. Skrivet under ${ut}`)
