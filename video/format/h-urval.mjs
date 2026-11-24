// Harness steg 1 (4 nov 2026): kunder och bibliotek. Urvalet görs ur befintlig data (E4-lager från
// Lite, residualer från baslinje.json, serierna) och låses i data/format/harness/urval.json innan
// formatkort v4 körs. Kriterierna står i filen.
//
//   node format/h-urval.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const H = path.join(DATA, 'format', 'harness')
fs.mkdirSync(H, { recursive: true })
if (fs.existsSync(path.join(H, 'urval.json'))) { console.log('urvalet är redan låst'); process.exit(0) }
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const KUNDER = ['pizzeriamums', 'chickenstreet.canada', 'kebabbabes', 'blackstonesteakhouse', 'babulsofficial', 'anettesrestaurang']
const e4 = new Map(las(path.join(DATA, 'format', 'e4', 'urval.json')).map(k => [k.id, k]))
const LD = path.join(DATA, 'format', 'e4', 'lager-gemini-3.1-flash-lite')
const lager = fs.readdirSync(LD).map(f => las(path.join(LD, f))).map(x => ({ ...x, ...e4.get(x.id) })).filter(x => Number.isFinite(x.rv) && !KUNDER.includes(x.konto))
const kalib = las(path.join(DATA, 'format', 'kalib', 'urval.json'))

function valj(filt, antal, maxPerKonto) {
  const ut = [], per = new Map()
  for (const x of lager.filter(filt).sort((a, b) => b.rv - a.rv)) {
    if ((per.get(x.konto) ?? 0) >= maxPerKonto) continue
    ut.push(x); per.set(x.konto, (per.get(x.konto) ?? 0) + 1)
    if (ut.length >= antal) break
  }
  return ut
}
const KRITERIER = {
  karna: 'Lite: spelad situation, personer minst halva tiden, fristående idé ≥ 3 och humor ≥ 1. Klippet gick bättre än kontots norm (rv > 0). Sorterat på rv, högst 2 per konto, 25 klipp.',
  mitten: 'Lite: (tävling, uppmaning eller erbjudande med personer minst halva tiden) eller (matandel ≥ 3 med personer minst tre fjärdedelar av tiden) eller verklig händelse. rv > 0, inte redan i kärnan. Sorterat på rv, högst 1 per konto, 15 klipp.',
  kalib: 'De 30 kalibreringsklippen. Ägaren har bedömt 27 av dem.',
  uteslutna: `Kundernas egna klipp: ${KUNDER.join(', ')}.`,
}
const karna = valj(x => x.roll && x.andel_person >= 2 && x.fristaende_ide >= 3 && x.humor >= 1 && x.rv > 0, 25, 2)
const kIds = new Set(karna.map(x => x.id))
const mitten = valj(x => !kIds.has(x.id) && x.rv > 0 && (((x.tavling || x.uppmaning || x.erbjudande) && x.andel_person >= 2) || (x.mat_andel >= 3 && x.andel_person >= 3) || x.handelse), 15, 1)
const bibliotek = [
  ...kalib.filter(k => !KUNDER.includes(k.konto)).map(k => ({ id: k.id, konto: k.konto, url: k.url, fil: k.fil, kalla: 'kalib', nr: k.nr })),
  ...karna.map(x => ({ id: x.id, konto: x.konto, url: x.url, vid: x.vid, fil: `C:/Users/praiseworthy/Downloads/letrend-bibliotek/${x.konto}/${x.vid}.mp4`, kalla: 'karna', rv: x.rv })),
  ...mitten.map(x => ({ id: x.id, konto: x.konto, url: x.url, vid: x.vid, fil: `C:/Users/praiseworthy/Downloads/letrend-bibliotek/${x.konto}/${x.vid}.mp4`, kalla: 'mitten', rv: x.rv })),
]
fs.writeFileSync(path.join(H, 'urval.json'), JSON.stringify({ last: new Date().toISOString(), kriterier: KRITERIER, kunder: KUNDER, bibliotek }, null, 1))
console.log(`låst: ${KUNDER.length} kunder, bibliotek ${bibliotek.length} klipp (kalib ${bibliotek.filter(b => b.kalla === 'kalib').length}, kärna ${karna.length}, mitten ${mitten.length})`)
console.log('kärna:', karna.map(x => x.konto).join(', '))
console.log('mitten:', mitten.map(x => x.konto).join(', '))
