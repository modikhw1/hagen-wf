// E4-analys enligt data/format/e4/forregistrering.json (låst före märkning och analys).
//   node format/e4-analys.mjs --modell gemini-3.8-flash
// Resultat: data/format/e4/analys-<modell>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { LAGER } from './lager.mjs'
import { spearman } from '../profil/baslinje.mjs'

const args = process.argv.slice(2)
const MODELL = args.includes('--modell') ? args[args.indexOf('--modell') + 1] : 'gemini-3.8-flash'
const E4 = path.join(DATA, 'format', 'e4')
const reg = JSON.parse(fs.readFileSync(path.join(E4, 'forregistrering.json'), 'utf8'))
const e1 = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'e1', 'analys.json'), 'utf8')).lager
const STABILA = Object.entries(e1).filter(([, r]) => r.stabil && r.typ !== 'kat').map(([n]) => n)
const urval = new Map(JSON.parse(fs.readFileSync(path.join(E4, 'urval.json'), 'utf8')).map(k => [k.id, k]))
const bas = new Map(JSON.parse(fs.readFileSync(path.join(DATA, 'profil', 'baslinje.json'), 'utf8')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const dir = path.join(E4, `lager-${MODELL}`)
const tal = v => typeof v === 'boolean' ? (v ? 1 : 0) : v
const rader = fs.readdirSync(dir).map(f => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'))).map(x => ({ ...x, ...urval.get(x.id), datum: bas.get(x.id)?.datum })).filter(r => Number.isFinite(r.rv))
const UTFALL = Object.keys(reg.utfall)

// Index: bara stabila lager ur förregistreringens listor.
const plus = reg.letrend_index.plus.filter(n => STABILA.includes(n)), minus = reg.letrend_index.minus.filter(n => STABILA.includes(n))
const z = n => { const v = rader.map(r => tal(r[n])); const m = v.reduce((a, b) => a + b) / v.length; const sd = Math.sqrt(v.reduce((a, b) => a + (b - m) ** 2, 0) / v.length) || 1; return v.map(x => (x - m) / sd) }
const zp = plus.map(z), zm = minus.map(z)
rader.forEach((r, i) => { r.index = (zp.length ? zp.reduce((s, a) => s + a[i], 0) / zp.length : 0) - (zm.length ? zm.reduce((s, a) => s + a[i], 0) / zm.length : 0) })

const perKonto = new Map()
for (const r of rader) { const l = perKonto.get(r.konto) ?? []; l.push(r); perKonto.set(r.konto, l) }
const konton = [...perKonto.entries()].filter(([, l]) => l.length >= 8)

let fro = 7
const slump = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const blanda = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(slump() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }
const medel = a => a.reduce((s, v) => s + v, 0) / a.length

function test(egenskap, utfall, { perm = 2000 } = {}) {
  const per = konton.map(([k, l]) => { const x = l.map(r => tal(r[egenskap])), y = l.map(r => r[utfall]); return { k, x, y, rho: spearman(x, y) } }).filter(p => Number.isFinite(p.rho))
  if (per.length < 10) return null
  const eff = medel(per.map(p => p.rho)), pos = per.filter(p => p.rho > 0).length / per.length
  let ext = 0
  for (let t = 0; t < perm; t++) { const e = medel(per.map(p => { const r = spearman(blanda(p.x), p.y); return Number.isFinite(r) ? r : 0 })); if (Math.abs(e) >= Math.abs(eff)) ext++ }
  // Tidshalvor: inom varje konto, äldre och nyare hälft.
  const halva = h => medel(konton.map(([, l]) => { const s = [...l].sort((a, b) => (a.datum ?? '').localeCompare(b.datum ?? '')); const d = h ? s.slice(s.length >> 1) : s.slice(0, s.length >> 1); const r = spearman(d.map(r => tal(r[egenskap])), d.map(r => r[utfall])); return r }).filter(Number.isFinite))
  const loo = per.filter(p => Math.sign(medel(per.filter(q => q !== p).map(q => q.rho))) === Math.sign(eff)).length / per.length
  return { konton: per.length, effekt: eff, andelPositiv: pos, p: (ext + 1) / (perm + 1), tidig: halva(false), sen: halva(true), loo }
}

// Tillägget: det avslöjade indexet (det ägaren faktiskt väljer), låst innan analysen.
const av = reg.tillagg_avslojat
if (av) {
  const ap = av.plus.map(z), am = av.minus.map(z)
  rader.forEach((r, i) => { r.avslojat = ap.reduce((s, a) => s + a[i], 0) / ap.length - am.reduce((s, a) => s + a[i], 0) / am.length })
}

const ut = { modell: MODELL, klipp: rader.length, konton: konton.length, index: { plus, minus }, avslojat: av ? { plus: av.plus, minus: av.minus } : null, resultat: {} }
for (const u of UTFALL) ut.resultat[`index→${u}`] = test('index', u)
if (av) for (const u of UTFALL) ut.resultat[`avslöjat→${u}`] = test('avslojat', u)

// Profilnivå (utforskande): kontots medel per lager, ägarens grupper mot den gamla banken.
const godk = new Set(fs.readFileSync(path.join(DATA, 'profil', 'godkanda.txt'), 'utf8').split(/\r?\n/).filter(Boolean))
const fore = new Set((fs.readFileSync(path.join(DATA, 'profil', 'forebilder.txt'), 'utf8').match(/@[a-z0-9._]+/g) ?? []).map(h => h.slice(1)))
const grupp = k => godk.has(k) ? 'ja' : fore.has(k) ? 'forebild' : 'bank'
const kontoMedel = [...perKonto.entries()].filter(([, l]) => l.length >= 6).map(([k, l]) => ({ k, g: grupp(k), n: l.length, ...Object.fromEntries([...Object.entries(LAGER).filter(([, [t]]) => t !== 'kat').map(([n]) => [n, medel(l.map(r => tal(r[n])))]), ['index', medel(l.map(r => r.index))], ['avslojat', medel(l.map(r => r.avslojat ?? 0))], ['rv_sd', Math.sqrt(medel(l.map(r => r.rv ** 2)))]]) }))
const profil = []
for (const n of [...Object.keys(LAGER).filter(n => LAGER[n][0] !== 'kat'), 'index', 'avslojat']) {
  const a = kontoMedel.filter(x => x.g !== 'bank').map(x => x[n]), b = kontoMedel.filter(x => x.g === 'bank').map(x => x[n])
  const d = medel(a) - medel(b), alla = [...a, ...b]
  let ext = 0
  for (let t = 0; t < 2000; t++) { const p = blanda(alla); if (Math.abs(medel(p.slice(0, a.length)) - medel(p.slice(a.length))) >= Math.abs(d)) ext++ }
  const sd = Math.sqrt(medel(alla.map(v => (v - medel(alla)) ** 2))) || 1
  profil.push({ lager: n, valda: medel(a), bank: medel(b), skillnad_sd: d / sd, p: (ext + 1) / 2001 })
}
profil.sort((x, y) => x.p - y.p).forEach((t, i, a) => { t.q = Math.min(1, t.p * a.length / (i + 1)) })
ut.profil = { konton: { valda: kontoMedel.filter(x => x.g !== 'bank').length, bank: kontoMedel.filter(x => x.g === 'bank').length }, lager: profil }
const lagerTester = []
for (const n of STABILA) for (const u of UTFALL) { const r = test(n, u, { perm: 1000 }); if (r) lagerTester.push({ lager: n, utfall: u, ...r }) }
// Benjamini–Hochberg
lagerTester.sort((a, b) => a.p - b.p).forEach((t, i, a) => { t.q = Math.min(1, t.p * a.length / (i + 1)) })
for (let i = lagerTester.length - 2; i >= 0; i--) lagerTester[i].q = Math.min(lagerTester[i].q, lagerTester[i + 1].q)
ut.lager = lagerTester
fs.writeFileSync(path.join(E4, `analys-${MODELL}.json`), JSON.stringify(ut, null, 1))

const f = x => Number.isFinite(x) ? x.toFixed(3) : '-'
console.log(`${rader.length} klipp, ${konton.length} konton med minst 8 klipp. Index plus: ${plus.join(', ')}; minus: ${minus.join(', ')}`)
for (const [k, r] of Object.entries(ut.resultat)) console.log(`${k.padEnd(10)} rho ${f(r.effekt)}  pos ${f(r.andelPositiv)}  p ${f(r.p)}  tidig ${f(r.tidig)} sen ${f(r.sen)}  loo ${f(r.loo)}`)
console.log(`\nprofilnivå: ägarens valda konton (ja + förebilder, ${ut.profil.konton.valda}) mot gamla banken (${ut.profil.konton.bank}), skillnad i sd, permutation:`)
for (const t of profil.slice(0, 16)) console.log(`${t.lager.padEnd(16)} valda ${f(t.valda)}  bank ${f(t.bank)}  skillnad ${f(t.skillnad_sd)} sd  p ${f(t.p)}  q ${f(t.q)}`)
console.log('\nlager med q < 0,10:')
for (const t of lagerTester.filter(t => t.q < 0.1)) console.log(`${t.lager.padEnd(16)} → ${t.utfall}  rho ${f(t.effekt)}  pos ${f(t.andelPositiv)}  p ${f(t.p)}  q ${f(t.q)}  halvor ${f(t.tidig)}/${f(t.sen)}`)
