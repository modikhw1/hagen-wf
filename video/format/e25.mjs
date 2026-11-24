// E25 (17 nov 2026): negativ input. Tio poster, klippets delar bland svarta platshållare. data/format/e25/forregistrering.json
//   node format/e25.mjs --urval
//   LOVABLE_KONTO=beacon node format/e25.mjs --villkor p0|p40|p60|p70 [--par 3]
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'

const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const E = path.join(DATA, 'format', 'e25'), D = path.join(os.homedir(), 'Downloads', 'letrend-e25'); fs.mkdirSync(D, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8')), liten = id => path.join(os.homedir(), 'Downloads', 'letrend-e13', `${id}.mp4`)
const frö = s => () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296 }

if (args.includes('--urval')) {
  const R = Object.fromEntries(fs.readFileSync(path.join(DATA, 'format', 'e15', 'motorer-flash.jsonl'), 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l)).map(r => [r.id, r]))
  const ids = las(path.join(DATA, 'format', 'e23', 'ids.json')), r = frö(25)
  const lag = ids.filter(i => ['i_bilden', 'i_klippningen'].includes(R[i].hantverk)).map(i => [r(), i]).sort((a, b) => a[0] - b[0]).slice(0, 60).map(x => x[1])
  const hog = ids.filter(i => ['i_iden', 'i_personen'].includes(R[i].hantverk)).map(i => [r(), i]).sort((a, b) => a[0] - b[0]).slice(0, 60).map(x => x[1])
  fs.writeFileSync(path.join(E, 'urval.json'), JSON.stringify({ lag, hog })); console.log(lag.length, hog.length); process.exit(0)
}
const V = varde('--villkor', 'p0'), M = { p0: 10, p40: 6, p60: 4, p70: 3 }[V], PAR = Number(varde('--par', 3))
const U = las(path.join(E, 'urval.json')), ids = [...U.lag, ...U.hog]
const SVART = path.join(D, 'svart.mp4')
if (!fs.existsSync(SVART)) await kor(verktyg.ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=240x426:r=2:d=1', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '32k', SVART])
async function delar(id) {
  const d = Number((await kor(verktyg.ffprobe, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', liten(id)])).trim()), L = d / M, ut = []
  for (let k = 0; k < M; k++) { const f = path.join(D, `${id}_m${M}_${k}.mp4`); if (!fs.existsSync(f)) await kor(verktyg.ffmpeg, ['-y', '-v', 'error', '-ss', (k * L).toFixed(2), '-t', L.toFixed(2), '-i', liten(id), '-r', '2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '33', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ac', '1', '-b:a', '32k', f]); ut.push(f) }
  return ut
}
const schema = { type: 'object', required: ['poster'], properties: { poster: { type: 'array', minItems: 10, maxItems: 10, items: { type: 'object', required: ['post', 'vad'], properties: { post: { type: 'integer' }, vad: { type: 'string', maxLength: 200 } } } } } }
const UT = path.join(E, V); fs.mkdirSync(UT, { recursive: true })
const kvar = ids.filter(id => !fs.existsSync(path.join(UT, `${id}.json`)))
console.log(`${V}: ${kvar.length} klipp, ${M} verkliga poster av 10`)
let i = 0, ny = 0, fel = 0
await Promise.all(Array.from({ length: PAR }, async () => { while (i < kvar.length) { const id = kvar[i++]; try {
  const del = await delar(id), r = frö([...id].reduce((s, c) => s + c.charCodeAt(0), 0) * 7 + M)
  const platser = Array.from({ length: 10 }, (_, k) => k).map(k => [r(), k]).sort((a, b) => a[0] - b[0]).slice(0, M).map(x => x[1]).sort((a, b) => a - b)
  const poster = Array.from({ length: 10 }, (_, k) => platser.includes(k) ? { verklig: platser.indexOf(k) } : { verklig: null })
  const inn = [{ text: 'Tio poster. Säg vad varje post är.' }]
  poster.forEach((p, k) => { inn.push({ text: `Post ${k + 1}:` }); inn.push({ fil: p.verklig === null ? SVART : del[p.verklig] }) })
  const svar = await beaconDelar({ modell: 'google/gemini-3.8-flash', schema, temperatur: 0.1, delar: inn })
  fs.writeFileSync(path.join(UT, `${id}.json`), JSON.stringify({ id, villkor: V, verkliga: platser.map(k => k + 1), poster: svar.data.poster })); ny++
} catch (e) { fel++; console.log('  FEL', id, e.message.slice(0, 140)) } } }))
console.log(`klart: ${ny} nya, ${fel} fel, ${beaconKostnad.usd.toFixed(2)} USD`)
