// E42: parvis läsning med ägarens två frågor (tittare, bibliotek). Förregistrering data/format/e42/forregistrering.json.
//   cd video && LOVABLE_KONTO=beacon timeout 570 node format/e42.mjs --mangd agare|utfall [--par 6] [--max N]
// Varje par läses i båda ordningarna (AB och BA). Återupptas per läsning.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'

const arg = (n, d) => { const i = process.argv.indexOf(n); return i > 0 ? process.argv[i + 1] : d }
const MANGD = arg('--mangd', 'agare'), PAR = Number(arg('--par', 6)), MAX = Number(arg('--max', 1e9)), MODELL = arg('--modell', 'google/gemini-3.1-pro-preview')
const ROT = path.resolve(import.meta.dirname, '../..'), F = path.join(ROT, 'data/format'), E = path.join(F, 'e42'), UT = path.join(E, 'lasning')
fs.mkdirSync(UT, { recursive: true })
const DL = os.homedir() + '/Downloads/'
const fil = id => [DL + 'letrend-k1/' + id + '.mp4', DL + 'letrend-e13/' + id + '.mp4'].find(f => fs.existsSync(f))

// ---- urval ----
let par = []
const urvalFil = path.join(E, `urval-${MANGD}.json`)
if (fs.existsSync(urvalFil)) par = JSON.parse(fs.readFileSync(urvalFil, 'utf8'))
else if (MANGD === 'agare') {
  const k1 = JSON.parse(fs.readFileSync(path.join(F, 'kontroll/las.json'), 'utf8')).K1
  const p7 = JSON.parse(fs.readFileSync(path.join(F, 'harness/pass7/forregistrering.json'), 'utf8')).par
  par = [...k1.map(p => ({ namn: `k1-${p.nr}`, v: p.vanster, h: p.hoger })), ...p7.map(p => ({ namn: `p7-${p.nr}`, v: p.vanster.id, h: p.hoger.id }))]
  fs.writeFileSync(urvalFil, JSON.stringify(par, null, 1))
} else {
  // frö 42, högst 2 par per konto, |du| >= 0,4, inga ägarklipp
  let s = 42; const rnd = () => (s = (s * 1103515245 + 12345) % 2147483648) / 2147483648
  const U = new Map(fs.readFileSync(path.join(F, 'e15/motorer-flash.jsonl'), 'utf8').trim().split('\n').map(l => JSON.parse(l)).filter(r => r.u != null).map(r => [r.id, r]))
  const agar = new Set(JSON.parse(fs.readFileSync(path.join(E, 'urval-agare.json'), 'utf8')).flatMap(p => [p.v, p.h]))
  const ids = JSON.parse(fs.readFileSync(path.join(F, 'e19/ids.json'), 'utf8')).filter(i => U.has(i) && fil(i) && !agar.has(i))
  const perKonto = {}; for (const i of ids) (perKonto[U.get(i).konto] ??= []).push(i)
  const konton = Object.keys(perKonto).sort(); const kand = []
  for (const k of konton) {
    const xs = perKonto[k].slice().sort(() => rnd() - 0.5); let n = 0; const anv = new Set()
    for (let a = 0; a < xs.length && n < 2; a++) for (let b = a + 1; b < xs.length && n < 2; b++) {
      if (anv.has(xs[a]) || anv.has(xs[b])) continue
      if (Math.abs(U.get(xs[a]).u - U.get(xs[b]).u) >= 0.4) { kand.push({ namn: `u-${k}-${n}`, v: xs[a], h: xs[b] }); anv.add(xs[a]); anv.add(xs[b]); n++ }
    }
  }
  par = kand.sort(() => rnd() - 0.5).slice(0, 200)
  fs.writeFileSync(urvalFil, JSON.stringify(par, null, 1))
}

const prompt = `Two short TikTok clips posted by restaurants, bars or cafés: clip A first, then clip B. Watch both fully. Do not describe them in marketing language.

Answer two separate questions. They may have different answers.

viewer: Which of the two would an ordinary TikTok viewer rather watch to the end and like? (A or B)

library: Which of the two would you rather keep in a library of formats that other restaurants, bars and cafés can make their own version of, with their own staff and a phone? (A or B)

Give one short reason for each (max 25 words).`
const schema = { type: 'object', properties: { viewer: { type: 'string', enum: ['A', 'B'] }, viewer_reason: { type: 'string', maxLength: 200 }, library: { type: 'string', enum: ['A', 'B'] }, library_reason: { type: 'string', maxLength: 200 } }, required: ['viewer', 'viewer_reason', 'library', 'library_reason'] }

const jobb = par.slice(0, MAX).flatMap(p => [[p, 'vh'], [p, 'hv']]).filter(([p, o]) => !fs.existsSync(path.join(UT, `${p.namn}-${o}.json`)) && fil(p.v) && fil(p.h))
console.log(`${MANGD}: ${par.length} par, ${jobb.length} läsningar kvar`)
const vila = ms => new Promise(r => setTimeout(r, ms)); let ok = 0, fel = 0
async function las([p, o]) {
  const [a, b] = o === 'vh' ? [p.v, p.h] : [p.h, p.v]
  for (let f = 0; f < 5; f++) {
    try {
      const r = await beaconDelar({ modell: MODELL, schema, temperatur: 0.1, delar: [{ text: 'CLIP A:' }, { fil: fil(a) }, { text: 'CLIP B:' }, { fil: fil(b) }, { text: prompt }] })
      const till = x => (x === 'A') === (o === 'vh') ? 'v' : 'h'
      fs.writeFileSync(path.join(UT, `${p.namn}-${o}.json`), JSON.stringify({ ...p, ordning: o, modell: r.modell, usd: r.usage?.cost_usd, ...r.data, tittare: till(r.data.viewer), bibliotek: till(r.data.library) }))
      ok++; return
    } catch (e) {
      const m = String(e.message ?? e)
      if (/quota|429|503|JSON/.test(m)) { await vila(10000 * (f + 1)); continue }
      fel++; console.log('fel', p.namn, o, m.slice(0, 140)); return
    }
  }
  fel++; console.log('gav upp', p.namn, o)
}
const ko = [...jobb]
await Promise.all(Array.from({ length: PAR }, async () => { while (ko.length) await las(ko.shift()) }))
console.log(`klart ${ok}, fel ${fel}, kostnad ${beaconKostnad.usd.toFixed(3)} USD`)
