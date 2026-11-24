// Harness v5 steg 3 (4 nov 2026): kundens LINJE. Pass 4–5 visade att ägaren bedömer passform som
// fortsättning på det kunden gör nu, och att profilen ur tio slumpvisa klipp missade en kursändring
// (anettesrestaurang). Linjen bygger därför på kontots tio SENASTE klipp, sedda som serie i en fil med
// titelkort, och jämförs med den äldre profilen (v0) för att hitta kursändringar. Det som är osäkert
// listas för CM att bekräfta. Luckor hålls isär från linjen.
//
//   LOVABLE_KONTO=2 node format/h-linje.mjs [--konton a,b,c] [--per 10]
// Resultat: data/format/harness/linje/<konto>.json
import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
import { LETREND, LINJE, UTFALL } from './doktrin.mjs'
import { STRATEGIER, KANTIGHET, TEMPO } from './v5.mjs'
import { LOKALDELAR, VERKSAMHETER, ROLLER } from './v4.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PER = Number(varde('--per', 10))
const H = path.join(DATA, 'format', 'harness'), UT = path.join(H, 'linje')
const NED = 'C:/Users/praiseworthy/Downloads/letrend-linje', VID = path.join(NED, '_vid')
fs.mkdirSync(UT, { recursive: true }); fs.mkdirSync(VID, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const konton = varde('--konton') ? varde('--konton').split(',') : las(path.join(H, 'urval.json')).kunder

// De senaste klippen ur bankens lista (nyast först), 5–120 s.
function senaste(konto) {
  const lista = las(path.join(DATA, 'bank', konto, 'lista.json')).klipp
  return lista.filter(k => k.langd >= 5 && k.langd <= 120).sort((a, b) => b.datum.localeCompare(a.datum)).slice(0, PER).reverse()
    .map(k => {
      const fil = [`C:/Users/praiseworthy/Downloads/letrend-bank/${konto}/${k.id}.mp4`, `C:/Users/praiseworthy/Downloads/letrend-e4/${konto}/${k.id}.mp4`, `C:/Users/praiseworthy/Downloads/letrend-serie/${konto}/${k.id}.mp4`].find(fs.existsSync) ?? `${NED}/${konto}/${k.id}.mp4`
      return { id: `${konto}-${k.id}`, vid: k.id, konto, datum: k.datum, text: (k.text ?? '').slice(0, 120), url: `https://www.tiktok.com/@${konto}/video/${k.id}`, fil, visningar: k.visningar }
    })
}

const FORMAT = "b[ext=mp4][height<=1024][vcodec~='^(h265|hevc|bytevc1)']/b[ext=mp4][height<=1024]/b[ext=mp4]/b"
function hamta(lista) {
  if (!lista.length) return Promise.resolve()
  const dir = path.join(NED, `_b${Math.random().toString(36).slice(2, 8)}`); fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(path.join(dir, 'lista.txt'), lista.map(k => k.url).join('\n'))
  return new Promise(res => { const p = spawn('uvx', ['yt-dlp', '--ffmpeg-location', verktyg.ffmpeg, '-f', FORMAT, '--merge-output-format', 'mp4', '--ignore-errors', '--no-progress', '-o', path.join(dir, '%(id)s.%(ext)s'), '-a', path.join(dir, 'lista.txt')], { windowsHide: true }); p.stdout.on('data', () => {}); p.stderr.on('data', () => {}); p.on('close', () => { for (const k of lista) { const f = path.join(dir, `${k.vid}.mp4`); if (fs.existsSync(f)) { fs.mkdirSync(path.dirname(k.fil), { recursive: true }); fs.renameSync(f, k.fil) } } fs.rmSync(dir, { recursive: true, force: true }); res() }) })
}
const ff = (...a) => kor(verktyg.ffmpeg, ['-y', '-v', 'error', ...a])
async function kort(n) { const f = path.join(VID, `kort${n}.mp4`); if (!fs.existsSync(f)) await ff('-f', 'lavfi', '-i', 'color=c=black:s=360x640:d=1:r=30', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '1', '-vf', `drawtext=fontfile='C\\:/Windows/Fonts/arialbd.ttf':text='KLIPP ${n}':fontcolor=white:fontsize=48:x=(w-tw)/2:y=(h-th)/2`, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-b:a', '48k', '-shortest', f); return f }
async function normal(k) {
  const f = path.join(VID, `n-${k.id}.mp4`); if (fs.existsSync(f)) return f
  const vf = 'scale=360:640:force_original_aspect_ratio=decrease,pad=360:640:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p'
  try { await ff('-i', k.fil, '-t', '30', '-vf', vf, '-map', '0:v:0', '-map', '0:a:0', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '32', '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-b:a', '48k', f) }
  catch { await ff('-i', k.fil, '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '30', '-vf', vf, '-map', '0:v', '-map', '1:a', '-shortest', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '32', '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-b:a', '48k', f) }
  return f
}
async function sekvens(konto, klipp) {
  const ut = path.join(VID, `${konto}.mp4`); if (fs.existsSync(ut)) return ut
  const delar = []; for (let i = 0; i < klipp.length; i++) { delar.push(await kort(i + 1)); delar.push(await normal(klipp[i])) }
  const lista = path.join(VID, `${konto}.txt`); fs.writeFileSync(lista, delar.map(d => `file '${d.replace(/\\/g, '/')}'`).join('\n'))
  await ff('-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', ut); return ut
}

const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description, extra = {}) => ({ type: 'array', items, description, ...extra })
const schema = k => obj({
  klipp: arr(obj({
    nr: n(1, k, ''), vad: s('Vad som händer, en mening.'),
    strategi: s('Vilken sorts klipp: sketchvarld, tilltal, premium_stamning, visning, kampanj eller trend.', STRATEGIER),
    kantighet: s('', KANTIGHET), person: s('fokus, behallare, roll eller ingen.', ['fokus', 'behallare', 'roll', 'ingen']),
    klippberoende: s('Hur mycket av värdet som sitter i klippning och efterarbete.', ['lite', 'en_del', 'mycket']),
  }), 'Ett objekt per klipp.', { minItems: k, maxItems: k }),
  linje: s('Kontots linje just nu, 2–3 meningar: vad kontot gör, hur det låter och vad ett naturligt nästa klipp är. Väg de senaste klippen tyngst.'),
  strategi: s('Kontots huvudstrategi just nu.', STRATEGIER),
  strategi_sekundar: s('Den näst vanligaste, eller samma som huvudstrategin om kontot är renodlat.', STRATEGIER),
  kantighet: s('Kontots kantighet.', KANTIGHET),
  tempo: s('Kontots typiska tempo.', TEMPO),
  klippberoende: s('Hur mycket kontot lutar sig på klippning och efterarbete.', ['lite', 'en_del', 'mycket']),
  tilltal_antal: n(0, k, 'I hur många av klippen någon talar direkt till kameran.'),
  frontfigurer: arr(obj({ etikett: s('Kort namn.'), roll: s('Vanligaste roll.', ROLLER), funktion: s('Är personen fokus (karisman bär), behållare (framför konceptet) eller rollspelare i sketcher?', ['fokus', 'behallare', 'roll']), styrka: s('Vad personen är bra på framför kameran, en mening.'), klipp: arr(n(1, k, ''), 'Klippen där personen syns.') }), 'Personer som syns i minst två klipp, viktigast först. Tom lista om ingen återkommer.'),
  personal_spelar: n(1, 5, 'Hur van personalen är att spela upp situationer. 1 = aldrig, 5 = ofta och bra.'),
  max_personer: n(0, 6, 'Hur många personer som brukar vara med i samma klipp.'),
  format: arr(obj({ namn: s('Formatets namn.'), beskrivning: s('Vad som återkommer.'), klipp: arr(n(1, k, ''), '') }), 'Format som återkommer i minst två klipp.'),
  verksamhet: s('', VERKSAMHETER),
  segment: s('enkel, premium eller kedja.', ['enkel', 'premium', 'kedja']),
  produkter: s('Vad som säljs, kort.'),
  lokal: arr(s('', LOKALDELAR), 'Delar av lokalen som används i klippen.'),
  sjalvbild: s('Hur kontot ser på sig självt och på marknadsföring, en mening.'),
  sticker_ut: arr(s('En sak.'), 'Sorters klipp som skulle kännas främmande eller sticka ut i kontots flöde, 2–4 st.'),
  kursandring: obj({ finns: b('Skiljer sig de senaste klippen tydligt från den äldre bilden nedan?'), vad: s('Vad som har ändrats, eller "ingen".') }),
  luckor: arr(s('En lucka.'), 'Det som saknas i mixen. Det är ett medvetet val för CM och ingen del av linjen. 0–3 st.'),
  att_bekrafta: arr(s('Ett påstående.'), 'Det i profilen som är osäkert och som CM bör bekräfta med kunden eller genom att titta på fler klipp, 1–4 st.'),
})
const prompt = (konto, klipp, aldre) => `Videon består av ${klipp.length} separata TikTok-klipp från @${konto}, kontots senaste i publiceringsordning (äldst först, nyast sist). Före varje klipp kommer ett svart titelkort "KLIPP 1", "KLIPP 2" och så vidare. Titelkorten hör inte till klippen. Klippen är högst 30 sekunder.

${LETREND}

${LINJE}

${UTFALL}

Uppgiften är att beskriva kundens linje, så att en CM kan välja klipp som är ett naturligt nästa klipp för just den här kunden. Beskriv vad kontot gör nu, inte vad det borde göra. Peka ut återkommande personer och format, och var noggrann med i vilka klipp de syns.

Klippens texter och datum:
${klipp.map((k, i) => `${i + 1}. ${k.datum}: ${k.text}`).join('\n')}

Den äldre bilden av kontot, byggd på tio slumpvisa äldre klipp, för att se om något har ändrats:
${aldre ? JSON.stringify(aldre) : 'saknas'}

Svara på svenska.`

for (const konto of konton) {
  const ut = path.join(UT, `${konto}.json`)
  if (fs.existsSync(ut)) { console.log(`${konto}: finns`); continue }
  let klipp = senaste(konto)
  await hamta(klipp.filter(k => !fs.existsSync(k.fil)))
  klipp = klipp.filter(k => fs.existsSync(k.fil))
  if (klipp.length < 6) { console.warn(`${konto}: för få filer (${klipp.length})`); continue }
  const fil = await sekvens(konto, klipp)
  const mb = fs.statSync(fil).size / 1e6
  if (mb > 15.5) { console.warn(`${konto}: för stor (${mb.toFixed(1)} MB)`); continue }
  const kf = path.join(H, 'kunder', `${konto}.json`)
  const aldre = fs.existsSync(kf) ? (({ beskrivning, persona, frontfigurer, personal_spelar, aterkommande_format, luckor }) => ({ beskrivning, persona, frontfigurer, personal_spelar, aterkommande_format, luckor }))(las(kf).profil) : null
  try {
    const r = await analyseraVideo({ fil, prompt: prompt(konto, klipp, aldre), schema: schema(klipp.length), temperatur: 0.2, modell: 'google/gemini-3.1-pro-preview' })
    fs.writeFileSync(ut, JSON.stringify({ konto, klipp: klipp.map(({ id, datum, url, visningar }) => ({ id, datum, url, visningar })), tokens: r.usage?.total_tokens, ...r.data }, null, 1))
    console.log(`${konto}: ${r.data.strategi}/${r.data.strategi_sekundar}, ${r.data.kantighet}, kursändring ${r.data.kursandring.finns ? r.data.kursandring.vad : 'nej'} (${r.usage?.total_tokens} tokens)`)
  } catch (e) { console.warn(`${konto}: ${e.message.slice(0, 200)}`); if (/ 402:/.test(e.message)) process.exit(1) }
}
