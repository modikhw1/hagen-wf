// Biblioteket v6, tratten steg 2 (4 nov 2026): ur bankens 2 632 relaterbara sketcher utan v5-kort, högst 5 per
// konto bland dem med rekonbar ≥ 4 (fast frö), för bredd över kontona. Hämtar filerna. Sedan körs
//   LOVABLE_KONTO=4 node format/kort5.mjs --extra ../data/format/bank2/extra.json --idfil ../data/format/bank2/ids.txt --ut ../bank2/kort --modell google/gemini-3.8-flash --kortdoktrin
//   node format/bank-tratt2.mjs [--per 5]
import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg } from '../analys/verktyg.mjs'
const args = process.argv.slice(2), PER = Number(args.includes('--per') ? args[args.indexOf('--per') + 1] : 5)
const F = path.join(DATA, 'format'), B = path.join(F, 'bank2'); fs.mkdirSync(B, { recursive: true })
const T = JSON.parse(fs.readFileSync(path.join(F, 'harness', 'bank-tratt.json'), 'utf8')).sketcher_utan_kort.filter(x => x.rekonbar >= 4)
let fro = 222; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }
const per = {}; for (const x of T) (per[x.konto] ??= []).push(x)
const val = Object.keys(per).sort().flatMap(k => bl(per[k]).slice(0, PER)).map(x => { const vid = x.id.slice(x.konto.length + 1); return { id: x.id, konto: x.konto, vid, url: `https://www.tiktok.com/@${x.konto}/video/${vid}`, fil: `C:/Users/praiseworthy/Downloads/letrend-bank/${x.konto}/${vid}.mp4`, kalla: 'bank2', innehall: x.innehall } })
const FORMAT = "b[ext=mp4][height<=1024][vcodec~='^(h265|hevc|bytevc1)']/b[ext=mp4][height<=1024]/b[ext=mp4]/b"
function hamta(lista) {
  const dir = path.join('C:/Users/praiseworthy/Downloads/letrend-bank', `_b${Math.random().toString(36).slice(2, 8)}`); fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(path.join(dir, 'lista.txt'), lista.map(k => k.url).join('\n'))
  return new Promise(res => { const p = spawn('uvx', ['yt-dlp', '--ffmpeg-location', verktyg.ffmpeg, '-f', FORMAT, '--merge-output-format', 'mp4', '--ignore-errors', '--no-progress', '-o', path.join(dir, '%(id)s.%(ext)s'), '-a', path.join(dir, 'lista.txt')], { windowsHide: true }); p.stdout.on('data', () => {}); p.stderr.on('data', () => {}); p.on('close', () => { for (const k of lista) { const f = path.join(dir, `${k.vid}.mp4`); if (fs.existsSync(f)) { fs.mkdirSync(path.dirname(k.fil), { recursive: true }); fs.renameSync(f, k.fil) } } fs.rmSync(dir, { recursive: true, force: true }); res() }) })
}
const behov = val.filter(k => !fs.existsSync(k.fil)), G = []
for (let i = 0; i < behov.length; i += 12) G.push(behov.slice(i, i + 12))
let gi = 0; await Promise.all(Array.from({ length: 6 }, async () => { while (gi < G.length) await hamta(G[gi++]) }))
const ok = val.filter(k => fs.existsSync(k.fil))
fs.writeFileSync(path.join(B, 'extra.json'), JSON.stringify(ok))
fs.writeFileSync(path.join(B, 'ids.txt'), ok.map(k => k.id).join('\n'))
console.log(`${val.length} valda från ${Object.keys(per).length} konton, ${ok.length} finns på disk`)
