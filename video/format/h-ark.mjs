// Underlag för ägaren till Miles-pass 4 och 5: per kund en profil, sex klipp i blind ordning och Pros anpassning.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const V = path.join(DATA, 'format', 'harness', 'validering'), UT = path.join(DATA, '..', 'karta', 'videoforandring', 'miles')
const U = JSON.parse(fs.readFileSync(path.join(V, 'urval.json'), 'utf8'))
const PASS = { 4: ['pizzeriamums', 'babulsofficial', 'anettesrestaurang'], 5: ['chickenstreet.canada', 'kebabbabes', 'blackstonesteakhouse'] }
for (const [p, kunder] of Object.entries(PASS)) {
  let t = `# Pass ${p}: matchning mot kund (4 nov 2026)\n\nTre kunder med sex biblioteksklipp var. Bedöm hur väl varje klipp passar **just den kunden** som nästa klipp, på en skala från 1 till 5, och om du skulle rekommendera det som det är, med ändringar eller inte. Klippen kommer i blind ordning. Sist för varje kund kommer en färdig anpassning att bedöma.\n`
  kunder.forEach((k, i) => {
    const L = 'ABC'[i], { profil, klipp } = U[k], a = JSON.parse(fs.readFileSync(path.join(V, 'anpassning', `${k}.json`), 'utf8'))
    t += `\n## Kund ${L}: @${k}\nProfil: https://www.tiktok.com/@${k}\n\n${profil.beskrivning}\n- **Frontfigurer:** ${profil.frontfigurer.map(f => `${f.etikett}: ${f.styrka}`).join('; ') || 'inga'}\n- **Ton:** ${profil.persona}\n- **Luckor:** ${profil.luckor.join('; ')}\n\n`
    t += klipp.map(c => `${L}${c.pos}. ${c.url}`).join('\n') + '\n'
    t += `\n### Anpassning ${L}: ${a.titel}\n${a.ide}\n\n**Roller:** ${a.roller.map(r => `${r.roll}: ${r.vem}`).join('; ')}\n\n` + a.scener.map(s => `${s.nr}. (${s.sekunder} s) ${s.vad} *Replik:* ${s.replik} *Bild:* ${s.bild}`).join('\n') + `\n\n**Byts:** ${a.byts.join('; ')}\n\n**Behålls:** ${a.behalls.join('; ')}\n\n**Brief:** ${a.brief}\n\n**Rätt om:** ${a.ratt_om}\n`
  })
  fs.writeFileSync(path.join(UT, `pass-${p}-underlag.md`), t)
  console.log(`pass ${p}: ${t.length} tecken`)
}
