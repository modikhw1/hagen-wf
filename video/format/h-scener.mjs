// Scenplan (4 nov 2026): vilka beats som behålls, byts, skrivs om, förenklas eller lämnas fria när ett
// biblioteksklipp flyttas till en kund, och varför. Ägaren i pass 4: originalet är ryggraden, och harnessen ska
// veta när och varför en scen behöver göras om (för omrendering med enkla platshållare).
// Reglerna kommer ur doktrinen och utfallen (eget ljud, utan efterarbete, karisma hör till kunden):
//   bar = fri                                   → fritt: kunden improviserar eller stryker
//   bunden = produkt  och kundens produkt skiljer → byt produkt: scenen görs om med kundens produkt
//   bunden = lokal    och kunden saknar lokaldelen → byt lokal: scenen görs om i kundens lokal
//   bunden = person   (karisma)                   → kundens frontfigur tar rollen, annars risk
//   bunden = trend    (ljud eller format)          → byt mot eget tal (trendljud sänker nyttan)
//   bunden = redigering                           → förenkla: värdet ska finnas kvar utan efterarbete
//   annars                                        → behåll som det är
//   node format/h-scener.mjs --konto <konto> --id <klipp-id>    (eller utan argument: alla par i pass 6)
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const kortFil = id => [path.join(H, 'v5', `${id}.json`), path.join(F, 'e6', 'kort', `${id}.json`), path.join(F, 'e6r', 'kort', `${id}.json`)].find(fs.existsSync)
const ord = t => new Set((t ?? '').toLowerCase().split(/[^a-zåäö]+/).filter(w => w.length > 3))
export function scenplan(c, L) {
  const kundProd = ord(L.produkter), fram = L.frontfigurer ?? []
  const beats = c.beats.map((b, i) => {
    let atgard = 'behall', skal = 'bär sig själv hos vilken verksamhet som helst'
    if (b.bar === 'fri') { atgard = 'fritt'; skal = 'bär inte idén, kunden gör det på sitt sätt eller stryker det' }
    else if (b.bunden === 'produkt') { const lika = [...ord(b.vad)].some(w => kundProd.has(w)); atgard = lika ? 'behall' : 'byt_produkt'; skal = lika ? 'kunden har samma sorts produkt' : `produkten måste bytas mot kundens (${(L.produkter ?? '').slice(0, 60)})` }
    else if (b.bunden === 'lokal') { atgard = 'byt_lokal'; skal = `görs om i kundens lokal (${(L.lokal ?? []).join(', ') || 'okänd'})` }
    else if (b.bunden === 'person') { const f = fram.find(x => x.funktion === 'fokus') ?? fram[0]; atgard = f ? 'frontfigur' : 'risk'; skal = f ? `${f.etikett} tar rollen: ${f.styrka}` : 'beatet bärs av en persons karisma och kunden har ingen frontfigur' }
    else if (b.bunden === 'trend') { atgard = 'eget_tal'; skal = 'byt trendljudet mot egna repliker: eget tal lyfter, trendljud sänker' }
    else if (b.bunden === 'redigering') { atgard = 'forenkla'; skal = 'värdet ska finnas kvar utan efterarbete: gör effekten enkel eller i kameran' }
    return { nr: i + 1, funktion: b.funktion, bar: b.bar, vad: b.vad, atgard, skal, omrendera: ['byt_produkt', 'byt_lokal', 'frontfigur', 'eget_tal', 'forenkla'].includes(atgard) }
  })
  const karnaRor = beats.filter(b => b.bar === 'karna' && b.omrendera).length
  // Produktjämförelsen är en grov ordheuristik (gemensamma ord), inte en semantisk jämförelse.
  const risker = beats.filter(b => b.atgard === 'risk').length
  const bas = karnaRor ? `${karnaRor} kärnbeat måste göras om: anpassningen rör idéns bärande del` : beats.some(b => b.omrendera) ? 'bara stöd- och fria beats ändras: kärnan kan göras som den är' : 'kan göras som den är'
  return { beats, omrendera: beats.filter(b => b.omrendera).length, karnaRor, risk: risker > 0, sammanfattning: risker ? `${bas}; ${risker} beat bärs av karisma som kunden saknar` : bas }
}
const args = process.argv.slice(2), varde = f => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : null }
if (process.argv[1] && import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const par = varde('--konto') ? [[varde('--konto'), varde('--id')]] : (() => { const R = las(path.join(H, 'pass6', 'forregistrering.json')); return R.kunder.flatMap(k => R.prognos[k].map(x => [k, x.id])) })()
  const ut = {}
  for (const [k, id] of par) { const p = scenplan(las(kortFil(id)), las(path.join(H, 'linje', `${k}.json`))); (ut[k] ??= {})[id] = p; console.log(`${k} ← ${id.split('-')[0]}: ${p.beats.map(b => `${b.nr}:${b.atgard}`).join(' ')} | ${p.sammanfattning}`) }
  if (!varde('--konto')) fs.writeFileSync(path.join(H, 'pass6', 'scenplaner.json'), JSON.stringify(ut, null, 1))
}
