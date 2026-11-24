// E13: läsarnas passform mot ägarens (pass 4–6), totalt och inom kund, med samma räknesätt som familjer-analys.mjs.
//   node format/e13-analys.mjs [--dump]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'

const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const E = path.join(DATA, 'format', 'e13'), PLAN = las(path.join(E, 'plan.json'))
const SAL = path.join(DATA, 'bank', 'sallning'), FAMJ = las(path.join(DATA, 'format', 'familjer', 'familjer.json'))
const lasare = fs.readdirSync(E).filter(d => /^b[123]-/.test(d))
const REP = { gor_det_nu: 3, har_gjort_forr: 2, narliggande: 1, aldrig: 0 }

// Familjebaslinjen: log antal av kandidatens familj i kundens hela historik (som i familjer-analys.mjs).
const famAntal = (konto, id) => {
  const typ = FAMJ[id]; if (!typ) return NaN
  const L = las(path.join(DATA, 'bank', konto, 'lista.json')).klipp.filter(x => fs.existsSync(path.join(SAL, `${konto}-${x.id}.json`)) && FAMJ[`${konto}-${x.id}`])
  return L.length ? Math.log(1 + L.filter(x => FAMJ[`${konto}-${x.id}`] === typ).length) : NaN
}

const par = []
for (const [konto, p] of Object.entries(PLAN)) for (const c of p.kandidater) {
  if (!Number.isFinite(c.agare)) continue
  const r = { konto, id: c.id, kalla: c.kalla, agare: c.agare, fam: famAntal(konto, c.id) }
  for (const l of lasare) { const f = path.join(E, l, `${konto}__${c.id}.json`); if (fs.existsSync(f)) { const s = las(f).svar; r[l] = s.passform; r[`${l}:rep`] = REP[s.repertoar]; r[`${l}:svar`] = s } }
  par.push(r)
}
const centrera = (rader, f) => { const m = {}; for (const k of new Set(rader.map(r => r.konto))) { const x = rader.filter(r => r.konto === k); m[k] = x.reduce((s, r) => s + f(r), 0) / x.length } return rader.map(r => f(r) - m[r.konto]) }
function perm(a, b, n = 5000) { const r0 = spearman(a, b); let fler = 0; const x = [...b]; for (let i = 0; i < n; i++) { for (let j = x.length - 1; j > 0; j--) { const k = Math.floor(Math.random() * (j + 1));[x[j], x[k]] = [x[k], x[j]] } if (spearman(a, x) >= r0) fler++ } return (fler + 1) / (n + 1) }
function rad(namn, f, bas = par) {
  const m = bas.filter(r => Number.isFinite(f(r)))
  if (m.length < 8) return console.log(`${namn.padEnd(34)} n ${m.length}`)
  const tot = spearman(m.map(r => r.agare), m.map(f)), a = centrera(m, r => r.agare), b = centrera(m, f), inom = spearman(a, b)
  const p6 = m.filter(r => r.kalla === 'pass6'), p45 = m.filter(r => r.kalla === 'pass45')
  const del = x => x.length >= 6 ? spearman(centrera(x, r => r.agare), centrera(x, f)).toFixed(2) : '–'
  console.log(`${namn.padEnd(34)} n ${String(m.length).padStart(2)}  rho ${tot.toFixed(2)}  inom kund ${inom.toFixed(2)} (p ${perm(a, b).toFixed(3)})  pass4–5 ${del(p45)}  pass6 ${del(p6)}  medelfel ${(m.reduce((s, r) => s + Math.abs(f(r) - r.agare), 0) / m.length).toFixed(2)}`)
}
console.log(`${par.length} par med ägarbetyg, läsare: ${lasare.join(', ') || 'inga'}\n`)
rad('familj: log antal i historiken', r => r.fam)
for (const l of lasare) { rad(`${l}: passform`, r => r[l]); rad(`${l}: repertoar`, r => r[`${l}:rep`]) }
// Gemensamma par, så att läsarna jämförs på samma underlag
const gem = par.filter(r => lasare.every(l => Number.isFinite(r[l])) && Number.isFinite(r.fam))
if (lasare.length > 1 && gem.length >= 8) {
  console.log(`\nPå de ${gem.length} par där alla läsare och familjen finns:`)
  rad('familj: log antal', r => r.fam, gem)
  for (const l of lasare) rad(`${l}: passform`, r => r[l], gem)
  rad('medel av läsarna', r => lasare.reduce((s, l) => s + r[l], 0) / lasare.length, gem)
  for (const l of lasare) rad(`${l} + familj (rang)`, r => r[l] + r.fam, gem)
}
if (process.argv.includes('--dump')) {
  for (const k of Object.keys(PLAN)) { console.log(`\n@${k}`); for (const r of par.filter(x => x.konto === k)) console.log(`  ägare ${r.agare}  ${lasare.map(l => `${l} ${r[l] ?? '–'} (${r[`${l}:svar`]?.repertoar ?? ''})`).join('  ')}  ${r.id}`) }
}
fs.writeFileSync(path.join(E, 'analys.json'), JSON.stringify(par.map(({ konto, id, kalla, agare, fam, ...x }) => ({ konto, id, kalla, agare, fam, ...Object.fromEntries(Object.entries(x).filter(([k]) => !k.endsWith(':svar'))) })), null, 1))
