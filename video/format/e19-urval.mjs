// E19: urval för replikering. Bankklipp som INTE har motor, högst 10 per konto, slumpade med fast frö och utan att
// se på utfall. Resultat: data/format/e19/ids.json
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const har = new Set([...fs.readdirSync(path.join(os.homedir(), 'Downloads', 'letrend-e13')).map(f => f.replace(/\.mp4$/, '')), ...Object.values(las(path.join(DATA, 'format', 'harness', 'bibliotek-v6.json')).hyllor).flat().map(k => k.id)])
let fro = 20261117; const slump = () => { fro = (fro * 1664525 + 1013904223) % 4294967296; return fro / 4294967296 }
const per = {}
for (const f of fs.readdirSync(path.join(DATA, 'bank', 'sallning')).sort()) { const s = las(path.join(DATA, 'bank', 'sallning', f)); if (har.has(s.id) || s.bildspel) continue; (per[s.konto] ??= []).push(s.id) }
const ids = []
for (const k of Object.keys(per).sort()) { const L = per[k].map(id => [slump(), id]).sort((a, b) => a[0] - b[0]).map(x => x[1]); ids.push(...L.slice(0, 10)) }
fs.writeFileSync(path.join(DATA, 'format', 'e19', 'ids.json'), JSON.stringify(ids))
const motorKonton = new Set([...har].map(id => id.slice(0, id.lastIndexOf('-'))))
console.log(ids.length, 'klipp från', Object.keys(per).length, 'konton;', Object.keys(per).filter(k => !motorKonton.has(k)).length, 'konton har inga klipp bland motorerna')
