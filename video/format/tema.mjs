// Temalagret (4 nov 2026): fyller bristen att kantighet inte fångar vuxna teman (relation, partner, alkohol,
// anspelningar). Ägaren i pass 4: vuxna parteman passar inte en familjär kund (anettesrestaurang). Textkedja
// ovanpå v5-korten (helhet, handling, kärna), 12 klipp per anrop. Inga videor skickas.
//   LOVABLE_KONTO=4 node format/tema.mjs [--modell google/gemini-3.8-flash]
// Resultat: data/format/harness/tema.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), UT = path.join(H, 'tema.json'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const DIRS = ['harness/v5', 'e6/kort', 'e6r/kort', 'bank2/kort', 'bank3/kort'].map(d => path.join(F, d))
const kortFil = id => DIRS.map(d => path.join(d, `${id}.json`)).find(fs.existsSync)
const B = las(path.join(H, 'bibliotek-v6.json')).hyllor
const ids = ['karna', 'mitten', 'situation'].flatMap(h => (B[h] ?? []).map(x => x.id))
const res = fs.existsSync(UT) ? las(UT) : {}
const kvar = ids.filter(id => !res[id])
const TEMAN = ['vardag', 'jobbet', 'relation_romantik', 'alkohol_fest', 'anspelning', 'mork_humor', 'familj_barn', 'mat']
const s = (d, e) => ({ type: 'string', description: d, ...(e ? { enum: e } : {}) }), b = d => ({ type: 'boolean', description: d })
const obj = p => ({ type: 'object', properties: p, required: Object.keys(p), additionalProperties: false })
for (let i = 0; i < kvar.length; i += 12) {
  const g = kvar.slice(i, i + 12), koder = g.map((_, j) => `K${j + 1}`), kort = g.map(id => las(kortFil(id)))
  const schema = obj({ bedomning: { type: 'array', minItems: g.length, maxItems: g.length, items: obj({ kod: s('', koder), tema: s('Klippets huvudtema.', TEMAN), vuxet: b('Bygger skämtet eller poängen på ett vuxet tema: dejting, partner och relationer, sex eller anspelningar, alkohol och fylla, eller mörk humor som inte passar barn?'), familjevanligt: b('Skulle klippet fungera hos en familjär verksamhet med barn i bild, utan att poängen går förlorad?') }) } })
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Bedöm temat i varje TikTok-klipp nedan utifrån beskrivningen. Svara på svenska.\n\n${kort.map((c, j) => `K${j + 1} ${JSON.stringify({ helhet: c.helhet, handling: c.handling, karna: c.karna })}`).join('\n')}`
  try {
    const r = await analyseraVideo({ fil: path.join(F, 'tom.mp4'), prompt, schema, temperatur: 0.1, modell: varde('--modell', 'google/gemini-3.8-flash') })
    for (const x of r.data.bedomning) { const id = g[koder.indexOf(x.kod)]; if (id) res[id] = { tema: x.tema, vuxet: x.vuxet, familjevanligt: x.familjevanligt } }
    fs.writeFileSync(UT, JSON.stringify(res, null, 1))
  } catch (e) { console.warn(e.message.slice(0, 200)); if (/ 402:/.test(e.message)) break }
  if ((i / 12) % 10 === 0) console.log(`${Math.min(i + 12, kvar.length)}/${kvar.length}`)
}
const v = Object.values(res); console.log(`${v.length} klipp: vuxet ${v.filter(x => x.vuxet).length}, inte familjevänligt ${v.filter(x => !x.familjevanligt).length}`)
