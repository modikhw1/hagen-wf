// E11b (utforskande, 4 nov 2026): distinktioner inom klipptyp i hela banken (10 650 klipp, inga anrop).
//   node format/e11b.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
const S = path.join(DATA, 'bank', 'sallning'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const alla = fs.readdirSync(S).map(f => las(path.join(S, f))).filter(k => Number.isFinite(bas.get(k.id)?.rv)).map(k => ({ ...k, rv: bas.get(k.id).rv, rl: bas.get(k.id).rl, langd: bas.get(k.id).langd }))
const per = {}; for (const k of alla) (per[k.konto] ??= []).push(k)
const grupper = Object.values(per).filter(l => l.length >= 20)
const inom = (fx, filt = () => true, fy = r => r.rv) => { const rs = []; for (const l of grupper) { const m = l.filter(filt); const x = m.map(fx); if (m.length < 6 || new Set(x).size < 2) continue; rs.push(spearman(x, m.map(fy))) } return rs.length ? `${(rs.reduce((s, v) => s + v, 0) / rs.length >= 0 ? '+' : '') + (rs.reduce((s, v) => s + v, 0) / rs.length).toFixed(3)} (${rs.length})` : '–' }
const T = ['relaterbar_sketch', 'direkt_tilltal', 'matporr_och_process', 'vardens_provsmakning']
const M = { rekonbar: x => x.rekonbar ?? 0, andel_person: x => x.andel_med_person ?? 0, personer: x => x.personer_max ?? 0, langd: x => x.langd ?? 0, inne: x => +!!x.inne_i_verksamheten, text_tung: x => +!!x.text_tung, bildspel: x => +!!x.bildspel, montage: x => +!!x.montage, bildkvalitet: x => x.bildkvalitet ?? 0 }
console.log(`${alla.length} klipp, ${grupper.length} konton. Medel av rho inom konto mot visningar, alla klipp och inom typ (antal konton)`)
console.log('mått'.padEnd(14) + 'alla'.padStart(15) + T.map(t => t.slice(0, 14).padStart(17)).join(''))
for (const [n, f] of Object.entries(M)) console.log(n.padEnd(14) + inom(f).padStart(15) + T.map(t => inom(f, x => x.typ === t).padStart(17)).join(''))
console.log('\ngillanden per visning (rl) för samma mått, alla klipp:', Object.entries(M).map(([n, f]) => `${n} ${inom(f, () => true, r => r.rl)}`).join(', '))
