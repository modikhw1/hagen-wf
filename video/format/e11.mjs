// E11: klipptyp mot utfall i hela banken (förregistrerat i data/format/e11/forregistrering.json). Inga anrop.
//   node format/e11.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
const S = path.join(DATA, 'bank', 'sallning'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const anv = new Set(['harness/v5', 'e6/kort', 'e6r/kort'].flatMap(d => fs.readdirSync(path.join(DATA, 'format', d)).map(f => f.replace(/\.json$/, ''))))
const alla = fs.readdirSync(S).map(f => las(path.join(S, f))).filter(k => Number.isFinite(bas.get(k.id)?.rv)).map(k => ({ ...k, rv: bas.get(k.id).rv }))
const modal = a => { const r = {}; for (const x of a) r[x] = (r[x] ?? 0) + 1; return Object.entries(r).sort((a, b) => b[1] - a[1])[0][0] }
function kor(data, namn) {
  const per = {}; for (const k of data) (per[k.konto] ??= []).push(k)
  const grupper = Object.values(per).filter(l => l.length >= 20)
  for (const l of grupper) { const m = modal(l.map(x => x.typ)); l.forEach(x => { x.kontotyp = m; x.sam = +(x.typ === m) }) }
  let fro = 11; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
  const st = (fx, ys, filt = () => true) => { const rs = []; for (const l of grupper.filter(l => filt(l[0]))) { const x = l.map(fx); if (new Set(x).size < 2) continue; rs.push(spearman(x, l.map(r => ys.get(r.id)))) } return { r: rs.reduce((s, v) => s + v, 0) / rs.length, k: rs.length } }
  const ys = new Map(grupper.flat().map(r => [r.id, r.rv]))
  const test = (fx, riktning = 1, filt) => { const obs = st(fx, ys, filt); let e = 0; for (let t = 0; t < 2000; t++) { const p = new Map(); for (const l of grupper) { const v = l.map(r => r.rv); for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } l.forEach((r, i) => p.set(r.id, v[i])) } if (riktning * st(fx, p, filt).r >= riktning * obs.r) e++ } return { ...obs, p: (e + 1) / 2001 } }
  const f = x => `${(x.r >= 0 ? '+' : '') + x.r.toFixed(3)} (${x.k} konton)${x.p !== undefined ? `, p ${x.p.toFixed(4)}` : ''}`
  console.log(`\n${namn}: ${grupper.flat().length} klipp, ${grupper.length} konton`)
  console.log(`  HE11a relaterbar_sketch → rv: ${f(test(x => +(x.typ === 'relaterbar_sketch')))}`)
  console.log(`  HE11b matporr_och_process → rv (nedåt): ${f(test(x => +(x.typ === 'matporr_och_process'), -1))}`)
  console.log(`  HE11c direkt_tilltal → rv: ${f(test(x => +(x.typ === 'direkt_tilltal')))}`)
  console.log(`  vardens_provsmakning → rv: ${f(st(x => +(x.typ === 'vardens_provsmakning'), ys))}`)
  for (const kt of ['matporr_och_process', 'relaterbar_sketch', 'direkt_tilltal']) console.log(`  HE11d sketch → rv i konton där ${kt} är vanligast: ${f(st(x => +(x.typ === 'relaterbar_sketch'), ys, k => k.kontotyp === kt))}`)
  for (const kt of ['matporr_och_process', 'relaterbar_sketch', 'direkt_tilltal']) console.log(`        tilltal → rv i konton där ${kt} är vanligast: ${f(st(x => +(x.typ === 'direkt_tilltal'), ys, k => k.kontotyp === kt))}`)
  console.log(`  HE11e kontots vanligaste typ → rv (nedåt): ${f(test(x => x.sam, -1))}`)
  console.log(`  rekonbar → rv: ${f(st(x => x.rekonbar ?? 0, ys))}, andel med person → rv: ${f(st(x => x.andel_med_person ?? 0, ys))}, montage → rv: ${f(st(x => +!!x.montage, ys))}`)
}
kor(alla, 'Alla sållade klipp med utfall')
kor(alla.filter(k => !anv.has(k.id)), 'Utan klipp som ingått i v5-körningar')
