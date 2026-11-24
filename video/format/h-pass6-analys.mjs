// Analys av pass 6 enligt data/format/harness/pass6/forregistrering.json.
// Ägarens svar kodas i data/format/harness/pass6/agare.json:
//   { "klipp": { "<konto>": { "<pos 1–5>": { "passform": 1–5, "rek": "som_den_ar"|"andringar"|"nej" } } },
//     "anpassning": { "<konto>": "som_den_ar"|"sma_andringar"|"nej" },
//     "omtest": { "babulsofficial": 1–5, "chickenstreet.canada": 1–5, "kebabbabes": 1–5 } }
//   node format/h-pass6-analys.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
const P = path.join(DATA, 'format', 'harness', 'pass6'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const R = las(path.join(P, 'forregistrering.json')), O = las(path.join(P, 'ordning.json')), A = las(path.join(P, 'agare.json'))
const rader = R.kunder.flatMap(k => O[k].map((id, i) => { const p = R.prognos[k].find(x => x.id === id); return { konto: k, id, typ: p.typ, v5: p.v5_total, pro: p.pro_passform, agare: A.klipp?.[k]?.[i + 1]?.passform } })).filter(r => Number.isFinite(r.agare))
let fro = 6; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
function perm(x, y) { const obs = spearman(x, y); let e = 0; for (let t = 0; t < 10000; t++) { const z = [...y]; for (let i = z.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [z[i], z[j]] = [z[j], z[i]] } if (spearman(x, z) >= obs) e++ } return { rho: obs, p: (e + 1) / 10001 } }
const a = perm(rader.map(r => r.v5), rader.map(r => r.agare)), c = perm(rader.map(r => r.pro), rader.map(r => r.agare))
console.log(`${rader.length} bedömda par`)
console.log(`HP6a v5 total: rho ${a.rho.toFixed(2)}, p ${a.p.toFixed(4)}`)
let ratt = 0, fel = 0
for (const id of R.delade) { const x = rader.filter(r => r.id === id); for (let i = 0; i < x.length; i++) for (let j = i + 1; j < x.length; j++) { if (x[i].agare === x[j].agare) continue; const s = Math.sign(x[i].agare - x[j].agare) * Math.sign(x[i].v5 - x[j].v5); if (s > 0) ratt++; else if (s < 0) fel++ } }
const binom = (k, n) => { let s = 0; for (let i = k; i <= n; i++) { let c = 1; for (let j = 0; j < i; j++) c = c * (n - j) / (j + 1); s += c / 2 ** n } return s }
console.log(`HP6b inom delade klipp: ${ratt} rätt, ${fel} fel, teckentest p ${binom(ratt, ratt + fel).toFixed(4)}`)
console.log(`HP6c Pro som CM: rho ${c.rho.toFixed(2)}, p ${c.p.toFixed(4)}`)
const an = Object.values(A.anpassning ?? {}); console.log(`HP6d anpassningar som kan skickas: ${an.filter(x => x !== 'nej').length} av ${an.length}`)
const V = las(path.join(DATA, 'format', 'harness', 'validering', 'agare.json'))
console.log(`HP6e omtest: ${R.omtest.map(o => `${o.konto} ${V.klipp[o.konto][o.pos].passform} → ${A.omtest?.[o.konto] ?? '–'}`).join(', ')}`)
for (const k of R.kunder) console.log(`  ${k}: ${rader.filter(r => r.konto === k).map(r => `${r.typ[0]} ägare ${r.agare} v5 ${r.v5} pro ${r.pro}`).join(' | ')}`)

// HP6f–j: v6 och v6.1, låsta efter v5 men innan ägaren sett passet.
for (const [namn, fil, falt] of [['v6 LeTrend-värde', 'forregistrering-v6.json', 'v6_varde'], ['v6 nytta (E7)', 'forregistrering-v6.json', 'v6_nytta'], ['v6.1', 'forregistrering-v61.json', 'v61']]) {
  const fp = path.join(P, fil); if (!fs.existsSync(fp)) continue
  const L = las(fp).prognos, val = r => L[r.konto].find(x => x.id === r.id)?.[falt]
  const m = rader.filter(r => Number.isFinite(val(r))), q = perm(m.map(val), m.map(r => r.agare))
  let ra = 0, fe = 0
  for (const id of R.delade) { const x = m.filter(r => r.id === id); for (let i = 0; i < x.length; i++) for (let j = i + 1; j < x.length; j++) { if (x[i].agare === x[j].agare) continue; const s = Math.sign(x[i].agare - x[j].agare) * Math.sign(val(x[i]) - val(x[j])); if (s > 0) ra++; else if (s < 0) fe++ } }
  console.log(`${namn}: rho ${q.rho.toFixed(2)}, p ${q.p.toFixed(4)}; inom delade klipp ${ra} rätt, ${fe} fel`)
}
