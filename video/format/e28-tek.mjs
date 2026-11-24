// E28, lager 1: teknisk mening utan modell. Per klipp (små kopior, 2 bilder/s, mono 32k):
//   klippsekvens (scenbyten, skottlängder), rörelse per bild (scenpoäng), tal och tystnad, ljudnivå.
//   node format/e28-tek.mjs [--par 4]
// Resultat: data/format/e28/tek.jsonl (en rad per klipp, återupptas)
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFile } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'
import { verktyg } from '../analys/verktyg.mjs'

const args = process.argv.slice(2), PAR = Number(args[args.indexOf('--par') + 1] || 4)
const E = path.join(DATA, 'format', 'e28'); fs.mkdirSync(E, { recursive: true })
const UT = path.join(E, 'tek.jsonl'), DIR = path.join(os.homedir(), 'Downloads', 'letrend-e13')
const klar = new Set(fs.existsSync(UT) ? fs.readFileSync(UT, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l).id) : [])
const ids = fs.readdirSync(DIR).filter(f => /-\d+\.mp4$/.test(f)).map(f => f.replace(/\.mp4$/, '')).filter(id => !klar.has(id))
const kor = a => new Promise(res => execFile(verktyg.ffmpeg, a, { maxBuffer: 64 * 1024 * 1024, windowsHide: true }, (e, out, err) => res(String(err))))
const med = x => { const s = [...x].sort((a, b) => a - b); return s.length ? s[Math.floor(s.length / 2)] : 0 }
const r2 = x => Math.round(x * 100) / 100

async function mat(id) {
  const f = path.join(DIR, `${id}.mp4`)
  const log = await kor(['-hide_banner', '-nostats', '-i', f, '-vf', "select='gte(scene,0)',metadata=print", '-af', 'silencedetect=n=-35dB:d=0.3,ebur128=framelog=quiet', '-f', 'null', '-'])
  // första bilden har ingen föregångare; dess scenpoäng räknas inte
  const t = [...log.matchAll(/pts_time:([0-9.]+)/g)].map(m => +m[1]).slice(1), sc = [...log.matchAll(/lavfi\.scene_score=([0-9.]+)/g)].map(m => +m[1]).slice(1)
  const dur = +(log.match(/Duration: (\d+):(\d+):([0-9.]+)/) ?? []).slice(1).reduce((s, v, i) => s + v * [3600, 60, 1][i], 0) || (t.at(-1) ?? 0) + 0.5
  const byten = t.filter((_, i) => sc[i] > 0.3)
  const gr = [0, ...byten, dur], skott = gr.slice(1).map((v, i) => v - gr[i]).filter(x => x > 0)
  const tyst = [...log.matchAll(/silence_start: ([0-9.]+)[\s\S]*?silence_end: ([0-9.]+)/g)].map(m => [+m[1], +m[2]])
  const tystTid = tyst.reduce((s, [a, b]) => s + Math.max(0, Math.min(b, dur) - a), 0)
  const forstaLjud = tyst.length && tyst[0][0] < 0.05 ? tyst[0][1] : 0
  const sum = log.slice(log.lastIndexOf('Integrated loudness')), I = +(sum.match(/I:\s+(-?[0-9.]+) LUFS/) ?? [0, NaN])[1], LRA = +(sum.match(/LRA:\s+([0-9.]+) LU/) ?? [0, NaN])[1]
  const rorelse = sc.length ? sc.reduce((s, v) => s + v, 0) / sc.length : 0, tidig = sc.filter((_, i) => t[i] < 2), sen = sc.filter((_, i) => t[i] >= 2)
  return { id, langd: r2(dur), byten: byten.length, takt: r2(byten.length / dur), skott_median: r2(med(skott)), skott_max: r2(Math.max(...skott)), skott_max_andel: r2(Math.max(...skott) / dur),
    skott_cv: r2(skott.length > 1 ? Math.sqrt(skott.reduce((s, v) => s + (v - skott.reduce((a, b) => a + b, 0) / skott.length) ** 2, 0) / skott.length) / (dur / skott.length) : 0),
    forsta_byte: r2(byten[0] ?? dur), byten_3s: byten.filter(x => x < 3).length, rorelse: r2(rorelse * 100), rorelse_2s: r2(tidig.length ? 100 * tidig.reduce((s, v) => s + v, 0) / tidig.length : 0),
    rorelse_kvot: r2(sen.length && rorelse ? (tidig.reduce((s, v) => s + v, 0) / Math.max(1, tidig.length)) / (sen.reduce((s, v) => s + v, 0) / sen.length) : 1),
    ljud_andel: r2(1 - tystTid / dur), pauser: tyst.length, forsta_ljud: r2(forstaLjud), lufs: I, lra: LRA, skott }
}
console.log(`${ids.length} klipp att mäta, ${PAR} samtidigt`)
let i = 0, n = 0
await Promise.all(Array.from({ length: PAR }, async () => { while (i < ids.length) { const id = ids[i++]; try { fs.appendFileSync(UT, JSON.stringify(await mat(id)) + '\n'); n++ } catch (e) { console.log('FEL', id, e.message.slice(0, 100)) } if (n % 300 === 0 && n) console.log(`  ${n}`) } }))
console.log(`klart: ${n} klipp`)
