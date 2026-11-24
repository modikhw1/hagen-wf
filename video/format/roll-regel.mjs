// H7: rollen i mixen härledd ur formatkortets stabila, beskrivande fält i stället för modellens
// direkta rollomdöme. Regeln är skriven ur ägarens principer (pass 1) och låst 3 nov innan pass 2.
// Ändra den inte förrän pass 2 och 3 är jämförda, annars är testet inte ärligt.
//
//   node format/roll-regel.mjs [--variant v2-gemini-3.1-pro-preview]
// Resultat: data/format/kalib/roll-regel-<variant>.json (låsta förutsägelser per klipp)
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

export function roll(x) {
  const r = x.replikering
  if (x.plattform === 'instagram_polish' || x.plattform === 'reklamfilm') return 'annan_kanal'
  if (x.visning.grad >= 3 && r.specificitet >= 3) return 'annan_kanal'
  if (x.persona.krav === 'stark' && !x.persona.rod_trad) return 'engangsbit'
  if (x.eskalering === 'ingen' && r.skadespel >= 4) return 'engangsbit'
  if (x.premiss.bar === 'nej') return 'engangsbit'
  if (x.salj === 'direkt' || x.skala === 'kedja' || x.visning.grad >= 2) return 'aterkommande_inslag'
  if (x.premiss.bar === 'ja' && x.relation >= 4 && x.vasshet >= 4) return 'huvudnummer'
  if (x.premiss.bar !== 'nej' && x.format_potential >= 3 && x.relation >= 3) return 'stomme'
  if (x.eskalering === 'ingen' && x.vasshet <= 2) return 'utfyllnad'
  return 'glitter'
}

if (process.argv[1]?.endsWith('roll-regel.mjs')) {
  const args = process.argv.slice(2)
  const VARIANT = args.includes('--variant') ? args[args.indexOf('--variant') + 1] : 'v2-gemini-3.1-pro-preview'
  const urval = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'kalib', 'urval.json'), 'utf8'))
  const ut = {}
  for (const k of urval) {
    const x = JSON.parse(fs.readFileSync(path.join(DATA, 'format', VARIANT, `${k.id}.json`), 'utf8'))
    ut[k.nr] = { regel: roll(x), modell: x.roll }
  }
  const fil = path.join(DATA, 'format', 'kalib', `roll-regel-${VARIANT}.json`)
  if (!fs.existsSync(fil)) fs.writeFileSync(fil, JSON.stringify({ last: new Date().toISOString(), prognos: ut }, null, 1))
  const agare = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'kalib', 'agare.json'), 'utf8')).klipp
  let r = 0, m = 0, n = 0
  for (const [nr, p] of Object.entries(ut)) { const o = agare[nr]; if (!o) continue; n++; if (o.roll === p.regel) r++; if (o.roll === p.modell) m++ }
  console.log(`klipp med ägarsvar: ${n}. Regeln träffar ${r}, modellens direkta roll ${m}.`)
  console.log(Object.entries(ut).map(([nr, p]) => `${nr}:${p.regel.slice(0, 6)}${p.regel === p.modell ? '' : '≠' + p.modell.slice(0, 6)}`).join(' '))
}
