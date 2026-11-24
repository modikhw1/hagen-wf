// Analys av matchningsvalideringen (pass 4 och 5) enligt data/format/harness/validering/forregistrering.json.
// Ägarens svar kodas i data/format/harness/validering/agare.json:
//   { "klipp": { "<konto>": { "<pos>": { "passform": 1–5, "rek": "som_den_ar" | "andringar" | "nej" } } },
//     "anpassning": { "<konto>": "som_den_ar" | "sma_andringar" | "nej" } }
//   node format/h-valid-analys.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
const V = path.join(DATA, 'format', 'harness', 'validering')
const U = JSON.parse(fs.readFileSync(path.join(V, 'urval.json'), 'utf8'))
const A = JSON.parse(fs.readFileSync(path.join(V, 'agare.json'), 'utf8'))
const medel = a => { const v = a.filter(Number.isFinite); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : NaN }
const rader = Object.entries(U).flatMap(([konto, { klipp }]) => klipp.map(k => ({ ...k, avsandare: k.konto, konto, agare: A.klipp?.[konto]?.[k.pos]?.passform, rek: A.klipp?.[konto]?.[k.pos]?.rek }))).filter(r => Number.isFinite(r.agare))
const kunder = [...new Set(rader.map(r => r.konto))]
let fro = 5; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
function test(a, b) { // ensidigt: medel(a) > medel(b), parvis inom kund, permutation av etiketter inom kund
  const diff = rows => medel(kunder.map(k => { const x = rows.filter(r => r.konto === k); return medel(x.filter(r => a.includes(r.g)).map(r => r.agare)) - medel(x.filter(r => b.includes(r.g)).map(r => r.agare)) }))
  const rows = rader.filter(r => a.includes(r.grupp) || b.includes(r.grupp)).map(r => ({ ...r, g: r.grupp }))
  const obs = diff(rows); let ext = 0
  for (let t = 0; t < 10000; t++) { const p = kunder.flatMap(k => { const x = rows.filter(r => r.konto === k), g = x.map(r => r.g); for (let i = g.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [g[i], g[j]] = [g[j], g[i]] } return x.map((r, i) => ({ ...r, g: g[i] })) }); if (diff(p) >= obs) ext++ }
  return { skillnad: obs, p: (ext + 1) / 10001 }
}
console.log(`${rader.length} bedömda klipp från ${kunder.length} kunder`)
for (const g of ['R', 'D', 'L']) console.log(`  ${g}: medelpassform ${medel(rader.filter(r => r.grupp === g).map(r => r.agare)).toFixed(2)} (n ${rader.filter(r => r.grupp === g).length}), rekommenderas som det är eller med ändringar: ${rader.filter(r => r.grupp === g && r.rek && r.rek !== 'nej').length}`)
const h1 = test(['R', 'D'], ['L']), h2 = test(['R'], ['D'])
console.log(`HM1 R+D > L: skillnad ${h1.skillnad.toFixed(2)}, p ${h1.p.toFixed(4)}`)
console.log(`HM2 R > D: skillnad ${h2.skillnad.toFixed(2)}, p ${h2.p.toFixed(4)}`)
const m = rader.filter(r => Number.isFinite(r.pro_passform))
console.log(`HM3 ägaren mot Pros passform: rho ${spearman(m.map(r => r.agare), m.map(r => r.pro_passform)).toFixed(2)} (n ${m.length})`)
const an = Object.values(A.anpassning ?? {}); console.log(`HM4 anpassningar som den är eller med små ändringar: ${an.filter(x => x !== 'nej').length} av ${an.length}`)
for (const k of kunder) console.log(`  ${k}: ${rader.filter(r => r.konto === k).sort((a, b) => a.pos - b.pos).map(r => `${r.pos}${r.grupp}=${r.agare}`).join(' ')}`)
