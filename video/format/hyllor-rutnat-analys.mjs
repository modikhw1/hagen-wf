// Analys av rutnätskorten för mitten och situation (förregistrerat i data/format/hyllor-rutnat/forregistrering.json).
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const F = path.join(DATA, 'format'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const DIRS = ['harness/v5', 'e6/kort', 'e6r/kort', 'bank2/kort', 'bank3/kort'].map(d => path.join(F, d))
const orig = id => { const f = DIRS.map(d => path.join(d, `${id}.json`)).find(fs.existsSync); return f ? las(f) : null }
const G = path.join(F, 'hyllor-rutnat', 'kort')
const r = fs.readdirSync(G).map(f => las(path.join(G, f))).map(g => ({ g, o: orig(g.id), rv: bas.get(g.id)?.rv, konto: g.konto })).filter(x => x.o && Number.isFinite(x.rv))
const KROK = { ingen: 0, svag: 1, stark: 2 }
let fro = 4; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
function diff(rows, fa, fb) {
  const per = {}; for (const x of rows) (per[x.konto] ??= []).push(x); const gr = Object.values(per).filter(l => l.length >= 3)
  const st = (f, ys) => { const rs = []; for (const l of gr) { const x = l.map(f); if (new Set(x).size > 1) rs.push(spearman(x, l.map(q => ys.get(q.g.id)))) } return rs.length ? rs.reduce((s, v) => s + v, 0) / rs.length : NaN }
  const ys = new Map(rows.map(x => [x.g.id, x.rv])), a = st(fa, ys), b = st(fb, ys); let e = 0
  for (let t = 0; t < 2000; t++) { const p = new Map(); for (const l of gr) { const v = l.map(q => q.rv); for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } l.forEach((q, i) => p.set(q.g.id, v[i])) } if (st(fa, p) - st(fb, p) >= a - b) e++ }
  return `${a.toFixed(3)} mot ${b.toFixed(3)} (${gr.length} konton), p ${((e + 1) / 2001).toFixed(3)}`
}
const tt = r.filter(x => x.o.sprak.strategi === 'tilltal')
console.log(`${r.length} klipp med båda vyerna, varav ${tt.length} tilltal`)
console.log(`HG1 tilltal, krok rutnät mot original → rv: ${diff(tt, x => KROK[x.g.grundvarde.krok], x => KROK[x.o.grundvarde.krok])}`)
console.log(`HG2 alla, grund med rutnätets krok mot original → rv: ${diff(r, x => grund({ ...x.o, grundvarde: { ...x.o.grundvarde, krok: x.g.grundvarde.krok } }).p, x => grund(x.o).p)}`)
