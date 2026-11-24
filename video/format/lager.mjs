// Lagerschemat för E1 och E4 (3 nov 2026): ett klipp beskrivs i 42 lager, de flesta rena
// iakttagelser och några konstrukt. Inga LeTrend-principer ligger i prompten, så att det som mäts är
// klippet och modellen, inte ägarens teori (källa 4 hålls utanför).
// Tre omformuleringar av prompten (PROMPTER) gör att promptens inverkan kan mätas för sig.
const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })

// typ: bin (sant/falskt), ord (ordnad skala), kat (kategorier). Används av analysen.
export const LAGER = {
  // Människor
  personer: ['ord', n(0, 3, 'Flest personer i bild samtidigt: 0, 1, 2, eller 3 = tre eller fler.')],
  andel_person: ['ord', n(0, 4, 'Hur stor del av tiden en person syns tydligt (mer än händer): 0 aldrig, 1 under en fjärdedel, 2 upp till hälften, 3 upp till tre fjärdedelar, 4 nästan hela tiden.')],
  personal: ['bin', b('Syns någon som tydligt är personal?')],
  gast: ['bin', b('Syns någon som tydligt är gäst eller kund?')],
  tilltal: ['bin', b('Talar någon direkt till kameran?')],
  dialog: ['bin', b('Pratar personer med varandra i bild?')],
  roll: ['bin', b('Spelar personerna upp en påhittad situation, en sketch?')],
  narbild_ansikte: ['bin', b('Finns närbilder där ett ansiktsuttryck bär något?')],
  // Ljud och text
  tal: ['kat', s('Hur tal förekommer.', ['inget', 'voiceover', 'repliker', 'bada'])],
  trendljud: ['bin', b('Används ett känt trendljud, en låt eller ett ljudklipp som andra också använder?')],
  mimar: ['bin', b('Mimar någon till ett ljud?')],
  musik: ['bin', b('Finns musik?')],
  skarmtext: ['ord', n(0, 3, 'Mängd skärmtext: 0 ingen, 1 en rad, 2 flera rader eller byten, 3 texten bär det mesta.')],
  text_poang: ['bin', b('Ligger klippets poäng främst i skärmtexten?')],
  // Bild och klippning
  klipp: ['ord', n(0, 3, 'Antal bildklipp: 0 en tagning, 1 två till fyra, 2 fem till tio, 3 fler än tio.')],
  montage: ['bin', b('Är det ett montage av korta bilder i takt med musik?')],
  kamera: ['kat', s('Kamerans rörelse för det mesta.', ['stilla', 'handhallen', 'mjuk_glid'])],
  effekter: ['ord', n(0, 3, 'Effekter, grafik och övergångar: 0 inga, 1 lite, 2 tydliga, 3 mycket.')],
  redigeringsskamt: ['bin', b('Ligger ett skämt i själva redigeringen, t.ex. en effekt som reagerar på det någon gör?')],
  slowmotion: ['bin', b('Finns slowmotion?')],
  bildkvalitet: ['ord', n(1, 5, '1 suddigt, mörkt eller skakigt, 5 skarpt och välexponerat.')],
  proffsljus: ['bin', b('Ser ljussättningen planerad och proffsig ut?')],
  // Innehåll
  mat_andel: ['ord', n(0, 4, 'Hur stor del av tiden mat eller dryck är i fokus: 0 aldrig, 4 nästan hela tiden.')],
  tillagning: ['bin', b('Visas tillagning eller uppläggning?')],
  lokal: ['ord', n(0, 3, 'Hur mycket av lokalen som syns: 0 inget, 3 mycket.')],
  utomhus: ['bin', b('Är det mesta filmat utomhus?')],
  erbjudande: ['bin', b('Nämns pris, erbjudande eller nyhet på menyn?')],
  uppmaning: ['bin', b('Uppmanas tittaren att komma, köpa, följa eller kommentera?')],
  tavling: ['bin', b('Är det en tävling, quiz eller giveaway?')],
  handelse: ['bin', b('Bygger klippet på en verklig händelse: event, öppning, flytt eller ombyggnad?')],
  hogtid: ['bin', b('Är klippet knutet till en högtid, säsong eller ett datum?')],
  // Struktur och ton
  krok: ['bin', b('Händer något som fångar uppmärksamheten under de första två sekunderna?')],
  vandning: ['bin', b('Finns en vändning eller punchline?')],
  eskalering: ['ord', n(0, 2, 'Byggs något upp: 0 nej, 1 lite, 2 tydligt i flera steg.')],
  humor: ['ord', n(0, 2, '0 ingen humor, 1 lätt, 2 tydligt komiskt.')],
  absurd: ['bin', b('Är något i klippet absurt eller orimligt med avsikt?')],
  vardag: ['bin', b('Bygger klippet på en igenkännbar vardagssituation?')],
  sjalvironi: ['bin', b('Driver verksamheten eller personalen med sig själva?')],
  // Konstrukt
  fristaende_ide: ['ord', n(1, 5, 'Hur tydlig och fristående idén är, en idé som går att ta med sig till en annan plats: 1 ingen idé, 5 en tydlig idé.')],
  feltolerans: ['ord', n(1, 5, 'Skulle klippet fortfarande fungera om det gjordes klumpigare, med sämre timing och enklare bild? 1 nej, faller helt. 5 ja, kanske till och med roligare.')],
  poleringsgap: ['ord', n(1, 5, 'Hur mycket svårare det är att nå samma känsla än det ser ut: 1 ser ut som det är, 5 ser enkelt ut men kräver kunnande i ljus, foto och klippning.')],
  relation: ['ord', n(1, 5, 'Hur mycket man lär känna personerna eller verksamheten: 1 inget, 5 mycket.')],
  kontotyp: ['kat', s('Vad kontot verkar vara.', ['restaurang', 'bar', 'kafe', 'butik', 'aktivitet', 'matguide', 'kreator', 'annat'])],
}

export const schema = obj(Object.fromEntries(Object.entries(LAGER).map(([k, [, d]]) => [k, d])))

export const PROMPTER = [
  konto => `Ett TikTok-klipp från @${konto}. Beskriv klippet genom att fylla i fälten. Bedöm det du ser och hör, inte det du gissar. Svara på svenska.`,
  konto => `Du är en noggrann analytiker av kortvideo. Titta på hela klippet från @${konto}, både bild, ljud och skärmtext, och koda det enligt schemat. Var exakt, och välj det värde som stämmer bäst även när du är osäker.`,
  konto => `Klipp från @${konto} på TikTok. Föreställ dig att du ska beskriva det för en kollega som inte kan se det. Fyll i varje fält så sakligt som möjligt.`,
]
