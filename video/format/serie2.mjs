// Serie 2: lönar det sig att hålla kontots fas? Enligt data/format/serie2/forregistrering.json.
// Inga modellanrop: bankens lista (visningar, datum) + sållning (Lite-typ).
//   node format/serie2.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { historik } from './serieprofil.mjs'

const BANK = path.join(DATA, 'bank')
const konton = fs.readdirSync(BANK).filter(k => fs.existsSync(path.join(BANK, k, 'lista.json')))
// SERIE_FAMILJ=1: ägarens formatfamiljer (data/format/familjer/familjer.json) i stället för Lite-typen (S1f, S2f)
const FAMJ = !process.env.SERIE_FAMILJ ? null : process.env.SERIE_FAMILJ === 'lokal' ? Object.fromEntries(Object.entries(JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'familjer', 'familjer-lokal.json'), 'utf8'))).map(([k, v]) => [k, v.familj])) : JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'familjer', 'familjer.json'), 'utf8'))
const TYPER = FAMJ ? Object.keys(JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'familjer', 'forregistrering.json'), 'utf8')).familjer) : ['matporr_och_process', 'direkt_tilltal', 'relaterbar_sketch', 'vardens_provsmakning', 'annat']
const median = a => { const b = a.filter(Number.isFinite).sort((x, y) => x - y); return b.length ? (b.length % 2 ? b[(b.length - 1) / 2] : (b[b.length / 2 - 1] + b[b.length / 2]) / 2) : NaN }
const entropi = b => { const c = {}; b.forEach(x => { c[x] = (c[x] || 0) + 1 }); return -Object.values(c).reduce((s, n) => s + (n / b.length) * Math.log(n / b.length), 0) }

// Per konto: kronologiskt (äldst först), relativ räckvidd mot rullande median av 15 närmaste i tid
const data = []
for (const k of konton) {
  const L = historik(k).filter(x => Number.isFinite(x.visningar) && x.visningar > 0 && x.datum && (!FAMJ || FAMJ[x.s.id])).map(x => FAMJ ? { ...x, s: { ...x.s, typ: FAMJ[x.s.id] } } : x).reverse()
  if (L.length < 30) continue
  const t = L.map(x => Date.parse(x.datum))
  L.forEach((x, i) => {
    const gr = L.map((y, j) => ({ j, d: Math.abs(t[j] - t[i]) })).filter(g => g.j !== i).sort((a, b) => a.d - b.d).slice(0, 15)
    x.rel = Math.log(x.visningar) - Math.log(median(gr.map(g => L[g.j].visningar)))
    const fore = L.slice(Math.max(0, i - 20), i)
    x.fas = fore.length >= 10 ? fore.filter(y => y.s.typ === x.s.typ).length / fore.length : NaN
  })
  data.push({ k, L })
}
console.log(`${data.length} konton, ${data.reduce((s, d) => s + d.L.length, 0)} klipp`)

let fro = 11; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const blanda = v => { for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } return v }
function inomGrupp(rader, grupp, x, y, n = 5000) {
  const g = {}; rader.forEach((r, i) => (g[grupp(r)] ??= []).push(i))
  const cx = rader.map(x), cy = rader.map(y)
  for (const idx of Object.values(g)) { const mx = idx.reduce((s, i) => s + cx[i], 0) / idx.length, my = idx.reduce((s, i) => s + cy[i], 0) / idx.length; idx.forEach(i => { cx[i] -= mx; cy[i] -= my }) }
  const obs = spearman(cx, cy); let hi = 0, lo = 0
  for (let t = 0; t < n; t++) { const z = [...cy]; for (const idx of Object.values(g)) { const v = blanda(idx.map(i => cy[i])); idx.forEach((i, m) => { z[i] = v[m] }) } const r = spearman(cx, z); if (r >= obs) hi++; if (r <= obs) lo++ }
  return { rho: obs, pHog: (hi + 1) / (n + 1), pLag: (lo + 1) / (n + 1), n: rader.length, grupper: Object.values(g).filter(i => i.length > 1).length }
}

// S1
const s1 = data.flatMap(d => d.L.filter(x => Number.isFinite(x.fas) && Number.isFinite(x.rel)).map(x => ({ k: d.k, typ: x.s.typ, fas: x.fas, rel: x.rel })))
const r1 = inomGrupp(s1.filter((r, _, a) => a.filter(z => z.k === r.k && z.typ === r.typ).length >= 5), r => r.k + '|' + r.typ, r => r.fas, r => r.rel)
console.log(`S1 fasandel → relativ räckvidd inom konto × typ: rho ${r1.rho.toFixed(3)}, ensidigt p ${r1.pHog.toFixed(4)} (n ${r1.n}, ${r1.grupper} grupper)`)
for (const typ of TYPER) {
  const s = s1.filter(r => r.typ === typ); if (s.length < 100) continue
  const r = inomGrupp(s.filter((q, _, a) => a.filter(z => z.k === q.k).length >= 5), q => q.k, q => q.fas, q => q.rel, 2000)
  console.log(`   ${typ.padEnd(22)} rho ${r.rho.toFixed(3)}  p ${r.pHog.toFixed(3)}  n ${r.n}`)
}
// Effektstorlek i klartext: fasandel ≥ 0,5 mot ≤ 0,15 inom konto × typ
{ const g = {}; s1.forEach(r => { (g[r.k + '|' + r.typ] ??= []).push(r) }); const d = []
  for (const v of Object.values(g)) { const a = v.filter(r => r.fas >= 0.5).map(r => r.rel), b = v.filter(r => r.fas <= 0.15).map(r => r.rel); if (a.length >= 3 && b.length >= 3) d.push(median(a) - median(b)) }
  console.log(`   i fas (≥ 50 %) mot utanför (≤ 15 %): median skillnad ×${Math.exp(median(d)).toFixed(2)} i visningar över ${d.length} konto × typ`) }

// S4 och S3: block om 10 (kronologiska)
const block = data.flatMap(d => { const b = []; for (let i = 0; i + 10 <= d.L.length; i += 10) { const s = d.L.slice(i, i + 10); b.push({ k: d.k, H: entropi(s.map(x => x.s.typ)), rel: median(s.map(x => x.rel)), G: s.filter(x => x.s.typ === 'vardens_provsmakning').length / 10 }) } return b })
const r4 = inomGrupp(block, r => r.k, r => r.H, r => r.rel)
console.log(`S4 typentropi per block → median relativ räckvidd inom konto: rho ${r4.rho.toFixed(3)}, ensidigt p (negativ) ${r4.pLag.toFixed(4)} (n ${r4.n} block, ${r4.grupper} konton)`)
{ const d = []; for (const k of new Set(block.map(b => b.k))) { const v = block.filter(b => b.k === k), a = v.filter(b => b.G > 0.25).map(b => b.rel), c = v.filter(b => b.G > 0 && b.G <= 0.25).map(b => b.rel); if (a.length && c.length) d.push(median(a) - median(c)) }
  console.log(`S3 G > 25 % mot 1–25 % inom konto: ${d.length} konton, median skillnad ×${Math.exp(median(d)).toFixed(2)}, ${d.filter(x => x < 0).length} av ${d.length} lägre`) }

// S2: fasskiften, binär segmentering
function ll(seq) { const c = {}; seq.forEach(x => { c[x] = (c[x] || 0) + 1 }); return Object.values(c).reduce((s, n) => s + n * Math.log(n / seq.length), 0) }
function segment(seq, a = 0, b = seq.length, ut = []) {
  const n = b - a, straff = 0.5 * (TYPER.length - 1) * Math.log(seq.length) * 2
  let bast = null
  for (let m = a + 15; m <= b - 15; m++) { const g = ll(seq.slice(a, m)) + ll(seq.slice(m, b)) - ll(seq.slice(a, b)); if (!bast || g > bast.g) bast = { m, g } }
  if (n >= 30 && bast && bast.g > straff) { segment(seq, a, bast.m, ut); ut.push(bast.m); segment(seq, bast.m, b, ut) }
  return ut
}
let medSkifte = 0, skiften = 0; const fore = [], efter = [], domByte = []
for (const d of data) {
  const seq = d.L.map(x => x.s.typ), cut = segment(seq).sort((a, b) => a - b)
  if (cut.length) medSkifte++
  skiften += cut.length
  const gr = [0, ...cut, seq.length]
  for (let i = 1; i < gr.length - 1; i++) {
    const A = d.L.slice(gr[i - 1], gr[i]), B = d.L.slice(gr[i], gr[i + 1])
    fore.push(median(A.map(x => Math.log(x.visningar)))); efter.push(median(B.map(x => Math.log(x.visningar))))
    const dom = s => { const c = {}; s.forEach(x => { c[x.s.typ] = (c[x.s.typ] || 0) + 1 }); return Object.entries(c).sort((p, q) => q[1] - p[1])[0][0] }
    domByte.push(`${dom(A)}→${dom(B)}`)
  }
}
const diff = fore.map((f, i) => efter[i] - f)
console.log(`S2 fasskiften: ${medSkifte} av ${data.length} konton har minst ett (${skiften} totalt). Absoluta visningar efter mot före: median ×${Math.exp(median(diff)).toFixed(2)}, ${diff.filter(x => x > 0).length} av ${diff.length} uppåt.`)
const byten = {}; domByte.forEach(b => { byten[b] = (byten[b] || 0) + 1 }); console.log('   dominant typ före→efter:', Object.entries(byten).sort((a, b) => b[1] - a[1]).map(([b, n]) => `${b.replace(/matporr_och_process/g, 'mat').replace(/direkt_tilltal/g, 'tilltal').replace(/relaterbar_sketch/g, 'sketch').replace(/vardens_provsmakning/g, 'gata')} ${n}`).join(', '))
// skiften mot sketch vs bort från sketch
const mot = domByte.map((b, i) => ({ b, d: diff[i] }))
for (const [namn, f] of [['till sketch', b => b.endsWith('relaterbar_sketch') && !b.startsWith('relaterbar_sketch')], ['från sketch', b => b.startsWith('relaterbar_sketch') && !b.endsWith('relaterbar_sketch')], ['till mat', b => b.endsWith('matporr_och_process') && !b.startsWith('matporr_och_process')], ['från mat', b => b.startsWith('matporr_och_process') && !b.endsWith('matporr_och_process')]]) {
  const v = mot.filter(x => f(x.b)).map(x => x.d); if (v.length) console.log(`   ${namn.padEnd(12)} n ${v.length}, median ×${Math.exp(median(v)).toFixed(2)}`)
}
fs.writeFileSync(path.join(DATA, 'format', 'serie2', FAMJ ? `resultat-familj-${process.env.SERIE_FAMILJ}.json` : 'resultat.json'), JSON.stringify({ S1: r1, S4: r4, konton: data.length, skiften, medSkifte }, null, 1))
