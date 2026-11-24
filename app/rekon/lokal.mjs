// Lokalen: Gemini lägger ut miljön (inte personerna) i en nyckelbild per scen, som rutor i bilden
// med form, kategori, färg, material, placering och ungefärlig storlek i meter. Lyftet till 3D görs
// i manus.mjs, som känner kamerans höjd och lutning. Sparas i data/rekon/<id>/lokal-2d.json.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { generera } from '../typer/gemini.mjs'
import { rutor, RUTOR, FPS } from './delat.mjs'

const MODELL = process.env.REKON_MODELL ?? 'gemini-3-flash-preview'
const REKON = path.join(DATA, 'rekon')
const lasJson = f => (fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null)

export const KATEGORIER = ['disk', 'bord', 'stol', 'hylla', 'skap', 'skylt', 'skarm', 'meny', 'lampa', 'flaska', 'burk', 'vaxt', 'apparat', 'kassa', 'dorr', 'fonster', 'tavla', 'pelare', 'balk', 'kakel', 'ovrigt']
export const PLACERING = ['golv', 'vagg', 'tak', 'pa_element', 'fritt']

const schema = {
  type: 'object',
  properties: {
    golv: { type: 'object', properties: { farg: { type: 'string' }, material: { type: 'string', enum: ['kakel', 'tra', 'sten', 'betong', 'matta'] }, synligt: { type: 'boolean' } }, required: ['farg', 'material', 'synligt'] },
    vagg: { type: 'object', properties: { farg: { type: 'string' }, material: { type: 'string', enum: ['puts', 'kakel', 'tegel', 'tra', 'panel', 'glas'] }, avstand: { type: 'number', description: 'ungefärligt avstånd från kameran till bakväggen i meter' } }, required: ['farg', 'material', 'avstand'] },
    element: {
      type: 'array', // maxItems här gör schemat för stort för Vertex (400); taket står i prompten
      items: {
        type: 'object',
        properties: {
          namn: { type: 'string', description: 'kort beskrivning, t.ex. "disk med granitskiva"' },
          kategori: { type: 'string', enum: KATEGORIER },
          ruta: { type: 'array', items: { type: 'integer' }, minItems: 4, maxItems: 4, description: '[ymin, xmin, ymax, xmax] i 0–1000 av bilden, den synliga delen' },
          form: { type: 'string', enum: ['lada', 'platta', 'cylinder', 'klot'] },
          farg: { type: 'string', description: 'dominerande färg som hex, som den ser ut i bilden' },
          material: { type: 'string', enum: ['tra', 'sten', 'kakel', 'puts', 'tegel', 'metall', 'glas', 'plast', 'tyg', 'ovrigt'] },
          lyser: { type: 'boolean', description: 'neonskylt, skärm eller lampa som lyser' },
          placering: { type: 'string', enum: PLACERING, description: 'golv: står på golvet; vagg: sitter på bakväggen; tak: hänger från taket; pa_element: står på ett annat element (t.ex. flaskor på disken); fritt: annat' },
          pa: { type: 'integer', description: 'index (0-baserat) för elementet det står på, om placering är pa_element' },
          storlek: { type: 'array', items: { type: 'number' }, minItems: 3, maxItems: 3, description: '[bredd, höjd, djup] i meter, hela föremålet även om det är delvis dolt' },
          framfor_personer: { type: 'boolean', description: 'står mellan kameran och någon person och skymmer delar av den' },
        },
        required: ['namn', 'kategori', 'ruta', 'form', 'farg', 'material', 'lyser', 'placering', 'storlek', 'framfor_personer'],
      },
    },
  },
  required: ['golv', 'vagg', 'element'],
}

const PROMPT = `Bilden är en ruta ur ett TikTok-klipp, filmat med mobil i stående format. Vi bygger upp miljön som enkel 3D (lådor, plattor, cylindrar) för att kunna filma om scenen från andra vinklar.

Lägg ut miljön, inte personerna: golvet, bakväggen och de föremål som tar plats i bilden eller som skymmer personer (disk, bord, hyllor, skyltar, skärmar, lampor, flaskor, apparater …). Ta med det som ger rummet dess utseende, högst 30 element, störst först. Ta inte med sådant som personerna håller i händerna (brickor, koppar, telefoner, mat de håller fram). Rutan är den synliga delen i bilden. Storleken är föremålets hela storlek i meter. Färgen som den ser ut i bilden (med ljuset).`

export async function stegLokal(id, om) {
  const ut = path.join(REKON, id, 'lokal-2d.json')
  if (!om && fs.existsSync(ut)) return
  const analys = lasJson(path.join(DATA, 'analys', `${id}.json`))
  const ramar = await rutor(id)
  let ore = 0
  const scener = []
  for (const s of analys.scener) {
    // nyckelbilden: strax efter scenens början (kameran har inte hunnit röra sig, se manus.mjs)
    const k = Math.min(ramar.length - 1, Math.round(s.start * FPS) + 2)
    const bild = fs.readFileSync(path.join(RUTOR, id, ramar[k])).toString('base64')
    const r = await generera({ modell: MODELL, parts: [{ inlineData: { mimeType: 'image/jpeg', data: bild } }, { text: PROMPT }], schema, temperatur: 0.1, tankande: 'low' })
    ore += r.ore ?? 0
    scener.push({ ruta: k, ...r.data })
  }
  fs.mkdirSync(path.dirname(ut), { recursive: true })
  fs.writeFileSync(ut, JSON.stringify({ id, modell: MODELL, ore, scener }, null, 1))
  console.log(`  lokal: ${scener.map(s => s.element.length).join('+')} element · ${ore.toFixed(1)} öre`)
}
