// E5 utforskande: hjälper ett medel av flera körningar/modeller (självkonsistens)?
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const dirs = { 'flash38-kort': path.join(DATA, 'e5', 'flash38-kort'), 'flash38-kort-b': path.join(DATA, 'e5', 'flash38-kort-b'), 'argon-kort': path.join(DATA, 'e5', 'argon-kort'), pro: path.join(H, 'v5'), 'pro-b': path.join(DATA, 'e5', 'pro-b'), argon: path.join(DATA, 'e5', 'argon'), flash38: path.join(DATA, 'e5', 'flash38'), 'pro-neutral': path.join(DATA, 'e5', 'pro-neutral') }
const g = (v, id) => { const f = path.join(dirs[v], `${id}.json`); return fs.existsSync(f) ? grund(las(f)).p : NaN }
const U = las(path.join(H, 'validering', 'urval.json')), A = las(path.join(H, 'validering', 'agare.json'))
const bib = las(path.join(H, 'urval.json')).bibliotek, kalib = las(path.join(F, 'kalib', 'agare.json')).klipp
const par = Object.entries(U).flatMap(([k, { klipp }]) => klipp.filter(c => Number.isFinite(A.klipp[k]?.[c.pos]?.passform)).map(c => ({ id: c.id, y: A.klipp[k][c.pos].passform })))
const bes = bib.filter(k => k.kalla === 'kalib' && kalib[k.nr]?.bibliotek).map(k => ({ id: k.id, y: { ja: 2, villkorat: 1, nej: 0 }[kalib[k.nr].bibliotek] }))
const kombi = { 'flash38-kort + flash38-kort-b': ['flash38-kort', 'flash38-kort-b'], 'flash38-kort + argon-kort': ['flash38-kort', 'argon-kort'], 'tre korta': ['flash38-kort', 'flash38-kort-b', 'argon-kort'], 'pro': ['pro'], 'pro + pro-b': ['pro', 'pro-b'], 'pro + argon': ['pro', 'argon'], 'pro + flash38': ['pro', 'flash38'], 'pro + pro-b + argon + flash38': ['pro', 'pro-b', 'argon', 'flash38'], 'argon + flash38': ['argon', 'flash38'] }
for (const [n, vs] of Object.entries(kombi)) {
  const f = id => vs.map(v => g(v, id)).reduce((s, x) => s + x, 0) / vs.length
  console.log(n.padEnd(32), 'passform', spearman(par.map(r => f(r.id)), par.map(r => r.y)).toFixed(2), ' bibliotek', spearman(bes.map(r => f(r.id)), bes.map(r => r.y)).toFixed(2))
}
