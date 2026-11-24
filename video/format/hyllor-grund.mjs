// Utforskande (4 nov 2026, inga anrop): grundvärdet → visningar inom konto per hylla i bibliotek v6, på alla klipp
// med utfall, för att se om det negativa resultatet i HG2 (de bäst rankade i mitten och situation) är urvalet.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
import { nytta6 } from './h-v6.mjs'
const F = path.join(DATA, 'format'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const DIRS = ['harness/v5', 'e6/kort', 'e6r/kort', 'bank2/kort', 'bank3/kort'].map(d => path.join(F, d))
const orig = id => las(DIRS.map(d => path.join(d, `${id}.json`)).find(fs.existsSync))
const B = las(path.join(F, 'harness', 'bibliotek-v6.json')).hyllor
const inom = (rows, fx) => { const per = {}; for (const x of rows) (per[x.konto] ??= []).push(x); const rs = []; for (const l of Object.values(per)) { if (l.length < 3) continue; const x = l.map(fx); if (new Set(x).size > 1) rs.push(spearman(x, l.map(q => q.rv))) } return rs.length ? `${(rs.reduce((s, v) => s + v, 0) / rs.length >= 0 ? '+' : '') + (rs.reduce((s, v) => s + v, 0) / rs.length).toFixed(3)} (${rs.length} konton)` : '–' }
for (const h of ['karna', 'mitten', 'situation', 'ute']) {
  const rows = (B[h] ?? []).map(x => ({ ...x, rv: bas.get(x.id)?.rv, c: orig(x.id) })).filter(x => Number.isFinite(x.rv))
  console.log(`${h.padEnd(10)} ${String(rows.length).padStart(4)} klipp: grund ${inom(rows, x => grund(x.c).p)}, nytta6 ${inom(rows, x => nytta6(x.c))}`)
}
const alla = Object.values(B).flat().map(x => ({ ...x, rv: bas.get(x.id)?.rv, c: orig(x.id) })).filter(x => Number.isFinite(x.rv))
console.log(`alla hyllor ${alla.length} klipp: grund ${inom(alla, x => grund(x.c).p)}, nytta6 ${inom(alla, x => nytta6(x.c))}`)
console.log(`hyllan som ordningstal (ute 0, capcut/situation 1, mitten 2, kärna 3) → rv: ${inom(alla, x => ({ ute: 0, capcut_referens: 1, situation: 1, mitten: 2, karna: 3 })[x.hylla_v6])}`)
