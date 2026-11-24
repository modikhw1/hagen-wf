// E10-bank (utforskande): räcker bankens sållningslager (typ, personer, montage, rekonbar) för en grov
// grundvärdesproxy? Korsvaliderat per konto på överlappet med E6/E6-R. Om ja: sålla hela banken gratis.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const F = path.join(DATA, 'format'), S = path.join(DATA, 'bank', 'sallning'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const sall = Object.fromEntries(fs.readdirSync(S).map(f => { const k = las(path.join(S, f)); return [k.id, k] }))
const typer = [...new Set(Object.values(sall).map(k => k.typ))]
const vek = k => [k.personer_max ?? 0, k.andel_med_person ?? 0, +!!k.inne_i_verksamheten, k.bildkvalitet ?? 0, +!!k.montage, +!!k.bildspel, +!!k.text_tung, k.rekonbar ?? 0, ...typer.map(t => +(k.typ === t))]
const tr = ['e6', 'e6r'].flatMap(d => las(path.join(F, d, 'urval.json')).filter(k => sall[k.id] && fs.existsSync(path.join(F, d, 'kort', `${k.id}.json`))).map(k => ({ konto: k.konto, x: vek(sall[k.id]), y: grund(las(path.join(F, d, 'kort', `${k.id}.json`))).p, typ: sall[k.id].typ })))
console.log(`överlapp ${tr.length} klipp, ${typer.length} typer`)
if (tr.length < 50) process.exit(0)
// Medel av grund per typ (korsvaliderat per konto) som enklaste proxy.
const konton = [...new Set(tr.map(r => r.konto))].sort(), g = k => konton.indexOf(k) % 10
const cv = tr.map(r => { const ov = tr.filter(x => g(x.konto) !== g(r.konto)); const sam = ov.filter(x => x.typ === r.typ); return { ...r, p: sam.length >= 3 ? sam.reduce((s, x) => s + x.y, 0) / sam.length : ov.reduce((s, x) => s + x.y, 0) / ov.length } })
console.log(`korsvaliderad rho, typens medelgrund mot grund: ${spearman(cv.map(r => r.p), cv.map(r => r.y)).toFixed(2)}`)
const pertyp = typer.map(t => { const l = tr.filter(r => r.typ === t); return [t, l.length, l.length ? l.reduce((s, r) => s + r.y, 0) / l.length : NaN] }).filter(x => x[1] >= 5).sort((a, b) => b[2] - a[2])
console.log('grund per sållningstyp (n ≥ 5):', pertyp.map(([t, n, m]) => `${t} ${m.toFixed(1)} (${n})`).join(', '))
