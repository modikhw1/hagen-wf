// Underlag för Miles-pass 6 (ägarens skärm): kundlinjer, klipp i blind ordning, anpassningar v5, omtest.
//   node format/h-pass6-underlag.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const H = path.join(DATA, 'format', 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const R = las(path.join(H, 'pass6', 'forregistrering.json'))
let fro = 606; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }
const bokstav = ['A', 'B', 'C']
const ordning = Object.fromEntries(R.kunder.map(k => [k, bl(R.prognos[k].map(x => x.id))]))
fs.writeFileSync(path.join(H, 'pass6', 'ordning.json'), JSON.stringify(ordning, null, 1))
let md = `# Pass 6: test av harnessen v5 (4 nov 2026)\n\nTre nya kunder med fem biblioteksklipp var, i blind ordning. Bedöm hur väl varje klipp passar **just den kunden** som nästa klipp (1–5) och om du skulle rekommendera det som det är, med ändringar eller inte. Några klipp visas för flera kunder: det är meningen. Sist för varje kund kommer en anpassning. Allra sist kommer tre klipp från tidigare pass (kund D–F), som omtest.\n`
R.kunder.forEach((k, i) => {
  const L = las(path.join(H, 'linje', `${k}.json`)), A = las(path.join(H, 'anpassning5', `${k}.json`))
  md += `\n## Kund ${bokstav[i]}: @${k}\nProfil: https://www.tiktok.com/@${k}\n\n${L.linje}\n- **Frontfigurer:** ${L.frontfigurer.map(f => `${f.etikett}: ${f.styrka}`).join(' ') || 'inga'}\n- **Skulle sticka ut:** ${L.sticker_ut.join('; ')}\n\n`
  ordning[k].forEach((id, j) => { md += `${bokstav[i]}${j + 1}. ${R.prognos[k].find(x => x.id === id).url}\n` })
  md += `\n### Anpassning ${bokstav[i]}: ${A.titel}\nKälla: ${A.url}\n\n${A.varfor_passar}\n\n**Kärnan:** ${A.karna}${A.som_den_ar ? ' Gör den som den är, med praktiska byten.' : ''}\n\n**Det som bär:**\n${A.bar.map(b => `- ${b.vad} (${b.varfor})`).join('\n')}\n\n**Fritt:** ${A.fritt.join('; ')}\n\n**Personen:** ${A.person.vem}, ${A.person.funktion === 'fokus' ? 'personen bär' : A.person.funktion === 'behallare' ? 'personen framför konceptet' : 'roller'}. ${A.person.kraver}\n\n**Byten:** ${A.byten.join('; ')}\n\n**Ton:** ${A.ton} Exempel: ${A.exempelrepliker.map(x => `"${x}"`).join(' ')}\n\n**Undvik:** ${A.racken.join('; ')}\n\n**Brief:** ${A.brief}\n\n**Rätt om:** ${A.ratt_om}\n`
})
const U = las(path.join(H, 'validering', 'urval.json'))
md += `\n## Omtest: kund D–F från tidigare pass\n`
R.omtest.forEach((o, i) => { const c = U[o.konto].klipp.find(c => c.pos === o.pos); md += `- **Kund ${'DEF'[i]}: @${o.konto}** (https://www.tiktok.com/@${o.konto}): ${c.url}\n` })
fs.writeFileSync(path.join(DATA, '..', 'karta', 'videoforandring', 'miles', 'pass-6-underlag.md'), md)
console.log(JSON.stringify(Object.fromEntries(Object.entries(ordning).map(([k, ids]) => [k, ids.map(id => R.prognos[k].find(x => x.id === id).avsandare)]))))
