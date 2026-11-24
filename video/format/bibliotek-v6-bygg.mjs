// Bibliotek v6 (4 nov 2026): alla v5-kort (biblioteket v0, E6, E6-R, bank2) samlade med två mått som inte blandas,
// hylla, språk och villkor, och ägarens omdöme där det finns. Inga anrop.
//   node format/bibliotek-v6-bygg.mjs
// Resultat: data/format/harness/bibliotek-v6.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { grund } from './h-match5.mjs'
import { nytta6, nytta62, rutnatKort } from './h-v6.mjs'
const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const kallor = [['v0', path.join(H, 'v5')], ['e6', path.join(F, 'e6', 'kort')], ['e6r', path.join(F, 'e6r', 'kort')], ['bank2', path.join(F, 'bank2', 'kort')], ['bank3', path.join(F, 'bank3', 'kort')]]
const kalib = las(path.join(F, 'kalib', 'agare.json')).klipp, bib = las(path.join(H, 'urval.json')).bibliotek
const nrAv = Object.fromEntries(bib.filter(k => k.kalla === 'kalib').map(k => [k.id, k.nr]))
const U = las(path.join(H, 'validering', 'urval.json')), A = las(path.join(H, 'validering', 'agare.json'))
const pf = {}; for (const [k, { klipp }] of Object.entries(U)) for (const c of klipp) { const p = A.klipp[k]?.[c.pos]?.passform; if (Number.isFinite(p)) (pf[c.id] ??= []).push(`${k} ${p}`) }
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const alla = {}
for (const [kalla, d] of kallor) if (fs.existsSync(d)) for (const f of fs.readdirSync(d)) { const c = las(path.join(d, f)); if (alla[c.id]) continue
  const nr = nrAv[c.id]
  alla[c.id] = { id: c.id, url: c.url, konto: c.konto, kalla, hylla: c.grundvarde.hylla, letrend_varde: grund(c).p, forvantad_nytta: +nytta6(c).toFixed(2), nytta_v62: +nytta62(c).toFixed(2), krok_rutnat: rutnatKort(c.id)?.grundvarde.krok ?? null, strategi: c.sprak.strategi, kantighet: c.sprak.kantighet, person: c.sprak.person, karna: c.karna, mall: c.mall, villkor: { personer_min: c.krav.personer_min, skadespel: c.krav.skadespel, redigering: c.krav.redigering, produkt: c.krav.produkt, verksamheter: c.krav.verksamheter, situation: c.krav.situation, segment: c.krav.segment }, agare: nr ? { bibliotek: kalib[nr]?.bibliotek, citat: kalib[nr]?.citat } : pf[c.id] ? { passform: pf[c.id] } : null, utfall_rv: bas.get(c.id)?.rv ?? null }
}
const l = Object.values(alla)
// Hyllorna i v6: ägarens biblioteksbeslut går före modellens hylla där det finns.
for (const x of l) { x.hylla_v6 = x.agare?.bibliotek === 'nej' ? 'ute' : x.agare?.bibliotek === 'ja' && x.hylla !== 'karna' ? 'karna' : x.hylla }
const hyllor = {}; for (const x of l) (hyllor[x.hylla_v6] ??= []).push(x)
for (const h of Object.values(hyllor)) h.sort((a, b) => b.nytta_v62 - a.nytta_v62 || b.letrend_varde - a.letrend_varde)
fs.writeFileSync(path.join(H, 'bibliotek-v6.json'), JSON.stringify({ byggt: new Date().toISOString(), kallor: kallor.map(k => k[0]), antal: l.length, hyllor: Object.fromEntries(Object.entries(hyllor).map(([h, v]) => [h, v])) }, null, 1))
const st = v => { const r = {}; for (const x of v) r[x.strategi] = (r[x.strategi] ?? 0) + 1; return Object.entries(r).sort((a, b) => b[1] - a[1]).map(([k, n]) => `${k} ${n}`).join(', ') }
console.log(`${l.length} kort. Hyllor i v6:`)
for (const [h, v] of Object.entries(hyllor).sort((a, b) => b[1].length - a[1].length)) console.log(`  ${h.padEnd(16)} ${String(v.length).padStart(4)} klipp från ${new Set(v.map(x => x.konto)).size} konton | ${st(v)}`)
const k = hyllor.karna ?? []
console.log(`kärnhyllan: ${k.length} klipp (v0 hade ~25), LeTrend-värde ≥ 5: ${k.filter(x => x.letrend_varde >= 5).length}, med ägarens omdöme: ${k.filter(x => x.agare).length}`)
