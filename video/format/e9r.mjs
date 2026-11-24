// E9-R: rutnätets krok på 200 bank2-sketcher (förregistrerat i data/format/e9r/forregistrering.json).
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const F = path.join(DATA, 'format'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const ids = fs.readFileSync(path.join(F, 'e9r', 'ids.txt'), 'utf8').split(/\r?\n/).filter(Boolean)
const k = (d, id) => { const f = path.join(F, d, `${id}.json`); return fs.existsSync(f) ? las(f) : null }
const ex = las(path.join(F, 'bank2', 'extra.json'))
const r = ids.map(id => ({ id, konto: ex.find(x => x.id === id)?.konto, rv: bas.get(id)?.rv, o: k('bank2/kort', id), g: k('e9r/rutnat', id) })).filter(x => x.o && x.g && Number.isFinite(x.rv))
const per = {}; for (const x of r) (per[x.konto] ??= []).push(x)
const gr = Object.values(per).filter(l => l.length >= 3)
let fro = 9; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const st = (fx, ys) => { const rs = []; for (const l of gr) { const x = l.map(fx); if (new Set(x).size > 1) rs.push(spearman(x, l.map(q => ys.get(q.id)))) } return rs.reduce((s, v) => s + v, 0) / rs.length }
const diff = (fa, fb) => { const ys = new Map(r.map(x => [x.id, x.rv])), obs = st(fa, ys) - st(fb, ys); let e = 0; for (let t = 0; t < 2000; t++) { const p = new Map(); for (const l of gr) { const v = l.map(q => q.rv); for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } l.forEach((q, i) => p.set(q.id, v[i])) } if (st(fa, p) - st(fb, p) >= obs) e++ } return { obs, p: (e + 1) / 2001, a: st(fa, ys), b: st(fb, ys) } }
const KROK = { ingen: 0, svag: 1, stark: 2 }
const kombi = x => grund({ ...x.o, grundvarde: { ...x.o.grundvarde, krok: x.g.grundvarde.krok } }).p
console.log(`${r.length} klipp med båda vyerna, ${gr.length} konton`)
const a = diff(x => KROK[x.g.grundvarde.krok], x => KROK[x.o.grundvarde.krok])
console.log(`HE9Ra krok → rv: rutnät ${a.a.toFixed(3)}, original ${a.b.toFixed(3)}, skillnad ${a.obs.toFixed(3)} (p ${a.p.toFixed(3)} för att skillnaden är slump)`)
const b = diff(kombi, x => grund(x.o).p)
console.log(`HE9Rb grund med rutnätets krok ${b.a.toFixed(3)}, grund original ${b.b.toFixed(3)}, skillnad ${b.obs.toFixed(3)} (p ${b.p.toFixed(3)})`)
console.log(`krok lika i original och rutnät: ${Math.round(100 * r.filter(x => x.o.grundvarde.krok === x.g.grundvarde.krok).length / r.length)} %`)
