// Harness v5 steg 5 (4 nov 2026): anpassning som anger KÄRNAN och det som bär, inte en scenlista.
// Ägaren om v0-anpassningarna (pass 4–5): inskrivna misstag blir falska, stela repliker ska bort, en
// sketch som passar rekommenderas som den är, skilj på personen som fokus och som behållare, och en
// lista över sekvenser ger lika vikt åt det som inte bär. Doktrinen: format/doktrin.mjs (ANPASSNING).
//
//   node format/h-anpassa5.mjs --konto <konto> --id <klipp-id>   (eller utan argument: Pros förstahandsval ur match5)
// Resultat: data/format/harness/anpassning5/<konto>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
import { LETREND, LINJE, ANPASSNING } from './doktrin.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const H = path.join(DATA, 'format', 'harness'), UT = path.join(H, varde('--ut', 'anpassning5'))
fs.mkdirSync(UT, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description) => ({ type: 'array', items, description })
const schema = obj({
  titel: s('Arbetstitel för kundens version.'),
  varfor_passar: s('Hur klippet fortsätter det kunden redan gör, 1–2 meningar.'),
  karna: s('Kärnan som måste finnas kvar, en mening.'),
  som_den_ar: b('Ska klippet göras som det är, med bara praktiska byten? Sant för en sketch som redan passar kunden.'),
  bar: arr(obj({ vad: s('Det som bär.'), varfor: s('Varför det bär, kort.') }), 'Det som bär idén: beats, en vändning, en replik, en bild. 1–4 st.'),
  fritt: arr(s('En sak.'), 'Det kunden kan göra på sitt eget sätt, improvisera eller stryka. 1–4 st.'),
  person: obj({ funktion: s('fokus: personens karisma bär. behallare: personen framför konceptet. roll: personerna spelar roller.', ['fokus', 'behallare', 'roll']), vem: s('Vem hos kunden, med frontfigurens etikett om det finns en.'), kraver: s('Vad det kräver av personen, en mening.') }),
  byten: arr(s('Ett byte.'), 'Praktiska byten mot kundens produkter, lokal och personer. 1–4 st.'),
  ton: s('Hur det ska låta, i kundens egen röst, en mening.'),
  exempelrepliker: arr(s('En replik.'), 'Högst två repliker som visar tonen. De är exempel, inte manus.'),
  racken: arr(s('En sak.'), 'Det som får idén att tappa sitt värde hos just den här kunden. 1–3 st.'),
  brief: s('Briefen till kunden, 2–4 meningar i du-form, som en CM skulle skicka. Säg varför klippet passar dem och vad som bär. Ingen scenlista.'),
  ratt_om: s('Så vet kunden att det blev rätt, en mening.'),
})

async function anpassa(konto, id) {
  const kf = [path.join(H, 'v5', `${id}.json`), path.join(DATA, 'format', 'e6', 'kort', `${id}.json`)].find(fs.existsSync)
  const L = las(path.join(H, 'linje', `${konto}.json`)), c = las(kf)
  const klipp = { helhet: c.helhet, handling: c.handling, redigeringsskamt: c.redigeringsskamt, karna: c.karna, mall: c.mall, platser: c.platser, beats: c.beats, grundvarde: c.grundvarde, sprak: c.sprak, forlaga: c.forlaga, krav: c.krav, anpassningsrisk: c.anpassningsrisk }
  const linje = { linje: L.linje, strategi: L.strategi, kantighet: L.kantighet, tempo: L.tempo, frontfigurer: L.frontfigurer.map(({ etikett, funktion, styrka }) => ({ etikett, funktion, styrka })), personal_spelar: L.personal_spelar, format: L.format.map(f => f.namn), verksamhet: L.verksamhet, produkter: L.produkter, lokal: L.lokal, sjalvbild: L.sjalvbild, sticker_ut: L.sticker_ut }
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Du är content manager på LeTrend och ska rekommendera biblioteksklippet nedan till kunden @${konto}.

${LETREND}

${LINJE}

${ANPASSNING}

Biblioteksklippet (@${c.konto}):
${JSON.stringify(klipp)}

Kundens linje:
${JSON.stringify(linje)}

Svara på svenska.`
  const r = await analyseraVideo({ fil: path.join(DATA, 'format', 'tom.mp4'), prompt, schema, temperatur: 0.4, modell: 'google/gemini-3.1-pro-preview' })
  const ut = { konto, kalla: id, kallakonto: c.konto, url: c.url, tokens: r.usage?.total_tokens, ...r.data }
  fs.writeFileSync(path.join(UT, `${konto}.json`), JSON.stringify(ut, null, 1))
  console.log(`${konto}: ${r.data.titel} (@${c.konto}, ${r.usage?.total_tokens} tokens)`)
}

if (varde('--konto')) await anpassa(varde('--konto'), varde('--id'))
else for (const f of fs.readdirSync(path.join(H, 'match5'))) {
  const m = las(path.join(H, 'match5', f)); if (!m.pro || fs.existsSync(path.join(UT, f))) continue
  const forsta = [...m.pro].sort((a, b) => b.passform - a.passform)[0]
  await anpassa(m.konto, forsta.id)
}
