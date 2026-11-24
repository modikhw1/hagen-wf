// E18 (17 nov 2026): LeTrend läst som aktör ur ägarens råa transkript. Förregistrering: data/format/e18/forregistrering.json.
//   letrend – ett anrop: transkript 2–6 → LeTrend-självet
//   mote    – bara text: LeTrend-självet + ett klipps motor → hemma 1–5
//   LOVABLE_KONTO=beacon node format/e18.mjs --steg letrend|mote [--urval pass7|bibliotek] [--par 3] [--max n]
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const STEG = varde('--steg', 'letrend'), MODELL = varde('--modell', 'google/gemini-4-argon'), PAR = Number(varde('--par', 3)), MAX = Number(varde('--max', 1e9)), URVAL = varde('--urval', 'pass7')
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
// Annan modell än Argon skriver sina svar i egna mappar (<steg>-<modell>); lagren den läser är fortfarande Argons.
const SUFF = MODELL.includes('argon') ? '' : '-' + MODELL.split('gemini-').pop().replace('-preview', '')
const E = path.join(DATA, 'format', 'e18'), E14 = path.join(DATA, 'format', 'e14')
const TR = path.join(os.homedir(), 'Desktop', 'hagen-ui', '_anteckningar', 'transkript')
const obj = (properties, description) => ({ type: 'object', properties, required: Object.keys(properties), ...(description ? { description } : {}) })
const s = (description, en) => ({ type: 'string', description, ...(en ? { enum: en } : {}) })
const lista = (items, description) => ({ type: 'array', items, description })

const letrendSchema = obj({
  lasning: s('Vad är LeTrend, läst ur hur ägaren talar om klipp? Fem till åtta meningar. Skriv det som bara syns när alla hans omdömen ses tillsammans, inte det han säger rakt ut en gång.'),
  spanningar: lista(obj({ mellan: s('De två polerna.'), lage: s('Var ägaren står mellan dem, och hur det syns i hans omdömen.'), belagg: s('Ett eller två korta citat av ägaren, ordagrant på engelska.') }), 'Fem till åtta spänningar som ägarens smak lever i. Läget är svaret, inte ett adjektiv.'),
  motorer: lista(obj({ motor: s('En sorts motor i klipp som ägaren dras till, sagt utan vara och lokal.'), varfor: s('Vad han ser i den.'), belagg: s('Citat eller klipp han berömde.') }), 'De motorer ägaren återkommer till med värme.'),
  granser: lista(obj({ aldrig: s('Något LeTrend inte är, enligt hur ägaren avfärdar klipp.'), syns_i: s('Citat eller exempel.'), sakerhet: s('', ['tydlig', 'trolig', 'gissning']) }), 'Negativa gränser.'),
  ankare: lista(obj({ klipp: s('Hur klippet beskrivs i transkriptet.'), varfor: s('Varför just det är LeTrend när det är som bäst, med ägarens ord.') }), 'Tre till fem klipp som ägaren behandlar som koordinater.'),
  sa_laser_han: s('Hur ägaren läser ett klipp: vad han ser först, vad som avgör, vad han struntar i, och i vilken ordning. Fem till åtta meningar.'),
  motsagelser: s('Ställen där ägaren säger emot sig själv eller ändrar sig. De ska inte slätas ut.'),
  miles: s('Begrepp och kriterier som kommer från Miles frågor och inte från ägaren, och som därför INTE har räknats in ovan.'),
})
const moteSchema = obj({
  vad_hander: s('Vad händer om klippet läggs i LeTrends bibliotek som förlaga? Tre meningar.'),
  forstarker: s('Vilken av LeTrends spänningar eller motorer klippet förstärker, eller "ingen".'),
  bryter: s('Vilken gräns det bryter, eller "ingen".'),
  hemma: { type: 'number', minimum: 1, maximum: 5, description: 'Hur väl klippet hör hemma i LeTrends bibliotek. 1 = främmande kropp, 5 = som ett av ankarklippen.' },
})

async function letrend() {
  const ut = path.join(E, `letrend${SUFF}.json`); if (fs.existsSync(ut)) return 'fanns'
  const filer = ['transkript2.txt', 'transkript3.txt', 'transkript 4.txt', 'transkript 5.txt', 'transkript 6.txt']
  const delar = filer.map((f, i) => ({ text: `SAMTAL ${i + 1} (${f}):\n${fs.readFileSync(path.join(TR, f), 'utf8')}` }))
  delar.push({ text: `Det här är fem samtal där ägaren till LeTrend ser klipp från restauranger, barer och kaféer och säger vad han tycker. En röstassistent (Miles) ställer frågorna. I utskriften står BÅDA under "Me:", så du måste själv skilja dem: Miles läser upp beskrivningar, frågar och sammanfattar; ägaren svarar, tvekar, resonerar och invänder. Bara ägarens egna ord räknas. Kriterier som Miles läser upp är inte ägarens, om han inte själv tar dem till sig eller gör om dem.\n\nLäs LeTrend som en aktör. Du ska inte sammanfatta samtalen och inte göra en regellista. Beskriv det spänningsfält ägarens smak lever i: vad han håller ihop, vilka motorer han dras till, vad LeTrend vägrar vara, vilka klipp som är hans koordinater, och hur han läser. Skriv på svenska, citera ägaren på engelska.` })
  const r = await beaconDelar({ modell: MODELL, schema: letrendSchema, delar })
  fs.mkdirSync(E, { recursive: true }); fs.writeFileSync(ut, JSON.stringify({ modell: r.modell, filer, ms: r.ms, usage: r.usage, letrend: r.data }, null, 1))
  return 'ny'
}

const motor = id => { for (const d of (varde('--motorer') ? [varde('--motorer')] : ['mekanism', 'mekanism-3.8-flash'])) { const f = path.join(E14, d, `${id}.json`); if (fs.existsSync(f)) return { fran: d, m: las(f).mekanism } } return null }
async function mote(id) {
  const dir = path.join(E, 'mote' + SUFF); fs.mkdirSync(dir, { recursive: true })
  const ut = path.join(dir, `${id}.json`); if (fs.existsSync(ut)) return 'fanns'
  const M = motor(id); if (!M) return 'saknar motor'
  const { yta, ...m } = M.m, L = las(path.join(E, `letrend${SUFF}.json`)).letrend, { miles, ...sjalv } = L
  const r = await beaconDelar({ modell: MODELL, schema: moteSchema, delar: [{ text: `LETREND, läst som aktör ur hur ägaren talar om klipp:\n${JSON.stringify(sjalv, null, 1)}` }, { text: `ETT KLIPP, beskrivet bara genom sin motor (varan, lokalen och människorna är borttagna):\n${JSON.stringify(m, null, 1)}` }, { text: `Simulera mötet. Vad händer om det här klippet läggs i LeTrends bibliotek som förlaga för andra verksamheter: vilken spänning förstärks, vilken gräns bryts? Läs klippet så som ägaren läser. Skriv på svenska.` }] })
  fs.writeFileSync(ut, JSON.stringify({ id, motor_fran: M.fran, modell: r.modell, ms: r.ms, usage: r.usage, mote: r.data }, null, 1))
  return 'ny'
}

let jobb
if (STEG === 'letrend') jobb = [{ namn: 'letrend', kor: letrend }]
else {
  let ids
  if (URVAL === 'pass7') ids = las(path.join(DATA, 'format', 'harness', 'pass7', 'forregistrering.json')).par.flatMap(p => [p.vanster.id, p.hoger.id])
  else ids = Object.values(las(path.join(DATA, 'format', 'harness', 'bibliotek-v6.json')).hyllor).flat().map(k => k.id).filter(id => motor(id))
  jobb = [...new Set(ids)].slice(0, MAX).map(id => ({ namn: id, kor: () => mote(id) }))
}
console.log(`${STEG}: ${jobb.length} jobb, ${PAR} samtidigt`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => { while (i < jobb.length) { const j = jobb[i++]; try { const r = await j.kor(); if (r === 'ny') ny++; else if (r !== 'fanns') console.log(`  ${j.namn}: ${r}`) } catch (e) { fel++; console.log(`  FEL ${j.namn}: ${e.message.slice(0, 160)}`) } } }))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.usd.toFixed(2)} USD`)
