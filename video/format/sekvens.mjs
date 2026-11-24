// Sekvenstest (3–4 nov 2026): fem klipp i en fil, åtskilda av titelkort "KLIPP n" (1 s).
//   A (trohet): lagerschemat per klipp ur sekvensen, framlänges och baklänges, jämfört med samma klipp ett och ett (Lite).
//   B (serie): fem klipp från samma konto. Återkommande personer, format, mix och persona som röd tråd (Pro).
//   C (jämförelse): fem klipp ägaren bedömt, rangordnade som biblioteksexempel (Pro, v3-principerna utan exempel).
//
//   node format/sekvens.mjs [A] [B] [C]
// Resultat: data/format/sekvens/<test>/<namn>.json och videorna i data/format/sekvens/vid/
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { LAGER } from './lager.mjs'
import { KONSTITUTION } from './v3.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'

const S = path.join(DATA, 'format', 'sekvens'), VID = path.join(S, 'vid')
fs.mkdirSync(VID, { recursive: true })
const urval = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'kalib', 'urval.json'), 'utf8'))
const kallor = JSON.parse(fs.readFileSync(path.join(DATA, 'kallor.json'), 'utf8'))
const ff = (...a) => kor(verktyg.ffmpeg, ['-y', '-v', 'error', ...a])

async function kort(n) {
  const f = path.join(VID, `kort${n}.mp4`)
  if (!fs.existsSync(f)) await ff('-f', 'lavfi', '-i', 'color=c=black:s=360x640:d=1:r=30', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '1', '-vf', `drawtext=fontfile='C\\:/Windows/Fonts/arialbd.ttf':text='KLIPP ${n}':fontcolor=white:fontsize=48:x=(w-tw)/2:y=(h-th)/2`, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-b:a', '48k', '-shortest', f)
  return f
}
async function normal(fil, namn) {
  const f = path.join(VID, `n-${namn}.mp4`)
  if (fs.existsSync(f)) return f
  // Ljud saknas ibland: lägg till tyst ljud så att alla delar har samma strömmar.
  const harLjud = await kor(verktyg.ffmpeg, ['-v', 'error', '-i', fil, '-map', '0:a:0', '-f', 'null', '-t', '0.1', '-']).then(() => true, () => false)
  const vf = 'scale=360:640:force_original_aspect_ratio=decrease,pad=360:640:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p'
  if (harLjud) await ff('-i', fil, '-t', '60', '-vf', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '32', '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-b:a', '48k', f)
  else await ff('-i', fil, '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '60', '-vf', vf, '-map', '0:v', '-map', '1:a', '-shortest', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '32', '-c:a', 'aac', '-b:a', '48k', f)
  return f
}
async function sekvens(namn, filer) {
  const ut = path.join(VID, `${namn}.mp4`)
  if (fs.existsSync(ut)) return ut
  const delar = []
  for (let i = 0; i < filer.length; i++) { delar.push(await kort(i + 1)); delar.push(await normal(filer[i].fil, filer[i].id)) }
  const lista = path.join(VID, `${namn}.txt`)
  fs.writeFileSync(lista, delar.map(d => `file '${d.replace(/\\/g, '/')}'`).join('\n'))
  await ff('-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', ut)
  return ut
}
const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description, k) => ({ type: 'array', items, description, minItems: k, maxItems: k })
async function kalla(test, namn, fil, prompt, schema, modell) {
  const ut = path.join(S, test, `${namn}.json`)
  if (fs.existsSync(ut)) return JSON.parse(fs.readFileSync(ut, 'utf8'))
  const r = await analyseraVideo({ fil, prompt, schema, temperatur: 0.2, modell })
  fs.mkdirSync(path.dirname(ut), { recursive: true })
  fs.writeFileSync(ut, JSON.stringify({ modell: r.modell, tokens: r.usage?.total_tokens, ms: r.ms, ...r.data }, null, 1))
  return r.data
}
const INLEDNING = antal => `Videon består av ${antal} separata TikTok-klipp i följd. Före varje klipp kommer ett svart titelkort med texten "KLIPP 1", "KLIPP 2" och så vidare. Titelkorten hör inte till klippen. Bedöm varje klipp för sig, som om du såg det ensamt, och blanda inte ihop dem.`
const tester = process.argv.slice(2).length ? process.argv.slice(2) : ['A', 'B', 'C']
const jobb = []

// A: trohet. Klipp 1–25 i fem grupper, framlänges och baklänges.
if (tester.includes('A')) {
  const lagerSchema = obj({ klipp: arr(obj({ nr: n(1, 5, 'Klippets nummer från titelkortet.'), ...Object.fromEntries(Object.entries(LAGER).map(([k, [, d]]) => [k, d])) }), 'Ett objekt per klipp, i ordning.', 5) })
  for (let g = 0; g < 5; g++) for (const riktning of ['fram', 'bak']) {
    const set = urval.slice(g * 5, g * 5 + 5)
    const ord = riktning === 'fram' ? set : [...set].reverse()
    jobb.push(async () => {
      const fil = await sekvens(`A-g${g + 1}-${riktning}`, ord)
      const r = await kalla('A', `g${g + 1}-${riktning}`, fil, `${INLEDNING(5)}\n\nKoda varje klipp genom att fylla i fälten. Bedöm det du ser och hör, inte det du gissar. Svara på svenska.`, lagerSchema, 'google/gemini-3.1-flash-lite')
      return { g, riktning, ids: ord.map(k => k.id), r }
    })
  }
}
// B: serie. Fem klipp per konto, ur filerna som finns i banken.
const SERIER = ['mondocoatbridge', 'babulsofficial', 'kebabbabes', 'jirvelius', 'dirtytaco.se', 'viasalessverige']
if (tester.includes('B')) {
  const serieSchema = obj({
    klipp: arr(obj({ nr: n(1, 5, 'Klippets nummer.'), vad: s('Vad som händer, en mening.'), roll: s('kott (sketch eller inbjudande innehåll med personer), stod (visning, nyhet, erbjudande, tävling) eller utanfor (montage, reklamfilm, event).', ['kott', 'stod', 'utanfor']) }), 'Ett objekt per klipp.', 5),
    aterkommande_personer: obj({ finns: b('Syns samma person i flera av klippen?'), vilka: s('Vilka, med kännetecken, och i vilka klipp. Annars "inga".') }),
    aterkommande_format: s('Återkommer ett format, en idé eller en mall i flera klipp? Vilket, och i vilka klipp. Annars "inget".'),
    rod_trad: s('Vad som binder ihop kontot: en persona, en ton, ett gäng eller ett tema. 1–2 meningar.'),
    mix: s('Hur kontot blandar underhållning och försäljning, och om blandningen verkar planerad eller slumpmässig. 1–2 meningar.'),
    strategityp: s('dialogsketch (sketcher och dialog med personer), tilltal_erbjudande (prata till kameran, sälja öppet), visning_trend (montage, mat, trendljud), trendsketch (sketcher till trendljud utan att sälja), eller blandad.', ['dialogsketch', 'tilltal_erbjudande', 'visning_trend', 'trendsketch', 'blandad']),
    inside: n(1, 5, 'Känns kontot som ett tv-program eller ett inside-skämt man lär känna? 1 nej, 5 ja.'),
    saknas: s('Vad som saknas i mixen för att kontot ska bli starkare, en mening.'),
  })
  for (const konto of SERIER) jobb.push(async () => {
    const filer = Object.entries(kallor).filter(([id, k]) => k.konto === konto && !k.raderad && k.fil && fs.existsSync(k.fil)).sort().slice(0, 5).map(([id, k]) => ({ id, fil: k.fil }))
    if (filer.length < 5) return { konto, fel: 'för få filer' }
    const fil = await sekvens(`B-${konto}`, filer)
    const r = await kalla('B', konto, fil, `${INLEDNING(5)} Alla fem klippen kommer från samma TikTok-konto (@${konto}), en verksamhet.\n\nBeskriv först varje klipp kort. Beskriv sedan kontot som serie: vad som återkommer, vad som binder ihop det och hur mixen ser ut. Svara på svenska.`, serieSchema, 'google/gemini-3.1-pro-preview')
    return { konto, ids: filer.map(f => f.id), r }
  })
}
// C: jämförelse. Fem klipp ägaren bedömt, rangordnade, framlänges och baklänges.
if (tester.includes('C')) {
  const rangSchema = obj({
    klipp: arr(obj({ nr: n(1, 5, 'Klippets nummer.'), vad: s('Vad som händer, en mening.'), bibliotek: s('Hör klippet hemma i LeTrends bibliotek? ja, villkorat eller nej.', ['ja', 'villkorat', 'nej']) }), 'Ett objekt per klipp.', 5),
    rangordning: arr(n(1, 5, ''), 'Klippens nummer från bästa till sämsta exempel att rekommendera ur biblioteket.', 5),
    skal: s('Varför den ordningen, 2–3 meningar.'),
  })
  for (let g = 0; g < 5; g++) for (const riktning of ['fram', 'bak']) {
    const set = urval.slice(g * 5, g * 5 + 5)
    const ord = riktning === 'fram' ? set : [...set].reverse()
    jobb.push(async () => {
      const fil = await sekvens(`A-g${g + 1}-${riktning}`, ord)
      const r = await kalla('C', `g${g + 1}-${riktning}`, fil, `${INLEDNING(5)}\n\n${KONSTITUTION}\n\nBedöm varje klipp, och rangordna dem sedan från bästa till sämsta exempel att rekommendera ur biblioteket. Jämför klippen med varandra. Svara på svenska.`, rangSchema, 'google/gemini-3.1-pro-preview')
      return { g, riktning, ids: ord.map(k => k.id), r }
    })
  }
}
const res = await Promise.all(jobb.map(j => j().catch(e => ({ fel: e.message.slice(0, 200) }))))
fs.writeFileSync(path.join(S, `resultat-${tester.join('')}.json`), JSON.stringify(res, null, 1))
console.log(`${res.length} jobb, ${res.filter(r => r.fel).length} fel`, res.filter(r => r.fel).map(r => r.fel).join(' | '))
