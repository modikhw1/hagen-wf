// Serie 2g: fasskiften med familjerna grupperade (person, mat, trend, kampanj), med kontroll för tidstrend.
// Förregistrering: data/format/serie2g/forregistrering.json. Inga anrop.
//   node format/serie2g.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { historik } from './serieprofil.mjs'
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const GRUPP = { dialogsketch: 'person', ordvits: 'person', absurd_improvisation: 'person', gatuinslag: 'person', tilltal_med_mat: 'person', text_utan_tal: 'person', stamningsmontage: 'mat', trend: 'trend', kampanj: 'kampanj' }
const TYPER = ['person', 'mat', 'trend', 'kampanj']
const FAM = Object.fromEntries(Object.entries(las(path.join(DATA, 'format', 'familjer', 'familjer-lokal.json'))).map(([k, v]) => [k, GRUPP[v.familj]]).filter(([, g]) => g))
const median = a => { const b = a.filter(Number.isFinite).sort((x, y) => x - y); return b.length ? (b.length % 2 ? b[(b.length - 1) / 2] : (b[b.length / 2 - 1] + b[b.length / 2]) / 2) : NaN }
function ll(seq) { const c = {}; seq.forEach(x => { c[x] = (c[x] || 0) + 1 }); return Object.values(c).reduce((s, n) => s + n * Math.log(n / seq.length), 0) }
function segment(seq, a = 0, b = seq.length, ut = []) {
  const straff = 0.5 * (TYPER.length - 1) * Math.log(seq.length) * 2
  let bast = null
  for (let m = a + 15; m <= b - 15; m++) { const g = ll(seq.slice(a, m)) + ll(seq.slice(m, b)) - ll(seq.slice(a, b)); if (!bast || g > bast.g) bast = { m, g } }
  if (b - a >= 30 && bast && bast.g > straff) { segment(seq, a, bast.m, ut); ut.push(bast.m); segment(seq, bast.m, b, ut) }
  return ut
}
const dom = s => { const c = {}; s.forEach(x => { c[x.g] = (c[x.g] || 0) + 1 }); return Object.entries(c).sort((p, q) => q[1] - p[1])[0][0] }
const konton = fs.readdirSync(path.join(DATA, 'bank')).filter(k => fs.existsSync(path.join(DATA, 'bank', k, 'lista.json')))
const skiften = [], utan = []
for (const k of konton) {
  const L = historik(k).filter(x => x.visningar > 0 && x.datum && FAM[x.s.id]).map(x => ({ ...x, g: FAM[x.s.id] })).reverse()
  if (L.length < 30) continue
  const cut = segment(L.map(x => x.g)).sort((a, b) => a - b)
  if (!cut.length) { utan.push(L); continue }
  const gr = [0, ...cut, L.length]
  for (let i = 1; i < gr.length - 1; i++) {
    const A = L.slice(gr[i - 1], gr[i]), B = L.slice(gr[i], gr[i + 1])
    skiften.push({ k, fran: dom(A), till: dom(B), pos: gr[i] / L.length, d: median(B.map(x => Math.log(x.visningar))) - median(A.map(x => Math.log(x.visningar))), nA: A.length, nB: B.length })
  }
}
// kontroll: låtsasbrytpunkt på samma relativa position i konton utan skifte, fönster lika långa som skiftets
let fro = 5; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const kontroll = s => { const d = []; for (let t = 0; t < 100 && utan.length; t++) { const L = utan[Math.floor(sl() * utan.length)], m = Math.max(15, Math.min(L.length - 15, Math.round(s.pos * L.length))); d.push(median(L.slice(m, Math.min(L.length, m + s.nB)).map(x => Math.log(x.visningar))) - median(L.slice(Math.max(0, m - s.nA), m).map(x => Math.log(x.visningar)))) } return median(d) }
skiften.forEach(s => { s.kontroll = kontroll(s); s.netto = s.d - s.kontroll })
console.log(`${skiften.length} skiften i ${new Set(skiften.map(s => s.k)).size} konton; ${utan.length} konton utan skifte (kontroll)`)
const rad = (namn, v) => v.length ? console.log(`${namn.padEnd(18)} n ${String(v.length).padStart(2)}  efter/före ×${Math.exp(median(v.map(s => s.d))).toFixed(2)}  kontroll ×${Math.exp(median(v.map(s => s.kontroll))).toFixed(2)}  netto ×${Math.exp(median(v.map(s => s.netto))).toFixed(2)}  uppåt netto ${v.filter(s => s.netto > 0).length}/${v.length}`) : console.log(`${namn.padEnd(18)} n 0`)
rad('alla', skiften)
const byten = {}; skiften.forEach(s => { const b = `${s.fran}→${s.till}`; (byten[b] ??= []).push(s) })
for (const [b, v] of Object.entries(byten).sort((a, c) => c[1].length - a[1].length)) rad(b, v)
rad('S2g1 mat→person', skiften.filter(s => s.fran === 'mat' && s.till === 'person'))
rad('S2g2 person→mat', skiften.filter(s => s.fran === 'person' && s.till === 'mat'))
rad('till trend', skiften.filter(s => s.till === 'trend')); rad('från trend', skiften.filter(s => s.fran === 'trend'))
rad('till kampanj', skiften.filter(s => s.till === 'kampanj')); rad('från kampanj', skiften.filter(s => s.fran === 'kampanj'))
fs.writeFileSync(path.join(DATA, 'format', 'serie2g', 'resultat.json'), JSON.stringify({ skiften, utan: utan.length }, null, 1))
