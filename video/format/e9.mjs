// E9: original mot 2×2-rutnät (förregistrerat i data/format/e9/forregistrering.json).
//   node format/e9.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const F = path.join(DATA, 'format'), E = path.join(F, 'e9'), H = path.join(F, 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const urval = las(path.join(F, 'e6r', 'urval.json'))
const ids = fs.readFileSync(path.join(E, 'ids.txt'), 'utf8').split(/\r?\n/).filter(Boolean)
const kort = (d, id) => { const f = path.join(E, d, `${id}.json`); return fs.existsSync(f) ? las(f) : null }
const rader = ids.map(id => ({ ...urval.find(k => k.id === id), o: kort(process.env.E9O ?? 'orig', id), r: kort(process.env.E9R ?? 'rutnat', id) })).filter(x => x.o && x.r)
const konton = [...new Set(rader.map(x => x.konto))]
const inom = fx => { const rs = []; for (const k of konton) { const l = rader.filter(x => x.konto === k), x = l.map(fx); if (new Set(x).size > 1) rs.push(spearman(x, l.map(r => r.rv))) } return `${(rs.reduce((s, v) => s + v, 0) / rs.length).toFixed(3)} (${rs.length} konton)` }
const KROK = { ingen: 0, svag: 1, stark: 2 }
console.log(`${rader.length} klipp med båda versionerna, ${konton.length} konton`)
console.log(`HE9a grund → rv: original ${inom(x => grund(x.o).p)}, rutnät ${inom(x => grund(x.r).p)}`)
console.log(`HE9b krok → rv: original ${inom(x => KROK[x.o.grundvarde.krok])}, rutnät ${inom(x => KROK[x.r.grundvarde.krok])}`)
console.log(`HE9c vändning → rv: original ${inom(x => +x.o.grundvarde.vandning)}, rutnät ${inom(x => +x.r.grundvarde.vandning)}`)
const lika = p => rader.filter(x => JSON.stringify(p(x.o)) === JSON.stringify(p(x.r))).length / rader.length
console.log(`överensstämmelse original–rutnät: premiss ${Math.round(100 * lika(c => c.grundvarde.premiss))} %, krok ${Math.round(100 * lika(c => c.grundvarde.krok))} %, vändning ${Math.round(100 * lika(c => c.grundvarde.vandning))} %, hylla ${Math.round(100 * lika(c => c.grundvarde.hylla))} %, tempo ${Math.round(100 * lika(c => c.sprak.tempo))} %`)
// E9b: ägarens klipp.
const U = las(path.join(H, 'validering', 'urval.json')), A = las(path.join(H, 'validering', 'agare.json'))
const par = Object.entries(U).flatMap(([k, { klipp }]) => klipp.filter(c => Number.isFinite(A.klipp[k]?.[c.pos]?.passform)).map(c => ({ id: c.id, y: A.klipp[k][c.pos].passform })))
const g = (d, id) => { const f = path.join(d, `${id}.json`); return fs.existsSync(f) ? grund(las(f)).p : NaN }
const AO = path.join(E, 'agare-orig'), AR = path.join(E, 'agare-rutnat'), m = par.filter(r => Number.isFinite(g(AR, r.id)) && Number.isFinite(g(AO, r.id)))
console.log(`HE9d ägarens passform (${m.length} par): original ${spearman(m.map(r => g(AO, r.id)), m.map(r => r.y)).toFixed(2)}, rutnät ${spearman(m.map(r => g(AR, r.id)), m.map(r => r.y)).toFixed(2)}`)
// Utforskande (efter E9): kombination, kroken ur rutnätet och resten ur originalet.
const kombi = (o, r) => ({ ...o, grundvarde: { ...o.grundvarde, krok: r.grundvarde.krok } })
console.log(`utforskande kombination grund → rv: ${inom(x => grund(kombi(x.o, x.r)).p)}`)
const mk = par.filter(r => Number.isFinite(g(AR, r.id)) && Number.isFinite(g(AO, r.id)))
const kg = id => grund(kombi(las(path.join(AO, `${id}.json`)), las(path.join(AR, `${id}.json`)))).p
console.log(`utforskande kombination mot ägarens passform: ${spearman(mk.map(r => kg(r.id)), mk.map(r => r.y)).toFixed(2)}; medel original+rutnät: ${spearman(mk.map(r => g(AO, r.id) + g(AR, r.id)), mk.map(r => r.y)).toFixed(2)}`)
