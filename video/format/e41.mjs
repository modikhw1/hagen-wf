// E41: två domar per klipp (överförbarhet, bärare, hålla, svepsekund), Argon, ett klipp per anrop.
// Förregistrering: data/format/e41/forregistrering.json. Modellen ser aldrig utfall, hylla, nytta eller ägarens svar.
//   cd video && LOVABLE_KONTO=beacon timeout 570 node format/e41.mjs --mangd k1|rep [--par 4] [--max N]
// Återupptas per klipp (hoppar över det som redan finns i data/format/e41/lasning/).
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'

const arg = (n, d) => { const i = process.argv.indexOf(n); return i > 0 ? process.argv[i + 1] : d }
const MANGD = arg('--mangd', 'k1'), PAR = Number(arg('--par', 4)), MAX = Number(arg('--max', 1e9)), MODELL = arg('--modell', 'google/gemini-4-argon')
const ROT = path.resolve(import.meta.dirname, '../..'), UT = path.join(ROT, 'data/format/e41/lasning')
fs.mkdirSync(UT, { recursive: true })

let ids, mapp
if (MANGD === 'k1') {
  const las = JSON.parse(fs.readFileSync(path.join(ROT, 'data/format/kontroll/las.json'), 'utf8'))
  ids = [...new Set(las.K1.flatMap(p => [p.vanster, p.hoger]))]; mapp = path.join(os.homedir(), 'Downloads/letrend-k1')
} else {
  ids = JSON.parse(fs.readFileSync(path.join(ROT, 'data/format/e19/argon-ids.json'), 'utf8')); mapp = path.join(os.homedir(), 'Downloads/letrend-e13')
}
const kvar = ids.filter(i => !fs.existsSync(path.join(UT, `${i}.json`)) && fs.existsSync(path.join(mapp, `${i}.mp4`))).slice(0, MAX)
console.log(`${MANGD}: ${ids.length} id, ${kvar.length} kvar`)

const prompt = `This is a short TikTok clip posted by a restaurant, bar or café. Watch all of it. Do not describe it in marketing language. Answer four things.

1. transferable (1–5): Suppose the staff of an ordinary café filmed the same idea on a phone, performed by an ordinary employee who is not an actor and does not stand out in looks or charisma. How much of what makes this clip work would remain? 1 = almost nothing remains, 5 = almost all of it remains.

2. carrier: what the effect of the clip mainly rests on. Pick one:
   premise (the idea or situation itself), person (who is in it: their looks, charisma, age, voice or way of being), production (camera work, editing skill, set, budget), circumstance (a particular place, weather, event or moment that cannot be arranged at will), postedit (a filter, effect or edit that the punchline depends on), offer (a price, deal or giveaway), food (how the food looks).

3. hold (1–5): How strongly does the clip hold an ordinary viewer scrolling TikTok through its whole length? 5 = there is no moment where one would swipe away, 1 = most would swipe away early.

4. swipe_second: the second where an ordinary viewer would most likely swipe away, or -1 if there is no such moment.

Give one short reason (max 20 words) for transferable and one for hold.`
const schema = { type: 'object', properties: {
  transferable: { type: 'integer', minimum: 1, maximum: 5 }, transferable_reason: { type: 'string', maxLength: 160 },
  carrier: { type: 'string', enum: ['premise', 'person', 'production', 'circumstance', 'postedit', 'offer', 'food'] },
  hold: { type: 'integer', minimum: 1, maximum: 5 }, hold_reason: { type: 'string', maxLength: 160 }, swipe_second: { type: 'number' } },
  required: ['transferable', 'transferable_reason', 'carrier', 'hold', 'hold_reason', 'swipe_second'] }

let ok = 0, fel = 0
const vila = ms => new Promise(r => setTimeout(r, ms))
async function las(id) {
  for (let f = 0; f < 6; f++) {
    try {
      const r = await beaconDelar({ modell: MODELL, schema, temperatur: 0.1, delar: [{ fil: path.join(mapp, `${id}.mp4`) }, { text: prompt }] })
      fs.writeFileSync(path.join(UT, `${id}.json`), JSON.stringify({ id, modell: r.modell, ms: r.ms, usd: r.usage?.cost_usd, ...r.data }))
      ok++; return
    } catch (e) {
      const m = String(e.message ?? e)
      if (/quota|429|503/.test(m)) { await vila(15000 * (f + 1)); continue }
      fel++; console.log('fel', id, m.slice(0, 160)); return
    }
  }
  fel++; console.log('kvot', id)
}
const ko = [...kvar]
await Promise.all(Array.from({ length: PAR }, async () => { while (ko.length) await las(ko.shift()) }))
console.log(`klart ${ok}, fel ${fel}, kostnad ${beaconKostnad.usd.toFixed(3)} USD på ${beaconKostnad.anrop} anrop`)
