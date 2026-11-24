// E10: grundvärdet ur billiga Lite-lager (förregistrerat i data/format/e10/forregistrering.json). Inga anrop.
//   node format/e10.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const F = path.join(DATA, 'format'), LD = path.join(F, 'e4', 'lager-gemini-3.1-flash-lite'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const lite = id => { const f = path.join(LD, `${id}.json`); return fs.existsSync(f) ? las(f) : null }
const NAMN = ['personer', 'andel_person', 'personal', 'gast', 'tilltal', 'dialog', 'roll', 'narbild_ansikte', 'trendljud', 'mimar', 'musik', 'skarmtext', 'text_poang', 'klipp', 'montage', 'effekter', 'redigeringsskamt', 'slowmotion', 'bildkvalitet', 'proffsljus', 'mat_andel', 'tillagning', 'lokal', 'utomhus', 'erbjudande', 'uppmaning', 'tavling', 'handelse', 'hogtid', 'krok', 'vandning', 'eskalering', 'humor', 'absurd', 'vardag', 'sjalvironi', 'fristaende_ide', 'feltolerans', 'poleringsgap', 'relation']
const TAL = { repliker: 'tal_repliker', voiceover: 'tal_voiceover', inget: 'tal_inget' }
const vek = L => [...NAMN.map(n => typeof L[n] === 'boolean' ? +L[n] : Number(L[n]) || 0), ...Object.keys(TAL).map(t => +(L.tal === t))]
// Träning: E6 + E6-R.
const tr = ['e6', 'e6r'].flatMap(d => las(path.join(F, d, 'urval.json')).filter(k => fs.existsSync(path.join(F, d, 'kort', `${k.id}.json`)) && lite(k.id)).map(k => ({ id: k.id, konto: k.konto, x: vek(lite(k.id)), y: grund(las(path.join(F, d, 'kort', `${k.id}.json`))).p })))
const p = tr[0].x.length
const mu = Array.from({ length: p }, (_, j) => tr.reduce((s, r) => s + r.x[j], 0) / tr.length), sd = Array.from({ length: p }, (_, j) => Math.sqrt(tr.reduce((s, r) => s + (r.x[j] - mu[j]) ** 2, 0) / tr.length) || 1)
const z = x => x.map((v, j) => (v - mu[j]) / sd[j])
function ridge(rows, lam) {
  const X = rows.map(r => [1, ...z(r.x)]), y = rows.map(r => r.y), q = p + 1
  const A = Array.from({ length: q }, (_, i) => Array.from({ length: q }, (_, j) => X.reduce((s, r) => s + r[i] * r[j], 0) + (i === j && i > 0 ? lam : 0)))
  const b = Array.from({ length: q }, (_, i) => X.reduce((s, r, k) => s + r[i] * y[k], 0))
  for (let i = 0; i < q; i++) { let m = i; for (let k = i + 1; k < q; k++) if (Math.abs(A[k][i]) > Math.abs(A[m][i])) m = k; [A[i], A[m]] = [A[m], A[i]]; [b[i], b[m]] = [b[m], b[i]]; for (let k = 0; k < q; k++) if (k !== i) { const f = A[k][i] / A[i][i]; for (let j = i; j < q; j++) A[k][j] -= f * A[i][j]; b[k] -= f * b[i] } }
  return b.map((v, i) => v / A[i][i])
}
const pred = (beta, x) => beta[0] + z(x).reduce((s, v, j) => s + v * beta[j + 1], 0)
const konton = [...new Set(tr.map(r => r.konto))].sort(), grupp = k => konton.indexOf(k) % 10
for (const lam of [1, 10, 50, 200]) { const cv = tr.map(r => ({ ...r, p: pred(ridge(tr.filter(x => grupp(x.konto) !== grupp(r.konto)), lam), r.x) })); console.log(`lambda ${lam}: korsvaliderad rho proxy–grund ${spearman(cv.map(r => r.p), cv.map(r => r.y)).toFixed(2)} (n ${tr.length})`) }
const LAM = 50, beta = ridge(tr, LAM)
const nam = [...NAMN, ...Object.values(TAL)]
console.log('störst vikt:', nam.map((n, j) => [n, beta[j + 1]]).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 10).map(([n, v]) => `${n} ${v >= 0 ? '+' : ''}${v.toFixed(2)}`).join(', '))
// Test: E4-klipp utanför E6/E6-R och biblioteket.
const anv = new Set([...tr.map(r => r.id), ...las(path.join(F, 'harness', 'urval.json')).bibliotek.map(k => k.id)])
const e4 = las(path.join(F, 'e4', 'urval.json')).filter(k => !anv.has(k.id) && lite(k.id)).map(k => ({ ...k, p: pred(beta, vek(lite(k.id))) }))
const per = {}; for (const k of e4) (per[k.konto] ??= []).push(k)
const grupper = Object.values(per).filter(l => l.length >= 4)
const stat = ys => { const rs = grupper.map(l => spearman(l.map(r => r.p), l.map(r => ys.get(r.id)))).filter(Number.isFinite); return rs.reduce((s, v) => s + v, 0) / rs.length }
const ys = new Map(e4.map(r => [r.id, r.rv])), obs = stat(ys)
let fro = 10, e = 0; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
for (let t = 0; t < 3000; t++) { const pm = new Map(); for (const l of grupper) { const v = l.map(r => r.rv); for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } l.forEach((r, i) => pm.set(r.id, v[i])) } if (stat(pm) >= obs) e++ }
console.log(`HE10b proxyn → visningar inom konto, osedda E4-klipp: ${obs.toFixed(3)} (${grupper.length} konton, ${grupper.reduce((s, l) => s + l.length, 0)} klipp), p ${((e + 1) / 3001).toFixed(4)}`)
fs.writeFileSync(path.join(F, 'e10', 'modell.json'), JSON.stringify({ lambda: LAM, namn: nam, mu, sd, beta }, null, 1))
// HE10c: E4:s uttalade LeTrend-index på samma osedda klipp (samma beräkning som e4-analys.mjs: stabila lager, z över klippen).
const reg = las(path.join(F, 'e4', 'forregistrering.json')), e1 = las(path.join(F, 'e1', 'analys.json')).lager
const STAB = Object.entries(e1).filter(([, r]) => r.stabil && r.typ !== 'kat').map(([n]) => n)
const plus = reg.letrend_index.plus.filter(n => STAB.includes(n)), minus = reg.letrend_index.minus.filter(n => STAB.includes(n))
const talv = v => typeof v === 'boolean' ? +v : Number(v) || 0
const zz = n => { const v = e4.map(r => talv(lite(r.id)[n])); const m = v.reduce((a, b) => a + b, 0) / v.length, s = Math.sqrt(v.reduce((a, b) => a + (b - m) ** 2, 0) / v.length) || 1; return v.map(x => (x - m) / s) }
const zp = plus.map(zz), zm = minus.map(zz)
e4.forEach((r, i) => { r.idx = (zp.length ? zp.reduce((s, a) => s + a[i], 0) / zp.length : 0) - (zm.length ? zm.reduce((s, a) => s + a[i], 0) / zm.length : 0) })
const rsI = grupper.map(l => spearman(l.map(r => r.idx), l.map(r => r.rv))).filter(Number.isFinite)
console.log(`HE10c E4-indexet på samma klipp: ${(rsI.reduce((s, v) => s + v, 0) / rsI.length).toFixed(3)} (proxyn ${obs.toFixed(3)})`)
