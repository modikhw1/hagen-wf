// E14 (17 nov 2026): läsning i lager i stället för en skala. Förregistrering: data/format/e14/forregistrering.json.
//   sjalv    – aktören som spänningsfält, läst ur 20 klipp som video (fyra nyare klipp hålls undan)
//   mekanism – ett klipps motor skild från dess yta
//   mote     – bara text: vad händer när motorn förs in i samlingen
//   LOVABLE_KONTO=beacon node format/e14.mjs --steg sjalv|mekanism|mote [--modell google/gemini-4-argon] [--par 3] [--kund a,b] [--max n]
// Resultat: data/format/e14/<steg>/...
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'
import { byggBand, bandDelar } from './e13-band.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const STEG = varde('--steg', 'sjalv'), MODELL = varde('--modell', 'google/gemini-4-argon'), PAR = Number(varde('--par', 3)), MAX = Number(varde('--max', 1e9))
const KUNDER = varde('--kund')?.split(',')
// Annan modell än Argon skriver sina svar i egna mappar (<steg>-<modell>); lagren den läser är fortfarande Argons.
const SUFF = MODELL.includes('argon') ? '' : '-' + MODELL.split('gemini-').pop().replace('-preview', '')
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const E = path.join(DATA, 'format', 'e14'), PLAN = las(path.join(DATA, 'format', 'e13', 'plan.json'))
const litenFil = id => path.join(os.homedir(), 'Downloads', 'letrend-e13', id + '.mp4')
const obj = (properties, description) => ({ type: 'object', properties, required: Object.keys(properties), ...(description ? { description } : {}) })
const s = (description, en) => ({ type: 'string', description, ...(en ? { enum: en } : {}) })
const lista = (items, description) => ({ type: 'array', items, description })

// Undanhållna klipp: plats 1, 4, 7 och 10 bland de nyaste som finns på disk. Självet byggs på resten.
export function delning(konto) {
  const H = PLAN[konto].historik.klipp.filter(k => fs.existsSync(litenFil(k.id))).sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
  const undan = [0, 3, 6, 9].map(i => H[i]).filter(Boolean), u = new Set(undan.map(k => k.id))
  return { undan, kvar: H.filter(k => !u.has(k.id)).reverse() }
}

const sjalvSchema = obj({
  lasning: s('Vad är det här för aktör, läst som en samling och inte klipp för klipp? Fyra till sex meningar. Skriv det som bara syns när klippen ses tillsammans.'),
  spanningar: lista(obj({ mellan: s('De två polerna, t.ex. "stolthet över hantverket ↔ självdistans".'), lage: s('Var aktören står mellan dem, och hur det syns. Inte ett ord utan ett läge.'), belagg: s('Klippnummer.') }), 'Fyra till sex spänningar som aktören lever i. Det är kombinationen som är tonen, inte ett adjektiv.'),
  motorer: lista(obj({ motor: s('Vad som får klippen att fungera, sagt utan vara och lokal: t.ex. "statusvändning mellan gäst och personal", "en person som förklarar sitt hantverk för någon som frågar".'), sa_har: s('Hur aktören gör den till sin.'), klipp: s('Klippnummer.') }), 'De motorer som återkommer.'),
  granser: lista(obj({ aldrig: s('Något aktören aldrig är eller gör, som vore möjligt för ett ställe av samma sort.'), syns_i: s('Vad i samlingen som visar gränsen.'), sakerhet: s('', ['tydlig', 'trolig', 'gissning']) }), 'Negativa gränser. Identitet syns ofta skarpast i det som saknas.'),
  ankare: lista(obj({ klipp: s('Klippnummer.'), varfor: s('Varför just det klippet är mest aktören själv.') }), 'Två eller tre klipp som är koordinater för vad aktören är.'),
  trajektoria: obj({ riktning: s('Vart samlingen rör sig över tid.'), overgivet: s('Försök som gjordes en eller två gånger och sedan lämnades, eller "inget".') }),
  bar: s('Vem eller vad som bär samlingen: vilka människor, vad de har visat att de kan, hur många de är.'),
  falt: s('Var aktören står bland ställen av samma sort: vilken sorts plats och publik, vad den gör som alla gör, och vad som är eget.'),
})

const mekanismSchema = obj({
  motor: s('Det som får klippet att fungera, i en till två meningar, sagt UTAN vara, maträtt, lokal, stad, namn eller språk. Så abstrakt att samma mening kunde gälla ett helt annat ställe, men så precis att den skiljer klippet från andra klipp.'),
  forlopp: s('Hur motorn spelas ut, steg för steg, fortfarande utan vara, lokal och namn.'),
  hallning: s('Avsändarens hållning till sig själv och publiken i klippet: t.ex. stolt, självironisk, säljande, inbjudande, torr.'),
  krav: obj({ manniskor: s('Hur många framför kameran och vad de gör.'), formaga: s('Vad det kräver av dem: tala fritt, spela, tajma, bara synas.'), utsatthet: s('Hur mycket de bjuder på sig själva eller riskerar sin värdighet.', ['ingen', 'lite', 'mycket']) }),
  hantverk: s('Var värdet sitter.', ['i_iden', 'i_personen', 'i_bilden', 'i_klippningen', 'i_erbjudandet']),
  slitage: s('Hur motorn står i sin omgivning just nu.', ['egen', 'beprovad', 'utsliten_mall']),
  yta: s('Det utbytbara som INTE hör till motorn: vara, lokal, kläder, språk, ljudval, vilka personerna är. Det här fältet förs inte vidare.'),
})

const moteSchema = obj({
  vad_hander: s('Vad händer om aktören gör ett klipp med den här motorn? Tre meningar.'),
  forstarker: s('Vilken av aktörens spänningar eller motorer som förstärks, eller "ingen".'),
  bryter: s('Vilken gräns eller spänning som bryts, eller "ingen".'),
  offras: s('Vad aktören måste ge upp eller göra om för att bära motorn, eller "inget".'),
  hemma: { type: 'number', minimum: 1, maximum: 5, description: 'Hur väl klippet hör hemma i samlingen efter mötet. 1 = främmande kropp, 5 = som om det alltid funnits där.' },
  egen: { type: 'integer', minimum: 0, maximum: 100, description: 'Hur troligt det är att klippet faktiskt är aktörens eget, i procent.' },
})

const dir = n => { const d = path.join(E, n); fs.mkdirSync(d, { recursive: true }); return d }
const sjalvFil = k => path.join(dir('sjalv'), `${k}.json`), mekFil = id => path.join(dir('mekanism' + (/argon/.test(MODELL) ? '' : '-' + MODELL.split('gemini-').pop())), `${id}.json`), moteFil = (k, id) => path.join(dir('mote' + SUFF), `${k}__${id}.json`)

async function sjalv(konto) {
  if (fs.existsSync(sjalvFil(konto))) return 'fanns'
  const { kvar, undan } = delning(konto), band = await byggBand(`${konto}~sjalv`, kvar)
  const r = await beaconDelar({ modell: MODELL, schema: sjalvSchema, delar: [{ text: `En samling klipp från ett och samma konto, ${kvar.length} stycken, äldst först. Klippen ligger i ${band.length} band.` }, ...bandDelar(band), { text: `Läs samlingen som en helhet. Du ska inte bedöma den och inte sammanfatta klipp för klipp. Beskriv aktören bakom den som ett spänningsfält: vad den håller ihop, vad den vägrar vara, vad som driver klippen och vart det är på väg. Ett adjektiv som "familjär" eller "exklusiv" är inte ett svar; läget mellan två poler, med belägg, är det. Skriv på svenska.` }] })
  fs.writeFileSync(sjalvFil(konto), JSON.stringify({ konto, modell: r.modell, kvar: kvar.map(k => k.id), undan: undan.map(k => k.id), ms: r.ms, usage: r.usage, sjalv: r.data }, null, 1))
  return 'ny'
}

async function mekanism(id) {
  if (fs.existsSync(mekFil(id))) return 'fanns'
  if (!fs.existsSync(litenFil(id))) return 'saknar klipp'
  const r = await beaconDelar({ modell: MODELL, schema: mekanismSchema, delar: [{ fil: litenFil(id) }, { text: `Skilj klippets motor från dess yta. Motorn är det som skulle finnas kvar om allt utbytbart byttes: en annan vara, en annan lokal, andra människor, ett annat språk. Ytan är resten. Nämn aldrig vara, maträtt, lokal, stad eller namn i något annat fält än "yta". Skriv på svenska.` }] })
  fs.writeFileSync(mekFil(id), JSON.stringify({ id, modell: r.modell, ms: r.ms, usage: r.usage, mekanism: r.data }, null, 1))
  return 'ny'
}

async function mote(konto, id) {
  if (fs.existsSync(moteFil(konto, id))) return 'fanns'
  const mf = path.join(E, 'mekanism', `${id}.json`)
  if (!fs.existsSync(mf) || !fs.existsSync(sjalvFil(konto))) return 'saknar lager'
  const { yta, ...motor } = las(mf).mekanism
  const r = await beaconDelar({ modell: MODELL, schema: moteSchema, delar: [{ text: `AKTÖREN, läst ur dess samling av klipp:\n${JSON.stringify(las(sjalvFil(konto)).sjalv, null, 1)}` }, { text: `ETT KLIPP, beskrivet bara genom sin motor (varan, lokalen och människorna är borttagna):\n${JSON.stringify(motor, null, 1)}` }, { text: `Simulera mötet. Vad händer om den här motorn förs in i aktörens samling: vilken spänning förstärks, vilken gräns bryts, vad måste offras? Döm inte om klippet är bra. Klippet kan vara aktörens eget eller komma från någon helt annan; avgör hur troligt det första är. Skriv på svenska.` }] })
  fs.writeFileSync(moteFil(konto, id), JSON.stringify({ konto, id, modell: r.modell, ms: r.ms, usage: r.usage, mote: r.data }, null, 1))
  return 'ny'
}

const kunder = Object.keys(PLAN).filter(k => !KUNDER || KUNDER.includes(k))
const undanAlla = Object.keys(PLAN).flatMap(k => delning(k).undan.map(c => c.id))
const kandidater = k => [...new Set(PLAN[k].kandidater.filter(c => Number.isFinite(c.agare)).map(c => c.id))]
let jobb = []
if (STEG === 'sjalv') jobb = kunder.map(k => ({ namn: k, kor: () => sjalv(k) }))
// --ids fil.json: motor för en given lista av klipp
else if (STEG === 'mekanism' && varde('--ids')) jobb = las(varde('--ids')).map(id => ({ namn: id, kor: () => mekanism(id) }))
// --alla: motor för varje litet klipp som finns på disk (E17, motorgeometri i stor skala)
else if (STEG === 'mekanism' && args.includes('--alla')) jobb = fs.readdirSync(path.join(os.homedir(), 'Downloads', 'letrend-e13')).filter(f => /^[^.]+.*-\d+\.mp4$/.test(f) && !f.includes('.tmp')).map(f => f.replace(/\.mp4$/, '')).filter(id => !fs.existsSync(mekFil(id))).map(id => ({ namn: id, kor: () => mekanism(id) }))
else if (STEG === 'mekanism') jobb =[...new Set([...undanAlla, ...Object.keys(PLAN).flatMap(kandidater)])].map(id => ({ namn: id, kor: () => mekanism(id) }))
else for (const k of kunder) for (const id of [...new Set([...undanAlla, ...kandidater(k)])]) jobb.push({ namn: `${k} ← ${id}`, kor: () => mote(k, id) })
jobb = jobb.slice(0, MAX)
console.log(`${STEG}: ${jobb.length} jobb, ${PAR} samtidigt`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => {
  while (i < jobb.length) {
    const j = jobb[i++]
    try { const r = await j.kor(); if (r === 'ny') ny++; else if (r !== 'fanns') console.log(`  ${j.namn}: ${r}`) } catch (e) { fel++; console.log(`  FEL ${j.namn}: ${e.message.slice(0, 160)}`) }
  }
}))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.anrop} anrop, ${beaconKostnad.usd.toFixed(2)} USD`)
