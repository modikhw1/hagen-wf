// Matchningens nyttosida (utforskande, 4 nov 2026): vilka sorters klipp går bättre i vilka sorters konton?
// E6 + E6-R: 597 klipp, 60 konton, inom konto mot visningar (rv). Kontots sort = dess vanligaste strategi
// bland dess 10 kort, andel klipp med personen i fokus, andel tilltal och vanligaste kantighet.
//   node format/e6-match.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const F = path.join(DATA, 'format'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const u = ['e6', 'e6r'].flatMap(d => las(path.join(F, d, 'urval.json')).filter(k => fs.existsSync(path.join(F, d, 'kort', `${k.id}.json`))).map(k => ({ ...k, urval: d, c: las(path.join(F, d, 'kort', `${k.id}.json`)) })))
const konton = [...new Set(u.map(x => x.konto))]
const modal = a => { const r = {}; for (const x of a) r[x] = (r[x] ?? 0) + 1; return Object.entries(r).sort((a, b) => b[1] - a[1])[0][0] }
const KANT = { familjar: 0, lekfull: 1, kantig: 2, vuxen: 3 }
const sort = {}
for (const k of konton) { const l = u.filter(x => x.konto === k); sort[k] = { strategi: modal(l.map(x => x.c.sprak.strategi)), fokus: l.filter(x => x.c.sprak.person === 'fokus').length / l.length, tilltal: l.filter(x => x.c.sprak.tilltal === 'till_kamera').length / l.length, kant: modal(l.map(x => x.c.sprak.kantighet)) } }
const medel = a => a.reduce((s, x) => s + x, 0) / a.length
const inom = (fx, kfilt) => { const rs = []; for (const k of konton.filter(k => kfilt(sort[k]))) { const l = u.filter(x => x.konto === k), x = l.map(fx); if (new Set(x).size > 1) rs.push(spearman(x, l.map(r => r.rv))) } return rs.length ? `${(medel(rs) >= 0 ? '+' : '') + medel(rs).toFixed(2)} (${rs.length})` : '–' }
const TYPER = ['sketchvarld', 'tilltal', 'visning', 'kampanj', 'premium_stamning']
const ksorter = [...new Set(Object.values(sort).map(s => s.strategi))].filter(s => Object.values(sort).filter(x => x.strategi === s).length >= 3)
console.log(`${u.length} klipp, ${konton.length} konton. Kontosorter (minst 3 konton): ${ksorter.map(s => `${s} ${Object.values(sort).filter(x => x.strategi === s).length}`).join(', ')}`)
console.log('\na. Klipptyp → visningar inom konto, per kontosort (rader: klipptyp, kolumner: kontosort)')
console.log('klipptyp'.padEnd(18) + ksorter.map(s => s.padStart(16)).join(''))
for (const t of TYPER) console.log(t.padEnd(18) + ksorter.map(s => inom(x => +(x.c.sprak.strategi === t), y => y.strategi === s).padStart(16)).join(''))
console.log('grundvärdet'.padEnd(18) + ksorter.map(s => inom(x => grund(x.c).p, y => y.strategi === s).padStart(16)).join(''))
console.log('\nb. Karisma hör till kunden? Personen i fokus → visningar')
console.log(`  konton där minst 30 % av klippen har en person i fokus: ${inom(x => +(x.c.sprak.person === 'fokus'), s => s.fokus >= 0.3)}`)
console.log(`  konton med färre:                                     ${inom(x => +(x.c.sprak.person === 'fokus'), s => s.fokus < 0.3)}`)
console.log('\nc. Eget tal och tilltal hos konton som talar till kameran ofta eller sällan')
console.log(`  tilltal till kameran, konton med minst 30 % tilltal: ${inom(x => +(x.c.sprak.tilltal === 'till_kamera'), s => s.tilltal >= 0.3)}`)
console.log(`  tilltal till kameran, konton med färre:              ${inom(x => +(x.c.sprak.tilltal === 'till_kamera'), s => s.tilltal < 0.3)}`)
console.log(`  eget tal, konton med minst 30 % tilltal:            ${inom(x => +(x.c.krav.ljud === 'eget_tal'), s => s.tilltal >= 0.3)}`)
console.log(`  eget tal, konton med färre:                         ${inom(x => +(x.c.krav.ljud === 'eget_tal'), s => s.tilltal < 0.3)}`)
console.log('\nd. Kantighet mot kontot')
console.log(`  kantigare än kontots vanligaste:  ${inom(x => +(KANT[x.c.sprak.kantighet] > KANT[sort[x.konto].kant]), () => true)}`)
console.log(`  snällare än kontots vanligaste:   ${inom(x => +(KANT[x.c.sprak.kantighet] < KANT[sort[x.konto].kant]), () => true)}`)
console.log('\ne. Replikerar mönstret mellan urvalen? Klipptyp → visningar, alla konton')
for (const t of TYPER) console.log(`  ${t.padEnd(18)} E6 ${inom(x => +(x.c.sprak.strategi === t), (s) => true)}`)
