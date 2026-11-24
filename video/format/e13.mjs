// E13 (16 nov 2026): stark serieläsning. En videomodell läser kundens historik som video (inte som Lite-typer
// eller textlinje) och bedömer passformen för ett kandidatklipp, så som ägaren gör. Förregistrering:
// data/format/e13/forregistrering.json. Klippen hämtas och skalas ned av format/e13-hamta.mjs.
//   LOVABLE_KONTO=beacon node format/e13.mjs --steg profil|b1|b2 [--modell google/gemini-3.1-pro-preview]
//       [--kalla pass45,pass6 | serie9] [--kund a,b] [--par 4] [--max n]
// Resultat: data/format/e13/profil-<m>/<konto>.json och data/format/e13/<steg>-<m>/<konto>__<id>.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'
import { LETREND, LINJE, GRUNDVARDE } from './doktrin.mjs'
import os from 'node:os'
import { byggBand, bandDelar } from './e13-band.mjs'

const litenFil = id => path.join(os.homedir(), 'Downloads', 'letrend-e13', id + '.mp4')
const delaId = id => { const i = id.lastIndexOf('-'); return { konto: id.slice(0, i), video: id.slice(i + 1) } }

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const STEG = varde('--steg', 'b2'), MODELL = varde('--modell', 'google/gemini-3.1-pro-preview'), PAR = Number(varde('--par', 4)), MAX = Number(varde('--max', 1e9))
const KALLOR = varde('--kalla', 'pass45,pass6').split(','), KUNDER = varde('--kund')?.split(',')
const mkort = MODELL.replace(/^google\/gemini-/, '').replace(/-preview$/, '')
// --etikett r2: en andra körning av samma läsare hamnar i <steg>-<m>-r2 (brus mellan körningar)
const ETIKETT = varde('--etikett') ? `-${varde('--etikett')}` : ''
const E = path.join(DATA, 'format', 'e13'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const PLAN = las(path.join(E, 'plan.json'))
const obj = (properties, description) => ({ type: 'object', properties, required: Object.keys(properties), ...(description ? { description } : {}) })
const s = (description, en) => ({ type: 'string', description, ...(en ? { enum: en } : {}) })
const VISAT = ['visat_ofta', 'visat_nagon_gang', 'aldrig']

const profilSchema = obj({
  helhet: s('Vad är det här för konto, sett som en serie? Tre till fem meningar.'),
  faser: { type: 'array', description: 'Seriens faser i tidsordning, äldst först. En fas är en period där kontot gör ungefär samma sak.', items: obj({ period: s('Ungefär från–till.'), gor: s('Vad kontot gör i fasen: format, vem som syns, ton.'), klipp: s('Vilka klippnummer som hör hit.') }) },
  nu: s('Vad kontot gör just nu (de senaste klippen) och vart det verkar vara på väg.'),
  format: { type: 'array', description: 'De återkommande formaten i historiken, vanligast först.', items: obj({ namn: s('Kort namn.'), beskrivning: s('Hur formatet går till, en mening.'), antal: { type: 'integer', description: 'Antal av de visade klippen.' }, senast: s('Senaste klippnummer med formatet.') }) },
  personer: { type: 'array', description: 'Återkommande personer framför kameran.', items: obj({ vem: s('Kort beskrivning (utseende, roll), inget namn behövs.'), gor: s('Vad personen gör i klippen: talar till kameran, spelar scener, mimar, visar mat, syns bara.'), antal: { type: 'integer', description: 'Antal av de visade klippen.' } }) },
  formagor: obj({ talar_till_kamera: s('Egen röst rakt till publiken.', VISAT), spelar_scener: s('Spelad situation eller sketch med roller.', VISAT), dialog_flera: s('Två eller fler i personalen spelar mot varandra.', VISAT), mimar_trendljud: s('Mimar eller agerar till lånat ljud.', VISAT), rost_over: s('Berättarröst över bilder.', VISAT), avancerad_klippning: s('Klippet bärs av redigering.', VISAT) }, 'Vad personalen har visat att den kan framför kameran.'),
  ton: s('Kontots ton: hur det skämtar eller inte, hur kantigt, hur vuxet, hur varmt.'),
  sjalvbild: s('Hur verksamheten vill framstå. Vad skulle kännas under dess värdighet eller fel för den?'),
  aldrig: s('Sådant som är vanligt på restaurang-TikTok men som kontot aldrig gör.'),
})

const bedomSchema = obj({
  kandidaten: s('Vad kandidatklippet är: format, vem som bär det, vad det kräver av den som gör det. Två meningar.'),
  repertoar: s('Finns kandidatens format i kundens historik? gor_det_nu = i de senaste klippen; har_gjort_forr = tydligt längre bak; narliggande = inte samma format men nära något de gör; aldrig = inget liknande.', ['gor_det_nu', 'har_gjort_forr', 'narliggande', 'aldrig']),
  belagg: s('Vilka historikklipp (nummer) som visar det, eller "inga".'),
  kraver_saknad_formaga: { type: 'boolean', description: 'Kräver klippet något personalen inte har visat att den kan, t.ex. en talare framför kameran eller skådespel?' },
  formaga: s('Vilken förmåga, eller "ingen".'),
  sjalvbild: s('Vad klippet gör med hur verksamheten vill framstå.', ['hojer', 'neutral', 'sanker']),
  ton: s('Klippets ton mot kundens.', ['passar', 'gransfall', 'bryter']),
  andringar: s('Vad som måste bytas för att kunden ska kunna göra det: inget, små byten (vara, replik), eller omskrivning.', ['inget', 'sma_byten', 'omskrivning', 'gar_inte']),
  passform: { type: 'number', minimum: 1, maximum: 5, description: 'Passform 1–5 som nästa klipp för kunden. Halva steg är tillåtna.' },
  skal: s('Varför, två meningar.'),
})

const SKALA = `Passformen sätter du som LeTrends ägare gör. Ägaren läser kundens hela historik i faser och frågar: har de gjort det här förut, kan de göra det i morgon med samma människor, och hur får det dem att framstå?
5 = formatet finns redan i kundens historik. Samma personer kan göra det i morgon, bara varan eller repliken byts.
4 = nära det kunden gör. Det passar, men är en annan smak eller kräver små byten.
3 = möjligt, men det sticker ut i flödet eller måste skrivas om.
2 = klippet sänker kundens självbild, eller kräver en förmåga kunden inte har visat (till exempel någon som talar säkert till kameran).
1 = fel fil helt: en annan sorts konto.
Bedöm passformen för just den här kunden, inte hur bra klippet är i allmänhet. Att ett format bara finns långt bak i historiken räcker ("they've done it before").`

// b3 (17 nov, efter jämförelsen av b2 mot ägarens skäl): b2 läste linjen för bokstavligt. Ägaren ger 4–4,5 åt en
// sketch med stark premiss även hos en kund som aldrig gjort sketcher ("a strong premise that can be abstracted
// regardless of where it's set"), och drar bara ned för självbild, ton och saknad förmåga. b3 börjar därför i
// klippets eget värde och drar av, i stället för att börja i repertoaren. Bandet visar bara 24 klipp, så b3 får
// också hela historikens formatfamiljer som tabell (det fångar t.ex. sketcher för hundra klipp sedan).
const FAMILJER = las(path.join(DATA, 'format', 'familjer', 'familjer.json'))
const FAMDEF = las(path.join(DATA, 'format', 'familjer', 'forregistrering.json')).familjer
function familjeText(konto) {
  const L = las(path.join(DATA, 'bank', konto, 'lista.json')).klipp.map(k => ({ ...k, f: FAMILJER[`${konto}-${k.id}`] })).filter(k => k.f).sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
  if (!L.length) return ''
  const rader = Object.keys(FAMDEF).map(f => ({ f, n: L.filter(k => k.f === f).length, sedan: L.findIndex(k => k.f === f) })).filter(r => r.n).sort((a, b) => b.n - a.n)
  return `Hela historiken för @${konto} (${L.length} klipp), grovt sorterad i formatfamiljer av en enklare textmodell. Använd den för det som ligger längre bak än banden visar; lita på banden när de säger emot.\n${rader.map(r => `- ${r.f} (${FAMDEF[r.f]}): ${r.n} klipp, senast för ${r.sedan} klipp sedan`).join('\n')}`
}
const SKALA3 = `Passformen sätter du som LeTrends ägare gör, i tre steg.

1. Klippets eget värde som förlaga. En fristående premiss som går att säga i en mening, tål att göras klumpigt och inte hänger på en viss person eller lokal går att flytta till nästan vilken restaurang som helst. Ett sådant klipp börjar på 4, även hos en kund som aldrig har gjort sketcher. Ett klipp utan egen idé (montage, ren visning, lapp med säljbudskap, trendljud) börjar på 3 och kan bara nå högre om kunden redan gör just det.

2. Dra av för det som faktiskt hindrar just den här kunden:
- Självbilden: en exklusiv eller prydlig verksamhet vill inte förminska sig själv eller sin mat. Slarvigt, kaotiskt eller för fånigt sänker.
- Tonen: vuxna teman eller mörk humor hos en familjär kund, eller för tamt hos en kantig.
- Förmågan: klippet hänger på en karismatisk talare, improvisation eller skådespel som personalen inte har visat. Bygger förlagan på improvisation går den bara att använda som skelett.
- Bemanningen: klippet kräver fler personer framför kameran än kunden har visat.
- Bundet: bilderna hänger på en vara, lokal eller händelse som kunden inte har, så att bara idén återstår.
Ett avdrag är ett steg, ett tungt avdrag två. Att kunden aldrig har gjort formatet är i sig inget avdrag.

3. Lägg till när formatet redan finns i kundens historik, även långt bak ("they've done it before"): då kan samma människor göra det i morgon, och betyget är 5 om inget drar av.

1 betyder fel fil helt, 2 att klippet skulle skada hur kunden framstår eller inte går att genomföra, 3 att det är möjligt men kräver omskrivning eller bara passar ibland, 4 att det passar med små byten, 5 att kunden skulle göra exakt det här. Använd hela skalan; ägarens medel över många par är ungefär 3,4.`
const bedomSchema3 = obj({
  kandidaten: s('Vad kandidatklippet är: premissen i en mening, vem som bär det, vad det kräver. Två meningar.'),
  premiss: s('Har klippet en fristående premiss som går att flytta?', ['stark', 'medel', 'svag', 'ingen']),
  grund: { type: 'number', minimum: 1, maximum: 5, description: 'Steg 1: klippets eget värde som förlaga, före kunden.' },
  repertoar: s('Finns kandidatens format i kundens historik (band och tabell)? gor_det_nu = i de senaste klippen; har_gjort_forr = längre bak; narliggande = nära något de gör; aldrig = inget liknande.', ['gor_det_nu', 'har_gjort_forr', 'narliggande', 'aldrig']),
  belagg: s('Vilka klipp eller vilken familj som visar det, eller "inga".'),
  avdrag: { type: 'array', description: 'Steg 2: det som hindrar just den här kunden. Tom lista om inget.', items: obj({ typ: s('', ['sjalvbild', 'ton', 'formaga', 'bemanning', 'bundet']), tyngd: s('', ['latt', 'tung']), vad: s('En mening.') }) },
  andringar: s('Vad som måste bytas: inget, små byten (vara, replik), omskrivning, eller går inte.', ['inget', 'sma_byten', 'omskrivning', 'gar_inte']),
  passform: { type: 'number', minimum: 1, maximum: 5, description: 'Passform 1–5 som nästa klipp för kunden. Halva steg är tillåtna.' },
  skal: s('Varför, två meningar.'),
})

// Historiken som band om fyra klipp (Vertex tar högst 10 videofiler per anrop), äldst först.
const historikDelar = async konto => {
  const H = PLAN[konto].historik.klipp.filter(k => fs.existsSync(litenFil(k.id))).sort((a, b) => (a.datum || '').localeCompare(b.datum || ''))
  const band = await byggBand(konto, H)
  return { delar: [{ text: `Historiken för @${konto}: ${H.length} klipp av kontots ${PLAN[konto].historik.antal}, äldst först. Klipp ${H.length} är det nyaste. Klippen ligger i ${band.length} band.` }, ...bandDelar(band)], n: H.length }
}
const profilFil = konto => path.join(E, `profil-${mkort}`, `${konto}.json`)

async function profil(konto) {
  const ut = profilFil(konto); if (fs.existsSync(ut)) return 'fanns'
  const { delar, n } = await historikDelar(konto)
  const r = await beaconDelar({ modell: MODELL, schema: profilSchema, delar: [{ text: LETREND }, ...delar, { text: `Beskriv @${konto} som en serie, utifrån de ${n} klippen ovan. Se på vad som faktiskt händer i bild och ljud, inte bara bildtexterna. Skriv på svenska.` }] })
  fs.mkdirSync(path.dirname(ut), { recursive: true }); fs.writeFileSync(ut, JSON.stringify({ konto, modell: r.modell, n, ms: r.ms, usage: r.usage, profil: r.data }, null, 1))
  return 'ny'
}

async function bedom(konto, c) {
  const ut = path.join(E, `${STEG}-${mkort}${ETIKETT}`, `${konto}__${c.id}.json`); if (fs.existsSync(ut)) return 'fanns'
  if (!fs.existsSync(litenFil(c.id))) return 'saknar klipp'
  const avs = delaId(c.id).konto
  let delar
  if (STEG === 'b3') delar = [{ text: `${LETREND}

${GRUNDVARDE}` }, ...(await historikDelar(konto)).delar, { text: familjeText(konto) }, { text: `Kandidatklippet, från ett annat konto (@${avs}):` }, { fil: litenFil(c.id) }]
  else if (STEG === 'b2') delar = [{ text: `${LETREND}\n\n${LINJE}` }, ...(await historikDelar(konto)).delar, { text: `Kandidatklippet, från ett annat konto (@${avs}):` }, { fil: litenFil(c.id) }]
  else { const P = las(profilFil(konto)).profil; delar = [{ text: `${LETREND}\n\n${LINJE}` }, { text: `Kunden @${konto}, beskriven som serie ur ${las(profilFil(konto)).n} av kontots klipp:\n${JSON.stringify(P, null, 1)}` }, { text: `Kandidatklippet, från ett annat konto (@${avs}):` }, { fil: litenFil(c.id) }] }
  delar.push({ text: `En CM överväger kandidatklippet som förlaga till nästa klipp för @${konto}.\n\n${STEG === 'b3' ? SKALA3 : SKALA}\n\nSkriv på svenska.` })
  const r = await beaconDelar({ modell: MODELL, schema: STEG === 'b3' ? bedomSchema3 : bedomSchema, delar })
  fs.mkdirSync(path.dirname(ut), { recursive: true }); fs.writeFileSync(ut, JSON.stringify({ konto, id: c.id, kalla: c.kalla, steg: STEG, modell: r.modell, ms: r.ms, usage: r.usage, svar: r.data }, null, 1))
  return 'ny'
}

const kunder = Object.keys(PLAN).filter(k => !KUNDER || KUNDER.includes(k))
let jobb = []
if (STEG === 'profil') jobb = kunder.map(k => ({ namn: k, kor: () => profil(k) }))
else for (const k of kunder) { const sedda = new Set(); for (const c of PLAN[k].kandidater) if (KALLOR.includes(c.kalla) && !sedda.has(c.id)) { sedda.add(c.id); jobb.push({ namn: `${k} ← ${c.id}`, kor: () => bedom(k, c) }) } }
jobb = jobb.slice(0, MAX)
console.log(`${STEG} ${mkort}: ${jobb.length} jobb, ${PAR} samtidigt`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => {
  while (i < jobb.length) {
    const j = jobb[i++]
    try { const r = await j.kor(); if (r === 'ny') ny++; else if (r !== 'fanns') console.log(`  ${j.namn}: ${r}`) } catch (e) { fel++; console.log(`  FEL ${j.namn}: ${e.message.slice(0, 200)}`) }
  }
}))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.anrop} anrop, ${beaconKostnad.usd.toFixed(2)} USD (loggat, överskattat för 3.x)`)
