// Harness steg 4c och 5 (4 nov 2026): valideringsurval, förregistrering och anpassningar.
// Per kund sex klipp i blind, slumpad ordning:
//   R = Pros två högst rankade (rerank)
//   D = de två bästa efter grindar och mjuk passform (deterministiskt), som inte finns i R, från olika konton
//   L = två lockklipp: klarar grindarna men rankas lägst och finns inte bland Pros sex. När det inte räcker
//       tas klipp som föll på en grind men inte är ute.
// För Pros förstahandsval skriver Pro en anpassning till kunden: roller, scener, repliker och en brief.
// Förregistreringen ligger i data/format/harness/validering/forregistrering.json.
//   node format/h-valid.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'

const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), V = path.join(H, 'validering')
fs.mkdirSync(V, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const v4 = id => las(path.join(H, 'v4', `${id}.json`))
let fro = 1104; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }

const reg = path.join(V, 'forregistrering.json')
if (!fs.existsSync(reg)) fs.writeFileSync(reg, JSON.stringify({
  last: new Date().toISOString() + ' (innan ägaren sett någon matchning)',
  design: 'Per kund 6 klipp: 2 R (Pros rerank), 2 D (deterministisk matchning), 2 L (lockklipp). Blind ordning. Ägaren ger passform 1–5 för just den kunden och svarar om hen skulle rekommendera klippet.',
  HM1: 'Medelpassform för R och D är högre än för L. Parvis inom kund, permutation av etiketterna inom kund, ensidigt p < 0,05.',
  HM2: 'Medelpassform för R är högre än för D. Samma test.',
  HM3: 'Ägarens passform korrelerar positivt med Pros passform (Spearman) över de klipp där Pros passform finns.',
  HM4: 'Pros anpassning av förstahandsvalet bedöms som skicka som den är eller med små ändringar för minst 4 av 6 kunder.',
}, null, 1))

const urval = {}
for (const f of fs.readdirSync(path.join(H, 'match'))) {
  const { konto, profil, resultat } = las(path.join(H, 'match', f))
  const rr = las(path.join(H, 'rerank', f)).rangordning
  const R = rr.slice(0, 2).map(x => x.id)
  const D = []
  for (const r of resultat.filter(r => r.godkand)) { if (D.length >= 2) break; if (R.includes(r.id) || D.some(id => v4(id).konto === r.konto)) continue; D.push(r.id) }
  const topp6 = new Set(rr.map(x => x.id))
  const L = []
  for (const r of [...resultat.filter(r => r.godkand)].reverse()) { if (L.length >= 2) break; if (topp6.has(r.id) || R.includes(r.id) || D.includes(r.id) || L.some(id => v4(id).konto === r.konto)) continue; L.push(r.id) }
  for (const r of resultat.filter(r => !r.godkand && r.zon !== 'ute')) { if (L.length >= 2) break; if ([...R, ...D, ...L].includes(r.id)) continue; L.push(r.id) }
  const klipp = bl([...R.map(id => ({ id, grupp: 'R' })), ...D.map(id => ({ id, grupp: 'D' })), ...L.map(id => ({ id, grupp: 'L' }))])
    .map((k, i) => { const c = v4(k.id), m = resultat.find(r => r.id === k.id), x = rr.find(r => r.id === k.id); return { ...k, pos: i + 1, url: c.url, konto: c.konto, karna: c.karna, handling: c.handling, pro_passform: x?.passform ?? null, pro_skal: x?.skal ?? null, frontfigur_roll: x?.roll_for_frontfigur ?? null, grind: m?.grind ?? [], skal: m?.skal ?? [] } })
  urval[konto] = { profil, klipp }
}
const ufil = path.join(V, 'urval.json')
if (!fs.existsSync(ufil)) fs.writeFileSync(ufil, JSON.stringify(urval, null, 1))
const U = las(ufil)

// Anpassningar för Pros förstahandsval.
const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description) => ({ type: 'array', items, description })
const schema = obj({
  titel: s('Arbetstitel för kundens version.'),
  ide: s('Idén i kundens version, en mening.'),
  roller: arr(obj({ roll: s('Rollen.'), vem: s('Vem hos kunden som spelar den, med frontfigurens etikett om det finns en.') }), 'Rollerna.'),
  scener: arr(obj({ nr: { type: 'integer' }, sekunder: s('Ungefärlig längd, t.ex. "0–3".'), vad: s('Vad som händer och syns.'), replik: s('Det som sägs eller står i skärmtext, ordagrant, eller "ingen".'), bild: s('Hur det filmas: utsnitt, vinkel, var i lokalen.') }), '2–6 scener.'),
  byts: arr(s('En sak.'), 'Det som byts mot kundens personer, produkter och lokal.'),
  behalls: arr(s('En sak.'), 'Det som måste behållas för att idén ska fungera.'),
  brief: s('Briefen till kunden, 2–4 meningar i du-form, som en CM skulle skicka.'),
  ratt_om: s('Så vet kunden att det blev rätt, en mening.'),
})
const AU = path.join(V, 'anpassning')
fs.mkdirSync(AU, { recursive: true })
for (const [konto, { profil }] of Object.entries(U)) {
  const f = path.join(AU, `${konto}.json`)
  if (fs.existsSync(f)) continue
  const forsta = las(path.join(H, 'rerank', `${konto}.json`)).rangordning[0]
  const c = v4(forsta.id)
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Du är content manager på LeTrend. Anpassa biblioteksklippet nedan till kunden @${konto}, så att kundens egen personal kan spela in det med en telefon. Använd kundens frontfigur, produkter och lokal. Behåll det som bär idén.

Biblioteksklippet (@${c.konto}):
${JSON.stringify({ handling: c.handling, redigeringsskamt: c.redigeringsskamt, karna: c.karna, mall: c.mall, platser: c.platser, krav: c.krav, anpassningsrisk: c.anpassningsrisk })}

Kundprofil:
${JSON.stringify(profil)}

Varför klippet valdes: ${forsta.skal} Frontfigurens roll: ${forsta.roll_for_frontfigur}.

Det LeTrend vet: klipp med kundens återkommande person når längre, och en matvisning behöver en person i bild och eget ljud. Skriv konkret, med riktiga repliker. Svara på svenska.`
  const r = await analyseraVideo({ fil: path.join(F, 'tom.mp4'), prompt, schema, temperatur: 0.4, modell: 'google/gemini-3.1-pro-preview' })
  fs.writeFileSync(f, JSON.stringify({ konto, kalla: forsta.id, kallakonto: c.konto, tokens: r.usage?.total_tokens, ...r.data }, null, 1))
  console.log(`${konto}: anpassning av @${c.konto} (${r.usage?.total_tokens} tokens): ${r.data.titel}`)
}
for (const [konto, { klipp }] of Object.entries(U)) console.log(`${konto}: ${klipp.map(k => `${k.pos}:${k.grupp}@${k.konto}`).join(' ')}`)
