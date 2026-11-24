// E17: underlag till motorgeometrin. En rad per klipp med motor: motortext, yta, svag text, utfall, familj, hylla.
// Resultat: data/format/e15/motorer.jsonl (samma mapp som inbäddaren e15_badda.py läser ur)
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
// node format/e17-underlag.mjs [mekanism | mekanism-3.8-flash]
const MAPP = process.argv[2] ?? 'mekanism', M = path.join(DATA, 'format', 'e14', MAPP), SAL = path.join(DATA, 'bank', 'sallning')
const FAM = las(path.join(DATA, 'format', 'familjer', 'familjer.json'))
const BIB = Object.fromEntries(Object.values(las(path.join(DATA, 'format', 'harness', 'bibliotek-v6.json')).hyllor).flat().map(k => [k.id, k]))
const listor = {}, utfall = {}
function konto(k) {
  if (k in listor) return
  const lf = path.join(DATA, 'bank', k, 'lista.json'); listor[k] = {}
  if (!fs.existsSync(lf)) return
  const L = las(lf).klipp; for (const x of L) listor[k][x.id] = x
  const T = L.filter(x => x.visningar > 0).sort((a, b) => (a.datum || '').localeCompare(b.datum || ''))
  T.forEach((x, i) => { const g = T.slice(Math.max(0, i - 10), i + 11).filter(y => y !== x).map(y => Math.log(y.visningar)).sort((a, b) => a - b); if (g.length >= 6) utfall[`${k}-${x.id}`] = Math.log(x.visningar) - g[Math.floor(g.length / 2)] })
}
const ut = []
for (const f of fs.readdirSync(M)) {
  const j = las(path.join(M, f)), id = j.id, i = id.lastIndexOf('-'), k = id.slice(0, i), m = j.mekanism
  konto(k); const meta = listor[k][id.slice(i + 1)] ?? {}, sf = path.join(SAL, `${id}.json`), sal = fs.existsSync(sf) ? las(sf) : {}
  ut.push(JSON.stringify({ id, konto: k, motor: m.motor, hel: `${m.motor} ${m.forlopp} Hållning: ${m.hallning}`, hallning: m.hallning, yta: m.yta, svag: `${sal.innehall ?? ''} ${(meta.text ?? '').replace(/#\S+/g, '').replace(/\s+/g, ' ').trim().slice(0, 200)}`.trim(), hantverk: m.hantverk, slitage: m.slitage, utsatthet: m.krav?.utsatthet, u: utfall[id] ?? null, familj: FAM[id] ?? null, hylla: BIB[id]?.hylla ?? null, varde: BIB[id]?.letrend_varde ?? null, kalla: BIB[id]?.kalla ?? null }))
}
fs.writeFileSync(path.join(DATA, 'format', 'e15', MAPP === 'mekanism' ? 'motorer.jsonl' : 'motorer-flash.jsonl'), ut.join('\n'))
const R = ut.map(x => JSON.parse(x)); console.log(R.length, 'klipp med motor,', new Set(R.map(r => r.konto)).size, 'konton,', R.filter(r => r.u !== null).length, 'med utfall,', R.filter(r => r.hylla).length, 'i biblioteket')
