// Tilltalshyllan (4 nov 2026): bankens direkt_tilltal med rekonbar >= 4 utan v5-kort, högst 3 per konto.
//   node format/bank-tratt3.mjs [--per 3]
import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg } from '../analys/verktyg.mjs'
const args = process.argv.slice(2), PER = Number(args.includes('--per') ? args[args.indexOf('--per') + 1] : 5)
const F = path.join(DATA, 'format'), B = path.join(F, 'bank3'); fs.mkdirSync(B, { recursive: true })
const T = (() => { const S = path.join(DATA, 'bank', 'sallning'), kort = new Set(['harness/v5', 'e6/kort', 'e6r/kort', 'bank2/kort'].flatMap(d => fs.existsSync(path.join(F, d)) ? fs.readdirSync(path.join(F, d)).map(f => f.replace(/.json$/, '')) : [])); return fs.readdirSync(S).map(f => JSON.parse(fs.readFileSync(path.join(S, f), 'utf8'))).filter(x => x.typ === 'direkt_tilltal' && x.rekonbar >= 4 && !kort.has(x.id)) })()
let fro = 333; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }
const per = {}; for (const x of T) (per[x.konto] ??= []).push(x)
const val = Object.keys(per).sort().flatMap(k => bl(per[k]).slice(0, PER)).map(x => { const vid = x.id.slice(x.konto.length + 1); return { id: x.id, konto: x.konto, vid, url: `https://www.tiktok.com/@${x.konto}/video/${vid}`, fil: `C:/Users/praiseworthy/Downloads/letrend-bank/${x.konto}/${vid}.mp4`, kalla: 'bank3', innehall: x.innehall } })
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
