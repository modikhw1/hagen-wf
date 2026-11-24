// Lokala transkript med whisper.cpp (6 nov 2026, inga anrop). Förregistrering: data/format/tal/forregistrering.json.
// ffmpeg tar ut ljudet (16 kHz mono), whisper-cli (base-q5_1, silero-VAD) ger segment med tider.
// Ordning: pass 7, pass 8:s källklipp, pass 4–6:s kandidater, kundernas klipp, resten. Återupptas.
//   node format/transkript.mjs [--max N] [--engelska]   (--engelska: översätt till engelska i stället, för Miles)
// Resultat: data/format/tal/<id>.json (eller tal-en/<id>.json)
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { execFile } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'
const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const EN = args.includes('--engelska')
const las = f => JSON.parse(fs.readFileSync(f, 'utf8')), H = path.join(DATA, 'format', 'harness')
const UT = path.join(DATA, 'format', EN ? 'tal-en' : 'tal'); fs.mkdirSync(UT, { recursive: true })
const W = path.join(os.homedir(), 'tools', 'whisper'), CLI = path.join(W, 'Release', 'whisper-cli.exe')
const DL = path.join(os.homedir(), 'Downloads'), TMP = path.join(os.tmpdir(), 'tal'); fs.mkdirSync(TMP, { recursive: true })
const kor = (cmd, a) => new Promise((res, rej) => execFile(cmd, a, { maxBuffer: 64 * 1024 * 1024, windowsHide: true, timeout: 600_000 }, (e, out, err) => e ? rej(new Error(String(err).slice(-300))) : res(out)))

// alla lokala mp4
const fil = {}
for (const kalla of ['letrend-e4', 'letrend-bibliotek', 'letrend-bank']) { const rot = path.join(DL, kalla); if (!fs.existsSync(rot)) continue
  for (const k of fs.readdirSync(rot)) { const d = path.join(rot, k); if (!fs.statSync(d).isDirectory()) continue; for (const f of fs.readdirSync(d)) if (f.endsWith('.mp4')) fil[`${k}-${f.replace(/\.mp4$/, '')}`] ??= path.join(d, f) } }
// prioritet
const prio = []
las(path.join(H, 'pass7', 'forregistrering.json')).par.forEach(p => prio.push(p.vanster.id, p.hoger.id))
las(path.join(H, 'pass8', 'forregistrering.json')).rader.forEach(r => prio.push(r.kalla))
Object.values(las(path.join(H, 'validering', 'urval.json'))).forEach(v => v.klipp.forEach(c => prio.push(c.id)))
Object.values(las(path.join(H, 'pass6', 'ordning.json'))).flat().forEach(id => prio.push(id))
const kunder = fs.readdirSync(path.join(H, 'linje')).map(f => f.replace(/\.json$/, ''))
Object.keys(fil).filter(id => kunder.includes(id.replace(/-\d+$/, ''))).forEach(id => prio.push(id))
const ordning = [...new Set([...prio.filter(id => fil[id]), ...Object.keys(fil).sort()])]
const kvar = ordning.filter(id => !fs.existsSync(path.join(UT, `${id}.json`))).slice(0, +varde('--max', 1e9))

async function tal(id) {
  const wav = path.join(TMP, `${id}.wav`), bas = path.join(TMP, id)
  await kor('ffmpeg', ['-v', 'error', '-y', '-i', fil[id], '-vn', '-ac', '1', '-ar', '16000', wav])
  const langd = parseFloat(await kor('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav]))
  await kor(CLI, ['-m', path.join(W, 'ggml-base-q5_1.bin'), '-f', wav, '-l', 'auto', '-t', '4', '-np', '-oj', '-of', bas, '--vad', '--vad-model', path.join(W, 'ggml-silero-v5.1.2.bin'), ...(EN ? ['-tr'] : [])])
  const j = las(`${bas}.json`), ms = t => { const m = t.match(/(\d+):(\d+):(\d+)[,.](\d+)/); return m ? +m[1] * 3600 + +m[2] * 60 + +m[3] + +m[4] / 1000 : NaN }
  const seg = (j.transcription || []).map(s => ({ fran: ms(s.timestamps.from), till: ms(s.timestamps.to), text: s.text.trim() })).filter(s => s.text && !/^\[.*\]$|^\(.*\)$/.test(s.text))
  fs.writeFileSync(path.join(UT, `${id}.json`), JSON.stringify({ id, langd, sprak: j.result?.language, segment: seg }))
  fs.rmSync(wav, { force: true }); fs.rmSync(`${bas}.json`, { force: true })
}
console.log(`${Object.keys(fil).length} lokala klipp, ${kvar.length} kvar att transkribera${EN ? ' (engelska)' : ''}`)
let n = 0; const t0 = Date.now()
// två parallella med fyra trådar var
let nasta = 0
const arb = async () => { while (nasta < kvar.length) { const id = kvar[nasta++]; try { await tal(id) } catch (e) { console.log(`${id}: FEL ${e.message.slice(0, 150)}`) } if (++n % 20 === 0) console.log(`${n}/${kvar.length} (${Math.round((Date.now() - t0) / 60000)} min)`) } }
await Promise.all([arb(), arb()])
console.log('klart')
