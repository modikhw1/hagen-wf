// E7-analys: en enda fråga mot grund() på preferens (ägaren) och nytta (E6, inom konto).
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const Q = { ...las(path.join(F, 'e7', 'bibliotek.json')), ...(fs.existsSync(path.join(F, 'e7', 'e6.json')) ? las(path.join(F, 'e7', 'e6.json')) : {}) }
const U = las(path.join(H, 'validering', 'urval.json')), A = las(path.join(H, 'validering', 'agare.json'))
const bib = las(path.join(H, 'urval.json')).bibliotek, kalib = las(path.join(F, 'kalib', 'agare.json')).klipp
const v5 = id => las(path.join(H, 'v5', `${id}.json`))
const par = Object.entries(U).flatMap(([k, { klipp }]) => klipp.filter(c => Number.isFinite(A.klipp[k]?.[c.pos]?.passform)).map(c => ({ id: c.id, y: A.klipp[k][c.pos].passform })))
const bes = bib.filter(k => k.kalla === 'kalib' && kalib[k.nr]?.bibliotek).map(k => ({ id: k.id, y: { ja: 2, villkorat: 1, nej: 0 }[kalib[k.nr].bibliotek] }))
const rang = a => { const s = a.map((v, i) => [v, i]).sort((x, y) => x[0] - y[0]), r = []; let i = 0; while (i < s.length) { let j = i; while (j + 1 < s.length && s[j + 1][0] === s[i][0]) j++; for (let k = i; k <= j; k++) r[s[k][1]] = (i + j) / 2 / (a.length - 1); i = j + 1 } return r }
for (const [n, d] of [['passform (35)', par], ['bibliotek (25)', bes]]) {
  const g = d.map(r => grund(v5(r.id)).p), q = d.map(r => Q[r.id]?.varde), rg = rang(g), rq = rang(q)
  console.log(`${n}: grund ${spearman(g, d.map(r => r.y)).toFixed(2)}, en fråga ${spearman(q, d.map(r => r.y)).toFixed(2)}, medel ${spearman(rg.map((x, i) => x + rq[i]), d.map(r => r.y)).toFixed(2)}`)
}
const E = path.join(F, 'e6'), urval = las(path.join(E, 'urval.json')).filter(k => Q[k.id] && fs.existsSync(path.join(E, 'kort', `${k.id}.json`)))
const konton = [...new Set(urval.map(k => k.konto))]
let fro = 7; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
function inom(fx) {
  const st = ys => { const rs = []; for (const k of konton) { const l = urval.filter(x => x.konto === k), x = l.map(fx), y = l.map(r => ys.get(r.id)); if (new Set(x).size > 1) rs.push(spearman(x, y)) } return rs.reduce((s, v) => s + v, 0) / rs.length }
  const ys = new Map(urval.map(r => [r.id, r.rv])), obs = st(ys); let e = 0
  for (let t = 0; t < 3000; t++) { const p = new Map(); for (const k of konton) { const l = urval.filter(x => x.konto === k), v = l.map(r => r.rv); for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } l.forEach((r, i) => p.set(r.id, v[i])) } if (st(p) >= obs) e++ }
  return { r: obs, p: (e + 1) / 3001 }
}
const kort = id => las(path.join(E, 'kort', `${id}.json`))
const gmap = new Map(urval.map(r => [r.id, grund(kort(r.id)).p]))
const rg = new Map(), rq = new Map()
for (const k of konton) { const l = urval.filter(x => x.konto === k); const a = rang(l.map(r => gmap.get(r.id))), b = rang(l.map(r => Q[r.id].varde)); l.forEach((r, i) => { rg.set(r.id, a[i]); rq.set(r.id, b[i]) }) }
const ng = inom(r => gmap.get(r.id)), nq = inom(r => Q[r.id].varde), nm = inom(r => rg.get(r.id) + rq.get(r.id))
console.log(`nytta, visningar inom konto (${urval.length} klipp, ${konton.length} konton): grund ${ng.r.toFixed(3)} (p ${ng.p.toFixed(4)}), en fråga ${nq.r.toFixed(3)} (p ${nq.p.toFixed(4)}), medel ${nm.r.toFixed(3)} (p ${nm.p.toFixed(4)})`)
