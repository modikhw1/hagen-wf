// Pass 7 (4 nov 2026): parvis biblioteksbedömning. Ägaren väljer det bättre BIBLIOTEKSKLIPPET i 20 par (H16 på
// ägaren själv) och säger varför. Paren tas ur E6 och E6-R (klipp ägaren inte sett), med hyllan kärna eller mitten.
//   10 "isär": grundvärdet (LeTrend-värdet) och nytta6 pekar åt olika håll inom paret
//   10 "ihop": båda pekar åt samma håll
// Låst i data/format/harness/pass7/forregistrering.json innan ägaren sett något.
// Pro skriver en mening på engelska om vad som händer i varje klipp, till Miles.
//   LOVABLE_KONTO=3 node format/h-pass7.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
import { grund } from './h-match5.mjs'
import { nytta6 } from './h-v6.mjs'
const F = path.join(DATA, 'format'), P = path.join(F, 'harness', 'pass7'); fs.mkdirSync(P, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8')), reg = path.join(P, 'forregistrering.json')
if (fs.existsSync(reg)) { console.log('pass 7 är redan låst'); process.exit(0) }
const sett = new Set([...fs.readFileSync(path.join(F, 'e5', 'ids.txt'), 'utf8').split(/\r?\n/), ...las(path.join(F, 'harness', 'pass6', 'forregistrering.json')).kunder.flatMap(k => las(path.join(F, 'harness', 'pass6', 'forregistrering.json')).prognos[k].map(x => x.id))])
const pool = ['e6', 'e6r'].flatMap(d => fs.readdirSync(path.join(F, d, 'kort')).map(f => las(path.join(F, d, 'kort', f)))).filter(c => !sett.has(c.id) && ['karna', 'mitten'].includes(c.grundvarde.hylla))
pool.forEach(c => { c.g = grund(c).p; c.n = nytta6(c) })
let fro = 707; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }
const anvand = new Set(), par = []
const ok = (a, b) => a.id !== b.id && !anvand.has(a.id) && !anvand.has(b.id) && a.konto !== b.konto
for (const typ of ['isar', 'ihop']) {
  let n = 0
  for (const a of bl(pool)) { if (n >= 10) break; for (const b of bl(pool)) { if (!ok(a, b)) continue; const dg = a.g - b.g, dn = a.n - b.n; const villkor = typ === 'isar' ? dg * dn < 0 && Math.abs(dg) >= 1 && Math.abs(dn) >= 1 : dg * dn > 0 && Math.abs(dg) >= 1; if (!villkor) continue; par.push({ typ, a, b }); anvand.add(a.id); anvand.add(b.id); n++; break } }
}
const ordnade = bl(par).map((p, i) => ({ nr: i + 1, typ: p.typ, ...(sl() < 0.5 ? { v: p.a, h: p.b } : { v: p.b, h: p.a }) }))
// Engelska innehållsbeskrivningar till Miles.
const klipp = ordnade.flatMap(p => [p.v, p.h]), eng = {}
const s = d => ({ type: 'string', description: d }), obj = p => ({ type: 'object', properties: p, required: Object.keys(p), additionalProperties: false })
for (let i = 0; i < klipp.length; i += 20) {
  const g = klipp.slice(i, i + 20)
  const r = await analyseraVideo({ fil: path.join(F, 'tom.mp4'), prompt: `Du ser inte någon video: videon är en tom platshållare. Skriv för varje klipp en neutral mening på engelska (högst 20 ord) om vad som händer, utan att värdera och utan konto- eller platsnamn.\n${g.map((c, j) => `K${j + 1}: ${c.handling}`).join('\n')}`, schema: obj({ rader: { type: 'array', minItems: g.length, maxItems: g.length, items: obj({ kod: s('K-kod'), engelska: s('En mening på engelska.') }) } }), temperatur: 0.2, modell: 'google/gemini-3.1-pro-preview' })
  for (const x of r.data.rader) { const c = g[Number(x.kod.slice(1)) - 1]; if (c) eng[c.id] = x.engelska }
}
const rad = c => ({ id: c.id, url: c.url, konto: c.konto, grund: c.g, nytta6: +c.n.toFixed(2), hylla: c.grundvarde.hylla, strategi: c.sprak.strategi, karna: c.karna, engelska: eng[c.id] })
fs.writeFileSync(reg, JSON.stringify({
  last: new Date().toISOString() + ' (innan ägaren sett något klipp i pass 7)',
  design: '20 par biblioteksklipp ur E6/E6-R. Ägaren väljer det bättre biblioteksklippet (vänster eller höger) och säger varför. 10 par där grundvärdet och nytta6 pekar isär, 10 där de pekar ihop.',
  par: ordnade.map(p => ({ nr: p.nr, typ: p.typ, vanster: rad(p.v), hoger: rad(p.h) })),
  HP7a: 'I alla par väljer ägaren det klipp som grundvärdet föredrar i mer än hälften av fallen (teckentest, ensidigt p < 0,05).',
  HP7b: 'I isär-paren följer ägaren grundvärdet (preferensen) oftare än nytta6 (nyttan): mer än 5 av 10.',
  HP7c: 'Beskrivande: utfallen (rv) för klippen i isär-paren visas först efter passet: följde nyttan eller ägaren utfallet?',
}, null, 1))
let md = `# Pass 7: parvis bibliotek (4 nov 2026)\n\nTjugo par. Välj det klipp som är det **bättre biblioteksklippet**: det CM helst vill ha i LeTrends bibliotek att rekommendera vidare. Det handlar inte om en viss kund. Säg varför.\n\n`
for (const p of ordnade) md += `**Par ${p.nr}**\n- Vänster: ${p.v.url}\n- Höger: ${p.h.url}\n\n`
fs.writeFileSync(path.join(DATA, '..', 'karta', 'videoforandring', 'miles', 'pass-7-underlag.md'), md)
console.log(`${ordnade.length} par låsta (${ordnade.filter(p => p.typ === 'isar').length} isär), ${Object.keys(eng).length} engelska beskrivningar`)
