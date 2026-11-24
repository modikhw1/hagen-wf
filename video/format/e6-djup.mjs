// E6 fördjupning (utforskande, 4 nov 2026). Samma 299 klipp och utfall som E6.
//  1. Fortsättning i flera dimensioner: samma strategi, kantighet, tempo, person, plattform, klippberoende
//     som kontots vanligaste, och avståndet till kontots mitt.
//  2. Samspel: grundvärde × fortsättning.
//  3. Formulans räckvidd: grundvärde → visningar per sorts konto (kontots vanligaste strategi, kontots storlek).
//  4. Större kluster: principalkomponenter över lagren (bibliotek + E6), mot preferens och nytta.
//   node format/e6-djup.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'

const F = path.join(DATA, 'format'), E = path.join(F, 'e6'), H = path.join(F, 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const urval = las(path.join(E, 'urval.json')).filter(k => fs.existsSync(path.join(E, 'kort', `${k.id}.json`))).map(k => ({ ...k, c: las(path.join(E, 'kort', `${k.id}.json`)) }))
const konton = [...new Set(urval.map(k => k.konto))]
const DIM = { strategi: c => c.sprak.strategi, kantighet: c => c.sprak.kantighet, tempo: c => c.sprak.tempo, person: c => c.sprak.person, plattform: c => c.sprak.plattform, klippberoende: c => c.sprak.klippberoende, funktion: c => c.funktion }
const modal = a => { const r = {}; for (const x of a) r[x] = (r[x] ?? 0) + 1; return Object.entries(r).sort((a, b) => b[1] - a[1])[0][0] }
const per = Object.fromEntries(konton.map(k => { const l = urval.filter(x => x.konto === k); const m = Object.fromEntries(Object.entries(DIM).map(([d, f]) => [d, modal(l.map(x => f(x.c)))])); return [k, l.map(x => ({ rv: x.rv, rl: x.rl, g: grund(x.c).p, same: Object.fromEntries(Object.entries(DIM).map(([d, f]) => [d, f(x.c) === m[d] ? 1 : 0])), c: x.c })).map(r => ({ ...r, avstand: Object.values(r.same).filter(v => !v).length })), m] }).map(([k, l, m]) => [k, { l, m }]))
let fro = 77; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }
const medel = a => a.length ? a.reduce((s, x) => s + x, 0) / a.length : NaN
function inom(fx, fy = r => r.rv, perm = 2000, filt = () => true) {
  const st = data => { const rs = []; for (const { l } of data) { const m = l.filter(filt); const x = m.map(fx), y = m.map(fy); if (m.length < 4 || new Set(x).size < 2) continue; rs.push(spearman(x, y)) } return { r: medel(rs), k: rs.length } }
  const data = Object.values(per), obs = st(data); if (!perm) return obs
  let e = 0; for (let t = 0; t < perm; t++) { const p = data.map(({ l, m }) => { const ys = bl(l.map(fy)); return { m, l: l.map((r, i) => ({ ...r, rv: ys[i], rl: ys[i] })) } }); if (st(p).r >= obs.r) e++ }
  return { ...obs, p: (e + 1) / (perm + 1) }
}
const f = v => Number.isFinite(v) ? (v >= 0 ? '+' : '') + v.toFixed(3) : '–'
const ut = {}
console.log('1. Fortsättning per dimension (samma som kontots vanligaste → visningar, gillanden inom konto)')
ut.fortsattning = {}
for (const d of Object.keys(DIM)) { const a = inom(r => r.same[d], r => r.rv, 0), b = inom(r => r.same[d], r => r.rl, 0); ut.fortsattning[d] = { rv: a, rl: b }; console.log(`  ${d.padEnd(14)} ${f(a.r)} ${f(b.r)} (${a.k} konton)`) }
const av = inom(r => -r.avstand, r => r.rv, 2000); ut.avstand = av
console.log(`  närhet till kontots mitt (antal dimensioner lika) → visningar: ${f(av.r)}, p ${av.p.toFixed(3)} (${av.k})`)

console.log('\n2. Samspel: fortsättning (samma strategi) bland klipp med högt och lågt grundvärde inom konto')
const hogt = r => { return r.ghog }
for (const { l } of Object.values(per)) { const med = [...l.map(r => r.g)].sort((a, b) => a - b)[Math.floor(l.length / 2)]; l.forEach(r => r.ghog = r.g >= med) }
for (const [n, filt] of [['högt grundvärde', r => r.ghog], ['lågt grundvärde', r => !r.ghog]]) { const a = inom(r => r.same.strategi, r => r.rv, 0, filt); ut[`samspel_${n}`] = a; console.log(`  ${n.padEnd(16)} samma strategi → visningar ${f(a.r)} (${a.k} konton)`) }

console.log('\n3. Formulans räckvidd: grundvärde → visningar inom konto, per sorts konto')
const kontoR = Object.entries(per).map(([k, { l, m }]) => ({ k, m, r: new Set(l.map(x => x.g)).size > 1 ? spearman(l.map(x => x.g), l.map(x => x.rv)) : NaN, bas: medel(urval.filter(x => x.konto === k).map(x => bas.get(x.id)?.bas_v).filter(Number.isFinite)) })).filter(x => Number.isFinite(x.r))
ut.rackvidd = {}
for (const s of [...new Set(kontoR.map(x => x.m.strategi))]) { const x = kontoR.filter(y => y.m.strategi === s); ut.rackvidd[s] = { r: medel(x.map(y => y.r)), n: x.length }; console.log(`  konton med strategi ${s.padEnd(16)} ${f(medel(x.map(y => y.r)))} (${x.length} konton)`) }
const medBas = [...kontoR.map(x => x.bas)].sort((a, b) => a - b)[Math.floor(kontoR.length / 2)]
for (const [n, filt] of [['små konton', x => x.bas < medBas], ['stora konton', x => x.bas >= medBas]]) { const x = kontoR.filter(filt); ut.rackvidd[n] = { r: medel(x.map(y => y.r)), n: x.length }; console.log(`  ${n.padEnd(30)} ${f(medel(x.map(y => y.r)))} (${x.length} konton)`) }
console.log(`  kontots grundvärde-nivå mot hur väl formeln fungerar där: rho ${spearman(kontoR.map(x => medel(per[x.k].l.map(y => y.g))), kontoR.map(x => x.r)).toFixed(2)}`)

// 4. Principalkomponenter över lagren.
const ORD = { premiss: c => ({ ingen: 0, svag: 1, medel: 2, stark: 3 })[c.grundvarde.premiss], utan_efterarbete: c => ({ nej: 0, delvis: 1, ja: 2 })[c.grundvarde.utan_efterarbete], krok: c => ({ ingen: 0, svag: 1, stark: 2 })[c.grundvarde.krok], vandning: c => +c.grundvarde.vandning, hojer_taket: c => +c.grundvarde.hojer_taket, kantighet: c => ({ familjar: 0, lekfull: 1, kantig: 2, vuxen: 3 })[c.sprak.kantighet], tempo: c => ({ lugnt: 0, medel: 1, hogt: 2 })[c.sprak.tempo], klippberoende: c => ({ lite: 0, en_del: 1, mycket: 2 })[c.sprak.klippberoende], bundna_bilder: c => ({ fa: 0, halften: 1, nastan_alla: 2 })[c.forlaga.bundna_bilder], sketch: c => +(c.sprak.strategi === 'sketchvarld'), tilltal: c => +(c.sprak.strategi === 'tilltal' || c.sprak.tilltal === 'till_kamera'), visning: c => +(c.sprak.strategi === 'visning'), karisma: c => +(c.grundvarde.bars_av === 'karisma' || c.sprak.person === 'fokus'), roll: c => +(c.sprak.person === 'roll'), ingen_person: c => +(c.sprak.person === 'ingen'), instagram: c => +(c.sprak.plattform !== 'tiktok'), skadespel: c => c.krav.skadespel, produktion: c => c.krav.produktion, personer: c => c.krav.personer_min, kott: c => +(c.funktion === 'kott'), stod: c => +(c.funktion === 'stod') }
const alla = [...fs.readdirSync(path.join(H, 'v5')).map(f => las(path.join(H, 'v5', f))), ...urval.map(x => x.c)]
const N = Object.keys(ORD), X = alla.map(c => N.map(n => ORD[n](c) ?? 0))
const mu = N.map((_, j) => medel(X.map(r => r[j]))), sd = N.map((_, j) => Math.sqrt(medel(X.map(r => (r[j] - mu[j]) ** 2))) || 1)
const Z = X.map(r => r.map((v, j) => (v - mu[j]) / sd[j]))
const C = N.map((_, i) => N.map((_, j) => medel(Z.map(r => r[i] * r[j]))))
const komp = []; let M = C.map(r => [...r])
for (let k = 0; k < 4; k++) { let v = N.map(() => Math.random()); for (let it = 0; it < 300; it++) { const w = M.map(r => r.reduce((s, x, j) => s + x * v[j], 0)); const nrm = Math.hypot(...w); v = w.map(x => x / nrm) } const lam = v.reduce((s, x, i) => s + x * M[i].reduce((t, y, j) => t + y * v[j], 0), 0); komp.push({ lam, v }); M = M.map((r, i) => r.map((x, j) => x - lam * v[i] * v[j])) }
const tot = N.length
console.log('\n4. Principalkomponenter (bibliotek + E6, ' + alla.length + ' klipp)')
const poang = (c, k) => N.reduce((s, n, j) => s + ((ORD[n](c) ?? 0) - mu[j]) / sd[j] * komp[k].v[j], 0)
const U = las(path.join(H, 'validering', 'urval.json')), A = las(path.join(H, 'validering', 'agare.json'))
const par = Object.entries(U).flatMap(([k, { klipp }]) => klipp.filter(c => Number.isFinite(A.klipp[k]?.[c.pos]?.passform)).map(c => ({ c: las(path.join(H, 'v5', `${c.id}.json`)), y: A.klipp[k][c.pos].passform })))
ut.komponenter = []
komp.forEach((k, i) => {
  const topp = N.map((n, j) => [n, k.v[j]]).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 6).map(([n, v]) => `${n} ${v >= 0 ? '+' : ''}${v.toFixed(2)}`)
  const pref = spearman(par.map(r => poang(r.c, i)), par.map(r => r.y)), nyt = inom(r => poang(r.c, i), r => r.rv, 0)
  ut.komponenter.push({ andel: k.lam / tot, laddningar: Object.fromEntries(N.map((n, j) => [n, k.v[j]])), preferens: pref, nytta: nyt.r })
  console.log(`  K${i + 1} (${Math.round(100 * k.lam / tot)} % av variansen): ${topp.join(', ')}\n     preferens (passform) ${f(pref)}, nytta (visningar inom konto) ${f(nyt.r)}`)
})
fs.writeFileSync(path.join(E, 'djup.json'), JSON.stringify(ut, null, 1))
