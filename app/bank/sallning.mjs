// Sållning av nedladdade bankklipp med Gemini, innan den dyra lokala analysen (~40 s per klipp).
// Flash-Lite ser klippet (480 bredd, 1 bild/s, med ljud) och svarar kort: typ (ur typlistan),
// personer, var det är filmat, bildkvalitet, montage, bildspel, texttyngd och hur väl det går att
// rekonstruera som 3D. Kostar ~1 öre per klipp. Resultat: data/bank/sallning/<id>.json.
//
//   node bank/sallning.mjs [--konto x] [--max 500] [--om]
import fs from 'node:fs'
import path from 'node:path'
import { DATA, TMP } from '../analys/pipeline.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { generera } from '../typer/gemini.mjs'

const MODELL = process.env.SALLNING_MODELL ?? 'gemini-3.5-flash-lite'
const UT = path.join(DATA, 'bank', 'sallning')
const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const lasJson = f => (fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null)

export function schema(typer) {
  return {
    type: 'object',
    properties: {
      innehall: { type: 'string', description: 'Vad klippet visar, en mening.' },
      typ: { type: 'string', enum: [...typer.map(t => t.id), 'annat'] },
      personer_max: { type: 'integer', description: 'Flest personer i bild samtidigt.' },
      andel_med_person: { type: 'number', description: '0–1: hur stor del av tiden minst en person syns tydligt (mer än händer).' },
      inne_i_verksamheten: { type: 'boolean', description: 'Filmat i eller vid restaurangen/kaféet (inte hemma, inte i en bil, inte stock footage).' },
      bildkvalitet: { type: 'integer', minimum: 1, maximum: 5, description: '1 suddigt/mörkt/skakigt, 5 skarpt och välexponerat.' },
      montage: { type: 'boolean', description: 'Snabba klipp mellan många korta bilder (under ~0,7 s i snitt).' },
      bildspel: { type: 'boolean', description: 'Stillbilder i stället för video.' },
      text_tung: { type: 'boolean', description: 'Budskapet bärs mest av skärmtext, bilden är bakgrund.' },
      rekonbar: { type: 'integer', minimum: 1, maximum: 5, description: 'Hur väl klippet går att återskapa som enkel 3D med personer som rör sig i en lokal: 5 = få personer, tydliga kroppar, en eller några platser; 1 = mest närbilder på mat, montage, effekter eller folkmassor.' },
      skal: { type: 'string', description: 'Kort: vad som drar ner eller upp.' },
    },
    required: ['innehall', 'typ', 'personer_max', 'andel_med_person', 'inne_i_verksamheten', 'bildkvalitet', 'montage', 'bildspel', 'text_tung', 'rekonbar', 'skal'],
  }
}

async function video(id, fil) {
  const ut = path.join(TMP, 'sallning', `${id}.mp4`)
  if (!fs.existsSync(ut)) {
    fs.mkdirSync(path.dirname(ut), { recursive: true })
    await kor(verktyg.ffmpeg, ['-y', '-v', 'error', '-i', fil, '-t', '90', '-vf', 'scale=480:-2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '32', '-c:a', 'aac', '-b:a', '48k', ut])
  }
  return { inlineData: { mimeType: 'video/mp4', data: fs.readFileSync(ut).toString('base64') }, videoMetadata: { fps: 1 } }
}

async function iTakt(lista, n, f) {
  let k = 0
  await Promise.all(Array.from({ length: Math.min(n, lista.length) }, async () => { while (k < lista.length) { const j = k++; await f(lista[j], j) } }))
}

if (import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const typer = lasJson(path.join(DATA, 'typer', 'typer.json'))?.typer
  if (!typer) { console.error('typlistan saknas (npm run typer -- typlista)'); process.exit(1) }
  const S = schema(typer)
  const typText = typer.map(t => `- ${t.id} (${t.namn}): ${t.definition}`).join('\n')
  const kallor = lasJson(path.join(DATA, 'kallor.json')) ?? {}
  const lista = Object.entries(kallor)
    .filter(([, k]) => (k.kalla === 'bank' || k.kalla === 'import') && (!varde('--konto') || k.konto === varde('--konto')) && fs.existsSync(k.fil))
    .filter(([id]) => args.includes('--om') || !fs.existsSync(path.join(UT, `${id}.json`)))
    .slice(0, Number(varde('--max', 100000)))
  fs.mkdirSync(UT, { recursive: true })
  let ore = 0, klara = 0, fel = 0
  await iTakt(lista, 6, async ([id, k]) => {
    try {
      const r = await generera({ modell: MODELL, parts: [await video(id, k.fil), { text: `Ett TikTok-klipp från ett konto för en restaurang, bar eller ett kafé (@${k.konto}).\nInnehållstyper:\n${typText}\n\nBedöm klippet kort enligt fälten. Svara på svenska.` }], schema: S, temperatur: 0.1 })
      ore += r.ore ?? 0
      fs.writeFileSync(path.join(UT, `${id}.json`), JSON.stringify({ id, konto: k.konto, modell: MODELL, ore: r.ore, ...r.data }))
      fs.rmSync(path.join(TMP, 'sallning', `${id}.mp4`), { force: true })
      if (++klara % 25 === 0) console.log(`  ${klara}/${lista.length} · ${ore.toFixed(0)} öre`)
    } catch (e) { fel++; console.warn(`  ${id}: ${e.message.slice(0, 160)}`) }
  })
  console.log(`sållning klar: ${klara} klipp, ${fel} fel, ${ore.toFixed(0)} öre`)
}
