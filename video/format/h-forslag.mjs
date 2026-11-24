// CM-förslag v6.2 (4 nov 2026): för varje kund med en linje, ur bibliotek v6 (kärna, mitten, situation):
//   topp 3 på LeTrend-värde (preferens: grund + mjukt linjeräcke + förlaga, h-v6.mjs varde)
//   topp 3 på förväntad nytta för kunden (nytta62 + E11:s fortsättning för sketch och komplement för tilltal/person)
//   topp 3 särskilt för kunden: grund ≥ 4 och störst skillnad mot medel över alla kunder (motverkar att samma sketch toppar överallt)
//   scenplanen för förstahandsvalet (h-scener.mjs)
// Två mått som inte blandas: där topplistorna skiljer sig är det ett val för CM. Inga anrop.
//   node format/h-forslag.mjs
// Resultat: karta/videoforandring/forslag-v6.md och data/format/harness/forslag-v6.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { varde, nytta62 } from './h-v6.mjs'
import { grund } from './h-match5.mjs'
// Nytta för kunden: nytta62 plus E11:s kundberoende regler, som kommer ur utfall (10 650 bankklipp).
const nyttaKund = (c, L) => { const sk = c.sprak.strategi === 'sketchvarld', tt = c.sprak.tilltal === 'till_kamera' || c.sprak.strategi === 'tilltal', ks = L.strategi === 'sketchvarld', kv = ['visning', 'premium_stamning'].includes(L.strategi); return nytta62(c) + (sk && ks ? 1 : 0) + (sk && kv ? 0.25 : 0) + (tt && kv ? 1 : 0) + (c.sprak.person !== 'ingen' && kv ? 0.5 : 0) }
import { scenplan } from './h-scener.mjs'
const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const DIRS = ['harness/v5', 'e6/kort', 'e6r/kort', 'bank2/kort', 'bank3/kort'].map(d => path.join(F, d))
const kortFil = id => DIRS.map(d => path.join(d, `${id}.json`)).find(fs.existsSync)
const B = las(path.join(H, 'bibliotek-v6.json')).hyllor
const kand = ['karna', 'mitten', 'situation'].flatMap(h => (B[h] ?? []).map(x => ({ ...x, hylla_v6: h })))
const kunder = fs.readdirSync(path.join(H, 'linje')).map(f => f.replace(/\.json$/, ''))
const ATG = { behall: 'behåll', fritt: 'fritt', byt_produkt: 'byt produkt', byt_lokal: 'byt lokal', frontfigur: 'frontfiguren tar rollen', risk: 'risk', eget_tal: 'byt till eget tal', forenkla: 'förenkla' }
const ut = {}
// Temaräcket (tema.mjs): ett vuxet tema hos en familjär eller lekfull kund sänker LeTrend-värdet med 2. Bara preferens: utfallen säger inget om det.
const TEMA = fs.existsSync(path.join(H, 'tema.json')) ? las(path.join(H, 'tema.json')) : {}
const temaStraff = (id, L) => TEMA[id]?.vuxet && ['familjar', 'lekfull'].includes(L.kantighet) ? 2 : 0
const Ls = Object.fromEntries(kunder.map(k => [k, las(path.join(H, 'linje', `${k}.json`))]))
const kortCache = new Map(kand.map(x => [x.id, las(kortFil(x.id))]))
const medelV = new Map(kand.map(x => { const c = kortCache.get(x.id); const vs = kunder.map(k => varde(c, Ls[k]).varde + nyttaKund(c, Ls[k])); return [x.id, vs.reduce((a, b) => a + b, 0) / vs.length] }))
let md = `# CM-förslag v6.2 (4 nov 2026)\n\nUr bibliotek v6 (${kand.length} klipp på hyllorna kärna, mitten och situation). För varje kund visas tre topplistor som inte blandas:\n- **LeTrend-värde** (preferens): klippets grundvärde, ett mjukt linjeräcke och förlagan.\n- **Förväntad nytta för kunden**: grundvärdet, eget ljud, person i visning, kroken ur rutnätet och E11:s regler, alltså att sketch är fortsättning och att tilltal och personer är komplement.\n- **Särskilt för kunden**: klipp med grundvärde minst 4 som passar just den här kunden bättre än de andra.\n\nDär listorna skiljer sig väljer CM. Kundens egna klipp och omöjliga klipp (fler personer än kunden har) är bortsorterade.\n`
for (const k of kunder) {
  const L = las(path.join(H, 'linje', `${k}.json`))
  const r = kand.filter(x => x.konto !== k).map(x => { const c = kortCache.get(x.id); const v0 = varde(c, L), ts0 = temaStraff(x.id, L), v = { ...v0, varde: v0.varde - ts0, skal: ts0 ? [...v0.skal, 'vuxet tema hos en familjär kund'] : v0.skal }, n = nyttaKund(c, L); return { x, c, v, n, sar: grund(c).p >= 4 ? v.varde + n - medelV.get(x.id) : -99 } }).filter(o => !(o.c.krav.personer_min > (L.max_personer ?? 2) + 1))
  const avs = new Set(), topp = (f) => { avs.clear(); return [...r].sort((a, b) => f(b) - f(a)).filter(o => !avs.has(o.x.konto) && avs.add(o.x.konto)).slice(0, 3) }
  const tv = topp(o => o.v.varde), tn = topp(o => o.n), ts = topp(o => o.sar)
  const plan = scenplan(tv[0].c, L)
  ut[k] = { linje: L.linje, letrend_varde: tv.map(o => ({ id: o.x.id, url: o.x.url, varde: +o.v.varde.toFixed(2), nytta: +o.n.toFixed(2), karna: o.x.karna, skal: o.v.skal })), forvantad_nytta: tn.map(o => ({ id: o.x.id, url: o.x.url, varde: +o.v.varde.toFixed(2), nytta: +o.n.toFixed(2), karna: o.x.karna })), sarskilt: ts.map(o => ({ id: o.x.id, url: o.x.url, lyft: +o.sar.toFixed(2), karna: o.x.karna })), scenplan_forsta: plan }
  const rad = o => `- ${o.x.karna} (${o.x.hylla_v6}, ${o.c.sprak.strategi}) · värde ${o.v.varde.toFixed(1)}, nytta ${o.n.toFixed(1)} · ${o.x.url}`
  md += `\n## @${k}\n${L.linje}\n\n**LeTrend-värde**\n${tv.map(rad).join('\n')}\n\n**Förväntad nytta för kunden**\n${tn.map(rad).join('\n')}\n\n**Särskilt för kunden** (bättre här än hos de andra kunderna)\n${ts.map(rad).join('\n')}\n\n**Scenplan för förstahandsvalet:** ${plan.sammanfattning}. ${plan.beats.map(b => `${b.nr} ${ATG[b.atgard]}`).join(', ')}.\n`
}
fs.writeFileSync(path.join(H, 'forslag-v6.json'), JSON.stringify(ut, null, 1))
fs.writeFileSync(path.join(DATA, '..', 'karta', 'videoforandring', 'forslag-v6.md'), md)
for (const [k, v] of Object.entries(ut)) { const samma = v.letrend_varde.filter(a => v.forvantad_nytta.some(b => b.id === a.id)).length; console.log(`${k}: värde ${v.letrend_varde.map(x => x.id.split('-')[0]).join(', ')} | nytta ${v.forvantad_nytta.map(x => x.id.split('-')[0]).join(', ')} | särskilt ${v.sarskilt.map(x => x.id.split('-')[0]).join(', ')}`) }
