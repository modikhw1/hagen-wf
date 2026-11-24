// E15: hämtar klipp till små kopior (240x426, 2 bilder/s) för motorläsning i stor skala. Originalet raderas direkt
// efter nedskalningen, eftersom disken är nästan full (ägaren har gett fritt att rensa, 17 nov).
//   node format/e15-hamta.mjs [--kalla bibliotek] [--par 5] [--bakifran] [--max n]
// Resultat: Downloads/letrend-e13/<id>.mp4 (samma mapp som E13/E14 läser ur) och data/format/e15/hamta-<kalla>.json
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { ytdlp } from '../bank/hamta.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PAR = Number(varde('--par', 5)), KALLA = varde('--kalla', 'bibliotek'), MAX = Number(varde('--max', 1e9))
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const LITEN = path.join(os.homedir(), 'Downloads', 'letrend-e13'), TMP = path.join(os.homedir(), 'Downloads', 'letrend-tmp')
fs.mkdirSync(LITEN, { recursive: true }); fs.mkdirSync(TMP, { recursive: true })
const litenFil = id => path.join(LITEN, `${id}.mp4`)

let ids
if (KALLA === 'bibliotek') ids = Object.values(las(path.join(DATA, 'format', 'harness', 'bibliotek-v6.json')).hyllor).flat().map(k => k.id)
else ids = las(KALLA)
ids = [...new Set(ids)]; if (args.includes('--bakifran')) ids.reverse(); ids = ids.slice(0, MAX)
const kvar = ids.filter(id => !fs.existsSync(litenFil(id)))
console.log(`${ids.length} klipp, ${kvar.length} kvar att hämta, ${PAR} samtidigt`)

async function ett(id) {
  if (fs.existsSync(litenFil(id))) return
  const i = id.lastIndexOf('-'), konto = id.slice(0, i), video = id.slice(i + 1), ra = path.join(TMP, `${id}.${process.pid}.mp4`)
  try {
    await ytdlp(['-f', 'b[height<=720][ext=mp4]/bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b', '--merge-output-format', 'mp4', '--no-write-comments', '-o', ra, `https://www.tiktok.com/@${konto}/video/${video}`])
    const tmp = litenFil(id) + `.${process.pid}.tmp.mp4`
    await kor(verktyg.ffmpeg, ['-y', '-v', 'error', '-i', ra, '-t', '90', '-vf', 'fps=2,scale=240:426:force_original_aspect_ratio=decrease,pad=240:426:(ow-iw)/2:(oh-ih)/2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '33', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ac', '1', '-b:a', '32k', tmp])
    fs.renameSync(tmp, litenFil(id))
  } finally { for (const f of fs.readdirSync(TMP)) if (f.startsWith(`${id}.${process.pid}`)) fs.rmSync(path.join(TMP, f), { force: true }) }
}
let i = 0, ny = 0; const fel = []
await Promise.all(Array.from({ length: PAR }, async () => {
  while (i < kvar.length) {
    const id = kvar[i++]
    try { await ett(id); ny++ } catch (e) { fel.push({ id, fel: e.message.slice(0, 160) }) }
    if ((ny + fel.length) % 50 === 0) console.log(`  ${ny + fel.length}/${kvar.length}, ${fel.length} fel`)
  }
}))
fs.writeFileSync(path.join(DATA, 'format', 'e15', `hamta-${path.basename(KALLA, '.json')}${args.includes('--bakifran') ? '-b' : ''}.json`), JSON.stringify({ ny, fel }, null, 1))
console.log(`klart: ${ny} nya, ${fel.length} fel`)
