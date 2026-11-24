// Hitta TikTok-konton för matverksamheter med Brave Search API: site:tiktok.com plus segment och stad.
// Handtagen tas ur träffarnas adresser (profiler och klipp), så inget är gissat.
//
//   node profil/brave.mjs [--sidor 2] [--max-fragor 600]
//
// Nyckeln: BRAVE_API_KEY i miljön eller i video/.env.local. Gratisnivån tillåter 1 fråga/s och
// 2 000 frågor/månad. Fynd: data/profil/brave-fynd.json (handtag → frågor). Frågor som redan är
// körda hoppas över, så körningen kan avbrytas. Pröva sedan med: node profil/kandidater.mjs --fran brave
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const SIDOR = Number(varde('--sidor', 2))
const MAX = Number(varde('--max-fragor', 600))
const UT = path.join(DATA, 'profil', 'brave-fynd.json')
const paus = ms => new Promise(r => setTimeout(r, ms))

const NYCKEL = process.env.BRAVE_API_KEY ?? (() => {
  try { return fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).find(l => l.startsWith('BRAVE_API_KEY='))?.slice(14).trim() } catch { return null }
})()
if (!NYCKEL) { console.error('BRAVE_API_KEY saknas (video/.env.local)'); process.exit(1) }

const LAND = {
  se: { stader: ['Stockholm', 'Göteborg', 'Malmö', 'Uppsala', 'Västerås', 'Örebro', 'Linköping', 'Helsingborg', 'Norrköping', 'Jönköping', 'Umeå', 'Lund'], ord: ['restaurang', 'burgare', 'kebab', 'pizzeria', 'kafé', 'bar', 'sushi', 'grill'] },
  dk: { stader: ['København', 'Aarhus', 'Odense', 'Aalborg'], ord: ['restaurant', 'burger', 'shawarma', 'pizzeria', 'café', 'bar', 'sushi', 'grill'] },
  de: { stader: ['Berlin', 'Hamburg', 'München', 'Köln', 'Frankfurt', 'Düsseldorf', 'Stuttgart', 'Leipzig'], ord: ['restaurant', 'burger', 'döner', 'pizzeria', 'café', 'bar', 'imbiss', 'sushi'] },
  uk: { stader: ['London', 'Manchester', 'Birmingham', 'Leeds', 'Glasgow', 'Liverpool', 'Bristol', 'Edinburgh'], ord: ['restaurant', 'burger', 'kebab', 'pizza', 'cafe', 'bar', 'takeaway', 'wings'] },
}
const fragor = Object.entries(LAND).flatMap(([land, { stader, ord }]) => stader.flatMap(s => ord.map(o => ({ land, q: `site:tiktok.com "${o}" ${s}` }))))
const EJ = new Set(['discover', 'tag', 'music', 'search', 'explore', 'live', 'foryou', 'following', 'login', 'about'])

const fynd = fs.existsSync(UT) ? JSON.parse(fs.readFileSync(UT, 'utf8')) : { korda: [], handtag: {} }
const korda = new Set(fynd.korda)
const spara = () => fs.writeFileSync(UT, JSON.stringify({ uppdaterad: new Date().toISOString(), korda: [...korda], handtag: fynd.handtag }, null, 1) + '\n')

async function sok(q, offset) {
  const url = `https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(q)}&count=20&offset=${offset}`
  for (let n = 1; ; n++) {
    const res = await fetch(url, { headers: { 'X-Subscription-Token': NYCKEL, accept: 'application/json' } })
    if (res.status === 429 && n < 5) { await paus(2000 * n); continue }
    if (!res.ok) throw new Error(`brave ${res.status}: ${(await res.text()).slice(0, 200)}`)
    return (await res.json()).web?.results ?? []
  }
}

let antal = 0
for (const { land, q } of fragor) {
  for (let sida = 0; sida < SIDOR; sida++) {
    const nyckel = `${q}#${sida}`
    if (korda.has(nyckel)) continue
    if (antal >= MAX) break
    await paus(1100)
    let traffar
    try { traffar = await sok(q, sida) } catch (e) { console.error(`${q}: ${e.message}`); if (/brave 40[13]/.test(e.message)) process.exit(1); break }
    antal++
    korda.add(nyckel)
    let nya = 0
    for (const r of traffar) {
      const h = r.url?.match(/tiktok\.com\/@([a-zA-Z0-9._]{2,24})/)?.[1]?.toLowerCase().replace(/\.+$/, '')
      if (!h || EJ.has(h)) continue
      if (!fynd.handtag[h]) { fynd.handtag[h] = { land, fragor: [] }; nya++ }
      if (!fynd.handtag[h].fragor.includes(q)) fynd.handtag[h].fragor.push(q)
    }
    spara()
    console.log(`${antal} ${q} (sida ${sida + 1}): ${traffar.length} träffar, ${nya} nya, ${Object.keys(fynd.handtag).length} totalt`)
    if (traffar.length < 20) break

  }
  if (antal >= MAX) break
}
console.log(`klart: ${antal} frågor, ${Object.keys(fynd.handtag).length} handtag i ${UT}`)
