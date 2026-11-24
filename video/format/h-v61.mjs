// Harness v6.1 (4 nov 2026): v6 med E11:s rättelse av matchningens nyttosida (10 650 bankklipp):
//   sketch är fortsättning: en sketch lyfter mest hos en kund som redan gör sketcher
//   tilltal och personer är komplement: de lyfter en kund som mest visar mat
//   fortsättning i sig är neutral
// Låses som en tredje prognos för pass 6, innan ägaren sett klippen.
//   node format/h-v61.mjs --las-pass6
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { varde } from './h-v6.mjs'
const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
export function varde61(c, L) {
  const v = varde(c, L), d = [...v.skal]; let p = v.varde
  const sketch = c.sprak.strategi === 'sketchvarld', tilltal = c.sprak.tilltal === 'till_kamera' || c.sprak.strategi === 'tilltal'
  const kundSketch = L.strategi === 'sketchvarld', kundVisning = ['visning', 'premium_stamning'].includes(L.strategi)
  if (sketch && kundSketch) { p += 1; d.push('sketch hos en sketchkund (fortsättning, E11 +0,15)') }
  if (sketch && kundVisning) { p += 0.25; d.push('sketch hos en visningskund (litet lyft, E11 +0,04–0,07)') }
  if (tilltal && kundVisning) { p += 1; d.push('tilltal hos en visningskund (komplement, E11 +0,10)') }
  if (c.sprak.person !== 'ingen' && kundVisning) { p += 0.5; d.push('person i bild hos en visningskund (E11 +0,12)') }
  return { varde: p, skal: d }
}
if (process.argv[1] && import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}` && process.argv.includes('--las-pass6')) {
  const P = path.join(H, 'pass6'), R = las(path.join(P, 'forregistrering.json')), ut = path.join(P, 'forregistrering-v61.json')
  if (fs.existsSync(path.join(P, 'agare.json'))) { console.log('ägarens svar finns redan: v6.1 kan inte låsas'); process.exit(1) }
  if (fs.existsSync(ut)) { console.log('v6.1 är redan låst'); process.exit(0) }
  const kortFil = id => [path.join(H, 'v5', `${id}.json`), path.join(F, 'e6', 'kort', `${id}.json`)].find(fs.existsSync)
  const prognos = Object.fromEntries(R.kunder.map(k => { const L = las(path.join(H, 'linje', `${k}.json`)); return [k, R.prognos[k].map(x => { const v = varde61(las(kortFil(x.id)), L); return { id: x.id, v61: +v.varde.toFixed(2), skal: v.skal } })] }))
  fs.writeFileSync(ut, JSON.stringify({ last: new Date().toISOString() + ' (efter v5- och v6-låsningarna, innan ägaren sett något klipp i pass 6)', prognos,
    HP6i: 'v6.1 korrelerar med ägarens passform minst lika starkt som v6 (samma 15 par).',
    HP6j: 'Inom de delade klippen ordnar v6.1 kunderna rätt minst lika ofta som v5 och v6.' }, null, 1))
  for (const k of R.kunder) console.log(`${k}: ${prognos[k].map(x => x.v61).join(' | ')}`)
}
