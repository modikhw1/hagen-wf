// E14: mäter lagren mot samlingen själv (HE14a, HE14b) och redovisar avläsningen mot ägaren (HE14c).
//   node format/e14-analys.mjs [--dump]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'

const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const E = path.join(DATA, 'format', 'e14'), PLAN = las(path.join(DATA, 'format', 'e13', 'plan.json'))
const FAM = las(path.join(DATA, 'format', 'familjer', 'familjer.json'))
const kunder = Object.keys(PLAN).filter(k => fs.existsSync(path.join(E, 'sjalv', `${k}.json`)))
const undan = Object.fromEntries(kunder.map(k => [k, las(path.join(E, 'sjalv', `${k}.json`)).undan]))
const agare = id => id.slice(0, id.lastIndexOf('-'))
const SUFF = process.argv.includes('--modell') ? '-' + process.argv[process.argv.indexOf('--modell') + 1] : ''
const mote = (k, id) => { const f = path.join(E, 'mote' + SUFF, `${k}__${id}.json`); return fs.existsSync(f) ? las(f).mote : null }
// AUC: andel par (eget, främmande) där det egna får högre värde; lika räknas som halv.
const auc = (egna, andra) => { if (!egna.length || !andra.length) return NaN; let s = 0; for (const a of egna) for (const b of andra) s += a > b ? 1 : a === b ? 0.5 : 0; return s / (egna.length * andra.length) }
const medel = x => x.reduce((s, v) => s + v, 0) / x.length

console.log('HE14a/b: känner självet igen aktörens egna undanhållna klipp, av bara motorn?\n')
const A = [], B = [], H = []
const allaUndan = Object.values(undan).flat()
for (const k of kunder) {
  const rad = allaUndan.map(id => ({ id, egen: agare(id) === k, m: mote(k, id) })).filter(r => r.m)
  const e = rad.filter(r => r.egen), a = rad.filter(r => !r.egen)
  const a1 = auc(e.map(r => r.m.egen), a.map(r => r.m.egen)), h1 = auc(e.map(r => r.m.hemma), a.map(r => r.m.hemma))
  // HE14b: främmande klipp av samma familj som något av kundens egna undanhållna
  const fam = new Set(e.map(r => FAM[r.id]).filter(Boolean)), aF = a.filter(r => fam.has(FAM[r.id]))
  const b1 = auc(e.filter(r => FAM[r.id]).map(r => r.m.egen), aF.map(r => r.m.egen))
  if (Number.isFinite(a1)) { A.push(a1); H.push(h1) } if (Number.isFinite(b1)) B.push(b1)
  console.log(`${k.padEnd(24)} egna ${e.length} (egen ${e.length ? medel(e.map(r => r.m.egen)).toFixed(0) : '–'} %)  främmande ${String(a.length).padStart(2)} (${a.length ? medel(a.map(r => r.m.egen)).toFixed(0) : '–'} %)  AUC egen ${Number.isFinite(a1) ? a1.toFixed(2) : '–'}  AUC hemma ${Number.isFinite(h1) ? h1.toFixed(2) : '–'}  samma familj: ${aF.length} främmande, AUC ${Number.isFinite(b1) ? b1.toFixed(2) : '–'}`)
}
if (A.length) console.log(`\nHE14a  medel-AUC (egen) ${medel(A).toFixed(2)} över ${A.length} kunder, tröskel 0,70, slump 0,50  →  ${medel(A) > 0.7 ? 'håller' : 'förkastas'}   (hemma: ${medel(H).toFixed(2)})`)
if (B.length) console.log(`HE14b  medel-AUC inom samma familj ${medel(B).toFixed(2)} över ${B.length} kunder, tröskel 0,60  →  ${medel(B) > 0.6 ? 'håller' : 'förkastas'}`)

// Läcka: nämner motortexten kundens konto eller yta?
const mek = fs.existsSync(path.join(E, 'mekanism')) ? fs.readdirSync(path.join(E, 'mekanism')).map(f => las(path.join(E, 'mekanism', f))) : []
const VAROR = /pizz|kebab|burgar|burger|kyckling|chicken|pasta|kaffe|café|cafe|biff|steak|taco|glass|sushi|falafel|bakelse|bulle|drink|cocktail/i
const lack = mek.filter(m => { const { yta, ...r } = m.mekanism; return VAROR.test(JSON.stringify(r)) })
console.log(`\nLäcka: ${lack.length} av ${mek.length} motortexter nämner en vara utanför fältet "yta".`)

// HE14c: avläsning mot ägaren, utan justering
const par = []
for (const k of kunder) for (const c of PLAN[k].kandidater) { if (!Number.isFinite(c.agare)) continue; const m = mote(k, c.id); if (m) par.push({ konto: k, id: c.id, kalla: c.kalla, agare: c.agare, hemma: m.hemma, egen: m.egen, m }) }
const centrera = (R, f) => { const mm = {}; for (const k of new Set(R.map(r => r.konto))) { const x = R.filter(r => r.konto === k); mm[k] = medel(x.map(f)) } return R.map(r => f(r) - mm[r.konto]) }
if (par.length >= 8) {
  console.log(`\nHE14c: avläsning mot ägarens passform (${par.length} par), ingen tröskel:`)
  for (const [n, f] of [['hemma', r => r.hemma], ['egen', r => r.egen]]) console.log(`  ${n.padEnd(6)} rho ${spearman(par.map(r => r.agare), par.map(f)).toFixed(2)}  inom kund ${spearman(centrera(par, r => r.agare), centrera(par, f)).toFixed(2)}  medel ${medel(par.map(f)).toFixed(1)} (ägaren ${medel(par.map(r => r.agare)).toFixed(1)})`)
  const E13 = path.join(DATA, 'format', 'e13', 'b2-4-argon'), b2 = par.map(r => { const f = path.join(E13, `${r.konto}__${r.id}.json`); return fs.existsSync(f) ? las(f).svar.passform : NaN })
  const ok = par.map((r, i) => ({ ...r, b2: b2[i] })).filter(r => Number.isFinite(r.b2))
  if (ok.length >= 8) console.log(`  E13 b2 (Argon, skala) på samma par: inom kund ${spearman(centrera(ok, r => r.agare), centrera(ok, r => r.b2)).toFixed(2)};  hemma + b2: ${spearman(centrera(ok, r => r.agare), centrera(ok, r => r.b2).map((v, i) => v + centrera(ok, r => r.hemma)[i])).toFixed(2)}`)
}
if (process.argv.includes('--dump')) for (const r of [...par].sort((a, b) => Math.abs(b.agare - b.hemma) - Math.abs(a.agare - a.hemma)).slice(0, 12)) console.log(`\n${r.konto} ← ${r.id}\n  ägare ${r.agare}, hemma ${r.hemma}, egen ${r.egen} %\n  förstärker: ${r.m.forstarker}\n  bryter: ${r.m.bryter}\n  offras: ${r.m.offras}`)
