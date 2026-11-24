// Sanning, preferens och nytta per lager (4 nov 2026).
//   sanning   = exakt överensstämmelse Pro mot Pros omkörning (E5, 40 klipp)
//   preferens = rho mot ägarens passform (35 par) och biblioteksbeslut (25 klipp)  [h-lager5.mjs]
//   nytta     = medel av rho inom konto mot visningar och gillanden (E6, 299 klipp, 29 konton)
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const F = path.join(DATA, 'format'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const L5 = Object.fromEntries(las(path.join(F, 'harness', 'lager5.json')).rad.map(r => [r.k, r]))
const E5 = las(path.join(F, 'e5', 'analys.json')).lager, E6 = las(path.join(F, 'e6', 'analys-kort.json')).karta
const bas = k => k.split('=')[0]
const f = v => Number.isFinite(v) ? (v >= 0 ? '+' : '') + v.toFixed(2) : '  – '
const rader = Object.keys(E6).filter(k => L5[k]).map(k => {
  const pref = ((L5[k].p1 ?? 0) + (L5[k].p2 ?? 0)) / 2, nytta = ((E6[k].rv.r ?? 0) + (E6[k].rl.r ?? 0)) / 2, stab = E5[bas(k)]?.[0]
  const klass = Math.abs(pref) >= 0.3 && Math.abs(nytta) >= 0.08 ? (Math.sign(pref) === Math.sign(nytta) ? 'båda' : 'MOTSATT') : Math.abs(pref) >= 0.3 ? 'preferens' : Math.abs(nytta) >= 0.08 ? 'nytta' : '–'
  return { k, pref, nytta, stab, klass }
})
console.log('lager'.padEnd(40), 'stabilitet', 'preferens', '  nytta', ' klass')
for (const r of rader.sort((a, b) => Math.abs(b.pref) + 4 * Math.abs(b.nytta) - Math.abs(a.pref) - 4 * Math.abs(a.nytta))) console.log(r.k.padEnd(40), (Number.isFinite(r.stab) ? Math.round(100 * r.stab) + ' %' : '–').padStart(10), f(r.pref).padStart(9), f(r.nytta).padStart(7), ' ' + r.klass)
fs.writeFileSync(path.join(F, 'triad.json'), JSON.stringify(rader, null, 1))
