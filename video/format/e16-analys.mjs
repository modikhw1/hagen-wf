// E16: HE16a (roller mot utfall inom konto), HE16b (omskrivet själv mot första självet i igenkänning), HE16c.
//   node format/e16-analys.mjs [--dump]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'

const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const E14 = path.join(DATA, 'format', 'e14'), E = path.join(DATA, 'format', 'e16'), FAM = las(path.join(DATA, 'format', 'familjer', 'familjer.json'))
const SUFF = process.argv.includes('--modell') ? '-' + process.argv[process.argv.indexOf('--modell') + 1] : ''
const medel = x => x.reduce((s, v) => s + v, 0) / x.length
const kunder = fs.existsSync(path.join(E, 'roller')) ? fs.readdirSync(path.join(E, 'roller')).map(f => f.replace('.json', '')) : []

// Utfall: log visningar minus medianen av de tio grannarna på var sida i tid (tar bort ålder och kontots nivå).
function utfall(konto) {
  const L = las(path.join(DATA, 'bank', konto, 'lista.json')).klipp.filter(k => k.visningar > 0).sort((a, b) => (a.datum || '').localeCompare(b.datum || ''))
  const ut = {}
  L.forEach((k, i) => { const g = L.slice(Math.max(0, i - 10), i + 11).filter(x => x !== k).map(x => Math.log(x.visningar)).sort((a, b) => a - b); if (g.length >= 6) ut[`${konto}-${k.id}`] = Math.log(k.visningar) - g[Math.floor(g.length / 2)] })
  return ut
}

const rader = []
for (const k of kunder) { const R = las(path.join(E, 'roller', `${k}.json`)), U = utfall(k); for (const c of R.klipp) { const id = R.ids[c.nr - 1]; if (id) rader.push({ konto: k, id, roll: c.roll, avsikt: c.avsikt, u: U[id], varfor: c.varfor }) } }
console.log(`${rader.length} klipp med roll hos ${kunder.length} kunder\n`)
for (const k of kunder) { const x = rader.filter(r => r.konto === k); console.log(`${k.padEnd(24)} ${['barande', 'stod', 'ihopkastat', 'avstickare'].map(r => `${r} ${x.filter(c => c.roll === r).length}`).join('  ')}`) }
const ok = rader.filter(r => Number.isFinite(r.u))
const grupp = r => medel(ok.filter(c => c.roll === r).map(c => c.u))
console.log(`\nHE16a: utfall (log visningar mot grannarna i tid), ${ok.length} klipp`)
for (const r of ['barande', 'stod', 'ihopkastat', 'avstickare']) { const n = ok.filter(c => c.roll === r).length; if (n) console.log(`  ${r.padEnd(11)} n ${String(n).padStart(3)}  medel ${grupp(r).toFixed(2)}  (×${Math.exp(grupp(r)).toFixed(2)})`) }
const B = ok.filter(c => c.roll === 'barande'), I = ok.filter(c => c.roll === 'ihopkastat')
if (B.length >= 5 && I.length >= 5) {
  const d0 = grupp('barande') - grupp('ihopkastat'); let fler = 0; const N = 5000, T = ok.filter(c => c.roll === 'barande' || c.roll === 'ihopkastat')
  for (let n = 0; n < N; n++) { // blanda rollerna inom konto
    let sb = 0, nb = 0, si = 0, ni = 0
    for (const k of kunder) { const x = T.filter(c => c.konto === k), roller = x.map(c => c.roll); for (let j = roller.length - 1; j > 0; j--) { const q = Math.floor(Math.random() * (j + 1));[roller[j], roller[q]] = [roller[q], roller[j]] } x.forEach((c, j) => { if (roller[j] === 'barande') { sb += c.u; nb++ } else { si += c.u; ni++ } }) }
    if (sb / nb - si / ni >= d0) fler++
  }
  console.log(`  bärande − ihopkastat = ${d0.toFixed(2)} (×${Math.exp(d0).toFixed(2)}), p ${((fler + 1) / (N + 1)).toFixed(3)}  →  ${d0 > 0 && (fler + 1) / (N + 1) < 0.05 ? 'håller' : 'förkastas'}`)
}
const cen = (R, f) => { const m = {}; for (const k of kunder) { const x = R.filter(r => r.konto === k); if (x.length) m[k] = medel(x.map(f)) } return R.map(r => f(r) - m[r.konto]) }
if (ok.length > 10) console.log(`  avsikt 1–5 mot utfall inom konto: rho ${spearman(cen(ok, r => r.avsikt), cen(ok, r => r.u)).toFixed(2)}`)

// HE16b: igenkänning med första självet (E14 mote) och det omskrivna (mote2)
const auc = (e, a) => { if (!e.length || !a.length) return NaN; let s = 0; for (const x of e) for (const y of a) s += x > y ? 1 : x === y ? 0.5 : 0; return s / (e.length * a.length) }
const agare = id => id.slice(0, id.lastIndexOf('-'))
const undan = kunder.flatMap(k => las(path.join(E14, 'sjalv', `${k}.json`)).undan)
console.log('\nHE16b: igenkänning av undanhållna klipp, första självet mot det omskrivna')
const A1 = [], A2 = [], F1 = [], F2 = []
for (const k of kunder) {
  const las2 = (d, bas) => undan.map(id => { const f = path.join(bas, d, `${k}__${id}.json`); return fs.existsSync(f) ? { id, egen: agare(id) === k, v: las(f).mote.egen } : null }).filter(Boolean)
  const m1 = las2('mote' + SUFF, E14), m2 = las2('mote2' + SUFF, E), gem = new Set(m2.map(r => r.id)), x1 = m1.filter(r => gem.has(r.id)), g1 = new Set(x1.map(r => r.id)), x2 = m2.filter(r => g1.has(r.id))
  if (x2.length < 8) continue
  const a = R => auc(R.filter(r => r.egen).map(r => r.v), R.filter(r => !r.egen).map(r => r.v))
  const fam = new Set(x2.filter(r => r.egen).map(r => FAM[r.id]).filter(Boolean)), f = R => auc(R.filter(r => r.egen && FAM[r.id]).map(r => r.v), R.filter(r => !r.egen && fam.has(FAM[r.id])).map(r => r.v))
  A1.push(a(x1)); A2.push(a(x2)); if (Number.isFinite(f(x1))) { F1.push(f(x1)); F2.push(f(x2)) }
  console.log(`  ${k.padEnd(24)} n ${x2.length}  AUC ${a(x1).toFixed(2)} → ${a(x2).toFixed(2)}   samma familj ${Number.isFinite(f(x1)) ? f(x1).toFixed(2) + ' → ' + f(x2).toFixed(2) : '–'}`)
}
if (A1.length) console.log(`  medel ${medel(A1).toFixed(2)} → ${medel(A2).toFixed(2)} (${A1.length} kunder);  samma familj ${F1.length ? medel(F1).toFixed(2) + ' → ' + medel(F2).toFixed(2) + ` (${F1.length} kunder)` : '–'}`)
if (process.argv.includes('--dump')) for (const r of rader.filter(c => c.roll === 'ihopkastat' || c.roll === 'avstickare')) console.log(`  ${r.konto} ${r.roll} avsikt ${r.avsikt} utfall ${Number.isFinite(r.u) ? r.u.toFixed(2) : '–'}: ${r.varfor}`)
