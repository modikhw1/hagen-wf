// E13 (16 nov 2026): hämtar om klippen som behövs för den starka serieläsningen, eftersom Downloads/letrend-bank
// inte finns kvar. Per kund (de nio med ägarbetyg i pass 4–6): ett urval ur historiken (de 14 nyaste + 10 jämnt
// spridda över resten, så att faserna syns) samt alla kandidatklipp (pass 4–6 och serie9). Varje klipp skalas
// också ned till en liten kopia (240x426, 2 bilder/s, mono) så att en hel historik ryms i ett anrop.
//   node format/e13-hamta.mjs [--par 3] [--bara-plan]
// Resultat: data/format/e13/plan.json, Downloads/letrend-bank/<konto>/<id>.mp4, Downloads/letrend-e13/<konto>-<id>.mp4
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { ytdlp } from '../bank/hamta.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PAR = Number(varde('--par', 3))
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const H = path.join(DATA, 'format', 'harness'), E = path.join(DATA, 'format', 'e13')
const BANK = path.join(os.homedir(), 'Downloads', 'letrend-bank'), LITEN = path.join(os.homedir(), 'Downloads', 'letrend-e13')
fs.mkdirSync(E, { recursive: true }); fs.mkdirSync(LITEN, { recursive: true })
export const delaId = id => { const i = id.lastIndexOf('-'); return { konto: id.slice(0, i), video: id.slice(i + 1) } }
export const litenFil = id => path.join(LITEN, `${id}.mp4`)

// Historiken sågs av ägaren senast 6 nov; listorna hämtades 3 nov och används som de är.
const NYA = 14, SPRIDDA = 10
function historik(konto, undanta) {
  const L = las(path.join(DATA, 'bank', konto, 'lista.json')).klipp
    .filter(k => !(k.langd != null && (k.langd < 3 || k.langd > 120)) && !undanta.has(`${konto}-${k.id}`))
    .sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
  const nya = L.slice(0, NYA), rest = L.slice(NYA), spridda = []
  for (let i = 0; i < SPRIDDA && rest.length; i++) { const k = rest[Math.min(rest.length - 1, Math.floor((i + 0.5) * rest.length / SPRIDDA))]; if (!spridda.includes(k)) spridda.push(k) }
  return { antal: L.length, klipp: [...nya, ...spridda].map(k => ({ id: `${konto}-${k.id}`, datum: k.datum, langd: k.langd, visningar: k.visningar, text: k.text })) }
}

// Kandidater: pass 4–5 (validering), pass 6 och serie9.
const kand = {}
const lagg = (konto, id, kalla, extra = {}) => { (kand[konto] ??= []).push({ id, kalla, ...extra }) }
const U = las(path.join(H, 'validering', 'urval.json')), V = las(path.join(H, 'validering', 'agare.json'))
for (const [k, svar] of Object.entries(V.klipp)) for (const [pos, s] of Object.entries(svar)) { const c = U[k].klipp.find(x => String(x.pos) === pos); if (c && Number.isFinite(s.passform)) lagg(k, c.id, 'pass45', { pos: +pos, agare: s.passform }) }
const O6 = las(path.join(H, 'pass6', 'ordning.json')), A6 = las(path.join(H, 'pass6', 'agare.json'))
for (const [k, ids] of Object.entries(O6)) ids.forEach((id, i) => { const s = A6.klipp[k]?.[i + 1]; if (s) lagg(k, id, 'pass6', { pos: i + 1, agare: s.passform }) })
const S9 = las(path.join(DATA, 'format', 'serie9', 'kandidater.json'))
for (const [k, v] of Object.entries(S9)) for (const c of v.val) lagg(k, c.id, 'serie9', { niva: c.niva, familj: c.familj })

const plan = {}
for (const [konto, K] of Object.entries(kand)) plan[konto] = { historik: historik(konto, new Set(K.map(c => c.id))), kandidater: K }
fs.writeFileSync(path.join(E, 'plan.json'), JSON.stringify(plan, null, 1))
let alla = [...new Set(Object.values(plan).flatMap(p => [...p.historik.klipp.map(k => k.id), ...p.kandidater.map(k => k.id)]))]
console.log(`${Object.keys(plan).length} kunder, ${alla.length} klipp (${Object.values(plan).reduce((s, p) => s + p.historik.klipp.length, 0)} historik, ${new Set(Object.values(plan).flatMap(p => p.kandidater.map(k => k.id))).size} kandidater)`)
if (args.includes('--bara-plan')) process.exit(0)
// --bakifran: en andra process kan ta listan från andra hållet medan den första går
if (args.includes('--bakifran')) alla = alla.reverse()

async function ett(id) {
  const { konto, video } = delaId(id), dir = path.join(BANK, konto), fil = path.join(dir, `${video}.mp4`), liten = litenFil(id)
  if (fs.existsSync(liten)) return 'fanns'
  if (!fs.existsSync(fil)) {
    fs.mkdirSync(dir, { recursive: true })
    await ytdlp(['-f', 'bv*[height<=1280][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b', '--merge-output-format', 'mp4', '--write-info-json', '--no-write-comments', '--sleep-requests', '1', '-o', path.join(dir, '%(id)s.%(ext)s'), `https://www.tiktok.com/@${konto}/video/${video}`])
  }
  const tmp = liten + `.${process.pid}.tmp.mp4`
  await kor(verktyg.ffmpeg, ['-y', '-v', 'error', '-i', fil, '-t', '90', '-vf', 'fps=2,scale=240:426:force_original_aspect_ratio=decrease,pad=240:426:(ow-iw)/2:(oh-ih)/2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '33', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ac', '1', '-b:a', '32k', tmp])
  fs.renameSync(tmp, liten)
  return 'ny'
}
let i = 0, ny = 0, fel = []
await Promise.all(Array.from({ length: PAR }, async () => {
  while (i < alla.length) {
    const id = alla[i++]
    try { if (await ett(id) === 'ny') ny++ } catch (e) { fel.push({ id, fel: e.message.slice(0, 200) }) }
    if ((ny + fel.length) % 20 === 0 && ny + fel.length) console.log(`  ${i}/${alla.length}, ${ny} nya, ${fel.length} fel`)
  }
}))
fs.writeFileSync(path.join(E, args.includes('--bakifran') ? 'hamta-fel-b.json' : 'hamta-fel.json'), JSON.stringify(fel, null, 1))
const mb = alla.filter(id => fs.existsSync(litenFil(id))).reduce((s, id) => s + fs.statSync(litenFil(id)).size, 0) / 1e6
console.log(`klart: ${ny} nya, ${fel.length} fel, ${alla.filter(id => fs.existsSync(litenFil(id))).length}/${alla.length} små kopior (${mb.toFixed(0)} MB)`)
