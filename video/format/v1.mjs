// Formatkort v1: schema, LeTrends principer och prompten. Delas av kort1.mjs (video) och doma.mjs (text).
const s = (description, extra = {}) => ({ type: 'string', description, ...extra })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description) => ({ type: 'array', items, description })

const INBJUDAN = ['igenkanning', 'overraskning', 'insyn', 'personlighet', 'begar', 'erbjudande', 'nyfikenhet', 'deltagande']
export const VERKSAMHETER = ['kafe', 'pizzeria_kebab', 'bar', 'gym', 'butik', 'livsmedelsbutik']

export const schema = obj({
  handling: s('Vad som händer, i ordning, 1–3 meningar. Ta med repliker och skärmtext som bär poängen.'),
  karna: s('Idén i en mening, utan verksamhetens namn, rätter eller personer: vad gör klippet sevärt?'),
  mall: s('Idén som återanvändbar mall med [platshållare].'),
  platser: arr(obj({ plats: s('Platshållarens namn.'), har: s('Vad den är i det här klippet.') }), 'Det som kan bytas ut. 1–5 st.'),
  last: arr(s('En sak.'), 'Det som måste finnas kvar för att idén ska fungera. 1–4 st.'),
  bartest: obj({
    skal: s('Tänk dig att en vanlig anställd utan vana framför kameran får en kort instruktion och spelar in idén. Vad händer med klippet? 1–2 meningar. Skriv detta först.'),
    betyg: n(1, 5, '1 = faller helt utan just den här personen, lokalen eller rätten. 3 = blir klart sämre men håller. 5 = bär lika bra.'),
    hanger_pa: arr(s('', { enum: ['person', 'lokal', 'rekvisita', 'nisch', 'produkt', 'trend', 'produktion', 'inget'] }), 'Det klippet hänger på så att det inte går att flytta. person: just den personens talang eller utseende. lokal: just den här lokalen. rekvisita: ett föremål andra inte har. nisch: något bara den här verksamheten gör. produkt: just den rätten eller varan. trend: ett ljud eller en meme. produktion: foto, klippning eller effekter. inget: går att flytta.'),
  }),
  vardet: obj({
    ide: n(0, 100, 'Andel av klippets dragningskraft från idén, manuset eller vändningen.'),
    framforande: n(0, 100, 'Från personernas timing, karisma eller skådespel.'),
    produktion: n(0, 100, 'Från foto, ljus, klippning, grafik eller effekter.'),
    produkt: n(0, 100, 'Från maten, varan eller lokalen i sig.'),
    trend: n(0, 100, 'Från ett trendljud, en meme eller ett känt format.'),
  }),
  visning: obj({
    grad: n(0, 3, 'Hur mycket som vilar på montage, grafik och snygga bilder av mat eller varor. 0 = inget. 1 = ett inslag i en idé som bärs av annat. 2 = en bärande del. 3 = hela klippet är visningen.'),
    ratt: s('Vad rätten eller varan bär. ingen: den är inte poängen. unik: den är ovanlig eller tillagningen är intressant i sig. aptitlig: den ser god ut. signatur: just verksamhetens egen specialitet är poängen.', { enum: ['ingen', 'unik', 'aptitlig', 'signatur'] }),
  }),
  roll: s('Klippets roll i en serie för en lekfull verksamhet. karna: en idé som bärs av personer och humor och kan formas för vilken verksamhet som helst. inslag: godkänt men inte centralt, till exempel ett visningsklipp, en nyhet eller ett erbjudande. utanfor: passar inte.', { enum: ['karna', 'inslag', 'utanfor'] }),
  ton: obj({
    sjalvdistans: n(1, 5, '1 = klassisk reklam som tar sig själv på allvar. 5 = leker med eller driver med förväntningen att sälja.'),
    inside: n(1, 5, '1 = inget som binder till ett gäng. 5 = känns som ett tv-program eller ett inside-skämt med personer man lär känna.'),
    livlighet: n(1, 5, '1 = stilla och neutralt. 5 = lekfullt och livligt.'),
    varumarkesrisk: n(1, 5, '1 = ingen risk. 5 = vulgärt, elakt eller kan skada varumärket.'),
  }),
  inbjudan: s('Främsta skälet att tittaren stannar: igenkanning, overraskning, insyn (bakom kulisserna), personlighet, begar (vill äta eller ha), erbjudande, nyfikenhet, deltagande (gissa, svara, tävla).', { enum: INBJUDAN }),
  salj: s('ingen (syns inte), fond (syns naturligt), vavd (produkten är del av poängen), direkt (visning, erbjudande, uppmaning).', { enum: ['ingen', 'fond', 'vavd', 'direkt'] }),
  troskel: obj({
    produktionskrav: n(1, 5, '1 = en telefon, en tagning. 3 = några klipp och enkel text. 5 = flera vinklar, ljussättning, avancerad klippning eller effekter.'),
    personer: n(0, 10, 'Hur många personer som behövs.'),
    agerande: n(1, 5, '1 = ingen behöver spela. 3 = en enkel replik eller reaktion. 5 = kräver skådespelartalang eller exakt timing.'),
  }),
  tankehojd: n(1, 5, '1 = filmar det som ändå händer eller visar bara produkten. 3 = en enkel idé. 5 = en genomtänkt idé med uppbyggnad och vändning.'),
  trend: s('egen, anpassad_trend (känt format eller ljud med egen vinkel) eller ren_trend.', { enum: ['egen', 'anpassad_trend', 'ren_trend'] }),
  forlust: arr(obj({
    verksamhet: s('', { enum: VERKSAMHETER }),
    vad_gar_forlorat: s('Vad av poängen som går förlorat där, eller "inget".'),
    passar: n(1, 5, 'Var sträng: 5 bara om inget av poängen går förlorat, 3 om idén måste byggas om, 1 om den inte går att göra.'),
  }), `En rad var för: ${VERKSAMHETER.join(', ')}.`),
  svaghet: s('Det som gör klippet mindre användbart som mall för andra verksamheter.'),
})

export const KONSTITUTION = `LeTrend hjälper lokala verksamheter (restauranger, barer, kaféer, senare gym och butiker) att göra TikTok. Principerna:
- Ett klipp är värdefullt som mall om idén bär även när en mindre skicklig anställd spelar ut den efter en instruktion. Det som hänger på just den personen, lokalen, en rekvisita eller en nisch som bara den verksamheten har, är inte värdefullt som mall.
- Montage, grafik och snygga mat- eller varubilder är godkända inslag i en serie men inte kärnan. Ett visningsklipp kan bära för att rätten är unik och intressant att se lagas, eller bara för att den ser god ut.
- De bästa profilerna väver in verksamheten i klipp där människorna står i fokus, med sketcher och humor, så att det känns som ett tv-program eller ett inside-skämt med personer man lär känna.
- TikTok driver med klassisk marknadsföring. LeTrend är för verksamheter som inte tar sig själva på för stort allvar men vill ha bra resultat. Proffsigt utförande är tillåtet. Vulgärt eller varumärkesskadligt är det inte.
Bedöm klippet som det är, även om det inte följer principerna.`

export const prompt = (konto, VARIANT) => `Ett TikTok-klipp från @${konto}.

Syftet är att förstå klippets IDÉ, så att en content manager kan anpassa den till en annan verksamhet, vars egen personal sedan spelar in sin version med en telefon. Skilj på idén (det som går att ta med sig), utförandet (personerna, fotot, klippningen) och det som bara gäller just den här verksamheten.
${VARIANT === 'konst' ? `\n${KONSTITUTION}\n` : ''}
Var konkret och nykter. Bedöm det du ser och hör, inte det du gissar. Svara på svenska.`

