// Formatkort: läser ut klippets IDÉ skild från utförandet och från verksamheten, så att en CM kan
// anpassa den till en annan verksamhet. Pilot 3 nov 2026 för att forma harnessen (se
// karta/videoforandring/harness.md). Via Lovable AI (typer/lovable.mjs).
//
//   node format/kort.mjs --modell google/gemini-3.1-pro-preview <id> <id> …
// Resultat: data/format/<modell>/<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v }
const MODELL = varde('--modell', 'google/gemini-3.1-flash-lite')
const PAR = Number(varde('--par', 6))
process.env.LOVABLE_MODELL = MODELL
const { analyseraVideo } = await import('../typer/lovable.mjs')

const UT = path.join(DATA, 'format', MODELL.replace(/\//g, '_'))
fs.mkdirSync(UT, { recursive: true })
const kallor = JSON.parse(fs.readFileSync(path.join(DATA, 'kallor.json'), 'utf8'))

const s = (description, extra = {}) => ({ type: 'string', description, ...extra })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description) => ({ type: 'array', items, description })

const INBJUDAN = ['igenkanning', 'overraskning', 'insyn', 'personlighet', 'begar', 'erbjudande', 'nyfikenhet', 'deltagande']
const VERKSAMHETER = ['kafe', 'pizzeria_kebab', 'finare_restaurang', 'bar', 'butik']

export const schema = obj({
  handling: s('Vad som händer, i ordning, 1–3 meningar.'),
  karna: s('Idén i en mening, utan verksamhetens namn, rätter eller personer: vad gör klippet sevärt?'),
  mall: s('Idén som återanvändbar mall med [platshållare], t.ex. "[en anställd] serverar [två produkter som ser lika ut] och blandar ihop dem".'),
  platser: arr(obj({ plats: s('Platshållarens namn.'), har: s('Vad den är i det här klippet.'), annan: s('Ett exempel på vad den kan vara hos en helt annan sorts verksamhet.') }), 'Det som kan bytas ut. 1–5 st.'),
  last: arr(s('En sak.'), 'Det som måste finnas kvar för att idén ska fungera. 1–4 st.'),
  vardet: obj({
    ide: n(0, 100, 'Andel av klippets dragningskraft som kommer från idén, manuset eller vändningen.'),
    framforande: n(0, 100, 'Från personernas timing, karisma eller skådespel.'),
    produktion: n(0, 100, 'Från foto, ljus, klippning eller effekter.'),
    produkt: n(0, 100, 'Från maten, varan eller lokalen i sig.'),
    trend: n(0, 100, 'Från ett trendljud, en meme eller ett känt format.'),
  }),
  inbjudan: s('Främsta skälet att tittaren stannar: igenkanning (känner igen situationen), overraskning (humor, vändning), insyn (bakom kulisserna), personlighet (personerna själva), begar (vill äta/ha), erbjudande (pris, nyhet, info), nyfikenhet (vill se hur det slutar), deltagande (gissa, svara, tävla).', { enum: INBJUDAN }),
  inbjudan_2: s('Näst främsta skälet.', { enum: INBJUDAN }),
  salj: s('Hur verksamheten säljs: ingen (syns inte), fond (syns naturligt i bakgrunden), vavd (produkten är del av poängen), direkt (visning, erbjudande, uppmaning).', { enum: ['ingen', 'fond', 'vavd', 'direkt'] }),
  produktionskrav: n(1, 5, '1 = en telefon, en tagning, inget redigerat. 3 = några klipp, enkel text. 5 = flera vinklar, ljussättning, avancerad klippning eller effekter.'),
  tankehojd: n(1, 5, '1 = filmar det som ändå händer eller bara visar produkten. 3 = en enkel idé. 5 = genomtänkt idé med uppbyggnad och vändning.'),
  trend: s('egen (egen idé), anpassad_trend (känt format eller ljud med egen vinkel), ren_trend (trenden gjord rakt av).', { enum: ['egen', 'anpassad_trend', 'ren_trend'] }),
  personer: n(0, 10, 'Hur många personer som behövs för att spela in idén.'),
  agerande: n(1, 5, '1 = ingen behöver spela något. 3 = enkel replik eller reaktion. 5 = kräver skådespelartalang eller exakt timing.'),
  overforing: arr(obj({
    verksamhet: s('Typ av verksamhet.', { enum: VERKSAMHETER }),
    passar: n(1, 5, 'Hur väl idén fungerar där utan att tappa poängen.'),
    version: s('Hur idén blir där, en mening.'),
  }), `En rad för var och en av: ${VERKSAMHETER.join(', ')}.`),
  serie: obj({ kan_bli_serie: { type: 'boolean', description: 'Kan bli ett återkommande inslag med nya varianter.' }, hur: s('Hur, en mening.') }),
  svaghet: s('Det som gör klippet mindre användbart som mall för andra verksamheter.'),
})

const prompt = konto => `Ett TikTok-klipp från @${konto}.

Syftet är att förstå klippets IDÉ, så att en content manager kan anpassa den till en annan verksamhet. Den verksamhetens egen personal spelar sedan in sin version med en telefon.

Skilj på tre saker:
- idén: det som går att ta med sig
- utförandet: personerna, fotot och klippningen
- det som bara gäller just den här verksamheten

Var konkret och nykter, och skriv inte som en säljare. Bedöm det du ser och hör, inte det du gissar. Svara på svenska.`

const ids = args.filter(a => !a.startsWith('--'))
let i = 0
await Promise.all(Array.from({ length: Math.min(PAR, ids.length) }, async () => {
  while (i < ids.length) {
    const id = ids[i++]
    const k = kallor[id]
    const ut = path.join(UT, `${id}.json`)
    if (fs.existsSync(ut)) continue
    try {
      const t0 = Date.now()
      const r = await analyseraVideo({ fil: k.fil, prompt: prompt(k.konto), schema, temperatur: 0.2 })
      fs.writeFileSync(ut, JSON.stringify({ id, konto: k.konto, modell: r.modell, tokens: r.usage?.total_tokens, ms: Date.now() - t0, ...r.data }, null, 1))
      console.log(`${id}: ok ${((Date.now() - t0) / 1000).toFixed(1)} s`)
    } catch (e) { console.warn(`${id}: ${e.message.slice(0, 300)}`) }
  }
}))
