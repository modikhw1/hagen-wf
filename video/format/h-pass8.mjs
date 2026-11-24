// Pass 8 (4 nov 2026): anpassningens form och scenplanen. Per kund ur pass 4–5:
//   två anpassningar av SAMMA källklipp, v0 (scenlista) och v5 (kärna, det som bär, fritt, person, ton), i blind ordning
//   scenplanen för källklippet (h-scener.mjs): ägaren säger vilka scener hen skulle göra om, och varför
// Sist: punkterna "att bekräfta" i kundlinjerna för alla nio kunder.
// Låst i data/format/harness/pass8/forregistrering.json.
//   node format/h-pass8.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { scenplan } from './h-scener.mjs'
const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), P = path.join(H, 'pass8'); fs.mkdirSync(P, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8')), reg = path.join(P, 'forregistrering.json')
if (fs.existsSync(reg)) { console.log('pass 8 är redan låst'); process.exit(0) }
const KUNDER = ['pizzeriamums', 'babulsofficial', 'anettesrestaurang', 'chickenstreet.canada', 'kebabbabes', 'blackstonesteakhouse']
let fro = 808; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const v0text = a => `**${a.titel}**\n\n${a.ide}\n\n**Roller:** ${a.roller.map(r => `${r.roll}: ${r.vem}`).join('; ')}\n\n${a.scener.map(s => `${s.nr}. (${s.sekunder} s) ${s.vad} *Replik:* ${s.replik} *Bild:* ${s.bild}`).join('\n')}\n\n**Byts:** ${a.byts.join('; ')}\n\n**Behålls:** ${a.behalls.join('; ')}\n\n**Brief:** ${a.brief}\n\n**Rätt om:** ${a.ratt_om}`
const v5text = a => `**${a.titel}**\n\n${a.varfor_passar}\n\n**Kärnan:** ${a.karna}${a.som_den_ar ? ' Gör den som den är, med praktiska byten.' : ''}\n\n**Det som bär:**\n${a.bar.map(b => `- ${b.vad} (${b.varfor})`).join('\n')}\n\n**Fritt:** ${a.fritt.join('; ')}\n\n**Personen:** ${a.person.vem}. ${a.person.kraver}\n\n**Byten:** ${a.byten.join('; ')}\n\n**Ton:** ${a.ton} Exempel: ${a.exempelrepliker.map(x => `"${x}"`).join(' ')}\n\n**Undvik:** ${a.racken.join('; ')}\n\n**Brief:** ${a.brief}\n\n**Rätt om:** ${a.ratt_om}`
const ATG = { behall: 'behåll', fritt: 'fritt', byt_produkt: 'byt produkt', byt_lokal: 'byt lokal', frontfigur: 'frontfiguren tar rollen', risk: 'risk: karisma kunden saknar', eget_tal: 'byt till eget tal', forenkla: 'förenkla' }
const bok = 'ABCDEF', rader = []
let md = `# Pass 8: anpassningens form och scenplanen (4 nov 2026)\n\nSex kunder från pass 4–5. För varje kund finns två anpassningar av **samma** källklipp i blind ordning (version 1 och 2). Säg vilken du hellre skickar och varför. Titta sedan på scenplanen: vilka scener skulle du göra om för kunden, och vilka skulle du behålla? Allra sist kommer en lista med påståenden om kunderna, som du bekräftar eller rättar.\n`
KUNDER.forEach((k, i) => {
  const a0 = las(path.join(H, 'validering', 'anpassning', `${k}.json`)), a5 = las(path.join(H, 'anpassning5-samma', `${k}.json`))
  const v5forst = sl() < 0.5
  const kort = las(path.join(H, 'v5', `${a0.kalla}.json`)), plan = scenplan(kort, las(path.join(H, 'linje', `${k}.json`)))
  rader.push({ kund: k, bokstav: bok[i], kalla: a0.kalla, url: kort.url, version1: v5forst ? 'v5' : 'v0', version2: v5forst ? 'v0' : 'v5', scenplan: plan.beats.map(b => ({ nr: b.nr, atgard: b.atgard })) })
  md += `\n## Kund ${bok[i]}: @${k}\nKällklipp: ${kort.url}\n\n### Version 1\n${v5forst ? v5text(a5) : v0text(a0)}\n\n### Version 2\n${v5forst ? v0text(a0) : v5text(a5)}\n\n### Scenplan\n${plan.beats.map(b => `${b.nr}. ${b.vad}: **${ATG[b.atgard]}** (${b.skal})`).join('\n')}\n`
})
const alla = [...KUNDER, ...las(path.join(H, 'pass6', 'forregistrering.json')).kunder]
md += `\n## Att bekräfta\n${alla.map(k => `- **@${k}:** ${las(path.join(H, 'linje', `${k}.json`)).att_bekrafta.join(' / ')}`).join('\n')}\n`
fs.writeFileSync(path.join(DATA, '..', 'karta', 'videoforandring', 'miles', 'pass-8-underlag.md'), md)
fs.writeFileSync(reg, JSON.stringify({
  last: new Date().toISOString() + ' (innan ägaren sett något i pass 8)', rader,
  HP8a: 'Ägaren skickar hellre v5-versionen än v0-versionen för minst 4 av 6 kunder.',
  HP8b: 'Ägarens val av scener att göra om stämmer med scenplanens åtgärd (behåll/fritt mot ändra) för minst 70 % av beatsen.',
  HP8c: 'Beskrivande: andelen påståenden under "att bekräfta" som ägaren säger är fel.',
}, null, 1))
const txt = `Speak English only, the whole time. Never say Swedish, Danish or German words and never try to pronounce account names: say "Client A" to "Client F". Do not greet me, explain the exercise, praise my answers or add your own adjectives. Another system analyses the recording afterwards, so your job is to get my choices and my reasons on the record.

WHO I AM
I run LeTrend. We help local restaurants, bars and cafés make TikTok content that their own staff film on a phone. A content manager (CM) recommends library clips to clients with a written adaptation.

WHAT WE ARE DOING
Six clients from an earlier session. For each client there are two written adaptations of the same library clip on my screen, version 1 and version 2, and a scene plan. I pick the version I would rather send and say why. Then I go through the scene plan. At the end there is a list of statements about the clients that I confirm or correct.

FOR EACH CLIENT
1. Say: "Client [letter]. Read version 1 and version 2 on your screen and tell me when you're done." Wait silently.
2. Ask: "Which would you rather send, version 1 or version 2?"
3. Ask: "Why?" Let me talk. Do not repeat my answer back to me.
4. Ask: "Would you send the other one at all?"
5. Say: "Now the scene plan. Which scenes would you change for this client, and which would you keep?" Let me go through it. Only if I skip a scene, ask once: "And scene [number]?"

AT THE END
6. Say: "Last part: the statements about the clients on your screen. Tell me which ones are wrong." Let me go through them.

HOW TO TALK
- One short question per turn. If I say "next", move on. If I say "quiet" or "wait", stop talking until I speak again.
- Never tell me which version the system made or prefers. You do not know.

TIME
About 30 minutes. When we are done or I say "wrap up", give a closing list of at most eight short lines in my words: what makes an adaptation good, and which scenes need changing and why. Then ask: "Anything important missing?"

Your first turn must be exactly: "Client A. Read version 1 and version 2 on your screen and tell me when you're done."`
fs.writeFileSync(path.join(DATA, '..', 'karta', 'videoforandring', 'miles', 'pass-8.txt'), txt)
console.log(rader.map(r => `${r.bokstav} ${r.kund}: version 1 = ${r.version1}`).join('\n'))
