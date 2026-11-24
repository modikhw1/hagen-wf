// E20: tjänstemötet som röd tråd. HE20a–d på replikeringsklippen (E19), samma tal för biblioteket, HE20e mot pass 7.
//   node format/e17-underlag.mjs mekanism-3.8-flash && node format/e20-analys.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const R0 = fs.readFileSync(path.join(DATA, 'format', 'e15', 'motorer-flash.jsonl'), 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l))
const L = path.join(DATA, 'format', 'e20', 'lasning'), NYA = new Set(las(path.join(DATA, 'format', 'e19', 'ids.json')))
const R = R0.map(r => { const f = path.join(L, `${r.id}.json`); return fs.existsSync(f) ? { ...r, ...las(f), ny: NYA.has(r.id) } : null }).filter(r => r && r.u !== null)
const medel = x => x.reduce((s, v) => s + v, 0) / x.length

// Skillnad i utfall inom konto mellan grupp A och B, med permutation av grupptillhörighet inom konto.
function prov(namn, rader, iA, iB, N = 5000) {
  const X = rader.filter(r => iA(r) || iB(r)), kon = [...new Set(X.map(r => r.konto))]
  const m = Object.fromEntries(kon.map(k => [k, medel(rader.filter(r => r.konto === k).map(r => r.u))]))  // kontots medel över ALLA dess klipp
  const y = X.map(r => r.u - m[r.konto]), a = X.map(iA), nA = a.filter(Boolean).length, nB = a.length - nA
  if (nA < 8 || nB < 8) return console.log(`  ${namn.padEnd(46)} för få (${nA} mot ${nB})`)
  const diff = g => { let sa = 0, sb = 0, na = 0; g.forEach((v, i) => { if (v) { sa += y[i]; na++ } else sb += y[i] }); return sa / na - sb / (g.length - na) }
  const d0 = diff(a); let fler = 0; const idx = kon.map(k => X.map((r, i) => r.konto === k ? i : -1).filter(i => i >= 0))
  for (let n = 0; n < N; n++) { const g = [...a]; for (const I of idx) { for (let j = I.length - 1; j > 0; j--) { const q = Math.floor(Math.random() * (j + 1)); const t = g[I[j]]; g[I[j]] = g[I[q]]; g[I[q]] = t } } if (diff(g) >= d0) fler++ }
  console.log(`  ${namn.padEnd(46)} n ${String(nA).padStart(4)} mot ${String(nB).padStart(4)}  skillnad ${d0 >= 0 ? '+' : ''}${d0.toFixed(3)} (×${Math.exp(d0).toFixed(2)})  p ${((fler + 1) / (N + 1)).toFixed(4)}`)
}
function allt(titel, rader) {
  console.log(`\n${titel}: ${rader.length} klipp, ${new Set(rader.map(r => r.konto)).size} konton`)
  for (const f of ['relation', 'friktion', 'insats', 'sida']) { const m = Object.fromEntries([...new Set(rader.map(r => r.konto))].map(k => [k, medel(rader.filter(r => r.konto === k).map(r => r.u))])); const g = {}; for (const r of rader) (g[r[f]] ??= []).push(r.u - m[r.konto]); console.log(`  ${f}: ${Object.entries(g).sort((a, b) => medel(b[1]) - medel(a[1])).map(([k, v]) => `${k} ${medel(v) >= 0 ? '+' : ''}${medel(v).toFixed(2)} (n ${v.length})`).join('  ')}`) }
  const gp = r => r.relation === 'gast_personal', ap = r => r.relation === 'avsandare_publik' || r.relation === 'ingen'
  prov('HE20a gäst–personal mot tilltal/ingen', rader, gp, ap)
  prov('HE20a utan klipp där insatsen är pengar', rader.filter(r => r.insats !== 'pengar'), gp, ap)
  prov('HE20b tydlig friktion mot ingen', rader, r => r.friktion === 'tydlig', r => r.friktion === 'ingen')
  prov('HE20c gäst–personal mot personal–personal', rader, gp, r => r.relation === 'personal_personal')
  prov('HE20d gästens/personalens sida mot verksamhetens', rader, r => r.sida !== 'verksamhetens', r => r.sida === 'verksamhetens')
  prov('     friktion inom tilltal (tydlig/mild mot ingen)', rader.filter(r => r.relation === 'avsandare_publik'), r => r.friktion !== 'ingen', r => r.friktion === 'ingen')
}
allt('REPLIKERING (E19, osedda klipp) – provet', R.filter(r => r.ny))
allt('Biblioteket och E13-klippen – där mönstret syntes, inget prov', R.filter(r => !r.ny))

// HE20e: pass 7
const P = las(path.join(DATA, 'format', 'harness', 'pass7', 'forregistrering.json')).par, A = las(path.join(DATA, 'format', 'harness', 'pass7', 'agare.json'))
const lf = id => { const f = path.join(L, `${id}.json`); return fs.existsSync(f) ? las(f) : null }, FR = { ingen: 0, mild: 1, tydlig: 2 }
let fh = 0, fl = 0, fs_ = 0, gv = 0, gb = 0
for (const p of P) { const val = A.val[p.nr], v = lf(p.vanster.id), h = lf(p.hoger.id); if (!val || !v || !h) continue; const [vald, annan] = val === 'v' ? [v, h] : [h, v]
  if (FR[vald.friktion] > FR[annan.friktion]) fh++; else if (FR[vald.friktion] < FR[annan.friktion]) fl++; else fs_++
  if ((vald.relation === 'gast_personal') !== (annan.relation === 'gast_personal')) { if (vald.relation === 'gast_personal') gv++; else gb++ } }
console.log(`\nHE20e, pass 7 (avläsning): ägarens val har högre friktion i ${fh} par, lägre i ${fl}, lika i ${fs_}. Där bara det ena klippet är gäst–personal valde ägaren det i ${gv} av ${gv + gb} par.`)
