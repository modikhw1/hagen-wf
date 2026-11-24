// Utforskande (4 nov 2026), E6 + E6-R (597 klipp, 60 konton), inom konto:
//  1. Portföljen: grundvärdet, kött, stöd, kampanj, tilltal och eget tal mot visningar, gillanden, kommentarer, delningar.
//  2. Tiden: grundvärdet → visningar i kontots äldre och nyare hälft av klippen.
//   node format/e6-portfolj.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
import { nytta6 } from './h-v6.mjs'
const F = path.join(DATA, 'format'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const u = ['e6', 'e6r'].flatMap(d => las(path.join(F, d, 'urval.json')).filter(k => fs.existsSync(path.join(F, d, 'kort', `${k.id}.json`))).map(k => ({ ...k, ...bas.get(k.id), c: las(path.join(F, d, 'kort', `${k.id}.json`)) })))
const konton = [...new Set(u.map(x => x.konto))]
const medel = a => a.reduce((s, x) => s + x, 0) / a.length
const inom = (fx, fy, filt = () => true) => { const rs = []; for (const k of konton) { const l = u.filter(x => x.konto === k && filt(x)), x = l.map(fx), y = l.map(fy); if (l.length < 4 || new Set(x).size < 2 || y.some(v => !Number.isFinite(v))) continue; rs.push(spearman(x, y)) } return rs.length ? (medel(rs) >= 0 ? '+' : '') + medel(rs).toFixed(2) : '–' }
const M = { grund: x => grund(x.c).p, nytta6: x => nytta6(x.c), kott: x => +(x.c.funktion === 'kott'), stod: x => +(x.c.funktion === 'stod'), kampanj: x => +(x.c.sprak.strategi === 'kampanj'), tavling: x => +(x.c.krav.situation === 'tavling'), tilltal: x => +(x.c.sprak.tilltal === 'till_kamera'), eget_tal: x => +(x.c.krav.ljud === 'eget_tal'), hojer_taket: x => +x.c.grundvarde.hojer_taket }
console.log('1. Portföljen (medel av rho inom konto)')
console.log('mått'.padEnd(13), 'visningar', 'gillanden', 'kommentarer', 'delningar')
for (const [n, f] of Object.entries(M)) console.log(n.padEnd(13), inom(f, x => x.rv).padStart(9), inom(f, x => x.rl).padStart(9), inom(f, x => x.rc).padStart(11), inom(f, x => x.rs).padStart(9))
console.log('\n2. Tiden: grundvärdet → visningar i kontots äldre och nyare hälft')
for (const k of konton) { const l = u.filter(x => x.konto === k).sort((a, b) => (a.datum ?? '').localeCompare(b.datum ?? '')); l.forEach((x, i) => x.halva = i < l.length / 2 ? 'aldre' : 'nyare') }
for (const h of ['aldre', 'nyare']) console.log(`  ${h}: grund ${inom(M.grund, x => x.rv, x => x.halva === h)}, nytta6 ${inom(M.nytta6, x => x.rv, x => x.halva === h)}`)
const ar = u.map(x => (x.datum ?? '').slice(0, 4)).filter(Boolean), rakna = {}; for (const a of ar) rakna[a] = (rakna[a] ?? 0) + 1
console.log('  klipp per år:', JSON.stringify(rakna))
