// Pass 8, version 3 (6 nov 2026): anpassningens form enligt ägarens regler från pass 8 del 1 (kund A).
// Förregistrering: data/format/harness/pass8/forregistrering-v3.json. Pro får samma v5-kort och kundlinje
// som v5 och v0, men inte de versionerna.
//   LOVABLE_KONTO=5 node format/h-anpassa8.mjs [--kund <konto>]
// Resultat: data/format/harness/pass8/v3/<kund>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
import { LETREND, LINJE } from './doktrin.mjs'

const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const H = path.join(DATA, 'format', 'harness'), UT = path.join(H, 'pass8', 'v3')
fs.mkdirSync(UT, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description) => ({ type: 'array', items, description })

export const FORM8 = `Så skriver LeTrend en anpassning (ägarens regler, 6 nov):
- Fånga kärnan: det underliggande som gör klippet rekommenderbart, i en mening.
- Avgör vad som återanvänds. En premissketch återanvänds genom premissen: skriv de repliker som bär skämtet ordagrant och lämna resten fritt. Ett ryggradsklipp (tilltal, visning, tillagning, intervju) återanvänds genom ryggraden: scenföljd, tempo och komposition. Där skrivs inga repliker, utan vad personen ska göra och säga i stort ("beskriv vad du gör medan du gör det").
- Ge scenerna i ordning. Varje scen säger vad den måste åstadkomma ("pointedness") och hur bilden ser ut. Scener som inte bär får vara korta och fria.
- Inga tidsstämplar och inga sekunder. Varje scen tar den tid repliken behöver, men varje replik ska ha ett syfte: tight, inget prat mellan stegen.
- Säg inte det självklara. Skriv inte att drinken byts mot pizza hos en pizzeria; kunden förstår att mallen görs med deras egna saker. Nämn bara byten som inte är självklara.
- Instruera inte personlighet ("var goofy", "var karismatisk"). Om förlagan bärs av personliga drag (missar, slarv, upptåg) blir de en tillåtelse: om det händer, lämna kvar, men tvinga inget. Skriv aldrig in misstag: ingen scen får be personen göra fel. Skriv villkorat, "om något går fel, ...".
- För mycket instruktion gör det stelt och mindre spontant; för lite gör att kunden svävar ut. Sikta på balansen: tydlig struktur, fria ord.
- Briefen är en guide i du-form, 2–3 meningar, som säger varför klippet passar kunden.`

const schema = obj({
  titel: s('Arbetstitel för kundens version.'),
  karna: s('Kärnan, en mening.'),
  aterbruk: s('Vad som återanvänds: premiss (skämtet och dess repliker), ryggrad (scenföljd, tempo, komposition) eller bada.', ['premiss', 'ryggrad', 'bada']),
  scener: arr(obj({
    vad: s('Vad scenen måste åstadkomma, en kort mening som börjar med ett verb.'),
    bild: s('Hur bilden ser ut, kort.'),
    replik: s('Repliken ordagrant BARA om den bär skämtet eller premissen, annars tom sträng.'),
    atgard: s('behall: som i förlagan. byt: något icke självklart byts. eget_tal: personen säger det med egna ord. forenkla: enklare än förlagan. tillat: förlagans personliga drag, tillåt men tvinga inte. fritt: kunden gör som hen vill eller stryker.', ['behall', 'byt', 'eget_tal', 'forenkla', 'tillat', 'fritt']),
  }), 'Scenerna i ordning, 2–6 st.'),
  tight: s('Hur kunden håller klippet tight, en mening, utan tider.'),
  tillat: arr(s('En sak.'), 'Förlagans personliga drag som tillåts men inte tvingas. 0–3 st.'),
  undvik: arr(s('En sak.'), 'Det som får idén att tappa värdet hos kunden. 1–3 st.'),
  brief: s('Briefen till kunden, 2–3 meningar i du-form.'),
  ratt_om: s('Så vet kunden att det blev rätt, en mening.'),
})

async function anpassa(kund, kalla) {
  const c = las(path.join(H, 'v5', `${kalla}.json`)), L = las(path.join(H, 'linje', `${kund}.json`))
  const klipp = { helhet: c.helhet, handling: c.handling, redigeringsskamt: c.redigeringsskamt, karna: c.karna, mall: c.mall, platser: c.platser, beats: c.beats, grundvarde: c.grundvarde, sprak: c.sprak, forlaga: c.forlaga, krav: c.krav, anpassningsrisk: c.anpassningsrisk }
  const linje = { linje: L.linje, strategi: L.strategi, kantighet: L.kantighet, tempo: L.tempo, frontfigurer: L.frontfigurer.map(({ etikett, funktion, styrka }) => ({ etikett, funktion, styrka })), personal_spelar: L.personal_spelar, format: L.format.map(f => f.namn), verksamhet: L.verksamhet, produkter: L.produkter, lokal: L.lokal, sjalvbild: L.sjalvbild, sticker_ut: L.sticker_ut }
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Du är content manager på LeTrend och ska rekommendera biblioteksklippet nedan till kunden @${kund}.

${LETREND}

${LINJE}

${FORM8}

Biblioteksklippet (@${c.konto}):
${JSON.stringify(klipp)}

Kundens linje:
${JSON.stringify(linje)}

Svara på svenska.`
  const r = await analyseraVideo({ fil: path.join(DATA, 'format', 'tom.mp4'), prompt, schema, temperatur: 0.4, modell: 'google/gemini-3.1-pro-preview' })
  fs.writeFileSync(path.join(UT, `${kund}.json`), JSON.stringify({ kund, kalla, kallakonto: c.konto, url: c.url, tokens: r.usage?.total_tokens, ...r.data }, null, 1))
  console.log(`${kund}: ${r.data.titel} (${r.data.aterbruk}, ${r.usage?.total_tokens} tokens)`)
}

const R = las(path.join(H, 'pass8', 'forregistrering.json')).rader
const valda = varde('--kund') ? R.filter(r => r.kund === varde('--kund')) : R
// B–F först (testet), A sist (sedd, för jämförelse med handskrivet utkast)
const ordning = [...valda.filter(r => r.kund !== 'pizzeriamums'), ...valda.filter(r => r.kund === 'pizzeriamums')]
await Promise.all(ordning.filter(r => !fs.existsSync(path.join(UT, `${r.kund}.json`))).map(r => anpassa(r.kund, r.kalla).catch(e => console.log(`${r.kund}: FEL ${e.message}`))))
