// Formatkort v5 (4 nov 2026). Bygger på v4 (krav, platser, visningsregeln) och lägger till det
// valideringen i Miles-pass 4–5 visade saknas:
//  - helhet först: hur idé, personer, tempo och bild samverkar, innan klippet delas upp
//  - grundvärde: premiss, om värdet finns kvar utan efterarbete, vad som går förlorat om det görs klumpigt
//  - språk: strategi, kantighet, tempo, klippberoende och personens funktion, för matchning mot kundens linje
//  - förlaga: hur bundna bilderna är till produkt och lokal
//  - beats med vad som bär och vad som är fritt, för anpassningen
// Doktrinen ligger i format/doktrin.mjs.
import { LETREND, GRUNDVARDE, LINJE, UTFALL } from './doktrin.mjs'
import { schema as v4 } from './v4.mjs'

const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description, extra = {}) => ({ type: 'array', items, description, ...extra })

export const STRATEGIER = ['sketchvarld', 'tilltal', 'premium_stamning', 'visning', 'kampanj', 'trend']
export const KANTIGHET = ['familjar', 'lekfull', 'kantig', 'vuxen']
export const TEMPO = ['lugnt', 'medel', 'hogt']

export const schema = obj({
  helhet: s('Vad klippet egentligen är, som en erfaren CM skulle säga det: hur idén, personerna, tempot och bilden samverkar och vad som gör att det fungerar eller inte. 2–3 meningar. Skriv det innan du delar upp klippet.'),
  handling: v4.properties.handling,
  redigeringsskamt: v4.properties.redigeringsskamt,
  karna: v4.properties.karna,
  mall: v4.properties.mall,
  platser: v4.properties.platser,
  beats: arr(obj({
    vad: s('Vad som händer i beatet, kort.'),
    funktion: s('Beatets uppgift.', ['krok', 'uppbyggnad', 'vandning', 'punchline', 'visning', 'tilltal', 'avslut']),
    bar: s('karna: utan det faller idén. stod: hjälper men kan göras på annat sätt. fri: kan improviseras eller strykas.', ['karna', 'stod', 'fri']),
    bunden: s('Vad beatet är bundet till hos avsändaren: ingen, produkt, lokal, person (en viss persons karisma), trend (ett ljud eller format) eller redigering (en effekt eller klippning).', ['ingen', 'produkt', 'lokal', 'person', 'trend', 'redigering']),
  }), 'Klippets beats i ordning, 2–7 st.', { minItems: 2, maxItems: 7 }),
  grundvarde: obj({
    premiss: s('stark: en fristående absurd eller igenkännbar idé som är rolig eller intressant i sig. medel: en idé finns men bär inte ensam. svag: idén är tunn och klippet lever på något annat. ingen: inget koncept, bara en visning, ett ögonblick eller ett tilltal.', ['stark', 'medel', 'svag', 'ingen']),
    bars_av: s('Det som främst bär klippets värde.', ['ide', 'struktur', 'karisma', 'produkt', 'produktion', 'trend', 'event']),
    klumpigt: s('Föreställ dig att en ovan anställd gör klippet stelt, med telefon och enkel klippning. Vad finns kvar och vad försvinner? En mening.'),
    utan_efterarbete: s('Finns värdet kvar i den versionen? ja, delvis eller nej.', ['ja', 'delvis', 'nej']),
    krok: s('Fångar de första två sekunderna tittaren med en fråga, en situation eller en spänning?', ['stark', 'svag', 'ingen']),
    vandning: b('Finns en uppbyggnad som leder till en vändning, punchline eller eskalering?'),
    planerat: b('Är klippet planerat innehåll, inte en fångst av något som redan händer?'),
    hojer_taket: b('Skulle det lära en annan verksamhet något den inte redan gör?'),
    hylla: s('Var klippet hör hemma i LeTrends bibliotek.', ['karna', 'mitten', 'situation', 'capcut_referens', 'ute']),
    hylla_skal: s('Varför den hyllan, en mening.'),
  }),
  sprak: obj({
    strategi: s('Vilken sorts konto klippet naturligt hör hemma hos. sketchvarld: en egen värld av sketcher med personalen, som ett tv-program. tilltal: en person talar till publiken med hög energi, frågor, tävlingar eller erbjudanden, ofta skarpt klippt. premium_stamning: finare verksamhet som visar miljö och mat med personlig ton. visning: mat och dryck i fokus. kampanj: kampanj eller reklam. trend: ett trendformat eller trendljud.', STRATEGIER),
    kantighet: s('familjar: barnsäkert och varmt. lekfull: fånigt och busigt. kantig: provocerande, mörk eller flörtig humor. vuxen: teman om sex, fylla eller relationer som inte passar alla.', KANTIGHET),
    tempo: s('Klippets tempo.', TEMPO),
    klippberoende: s('Hur mycket av värdet som sitter i klippning och efterarbete: lite, en del eller mycket.', ['lite', 'en_del', 'mycket']),
    person: s('fokus: personens karisma bär klippet. behallare: personen framför konceptet men vem som helst kan göra det. roll: personerna spelar roller i en sketch. ingen: ingen person bär klippet.', ['fokus', 'behallare', 'roll', 'ingen']),
    tilltal: s('Hur personerna förhåller sig till kameran.', ['spelad_scen', 'till_kamera', 'berattarrost', 'inget']),
    plattform: s('tiktok: personer i fokus, självironi, vardagligt. instagram: polerat, stämning, upplevelse. reklam: reklamfilm.', ['tiktok', 'instagram', 'reklam']),
  }),
  forlaga: obj({
    bundna_bilder: s('Hur stor del av bilderna som måste göras om för en annan sorts verksamhet för att poängen ska finnas kvar.', ['fa', 'halften', 'nastan_alla']),
    bunden_till: s('Vad bilderna är bundna till, t.ex. "en kebabgrill" eller "en bar med ölkranar", eller "inget".'),
    passar_samst: s('Vilken sorts verksamhet förlagan ligger längst ifrån, och varför, en mening.'),
  }),
  krav: v4.properties.krav,
  regler: v4.properties.regler,
  funktion: v4.properties.funktion,
  evergreen: v4.properties.evergreen,
  anpassningsrisk: v4.properties.anpassningsrisk,
})

export const prompt = konto => `Ett TikTok-klipp från @${konto}.

${LETREND}

${GRUNDVARDE}

${LINJE}

${UTFALL}

Din uppgift är att beskriva klippet så att en CM kan avgöra om det hör hemma i biblioteket och vilka kunder det passar. Börja med helheten: förstå vad som gör klippet till det det är innan du delar upp det. Bedöm klippet som det är, inte hur det skulle kunna bli. Titta noga efter skämt som ligger i redigeringen. Var konkret och nykter, och gissa inte. Svara på svenska.`

// E8: samma schema med den korta doktrinen.
import { KORT } from './doktrin.mjs'
export const promptKort = konto => `Ett TikTok-klipp från @${konto}.

${KORT}

Beskriv klippet så att en CM kan avgöra om det hör hemma i biblioteket och vilka kunder det passar. Börja med helheten. Bedöm klippet som det är. Var konkret och gissa inte. Svara på svenska.`
