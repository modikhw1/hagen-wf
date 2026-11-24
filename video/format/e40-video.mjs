// E40: hämta minsta video för ett urval osedda klipp. Inga modellanrop.
//   node format/e34-ljud.mjs --del 0 --delar 2
// Urvalet dras en gång (högst 40 per konto, 3–180 s, frö 34) till data/format/e34/ljud-urval.json.
// Filer: ~/Downloads/letrend-e34/<konto>-<id>.<ext>; finns filen hoppas den över (återupptas).
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { ytdlp } from '../bank/hamta.mjs'
import { DATA } from '../analys/pipeline.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const DEL = Number(varde('--del', 0)), DELAR = Number(varde('--delar', 1))
const E = path.join(DATA, 'format', 'e34'), UT = path.join(os.homedir(), 'Downloads', 'letrend-e34v'); fs.mkdirSync(UT, { recursive: true })
const urvalFil = path.join(E, 'ljud-urval.json')
if (!fs.existsSync(urvalFil)) {
  let s = 34; const rnd = () => ((s = (s * 1103515245 + 12345) % 2 ** 31) / 2 ** 31)
  const osedda = JSON.parse(fs.readFileSync(path.join(E, 'osedda.json'), 'utf8')), per = {}
  const langd = {}
  for (const f of fs.readdirSync(path.join(E, 'listor'))) { const j = JSON.parse(fs.readFileSync(path.join(E, 'listor', f), 'utf8')); for (const x of j.klipp) langd[`${j.konto}-${x.id}`] = x.langd }
  for (const id of osedda) { const l = langd[id]; if (l != null && (l < 3 || l > 180)) continue; const k = id.slice(0, id.lastIndexOf('-')); (per[k] ??= []).push(id) }
  const urval = []
  for (const k of Object.keys(per).sort()) { const a = per[k].map(i => [rnd(), i]).sort((x, y) => x[0] - y[0]).slice(0, 40).map(x => x[1]); urval.push(...a) }
  fs.writeFileSync(urvalFil, JSON.stringify(urval)); console.log(`urval: ${urval.length} klipp`)
}
const urval = JSON.parse(fs.readFileSync(urvalFil, 'utf8')).filter((_, n) => n % DELAR === DEL)
const finns = new Set(fs.readdirSync(UT).map(f => f.replace(/\.[^.]+$/, '')))
let ok = 0, fel = 0
for (const id of urval) {
  if (finns.has(id)) continue
  const k = id.slice(0, id.lastIndexOf('-')), v = id.slice(id.lastIndexOf('-') + 1)
  try {
    await ytdlp(['-f', 'b[vcodec^=h264]/b[vcodec!=none]', '-S', '+size', '--no-write-info-json', '--sleep-requests', '1', '-o', path.join(UT, `${id}.%(ext)s`), `https://www.tiktok.com/@${k}/video/${v}`], { timeout: 120_000 })
    if (++ok % 25 === 0) console.log(`  del ${DEL}: ${ok} hämtade`)
  } catch (e) { fel++; console.warn(`${id}: ${e.message.slice(0, 120)}`) }
}
console.log(`del ${DEL} klar: ${ok} nya, ${fel} fel`)
