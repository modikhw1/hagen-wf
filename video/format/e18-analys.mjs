// E18: HE18a (pass 7, undanhållet), HE18b (utfall inom konto), HE18c (var självet och hyllan går isär).
//   node format/e18-analys.mjs [--dump]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'

const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const E = path.join(DATA, 'format', 'e18'), H = path.join(DATA, 'format', 'harness')
// node format/e18-analys.mjs [--modell 3.1-pro]
const SUFF = process.argv.includes('--modell') ? '-' + process.argv[process.argv.indexOf('--modell') + 1] : ''
const mote = id => { const f = path.join(E, 'mote' + SUFF, `${id}.json`); return fs.existsSync(f) ? las(f) : null }
const medel = x => x.reduce((s, v) => s + v, 0) / x.length

// HE18a
const P = las(path.join(H, 'pass7', 'forregistrering.json')).par, A = las(path.join(H, 'pass7', 'agare.json'))
let ratt = 0, fel = 0, lika = 0, sakn = 0, nyt = 0, gru = 0, n = 0; const rader = []
for (const p of P) {
  const val = A.val[p.nr]; if (!val) continue
  const v = mote(p.vanster.id), h = mote(p.hoger.id); if (!v || !h) { sakn++; continue }
  const d = v.mote.hemma - h.mote.hemma, r = d === 0 ? 'lika' : (d > 0) === (val === 'v') ? 'rätt' : 'fel'
  if (r === 'rätt') ratt++; else if (r === 'fel') fel++; else lika++
  n++; if ((p.vanster.nytta6 - p.hoger.nytta6 > 0) === (val === 'v') && p.vanster.nytta6 !== p.hoger.nytta6) nyt++; if ((p.vanster.grund - p.hoger.grund > 0) === (val === 'v') && p.vanster.grund !== p.hoger.grund) gru++
  rader.push({ nr: p.nr, typ: p.typ, val, v: v.mote.hemma, h: h.mote.hemma, r, vk: p.vanster.karna, hk: p.hoger.karna, vm: v.mote, hm: h.mote })
}
console.log(`HE18a: pass 7, ${n} par med möte (${sakn} saknar): ${ratt} rätt, ${fel} fel, ${lika} lika  →  ${(ratt + lika / 2).toFixed(1)} av ${n}   (tröskel 13 av 19; på samma par: nytta6 ${nyt}, grundvärdet ${gru})`)
if (process.argv.includes('--dump')) for (const r of rader) console.log(`  par ${r.nr} (${r.typ}) ägaren ${r.val}  hemma v ${r.v} / h ${r.h}  ${r.r}\n     v: ${r.vk}\n     h: ${r.hk}${r.r === 'fel' ? `\n     möte v: ${r.vm.vad_hander}\n     möte h: ${r.hm.vad_hander}` : ''}`)

// HE18b och HE18c: biblioteket
const BIB = Object.values(las(path.join(H, 'bibliotek-v6.json')).hyllor).flat(), utf = {}
function utfall(k) { if (k in utf) return; utf[k] = {}; const lf = path.join(DATA, 'bank', k, 'lista.json'); if (!fs.existsSync(lf)) return; const T = las(lf).klipp.filter(x => x.visningar > 0).sort((a, b) => (a.datum || '').localeCompare(b.datum || '')); T.forEach((x, i) => { const g = T.slice(Math.max(0, i - 10), i + 11).filter(y => y !== x).map(y => Math.log(y.visningar)).sort((a, b) => a - b); if (g.length >= 6) utf[k][`${k}-${x.id}`] = Math.log(x.visningar) - g[Math.floor(g.length / 2)] }) }
const B = []
for (const c of BIB) { const m = mote(c.id); if (!m) continue; utfall(c.konto); B.push({ ...c, hemma: m.mote.hemma, u: utf[c.konto][c.id], m: m.mote, fran: m.motor_fran }) }
if (B.length >= 30) {
  const ok = B.filter(r => Number.isFinite(r.u)), cen = (R, f) => { const mm = {}; for (const k of new Set(R.map(r => r.konto))) mm[k] = medel(R.filter(r => r.konto === k).map(f)); return R.map(r => f(r) - mm[r.konto]) }
  const flera = ok.filter(r => ok.filter(x => x.konto === r.konto).length >= 3)
  console.log(`\nHE18b: ${B.length} biblioteksklipp med möte, ${ok.length} med utfall`)
  console.log(`  hemma mot utfall: rho ${spearman(ok.map(r => r.hemma), ok.map(r => r.u)).toFixed(3)}; inom konto (konton med minst 3 klipp, n ${flera.length}): ${spearman(cen(flera, r => r.hemma), cen(flera, r => r.u)).toFixed(3)}  (tröskel 0,10)`)
  console.log(`  v5 letrend_varde på samma klipp, inom konto: ${spearman(cen(flera, r => r.letrend_varde), cen(flera, r => r.u)).toFixed(3)};  nytta_v62: ${spearman(cen(flera, r => r.nytta_v62), cen(flera, r => r.u)).toFixed(3)}`)
  console.log(`\nHE18c: hemma per hylla`)
  for (const h of ['karna', 'mitten', 'situation', 'capcut_referens', 'ute']) { const x = B.filter(r => r.hylla === h); if (x.length) console.log(`  ${h.padEnd(16)} n ${String(x.length).padStart(4)}  hemma ${medel(x.map(r => r.hemma)).toFixed(2)}  andel ≥4: ${(x.filter(r => r.hemma >= 4).length / x.length).toFixed(2)}  andel ≤2: ${(x.filter(r => r.hemma <= 2).length / x.length).toFixed(2)}`) }
  if (process.argv.includes('--dump')) {
    console.log('\nUte på hyllan men hemma hos LeTrend-självet:'); for (const r of B.filter(r => r.hylla === 'ute' && r.hemma >= 4.5).slice(0, 10)) console.log(`  ${r.id}: ${r.karna}\n     ${r.m.vad_hander}`)
    console.log('\nKärna på hyllan men främmande för LeTrend-självet:'); for (const r of B.filter(r => r.hylla === 'karna' && r.hemma <= 2.5).slice(0, 10)) console.log(`  ${r.id}: ${r.karna}\n     bryter: ${r.m.bryter}`)
  }
}
