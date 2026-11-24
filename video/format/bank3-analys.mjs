// Analys av bank3, tilltalshyllan (förregistrerat i data/format/bank3/forregistrering.json).
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
import { nytta6 } from './h-v6.mjs'
const B = path.join(DATA, 'format', 'bank3'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const u = las(path.join(B, 'extra.json')).filter(k => fs.existsSync(path.join(B, 'kort', `${k.id}.json`))).map(k => ({ ...k, c: las(path.join(B, 'kort', `${k.id}.json`)), rv: bas.get(k.id)?.rv })).filter(k => Number.isFinite(k.rv))
const per = {}; for (const k of u) (per[k.konto] ??= []).push(k)
const gr = Object.values(per).filter(l => l.length >= 3)
let fro = 2; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const test = fx => { const st = ys => { const rs = []; for (const l of gr) { const x = l.map(fx); if (new Set(x).size > 1) rs.push(spearman(x, l.map(r => ys.get(r.id)))) } return { r: rs.reduce((s, v) => s + v, 0) / rs.length, k: rs.length } }; const ys = new Map(u.map(r => [r.id, r.rv])), obs = st(ys); let e = 0; for (let t = 0; t < 3000; t++) { const p = new Map(); for (const l of gr) { const v = l.map(r => r.rv); for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } l.forEach((r, i) => p.set(r.id, v[i])) } if (st(p).r >= obs.r) e++ } return `${obs.r >= 0 ? '+' : ''}${obs.r.toFixed(3)} (${obs.k} konton), p ${((e + 1) / 3001).toFixed(4)}` }
console.log(`${u.length} kort med utfall från ${Object.keys(per).length} konton`)
console.log(`HT1 grund → rv inom konto: ${test(x => grund(x.c).p)}`)
console.log(`(HB2-motsvarighet) premiss stark → rv inom konto: ${test(x => +(x.c.grundvarde.premiss === 'stark'))}`)
const hyl = {}; for (const k of u) hyl[k.c.grundvarde.hylla] = (hyl[k.c.grundvarde.hylla] ?? 0) + 1
console.log(`(hyllor) hyllor: ${JSON.stringify(hyl)}, kärna ${Math.round(100 * (hyl.karna ?? 0) / u.length)} %`)
console.log(`utforskande: nytta6 → rv ${test(x => nytta6(x.c))}, eget tal → rv ${test(x => +(x.c.krav.ljud === 'eget_tal'))}, höjer taket → rv ${test(x => +x.c.grundvarde.hojer_taket)}`)
console.log(`HT2 personen i fokus → rv inom konto: ${test(x => +(x.c.sprak.person === 'fokus'))}`)
console.log(`HT3 kärna ${Math.round(100 * (hyl.karna ?? 0) / u.length)} % (högst 20 % väntat)`)
