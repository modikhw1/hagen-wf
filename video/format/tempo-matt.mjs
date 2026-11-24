// Tempo och ljud ur lokala mp4 utan modell (6 nov 2026). Förregistrering: data/format/tempo/forregistrering.json.
// ffmpeg.exe blockeras av Windows på den här datorn, så allt mäts med ffprobe och lavfi-filter:
//   klipptakt: movie=...,fps=8,scale=128:-2,select=gt(scene\,0.3) (antal scenbyten)
//   ljud: amovie=...,silencedetect=n=-35dB:d=0.2,ebur128=metadata=1,astats=metadata=1:reset=0
//   node format/tempo-matt.mjs [--samtidigt 6]
// Resultat: data/format/tempo/matt.jsonl (en rad per klipp, återupptas)
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { execFile } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'

const args = process.argv.slice(2), varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const UT = path.join(DATA, 'format', 'tempo', 'matt.jsonl'), DL = path.join(os.homedir(), 'Downloads')
const klar = new Set(fs.existsSync(UT) ? fs.readFileSync(UT, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l).id) : [])
const filer = [], ENDAST = process.env.TEMPO_ENDAST ? new Set(process.env.TEMPO_ENDAST.split(',')) : null
for (const kalla of ['letrend-bibliotek', 'letrend-bank', 'letrend-e4']) {
  const rot = path.join(DL, kalla); if (!fs.existsSync(rot)) continue
  for (const k of fs.readdirSync(rot)) { const d = path.join(rot, k); if (!fs.statSync(d).isDirectory()) continue
    for (const f of fs.readdirSync(d)) if (f.endsWith('.mp4')) { const id = `${k}-${f.replace(/\.mp4$/, '')}`; if (!klar.has(id) && (!ENDAST || ENDAST.has(id)) && !filer.some(x => x.id === id)) filer.push({ id, kalla, fil: path.join(d, f) }) } }
}
const probe = (a, cwd) => new Promise(res => execFile('ffprobe', ['-v', 'error', ...a], { maxBuffer: 64 * 1024 * 1024, cwd }, (e, out) => res(e ? null : out)))
// lavfi-sökvägar: snedstreck framåt, kolon och kommatecken skyddade
const lav = f => f.replace(/\\/g, '/').replace(/:/g, '\\:').replace(/,/g, '\\,').replace(/'/g, "\\'")
async function mat(x) {
  const dir = path.dirname(x.fil), fn = path.basename(x.fil)
  const dur = parseFloat(await probe(['-show_entries', 'format=duration', '-of', 'csv=p=0', fn], dir))
  const sc = await probe(['-f', 'lavfi', '-i', `movie=${fn},fps=8,scale=128:-2,select=gt(scene\\,0.3)`, '-show_entries', 'frame=pts_time', '-of', 'csv=p=0'], dir)
  const au = await probe(['-f', 'lavfi', '-i', `amovie=${fn},silencedetect=n=-35dB:d=0.2,ebur128=metadata=1,astats=metadata=1:reset=0`, '-show_entries', 'frame_tags=lavfi.silence_duration,lavfi.r128.LRA,lavfi.astats.Overall.RMS_level', '-of', 'default=nw=1'], dir)
  const r = { id: x.id, kalla: x.kalla, langd: dur, byten: sc == null ? null : sc.split('\n').filter(l => l.trim()).length }
  if (au) { let tyst = 0, lra = null, rms = null; for (const l of au.split('\n')) { const m = l.match(/TAG:lavfi\.(silence_duration|r128\.LRA|astats\.Overall\.RMS_level)=(-?[\d.]+|-inf)/); if (!m) continue; if (m[1] === 'silence_duration') tyst += +m[2]; else if (m[1] === 'r128.LRA') lra = +m[2]; else rms = m[2] === '-inf' ? -120 : +m[2] } r.tyst = dur ? tyst / dur : null; r.lra = lra; r.rms = rms } else r.ljud = false
  r.takt = r.byten != null && dur ? 10 * r.byten / dur : null
  fs.appendFileSync(UT, JSON.stringify(r) + '\n')
}
let nasta = 0, n = 0; const t0 = Date.now()
const arb = async () => { while (nasta < filer.length) { const x = filer[nasta++]; try { await mat(x) } catch (e) { console.log(x.id, e.message) } if (++n % 100 === 0) console.log(`${n}/${filer.length} (${Math.round((Date.now() - t0) / 1000)} s)`) } }
console.log(`${filer.length} klipp att mäta (${klar.size} klara)`)
await Promise.all(Array.from({ length: +varde('--samtidigt', 6) }, arb))
console.log('klart')
