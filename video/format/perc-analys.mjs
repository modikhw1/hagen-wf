// Analys av perceptionsexperimentet: reliabilitet per videotyp.
// omtest: samma modell och typ, körning 1 mot 2. mellan modeller: Lite mot 3.8-flash (båda körningarna).
// mot Pro: överensstämmelse med Pro på originalet ur E1 (där det finns), som en grov validitetsproxy.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { LAGER } from './lager.mjs'

const S = path.join(DATA, 'format', 'perc', 'svar'), E1 = path.join(DATA, 'format', 'e1', 'gemini-3.1-pro-preview')
const urval = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'kalib', 'urval.json'), 'utf8'))
const las = d => Object.fromEntries(fs.existsSync(d) ? fs.readdirSync(d).map(f => { const x = JSON.parse(fs.readFileSync(path.join(d, f), 'utf8')); return [x.id, x] }) : [])
const tal = v => typeof v === 'boolean' ? (v ? 1 : 0) : v
function alfa(enheter, typ) {
  const o = new Map(), add = (a, b, w) => { const k = `${a}\u0000${b}`; o.set(k, (o.get(k) ?? 0) + w) }
  for (const u of enheter) { const v = u.filter(x => x != null); const m = v.length; if (m < 2) continue; for (let i = 0; i < m; i++) for (let j = 0; j < m; j++) if (i !== j) add(v[i], v[j], 1 / (m - 1)) }
  const nc = new Map(); let n = 0
  for (const [k, w] of o) { const c = k.split('\u0000')[0]; nc.set(c, (nc.get(c) ?? 0) + w); n += w }
  const d2 = (a, b) => typ === 'kat' ? (a === b ? 0 : 1) : (Number(a) - Number(b)) ** 2
  let Do = 0; for (const [k, w] of o) { const [a, b] = k.split('\u0000'); Do += w * d2(a, b) }
  Do /= n; let De = 0; const vals = [...nc.keys()]; for (const a of vals) for (const b of vals) De += nc.get(a) * nc.get(b) * d2(a, b); De /= n * (n - 1)
  return De === 0 ? NaN : 1 - Do / De
}
const TYPER = ['orig', 'lang', 'rutnat'], M = ['gemini-3.1-flash-lite', 'gemini-3.8-flash']
const d = Object.fromEntries(TYPER.map(t => [t, Object.fromEntries(M.map(m => [m, [1, 2].map(k => las(path.join(S, `${t}-${m}-k${k}`)))]))]))
const pro = [1, 2, 3].flatMap(p => [1, 2].map(k => las(path.join(E1, `p${p}-k${k}`))))
const v = (x, n, typ) => x?.[n] == null ? null : typ === 'kat' ? x[n] : tal(x[n])
const ut = {}
for (const [n, [typ]] of Object.entries(LAGER)) {
  ut[n] = {}
  for (const t of TYPER) {
    const omtest = M.map(m => alfa(urval.map(k => d[t][m].map(r => v(r[k.id], n, typ))), typ))
    const mellan = alfa(urval.map(k => M.flatMap(m => d[t][m].map(r => v(r[k.id], n, typ)))), typ)
    // mot Pro: alfa mellan Pro-konsensus (medel/typvärde över Pro-svar) och typens fyra svar
    const motPro = alfa(urval.map(k => { const ps = pro.map(r => v(r[k.id], n, typ)).filter(x => x != null); if (!ps.length) return []; const pv = typ === 'kat' ? ps.sort((a, b) => ps.filter(x => x === b).length - ps.filter(x => x === a).length)[0] : ps.reduce((a, b) => a + b) / ps.length; return [typ === 'kat' ? pv : Math.round(pv * 2) / 2, ...M.flatMap(m => d[t][m].map(r => v(r[k.id], n, typ)))] }), typ)
    ut[n][t] = { omtestLite: omtest[0], omtestFlash: omtest[1], mellan, motPro }
  }
}
const tok = Object.fromEntries(TYPER.map(t => [t, Math.round(M.flatMap(m => d[t][m].flatMap(r => Object.values(r).map(x => x.tokens))).reduce((a, b) => a + b, 0) / (M.length * 2 * urval.length))]))
fs.writeFileSync(path.join(DATA, 'format', 'perc', 'analys.json'), JSON.stringify({ tokens: tok, lager: ut }, null, 1))
const f = x => Number.isFinite(x) ? (x >= 0 ? ' ' : '') + x.toFixed(2) : '  -  '
console.log('tokens per anrop:', JSON.stringify(tok))
console.log(`${'lager'.padEnd(16)} | mellan modeller: orig  lång  rutnät | omtest Lite: orig lång rutnät | mot Pro: orig lång rutnät`)
const fokus = ['krok', 'redigeringsskamt', 'absurd', 'eskalering', 'vandning', 'slowmotion', 'mimar', 'trendljud', 'effekter', 'klipp', 'montage', 'kamera', 'feltolerans', 'poleringsgap', 'humor', 'roll', 'fristaende_ide', 'relation', 'lokal', 'sjalvironi']
for (const n of [...fokus, ...Object.keys(LAGER).filter(n => !fokus.includes(n))]) { const r = ut[n]; console.log(`${n.padEnd(16)} |                 ${TYPER.map(t => f(r[t].mellan)).join('  ')} |             ${TYPER.map(t => f(r[t].omtestLite)).join(' ')} |        ${TYPER.map(t => f(r[t].motPro)).join(' ')}`) }
const snitt = t => { const a = Object.values(ut).map(r => r[t].mellan).filter(Number.isFinite); return a.reduce((x, y) => x + y, 0) / a.length }
console.log('\nsnitt mellan modeller, alla lager:', TYPER.map(t => `${t} ${snitt(t).toFixed(3)}`).join(' | '))
const sf = t => { const a = fokus.slice(0, 10).map(n => ut[n][t].mellan).filter(Number.isFinite); return a.reduce((x, y) => x + y, 0) / a.length }
console.log('snitt mellan modeller, tid och klippning (10 första):', TYPER.map(t => `${t} ${sf(t).toFixed(3)}`).join(' | '))
// klipp 14: redigeringsskämtet som facit
const k14 = urval[13].id
console.log('\nklipp 14 redigeringsskamt (8 svar per typ):', TYPER.map(t => `${t} ${M.flatMap(m => d[t][m].map(r => r[k14]?.redigeringsskamt ? 1 : 0)).join('')}`).join(' | '))
