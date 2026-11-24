// Kontaktark per kund (6 nov 2026): hela historiken som en bild, rader om 10 klipp, nyast först.
// Varje ruta: klippets omslag, familjebokstav (D dialogsketch, T tilltal med mat, M stämning/mat, R trend,
// K kampanj, G gata, X text utan tal, O ordvits, A absurd) och månad. Färgen på bandet visar gruppen
// (person grön, mat orange, trend lila, kampanj blå), så att faserna syns på avstånd.
// Omslagen hämtas färska med yt-dlp --flat-playlist (ett anrop per profil); ffmpeg ritar och lägger ihop.
//   node format/kontaktark.mjs konto1,konto2
// Resultat: karta/videoforandring/miles/serie/<konto>.jpg
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { execFile } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'

const YTDLP = ['--from', 'yt-dlp[default,curl-cffi]==2026.10.26', 'yt-dlp']
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const kor = (cmd, a, opt = {}) => new Promise((res, rej) => execFile(cmd, a, { maxBuffer: 512 * 1024 * 1024, windowsHide: true, ...opt }, (e, out, err) => e ? rej(new Error(String(err).slice(-300))) : res(out)))
const FAM = Object.fromEntries(Object.entries(las(path.join(DATA, 'format', 'familjer', 'familjer-lokal.json'))).map(([k, v]) => [k, v.familj]))
const BOK = { dialogsketch: 'D', tilltal_med_mat: 'T', stamningsmontage: 'M', trend: 'R', kampanj: 'K', gatuinslag: 'G', text_utan_tal: 'X', ordvits: 'O', absurd_improvisation: 'A', annat: '.' }
const FARG = { D: '0x2e7d32', O: '0x2e7d32', A: '0x2e7d32', G: '0x2e7d32', T: '0x2e7d32', X: '0x2e7d32', M: '0xef6c00', R: '0x7b1fa2', K: '0x1565c0', '.': '0x616161', '?': '0x000000' }
const UT = path.join(DATA, '..', 'karta', 'videoforandring', 'miles', 'serie'), TMP = path.join(os.tmpdir(), 'kontaktark')
fs.mkdirSync(UT, { recursive: true })
const FONT = "C\\:/Windows/Fonts/arialbd.ttf"

async function ark(k) {
  const d = path.join(TMP, k); fs.mkdirSync(d, { recursive: true })
  const pl = JSON.parse(await kor('uvx', [...YTDLP, '--flat-playlist', '-J', `https://www.tiktok.com/@${k}`], { timeout: 300_000 }))
  const datum = Object.fromEntries(las(path.join(DATA, 'bank', k, 'lista.json')).klipp.map(x => [x.id, x.datum]))
  const klipp = pl.entries.map(e => ({ id: String(e.id), url: (e.thumbnails || []).find(t => t.id === 'cover')?.url ?? e.thumbnails?.[0]?.url, datum: datum[e.id] ?? (e.timestamp ? new Date(e.timestamp * 1000).toISOString().slice(0, 10) : '') }))
    .sort((a, b) => b.datum.localeCompare(a.datum))
  let nasta = 0
  const arb = async () => { while (nasta < klipp.length) { const i = nasta++, x = klipp[i]; const ut = path.join(d, `${String(i).padStart(4, '0')}.jpg`); if (fs.existsSync(ut)) continue
    const b = BOK[FAM[`${k}-${x.id}`]] ?? '?', text = `${b}  ${x.datum.slice(2, 7)}`
    const rita = `scale=120:213:force_original_aspect_ratio=increase,crop=120:213,drawbox=y=ih-30:w=iw:h=30:color=${FARG[b]}@0.9:t=fill,drawtext=fontfile='${FONT}':text='${text}':fontcolor=white:fontsize=17:x=6:y=h-24`
    try {
      if (!x.url) throw new Error('inget omslag')
      const bild = path.join(d, `${x.id}.src`)
      if (!fs.existsSync(bild)) { const r = await fetch(x.url, { signal: AbortSignal.timeout(20_000) }); if (!r.ok) throw new Error(`${r.status}`); fs.writeFileSync(bild, Buffer.from(await r.arrayBuffer())) }
      await kor('ffmpeg', ['-v', 'error', '-y', '-i', bild, '-vf', rita, '-frames:v', '1', ut])
    } catch { await kor('ffmpeg', ['-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=0x222222:s=120x213', '-vf', rita.replace(/^scale=[^,]+,crop=[^,]+,/, ''), '-frames:v', '1', ut]) }
  } }
  await Promise.all(Array.from({ length: 8 }, arb))
  const rader = Math.ceil(klipp.length / 10)
  // fyll sista raden med vita rutor
  for (let i = klipp.length; i < rader * 10; i++) await kor('ffmpeg', ['-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=0xffffff:s=120x213', '-frames:v', '1', path.join(d, `${String(i).padStart(4, '0')}.jpg`)])
  const fil = path.join(UT, `${k}.jpg`)
  // rader med hstack (10 rutor), sedan vstack (tile-filtret tappade rutor med bildsekvenser här)
  const radfiler = []
  for (let r = 0; r < rader; r++) {
    const rf = path.join(d, `rad${String(r).padStart(3, '0')}.png`), inn = []
    for (let i = 0; i < 10; i++) inn.push('-i', path.join(d, `${String(r * 10 + i).padStart(4, '0')}.jpg`))
    const fc = Array.from({ length: 10 }, (_, i) => `[${i}:v]format=rgb24,setsar=1,pad=126:219:3:3:white[p${i}]`).join(';') + ';' + Array.from({ length: 10 }, (_, i) => `[p${i}]`).join('') + 'hstack=inputs=10'
    await kor('ffmpeg', ['-v', 'error', '-y', ...inn, '-filter_complex', fc, '-frames:v', '1', rf])
    radfiler.push(rf)
  }
  const inn = radfiler.flatMap(f => ['-i', f])
  const fc = radfiler.length > 1 ? radfiler.map((_, i) => `[${i}:v]`).join('') + `vstack=inputs=${radfiler.length}` : '[0:v]null'
  await kor('ffmpeg', ['-v', 'error', '-y', ...inn, '-filter_complex', fc, '-frames:v', '1', '-q:v', '3', fil])
  console.log(`${k}: ${klipp.length} klipp, ${rader} rader -> ${path.relative(path.join(DATA, '..'), fil)}`)
}
for (const k of (process.argv[2] || '').split(',').filter(Boolean)) { try { await ark(k) } catch (e) { console.log(`${k}: FEL ${e.message}`) } }
