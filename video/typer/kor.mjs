// Innehållstyper för skyddsräckena, föreslagna av Gemini.
//
//   node typer/kor.mjs forslag    fas 1: per klipp (video + våra scengränser) fria förslag
//   node typer/kor.mjs typlista   fas 2: förslagen slås ihop till en sluten typlista och scenfunktioner
//   node typer/kor.mjs marka      fas 3: varje klipp märks mot de slutna listorna
//   node typer/kor.mjs alla       1–3 i följd
//   --om        gör om även det som redan finns
//   --bara id   ett klipp
//
// Fas 1 och 3 ser videon (nedskalad till 480 bred, med ljud: humorn sitter ofta i ljudet) och får
// scenerna som analysen hittade, så att varje scen kan märkas på sin plats. Gemini ger dessutom en
// egen rörlighetsbedömning per scen, ett oberoende mått att jämföra rörlighetsmodellen mot.
// Allt cachas i data/typer/, med scengränsernas fingeravtryck: ändras analysen görs klippet om.
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { DATA, TMP } from '../analys/pipeline.mjs'
import { generera } from './gemini.mjs'

const MODELL_KLIPP = process.env.TYPER_MODELL ?? 'gemini-3.5-flash-lite'
const MODELL_LISTA = process.env.TYPER_MODELL_LISTA ?? 'gemini-3.1-pro-preview'
const UT = path.join(DATA, 'typer')
const SAMTIDIGT = 4

const args = process.argv.slice(2)
const fas = args.find(a => !a.startsWith('--') && args[args.indexOf(a) - 1] !== '--bara') ?? 'alla'
const om = args.includes('--om')
const bara = args.includes('--bara') ? args[args.indexOf('--bara') + 1] : null

const r2 = v => Math.round(v * 100) / 100
const lasJson = f => (fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null)
const skriv = (f, d) => { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, JSON.stringify(d, null, 2)) }

// ---------- klippen ----------
function klippen() {
  const kallor = lasJson(path.join(DATA, 'kallor.json')) ?? {}
  return fs.readdirSync(path.join(DATA, 'analys'))
    .filter(f => f.endsWith('.json'))
    .map(f => lasJson(path.join(DATA, 'analys', f)))
    .filter(a => a?.scener?.length && kallor[a.id]?.fil && fs.existsSync(kallor[a.id].fil))
    .filter(a => !bara || a.id === bara)
    .map(a => {
      const scener = a.scener.map(s => ({ i: s.i, start: r2(s.start), slut: r2(s.slut) }))
      return { id: a.id, konto: a.konto, fil: kallor[a.id].fil, langd: a.meta?.langd, scener, avtryck: crypto.createHash('sha1').update(JSON.stringify(scener)).digest('hex').slice(0, 12) }
    })
}

async function videoDel(k) {
  const ut = path.join(TMP, 'typer', `${k.id}.mp4`)
  if (!fs.existsSync(ut)) {
    fs.mkdirSync(path.dirname(ut), { recursive: true })
    await kor(verktyg.ffmpeg, ['-y', '-v', 'error', '-i', k.fil, '-vf', 'scale=480:-2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', ut])
  }
  return { inlineData: { mimeType: 'video/mp4', data: fs.readFileSync(ut).toString('base64') }, videoMetadata: { fps: 2 } }
}

const scenLista = k => k.scener.map(s => `scen ${s.i + 1}: ${s.start.toFixed(2)}–${s.slut.toFixed(2)} s`).join('\n')

async function iTakt(lista, n, f) {
  const ut = []
  let k = 0
  await Promise.all(Array.from({ length: Math.min(n, lista.length) }, async () => {
    while (k < lista.length) { const j = k++; ut[j] = await f(lista[j], j) }
  }))
  return ut
}

// ---------- fas 1: fria förslag ----------
const SYSTEM = `Du analyserar korta TikTok-klipp från restauranger och små lokala företag. Svara på svenska.
Syftet är att förstå hur klippets scenografi (kamera, utsnitt, rörelse, hur scenerna följer på varandra) tjänar innehållets mening, så att klippet senare kan filmas om på andra sätt utan att tappa det som gör det begripligt och roligt.`

const INTENT = ['A_underhallning', 'B_marknadsforing', 'C_operativt']
const MEKANIK = ['1_sound', '2_text', '3_script', '4_talking_head']

const forslagSchema = n => ({
  type: 'object',
  properties: {
    handling: { type: 'string', description: 'Vad som händer i klippet, 1–2 meningar.' },
    syfte: { type: 'string', description: 'Vad klippet vill åstadkomma hos tittaren, 1 mening.' },
    primary_intent: { type: 'string', enum: INTENT, description: 'A underhållning (humor, trend, persona), B marknadsföring (produkt, erbjudande, plats), C operativt (öppettider, nyheter, praktisk info).' },
    andel_marknadsforing: { type: 'number', description: '0–1: hur mycket av klippet som säljer något, även när det är förpackat som humor.' },
    mechanic: { type: 'string', enum: MEKANIK, description: '1 ljudet bär (trendljud, lipsync), 2 skärmtexten bär, 3 manus/dialog bär, 4 en person pratar i kameran.' },
    typ: {
      type: 'object',
      properties: {
        namn: { type: 'string', description: 'Ditt förslag på innehållstyp, 2–4 ord, så att liknande klipp kan grupperas (t.ex. "ren humor", "humor med produkt", "notis").' },
        definition: { type: 'string', description: 'Vad som definierar typen, 1 mening.' },
      },
      required: ['namn', 'definition'],
    },
    ton: { type: 'string', description: 'Tonen i några ord.' },
    scener: {
      type: 'array', minItems: n, maxItems: n,
      items: {
        type: 'object',
        properties: {
          scen: { type: 'integer' },
          vad: { type: 'string', description: 'Vad som syns och händer i scenen, kort.' },
          funktion: { type: 'string', description: 'Scenens funktion i klippet med ett par ord (t.ex. krok, etablering, uppbyggnad, vändning, punchline, reaktion, produktbild, erbjudande, uppmaning).' },
          kamera: { type: 'string', description: 'Hur scenen är filmad: utsnitt, vinkel, kamerarörelse.' },
          varfor: { type: 'string', description: 'Varför scenen är filmad så, sett till dess funktion. Vad skulle gå förlorat med ett annat sätt?' },
          rorlighet: { type: 'integer', minimum: 1, maximum: 10, description: 'Hur rörlig och expansiv bilden upplevs som helhet: 1 stilla och subtil, 10 bilden är i ständig rörelse.' },
        },
        required: ['scen', 'vad', 'funktion', 'kamera', 'varfor', 'rorlighet'],
      },
    },
    scenografi: { type: 'string', description: 'Hur klippet är komponerat som helhet (enhetligt eller varierat, lugnt eller rörligt) och varför det passar syftet, 1–2 meningar.' },
  },
  required: ['handling', 'syfte', 'primary_intent', 'andel_marknadsforing', 'mechanic', 'typ', 'ton', 'scener', 'scenografi'],
})

async function forslag() {
  const lista = klippen()
  let ore = 0
  await iTakt(lista, SAMTIDIGT, async k => {
    const fil = path.join(UT, 'forslag', `${k.id}.json`)
    const fore = lasJson(fil)
    if (!om && fore?.avtryck === k.avtryck && fore.modell === MODELL_KLIPP) return
    const text = `Klippet är ${k.langd?.toFixed(1)} s och har delats upp i ${k.scener.length} scener av en automatisk analys (bildklipp):\n${scenLista(k)}\n\nBeskriv klippet och varje scen i den ordningen. Om en gräns verkar fel, säg det i scenens "vad".`
    const r = await generera({ modell: MODELL_KLIPP, system: SYSTEM, parts: [await videoDel(k), { text }], schema: forslagSchema(k.scener.length) })
    ore += r.ore ?? 0
    skriv(fil, { id: k.id, konto: k.konto, avtryck: k.avtryck, modell: r.modell, ore: r.ore, tokens: r.usage?.promptTokenCount, scengranser: k.scener, ...r.data })
    console.log(`${k.id}: ${r.data.typ.namn} · ${r.data.primary_intent} · ${r.ms} ms · ${r.ore?.toFixed(2)} öre`)
  })
  console.log(`fas 1 klar: ${lista.length} klipp, ${ore.toFixed(1)} öre`)
}

// ---------- fas 2: sluten typlista ----------
const typlistaSchema = {
  type: 'object',
  properties: {
    typer: {
      type: 'array', minItems: 3, maxItems: 8,
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'kort id i snake_case utan å, ä, ö' },
          namn: { type: 'string' },
          definition: { type: 'string', description: 'Vad som avgör att ett klipp hör hit, så att två personer märker lika.' },
          skiljer_fran: { type: 'string', description: 'Gränsen mot de närmaste andra typerna.' },
          primary_intent: { type: 'string', enum: INTENT },
          oppning: { type: 'string', description: 'Vad öppningen (första scenen eller sekunderna) klassiskt gör och hur den brukar vara filmad i typen.' },
          mitt: { type: 'string', description: 'Samma för mitten.' },
          slut: { type: 'string', description: 'Samma för slutet.' },
          scenografi: { type: 'string', description: 'Vad som klassiskt förväntas av kamera och rytm i typen, och vad som skulle bryta mot typen.' },
          exempel: { type: 'array', items: { type: 'string' }, description: 'klipp-id ur underlaget' },
        },
        required: ['id', 'namn', 'definition', 'skiljer_fran', 'primary_intent', 'oppning', 'mitt', 'slut', 'scenografi', 'exempel'],
      },
    },
    funktioner: {
      type: 'array', minItems: 4, maxItems: 12,
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'kort id i snake_case utan å, ä, ö' },
          namn: { type: 'string' },
          definition: { type: 'string' },
          kamera: { type: 'string', description: 'Vad funktionen kräver eller tål av kameran: vad som måste synas, hur mycket rörelse den bär.' },
        },
        required: ['id', 'namn', 'definition', 'kamera'],
      },
    },
    resonemang: { type: 'string', description: 'Kort: hur du kom fram till indelningen och vad som är osäkert.' },
  },
  required: ['typer', 'funktioner', 'resonemang'],
}

async function typlista() {
  const f = fs.readdirSync(path.join(UT, 'forslag')).map(x => lasJson(path.join(UT, 'forslag', x)))
  const underlag = f.map(x => ({
    id: x.id, konto: x.konto, handling: x.handling, syfte: x.syfte, intent: x.primary_intent, marknadsforing: x.andel_marknadsforing,
    mekanik: x.mechanic, forslag: `${x.typ.namn}: ${x.typ.definition}`, ton: x.ton, scenografi: x.scenografi,
    scener: x.scener.map((s, i) => `${i + 1}. [${s.funktion}] ${s.vad} · ${s.kamera} · rörlighet ${s.rorlighet}`),
  }))
  const text = `Här är ${underlag.length} klipp, var och ett beskrivet av en modell som såg videon, med ett fritt förslag på innehållstyp och en funktion per scen.

Uppgift:
1. Föreslå en sluten lista med innehållstyper (3–8) som täcker klippen. Typerna ska vara användbara som skyddsräcken när ett klipp filmas om: två klipp av samma typ ska ha liknande förväntningar på hur öppning, mitt och slut är komponerade. Utgå från förslagen men slå ihop synonymer och dela där förväntningarna på scenografin skiljer sig (t.ex. ren humor, humor som bär en produkt, notis/information). Varje klipp ska passa i exakt en typ.
2. Föreslå en sluten lista med scenfunktioner (4–12) som täcker de fria funktionerna i underlaget.
Grunda allt i underlaget, inte i allmänna antaganden.

Underlag (JSON):
${JSON.stringify(underlag, null, 1)}`
  const r = await generera({ modell: MODELL_LISTA, parts: [{ text }], schema: typlistaSchema, temperatur: 0.3 })
  skriv(path.join(UT, 'typer.json'), { modell: r.modell, ore: r.ore, skapad: new Date().toISOString(), klipp: underlag.length, ...r.data })
  console.log(`fas 2 klar: ${r.data.typer.map(t => t.namn).join(', ')} · ${r.data.funktioner.length} scenfunktioner · ${r.ore?.toFixed(1)} öre`)
}

// ---------- fas 3: märkning mot de slutna listorna ----------
async function marka() {
  const tl = lasJson(path.join(UT, 'typer.json'))
  if (!tl) throw new Error('typer.json saknas, kör typlista först')
  const lista = klippen()
  const typId = tl.typer.map(t => t.id)
  const funkId = tl.funktioner.map(t => t.id)
  const definitioner = `Innehållstyper:\n${tl.typer.map(t => `- ${t.id} (${t.namn}): ${t.definition} Gräns: ${t.skiljer_fran}`).join('\n')}\n\nScenfunktioner:\n${tl.funktioner.map(t => `- ${t.id} (${t.namn}): ${t.definition}`).join('\n')}`
  let ore = 0
  await iTakt(lista, SAMTIDIGT, async k => {
    const fil = path.join(UT, 'markning', `${k.id}.json`)
    const fore = lasJson(fil)
    if (!om && fore?.avtryck === k.avtryck && fore.lista === tl.skapad) return
    const schema = {
      type: 'object',
      properties: {
        typ: { type: 'string', enum: typId },
        sakerhet: { type: 'number', description: '0–1' },
        alternativ: { type: 'string', enum: [...typId, 'ingen'], description: 'näst bästa typ, eller ingen' },
        motivering: { type: 'string', description: '1 mening' },
        scener: {
          type: 'array', minItems: k.scener.length, maxItems: k.scener.length,
          items: { type: 'object', properties: { scen: { type: 'integer' }, funktion: { type: 'string', enum: funkId }, rorlighet: { type: 'integer', minimum: 1, maximum: 10 } }, required: ['scen', 'funktion', 'rorlighet'] },
        },
        // takter: klippets dramaturgi i tid, oberoende av bildklippen (en enda tagning har också öppning, mitt och slut)
        takter: {
          type: 'array', minItems: 1, maxItems: 10,
          description: 'Klippets takter i tidsordning, utan luckor från 0 till slutet. En takt slutar där funktionen byts, oavsett om bilden klipps.',
          items: { type: 'object', properties: { start: { type: 'number' }, slut: { type: 'number' }, funktion: { type: 'string', enum: funkId } }, required: ['start', 'slut', 'funktion'] },
        },
      },
      required: ['typ', 'sakerhet', 'alternativ', 'motivering', 'scener', 'takter'],
    }
    const text = `${definitioner}\n\nKlippet är ${k.langd?.toFixed(1)} s med scenerna (bildklipp):\n${scenLista(k)}\n\nMärk klippets typ, varje scens funktion och klippets takter med listorna ovan. Takterna följer dramaturgin i tid, inte bildklippen: en lång tagning kan ha flera takter, och flera korta scener kan vara en takt. Rörlighet per scen: hur rörlig och expansiv bilden upplevs, 1 stilla och subtil, 10 bilden är i ständig rörelse.`
    const r = await generera({ modell: MODELL_KLIPP, system: SYSTEM, parts: [await videoDel(k), { text }], schema })
    ore += r.ore ?? 0
    skriv(fil, { id: k.id, avtryck: k.avtryck, lista: tl.skapad, modell: r.modell, ore: r.ore, ...r.data })
    console.log(`${k.id}: ${r.data.typ} (${r.data.sakerhet}) · ${r.data.takter.map(s => `${s.funktion} ${s.start}–${s.slut}`).join(" → ")}`)
  })
  console.log(`fas 3 klar: ${lista.length} klipp, ${ore.toFixed(1)} öre`)
}

const faser = { forslag, typlista, marka }
for (const f of fas === 'alla' ? ['forslag', 'typlista', 'marka'] : [fas]) {
  if (!faser[f]) { console.error(`okänd fas ${f}`); process.exit(1) }
  await faser[f]()
}
