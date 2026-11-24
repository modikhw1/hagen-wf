// E1-analys: hur mycket av varje lager är klippet, och hur mycket är modell, prompt och slump?
// - Variansandelar (generaliseringsteori, helt korsad slumpmodell klipp × modell × prompt med två
//   körningar per cell) för lager med siffervärden (bin, ord).
// - Krippendorffs alfa över alla 18 bedömningar per klipp (intervall för bin/ord, nominal för kat),
//   och inom varje modell (6 bedömningar per klipp).
// - Exakt överensstämmelse: samma modell och prompt i två körningar, samma modell med olika prompter,
//   och olika modeller med samma prompt.
// Kriteriet låstes innan analysen kördes: ett lager är STABILT om alfa över alla modeller ≥ 0,667 och
// klippets andel av variansen ≥ 0,5 (för kat: alfa ≥ 0,667).
//
//   node format/e1-analys.mjs
// Resultat: data/format/e1/analys.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { LAGER } from './lager.mjs'

const E1 = path.join(DATA, 'format', 'e1')
const urval = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'kalib', 'urval.json'), 'utf8'))
const MODELLER = fs.readdirSync(E1).filter(d => fs.statSync(path.join(E1, d)).isDirectory())
const P = [1, 2, 3], K = [1, 2]
const data = {} // data[modell][p][k][id] = svar
for (const m of MODELLER) { data[m] = {}; for (const p of P) { data[m][p] = {}; for (const k of K) { data[m][p][k] = {}; const d = path.join(E1, m, `p${p}-k${k}`); if (!fs.existsSync(d)) continue; for (const f of fs.readdirSync(d)) { const x = JSON.parse(fs.readFileSync(path.join(d, f), 'utf8')); data[m][p][k][x.id] = x } } } }

const tal = v => typeof v === 'boolean' ? (v ? 1 : 0) : v
function alfa(enheter, typ) { // enheter: array av arrayer med värden (null = saknas)
  const o = new Map(), add = (a, b, w) => { const k = `${a}\u0000${b}`; o.set(k, (o.get(k) ?? 0) + w) }
  for (const u of enheter) { const v = u.filter(x => x != null); const m = v.length; if (m < 2) continue; for (let i = 0; i < m; i++) for (let j = 0; j < m; j++) if (i !== j) add(v[i], v[j], 1 / (m - 1)) }
  const nc = new Map(); let n = 0
  for (const [k, w] of o) { const c = k.split('\u0000')[0]; nc.set(c, (nc.get(c) ?? 0) + w); n += w }
  const d2 = (a, b) => typ === 'kat' ? (a === b ? 0 : 1) : (Number(a) - Number(b)) ** 2
  let Do = 0; for (const [k, w] of o) { const [a, b] = k.split('\u0000'); Do += w * d2(a, b) }
  Do /= n
  let De = 0; const vals = [...nc.keys()]; for (const a of vals) for (const b of vals) De += nc.get(a) * nc.get(b) * d2(a, b)
  De /= n * (n - 1)
  return De === 0 ? NaN : 1 - Do / De
}

function varians(namn) { // generaliseringsteori, balanserad design; saknade värden fylls med cellens andra körning eller modellens klippmedel
  const C = urval.length, M = MODELLER.length, Pn = P.length, R = K.length
  const y = urval.map(kl => MODELLER.map(m => P.map(p => K.map(k => { const v = data[m][p][k][kl.id]?.[namn]; return v == null ? null : tal(v) }))))
  for (const c of y) for (const mm of c) { const alla = mm.flat().filter(v => v != null); const mx = alla.length ? alla.reduce((a, b) => a + b) / alla.length : 0; for (const pp of mm) for (let r = 0; r < R; r++) if (pp[r] == null) pp[r] = pp[1 - r] ?? mx }
  const mean = a => a.reduce((s, v) => s + v, 0) / a.length
  const G = mean(y.flat(3))
  const mc = y.map(c => mean(c.flat(2))), mm = MODELLER.map((_, j) => mean(y.map(c => c[j].flat()).flat())), mp = P.map((_, l) => mean(y.map(c => c.map(m => m[l])).flat(2)))
  const mcm = y.map(c => c.map(m => mean(m.flat()))), mcp = y.map(c => P.map((_, l) => mean(c.map(m => m[l]).flat()))), mmp = MODELLER.map((_, j) => P.map((_, l) => mean(y.map(c => c[j][l]).flat())))
  const cell = y.map(c => c.map(m => m.map(p => mean(p))))
  let SSc = 0, SSm = 0, SSp = 0, SScm = 0, SScp = 0, SSmp = 0, SScmp = 0, SSe = 0
  for (let i = 0; i < C; i++) SSc += M * Pn * R * (mc[i] - G) ** 2
  for (let j = 0; j < M; j++) SSm += C * Pn * R * (mm[j] - G) ** 2
  for (let l = 0; l < Pn; l++) SSp += C * M * R * (mp[l] - G) ** 2
  for (let i = 0; i < C; i++) for (let j = 0; j < M; j++) SScm += Pn * R * (mcm[i][j] - mc[i] - mm[j] + G) ** 2
  for (let i = 0; i < C; i++) for (let l = 0; l < Pn; l++) SScp += M * R * (mcp[i][l] - mc[i] - mp[l] + G) ** 2
  for (let j = 0; j < M; j++) for (let l = 0; l < Pn; l++) SSmp += C * R * (mmp[j][l] - mm[j] - mp[l] + G) ** 2
  for (let i = 0; i < C; i++) for (let j = 0; j < M; j++) for (let l = 0; l < Pn; l++) {
    SScmp += R * (cell[i][j][l] - mcm[i][j] - mcp[i][l] - mmp[j][l] + mc[i] + mm[j] + mp[l] - G) ** 2
    for (let r = 0; r < R; r++) SSe += (y[i][j][l][r] - cell[i][j][l]) ** 2
  }
  const MS = { c: SSc / (C - 1), m: SSm / (M - 1), p: SSp / (Pn - 1), cm: SScm / ((C - 1) * (M - 1)), cp: SScp / ((C - 1) * (Pn - 1)), mp: SSmp / ((M - 1) * (Pn - 1)), cmp: SScmp / ((C - 1) * (M - 1) * (Pn - 1)), e: SSe / (C * M * Pn * (R - 1)) }
  const v = {}
  v.e = MS.e
  v.cmp = Math.max(0, (MS.cmp - MS.e) / R)
  v.cm = Math.max(0, (MS.cm - MS.cmp) / (R * Pn))
  v.cp = Math.max(0, (MS.cp - MS.cmp) / (R * M))
  v.mp = Math.max(0, (MS.mp - MS.cmp) / (R * C))
  v.c = Math.max(0, (MS.c - MS.cm - MS.cp + MS.cmp) / (R * M * Pn))
  v.m = Math.max(0, (MS.m - MS.cm - MS.mp + MS.cmp) / (R * C * Pn))
  v.p = Math.max(0, (MS.p - MS.cp - MS.mp + MS.cmp) / (R * C * M))
  const tot = Object.values(v).reduce((a, b) => a + b, 0) || 1
  return { klipp: v.c / tot, modell: (v.m + v.cm) / tot, prompt: (v.p + v.cp + v.mp) / tot, slump: (v.cmp + v.e) / tot, modellmedel: Object.fromEntries(MODELLER.map((m, j) => [m, +mm[j].toFixed(2)])) }
}

function overens(namn) {
  let a = 0, an = 0, b = 0, bn = 0, c = 0, cn = 0
  for (const kl of urval) {
    for (const m of MODELLER) for (const p of P) { const x = data[m][p][1][kl.id]?.[namn], y = data[m][p][2][kl.id]?.[namn]; if (x != null && y != null) { an++; if (x === y) a++ } }
    for (const m of MODELLER) for (const [p, q] of [[1, 2], [1, 3], [2, 3]]) { const x = data[m][p][1][kl.id]?.[namn], y = data[m][q][1][kl.id]?.[namn]; if (x != null && y != null) { bn++; if (x === y) b++ } }
    for (const p of P) for (let i = 0; i < MODELLER.length; i++) for (let j = i + 1; j < MODELLER.length; j++) { const x = data[MODELLER[i]][p][1][kl.id]?.[namn], y = data[MODELLER[j]][p][1][kl.id]?.[namn]; if (x != null && y != null) { cn++; if (x === y) c++ } }
  }
  return { omkorning: a / an, prompt: b / bn, modell: c / cn }
}

const ut = {}
for (const [namn, [typ]] of Object.entries(LAGER)) {
  const enh = (ms) => urval.map(kl => ms.flatMap(m => P.flatMap(p => K.map(k => { const v = data[m][p][k][kl.id]?.[namn]; return v == null ? null : (typ === 'kat' ? v : tal(v)) }))))
  const r = { typ, alfa: alfa(enh(MODELLER), typ), alfaPerModell: Object.fromEntries(MODELLER.map(m => [m, alfa(enh([m]), typ)])), overens: overens(namn) }
  if (typ !== 'kat') r.varians = varians(namn)
  r.stabil = r.alfa >= 0.667 && (typ === 'kat' || r.varians.klipp >= 0.5)
  ut[namn] = r
}
const tok = Object.fromEntries(MODELLER.map(m => { let t = 0, n = 0; for (const p of P) for (const k of K) for (const x of Object.values(data[m][p][k])) { t += x.tokens ?? 0; n++ } return [m, { anrop: n, tokens: Math.round(t / n) }] }))
fs.writeFileSync(path.join(E1, 'analys.json'), JSON.stringify({ modeller: tok, lager: ut }, null, 1))

const f = x => Number.isFinite(x) ? x.toFixed(2) : ' -  '
const kort = m => m.replace('gemini-', '').replace('-preview', '')
console.log('anrop och tokens per modell:', JSON.stringify(tok))
console.log(`\n${'lager'.padEnd(17)} typ  alfa | ${MODELLER.map(m => kort(m).padEnd(9)).join(' ')}| klipp modell prompt slump | omk  prompt modell | stabil`)
for (const [namn, r] of Object.entries(ut).sort((a, b) => (b[1].alfa || 0) - (a[1].alfa || 0))) {
  const v = r.varians
  console.log(`${namn.padEnd(17)} ${r.typ}  ${f(r.alfa)} | ${MODELLER.map(m => f(r.alfaPerModell[m]).padEnd(9)).join(' ')}| ${v ? [v.klipp, v.modell, v.prompt, v.slump].map(f).join('  ') : '   (kategorier)       '} | ${f(r.overens.omkorning)} ${f(r.overens.prompt)}  ${f(r.overens.modell)} | ${r.stabil ? 'JA' : ''}`)
}
const st = Object.entries(ut).filter(([, r]) => r.stabil).map(([n]) => n)
console.log(`\nstabila lager (${st.length} av ${Object.keys(ut).length}): ${st.join(', ')}`)
