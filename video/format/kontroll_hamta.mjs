// Kontroller med ägaren: hämtar klippen i kandidater.json i full kvalitet (spelas lokalt, utan siffror).
//   timeout 570 node format/kontroll_hamta.mjs   (återupptas; hämtade och misslyckade hoppas över)
import fs from 'node:fs'
import path from 'node:path'
import { ytdlp } from '../bank/hamta.mjs'
import { DATA } from '../analys/pipeline.mjs'

const RAD = path.join(DATA, 'format', 'kontroll')
const KL = path.join(RAD, 'klipp'); fs.mkdirSync(KL, { recursive: true })
const { url } = JSON.parse(fs.readFileSync(path.join(RAD, 'kandidater.json'), 'utf8'))
const FEL = path.join(RAD, 'hamta-fel.json')
const fel = fs.existsSync(FEL) ? JSON.parse(fs.readFileSync(FEL, 'utf8')) : {}
let ok = 0, nya = 0
for (const [id, u] of Object.entries(url)) {
  const fil = path.join(KL, `${id}.mp4`)
  if (fs.existsSync(fil)) { ok++; continue }
  if (fel[id]) continue
  try {
    await ytdlp(['-f', 'bv*[height<=1024][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b', '--merge-output-format', 'mp4', '--no-write-comments', '--sleep-requests', '1', '-o', path.join(KL, `${id}.%(ext)s`), u], { timeout: 180_000 })
    if (fs.existsSync(fil)) { ok++; nya++; console.log('ok', id) } else throw new Error('ingen fil')
  } catch (e) {
    fel[id] = String(e.message ?? e).slice(0, 200); fs.writeFileSync(FEL, JSON.stringify(fel, null, 1))
    console.log('fel', id, fel[id].slice(0, 100))
  }
}
console.log(`klart: ${ok} av ${Object.keys(url).length} (nya ${nya}, fel ${Object.keys(fel).length})`)
