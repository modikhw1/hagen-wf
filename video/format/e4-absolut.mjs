// Utforskande tillägg till E4 (inte förregistrerat): rl, rc och rs är andelar per visning. Den
// absoluta mängden gillanden, kommentarer och delningar mot kontots norm är ungefär rv + rl, rv + rc
// och rv + rs. Samma test inom konto som i e4-analys.mjs, med 1000 permutationer.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
const E4 = path.join(DATA, 'format', 'e4'), dir = path.join(E4, 'lager-gemini-3.1-flash-lite')
const urval = new Map(JSON.parse(fs.readFileSync(path.join(E4, 'urval.json'), 'utf8')).map(k => [k.id, k]))
const tal = v => typeof v === 'boolean' ? (v ? 1 : 0) : v
const rader = fs.readdirSync(dir).map(f => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'))).map(x => ({ ...x, ...urval.get(x.id) })).filter(r => Number.isFinite(r.rv))
for (const r of rader) { r.abs_l = r.rv + r.rl; r.abs_c = r.rv + r.rc; r.abs_s = r.rv + r.rs }
const per = new Map(); for (const r of rader) { const l = per.get(r.konto) ?? []; l.push(r); per.set(r.konto, l) }
const konton = [...per.values()].filter(l => l.length >= 8)
let fro = 11; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }
const medel = a => a.reduce((s, v) => s + v, 0) / a.length
function test(n, u) {
  const p = konton.map(l => ({ x: l.map(r => tal(r[n])), y: l.map(r => r[u]) })).map(o => ({ ...o, rho: spearman(o.x, o.y) })).filter(o => Number.isFinite(o.rho))
  const e = medel(p.map(o => o.rho)); let ext = 0
  for (let t = 0; t < 1000; t++) if (Math.abs(medel(p.map(o => { const r = spearman(bl(o.x), o.y); return Number.isFinite(r) ? r : 0 }))) >= Math.abs(e)) ext++
  return { e, p: (ext + 1) / 1001 }
}
const LAGER = ['tavling', 'uppmaning', 'erbjudande', 'handelse', 'roll', 'humor', 'dialog', 'vandning', 'sjalvironi', 'andel_person', 'fristaende_ide', 'tilltal', 'montage', 'trendljud', 'mat_andel']
const f = x => (x >= 0 ? ' ' : '') + x.toFixed(2)
console.log('lager            | räckvidd | gillanden abs (per visning) | kommentarer abs (per visning) | delningar abs (per visning)')
for (const n of LAGER) {
  const t = ['rv', 'abs_l', 'rl', 'abs_c', 'rc', 'abs_s', 'rs'].map(u => test(n, u))
  const s = o => f(o.e) + (o.p < 0.01 ? '**' : o.p < 0.05 ? '* ' : '  ')
  console.log(`${n.padEnd(16)} | ${s(t[0])}  | ${s(t[1])} (${s(t[2])})          | ${s(t[3])} (${s(t[4])})           | ${s(t[5])} (${s(t[6])})`)
}
