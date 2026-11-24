// E34: hämta nya profillistor utan att skriva över data/bank. Bara listan (yt-dlp --flat-playlist), inga klipp.
//   node format/e34-listor.mjs [--max 1000] [--konton a,b]
// Sparar data/format/e34/listor/<konto>.json; konton som redan finns hoppas över (återupptas).
import fs from 'node:fs'
import path from 'node:path'
import { ytdlp } from '../bank/hamta.mjs'
import { DATA } from '../analys/pipeline.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MAX = Number(varde('--max', 1000))
const UT = path.join(DATA, 'format', 'e34', 'listor'); fs.mkdirSync(UT, { recursive: true })
const alla = fs.readdirSync(path.join(DATA, 'bank')).filter(k => fs.existsSync(path.join(DATA, 'bank', k, 'lista.json')))
const konton = varde('--konton', null)?.split(',') ?? alla
let n = 0
for (const konto of konton) {
  const fil = path.join(UT, `${konto}.json`)
  if (fs.existsSync(fil)) continue
  try {
    const pl = JSON.parse(await ytdlp(['--flat-playlist', '-J', '--playlist-end', String(MAX), `https://www.tiktok.com/@${konto}`], { timeout: 300_000 }))
    const lista = (pl.entries ?? []).map(e => ({ id: e.id, langd: e.duration, visningar: e.view_count, gillanden: e.like_count, kommentarer: e.comment_count, delningar: e.repost_count, datum: e.timestamp ? new Date(e.timestamp * 1000).toISOString().slice(0, 10) : null, text: e.title ?? e.description ?? '' }))
    fs.writeFileSync(fil, JSON.stringify({ konto, hamtad: new Date().toISOString(), antal: lista.length, klipp: lista }))
    const gammal = JSON.parse(fs.readFileSync(path.join(DATA, 'bank', konto, 'lista.json'), 'utf8')).klipp.length
    console.log(`${++n} @${konto}: ${lista.length} (förra ${gammal})`)
  } catch (e) { console.warn(`@${konto}: ${e.message.slice(0, 160)}`) }
}
