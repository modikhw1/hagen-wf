// Analys av sekvenstest A: tappar modellen detaljer när fem klipp ligger i samma fil?
// Jämförs per lager: ensam körning 1 mot 2 (omtest, baslinje), sekvens mot ensam, framlänges mot
// baklänges, och hur väl svaret stämmer för varje position (1–5) mot ensam körning.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { LAGER } from './lager.mjs'
const F = path.join(DATA, 'format')
const res = JSON.parse(fs.readFileSync(path.join(F, 'sekvens', 'resultat-A.json'), 'utf8')).filter(r => !r.fel)
const ens = k => Object.fromEntries(fs.readdirSync(path.join(F, 'perc', 'svar', `orig-gemini-3.1-flash-lite-k${k}`)).map(f => { const x = JSON.parse(fs.readFileSync(path.join(F, 'perc', 'svar', `orig-gemini-3.1-flash-lite-k${k}`, f), 'utf8')); return [x.id, x] }))
const e1 = ens(1), e2 = ens(2)
const seq = { fram: {}, bak: {} }, pos = {}
for (const r of res) r.r.klipp.forEach((x, i) => { const id = r.ids[i]; seq[r.riktning][id] = x; (pos[id] ??= {})[r.riktning] = i + 1 })
const ids = Object.keys(seq.fram).filter(id => seq.bak[id] && e1[id] && e2[id])
const lika = (a, b, n) => a?.[n] != null && b?.[n] != null ? (a[n] === b[n] ? 1 : 0) : null
const medel = a => { const v = a.filter(x => x != null); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : NaN }
const rader = []
for (const n of Object.keys(LAGER)) {
  rader.push({ n, omtest: medel(ids.map(id => lika(e1[id], e2[id], n))), sekvens: medel(ids.flatMap(id => [lika(seq.fram[id], e1[id], n), lika(seq.bak[id], e2[id], n)])), framBak: medel(ids.map(id => lika(seq.fram[id], seq.bak[id], n))) })
}
const tot = k => medel(rader.map(r => r[k]))
console.log(`${ids.length} klipp. Exakt överensstämmelse i snitt över ${rader.length} lager:`)
console.log(`  ensam mot ensam (omtest)      ${tot('omtest').toFixed(3)}`)
console.log(`  sekvens mot ensam             ${tot('sekvens').toFixed(3)}`)
console.log(`  sekvens framlänges mot bak    ${tot('framBak').toFixed(3)}`)
// per position: andel lager som stämmer med ensam körning
const perPos = [1, 2, 3, 4, 5].map(p => medel(ids.flatMap(id => ['fram', 'bak'].filter(rk => pos[id][rk] === p).flatMap(rk => Object.keys(LAGER).map(n => lika(seq[rk][id], e1[id], n)))))) 
console.log('  per position 1–5 mot ensam:  ', perPos.map(x => x.toFixed(3)).join('  '))
console.log('\nstörst tapp (omtest minus sekvens):')
for (const r of rader.sort((a, b) => (b.omtest - b.sekvens) - (a.omtest - a.sekvens)).slice(0, 12)) console.log(`  ${r.n.padEnd(16)} omtest ${r.omtest.toFixed(2)}  sekvens ${r.sekvens.toFixed(2)}  fram/bak ${r.framBak.toFixed(2)}`)
console.log('\nminst tapp:')
for (const r of rader.slice(-8)) console.log(`  ${r.n.padEnd(16)} omtest ${r.omtest.toFixed(2)}  sekvens ${r.sekvens.toFixed(2)}`)
// läckage: blir klippen mer lika varandra i sekvensen än ensamma? (varians mellan klipp inom grupp)
const spr = (src) => medel(res.filter(r => r.riktning === 'fram').flatMap(r => Object.entries(LAGER).filter(([, [t]]) => t !== 'kat').map(([n]) => { const v = r.ids.map(id => { const x = src[id]?.[n]; return typeof x === 'boolean' ? +x : x }).filter(x => x != null); const m = medel(v); return medel(v.map(x => (x - m) ** 2)) })))
console.log(`\nspridning mellan klippen i en grupp: ensamma ${spr(e1).toFixed(3)}, i sekvens ${spr(seq.fram).toFixed(3)} (lägre = klippen smetas ihop)`)
const tok = res.map(r => JSON.parse(fs.readFileSync(path.join(F, 'sekvens', 'A', `g${r.g + 1}-${r.riktning}.json`), 'utf8')).tokens)
console.log(`tokens per sekvens ${Math.round(medel(tok))} (= ${Math.round(medel(tok) / 5)} per klipp; ensam ≈ 4900)`)
