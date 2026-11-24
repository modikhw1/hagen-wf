// Utforskande (4 nov 2026): saknas ett nyttolager för "anledning" (lansering, högtid, event, tävling) och för
// längd och trendljud? Inom konto i E6 (299 klipp).
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const DIR = process.env.E6DIR ?? 'e6', E = path.join(DATA, 'format', DIR), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const u = las(path.join(E, 'urval.json')).filter(k => fs.existsSync(path.join(E, 'kort', `${k.id}.json`))).map(k => ({ ...k, c: las(path.join(E, 'kort', `${k.id}.json`)) }))
const konton = [...new Set(u.map(x => x.konto))]
const inom = (fx, filt = () => true) => { const rs = []; for (const k of konton) { const l = u.filter(x => x.konto === k && filt(x)), x = l.map(fx); if (l.length < 4 || new Set(x).size < 2) continue; rs.push(spearman(x, l.map(r => r.rv))) } return `${(rs.reduce((s, v) => s + v, 0) / rs.length >= 0 ? '+' : '') + (rs.reduce((s, v) => s + v, 0) / rs.length).toFixed(3)} (${rs.length} konton)` }
const rakna = {}; for (const x of u) rakna[x.c.krav.situation] = (rakna[x.c.krav.situation] ?? 0) + 1
console.log('situationer:', JSON.stringify(rakna))
console.log('anledning (situation inte vardag) → rv:', inom(x => +(x.c.krav.situation !== 'vardag')))
console.log('lansering → rv:', inom(x => +(x.c.krav.situation === 'lansering')))
console.log('evergreen → rv:', inom(x => +x.c.evergreen))
console.log('längd → rv:', inom(x => x.langd))
console.log('längd → rv bland sketcher:', inom(x => x.langd, x => x.c.sprak.strategi === 'sketchvarld'))
console.log('trendljud → rv:', inom(x => +(x.c.krav.ljud === 'trendljud')))
console.log('trendljud → rv bland sketcher:', inom(x => +(x.c.krav.ljud === 'trendljud'), x => x.c.sprak.strategi === 'sketchvarld'))
console.log('eget tal → rv:', inom(x => +(x.c.krav.ljud === 'eget_tal')))
console.log('grund + anledning → rv:', inom(x => grund(x.c).p + 2.5 * +(x.c.krav.situation !== 'vardag')))
console.log('grund → rv (jämförelse):', inom(x => grund(x.c).p))
