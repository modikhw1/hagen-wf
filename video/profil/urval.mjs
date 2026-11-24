// Efterfilter på profil/kandidater.mjs: ger ägaren en kort lista med troliga verksamheter.
// Läser data/profil/kandidater.json, hämtar profilsidan igen (bio, kontots språk, bio-länk) och
// skriver karta/videoforandring/kandidater-urval.md.
//
//   node profil/urval.mjs
//
// Regler (ägarens 3 nov): recensenter, livsstils- och kreatörskonton samt officiella stads-/turismkonton
// tas bort. Kvar blir konton med stark verksamhetssignal i bion: adress med nummer, telefon,
// öppettider, bokning/beställning eller leveranstjänst. Kontots språk ska vara svenska, danska,
// tyska eller engelska.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const PROFIL = path.join(DATA, 'profil')
const MD = path.join(DATA, '..', 'karta', 'videoforandring', 'kandidater-urval.md')
const las = (f, d) => { try { return JSON.parse(fs.readFileSync(f, 'utf8')) } catch { return d } }
const paus = ms => new Promise(r => setTimeout(r, ms))

const KREATOR = /mattips|matblogg|recension|food ?(tips|guide|review|blogger|lover|diar)|foodie|spots|hidden gems|discover|exploring|explore|lifestyle|vlog|travel|tourist|turist|tourism|turism|official|officiell|kooperation|cooperation|collab|samarbete|promos?\b|dm for|creator|influencer|ugc|documenting|media\b|@(gmail|hotmail|outlook|web\.de|gmx|yahoo|icloud)|📩|💌|✉️|follow for|with me|my world|dad life|mum life/i
const NAMN = /foodie|eats|munchies|guide|tips|blogg|blog|review|recens|livet|lifestyle|town|staden|city|stories|onthemove|travel|resor|diary|diaries|media|spots/
const AFFAR = [
  /\b\d{1,4}[a-z]? ?(st|street|rd|road|gatan|gata|vägen|väg|vej|gade|straße|strasse|str\.|allé|torg|plads|lane|high st)\b/i,
  /\b(gatan|vägen|vej|gade|straße|strasse|street|road)\b ?\d/i,
  /\b\d{3} ?\d{2}\b|\b\d{5}\b|\b[A-Z]{1,2}\d{1,2}[A-Z]? ?\d[A-Z]{2}\b/,
  /tel[:. ]|\+\d{2} ?\d|📞|☎|call us|ring/i,
  /öppet|öppettider|åbent|geöffnet|uhr|open (daily|every|mon|tue|7)|mo[-–]|mån[-–]/i,
  /boka|book (a|bord|your|now|table)|bestil|bestell|reserv|beställ|order (now|online|here)|takeaway|take away|leverans|delivery|lieferando|wolt|foodora|uber ?eats|just ?eat|deliveroo/i,
  /restaurang|restaurant|pizzeria|café|cafe|kaffebar|bar\b|grill|kebab|burger|sushi|bistro|bageri|bakery|bäckerei|imbiss|pub\b|diner|kitchen|kök\b|takeaway/i,
]
const SPRAK = new Set(['sv', 'da', 'de', 'en', 'nb', 'no'])

async function info(h) {
  for (let n = 1; n <= 3; n++) {
    try {
      const t = await (await fetch(`https://www.tiktok.com/@${h}`, { headers: { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36' } })).text()
      const bio = t.match(/"signature":"((?:[^"\\]|\\.)*)"/)?.[1]
      const sprak = [...t.matchAll(/"language":"([a-z-]+)"/g)].map(m => m[1])
      return {
        bio: bio ? JSON.parse(`"${bio}"`).replace(/\s+/g, ' ').trim() : '',
        sprak: sprak.length > 1 ? sprak[1] : null, // första är sidans gränssnitt, andra kontots
        lank: t.match(/"bioLink":\{"link":"((?:[^"\\]|\\.)*)"/)?.[1] ? JSON.parse(`"${t.match(/"bioLink":\{"link":"((?:[^"\\]|\\.)*)"/)[1]}"`) : null,
      }
    } catch { await paus(2000 * n) }
  }
  return null
}

const beslut = las(path.join(PROFIL, 'beslut.json'), { behall: {}, stryk: [] })
const stryk = new Set(beslut.stryk)
const alla = las(path.join(PROFIL, 'kandidater.json'), { kandidater: [] }).kandidater
  .filter(k => (k.skal === 'obedömd' || k.skal === 'ok') && !stryk.has(k.handtag) && !beslut.behall[k.handtag])
let i = 0
await Promise.all(Array.from({ length: 10 }, async () => { while (i < alla.length) { const k = alla[i++]; k.info = await info(k.handtag) } }))

const ut = { verksamhet: [], kreator: [], sprak: [], svag: [] }
for (const k of alla) {
  const bio = k.info?.bio ?? ''
  const lank = k.info?.lank ?? ''
  if (NAMN.test(k.handtag) || KREATOR.test(bio)) { ut.kreator.push(k); continue }
  if (k.info?.sprak && !SPRAK.has(k.info.sprak.slice(0, 2))) { ut.sprak.push(k); continue }
  k.signaler = AFFAR.filter(r => r.test(bio)).length + (/\.(se|dk|de|co\.uk|uk)\b/.test(lank) && !/linktr|linkin|beacons/.test(lank) ? 1 : 0)
  ;(k.signaler >= 2 ? ut.verksamhet : ut.svag).push(k)
}
const tal = n => n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k` : String(n)
const rad = k => `- [@${k.handtag}](https://www.tiktok.com/@${k.handtag}) · ${tal(k.foljare)} följare, median ${tal(k.storlek.median)}, ${k.storlek.aktiva} klipp/90 d${k.info?.sprak ? ` · ${k.info.sprak}` : ''} · ”${(k.info?.bio ?? '').slice(0, 100)}”`
ut.verksamhet.sort((a, b) => b.storlek.median - a.storlek.median)
ut.svag.sort((a, b) => b.storlek.median - a.storlek.median)
fs.writeFileSync(MD, `# Urval att titta på (${new Date().toISOString().slice(0, 16).replace('T', ' ')})

${alla.length} konton klarade följare (700–30 000), storlek och aktivitet. Bion och namnet har sedan sorterat bort ${ut.kreator.length} recensenter, kreatörer och officiella konton, och ${ut.sprak.length} på annat språk än svenska, danska, tyska eller engelska. Säg vilka som ska behållas, så förs de in i \`data/profil/beslut.json\`.

## Troliga verksamheter (${ut.verksamhet.length})

Minst två verksamhetssignaler i bion: adress, telefon, öppettider, bokning/beställning, restaurangord eller egen webbplats.

${ut.verksamhet.map(rad).join('\n')}

## Osäkra (${ut.svag.length})

${ut.svag.map(rad).join('\n')}
`)
console.log(`verksamheter ${ut.verksamhet.length}, osäkra ${ut.svag.length}, kreatörer ${ut.kreator.length}, annat språk ${ut.sprak.length} → ${MD}`)
