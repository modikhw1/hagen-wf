// Harness steg 4b (4 nov 2026): Pro rangordnar de klipp som klarat grindarna för en kund, som en CM
// skulle göra. Pro tittar på ton, persona, produkter, kundens befintliga format, frontfigurer och luckor.
// Text på en tom platshållare.
//   node format/h-rerank.mjs
// Resultat: data/format/harness/rerank/<konto>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'

const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), UT = path.join(H, 'rerank')
fs.mkdirSync(UT, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const v4 = id => las(path.join(H, 'v4', `${id}.json`))
const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })

for (const f of fs.readdirSync(path.join(H, 'match'))) {
  const { konto, profil, resultat } = las(path.join(H, 'match', f))
  const ut = path.join(UT, f)
  if (fs.existsSync(ut)) { console.log(`${konto}: finns`); continue }
  // Högst 25 kandidater (bäst efter grindar och mjuk passform), eftersom prompten får vara högst 20 000 tecken.
  const kand = resultat.filter(r => r.godkand).slice(0, 25)
  const koder = kand.map((r, i) => ({ kod: `K${i + 1}`, id: r.id }))
  let lista = kand.map((r, i) => { const k = v4(r.id); return `K${i + 1} [${r.zon}/${k.funktion}] ${k.karna} Kräver: ${k.krav.roller.join(', ')}; skådespel ${k.krav.skadespel}; efterarbete ${k.krav.redigering}; lokal ${k.krav.lokal.join('/')}; produkt ${k.krav.produkt}${k.krav.produkt_typ !== 'ingen' ? ` (${k.krav.produkt_typ})` : ''}; situation ${k.krav.situation}; ljud ${k.krav.ljud}. Risk: ${k.anpassningsrisk.slice(0, 90)}` }).join('\n')
  const schema = obj({
    rangordning: { type: 'array', minItems: Math.min(6, kand.length), maxItems: Math.min(6, kand.length), items: obj({ kod: s('Klippets kod.', koder.map(k => k.kod)), passform: n(1, 5, 'Hur väl klippet passar just den här kunden. 5 = ett självklart nästa klipp.'), roll_for_frontfigur: s('Vilken roll kundens frontfigur tar, eller "ingen frontfigur".'), skal: s('Varför det passar kunden, med koppling till ton, produkter, format eller luckor. En mening.') }), description: 'De bästa klippen för kunden, bäst först. Undvik två klipp med nästan samma idé.' },
    mix: s('Hur de valda klippen tillsammans fyller kundens luckor, en mening.'),
  })
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Du är content manager på LeTrend. Välj de klipp ur biblioteket som passar kunden @${konto} bäst som nästa klipp att spela in. Alla kandidater nedan är redan genomförbara för kunden.

Kundprofil:
${JSON.stringify(profil)}

Det LeTrend vet: klipp med kundens återkommande person och i återkommande format når cirka 30 % längre. Personer, humor och direkt tilltal ger räckvidd. Frågor till publiken, som tävling, uppmaning och erbjudande, ger kommentarer. En matvisning behöver en person i bild och eget ljud, inte trendljud.

Kandidater:
${lista}

Välj efter hur väl klippet passar just den här kundens ton, persona, produkter, lokal, frontfigurer och luckor, inte efter hur bra det är i allmänhet. Svara på svenska.`
  const r = await analyseraVideo({ fil: path.join(F, 'tom.mp4'), prompt, schema, temperatur: 0.2, modell: 'google/gemini-3.1-pro-preview' })
  const rang = r.data.rangordning.map(x => ({ ...x, id: koder.find(k => k.kod === x.kod)?.id }))
  fs.writeFileSync(ut, JSON.stringify({ konto, kandidater: kand.length, tokens: r.usage?.total_tokens, rangordning: rang, mix: r.data.mix }, null, 1))
  console.log(`${konto}: ${kand.length} kandidater, ${r.usage?.total_tokens} tokens. ${rang.map(x => `${x.passform}:${v4(x.id).konto}`).join(', ')}`)
}
