// Pass 8b (6 nov 2026): kund B–F med tre versioner (v5, v0, v3) i låst blind ordning
// enligt data/format/harness/pass8/forregistrering-v3.json. Läser v5- och v0-texterna ur pass 8-underlaget
// och v3 ur pass8/v3/. Skriver karta/videoforandring/miles/pass-8b-underlag.md.
//   node format/h-pass8b.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const H = path.join(DATA, 'format', 'harness'), M = path.join(DATA, '..', 'karta', 'videoforandring', 'miles')
const R = las(path.join(H, 'pass8', 'forregistrering.json')).rader, O = las(path.join(H, 'pass8', 'forregistrering-v3.json')).ordning
const md = fs.readFileSync(path.join(M, 'pass-8-underlag.md'), 'utf8')
const ATG = { behall: 'behåll', byt: 'byt', eget_tal: 'egna ord', forenkla: 'förenkla', tillat: 'tillåt, tvinga inte', fritt: 'fritt' }
const v3text = a => `**${a.titel}**\n\n**Kärnan:** ${a.karna}\n\n**Scenerna:**\n${a.scener.map((s, i) => `${i + 1}. ${s.vad} *Bild:* ${s.bild}${s.replik ? ` *Replik:* "${s.replik}"` : ''} (${ATG[s.atgard]})`).join('\n')}\n\n**Tight:** ${a.tight}${a.tillat.length ? `\n\n**Tillåt:** ${a.tillat.join('; ')}` : ''}\n\n**Undvik:** ${a.undvik.join('; ')}\n\n**Brief:** ${a.brief}\n\n**Rätt om:** ${a.ratt_om}`

// Dela pass 8-underlaget i block per kund
const block = {}
for (const del of md.split(/\n(?=## )/)) { const m = del.match(/^## Kund ([A-F]): @(\S+)/); if (m) block[m[2]] = del }
const efter = md.slice(md.indexOf('## Att bekräfta'))
const bokstav = ['B', 'C', 'D', 'E', 'F']
let ut = `# Pass 8b: anpassningens form, tre versioner (6 nov 2026)\n\nFem kunder. För varje kund finns tre anpassningar av **samma** källklipp i blind ordning (version 1, 2 och 3). Säg vilken du hellre skickar, gärna i ordning, och varför. Titta sedan på scenplanen. Sist kommer påståendena om kunderna och serien.\n`
for (const [i, kund] of Object.keys(O).entries()) {
  const r = R.find(x => x.kund === kund), b = block[kund]
  const v1 = b.match(/### Version 1\n([\s\S]*?)\n### Version 2/)[1].trim(), v2 = b.match(/### Version 2\n([\s\S]*?)\n### Scenplan/)[1].trim()
  const plan = b.match(/### Scenplan\n([\s\S]*)$/)[1].trim()
  const text = { [r.version1]: v1, [r.version2]: v2, v3: v3text(las(path.join(H, 'pass8', 'v3', `${kund}.json`))) }
  ut += `\n## Kund ${bokstav[i]}: @${kund}\nKällklipp: ${r.url}\n\n${O[kund].map((v, j) => `### Version ${j + 1}\n${text[v]}`).join('\n\n')}\n\n### Scenplan\n${plan}\n`
}
ut += `\n${efter}`
fs.writeFileSync(path.join(M, 'pass-8b-underlag.md'), ut)
console.log(`pass-8b-underlag.md: ${ut.split(/\s+/).length} ord`)
