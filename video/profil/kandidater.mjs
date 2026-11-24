// Kandidatlista för nya konton: sök brett, pröva hårt, och låt ägaren stryka för hand.
//
//   node profil/kandidater.mjs [--antal 100] [--golv 3000]
//
// Källor:
//  1. Gemini med Google-sökning, många smala frågor: land (Sverige, Danmark, Tyskland, Storbritannien)
//     gånger segment (burgare, kebab, pizza ...), plus "konton som liknar @förebild".
//  2. @-omnämnanden i förebildernas klipptexter (samarbeten, systerkonton).
// Prövning: yt-dlp-listning (storlek = medianvisningar för klipp 14–180 dagar, aktivitet = klipp senaste
// 90 dagarna) och Gemini på namn och klipptexter (verksamhet eller inte, land, kedja, innehållsstil).
// Resultat: data/profil/kandidater.json och karta/videoforandring/kandidater.md (en rad per konto;
// stryk raderna som inte passar, kör sedan profil/godkann.mjs).
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { listaProfil } from '../bank/forurval.mjs'
import { ytdlpMedPaus } from '../bank/profiler.mjs'
import { generera } from '../typer/gemini.mjs'
import { storlek, omnamnanden } from './sok.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const ANTAL = Number(varde('--antal', 100))
const GOLV = Number(varde('--golv', 2000))
const FOLJ = [Number(varde('--foljare-min', 700)), Number(varde('--foljare-max', 30000))]
const PROFIL = path.join(DATA, 'profil')
const UT = path.join(PROFIL, 'kandidater.json')
const LISTOR = path.join(PROFIL, 'sok-listor')
const MD = path.join(DATA, '..', 'karta', 'videoforandring', 'kandidater.md')
const las = (f, d = null) => { try { return JSON.parse(fs.readFileSync(f, 'utf8')) } catch { return d } }
const giltigt = h => /^[a-z0-9._]{2,24}$/.test(h) && /[a-z0-9_]/.test(h)
const logg = t => { console.log(t); fs.appendFileSync(path.join(PROFIL, 'kandidater-logg.txt'), `${new Date().toISOString()} ${t}\n`) }
const paus = ms => new Promise(r => setTimeout(r, ms))

async function iTakt(lista, n, f) {
  let k = 0
  await Promise.all(Array.from({ length: Math.min(n, lista.length) }, async () => { while (k < lista.length) { const j = k++; await f(lista[j], j) } }))
}

async function anropa(opt) {
  for (let n = 1; ; n++) {
    try { return await generera(opt) } catch (e) {
      if (n < 4 && /429|5\d\d|fetch failed|ECONNRESET/.test(e.message)) { await paus(15_000 * n); continue }
      throw e
    }
  }
}

const LAND = ['Sverige', 'Danmark', 'Tyskland', 'Storbritannien']
const SEGMENT = [
  'smashburgare och hamburgerrestauranger', 'kebab, döner och shawarma', 'pizzerior och italienska restauranger',
  'fried chicken och kycklingrestauranger', 'asiatiska restauranger, sushi och ramen', 'kaféer, bagerier och brunch',
  'barer, pubar och nattklubbar', 'restaurangkedjor och franchises', 'street food och matvagnar', 'grill, steakhouse och BBQ',
]
const STIL = 'Kontona ska drivas av verksamheten själv och vara starka på TikTok: sketcher, trender, personalen framför kameran, humor och relaterbara situationer, inte bara matbilder. Hög och jämn räckvidd.'

async function googla(fraga) {
  const r = await anropa({ modell: process.env.SOK_MODELL ?? 'gemini-3.8-flash', sok: true, temperatur: 0.4, parts: [{ text: `${fraga}\n${STIL}\nSök på webben och lista upp till 20 sådana TikTok-konton. Skriv ett konto per rad som "@handtag — namn — stad". Använd bara handtag du har sett i källorna; gissa inte.` }] })
  return { ore: r.ore, handtag: [...new Set([...r.text.toLowerCase().matchAll(/@([a-z0-9._]{2,24})/g)].map(m => m[1].replace(/\.+$/, '')).filter(giltigt))] }
}

const BEDOM = {
  type: 'object',
  properties: {
    verksamhet: { type: 'boolean', description: 'Kontot tillhör en restaurang, ett kafé, en bar, en matvagn eller en matkedja (inte en matkreatör, influencer, recensent, leverantör, varumärke i dagligvaruhandeln eller media).' },
    land: { type: 'string', description: 'Troligt land.' },
    stad: { type: 'string', description: 'Trolig stad, eller tom.' },
    segment: { type: 'string', description: 'Kort: t.ex. burgare, kebab, pizza, kafé, bar.' },
    kedja: { type: 'boolean', description: 'Flera enheter eller franchise.' },
    stil: { type: 'integer', minimum: 1, maximum: 5, description: 'Hur väl klipptexterna tyder på personer, sketcher, humor och trender (5) i stället för rena erbjudanden och matbilder (1).' },
    skal: { type: 'string', description: 'En kort mening om kontot och dess innehåll.' },
  },
  required: ['verksamhet', 'land', 'stad', 'segment', 'kedja', 'stil', 'skal'],
}

async function bedom(h, lista) {
  const texter = lista.slice(0, 20).map(k => `- ${(k.text ?? '').slice(0, 180).replace(/\s+/g, ' ')}`).join('\n')
  const r = await anropa({ modell: 'gemini-3.5-flash-lite', schema: BEDOM, temperatur: 0, parts: [{ text: `TikTok-konto @${h}. Senaste klipptexterna:\n${texter}\n\nBedöm kontot.` }] })
  return { ...r.data, ore: r.ore }
}

// Följarantalet står i profilsidans inbäddade data (avrundat, t.ex. 12300).
// Läses ur "stats" (kontots egna siffror) och secUid, som yt-dlp behöver när handtaget inte räcker
// ("Unable to extract secondary user ID"). Två försök; sidan laddar ibland utan data.
async function profilInfo(h) {
  for (let n = 1; n <= 3; n++) {
    try {
      const res = await fetch(`https://www.tiktok.com/@${h}`, { headers: { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36' } })
      const t = await res.text()
      const stats = t.match(/"stats":\{"followerCount":(\d+)[^}]*"videoCount":(\d+)/)
      const sec = t.match(/"secUid":"(MS4wLjABAAAA[\w-]+)"/)
      const bio = t.match(/"signature":"((?:[^"\\]|\\.)*)"/)?.[1]
      const text = bio ? JSON.parse(`"${bio}"`).replace(/\s+/g, ' ').trim() : ''
      if (stats) return { foljare: Number(stats[1]), videor: Number(stats[2]), secUid: sec?.[1] ?? null, bio: text }
    } catch { /* nytt försök */ }
    await paus(3000 * n)
  }
  return null
}
// Ägarens regel: recensenter, livsstilskonton och officiella stads-/turismkonton hör inte till urvalet.
// Avgörs av handtaget och bion; verksamhetssignaler (adress, öppettider, meny, beställning) visas i listan.
const STAD = 'malmo|malmö|gbg|goteborg|göteborg|gothenburg|sthlm|stockholm|orebro|örebro|uppsala|lund|london|berlin|hamburg|munich|cph|kbh|copenhagen|aarhus|manchester|glasgow'
const EJ_NAMN = new RegExp(`foodie|eats|munchies|guide|tips|blogg|blog|review|recens|livet|lifestyle|town|staden|stories|onthemove|travel|resor|(^|[._])(${STAD})[._]?(food|dine|mat)|(food|mat)[._]?(${STAD})`)
const EJ_BIO = /mattips|matblogg|recension|food ?(tips|guide|review|blogger|lover)|foodie|official tourism|tourism|turism|visit ?[a-zåäö]+|content creator|creator|influencer|ugc|samarbete|collab|reviews/i
const AFFAR_BIO = /öppet|öppettider|open (daily|every|mon|tue)|opening|tel[:. ]|\+\d{2} ?\d|📞|☎|meny|menu|beställ|order|boka|book (a|your|now)|välkomna|welcome to|takeaway|take away|leverans|delivery|wolt|foodora|uber ?eats|just ?eat|deliveroo|lieferando|adress|address|📍/i
const ejUrval = (h, bio = '') => EJ_NAMN.test(h) || EJ_BIO.test(bio)
const listaVia =(h, secUid) => listaProfil(h, { bank: LISTOR, anropa: (a, o) => ytdlpMedPaus(secUid ? a.map(x => x === `https://www.tiktok.com/@${h}` ? `tiktokuser:${secUid}` : x) : a, o) })

// Förebilder och redan kända konton.
const forebilder = [...new Set(fs.readFileSync(path.join(PROFIL, 'forebilder.txt'), 'utf8').split(/\r?\n/)
  .filter(l => l.trim() && !l.trim().startsWith('#')).map(l => l.match(/@([a-z0-9._]+)/i)?.[1]?.toLowerCase()).filter(Boolean))]
const bank = new Set(fs.readdirSync(path.join(DATA, 'bank')).filter(k => fs.existsSync(path.join(DATA, 'bank', k, 'lista.json'))))
const tidigare = las(UT, { kandidater: [] })
// Fel och rader från före följarkontrollen (foljare saknas) prövas igen.
const provade = new Map(tidigare.kandidater.filter(k => !k.skal?.startsWith('fel') && k.foljare != null).map(k => [k.handtag, k]))
const kanda = new Set([...forebilder, ...bank])
let ore = 0

// Löpande: varje ny kandidat prövas direkt, och listan skrivs om efter varje godkänd,
// så att ägaren kan börja titta innan sökningen är klar.
const kallor = new Map()
const spara = () => fs.writeFileSync(UT, JSON.stringify({ uppdaterad: new Date().toISOString(), golv: GOLV, kandidater: [...provade.values()] }, null, 1) + '\n')
const tal = n => n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k` : String(n)
let fas = 'söker'

function skrivLista() {
  // Verksamheter som klarar storlek och aktivitet, sorterade på stil och sedan räckvidd,
  // med högst 40 % från ett och samma land så att bredden finns kvar.
  // Ägarens beslut (data/profil/beslut.json): strukna visas inte, behållna står först under egen rubrik.
  const beslut = las(path.join(PROFIL, 'beslut.json'), { behall: {}, stryk: [] })
  const stryk = new Set(beslut.stryk)
  const ok = [...provade.values()].filter(k => k.skal === 'ok' && !stryk.has(k.handtag) && !beslut.behall[k.handtag])
    .sort((a, b) => (b.bedomning.stil - a.bedomning.stil) || (b.storlek.median - a.storlek.median))
  const perLand = {}
  const valda = []
  for (const k of ok) {
    const l = k.bedomning.land
    if (ok.length > ANTAL && (perLand[l] ?? 0) >= ANTAL * 0.4) continue
    perLand[l] = (perLand[l] ?? 0) + 1
    valda.push(k)
    if (valda.length >= ANTAL) break
  }
  // Verksamhetssignal i bion först, sedan räckvidd.
  const affar = k => (AFFAR_BIO.test(k.bio ?? '') ? 1 : 0)
  const obedomda = [...provade.values()].filter(k => k.skal === 'obedömd' && !stryk.has(k.handtag) && !beslut.behall[k.handtag] && !ejUrval(k.handtag, k.bio ?? ''))
    .sort((a, b) => (affar(b) - affar(a)) || (b.storlek.median - a.storlek.median))
    .map(k => `- [@${k.handtag}](https://www.tiktok.com/@${k.handtag}) · ${tal(k.foljare)} följare, median ${tal(k.storlek.median)}, ${k.storlek.aktiva} klipp/90 d${affar(k) ? ' · **verksamhet i bion**' : ''} · ${k.bio ? `”${k.bio.slice(0, 90)}”` : 'ingen bio'}`)
  const behallna = Object.entries(beslut.behall).map(([h, varfor]) => `- [@${h}](https://www.tiktok.com/@${h}) · ${varfor}`)
  const rader = valda.map(k => {
    const b = k.bedomning
    return `- [@${k.handtag}](https://www.tiktok.com/@${k.handtag}) · ${b.land}${b.stad ? `, ${b.stad}` : ''} · ${b.segment}${b.kedja ? ', kedja' : ''} · ${k.foljare != null ? `${tal(k.foljare)} följare, ` : ''}median ${tal(k.storlek.median)}, ${k.storlek.aktiva} klipp/90 d · stil ${b.stil} · ${b.skal}`
  })
  fs.writeFileSync(MD, `# Kandidater till banken (${new Date().toISOString().slice(0, 10)})

**Läge: ${fas}.** ${valda.length} konton av ${ok.length} som klarat prövningen (${provade.size} prövade, ${kallor.size} hittade). Säg vilka som ska behållas eller strykas, så förs det in i \`data/profil/beslut.json\` (filen skrivs om löpande, så strykningar direkt här försvinner).

## Behållna (${behallna.length})

${behallna.join('\n')}

## Att titta på

Prövningen: ${FOLJ[0]}–${FOLJ[1]} följare (förebilderna har mest 1 000–12 000), medianvisningar minst ${GOLV} för klipp 14–180 dagar gamla, minst 4 klipp de senaste 90 dagarna, och Geminis bedömning av klipptexterna att det är en verksamhet. *Stil* (1–5) är Geminis gissning från texterna om hur mycket personer, sketcher och humor bär innehållet. Sorterad på stil och sedan räckvidd.

${rader.join('\n')}

## Obedömda (${obedomda.length})

Klarade följare, storlek och aktivitet men har inte bedömts av Gemini (krediten slut). Kan vara privatpersoner eller recensenter. Sorterade på medianvisningar; sökfrågan som hittade kontot står sist.

${obedomda.join('\n')}
`)
  return { valda: valda.length, perLand }
}

async function prova(h) {
  const rad = { handtag: h, kallor: [...kallor.get(h)] }
  try {
    const info = await profilInfo(h)
    rad.foljare = info?.foljare ?? null
    rad.bio = info?.bio ?? null
    if (!info) rad.skal = 'fel: profilsidan gav ingen data'
    else if (ejUrval(h, info.bio)) rad.skal = 'recensent, livsstil eller officiellt (namn/bio)'
    else if (!info.videor) rad.skal = 'inga klipp'
    else if (rad.foljare < FOLJ[0] || rad.foljare > FOLJ[1]) rad.skal = rad.foljare < FOLJ[0] ? 'för få följare' : 'för många följare'
    else {
      const lista = await listaVia(h, info.secUid)
      rad.storlek = storlek(lista)
      if (!lista.length) rad.skal = 'inga klipp'
      else if (rad.storlek.median < GOLV) rad.skal = 'för liten'
      else if (rad.storlek.aktiva < 4) rad.skal = 'inte aktiv'
      else {
        // Utan Gemini-kredit (402) eller med --utan-bedomning: kontot listas obedömt, ägaren tittar ändå.
        try {
          if (args.includes('--utan-bedomning')) throw new Error('utan bedömning')
          rad.bedomning = await bedom(h, lista)
          ore += rad.bedomning.ore ?? 0
          rad.skal = rad.bedomning.verksamhet ? 'ok' : 'inte en verksamhet'
        } catch (e) {
          if (!/402|utan bedömning/.test(e.message)) throw e
          rad.skal = 'obedömd'
        }
      }
    }
  } catch (e) { rad.skal = `fel: ${e.message.slice(0, 120)}` }
  provade.set(h, rad)
  logg(`@${h}: ${rad.skal}${rad.foljare != null ? ` (${rad.foljare} följare)` : ''}`)
  spara()
  if (rad.skal === 'ok' || rad.skal === 'obedömd') skrivLista()
}

// Prövningskö med 4 samtidiga.
const ko = []
let aktiva = 0
const vantare = []
async function kor() {
  // 10 samtidiga: profilsidan (0,5 s) sållar bort de flesta; yt-dlp-listningarna köas ändå med 1 s mellanrum.
  while (ko.length && aktiva < 10) {
    const h = ko.shift()
    aktiva++
    prova(h).finally(() => { aktiva--; kor(); if (!aktiva && !ko.length) vantare.splice(0).forEach(r => r()) })
  }
}
const laggTill = (h, kalla) => {
  if (kanda.has(h)) return
  const s = kallor.get(h)
  if (s) { s.add(kalla); return }
  kallor.set(h, new Set([kalla]))
  if (provade.has(h) && !provade.get(h).skal?.startsWith('fel')) return
  ko.push(h)
  kor()
}

// --fran brave: handtagen från profil/brave.mjs i stället för omnämnanden och Gemini-sökning.
const FRAN = varde('--fran')
// Redan prövade konton utan bio (från före bio-filtret) får sin bio nu, så att listan kan filtreras.
const utanBio = [...provade.values()].filter(k => (k.skal === 'obedömd' || k.skal === 'ok') && k.bio === undefined)
if (utanBio.length) {
  logg(`hämtar bio för ${utanBio.length} prövade konton`)
  await iTakt(utanBio, 10, async k => { const i = await profilInfo(k.handtag); k.bio = i?.bio ?? null; if (ejUrval(k.handtag, k.bio ?? '')) k.skal = 'recensent, livsstil eller officiellt (namn/bio)' })
  spara()
  skrivLista()
}
if (FRAN === 'brave') {
  const fynd = las(path.join(PROFIL, 'brave-fynd.json'), { handtag: {} }).handtag
  for (const [h, f] of Object.entries(fynd)) laggTill(h, `brave: ${f.fragor[0]}`)
  logg(`brave: ${Object.keys(fynd).length} handtag, ${ko.length + aktiva} att pröva`)
  let senast = 0
  while (aktiva || ko.length) { await paus(15_000); const n = provade.size; if (n - senast >= 50) { senast = n; logg(`prövat ${n}, ${[...provade.values()].filter(k => k.skal === 'ok').length} ok, ${ko.length} kvar`) } }
}

// 1. Omnämnanden (snabbt, utan Gemini).
for (const f of FRAN ? [] : forebilder) {
  try {
    const lista = await listaProfil(f, { bank: fs.existsSync(path.join(DATA, 'bank', f, 'lista.json')) ? path.join(DATA, 'bank') : LISTOR })
    for (const [h, n] of omnamnanden(lista, kanda)) if (n >= 2 || /burger|kebab|pizz|sushi|cafe|kafe|coffee|bar|krog|restaurang|grill|food|chicken|bistro|kitchen/.test(h)) laggTill(h, `omnämnd av @${f}`)
  } catch (e) { logg(`@${f}: listningen föll: ${e.message.slice(0, 120)}`) }
}
logg(`omnämnanden: ${kallor.size} kandidater`)

// 2. Google via Gemini.
const fragor = FRAN ? [] : [
  ...forebilder.map(f => ({ fraga: `TikTok-konton för matverksamheter i Sverige, Danmark, Tyskland eller Storbritannien som liknar @${f} i koncept, tempo och produktionsvärde.`, kalla: `google: liknar @${f}` })),
  ...LAND.flatMap(l => SEGMENT.map(s => ({ fraga: `TikTok-konton för ${s} i ${l}.`, kalla: `google: ${s.split(/[ ,]/)[0]}, ${l}` }))),
]
logg(`${forebilder.length} förebilder, ${fragor.length} sökfrågor`)
let klara = 0
await iTakt(fragor, 8, async ({ fraga, kalla }) => {
  try { const r = await googla(fraga); ore += r.ore ?? 0; for (const h of r.handtag) laggTill(h, kalla) } catch (e) { logg(`sökningen föll (${kalla}): ${e.message.slice(0, 120)}`) }
  if (++klara % 5 === 0) logg(`sökning ${klara}/${fragor.length}: ${kallor.size} hittade, ${[...provade.values()].filter(k => k.skal === 'ok').length} ok, ${(ore / 100).toFixed(2)} kr`)
})
if (aktiva || ko.length) await new Promise(r => vantare.push(r))
fas = 'klar'
const { valda, perLand } = skrivLista()
spara()
logg(`klart: ${valda} på listan (${Object.entries(perLand).map(([l, n]) => `${l} ${n}`).join(', ')}), ${(ore / 100).toFixed(2)} kr. ${MD}`)
