// Formatkort v4 (4 nov 2026): klippets KRAV på en kund, strukturerat så att det går att matcha mot en
// kundprofil (format/h-kund.mjs). Bygger på v3 (biblioteket först, tre zoner) och på utfallen i E4 och i
// serietestet: visningsregeln, trendljud, tilltal och återkommande personer.
// Platserna har typer, så att matchningen vet vad som byts mot kundens personer, produkter och lokal.
const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description) => ({ type: 'array', items, description })

export const ROLLER = ['anstalld', 'kock', 'bartender', 'kassor', 'servitor', 'agare', 'gast', 'forbipasserande', 'barn', 'ingen']
export const LOKALDELAR = ['disk_kassa', 'kok', 'bar', 'matsal', 'uteservering', 'entre', 'butik_hylla', 'ingen_sarskild']
export const VERKSAMHETER = ['restaurang', 'snabbmat', 'kafe', 'bar', 'finare_restaurang', 'butik', 'aktivitet']
export const SITUATIONER = ['vardag', 'lansering', 'hogtid', 'event', 'flytt_ombyggnad', 'tavling', 'rekrytering']

export const schema = obj({
  handling: s('Vad som händer, i ordning, 1–3 meningar, med repliker och skärmtext som bär poängen.'),
  redigeringsskamt: s('Ett skämt eller en poäng som ligger i själva redigeringen eller bildrutan. Titta noga. Annars "inget".'),
  karna: s('Idén i en mening, utan verksamhetens namn, rätter eller personer.'),
  mall: s('Idén som återanvändbar mall med [platshållare].'),
  platser: arr(obj({
    plats: s('Platshållarens namn, som i mallen.'),
    har: s('Vad den är i det här klippet.'),
    typ: s('Vad som byts ut: person (en roll som spelas), produkt (rätt, dryck, vara), lokal (en del av lokalen), replik (det som sägs), text (skärmtext), rekvisita, situation.', ['person', 'produkt', 'lokal', 'replik', 'text', 'rekvisita', 'situation']),
  }), 'Allt som kan bytas ut för att klippet ska passa en annan verksamhet. 1–6 st.'),
  zon: s('karna: en fristående, stark idé som bärs av människor, fungerar i många verksamheter och tål att göras klumpigare. mitten: godkänd men villkorad av kunden, t.ex. visning, nyhet, tävling eller ett format som kräver viss kapacitet, segment eller situation. ute: eventfångst, Instagram-polering, reklamfilm, eller något som bärs av en persons karisma eller ett kontos egen värld.', ['karna', 'mitten', 'ute']),
  zon_skal: s('Varför den zonen, 1–2 meningar.'),
  krav: obj({
    personer_min: n(0, 6, 'Minsta antal personer som behövs.'),
    roller: arr(s('', ROLLER), 'Rollerna som behövs, en per person.'),
    frontfigur: obj({ passar: b('Kan huvudrollen spelas av verksamhetens återkommande person, t.ex. ägaren eller en anställd som brukar synas?'), roll: s('Vilken roll frontfiguren skulle ta, annars "ingen".') }),
    skadespel: n(1, 5, 'Karisma eller timing som krävs. 1 = ingen, 3 = en enkel replik eller reaktion, 5 = en personlighet som inte går att instruera fram.'),
    redigering: s('Vad som krävs i efterarbete: ingen (en tagning), enkel (några klipp och text), mall (CapCut-liknande mall eller takt), avancerad (effekter som måste sitta exakt).', ['ingen', 'enkel', 'mall', 'avancerad']),
    produktion: n(1, 5, '1 = en telefon räcker, 5 = ljus, foto och klippning som en vanlig kund inte har.'),
    lokal: arr(s('', LOKALDELAR), 'Delar av lokalen som behövs.'),
    produkt: s('ingen, valfri (vilken produkt som helst), mat (någon rätt), specifik (en viss sorts rätt eller vara, beskriv i produkt_typ), dryck, varor.', ['ingen', 'valfri', 'mat', 'specifik', 'dryck', 'varor']),
    produkt_typ: s('Vilken sorts produkt som krävs om den är specifik, annars "ingen".'),
    verksamheter: arr(s('', VERKSAMHETER), 'Verksamheter där idén fungerar utan att poängen går förlorad.'),
    segment: s('alla, enkel (vardagliga lokaler), premium (finare lokaler med egen produktionskompetens) eller kedja (volym och budget).', ['alla', 'enkel', 'premium', 'kedja']),
    situation: s('När klippet passar.', SITUATIONER),
    persona: s('Kräver en stark persona? ingen, vardag eller stark.', ['ingen', 'vardag', 'stark']),
    ljud: s('Vad ljudet bygger på: eget_tal, voiceover, trendljud eller musik.', ['eget_tal', 'voiceover', 'trendljud', 'musik']),
    trendljud_utbytbart: b('Om ljudet är ett trendljud: kan personerna spela in replikerna själva i stället?'),
  }),
  regler: obj({
    visning_med_person: b('Om klippet visar mat eller dryck: syns en person i bild större delen av tiden?'),
    trendljud_i_visning: b('Visas mat eller dryck till ett trendljud?'),
  }),
  funktion: s('kott (sketch eller inbjudande innehåll med personer, ger räckvidd och gillanden), stod (fråga till publiken, visning, nyhet eller erbjudande, ger kommentarer) eller utanfor.', ['kott', 'stod', 'utanfor']),
  evergreen: b('Fungerar klippet när som helst, inte bara vid en viss tid eller händelse?'),
  anpassningsrisk: s('Vad som mest troligt går fel när en annan verksamhet gör sin version, en mening.'),
})

export const KONSTITUTION = `LeTrend hjälper lokala verksamheter (restauranger, barer, kaféer, senare butiker) att göra TikTok som personalen själv spelar in. En content manager (CM) väljer klipp ur LeTrends bibliotek och anpassar dem till en kund. Du ska beskriva vad klippet KRÄVER av en kund, så att det kan matchas mot rätt kunder.

Principer:
1. Biblioteket bygger på planerade, fristående idéer som bärs av människor och fungerar i många miljöer. Eventfångster, reklamfilm och sådant som bärs av en persons karisma är inte biblioteksklipp.
2. Kunden spelar in själv utan handhållning. Bedöm vad som krävs i personer, roller, skådespel, efterarbete, lokal och produkt, och var ärlig om poleringsgapet: om klippet ser enkelt ut men kräver ljus, foto och klippning.
3. Det LeTrend vet om utfall, mätt inom samma konto:
   - Personer i bild, en spelad situation, humor och direkt tilltal ger räckvidd.
   - En matvisning med en person i bild når ungefär dubbelt så långt som en visning utan person. Med trendljud eller som montage når den kortare.
   - Klipp med verksamhetens återkommande person eller i ett återkommande format når cirka 30 % längre.
   - Tävlingar, uppmaningar och erbjudanden ger kommentarer men inte räckvidd.
4. Därför är det viktigt om klippets huvudroll kan spelas av kundens återkommande person, och om ett trendljud kan bytas mot egna repliker.
Bedöm klippet som det är. Titta noga efter skämt som ligger i redigeringen.`

export const prompt = konto => `Ett TikTok-klipp från @${konto}.

${KONSTITUTION}

Var konkret och nykter. Bedöm det du ser och hör, inte det du gissar. Svara på svenska.`
