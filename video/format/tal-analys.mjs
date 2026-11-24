// Tal ur lokala transkript mot räckvidd och mot ägarens val i pass 7 (6 nov 2026, inga anrop).
// Förregistrering: data/format/tal/forregistrering.json. Transkript: format/transkript.mjs.
//   node format/tal-analys.mjs
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { historik } from './serieprofil.mjs'
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const TAL = path.join(DATA, 'format', 'tal')
const FAM = Object.fromEntries(Object.entries(las(path.join(DATA, 'format', 'familjer', 'familjer-lokal.json'))).map(([k, v]) => [k, v.familj]))
const DL = path.join(os.homedir(), 'Downloads', 'letrend-bank')
const median = a => { const b = a.filter(Number.isFinite).sort((x, y) => x - y); return b.length ? (b.length % 2 ? b[(b.length - 1) / 2] : (b[b.length / 2 - 1] + b[b.length / 2]) / 2) : NaN }
const binom = (k, n) => { let s = 0; for (let i = k; i <= n; i++) { let c = 1; for (let j = 0; j < i; j++) c = c * (n - j) / (j + 1); s += c / 2 ** n } return s }
const ljud = j => { const t = (j.track || '').toLowerCase(), a = (j.artist || (j.artists || [])[0] || '').toLowerCase(), u = (j.uploader || '').toLowerCase(), ch = (j.channel || '').toLowerCase(); if (!t) return null; if (/original|orijinal|originalljud|originalton|suono|son original|sonido/.test(t)) return !a || a === u || a === ch || u.includes(a) || a.includes(u) ? 'eget' : 'lanat'; return 'lat' }

// mått per klipp
const M = new Map()
for (const f of fs.readdirSync(TAL).filter(f => f.endsWith('.json') && f !== 'forregistrering.json')) {
  const j = las(path.join(TAL, f)), s = j.segment.filter(x => Number.isFinite(x.fran) && x.till > x.fran)
  const talsek = s.reduce((a, x) => a + (x.till - x.fran), 0), ord = s.reduce((a, x) => a + x.text.split(/\s+/).filter(Boolean).length, 0)
  let dod = 0; for (let i = 1; i < s.length; i++) { const p = s[i].fran - s[i - 1].till; if (p > 0.7) dod += p }
  M.set(j.id, { id: j.id, langd: j.langd, talandel: j.langd ? Math.min(1, talsek / j.langd) : NaN, ordps: talsek > 2 ? ord / talsek : NaN, dodtid: s.length > 1 && j.langd ? dod / j.langd : NaN, repliker: s.length, sprak: j.sprak })
}
// relativ räckvidd
const rader = []
for (const k of new Set([...M.keys()].map(id => id.replace(/-\d+$/, '')))) {
  if (!fs.existsSync(path.join(DATA, 'bank', k, 'lista.json'))) continue
  const L = historik(k).filter(x => x.visningar > 0 && x.datum); if (L.length < 20) continue
  const t = L.map(x => Date.parse(x.datum))
  L.forEach((x, i) => { const m = M.get(x.s.id); if (!m) return
    const gr = L.map((y, q) => ({ q, d: Math.abs(t[q] - t[i]) })).filter(g => g.q !== i).sort((a, b) => a.d - b.d).slice(0, 15)
    const ip = path.join(DL, k, `${x.id}.info.json`)
    rader.push({ ...m, k, f: FAM[x.s.id], rv: Math.log(x.visningar) - Math.log(median(gr.map(g => L[g.q].visningar))), lj: fs.existsSync(ip) ? ljud(las(ip)) : null }) })
}
console.log(`${M.size} transkript, ${rader.length} med relativ räckvidd i ${new Set(rader.map(r => r.k)).size} konton`)
console.log('Median per familj: talandel, ord/s, dötid')
for (const f of [...new Set(rader.map(r => r.f))]) { const v = rader.filter(r => r.f === f); if (v.length >= 10) console.log(`  ${String(f).padEnd(20)} n ${String(v.length).padStart(4)}  tal ${median(v.map(r => r.talandel)).toFixed(2)}  ord/s ${median(v.map(r => r.ordps)).toFixed(2)}  dötid ${median(v.map(r => r.dodtid)).toFixed(2)}`) }

let fro = 9; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
function inomGrupp(rr, grupp, x, y, n = 3000) {
  rr = rr.filter(r => Number.isFinite(x(r)) && Number.isFinite(y(r)))
  const g = {}; rr.forEach((r, i) => (g[grupp(r)] ??= []).push(i)); for (const k in g) if (g[k].length < 4) delete g[k]
  const idxAlla = Object.values(g).flat(); rr = idxAlla.map(i => rr[i]); const g2 = {}; rr.forEach((r, i) => (g2[grupp(r)] ??= []).push(i))
  const cx = rr.map(x), cy = rr.map(y)
  for (const idx of Object.values(g2)) { const mx = idx.reduce((s, i) => s + cx[i], 0) / idx.length, my = idx.reduce((s, i) => s + cy[i], 0) / idx.length; idx.forEach(i => { cx[i] -= mx; cy[i] -= my }) }
  const obs = spearman(cx, cy); let hi = 0, lo = 0
  for (let t = 0; t < n; t++) { const z = [...cy]; for (const idx of Object.values(g2)) { const v = idx.map(i => cy[i]); for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } idx.forEach((i, m) => { z[i] = v[m] }) } const r = spearman(cx, z); if (r >= obs) hi++; if (r <= obs) lo++ }
  return { rho: obs, pHog: (hi + 1) / (n + 1), pLag: (lo + 1) / (n + 1), n: rr.length }
}
function mw(a, b) { const all = [...a.map(v => [v, 0]), ...b.map(v => [v, 1])].sort((x, y) => x[0] - y[0]); let r = 0; all.forEach((x, i) => { if (x[1] === 0) r += i + 1 }); const n1 = a.length, n2 = b.length, U = r - n1 * (n1 + 1) / 2, sd = Math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12), z = (U - n1 * n2 / 2) / sd; const t = 1 / (1 + 0.3275911 * Math.abs(z / Math.SQRT2)), e = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-(z * z) / 2); return { auc: U / (n1 * n2), p: 0.5 * (1 - (z >= 0 ? e : -e)) } }
const res = {}
const eg = rader.filter(r => r.lj === 'eget').map(r => r.talandel).filter(Number.isFinite), lat = rader.filter(r => r.lj === 'lat').map(r => r.talandel).filter(Number.isFinite)
res.TA1 = mw(eg, lat); console.log(`\nTA1 talandel, eget ljud (n ${eg.length}) mot låt (n ${lat.length}): AUC ${res.TA1.auc.toFixed(2)}, p ${res.TA1.p.toExponential(1)}`)
const grp = r => r.k + '|' + r.f, fam = ['dialogsketch', 'tilltal_med_mat']
for (const [namn, f] of [['båda', fam], ['dialogsketch', ['dialogsketch']], ['tilltal_med_mat', ['tilltal_med_mat']]]) {
  const v = rader.filter(r => f.includes(r.f))
  const a = inomGrupp(v, grp, r => r.dodtid, r => r.rv), b = inomGrupp(v, grp, r => r.ordps, r => r.rv)
  res[namn] = { TA2: a, TA3: b }
  console.log(`${namn.padEnd(16)} TA2 dötid→rv rho ${a.rho.toFixed(3)} p(låg) ${a.pLag.toFixed(3)} n ${a.n}   TA3 ord/s→rv rho ${b.rho.toFixed(3)} p(hög) ${b.pHog.toFixed(3)} n ${b.n}`)
}
{ const g = {}; rader.filter(r => r.f === 'dialogsketch').forEach(r => (g[r.k] ??= []).push(r)); const d = []
  for (const v of Object.values(g)) { const a = v.filter(r => r.talandel >= 0.3).map(r => r.rv), b = v.filter(r => r.talandel < 0.3).map(r => r.rv); if (a.length >= 3 && b.length >= 3) d.push(median(a) - median(b)) }
  const upp = d.filter(x => x > 0).length; res.TA4 = { x: Math.exp(median(d)), upp, n: d.length, p: binom(upp, d.length) }
  console.log(`TA4 dialogsketch med eget tal (talandel ≥ 0,3) mot utan: ×${res.TA4.x.toFixed(2)} (${upp} av ${d.length} konton, p ${res.TA4.p.toFixed(3)})`) }
const P7 = las(path.join(DATA, 'format', 'harness', 'pass7', 'forregistrering.json')), A7 = las(path.join(DATA, 'format', 'harness', 'pass7', 'agare.json'))
let hog = 0, n5 = 0; const par = []
for (const p of P7.par) { const v = A7.val[p.nr]; if (!v) continue; const a = M.get(v === 'v' ? p.vanster.id : p.hoger.id), b = M.get(v === 'v' ? p.hoger.id : p.vanster.id); if (!a || !b) continue; n5++; if (a.talandel > b.talandel) hog++; par.push(`${p.nr}${p.typ === 'isar' ? '*' : ''}: ${a.talandel.toFixed(2)}/${b.talandel.toFixed(2)}`) }
res.TA5 = { hog, n: n5, p: binom(hog, n5) }
console.log(`TA5 pass 7: valt klipp har högre talandel i ${hog} av ${n5} par (p ${res.TA5.p.toFixed(3)})\n  ${par.join('  ')}`)
fs.writeFileSync(path.join(TAL, '..', 'tal-resultat.json'), JSON.stringify({ transkript: M.size, rader: rader.length, ...res }, null, 1))
