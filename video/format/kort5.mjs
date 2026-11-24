// Formatkort v5 på biblioteket (data/format/harness/urval.json) och på extra klipp.
//   LOVABLE_KONTO=2 node format/kort5.mjs [--par 8] [--ids id1,id2] [--ut v5b] [--extra fil.json]
// --extra: en JSON-lista med { id, konto, url, fil } utöver biblioteket (t.ex. nya klipp till pass 6).
// Resultat: data/format/harness/<ut>/<id>.json (standard v5)
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { schema, prompt, promptKort } from './v5.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PAR = Number(varde('--par', 8))
const H = path.join(DATA, 'format', 'harness'), UT = path.join(H, varde('--ut', 'v5'))
fs.mkdirSync(UT, { recursive: true })
let lista = JSON.parse(fs.readFileSync(path.join(H, 'urval.json'), 'utf8')).bibliotek
if (varde('--extra')) lista = [...lista, ...JSON.parse(fs.readFileSync(varde('--extra'), 'utf8'))]
// --modell: annan modell (t.ex. google/gemini-4-argon). --neutral: samma schema utan doktrinen i prompten (E5).
// --idfil: en fil med ett id per rad.
const MODELL = varde('--modell', 'google/gemini-3.1-pro-preview')
const NEUTRAL = args.includes('--neutral')
const KORTD = args.includes('--kortdoktrin')
// --rutnat (E9): videon i 2×2-rutnät, fyra tidpunkter en kvarts sekund isär per bild, så att 1 bild/s visar 4.
const RUTNAT = args.includes('--rutnat')
const RN = 'C:/Users/praiseworthy/Downloads/letrend-rutnat'
const RNOT = ' Varje bild i videon är ett rutnät 2×2 med fyra tidpunkter i följd, en kvarts sekund isär (uppe till vänster, uppe till höger, nere till vänster, nere till höger). Bedöm klippet som det är, inte rutnätet: rutnätet är inte en effekt i klippet.'
async function rutnat(k) { const f = `${RN}/${k.id}.mp4`; if (fs.existsSync(f)) return f; fs.mkdirSync(RN, { recursive: true }); await kor(verktyg.ffmpeg, ['-y', '-v', 'error', '-i', k.fil, '-t', '90', '-vf', 'fps=4,scale=360:640:force_original_aspect_ratio=decrease,pad=360:640:(ow-iw)/2:(oh-ih)/2,tile=2x2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ac', '1', '-b:a', '48k', f]); return f }
const promptFor = konto => KORTD ? promptKort(konto) : NEUTRAL ? `Ett TikTok-klipp från @${konto}. Beskriv klippet enligt schemat. Var konkret och gissa inte. Svara på svenska.` : prompt(konto)
const ids = varde('--ids') ? new Set(varde('--ids').split(',')) : varde('--idfil') ? new Set(fs.readFileSync(varde('--idfil'), 'utf8').split(/\r?\n/).filter(Boolean)) : null
if (ids) lista = lista.filter(k => ids.has(k.id))
const ko = lista.filter(k => fs.existsSync(k.fil) && !fs.existsSync(path.join(UT, `${k.id}.json`)))
console.log(`${lista.filter(k => fs.existsSync(k.fil)).length}/${lista.length} filer finns, ${ko.length} att köra`)
let i = 0, ok = 0, fel = 0, tokens = 0
await Promise.all(Array.from({ length: PAR }, async () => {
  while (i < ko.length) {
    const k = ko[i++]
    try {
      const r = await analyseraVideo({ fil: RUTNAT ? await rutnat(k) : k.fil, prompt: promptFor(k.konto) + (RUTNAT ? RNOT : ''), schema, temperatur: 0.2, modell: MODELL })
      tokens += r.usage?.total_tokens ?? 0
      fs.writeFileSync(path.join(UT, `${k.id}.json`), JSON.stringify({ id: k.id, konto: k.konto, kalla: k.kalla, url: k.url, modell: r.modell, neutral: NEUTRAL, tokens: r.usage?.total_tokens, ms: r.ms, ...r.data }, null, 1))
      ok++
    } catch (e) { fel++; console.warn(`${k.id}: ${e.message.slice(0, 200)}`); if (/ 402:/.test(e.message)) process.exit(1) }
  }
}))
console.log(`klart: ${ok} ok, ${fel} fel, ${tokens} tokens (~${(tokens / 1000 * 0.016).toFixed(2)} krediter)`)
