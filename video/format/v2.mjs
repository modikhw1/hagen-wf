// Formatkort v2 (3 nov 2026): bygger på ägarens Miles-pass 1 (klipp 1–10, data/format/kalib/agare.json).
// Nytt mot v1:
// - premiss och exemplar hålls isär (formatet kan bära fast klippet är svagt, och tvärtom)
// - replikering i flera delar
// - eskalering, relation, vasshet, persona med röd tråd, humorns räckvidd, plattformsspråk och skala
// - rollen i mixen har sju roller i stället för kärna, inslag och utanför (v1 träffade 3 av 10)
// Klipp 1–10 är träning. Klipp 11–30 hålls utanför och prövas i Miles-pass 2 och 3.
const s = (description, extra = {}) => ({ type: 'string', description, ...extra })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description) => ({ type: 'array', items, description })

export const ROLLER = {
  huvudnummer: 'det verksamheten skulle visa för att visa sitt huvudvärde: den roligaste sketchen, den mest intressanta situationen, en milstolpe',
  stomme: 'ett format som kanalen kan byggas kring och som återkommer ofta, kanalens huvudinnehåll',
  aterkommande_inslag: 'en återkommande kategori som bär sig själv och används med avsikt då och då, t.ex. en tävling knuten till kalendern eller en visning var femte video',
  glitter: 'kul, lätt och snabbt glömt, ger glans åt ett avslappnat flöde men är inte huvudrätten',
  utfyllnad: 'lågt arbete som fyller en plats och håller balansen, ett godtagbart klipp som inte sticker ut',
  engangsbit: 'en engångsspik eller karaktärsbit som inte går att upprepa som kategori, högst en del av en sketch',
  annan_kanal: 'Instagram-polerat visningsklipp eller reklamfilm, inte LeTrends fil, högst en avrundning ibland',
}

export const schema = obj({
  handling: s('Vad som händer, i ordning, 1–3 meningar, med repliker och skärmtext som bär poängen.'),
  karna: s('Idén i en mening, utan verksamhetens namn, rätter eller personer.'),
  mall: s('Idén som återanvändbar mall med [platshållare].'),
  platser: arr(obj({ plats: s('Platshållarens namn.'), har: s('Vad den är i det här klippet.') }), 'Det som kan bytas ut. 1–5 st.'),
  last: arr(s('En sak.'), 'Det som måste finnas kvar för att idén ska fungera. 1–4 st.'),
  premiss: obj({
    skal: s('Skriv först: en vanlig anställd utan kameravana får en kort instruktion och spelar in idén. Vad händer? 1–2 meningar.'),
    bar: s('Bär premissen med en vanlig anställd? ja, delvis (bär om villkor uppfylls) eller nej.', { enum: ['ja', 'delvis', 'nej'] }),
    hanger_pa: arr(s('', { enum: ['person', 'persona', 'lokal', 'rekvisita', 'nisch', 'meny', 'produktion', 'trend', 'personalfrihet', 'inget'] }), 'Det som hindrar flytt. person: just den personens talang. persona: en stark attityd eller ett personligt ämne. lokal: just denna lokal. rekvisita: ett ovanligt föremål. nisch: något bara denna verksamhet gör. meny: bilderna är bundna till just dessa rätter. produktion: foto, klippning, grafik. trend: ett ljud eller en meme. personalfrihet: personalen måste spela karaktärer eller ta personliga ämnen. inget.'),
  }),
  exemplar: obj({
    betyg: n(1, 5, 'Hur väl just det här klippet är gjort för vad det är: idéns styrka, längd, tajming och klippning. Inte hur polerat det är. 1 = skulle inte rekommenderas som förebild, 5 = ett utmärkt exempel.'),
    forhojning: s('Vad i utförandet som skulle göra det minnesvärt, till exempel rollbesättning, överdrift eller tajming. Annars "inget".'),
  }),
  format_potential: n(1, 5, 'Kan formatet, väl gjort, bära en kanal som återkommande innehåll? Bedöms oberoende av hur bra just det här klippet är.'),
  replikering: obj({
    skadespel: n(1, 5, 'Karisma, attityd eller timing som krävs. 1 = ingen, 5 = en personlighet som inte går att instruera fram.'),
    produktionsoga: s('Kräver någon på plats med öga för bild och klippning, t.ex. CapCut-vana.', { enum: ['nej', 'lite', 'ja'] }),
    produktionskrav: n(1, 5, '1 = en telefon, en tagning. 5 = budget, team, avancerad grafik.'),
    scener_tid: n(1, 5, 'Tid och antal scener att spela in. 1 = en tagning på en minut, 5 = många scener och planering.'),
    specificitet: n(0, 3, 'Hur mycket av bilderna som är bundet till just denna meny eller lokal och måste bytas. 0 = inget, 3 = allt.'),
    personalfrihet: n(1, 5, 'Hur mycket personalen måste spela karaktärer, bära civila kläder eller ta personliga ämnen. 1 = inget, 5 = mycket.'),
    instruktion: n(1, 5, 'Hur exakt en CM kan instruera så att resultatet blir lika bra. 1 = går inte, 5 = scen för scen.'),
  }),
  eskalering: s('Har klippet uppbyggnad och vändning? ingen (en jämn tagning eller visning), en_vandning, flera.', { enum: ['ingen', 'en_vandning', 'flera'] }),
  vardet: obj({
    ide: n(0, 100, 'Andel av dragningskraften från idén, manuset eller vändningen.'),
    framforande: n(0, 100, 'Från personernas timing, karisma eller skådespel.'),
    produktion: n(0, 100, 'Från foto, ljus, klippning, grafik eller effekter.'),
    produkt: n(0, 100, 'Från maten, varan eller lokalen i sig.'),
    trend: n(0, 100, 'Från ett trendljud, en meme eller ett känt format.'),
  }),
  visning: obj({
    grad: n(0, 3, '0 = ingen visning. 1 = ett inslag i en idé. 2 = en bärande del. 3 = hela klippet är visning.'),
    ratt: s('ingen, unik (intressant i sig), aptitlig (ser god ut) eller signatur (verksamhetens specialitet är poängen).', { enum: ['ingen', 'unik', 'aptitlig', 'signatur'] }),
  }),
  relation: n(1, 5, 'Bygger klippet en relation: att lära känna personalen, teamet eller verksamheten, inside-känsla? 1 = väcker bara intresse, 5 = man känner att man lär känna dem.'),
  vasshet: n(1, 5, 'Hur skarp och fokuserad idén är, inte klippningen. 1 = platt och utan poäng, 5 = en tydlig, skarp poäng.'),
  persona: obj({
    krav: s('Kräver klippet en stark persona eller attityd? ingen, vardag (vanlig glimt i ögat) eller stark (kaxig, provocerande, personligt utlämnande).', { enum: ['ingen', 'vardag', 'stark'] }),
    rod_trad: b('Är klippet meningsfullt bara om personan är varumärkets röda tråd, och inte som engångsgrej?'),
  }),
  humor: s('ingen, universell (de flesta förstår, t.ex. absurd vardagshumor), smal (passar en viss publik) eller polariserande.', { enum: ['ingen', 'universell', 'smal', 'polariserande'] }),
  plattform: s('tiktok_nativ (lekfullt, självironiskt, personer i fokus), blandad, instagram_polish (estetiskt visningsklipp, CapCut-övergångar) eller reklamfilm (budget, team).', { enum: ['tiktok_nativ', 'blandad', 'instagram_polish', 'reklamfilm'] }),
  skala: s('enhet (passar en enskild verksamhet), kedja (bygger på volym eller budget, t.ex. stora giveaways) eller bada.', { enum: ['enhet', 'kedja', 'bada'] }),
  salj: s('ingen, fond, vavd (produkten är del av poängen), inbjudan (lågt tryck) eller direkt (pris, erbjudande, uppmaning).', { enum: ['ingen', 'fond', 'vavd', 'inbjudan', 'direkt'] }),
  ton: obj({
    sjalvdistans: n(1, 5, '1 = tar sig själv på allvar. 5 = driver med förväntningen att sälja.'),
    inside: n(1, 5, '1 = inget som binder till ett gäng. 5 = som ett tv-program eller ett inside-skämt.'),
    varumarkesrisk: n(1, 5, '1 = ingen risk. 5 = vulgärt, elakt eller skadligt.'),
  }),
  trend: s('egen, anpassad_trend eller ren_trend.', { enum: ['egen', 'anpassad_trend', 'ren_trend'] }),
  roll: s(`Klippets roll i en LeTrend-mix: ${Object.entries(ROLLER).map(([k, v]) => `${k} (${v})`).join('; ')}.`, { enum: Object.keys(ROLLER) }),
  roll_villkor: s('Under vilka villkor rollen gäller, t.ex. "knuten till ett kalendertillfälle", "bara om personan är röd tråd" eller "inga".'),
  svaghet: s('Det som gör klippet mindre användbart som förebild för andra verksamheter.'),
})

export const KONSTITUTION = `LeTrend hjälper lokala verksamheter (restauranger, barer, kaféer, senare gym och butiker) att göra TikTok som personalen själv spelar in. En content manager (CM) väljer klipp ur en bank och anpassar dem. Principerna:
1. Håll isär två frågor. Bär formatet, alltså premissen spelad av en vanlig anställd efter en kort instruktion? Och är just det här klippet ett bra exempel att rekommendera, med idé, längd, tajming och klippning? Ett format kan bära en hel kanal fast klippet är svagt, och ett välgjort klipp kan vara omöjligt att flytta.
2. Replikering är mer än skådespel. Den avgörs av tid och antal scener, om någon på plats har öga för bild och klippning, hur mycket av bilderna som är bundet till just den menyn eller lokalen, om personalen är fri att spela karaktärer eller ta personliga ämnen, och om en CM kan skriva exakta instruktioner.
3. Polering är inte värde. Överskatta inte snabb klippning, zoomar och effekter: ett lugnt och enkelt klipp kan vara godkänt. Instagram-polerade visningsklipp och reklamfilmer är en annan fil än LeTrends.
4. Rollen är relativ till mixen. Ett återkommande inslag måste bära sig självt som en kategori som används med avsikt. En engångsbit som bara bärs av en persons energi är inget inslag. Huvudnumret är det verksamheten skulle visa för att visa sitt huvudvärde.
5. LeTrend värderar relation: att lära känna personalen och verksamheten, en inside-känsla och att verksamheten driver med sig själv. Ett klipp som bara väcker intresse, som en visning, bygger ingen relation.
6. Innehåll som kräver en stark persona är meningsfullt bara om den personan är varumärkets röda tråd, inte som engångsgrej. Det gäller en kaxig eller provocerande attityd och personliga ämnen. Absurd vardagshumor förstår de flesta, medan till exempel dejtingteman passar färre.
7. Giveaways och kampanjer i volym är kedjornas spel. För en enskild enhet fungerar samma format knutet till ett kalendertillfälle.
8. Ett klipp med uppbyggnad och vändning kan bäras av en vanlig anställd. En lång tagning utan eskalering kräver karisma.
Bedöm klippet som det är, även när det inte följer principerna.`

export const prompt = (konto, kontext) => `Ett TikTok-klipp från @${konto}.

Syftet är att förstå klippets IDÉ och dess värde i en LeTrend-mix, så att en content manager kan välja och anpassa den till en annan verksamhet, vars egen personal spelar in sin version med en telefon.

${KONSTITUTION}
${kontext ? `\nKontots övriga klipp, en rad per klipp med typ och innehåll. Använd dem för att bedöma klippets roll i kontots mix och om personan är kontots röda tråd:\n${kontext}\n` : ''}
Var konkret och nykter. Bedöm det du ser och hör, inte det du gissar. Svara på svenska.`
