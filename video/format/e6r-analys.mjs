// E6-R: replikering på 30 nya konton (förregistrerat i data/format/e6r/forregistrering.json).
//   node format/e6r-analys.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const F = path.join(DATA, 'format'), E = path.join(F, 'e6r'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const Q = fs.existsSync(path.join(F, 'e7', 'e6r.json')) ? las(path.join(F, 'e7', 'e6r.json')) : {}
const D = las(path.join(F, 'e6', 'djup.json')).komponenter
const urval = las(path.join(E, 'urval.json')).filter(k => fs.existsSync(path.join(E, 'kort', `${k.id}.json`))).map(k => ({ ...k, c: las(path.join(E, 'kort', `${k.id}.json`)) }))
const ORD = { premiss: c => ({ ingen: 0, svag: 1, medel: 2, stark: 3 })[c.grundvarde.premiss], utan_efterarbete: c => ({ nej: 0, delvis: 1, ja: 2 })[c.grundvarde.utan_efterarbete], krok: c => ({ ingen: 0, svag: 1, stark: 2 })[c.grundvarde.krok], vandning: c => +c.grundvarde.vandning, hojer_taket: c => +c.grundvarde.hojer_taket, kantighet: c => ({ familjar: 0, lekfull: 1, kantig: 2, vuxen: 3 })[c.sprak.kantighet], tempo: c => ({ lugnt: 0, medel: 1, hogt: 2 })[c.sprak.tempo], klippberoende: c => ({ lite: 0, en_del: 1, mycket: 2 })[c.sprak.klippberoende], bundna_bilder: c => ({ fa: 0, halften: 1, nastan_alla: 2 })[c.forlaga.bundna_bilder], sketch: c => +(c.sprak.strategi === 'sketchvarld'), tilltal: c => +(c.sprak.strategi === 'tilltal' || c.sprak.tilltal === 'till_kamera'), visning: c => +(c.sprak.strategi === 'visning'), karisma: c => +(c.grundvarde.bars_av === 'karisma' || c.sprak.person === 'fokus'), roll: c => +(c.sprak.person === 'roll'), ingen_person: c => +(c.sprak.person === 'ingen'), instagram: c => +(c.sprak.plattform !== 'tiktok'), skadespel: c => c.krav.skadespel, produktion: c => c.krav.produktion, personer: c => c.krav.personer_min, kott: c => +(c.funktion === 'kott'), stod: c => +(c.funktion === 'stod') }
const N = Object.keys(ORD), X = urval.map(x => N.map(n => ORD[n](x.c) ?? 0))
const mu = N.map((_, j) => X.reduce((s, r) => s + r[j], 0) / X.length), sd = N.map((_, j) => Math.sqrt(X.reduce((s, r) => s + (r[j] - mu[j]) ** 2, 0) / X.length) || 1)
const K = (i, r) => N.reduce((s, n, j) => s + (r[j] - mu[j]) / sd[j] * D[i].laddningar[n], 0)
urval.forEach((x, i) => { x.k1 = K(0, X[i]); x.k2 = K(1, X[i]); x.g = grund(x.c).p; x.q = Q[x.id]?.varde })
const konton = [...new Set(urval.map(k => k.konto))]
const modal = a => { const r = {}; for (const x of a) r[x] = (r[x] ?? 0) + 1; return Object.entries(r).sort((a, b) => b[1] - a[1])[0][0] }
for (const k of konton) { const l = urval.filter(x => x.konto === k), ms = modal(l.map(x => x.c.sprak.strategi)), mp = modal(l.map(x => x.c.sprak.person)); l.forEach(x => { x.samStrat = +(x.c.sprak.strategi === ms); x.samPers = +(x.c.sprak.person === mp); x.kontoStrat = ms }) }
let fro = 99; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
function inom(fx, riktning = 1, filt = () => true) {
  const st = ys => { const rs = []; for (const k of konton) { const l = urval.filter(x => x.konto === k && filt(x)), x = l.map(fx); if (l.length < 4 || new Set(x).size < 2 || x.some(v => !Number.isFinite(v))) continue; rs.push(spearman(x, l.map(r => ys.get(r.id)))) } return { r: rs.reduce((s, v) => s + v, 0) / rs.length, k: rs.length } }
  const ys = new Map(urval.map(r => [r.id, r.rv])), obs = st(ys); let e = 0
  for (let t = 0; t < 3000; t++) { const p = new Map(); for (const k of konton) { const l = urval.filter(x => x.konto === k), v = l.map(r => r.rv); for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } l.forEach((r, i) => p.set(r.id, v[i])) } if (riktning * st(p).r >= riktning * obs.r) e++ }
  return { ...obs, p: (e + 1) / 3001 }
}
const f = v => (v >= 0 ? '+' : '') + v.toFixed(3)
console.log(`${urval.length} kort från ${konton.length} konton, ${urval.filter(x => Number.isFinite(x.q)).length} med E7-fråga`)
const h1 = inom(x => x.g), h2 = inom(x => x.q), h3 = inom(x => x.samStrat, -1), h4 = inom(x => x.samPers), h5a = inom(x => x.k1), h5b = inom(x => x.k2), h7 = inom(x => +x.c.grundvarde.hojer_taket)
console.log(`HR1 grund → rv: ${f(h1.r)} (${h1.k}), p ${h1.p.toFixed(4)}`)
console.log(`HR2 E7-frågan → rv: ${f(h2.r)} (${h2.k}), p ${h2.p.toFixed(4)}; minst lika stark som grund: ${h2.r >= h1.r ? 'ja' : 'nej'}`)
console.log(`HR3 samma strategi → rv (nedåt): ${f(h3.r)} (${h3.k}), p ${h3.p.toFixed(4)}`)
console.log(`HR4 samma personnärvaro → rv: ${f(h4.r)} (${h4.k}), p ${h4.p.toFixed(4)}`)
console.log(`HR5 K1 → rv: ${f(h5a.r)}, p ${h5a.p.toFixed(4)}; K2 → rv: ${f(h5b.r)} (|rho| < 0,05: ${Math.abs(h5b.r) < 0.05 ? 'ja' : 'nej'})`)
for (const s of [...new Set(urval.map(x => x.kontoStrat))]) { const r = inom(x => x.g, 1, x => x.kontoStrat === s); console.log(`HR6 grund → rv i konton med strategi ${s}: ${Number.isFinite(r.r) ? f(r.r) : '–'} (${r.k} konton)`) }
console.log(`HR7 höjer taket → rv: ${f(h7.r)} (${h7.k}), p ${h7.p.toFixed(4)}`)
const h8 = inom(x => +(x.c.krav.ljud === 'eget_tal')), h9 = inom(x => +(x.c.krav.ljud === 'trendljud'), -1)
console.log(`HR8 eget tal → rv: ${f(h8.r)} (${h8.k}), p ${h8.p.toFixed(4)}`)
console.log(`HR9 trendljud → rv (nedåt): ${f(h9.r)} (${h9.k}), p ${h9.p.toFixed(4)}`)
