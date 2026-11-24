// Eget ljud mot lånat ljud och låt (TikToks metadata, inga anrop), inom konto och familj. Utforskande, 6 nov 2026.
// Relativ räckvidd = log(visningar) mot medianen av de 15 närmaste klippen i tid (som serie 2).
//   node format/ljud-rv.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { historik } from './serieprofil.mjs'
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const FAM = Object.fromEntries(Object.entries(las(path.join(DATA, 'format', 'familjer', 'familjer-lokal.json'))).map(([k, v]) => [k, v.familj]))
const BANKDL = path.join(process.env.USERPROFILE, 'Downloads', 'letrend-bank')
const ljud = j => { const t = (j.track || '').toLowerCase(), a = (j.artist || (j.artists || [])[0] || '').toLowerCase(), u = (j.uploader || '').toLowerCase(), ch = (j.channel || '').toLowerCase(); if (!t) return null; if (/original|orijinal|originalljud|originalton|suono|son original|sonido/.test(t)) return !a || a === u || a === ch || u.includes(a) || a.includes(u) ? 'eget' : 'lanat'; return 'lat' }
const median = a => { const b = a.filter(Number.isFinite).sort((x, y) => x - y); return b.length ? (b.length % 2 ? b[(b.length - 1) / 2] : (b[b.length / 2 - 1] + b[b.length / 2]) / 2) : NaN }
const rader = []
for (const k of fs.readdirSync(path.join(DATA, 'bank')).filter(k => fs.existsSync(path.join(DATA, 'bank', k, 'lista.json')))) {
  const L = historik(k).filter(x => x.visningar > 0 && x.datum); if (L.length < 30) continue
  const t = L.map(x => Date.parse(x.datum))
  L.forEach((x, i) => {
    const p = path.join(BANKDL, k, `${x.id}.info.json`); if (!fs.existsSync(p)) return
    const l = ljud(las(p)); if (!l) return
    const gr = L.map((y, j) => ({ j, d: Math.abs(t[j] - t[i]) })).filter(g => g.j !== i).sort((a, b) => a.d - b.d).slice(0, 15)
    rader.push({ k, f: FAM[x.s.id], l, rel: Math.log(x.visningar) - Math.log(median(gr.map(g => L[g.j].visningar))) })
  })
}
console.log(`${rader.length} klipp, ${new Set(rader.map(r => r.k)).size} konton. Andel: ${['eget', 'lanat', 'lat'].map(l => `${l} ${Math.round(100 * rader.filter(r => r.l === l).length / rader.length)}%`).join(', ')}`)
// skillnad i median rel inom konto × familj, eget mot övrigt, sammanvägt som median över grupper
for (const [namn, a, b] of [['eget mot lånat', 'eget', 'lanat'], ['eget mot låt', 'eget', 'lat'], ['lånat mot låt', 'lanat', 'lat']]) {
  const g = {}; rader.forEach(r => (g[r.k + '|' + r.f] ??= []).push(r)); const d = []
  for (const v of Object.values(g)) { const x = v.filter(r => r.l === a).map(r => r.rel), y = v.filter(r => r.l === b).map(r => r.rel); if (x.length >= 3 && y.length >= 3) d.push(median(x) - median(y)) }
  const upp = d.filter(z => z > 0).length
  let p = 0; for (let i = upp; i <= d.length; i++) { let c = 1; for (let j = 0; j < i; j++) c = c * (d.length - j) / (j + 1); p += c / 2 ** d.length }
  console.log(`${namn.padEnd(16)} ×${Math.exp(median(d)).toFixed(2)} (median över ${d.length} konto × familj, ${upp} av ${d.length} högre, teckentest p ${p.toFixed(4)})`)
}
for (const f of ['dialogsketch', 'tilltal_med_mat', 'stamningsmontage', 'trend', 'kampanj']) {
  const g = {}; rader.filter(r => r.f === f).forEach(r => (g[r.k] ??= []).push(r)); const d = []
  for (const v of Object.values(g)) { const x = v.filter(r => r.l === 'eget').map(r => r.rel), y = v.filter(r => r.l !== 'eget').map(r => r.rel); if (x.length >= 3 && y.length >= 3) d.push(median(x) - median(y)) }
  console.log(`  ${f.padEnd(18)} eget mot annat ×${Math.exp(median(d)).toFixed(2)} (${d.filter(z => z > 0).length} av ${d.length} konton)`)
}
