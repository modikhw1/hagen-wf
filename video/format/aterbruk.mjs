// Återbruk och unika drag för bibliotek v6 (6 nov 2026). Förregistrering: data/format/aterbruk/forregistrering.json
//   LOVABLE_KONTO=5 node format/aterbruk.mjs [--samtidigt 10]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const F = path.join(DATA, 'format', 'aterbruk'), SATS = path.join(F, 'sats'); fs.mkdirSync(SATS, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const B = las(path.join(DATA, 'format', 'harness', 'bibliotek-v6.json')), kort = []
;(function w(o) { if (Array.isArray(o)) o.forEach(w); else if (o && typeof o === 'object') { if (o.id && 'nytta_v62' in o) kort.push(o); else Object.values(o).forEach(w) } })(B)
const urval = kort.filter(k => ['karna', 'mitten', 'situation'].includes(k.hylla)).sort((a, b) => a.id.localeCompare(b.id))
const satser = []; for (let i = 0; i < urval.length; i += 40) satser.push(urval.slice(i, i + 40))
const schema = { type: 'object', properties: { klipp: { type: 'array', items: { type: 'object', properties: { nr: { type: 'integer' }, aterbruk: { type: 'string', enum: ['premiss', 'ryggrad', 'bada', 'inget'] }, unika_drag: { type: 'boolean' } }, required: ['nr', 'aterbruk', 'unika_drag'], additionalProperties: false } } }, required: ['klipp'], additionalProperties: false }
async function klassa(n) {
  const ut = path.join(SATS, `${n}.json`); if (fs.existsSync(ut)) return
  const ks = satser[n]
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Nedan finns ${ks.length} TikTok-klipp ur ett bibliotek som en content manager rekommenderar till andra restauranger, barer och kaféer, som gör egna versioner. För varje klipp:
- aterbruk: vad som följer med till en annan verksamhet. premiss = skämtet eller situationen och dess vändning (en sketch kan göras om med andra personer). ryggrad = scenföljd, tempo och komposition, medan innehållet byts (tilltal, visning, tillagning, intervju, montage). bada = båda. inget = bara produkten, erbjudandet eller eventet; inget går att föra vidare.
- unika_drag: true om klippets värde hänger på drag hos just den personen, platsen eller produkten (en viss persons karisma eller personlighet, en unik lokal eller vy, ett eget erbjudande, planerade kvicka svar) som inte följer med till en annan kund. false om en vanlig personal kan bära det.

Klipp:
${ks.map((k, i) => `${i + 1}. ${k.karna} | mall: ${k.mall} | strategi ${k.strategi}, person ${k.person}`).join('\n')}`
  const r = await analyseraVideo({ fil: path.join(DATA, 'format', 'tom.mp4'), prompt, schema, temperatur: 0, modell: 'google/gemini-3.8-flash' })
  const m = {}; for (const x of r.data.klipp) if (ks[x.nr - 1]) m[ks[x.nr - 1].id] = { aterbruk: x.aterbruk, unika_drag: x.unika_drag }
  fs.writeFileSync(ut, JSON.stringify({ tokens: r.usage?.total_tokens, klipp: m }))
}
let nasta = 0, fel = 0
const arb = async () => { while (nasta < satser.length) { const n = nasta++; try { await klassa(n) } catch (e) { fel++; console.log(`sats ${n}: ${e.message.slice(0, 160)}`) } } }
await Promise.all(Array.from({ length: +varde('--samtidigt', 10) }, arb))
const allt = {}; for (const f of fs.readdirSync(SATS)) Object.assign(allt, las(path.join(SATS, f)).klipp)
fs.writeFileSync(path.join(F, 'aterbruk.json'), JSON.stringify(allt))
console.log(`${urval.length} kort i ${satser.length} satser; klassade ${Object.keys(allt).length}, ${fel} fel`)
