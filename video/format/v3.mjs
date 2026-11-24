// Formatkort v3 (3 nov 2026): bygger på ägarens Miles-pass 1 och 2 (klipp 1–20, data/format/kalib/agare.json).
// Nytt mot v2:
// - biblioteket först: om klippet hör hemma i LeTrends bibliotek, med fem delfrågor
// - träffsäkerheten: hur sannolikt det är att en vanlig kund lyckas, med poleringsgap och precisionskrav
// - funktion i mixen med tre lägen (kött, stöd, utanför) i stället för sju roller, som ägaren tyckte var för många
// - redigeringsskämt (v2 missade metaskämtet i klipp 14), strategityp, segment och tid
// - exempel: ägarens omdömen om klipp 1–20 kan läggas i prompten (tes H19)
// Klipp 21–30 är testmängden.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const s = (description, extra = {}) => ({ type: 'string', description, ...extra })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description) => ({ type: 'array', items, description })

export const schema = obj({
  handling: s('Vad som händer, i ordning, 1–3 meningar, med repliker och skärmtext som bär poängen.'),
  redigeringsskamt: s('Ett skämt eller en poäng som ligger i själva redigeringen eller bildrutan, till exempel en effekt som reagerar på det personen gör eller text som ändras. Titta noga. Om det inte finns, skriv "inget".'),
  karna: s('Idén i en mening, utan verksamhetens namn, rätter eller personer.'),
  mall: s('Idén som återanvändbar mall med [platshållare].'),
  strategi: s('ide_sketch (en scen eller sketch med en idé), dialog_tilltal (prata direkt med publiken, monolog, svara på kommentarer), visning (mat, dryck eller lokal i bild), meddelande (nyhet, PSA, öppettider), tavling, event (fångat från ett event), trend_mim (mima eller följa ett trendljud).', { enum: ['ide_sketch', 'dialog_tilltal', 'visning', 'meddelande', 'tavling', 'event', 'trend_mim'] }),
  bibliotek: obj({
    skal: s('Skriv först: kan en CM rekommendera just det här klippet som förebild till en annan verksamhet, som spelar in sin version själv efter en kort brief? Varför, 1–2 meningar.'),
    planerat: s('planerat_format (går att planera och spela in när som helst), eventfangst (bygger på ett event som ändå äger rum), nyhetsberoende (kräver en verklig nyhet, öppning eller kampanj).', { enum: ['planerat_format', 'eventfangst', 'nyhetsberoende'] }),
    fristaende_ide: s('Finns en fristående, stark idé som går att ta med sig? ja, delvis eller nej (det bärs av en persons karisma, en dialog med publiken eller kontots egen värld).', { enum: ['ja', 'delvis', 'nej'] }),
    manniskor: s('i_centrum (personer bär idén), med (personer syns men bär inte), inga.', { enum: ['i_centrum', 'med', 'inga'] }),
    bred_miljo: n(1, 5, 'Hur väl idén fungerar i många olika lokaler och menyer. 1 = bara här, 5 = nästan överallt.'),
    precision: s('Vad som måste bli exakt rätt för att klippet ska fungera, till exempel en tajming, en bildvinkel eller en klippning. Annars "inget".'),
    poleringsgap: n(1, 5, 'Hur mycket svårare det är att nå samma känsla än det ser ut. 1 = ser ut som det är, 5 = ser enkelt ut men kräver ljus, foto och klippning som en vanlig kund inte har.'),
    sannolikhet: n(1, 5, 'Hur sannolikt det är att en vanlig kund, med klippet som förebild och en kort brief, får sin version att fungera. 1 = osannolikt, 3 = ungefär hälften, 5 = nästan säkert.'),
    beslut: s('Hör klippet hemma i biblioteket? ja, villkorat (bara för vissa verksamheter eller under vissa villkor) eller nej.', { enum: ['ja', 'villkorat', 'nej'] }),
    villkor: s('Villkoren om beslutet är villkorat, annars "inga".'),
  }),
  personal: obj({
    bar: s('Kan en vanlig anställd göra en fungerande version? ja, delvis eller nej.', { enum: ['ja', 'delvis', 'nej'] }),
    hanger_pa: arr(s('', { enum: ['person', 'persona', 'lokal', 'rekvisita', 'nisch', 'meny', 'produktion', 'redigering', 'trend', 'personalfrihet', 'event', 'manus', 'inget'] }), 'Det som hindrar.'),
  }),
  funktion: s('Funktion i en LeTrend-mix. kott: sketcher och inbjudande innehåll med personer, kanalens kärna. stod: stöder köttet, som visning, nyhet, PSA, tävling eller lätt glitter, ofta en fråga till publiken och använt med avsikt då och då. utanfor: eventfångst, Instagram-polering eller reklamfilm som fungerar för verksamheten men inte i biblioteket.', { enum: ['kott', 'stod', 'utanfor'] }),
  funktion_villkor: s('Villkor för funktionen, till exempel "var femte video", "om kanalen lutar mot meme" eller "inga".'),
  segment: s('Vilka verksamheter klippet passar som förebild: alla, enkel (vardagliga lokaler), premium (finare lokaler med egen produktionskompetens) eller kedja (volym och budget).', { enum: ['alla', 'enkel', 'premium', 'kedja'] }),
  tid: s('evergreen (fungerar när som helst) eller tidsbunden (högtid, säsong eller nyhet).', { enum: ['evergreen', 'tidsbunden'] }),
  relation: n(1, 5, 'Bygger klippet en relation: lär man känna personalen och verksamheten? 1 = väcker bara intresse, 5 = man känner att man lär känna dem.'),
  persona: obj({
    krav: s('ingen, vardag eller stark (kaxig, provocerande, personligt utlämnande).', { enum: ['ingen', 'vardag', 'stark'] }),
    rod_trad: b('Är det meningsfullt bara om personan är varumärkets röda tråd?'),
  }),
  plattform: s('tiktok_nativ, blandad, instagram_polish eller reklamfilm.', { enum: ['tiktok_nativ', 'blandad', 'instagram_polish', 'reklamfilm'] }),
  svaghet: s('Det som gör klippet mindre användbart som förebild.'),
})

export const KONSTITUTION = `LeTrend hjälper lokala verksamheter (restauranger, barer, kaféer, senare gym och butiker) att göra TikTok som personalen själv spelar in. En content manager (CM) väljer klipp ur LeTrends bibliotek och rekommenderar dem som förebild. Principerna:
1. Biblioteket först. Frågan är om klippet hör hemma i biblioteket, alltså om en CM kan rekommendera det som förebild till en annan verksamhet. Ett klipp kan fungera utmärkt för sin egen verksamhet men inte för biblioteket.
2. Biblioteket bygger på planerat innehåll med fristående, starka idéer som går att abstrahera, som bärs av människor och som fungerar i många miljöer. Det här är inte biblioteksklipp, även när de är bra: eventfångster, nyheter som kräver en verklig händelse, och innehåll som bärs av en persons karisma eller av kontots egen dialog med publiken.
3. Kunden spelar in själv utan handhållning: briefen är en guide, inte en manual. Bedöm hur sannolikt det är att en vanlig kund träffar rätt. Enkla bilder kan dölja ett poleringsgap: det ser lätt ut men är svårt att få att se ut så. Omvänt är ett format där inget måste bli exakt rätt lätt att klara, även utan polering.
4. Produktion är inte det LeTrend hjälper med. Klipp vars värde ligger i ljus, foto och klippning passar bara verksamheter i premiumsegmentet som har egen kompetens.
5. Funktion i mixen. Kött är sketcher och inbjudande innehåll med personer, kanalens kärna. Stöd är visning, nyhet, PSA, tävling och lätt glitter, ofta en fråga till publiken ("kom och ät"), använt med avsikt ungefär var femte video. Utanför är eventfångst, Instagram-polering och reklamfilm. Glitter som verkligen fångar och förtjusar, och inte är tomt, kan vara kött.
6. Visning och marknadsföring behöver en människa eller berättare som förankrar dem, annars blir de bara en snygg bild.
7. Sketcher i en filmvärld är kött, men i mixen behöver de förankras i verkligheten med direkt tilltal och publikkontakt.
8. Innehåll som kräver en stark persona är meningsfullt bara om personan är varumärkets röda tråd. Giveaways i volym är kedjornas spel, och för en enskild enhet knyts de till kalendern. Ett klipp som fungerar året runt är bättre än ett tidsbundet.
Bedöm klippet som det är, även när det inte följer principerna. Titta noga efter skämt som ligger i redigeringen.`

// Ägarens omdömen om klipp 1–20 som exempel (H19). Beskrivningen kommer från v2 och är rättad där
// modellen såg fel (klipp 14).
const RATTAD = { 14: 'En anställd hoppar upp och ner i en tom restaurang med en meny i handen. Hela bildrutan skakar till och trycks ner varje gång hon landar, som om hon hoppade i en hiss, medan texten blir alltmer vädjande: "COME EAT AT MONDO PLEASE".' }
export function exempel() {
  const agare = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'kalib', 'agare.json'), 'utf8')).klipp
  const urval = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'kalib', 'urval.json'), 'utf8'))
  return Object.entries(agare).map(([nr, o]) => {
    const k = urval[Number(nr) - 1]
    const besk = RATTAD[nr] ?? JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'v2-gemini-3.1-pro-preview', `${k.id}.json`), 'utf8')).handling
    return `Exempel ${nr}: ${besk}\nÄgaren: bibliotek ${o.bibliotek}, funktion ${o.funktion}, personal ${o.bar}${o.villkor ? `, villkor: ${o.villkor}` : ''}. ${o.not}`
  }).join('\n\n')
}

export const prompt = (konto, medExempel) => `Ett TikTok-klipp från @${konto}.

${KONSTITUTION}
${medExempel ? `\nSå här har ägaren bedömt tjugo andra klipp. Använd ägarens bedömningar som måttstock, inte som mallar att kopiera:\n\n${exempel()}\n` : ''}
Var konkret och nykter. Bedöm det du ser och hör, inte det du gissar. Svara på svenska.`
