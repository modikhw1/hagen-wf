// Analys av pass 7 enligt data/format/harness/pass7/forregistrering.json.
// Ägarens val kodas i data/format/harness/pass7/agare.json: { "val": { "<nr>": "v" | "h" }, "skal": { "<nr>": "..." } }
//   node format/h-pass7-analys.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const P = path.join(DATA, 'format', 'harness', 'pass7'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const R = las(path.join(P, 'forregistrering.json')), A = las(path.join(P, 'agare.json'))
const binom = (k, n) => { let s = 0; for (let i = k; i <= n; i++) { let c = 1; for (let j = 0; j < i; j++) c = c * (n - j) / (j + 1); s += c / 2 ** n } return s }
const r = R.par.filter(p => A.val?.[p.nr]).map(p => { const val = A.val[p.nr] === 'v' ? p.vanster : p.hoger, annat = A.val[p.nr] === 'v' ? p.hoger : p.vanster; return { ...p, grund: Math.sign(val.grund - annat.grund), nytta: Math.sign(val.nytta6 - annat.nytta6) } })
const g = r.filter(x => x.grund > 0).length, gn = r.filter(x => x.grund !== 0).length
console.log(`HP7a ägaren följer grundvärdet i ${g} av ${gn} par, p ${binom(g, gn).toFixed(4)}`)
const is = r.filter(x => x.typ === 'isar'); console.log(`HP7b isär-par: följer grundvärdet ${is.filter(x => x.grund > 0).length}, följer nyttan ${is.filter(x => x.nytta > 0).length} av ${is.length}`)
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(x => [`${x.konto}-${x.id}`, x]))
const rv = id => bas.get(id)?.rv
console.log('HP7c isär-par, utfall (rv) för ägarens val mot det andra:')
for (const x of is) { const val = A.val[x.nr] === 'v' ? x.vanster : x.hoger, annat = A.val[x.nr] === 'v' ? x.hoger : x.vanster; console.log(`  par ${x.nr}: valt rv ${rv(val.id)?.toFixed(2)} mot ${rv(annat.id)?.toFixed(2)} (valde ${x.grund > 0 ? 'grundvärdets' : 'nyttans'})`) }
