// Importera klipp som laddats ner på annat sätt (t.ex. bulktik.com eller ssstik): en mapp med mp4-filer,
// en undermapp per konto eller kontot i filnamnet (@konto_videoid.mp4, ssstik.io_@konto_id.mp4).
//
//   node bank/importera.mjs <mapp> [--konto namn]
//
// Klippen registreras i data/kallor.json som <konto>-<id>. Metadata (visningar, gillanden) saknas då;
// bank/hamta.mjs ger den, och urvalet väger engagemang bara där det finns.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const args = process.argv.slice(2)
const mapp = args.find(a => !a.startsWith('--'))
const kontoArg = args.includes('--konto') ? args[args.indexOf('--konto') + 1] : null
if (!mapp || !fs.existsSync(mapp)) { console.error('ange en mapp med mp4-filer'); process.exit(1) }

const filer = []
const gaIgenom = d => { for (const f of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, f.name); if (f.isDirectory()) gaIgenom(p); else if (/\.mp4$/i.test(f.name)) filer.push(p) } }
gaIgenom(mapp)

const kallorFil = path.join(DATA, 'kallor.json')
const kallor = fs.existsSync(kallorFil) ? JSON.parse(fs.readFileSync(kallorFil, 'utf8')) : {}
let nya = 0
for (const f of filer) {
  const namn = path.basename(f, path.extname(f))
  const m = namn.match(/@([\w.\-]+?)[_\- ]+(\d{6,})/)
  const konto = kontoArg ?? m?.[1] ?? (path.dirname(f) !== path.resolve(mapp) ? path.basename(path.dirname(f)) : 'okand')
  const vid = m?.[2] ?? (namn.match(/(\d{8,})/)?.[1] ?? namn.replace(/[^\w.\-]/g, '_'))
  const id = `${konto}-${vid}`
  if (kallor[id]) continue
  kallor[id] = { fil: f.replaceAll('\\', '/'), konto, kalla: 'import', video: vid }
  nya++
}
fs.writeFileSync(kallorFil, JSON.stringify(kallor, null, 2))
console.log(`${filer.length} filer, ${nya} nya i kallor.json`)
