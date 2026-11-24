// Metaanalys (4 nov 2026, inga anrop): alla v5-kort med utfall (E6, E6-R, bank2, bank3), medel av rho inom konto
// mot visningar, med 95 % konfidensintervall genom bootstrap över konton (2 000 dragningar).
//   node format/meta.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
import { nytta6 } from './h-v6.mjs'
const F = path.join(DATA, 'format'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const kallor = [['e6', 'urval.json'], ['e6r', 'urval.json'], ['bank2', 'extra.json'], ['bank3', 'extra.json']]
const sett = new Set(), u = []
for (const [d, f] of kallor) for (const k of las(path.join(F, d, f))) { const kf = path.join(F, d, 'kort', `${k.id}.json`); if (sett.has(k.id) || !fs.existsSync(kf)) continue; const rv = bas.get(k.id)?.rv; if (!Number.isFinite(rv)) continue; sett.add(k.id); u.push({ id: k.id, konto: k.konto, rv, c: las(kf), kalla: d }) }
const per = {}; for (const x of u) (per[x.konto] ??= []).push(x)
const konton = Object.keys(per).filter(k => per[k].length >= 4)
const M = {
  'grundvärdet': c => grund(c).p, 'nytta6': c => nytta6(c), 'premiss stark': c => +(c.grundvarde.premiss === 'stark'), 'höjer taket': c => +c.grundvarde.hojer_taket,
  'utan efterarbete': c => ({ nej: 0, delvis: 1, ja: 2 })[c.grundvarde.utan_efterarbete], 'vändning': c => +c.grundvarde.vandning, 'krok (original)': c => ({ ingen: 0, svag: 1, stark: 2 })[c.grundvarde.krok],
  'eget tal': c => +(c.krav.ljud === 'eget_tal'), 'trendljud': c => +(c.krav.ljud === 'trendljud'), 'ingen person bär': c => +(c.sprak.person === 'ingen'), 'karisma (fokus)': c => +(c.sprak.person === 'fokus'),
  'sketch': c => +(c.sprak.strategi === 'sketchvarld'), 'tilltal': c => +(c.sprak.strategi === 'tilltal'), 'visning': c => +(c.sprak.strategi === 'visning'), 'Instagram-språk': c => +(c.sprak.plattform !== 'tiktok'),
  'klippberoende': c => ({ lite: 0, en_del: 1, mycket: 2 })[c.sprak.klippberoende], 'bundna bilder': c => ({ fa: 0, halften: 1, nastan_alla: 2 })[c.forlaga.bundna_bilder], 'kantighet': c => ({ familjar: 0, lekfull: 1, kantig: 2, vuxen: 3 })[c.sprak.kantighet],
}
const rKonto = (k, f) => { const l = per[k], x = l.map(q => f(q.c)); return new Set(x).size > 1 ? spearman(x, l.map(q => q.rv)) : null }
let fro = 31; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
console.log(`${u.length} klipp med utfall, ${konton.length} konton med minst 4 klipp\n`)
console.log('spak'.padEnd(20), 'rho', '  95 % KI', '        konton')
const ut = {}
for (const [n, f] of Object.entries(M)) {
  const rk = konton.map(k => rKonto(k, f)).filter(v => v !== null), m = rk.reduce((s, v) => s + v, 0) / rk.length
  const bs = []; for (let b = 0; b < 2000; b++) { let s = 0; for (let i = 0; i < rk.length; i++) s += rk[Math.floor(sl() * rk.length)]; bs.push(s / rk.length) }
  bs.sort((a, b) => a - b); const lo = bs[50], hi = bs[1949]
  ut[n] = { rho: m, ki: [lo, hi], konton: rk.length }
  const fmt = v => (v >= 0 ? '+' : '') + v.toFixed(2)
  console.log(n.padEnd(20), fmt(m), `[${fmt(lo)}, ${fmt(hi)}]`, String(rk.length).padStart(6), lo > 0 ? '  säkert positiv' : hi < 0 ? '  säkert negativ' : '')
}
fs.writeFileSync(path.join(F, 'meta.json'), JSON.stringify({ klipp: u.length, konton: konton.length, spakar: ut }, null, 1))
