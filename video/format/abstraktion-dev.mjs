// Utveckling: abstraktionslagret mot ägaren (biblioteksbeslut 1–27, passform pass 4–5). Inte ett test:
// lagret upptäcktes i residualerna på samma klipp.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const H = path.join(DATA, 'format', 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const AB = las(path.join(H, 'abstraktion.json')), V5 = id => las(path.join(H, 'v5', `${id}.json`))
const bib = las(path.join(H, 'urval.json')).bibliotek, kalib = las(path.join(DATA, 'format', 'kalib', 'agare.json')).klipp
const U = las(path.join(H, 'validering', 'urval.json')), A = las(path.join(H, 'validering', 'agare.json'))
const AV = { ide: 2, form: 1, ingen: 0 }
// grund2: idé bedöms på premissen som förut; form får ett fast mittenvärde (villkorat); ingen får golvet.
export const grund2 = (c, ab) => ab?.abstraktion === 'form' ? 1.5 : ab?.abstraktion === 'ingen' ? Math.min(grund(c).p, 0) : grund(c).p
const bes = bib.filter(k => k.kalla === 'kalib' && kalib[k.nr]?.bibliotek).map(k => ({ id: k.id, nr: k.nr, y: { ja: 2, villkorat: 1, nej: 0 }[kalib[k.nr].bibliotek] }))
const par = Object.entries(U).flatMap(([k, { klipp }]) => klipp.filter(c => Number.isFinite(A.klipp[k]?.[c.pos]?.passform)).map(c => ({ id: c.id, y: A.klipp[k][c.pos].passform })))
for (const [n, f] of [['grund (v5)', id => grund(V5(id)).p], ['abstraktion', id => AV[AB[id]?.abstraktion]], ['grund2', id => grund2(V5(id), AB[id])]])
  console.log(n.padEnd(14), 'bibliotek', spearman(bes.map(r => f(r.id)), bes.map(r => r.y)).toFixed(2), ' passform', spearman(par.map(r => f(r.id)), par.map(r => r.y)).toFixed(2))
console.log('\nkorstabell ägarens bibliotek × abstraktion (klipp 1–27)')
for (const y of [2, 1, 0]) console.log(['nej', 'villkorat', 'ja'][y].padEnd(10), ['ide', 'form', 'ingen'].map(a => `${a} ${bes.filter(r => r.y === y && AB[r.id]?.abstraktion === a).map(r => r.nr).join(',') || '-'}`).join(' | '))
