// E16 (17 nov 2026): läsning i serie. Förregistrering: data/format/e16/forregistrering.json.
//   roller – pass 2: samma band som E14, självet som lins, en roll per klipp (bärande, stöd, ihopkastat, avstickare)
//   sjalv2 – pass 3: självet omskrivet ur de bärande klippen (bara text)
//   mote2  – samma möte som E14 men mot sjalv2 (bara undanhållna klipp)
//   LOVABLE_KONTO=beacon node format/e16.mjs --steg roller|sjalv2|mote2 [--par 2] [--kund a,b]
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'
import { byggBand } from './e13-band.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const STEG = varde('--steg', 'roller'), MODELL = varde('--modell', 'google/gemini-4-argon'), PAR = Number(varde('--par', 2)), KUNDER = varde('--kund')?.split(',')
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
// Annan modell än Argon skriver sina svar i egna mappar (<steg>-<modell>); lagren den läser är fortfarande Argons.
const SUFF = MODELL.includes('argon') ? '' : '-' + MODELL.split('gemini-').pop().replace('-preview', '')
const E14 = path.join(DATA, 'format', 'e14'), E = path.join(DATA, 'format', 'e16'), PLAN = las(path.join(DATA, 'format', 'e13', 'plan.json'))
const litenFil = id => path.join(os.homedir(), 'Downloads', 'letrend-e13', id + '.mp4')
const obj = (properties, description) => ({ type: 'object', properties, required: Object.keys(properties), ...(description ? { description } : {}) })
const s = (description, en) => ({ type: 'string', description, ...(en ? { enum: en } : {}) })
const dir = n => { const d = path.join(E, n); fs.mkdirSync(d, { recursive: true }); return d }
const tid = x => `${Math.floor(x / 60)}:${String(x % 60).padStart(2, '0')}`

const rollSchema = obj({
  klipp: { type: 'array', description: 'En rad per klipp, i nummerordning, alla klipp.', items: obj({
    nr: { type: 'integer' },
    roll: s('barande = aktören när den är sig själv med avsikt; stod = rimligt i samlingen men bär inget eget; ihopkastat = utfyllnad utan tanke, lagt upp för att något skulle upp; avstickare = ett genomtänkt försök som inte är aktören.', ['barande', 'stod', 'ihopkastat', 'avstickare']),
    avsikt: { type: 'integer', minimum: 1, maximum: 5, description: 'Hur mycket tanke och avsikt som syns i klippet, oavsett om det lyckas. 1 = ingen, 5 = genomtänkt.' },
    uttrycker: s('Vilken av aktörens spänningar eller motorer klippet uttrycker, eller "ingen".'),
    varfor: s('En mening.'),
  }) },
  brus: s('Vad i samlingen som är brus: vilken sorts klipp som ligger där utan att säga något om aktören.'),
})
const sjalv2Schema = k => obj({ ...k.properties, brus: s('Det i samlingen som inte hör till aktören och som läsningen bortser från.') })

async function roller(konto) {
  const ut = path.join(dir('roller'), `${konto}.json`); if (fs.existsSync(ut)) return 'fanns'
  const S = las(path.join(E14, 'sjalv', `${konto}.json`))
  const H = PLAN[konto].historik.klipp.filter(k => S.kvar.includes(k.id)).sort((a, b) => S.kvar.indexOf(a.id) - S.kvar.indexOf(b.id))
  const band = await byggBand(`${konto}~sjalv`, H)
  // Bandtexten utan visningar: utfallet får inte synas (HE16a)
  const delar = [{ text: `En samling klipp från ett och samma konto, ${H.length} stycken, äldst först, i ${band.length} band.` }]
  for (const [i, b] of band.entries()) { delar.push({ text: `Band ${i + 1} av ${band.length}, klippnumret står i bildens övre vänstra hörn:\n${b.klipp.map(c => `Klipp ${c.nr} börjar vid ${tid(c.start)}.`).join('\n')}` }); delar.push({ fil: b.fil }) }
  delar.push({ text: `En första läsning av samlingen gav den här bilden av aktören:\n${JSON.stringify(S.sjalv, null, 1)}` })
  delar.push({ text: `Läs samlingen en gång till, nu med den bilden som lins. Ett konto lägger upp både klipp som är gjorda med avsikt och klipp som bara kastats ihop för att något skulle upp. Alla klipp säger inte lika mycket om aktören. Ange för varje klipp vilken roll det har i samlingen. Bedöm avsikten och rollen ur det som syns och hörs i klippet, inte ur hur väl klippet verkar ha gått. Säg emot den första läsningen där klippen visar att den hade fel. Skriv på svenska.` })
  const r = await beaconDelar({ modell: MODELL, schema: rollSchema, delar })
  fs.writeFileSync(ut, JSON.stringify({ konto, modell: r.modell, ids: H.map(k => k.id), ms: r.ms, usage: r.usage, ...r.data }, null, 1))
  return 'ny'
}

// Schemat för självet lånas ur ett sparat själv (samma fält), så att pass 3 skriver samma form.
const form = v => Array.isArray(v) ? { type: 'array', items: form(v[0] ?? '') } : v && typeof v === 'object' ? obj(Object.fromEntries(Object.entries(v).map(([k, x]) => [k, form(x)]))) : { type: 'string' }
async function sjalv2(konto) {
  const ut = path.join(dir('sjalv2' + SUFF), `${konto}.json`); if (fs.existsSync(ut)) return 'fanns'
  const rf = path.join(E, 'roller', `${konto}.json`); if (!fs.existsSync(rf)) return 'saknar roller'
  const S = las(path.join(E14, 'sjalv', `${konto}.json`)), R = las(rf)
  const r = await beaconDelar({ modell: MODELL, schema: sjalv2Schema(form(S.sjalv)), delar: [{ text: `FÖRSTA LÄSNINGEN av en aktör, gjord ur alla klipp i samlingen som om de vägde lika:\n${JSON.stringify(S.sjalv, null, 1)}` }, { text: `ANDRA LÄSNINGEN, klipp för klipp, med rollen varje klipp har i samlingen:\n${JSON.stringify({ klipp: R.klipp, brus: R.brus }, null, 1)}` }, { text: `Skriv om bilden av aktören så att den bara vilar på de bärande klippen. Stödklipp får bekräfta men inte bära. Ihopkastade klipp och avstickare ska inte forma bilden; namnge dem som brus. Ta bort spänningar, motorer och gränser som bara hade stöd i brus, och skärp dem som de bärande klippen visar. Behåll klippnumren som belägg. Skriv på svenska.` }] })
  fs.writeFileSync(ut, JSON.stringify({ konto, modell: r.modell, kvar: S.kvar, undan: S.undan, ms: r.ms, usage: r.usage, sjalv: r.data }, null, 1))
  return 'ny'
}

const moteSchema = obj({ vad_hander: s('Tre meningar.'), forstarker: s(''), bryter: s(''), offras: s(''), hemma: { type: 'number', minimum: 1, maximum: 5 }, egen: { type: 'integer', minimum: 0, maximum: 100 } })
async function mote2(konto, id) {
  const ut = path.join(dir('mote2' + SUFF), `${konto}__${id}.json`); if (fs.existsSync(ut)) return 'fanns'
  const sf = path.join(E, 'sjalv2' + SUFF, `${konto}.json`), mf = path.join(E14, 'mekanism', `${id}.json`); if (!fs.existsSync(sf) || !fs.existsSync(mf)) return 'saknar lager'
  const { yta, ...motor } = las(mf).mekanism
  // Samma ordalydelse som E14 mote, så att bara självet skiljer
  const r = await beaconDelar({ modell: MODELL, schema: moteSchema, delar: [{ text: `AKTÖREN, läst ur dess samling av klipp:\n${JSON.stringify(las(sf).sjalv, null, 1)}` }, { text: `ETT KLIPP, beskrivet bara genom sin motor (varan, lokalen och människorna är borttagna):\n${JSON.stringify(motor, null, 1)}` }, { text: `Simulera mötet. Vad händer om den här motorn förs in i aktörens samling: vilken spänning förstärks, vilken gräns bryts, vad måste offras? Döm inte om klippet är bra. Klippet kan vara aktörens eget eller komma från någon helt annan; avgör hur troligt det första är. Skriv på svenska.` }] })
  fs.writeFileSync(ut, JSON.stringify({ konto, id, modell: r.modell, ms: r.ms, usage: r.usage, mote: r.data }, null, 1))
  return 'ny'
}

const kunder = Object.keys(PLAN).filter(k => (!KUNDER || KUNDER.includes(k)) && fs.existsSync(path.join(E14, 'sjalv', `${k}.json`)))
const undanAlla = kunder.flatMap(k => las(path.join(E14, 'sjalv', `${k}.json`)).undan)
let jobb = STEG === 'roller' ? kunder.map(k => ({ namn: k, kor: () => roller(k) })) : STEG === 'sjalv2' ? kunder.map(k => ({ namn: k, kor: () => sjalv2(k) })) : kunder.flatMap(k => undanAlla.map(id => ({ namn: `${k} ← ${id}`, kor: () => mote2(k, id) })))
console.log(`${STEG}: ${jobb.length} jobb, ${PAR} samtidigt`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => { while (i < jobb.length) { const j = jobb[i++]; try { const r = await j.kor(); if (r === 'ny') ny++; else if (r !== 'fanns') console.log(`  ${j.namn}: ${r}`) } catch (e) { fel++; console.log(`  FEL ${j.namn}: ${e.message.slice(0, 160)}`) } } }))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.usd.toFixed(2)} USD`)
