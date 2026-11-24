// Tempo och ljud mot räckvidd och mot ägarens val i pass 7 (6 nov 2026, inga anrop).
// Förregistrering: data/format/tempo/forregistrering.json. Mätningar: format/tempo-matt.mjs (matt.jsonl).
//   node format/tempo-analys.mjs
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { historik } from './serieprofil.mjs'
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const M = new Map(fs.readFileSync(path.join(DATA, 'format', 'tempo', 'matt.jsonl'), 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l)).map(r => [r.id, r]))
const FAM = Object.fromEntries(Object.entries(las(path.join(DATA, 'format', 'familjer', 'familjer-lokal.json'))).map(([k, v]) => [k, v.familj]))
const DL = path.join(os.homedir(), 'Downloads', 'letrend-bank')
const median = a => { const b = a.filter(Number.isFinite).sort((x, y) => x - y); return b.length ? (b.length % 2 ? b[(b.length - 1) / 2] : (b[b.length / 2 - 1] + b[b.length / 2]) / 2) : NaN }
const binom = (k, n) => { let s = 0; for (let i = k; i <= n; i++) { let c = 1; for (let j = 0; j < i; j++) c = c * (n - j) / (j + 1); s += c / 2 ** n } return s }
const ljud = j => { const t = (j.track || '').toLowerCase(), a = (j.artist || (j.artists || [])[0] || '').toLowerCase(), u = (j.uploader || '').toLowerCase(), ch = (j.channel || '').toLowerCase(); if (!t) return null; if (/original|orijinal|originalljud|originalton|suono|son original|sonido/.test(t)) return !a || a === u || a === ch || u.includes(a) || a.includes(u) ? 'eget' : 'lanat'; return 'lat' }

// relativ räckvidd för mätta klipp som finns i bankens listor
const konton = new Set([...M.keys()].map(id => id.replace(/-\d+$/, '')))
const rader = []
for (const k of konton) {
  if (!fs.existsSync(path.join(DATA, 'bank', k, 'lista.json'))) continue
  const L = historik(k).filter(x => x.visningar > 0 && x.datum); if (L.length < 20) continue
  const t = L.map(x => Date.parse(x.datum))
  L.forEach((x, i) => {
    const m = M.get(x.s.id); if (!m || !Number.isFinite(m.takt)) return
    const gr = L.map((y, q) => ({ q, d: Math.abs(t[q] - t[i]) })).filter(g => g.q !== i).sort((a, b) => a.d - b.d).slice(0, 15)
    const ip = path.join(DL, k, `${x.id}.info.json`)
    rader.push({ ...m, k, f: FAM[x.s.id], rv: Math.log(x.visningar) - Math.log(median(gr.map(g => L[g.q].visningar))), lj: fs.existsSync(ip) ? ljud(las(ip)) : null })
  })
}
console.log(`${M.size} mätta klipp, ${rader.length} med relativ räckvidd i ${new Set(rader.map(r => r.k)).size} konton`)

let fro = 3; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
function inomGrupp(rr, grupp, x, y, n = 3000) {
  const g = {}; rr.forEach((r, i) => (g[grupp(r)] ??= []).push(i))
  const cx = rr.map(x), cy = rr.map(y)
  for (const idx of Object.values(g)) { const mx = idx.reduce((s, i) => s + cx[i], 0) / idx.length, my = idx.reduce((s, i) => s + cy[i], 0) / idx.length; idx.forEach(i => { cx[i] -= mx; cy[i] -= my }) }
  const obs = spearman(cx, cy); let hi = 0, lo = 0
  for (let t = 0; t < n; t++) { const z = [...cy]; for (const idx of Object.values(g)) { const v = idx.map(i => cy[i]); for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } idx.forEach((i, m) => { z[i] = v[m] }) } const r = spearman(cx, z); if (r >= obs) hi++; if (r <= obs) lo++ }
  return { rho: obs, pHog: (hi + 1) / (n + 1), pLag: (lo + 1) / (n + 1), n: rr.length }
}
const grp = r => r.k + '|' + r.f
const ur = fam => { const v = rader.filter(r => fam.includes(r.f)); return v.filter(r => v.filter(z => grp(z) === grp(r)).length >= 4) }
const res = {}
console.log('\nKlipptakt (scenbyten per 10 s) och längd per familj, median:')
for (const f of [...new Set(rader.map(r => r.f))]) { const v = rader.filter(r => r.f === f); if (v.length >= 10) console.log(`  ${String(f).padEnd(20)} n ${String(v.length).padStart(4)}  takt ${median(v.map(r => r.takt)).toFixed(2)}  längd ${median(v.map(r => r.langd)).toFixed(0)} s  tystnad ${median(v.map(r => r.tyst)).toFixed(2)}`) }
for (const [namn, fam] of [['dialogsketch + tilltal', ['dialogsketch', 'tilltal_med_mat']], ['dialogsketch', ['dialogsketch']], ['tilltal_med_mat', ['tilltal_med_mat']], ['stamningsmontage', ['stamningsmontage']]]) {
  const v = ur(fam); if (v.length < 20) continue
  const t1 = inomGrupp(v, grp, r => r.takt, r => r.rv), t2 = inomGrupp(v, grp, r => r.langd, r => r.rv)
  res[namn] = { t1, t2 }
  console.log(`${namn.padEnd(24)} n ${v.length}  T1 takt→rv rho ${t1.rho.toFixed(3)} p(hög) ${t1.pHog.toFixed(3)}   T2 längd→rv rho ${t2.rho.toFixed(3)} p(låg) ${t2.pLag.toFixed(3)}`)
}
// T3: eget ljud mot låt, tystnad och LRA (Mann–Whitney med normalapproximation, ensidigt)
function mw(a, b) { const all = [...a.map(v => [v, 0]), ...b.map(v => [v, 1])].sort((x, y) => x[0] - y[0]); let r = 0; all.forEach((x, i) => { if (x[1] === 0) r += i + 1 }); const n1 = a.length, n2 = b.length, U = r - n1 * (n1 + 1) / 2, mu = n1 * n2 / 2, sd = Math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12), z = (U - mu) / sd; return { auc: U / (n1 * n2), z, p: 0.5 * (1 - erf(z / Math.SQRT2)) } }
function erf(x) { const t = 1 / (1 + 0.3275911 * Math.abs(x)), y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x); return x >= 0 ? y : -y }
const eg = rader.filter(r => r.lj === 'eget'), lat = rader.filter(r => r.lj === 'lat')
const t3a = mw(eg.map(r => r.tyst).filter(Number.isFinite), lat.map(r => r.tyst).filter(Number.isFinite)), t3b = mw(eg.map(r => r.lra).filter(Number.isFinite), lat.map(r => r.lra).filter(Number.isFinite))
res.T3 = { t3a, t3b }
console.log(`\nT3 eget ljud (n ${eg.length}) mot låt (n ${lat.length}): tystnad AUC ${t3a.auc.toFixed(2)} p ${t3a.p.toExponential(1)}; LRA AUC ${t3b.auc.toFixed(2)} p ${t3b.p.toExponential(1)}`)
// T4: pass 7
const P7 = las(path.join(DATA, 'format', 'harness', 'pass7', 'forregistrering.json')), A7 = las(path.join(DATA, 'format', 'harness', 'pass7', 'agare.json'))
let hog = 0, n4 = 0, kort = 0; const t4 = []
for (const p of P7.par) { const v = A7.val[p.nr]; if (!v) continue; const val = M.get(v === 'v' ? p.vanster.id : p.hoger.id), ann = M.get(v === 'v' ? p.hoger.id : p.vanster.id); if (!val || !ann || !Number.isFinite(val.takt) || !Number.isFinite(ann.takt)) continue; n4++; if (val.takt > ann.takt) hog++; if (val.langd < ann.langd) kort++; t4.push({ nr: p.nr, typ: p.typ, valt: +val.takt.toFixed(2), annat: +ann.takt.toFixed(2), langd: [Math.round(val.langd), Math.round(ann.langd)] }) }
res.T4 = { hog, kort, n: n4, par: t4 }
console.log(`T4 pass 7: valt klipp har högre klipptakt i ${hog} av ${n4} par (p ${binom(hog, n4).toFixed(3)}), kortare i ${kort} av ${n4}`)
console.log(t4.map(x => `${x.nr}${x.typ === 'isar' ? '*' : ''}: ${x.valt}/${x.annat}`).join('  '))
fs.writeFileSync(path.join(DATA, 'format', 'tempo', 'resultat.json'), JSON.stringify({ matta: M.size, rader: rader.length, ...res }, null, 1))
