// Formatkort v4 på biblioteket (data/format/harness/urval.json). Hämtar klipp som saknas på disk och kör Pro.
//   node format/kort4.mjs [--par 8]
// Resultat: data/format/harness/v4/<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg } from '../analys/verktyg.mjs'
import { schema, prompt } from './v4.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'

const args = process.argv.slice(2)
const PAR = Number(args.includes('--par') ? args[args.indexOf('--par') + 1] : 8)
const H = path.join(DATA, 'format', 'harness'), UT = path.join(H, 'v4')
fs.mkdirSync(UT, { recursive: true })
const { bibliotek } = JSON.parse(fs.readFileSync(path.join(H, 'urval.json'), 'utf8'))

const FORMAT = "b[ext=mp4][height<=1024][vcodec~='^(h265|hevc|bytevc1)']/b[ext=mp4][height<=1024]/b[ext=mp4]/b"
const behov = bibliotek.filter(k => !fs.existsSync(k.fil))
if (behov.length) {
  const dir = 'C:/Users/praiseworthy/Downloads/letrend-bibliotek/_b'
  fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(path.join(dir, 'lista.txt'), behov.map(k => k.url).join('\n'))
  await new Promise(res => { const p = spawn('uvx', ['yt-dlp', '--ffmpeg-location', verktyg.ffmpeg, '-f', FORMAT, '--merge-output-format', 'mp4', '--ignore-errors', '--no-progress', '-o', path.join(dir, '%(id)s.%(ext)s'), '-a', path.join(dir, 'lista.txt')], { windowsHide: true }); p.stdout.on('data', () => {}); p.stderr.on('data', () => {}); p.on('close', res) })
  for (const k of behov) { const f = path.join(dir, `${k.vid}.mp4`); if (fs.existsSync(f)) { fs.mkdirSync(path.dirname(k.fil), { recursive: true }); fs.renameSync(f, k.fil) } }
  fs.rmSync(dir, { recursive: true, force: true })
}
const ko = bibliotek.filter(k => fs.existsSync(k.fil) && !fs.existsSync(path.join(UT, `${k.id}.json`)))
console.log(`${bibliotek.filter(k => fs.existsSync(k.fil)).length}/${bibliotek.length} filer finns, ${ko.length} att köra`)
let i = 0, ok = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => {
  while (i < ko.length) {
    const k = ko[i++]
    try {
      const r = await analyseraVideo({ fil: k.fil, prompt: prompt(k.konto), schema, temperatur: 0.2, modell: 'google/gemini-3.1-pro-preview' })
      fs.writeFileSync(path.join(UT, `${k.id}.json`), JSON.stringify({ id: k.id, konto: k.konto, kalla: k.kalla, url: k.url, tokens: r.usage?.total_tokens, ...r.data }, null, 1))
      ok++
    } catch (e) { fel++; console.warn(`${k.id}: ${e.message.slice(0, 200)}`); if (/ 402:/.test(e.message)) process.exit(1) }
  }
}))
console.log(`klart: ${ok} ok, ${fel} fel`)
