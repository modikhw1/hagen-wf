// E6 urval (4 nov 2026): 30 konton × 10 klipp ur E4 med utfall mot kontots egen norm, för att skilja
// preferens (ägarens omdöme) från nytta (utfall inom kontot). Fast frö. Kunderna i pass 4–5 och klipp som
// redan ligger i biblioteket (valda på utfall) utesluts. Hämtar filer som saknas.
//   node format/e6-urval.mjs
import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg } from '../analys/verktyg.mjs'

const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const F = path.join(DATA, 'format'), E = path.join(F, varde('--ut', 'e6')); fs.mkdirSync(E, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const e4 = las(path.join(F, 'e4', 'urval.json'))
const H = las(path.join(F, 'harness', 'urval.json'))
const forra = varde('--utesluta') ? new Set(las(path.join(F, varde('--utesluta'), 'urval.json')).map(k => k.konto)) : new Set()
const bort = new Set([...H.kunder, ...forra]), ibib = new Set(H.bibliotek.map(k => k.id))
let fro = Number(varde('--fro', 606)); const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }
const per = new Map(); for (const k of e4) { if (bort.has(k.konto) || ibib.has(k.id)) continue; const l = per.get(k.konto) ?? []; l.push(k); per.set(k.konto, l) }
const konton = bl([...per.entries()].filter(([, l]) => l.length >= 10).map(([k]) => k).sort()).slice(0, 30)
const urval = konton.flatMap(k => bl(per.get(k)).slice(0, 10)).map(k => ({ ...k, fil: k.fil ?? `C:/Users/praiseworthy/Downloads/letrend-e4/${k.konto}/${k.vid}.mp4` }))
fs.writeFileSync(path.join(E, 'urval.json'), JSON.stringify(urval, null, 1))
fs.writeFileSync(path.join(E, 'ids.txt'), urval.map(k => k.id).join('\n'))
console.log(`${konton.length} konton, ${urval.length} klipp, ${urval.filter(k => fs.existsSync(k.fil)).length} finns på disk`)

const FORMAT = "b[ext=mp4][height<=1024][vcodec~='^(h265|hevc|bytevc1)']/b[ext=mp4][height<=1024]/b[ext=mp4]/b"
function hamta(lista) {
  const dir = path.join('C:/Users/praiseworthy/Downloads/letrend-e4', `_b${Math.random().toString(36).slice(2, 8)}`); fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(path.join(dir, 'lista.txt'), lista.map(k => k.url).join('\n'))
  return new Promise(res => { const p = spawn('uvx', ['yt-dlp', '--ffmpeg-location', verktyg.ffmpeg, '-f', FORMAT, '--merge-output-format', 'mp4', '--ignore-errors', '--no-progress', '-o', path.join(dir, '%(id)s.%(ext)s'), '-a', path.join(dir, 'lista.txt')], { windowsHide: true }); p.stdout.on('data', () => {}); p.stderr.on('data', () => {}); p.on('close', () => { for (const k of lista) { const f = path.join(dir, `${k.vid}.mp4`); if (fs.existsSync(f)) { fs.mkdirSync(path.dirname(k.fil), { recursive: true }); fs.renameSync(f, k.fil) } } fs.rmSync(dir, { recursive: true, force: true }); res() }) })
}
const behov = urval.filter(k => !fs.existsSync(k.fil)), B = []
for (let i = 0; i < behov.length; i += 12) B.push(behov.slice(i, i + 12))
let bi = 0; await Promise.all(Array.from({ length: 6 }, async () => { while (bi < B.length) await hamta(B[bi++]) }))
console.log(`hämtat; ${urval.filter(k => fs.existsSync(k.fil)).length} av ${urval.length} finns`)
