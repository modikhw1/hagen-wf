// E3-lite (3 nov 2026): vad följer ägarens omdömen egentligen? Ägarens poäng (bibliotek ja 2,
// villkorat 1, nej 0; funktion kött 2, stöd 1, utanför 0) jämförs med klippens lagervärden. Lagervärdena
// är modellernas samsyn ur E1: medel över alla bedömningar som finns per klipp.
// Driften mellan passen räknas bort genom att poängen centreras inom varje pass.
//
//   node format/e3-avslojat.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { LAGER } from './lager.mjs'
import { spearman } from '../profil/baslinje.mjs'

const F = path.join(DATA, 'format')
const urval = JSON.parse(fs.readFileSync(path.join(F, 'kalib', 'urval.json'), 'utf8'))
const agare = JSON.parse(fs.readFileSync(path.join(F, 'kalib', 'agare.json'), 'utf8')).klipp
const e1 = JSON.parse(fs.readFileSync(path.join(F, 'e1', 'analys.json'), 'utf8')).lager
const bas = new Map(JSON.parse(fs.readFileSync(path.join(DATA, 'profil', 'baslinje.json'), 'utf8')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const tal = v => typeof v === 'boolean' ? (v ? 1 : 0) : v
const samsyn = {}
for (const m of fs.readdirSync(path.join(F, 'e1')).filter(d => fs.statSync(path.join(F, 'e1', d)).isDirectory()))
  for (const c of fs.readdirSync(path.join(F, 'e1', m))) for (const f of fs.readdirSync(path.join(F, 'e1', m, c))) {
    const x = JSON.parse(fs.readFileSync(path.join(F, 'e1', m, c, f), 'utf8'))
    const s = samsyn[x.id] ??= {}
    for (const [n, [typ]] of Object.entries(LAGER)) if (typ !== 'kat' && x[n] != null) (s[n] ??= []).push(tal(x[n]))
  }
const NR = Object.keys(agare).map(Number)
const pass = nr => nr <= 10 ? 1 : nr <= 20 ? 2 : 3
const POANG = { bibliotek: { ja: 2, villkorat: 1, nej: 0 }, funktion: { kott: 2, stod: 1, utanfor: 0 } }
const centrera = (mal) => { const v = NR.map(nr => POANG[mal][agare[nr][mal]]); const m = p => { const x = NR.map((nr, i) => [nr, v[i]]).filter(([nr]) => pass(nr) === p).map(([, y]) => y); return x.reduce((a, b) => a + b, 0) / x.length }; const mp = { 1: m(1), 2: m(2), 3: m(3) }; return NR.map((nr, i) => v[i] - mp[pass(nr)]) }

const rader = []
for (const [n, [typ]] of Object.entries(LAGER)) {
  if (typ === 'kat') continue
  const x = NR.map(nr => { const v = samsyn[urval[nr - 1].id]?.[n]; return v?.length ? v.reduce((a, b) => a + b, 0) / v.length : NaN })
  const rad = { lager: n, stabil: e1[n]?.stabil, alfa: e1[n]?.alfa }
  for (const mal of ['bibliotek', 'funktion']) { rad[mal] = spearman(x, centrera(mal)); rad[`${mal}_ra`] = spearman(x, NR.map(nr => POANG[mal][agare[nr][mal]])) }
  rad.rv = spearman(x, NR.map(nr => bas.get(urval[nr - 1].id)?.rv ?? NaN))
  rader.push(rad)
}
// Permutationsgräns: hur stor |rho| blir av slumpen med n = 27?
let fro = 3; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const y = centrera('bibliotek'), xs = rader.map(r => r.lager)
const max = []
for (let t = 0; t < 2000; t++) { const p = [...y]; for (let i = p.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [p[i], p[j]] = [p[j], p[i]] } max.push(Math.abs(spearman(NR.map((_, i) => i), p))) }
max.sort((a, b) => a - b)
const grans = max[Math.floor(0.95 * max.length)]
fs.writeFileSync(path.join(F, 'kalib', 'e3-avslojat.json'), JSON.stringify({ grans95: grans, rader }, null, 1))
const f = x => Number.isFinite(x) ? (x >= 0 ? ' ' : '') + x.toFixed(2) : '  -  '
console.log(`n = ${NR.length} klipp. |rho| > ${grans.toFixed(2)} är ovanligt för slumpen (95 %, ett lager i taget).`)
console.log(`${'lager'.padEnd(16)} stabil | bibliotek (drift bort / rå) | funktion (drift bort / rå) | klippets rv`)
for (const r of rader.sort((a, b) => Math.abs(b.bibliotek) - Math.abs(a.bibliotek))) console.log(`${r.lager.padEnd(16)} ${r.stabil ? 'ja ' : '   '}    | ${f(r.bibliotek)} / ${f(r.bibliotek_ra)}${Math.abs(r.bibliotek) > grans ? ' *' : '  '}             | ${f(r.funktion)} / ${f(r.funktion_ra)}${Math.abs(r.funktion) > grans ? ' *' : '  '}            | ${f(r.rv)}`)
