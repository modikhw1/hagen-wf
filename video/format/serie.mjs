// Serietest (4 nov 2026): tio klipp från samma konto i datumordning i en fil, med titelkort "KLIPP n".
// Pro pekar ut kontots frontfigurer och återkommande format och anger för varje klipp vilka som syns.
// Analysen (format/serie-analys.mjs) prövar inom konto om klippen med frontfiguren eller formatet går
// bättre än kontots övriga klipp. Det går inte att se i ett ensamt klipp.
//
//   node format/serie.mjs [--konton 40] [--per 10]
// Resultat: data/format/serie/<konto>.json, videorna i Downloads/letrend-serie
import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const ANTAL = Number(varde('--konton', 40)), PER = Number(varde('--per', 10))
// --replik: alla återstående konton med minst PER klipp som inte redan finns i data/format/serie,
// till data/format/serie-r (replikering av HS1, HS4 och HS6).
const REPLIK = args.includes('--replik')
const NED = 'C:/Users/praiseworthy/Downloads/letrend-serie', UT = path.join(DATA, 'format', REPLIK ? 'serie-r' : 'serie'), VID = path.join(NED, '_vid')
const KLARA = new Set(fs.existsSync(path.join(DATA, 'format', 'serie')) ? fs.readdirSync(path.join(DATA, 'format', 'serie')).filter(f => f.endsWith('.json')).map(f => f.replace(/\.json$/, '')) : [])
fs.mkdirSync(UT, { recursive: true }); fs.mkdirSync(VID, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const e4 = las(path.join(DATA, 'format', 'e4', 'urval.json'))
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const godk = new Set(fs.readFileSync(path.join(DATA, 'profil', 'godkanda.txt'), 'utf8').split(/\r?\n/).filter(Boolean))
const fore = new Set((fs.readFileSync(path.join(DATA, 'profil', 'forebilder.txt'), 'utf8').match(/@[a-z0-9._]+/g) ?? []).map(h => h.slice(1)))

// Konton: 25 valda (ja + förebilder) och 15 ur banken, med minst PER klipp i E4-urvalet. Fast frö.
let fro = 404; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }
const perKonto = new Map(); for (const k of e4) { const l = perKonto.get(k.konto) ?? []; l.push(k); perKonto.set(k.konto, l) }
const valbara = [...perKonto.entries()].filter(([, l]) => l.length >= PER)
const kand = REPLIK ? valbara.filter(([k]) => !KLARA.has(k)) : valbara
const valda = bl(kand.filter(([k]) => godk.has(k) || fore.has(k))).slice(0, REPLIK ? 1e9 : Math.round(ANTAL * 0.625))
const bank = bl(kand.filter(([k]) => !godk.has(k) && !fore.has(k))).slice(0, REPLIK ? 1e9 : ANTAL - valda.length)
const konton = [...valda, ...bank].map(([konto, l]) => ({ konto, grupp: godk.has(konto) ? 'ja' : fore.has(konto) ? 'forebild' : 'bank', klipp: bl(l).slice(0, PER).map(k => ({ ...k, datum: bas.get(k.id)?.datum ?? '' })).sort((a, b) => a.datum.localeCompare(b.datum)) }))
console.log(`${konton.length} konton (${valda.length} valda, ${bank.length} bank), ${konton.length * PER} klipp`)

// Hämta det som saknas, i batcher med yt-dlp.
const FORMAT = "b[ext=mp4][height<=1024][vcodec~='^(h265|hevc|bytevc1)']/b[ext=mp4][height<=1024]/b[ext=mp4]/b"
for (const k of konton.flatMap(x => x.klipp)) { if (!fs.existsSync(k.fil)) k.fil = `${NED}/${k.konto}/${k.vid}.mp4` }
const behov = konton.flatMap(x => x.klipp).filter(k => !fs.existsSync(k.fil))
function batch(lista) {
  const dir = path.join(NED, `_b${Math.random().toString(36).slice(2, 8)}`); fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(path.join(dir, 'lista.txt'), lista.map(k => k.url).join('\n'))
  return new Promise(res => { const p = spawn('uvx', ['yt-dlp', '--ffmpeg-location', verktyg.ffmpeg, '-f', FORMAT, '--merge-output-format', 'mp4', '--ignore-errors', '--no-progress', '-o', path.join(dir, '%(id)s.%(ext)s'), '-a', path.join(dir, 'lista.txt')], { windowsHide: true }); p.stdout.on('data', () => {}); p.stderr.on('data', () => {}); p.on('close', () => { for (const k of lista) { const f = path.join(dir, `${k.vid}.mp4`); if (fs.existsSync(f)) { fs.mkdirSync(path.dirname(k.fil), { recursive: true }); fs.renameSync(f, k.fil) } } fs.rmSync(dir, { recursive: true, force: true }); res() }) })
}
const B = []; for (let i = 0; i < behov.length; i += 12) B.push(behov.slice(i, i + 12))
let bi = 0; await Promise.all(Array.from({ length: 6 }, async () => { while (bi < B.length) await batch(B[bi++]) }))
console.log(`hämtat; ${konton.flatMap(x => x.klipp).filter(k => fs.existsSync(k.fil)).length} filer finns`)

const ff = (...a) => kor(verktyg.ffmpeg, ['-y', '-v', 'error', ...a])
async function kort(n) { const f = path.join(VID, `kort${n}.mp4`); if (!fs.existsSync(f)) await ff('-f', 'lavfi', '-i', 'color=c=black:s=360x640:d=1:r=30', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '1', '-vf', `drawtext=fontfile='C\\:/Windows/Fonts/arialbd.ttf':text='KLIPP ${n}':fontcolor=white:fontsize=48:x=(w-tw)/2:y=(h-th)/2`, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-b:a', '48k', '-shortest', f); return f }
async function normal(k) {
  const f = path.join(VID, `n-${k.id}.mp4`); if (fs.existsSync(f)) return f
  const vf = 'scale=360:640:force_original_aspect_ratio=decrease,pad=360:640:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p'
  try { await ff('-i', k.fil, '-t', '30', '-vf', vf, '-map', '0:v:0', '-map', '0:a:0', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '32', '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-b:a', '48k', f) }
  catch { await ff('-i', k.fil, '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '30', '-vf', vf, '-map', '0:v', '-map', '1:a', '-shortest', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '32', '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-b:a', '48k', f) }
  return f
}
async function sekvens(x) {
  const ut = path.join(VID, `${x.konto}.mp4`); if (fs.existsSync(ut)) return ut
  const delar = []; for (let i = 0; i < x.klipp.length; i++) { delar.push(await kort(i + 1)); delar.push(await normal(x.klipp[i])) }
  const lista = path.join(VID, `${x.konto}.txt`); fs.writeFileSync(lista, delar.map(d => `file '${d.replace(/\\/g, '/')}'`).join('\n'))
  await ff('-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', ut); return ut
}
const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description, extra = {}) => ({ type: 'array', items, description, ...extra })
const schema = k => obj({
  frontfigurer: arr(obj({ etikett: s('Kort namn, t.ex. "skäggig man" eller "rosa-tröjan".'), kannetecken: s('Hur personen känns igen.'), klipp: arr(n(1, k, ''), 'Alla klipp där personen syns.') }), 'Personer som syns i minst två av klippen. Tom lista om ingen återkommer.'),
  format: arr(obj({ namn: s('Kort namn på formatet eller idén.'), beskrivning: s('Vad som återkommer.'), klipp: arr(n(1, k, ''), 'Alla klipp med formatet.') }), 'Format, idéer eller mallar som återkommer i minst två klipp. Tom lista om inget återkommer.'),
  klipp: arr(obj({ nr: n(1, k, ''), vad: s('Vad som händer, en mening.'), roll: s('kott (sketch eller inbjudande innehåll med personer), stod (visning, nyhet, erbjudande, tävling) eller utanfor (montage, reklamfilm, event).', ['kott', 'stod', 'utanfor']), anknyter: b('Anknyter klippet till något i ett annat klipp, t.ex. en fortsättning, en återkommande replik eller ett inside-skämt?') }), 'Ett objekt per klipp.', { minItems: k, maxItems: k }),
  rod_trad: s('Vad som binder ihop kontot, 1–2 meningar.'),
  planerat: n(1, 5, 'Hur planerad mixen verkar: 1 slumpmässig, 5 tydligt planerad.'),
  inside: n(1, 5, 'Känns kontot som ett tv-program eller ett inside-skämt man lär känna? 1 nej, 5 ja.'),
  saknas: s('Vad som saknas för att kontot ska bli starkare, en mening.'),
})
const prompt = (x) => `Videon består av ${x.klipp.length} separata TikTok-klipp från samma konto (@${x.konto}), i den ordning de publicerades. Före varje klipp kommer ett svart titelkort med texten "KLIPP 1", "KLIPP 2" och så vidare. Titelkorten hör inte till klippen.

Uppgiften är att förstå kontot som serie. Peka ut personer som återkommer i flera klipp och format som återkommer. Ange för varje klipp vad som händer. Var noggrann med vilka klipp en person faktiskt syns i, och gissa inte. Svara på svenska.`

let i = 0, ok = 0, fel = 0
await Promise.all(Array.from({ length: 8 }, async () => {
  while (i < konton.length) {
    const x = konton[i++]
    const ut = path.join(UT, `${x.konto}.json`)
    if (fs.existsSync(ut)) { ok++; continue }
    x.klipp = x.klipp.filter(k => fs.existsSync(k.fil))
    if (x.klipp.length < 6) { fel++; console.warn(`${x.konto}: för få filer`); continue }
    try {
      const fil = await sekvens(x)
      if (fs.statSync(fil).size > 15.5e6) { fel++; console.warn(`${x.konto}: för stor (${(fs.statSync(fil).size / 1e6).toFixed(1)} MB)`); continue }
      const r = await analyseraVideo({ fil, prompt: prompt(x), schema: schema(x.klipp.length), temperatur: 0.2, modell: 'google/gemini-3.1-pro-preview' })
      fs.writeFileSync(ut, JSON.stringify({ konto: x.konto, grupp: x.grupp, ids: x.klipp.map(k => k.id), modell: r.modell, tokens: r.usage?.total_tokens, ...r.data }, null, 1))
      ok++
    } catch (e) { fel++; console.warn(`${x.konto}: ${e.message.slice(0, 200)}`); if (/ 402:/.test(e.message)) process.exit(1) }
  }
}))
console.log(`klart: ${ok} ok, ${fel} fel`)
