// Urval för kalibreringen av formatkortet mot ägaren: 30 klipp i fem grupper, spridda över
// sållningens innehållstyper, med fast slumpfrö. Laddar ner det som saknas på disk.
//
//   node format/kalib-urval.mjs [--fro 7]
// Resultat: data/format/kalib/urval.json (gruppen och typen visas inte för ägaren).
import fs from 'node:fs'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg } from '../analys/verktyg.mjs'

const args = process.argv.slice(2)
const FRO = Number(args[args.indexOf('--fro') + 1] || 7)
const BANK = 'C:/Users/praiseworthy/Downloads/letrend-bank'
const UT = path.join(DATA, 'format', 'kalib')
fs.mkdirSync(UT, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))

let fro = FRO
const slump = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const blanda = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(slump() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }

const kallor = las(path.join(DATA, 'kallor.json'))
const sp = las(path.join(DATA, 'profil', 'stickprov.json')).klipp
const godk = new Set(fs.readFileSync(path.join(DATA, 'profil', 'godkanda.txt'), 'utf8').split(/\r?\n/).filter(Boolean))
const fore = new Set((fs.readFileSync(path.join(DATA, 'profil', 'forebilder.txt'), 'utf8').match(/@[a-z0-9._]+/g) ?? []).map(h => h.slice(1)))
const pilot = new Set(fs.readdirSync(path.join(DATA, 'format', 'google_gemini-3.1-pro-preview')).map(f => f.replace(/\.json$/, '')))
const BALANS = new Set(['mondocoatbridge', 'babulsofficial'])
// Privatpersoner och kreatörer i den gamla banken räknas inte som verksamheter.
const PRIVAT = new Set(['27annnn', 'alexandra', 'bram', 'brams', 'eliassafar1', 'hermanoerkano', 'jasse', 'juiceboxswe', 'kristijanlane', 'marianathly', 'matteus', 'megicmike133', 'sampev2', 'simonkafi', 'therese', 'mandiholm1'])
const STRUKNA = ['bunsik_uk', 'gasolinegrill', 'bennepastabar', 'berlinerdonermalmo']

const grupp = h => BALANS.has(h) ? 'balans' : godk.has(h) ? 'ja' : fore.has(h) ? 'forebild' : PRIVAT.has(h) ? null : 'bank'
const typAv = id => { const f = path.join(DATA, 'bank', 'sallning', `${id}.json`); return fs.existsSync(f) ? las(f).typ : null }

// Inom en grupp: varva mellan typer och konton, så att en grupp inte blir bara sketcher eller ett konto.
function valj(kandidater, n) {
  const perTyp = new Map()
  for (const k of blanda(kandidater)) { const l = perTyp.get(k.typ) ?? []; l.push(k); perTyp.set(k.typ, l) }
  const ut = [], konton = new Map()
  for (let varv = 0; ut.length < n && varv < 50; varv++) {
    for (const [, l] of [...perTyp.entries()].sort((a, b) => b[1].length - a[1].length)) {
      const i = l.findIndex(k => (konton.get(k.handtag) ?? 0) <= varv)
      if (i < 0 || ut.length >= n) continue
      const [k] = l.splice(i, 1); ut.push(k); konton.set(k.handtag, (konton.get(k.handtag) ?? 0) + 1)
    }
  }
  return ut
}

const STORLEK = { balans: 6, ja: 8, forebild: 5, bank: 6 }
const urval = []
for (const [g, n] of Object.entries(STORLEK)) {
  const kand = sp.map(k => ({ ...k, key: `${k.handtag}-${k.id}` }))
    .filter(k => grupp(k.handtag) === g && !pilot.has(k.key))
    .map(k => ({ ...k, typ: typAv(k.key) })).filter(k => k.typ && k.typ !== 'annat')
  urval.push(...valj(kand, n).map(k => ({ ...k, grupp: g })))
}

// Strukna konton finns inte i banken: lista dem med yt-dlp och dra behöriga klipp (5–90 s, minst 14 dagar).
const yt = (...a) => spawnSync('uvx', ['yt-dlp', ...a], { encoding: 'utf8', maxBuffer: 1e8, windowsHide: true })
const nu = Date.now() / 1000
const strukna = []
for (const h of STRUKNA) {
  const r = yt('--flat-playlist', '-J', '--playlist-end', '60', `https://www.tiktok.com/@${h}`)
  try {
    const e = (JSON.parse(r.stdout).entries ?? []).filter(x => x.duration >= 5 && x.duration <= 90 && (!x.timestamp || nu - x.timestamp > 14 * 86400))
    strukna.push(...blanda(e).slice(0, 2).map(x => ({ handtag: h, id: String(x.id), url: `https://www.tiktok.com/@${h}/video/${x.id}`, key: `${h}-${x.id}`, typ: null, grupp: 'struken' })))
  } catch { console.warn(`${h}: kunde inte listas`) }
}
urval.push(...blanda(strukna).slice(0, 5))

// Ladda ner det som saknas.
const FORMAT = "b[ext=mp4][height<=1024][vcodec~='^(h265|hevc|bytevc1)']/b[ext=mp4][height<=1024]/b[ext=mp4]/b"
for (const k of urval) {
  const fil = kallor[k.key]?.fil && fs.existsSync(kallor[k.key].fil) ? kallor[k.key].fil : path.join(BANK, k.handtag, `${k.id}.mp4`).replace(/\\/g, '/')
  if (!fs.existsSync(fil)) {
    fs.mkdirSync(path.dirname(fil), { recursive: true })
    const r = yt('--ffmpeg-location', verktyg.ffmpeg, '-f', FORMAT, '--merge-output-format', 'mp4', '--no-progress', '-o', fil, k.url)
    if (!fs.existsSync(fil)) console.warn(`${k.key}: hämtningen föll ${r.stderr.split('\n').filter(l => /ERROR/.test(l)).join(' ').slice(0, 200)}`)
  }
  k.fil = fil
}

const klara = blanda(urval.filter(k => fs.existsSync(k.fil))).map((k, i) => ({ nr: i + 1, id: k.key, konto: k.handtag, url: k.url, fil: k.fil, grupp: k.grupp, typ: k.typ }))
fs.writeFileSync(path.join(UT, 'urval.json'), JSON.stringify(klara, null, 1))
const rakna = f => Object.entries(klara.reduce((m, k) => ({ ...m, [f(k)]: (m[f(k)] ?? 0) + 1 }), {})).map(([a, b]) => `${a} ${b}`).join(', ')
console.log(`${klara.length} klipp. Grupper: ${rakna(k => k.grupp)}. Typer: ${rakna(k => k.typ)}`)
