// Engagemang per formatfamilj på hela banken (6 nov 2026, inga anrop).
// Förregistrering: data/format/engagemang/forregistrering.json
//   node format/engagemang.mjs
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { DATA } from '../analys/pipeline.mjs'
import { historik } from './serieprofil.mjs'
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const FAM = Object.fromEntries(Object.entries(las(path.join(DATA, 'format', 'familjer', 'familjer-lokal.json'))).map(([k, v]) => [k, v.familj]))
const DL = path.join(os.homedir(), 'Downloads', 'letrend-bank')
const median = a => { const b = a.filter(Number.isFinite).sort((x, y) => x - y); return b.length ? (b.length % 2 ? b[(b.length - 1) / 2] : (b[b.length / 2 - 1] + b[b.length / 2]) / 2) : NaN }
const binom = (k, n) => { let s = 0; for (let i = k; i <= n; i++) { let c = 1; for (let j = 0; j < i; j++) c = c * (n - j) / (j + 1); s += c / 2 ** n } return s }

const rader = []
for (const k of fs.readdirSync(path.join(DATA, 'bank')).filter(k => fs.existsSync(path.join(DATA, 'bank', k, 'lista.json')))) {
  const L = historik(k).filter(x => x.visningar > 0 && x.datum); if (L.length < 30) continue
  const t = L.map(x => Date.parse(x.datum)), r = []
  L.forEach((x, i) => {
    const p = path.join(DL, k, `${x.id}.info.json`); if (!fs.existsSync(p) || !FAM[x.s.id]) return
    const j = las(p), v = j.view_count || x.visningar; if (!(v > 0)) return
    const gr = L.map((y, q) => ({ q, d: Math.abs(t[q] - t[i]) })).filter(g => g.q !== i).sort((a, b) => a.d - b.d).slice(0, 15)
    r.push({ k, f: FAM[x.s.id], rv: Math.log(x.visningar) - Math.log(median(gr.map(g => L[g.q].visningar))),
      kom: Math.log(((j.comment_count ?? 0) + 1) / v), spar: Math.log(((j.save_count ?? 0) + 1) / v), rep: Math.log(((j.repost_count ?? 0) + 1) / v), like: Math.log(((j.like_count ?? 0) + 1) / v) })
  })
  for (const m of ['kom', 'spar', 'rep', 'like']) { const md = median(r.map(x => x[m])); r.forEach(x => { x[m] -= md }) }
  rader.push(...r)
}
const UTF = ['rv', 'kom', 'spar', 'rep', 'like'], FAMS = [...new Set(rader.map(r => r.f))]
console.log(`${rader.length} klipp, ${new Set(rader.map(r => r.k)).size} konton`)
// familj mot kontots övriga klipp
function mot(f, m, annan = null) {
  const g = {}; rader.forEach(r => (g[r.k] ??= []).push(r)); const d = []
  for (const v of Object.values(g)) { const a = v.filter(r => r.f === f).map(r => r[m]), b = v.filter(r => annan ? r.f === annan : r.f !== f).map(r => r[m]); if (a.length >= 3 && b.length >= 3) d.push(median(a) - median(b)) }
  const upp = d.filter(x => x > 0).length
  return { x: Math.exp(median(d)), upp, n: d.length, pHog: binom(upp, d.length), pLag: binom(d.length - upp, d.length) }
}
const fmt = o => o.n ? `×${o.x.toFixed(2)} (${o.upp}/${o.n})` : '–'
console.log('\nE5 profil: familj mot kontots övriga klipp, median över konton (antal konton där familjen ligger högre / alla)')
console.log('familj'.padEnd(22) + UTF.map(u => ({ rv: 'räckvidd', kom: 'kommentarer', spar: 'sparningar', rep: 'reposts', like: 'likes' })[u].padEnd(16)).join(''))
for (const f of FAMS) console.log(f.padEnd(22) + UTF.map(u => fmt(mot(f, u)).padEnd(16)).join(''))
const res = {}
const e1 = mot('gatuinslag', 'kom'); res.E1 = e1; console.log(`\nE1 gatuinslag, kommentarer: ${fmt(e1)} p ${e1.pHog.toFixed(4)}`)
const e2a = mot('stamningsmontage', 'spar', 'dialogsketch'), e2b = mot('tilltal_med_mat', 'spar', 'dialogsketch'); res.E2 = { e2a, e2b }
console.log(`E2 sparningar mot dialogsketch: mat ${fmt(e2a)} p ${e2a.pHog.toFixed(4)}; tilltal_med_mat ${fmt(e2b)} p ${e2b.pHog.toFixed(4)}`)
const e3a = mot('dialogsketch', 'rv'), e3b = mot('dialogsketch', 'rep'); res.E3 = { e3a, e3b }
console.log(`E3 dialogsketch: räckvidd ${fmt(e3a)} p ${e3a.pHog.toFixed(4)}; reposts ${fmt(e3b)} p ${e3b.pHog.toFixed(4)}`)
const e4a = mot('kampanj', 'kom'), e4b = mot('kampanj', 'rv'); res.E4 = { e4a, e4b }
console.log(`E4 kampanj: kommentarer ${fmt(e4a)} p ${e4a.pHog.toFixed(4)}; räckvidd ${fmt(e4b)} p(lägre) ${e4b.pLag.toFixed(4)}`)
fs.writeFileSync(path.join(DATA, 'format', 'engagemang', 'resultat.json'), JSON.stringify({ klipp: rader.length, ...res, profil: Object.fromEntries(FAMS.map(f => [f, Object.fromEntries(UTF.map(u => [u, mot(f, u)]))])) }, null, 1))
