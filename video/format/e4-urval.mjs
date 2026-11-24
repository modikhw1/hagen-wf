// E4 (3 nov 2026): urval och nedladdning. Upp till 14 slumpvisa klipp per verksamhetskonto ur det
// osållade stickprovet (profil/stickprov.json), med residualer från profil/baslinje.json. Privatpersoner
// och de 30 kalibreringsklippen räknas inte. Filerna läggs i Downloads/letrend-e4 och raderas efter
// märkningen (format/e4.mjs). kallor.json rörs inte.
//
//   node format/e4-urval.mjs [--per-konto 14] [--hamta-par 6] [--batch 12]
// Resultat: data/format/e4/urval.json
import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg } from '../analys/verktyg.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PER = Number(varde('--per-konto', 14))
const HAMTA_PAR = Number(varde('--hamta-par', 6))
const BATCH = Number(varde('--batch', 12))
const NED = 'C:/Users/praiseworthy/Downloads/letrend-e4'
const UT = path.join(DATA, 'format', 'e4')
fs.mkdirSync(UT, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))

const PRIVAT = new Set(['27annnn', 'alexandra', 'bram', 'brams', 'eliassafar1', 'hermanoerkano', 'jasse', 'juiceboxswe', 'kristijanlane', 'marianathly', 'matteus', 'megicmike133', 'sampev2', 'simonkafi', 'therese', 'mandiholm1'])
const kalib = new Set(las(path.join(DATA, 'format', 'kalib', 'urval.json')).map(k => k.id))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const kallor = las(path.join(DATA, 'kallor.json'))
const sp = las(path.join(DATA, 'profil', 'stickprov.json')).klipp

let fro = 20261103
const slump = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const perKonto = new Map()
for (const k of sp) {
  const id = `${k.handtag}-${k.id}`, r = bas.get(id)
  if (PRIVAT.has(k.handtag) || kalib.has(id) || !r || !(r.langd >= 5 && r.langd <= 90)) continue
  const l = perKonto.get(k.handtag) ?? []; l.push({ id, konto: k.handtag, vid: k.id, url: k.url, langd: r.langd, rv: r.rv, rl: r.rl, rc: r.rc, rs: r.rs }); perKonto.set(k.handtag, l)
}
const urval = []
for (const [, l] of perKonto) {
  for (let i = l.length - 1; i > 0; i--) { const j = Math.floor(slump() * (i + 1)); [l[i], l[j]] = [l[j], l[i]] }
  urval.push(...l.slice(0, PER))
}
// Filer som redan ligger på disk återanvänds, resten hämtas.
for (const k of urval) {
  const befintlig = kallor[k.id]?.fil
  k.fil = befintlig && !kallor[k.id].raderad && fs.existsSync(befintlig) ? befintlig : `${NED}/${k.konto}/${k.vid}.mp4`
}
const behov = urval.filter(k => !fs.existsSync(k.fil))
console.log(`${urval.length} klipp från ${perKonto.size} konton, ${behov.length} att hämta`)

const FORMAT = "b[ext=mp4][height<=1024][vcodec~='^(h265|hevc|bytevc1)']/b[ext=mp4][height<=1024]/b[ext=mp4]/b"
const SPARR = /HTTP Error 403|HTTP Error 429|captcha|rate.?limit|too many requests|blocked/i
const paus = ms => new Promise(r => setTimeout(r, ms))
function batch(lista) {
  const dir = path.join(NED, `_b${Math.random().toString(36).slice(2, 8)}`)
  fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(path.join(dir, 'lista.txt'), lista.map(k => k.url).join('\n'))
  return new Promise(res => {
    const p = spawn('uvx', ['yt-dlp', '--ffmpeg-location', verktyg.ffmpeg, '-f', FORMAT, '--merge-output-format', 'mp4', '--ignore-errors', '--no-progress', '--no-overwrites', '-o', path.join(dir, '%(id)s.%(ext)s'), '-a', path.join(dir, 'lista.txt')], { windowsHide: true })
    let fel = ''
    const stopp = setTimeout(() => p.kill(), 15 * 60_000)
    p.stderr.on('data', d => { fel += d }); p.stdout.on('data', () => {})
    p.on('close', () => {
      clearTimeout(stopp)
      for (const k of lista) { const f = path.join(dir, `${k.vid}.mp4`); if (fs.existsSync(f)) { fs.mkdirSync(path.dirname(k.fil), { recursive: true }); fs.renameSync(f, k.fil) } }
      fs.rmSync(dir, { recursive: true, force: true })
      res(fel.split('\n').filter(l => /ERROR/.test(l)))
    })
  })
}
const batcher = []
for (let i = 0; i < behov.length; i += BATCH) batcher.push(behov.slice(i, i + BATCH))
let nasta = 0, klara = 0, par = HAMTA_PAR
const t0 = Date.now()
await Promise.all(Array.from({ length: HAMTA_PAR }, async (_, plats) => {
  while (nasta < batcher.length) {
    if (plats >= par) { await paus(5000); continue }
    const b = batcher[nasta++]
    const fel = await batch(b)
    klara += b.length
    if (fel.filter(l => SPARR.test(l)).length >= Math.max(2, b.length / 3)) { par = Math.max(1, Math.floor(par / 2)); console.log(`vakt: spärr, ${par} parallellt, 10 min paus`); await paus(600_000) }
    if (nasta % 10 === 0) console.log(`${klara}/${behov.length} behandlade, ${((Date.now() - t0) / 1000 / klara).toFixed(2)} s/klipp`)
  }
}))
const finns = urval.filter(k => fs.existsSync(k.fil))
fs.writeFileSync(path.join(UT, 'urval.json'), JSON.stringify(finns, null, 1))
console.log(`klart: ${finns.length} av ${urval.length} klipp finns på disk`)
