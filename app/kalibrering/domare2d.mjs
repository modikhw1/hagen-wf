// Maskindomare för Rörlighet på riktig video: Gemini ser samma scen genom två virtuella kameror
// (2D-uttryck) och väljer vilken som är mer rörlig och expansiv. Bedömningarna sparas som vanliga
// rader i data/bedomningar/rorlighet-uttryck.jsonl, med bedomare 'gemini-…', så att de kan jämföras
// med människans på samma par (överensstämmelse) innan de används i skala.
//
//   node kalibrering/domare2d.mjs <id> [--par 40] [--modell gemini-3-flash-preview] [--samma-som-manniska]
// --samma-som-manniska: döm exakt de par en människa redan bedömt (för valideringen).
// Kräver dev-servern på localhost:5180 (läser data och renderar via uttryck/matning2d.html).
import fs from 'node:fs'
import path from 'node:path'
import { DATA, TMP } from '../analys/pipeline.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { generera } from '../typer/gemini.mjs'
import { modellFor, placeraAlla, INBYGGD } from './placering.mjs'
import { valjPar, bedomningsRad, VERTIKAL_UTTRYCK } from './par.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const id = args.find((a, i) => !a.startsWith('--') && !['--par', '--modell'].includes(args[i - 1]))
const MODELL = varde('--modell', 'gemini-3-flash-preview')
const ANTAL = Number(varde('--par', 40))
const BAS = 'http://localhost:5180'
const j = u => fetch(BAS + u).then(r => (r.ok ? r.json() : null))

const fil = path.join(DATA, 'bedomningar', `${VERTIKAL_UTTRYCK}.jsonl`)
const lasRader = () => (fs.existsSync(fil) ? fs.readFileSync(fil, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l)) : [])

const SCHEMA = { type: 'object', properties: { val: { type: 'string', enum: ['A', 'B', 'lika'] }, sakerhet: { type: 'number', description: '0–1' }, varfor: { type: 'string', description: 'en mening' } }, required: ['val', 'sakerhet', 'varfor'] }
const FRAGA = `Två korta videor visar exakt samma scen ur ett TikTok-klipp (samma personer och samma handling), men sedd på olika sätt.
Vilken av dem spelas ut med mer FART? Med fart menas: personernas rörelse och momentum, entréer, det som händer runt dem, hur mycket de fyller bilden och varifrån scenen ses. Små personer i en vid bild känns lugnare än samma personer som fyller bilden.
Räkna INTE kameraskak, effekter eller zoomryck som fart.
Svara "lika" bara om du verkligen inte kan skilja dem åt.`

const { chromium } = await import('playwright-core')
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const page = await browser.newPage()
page.setDefaultTimeout(0)
await page.goto(`${BAS}/uttryck/matning2d.html`)
await page.evaluate(() => window.mat2dRedo)

async function video(scen, uttryck) {
  const r = await page.evaluate(a => window.rendera2d(a), { id, scen, uttryck })
  const dir = path.join(TMP, `domare-${Date.now()}-${Math.random().toString(36).slice(2)}`)
  fs.mkdirSync(dir, { recursive: true })
  r.bilder.forEach((b, k) => fs.writeFileSync(path.join(dir, `${String(k + 1).padStart(5, '0')}.jpg`), Buffer.from(b.split(',')[1], 'base64')))
  const ut = path.join(dir, 'v.mp4')
  await kor(verktyg.ffmpeg, ['-v', 'error', '-y', '-framerate', String(r.fps), '-i', '%05d.jpg', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', ut], dir)
  const data = fs.readFileSync(ut).toString('base64')
  fs.rmSync(dir, { recursive: true, force: true })
  return { inlineData: { mimeType: 'video/mp4', data }, videoMetadata: { fps: 5 } }
}

const [an, ut, korr, kal, bed] = await Promise.all([j(`/__data/analys/${id}.json`), j(`/__data/uttryck2d/${id}.json`), j('/__data/brygga/korrektion.json'), j('/__kalib'), j('/__bedomningar/rorlighet')])
const ingen = INBYGGD // 2D: analysens egna mått, alla gäller
const vertikal = kal.vertikaler.find(v => v.id === 'rorlighet')
const m = modellFor({ vertikal, korr: ingen, bibliotek: kal.items.scen, bedomningar: bed ?? [] })
const listor = placeraAlla(an.scener.map((_, i) => (ut.scener[i]?.version === 1 ? ut.scener[i] : null)), { mod: m.mod, namn: m.namn, korr: ingen })

const rader = lasRader()
const paren = []
if (args.includes('--samma-som-manniska')) {
  const gjordaAvGemini = new Set(rader.filter(r => r.bedomare?.startsWith('gemini')).map(r => `${r.a}|${r.b}`))
  for (const r of rader.filter(r => !r.bedomare?.startsWith('gemini') && r.a.startsWith(id + '#') && r.val !== 'hoppa')) {
    if (gjordaAvGemini.has(`${r.a}|${r.b}`)) continue
    const [, s, a] = r.a.split('#'), b = r.b.split('#')[2]
    const A = listor[s]?.find(x => x.id === a), B = listor[s]?.find(x => x.id === b)
    if (A && B) paren.push({ scen: Number(s), a: A, b: B, sort: r.sort ?? 'kamera' })
  }
} else {
  const gjorda = new Set()
  for (let k = 0; k < ANTAL; k++) {
    const p = valjPar(listor, { gjorda, sort: Math.random() < 0.75 ? 'kamera' : 'ankare' })
    if (!p) break
    gjorda.add(`${p.scen}:${[p.a.id, p.b.id].sort().join('|')}`)
    paren.push(p)
  }
}
let ore = 0
for (const [k, p] of paren.entries()) {
  const va = await video(p.scen, p.a.id)
  const vb = await video(p.scen, p.b.id)
  const r = await generera({ modell: MODELL, parts: [{ text: 'Video A:' }, va, { text: 'Video B:' }, vb, { text: FRAGA }], schema: SCHEMA, temperatur: 0, tankande: 'low' })
  ore += r.ore ?? 0
  const val = r.data.val === 'A' ? 'a' : r.data.val === 'B' ? 'b' : 'lika'
  const rad = { ...bedomningsRad({ klipp: id, par: p, val, korr: ingen, namn: m.namn, ms: r.ms, bedomare: MODELL }), sakerhet: r.data.sakerhet, varfor: r.data.varfor, tid: new Date().toISOString() }
  fs.mkdirSync(path.dirname(fil), { recursive: true })
  fs.appendFileSync(fil, JSON.stringify(rad) + '\n')
  console.log(`${k + 1}/${paren.length} scen ${p.scen + 1}: ${r.data.val} (${r.data.sakerhet}) · modellen tror ${p.a.u > p.b.u ? 'A' : 'B'} · ${r.data.varfor}`)
}
console.log(`${paren.length} par, ${ore.toFixed(1)} öre`)
await browser.close()
