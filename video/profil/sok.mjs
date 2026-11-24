// Sök profiler i samma skikt som ett par förebilder: verksamheter som satsar på TikTok-content.
//
//   node profil/sok.mjs bramsburgers kebabdudes [--max 30] [--djup 2]
//
// Kandidater kommer från två håll:
//  1. @-omnämnanden i förebildernas (och sedan de godkändas) klipptexter: samarbeten, systerkonton.
//  2. Gemini med Google-sökning: liknande svenska/nordiska matverksamheter som syns på TikTok.
// Varje kandidat listas med yt-dlp och prövas mot tre krav:
//  - storlek: medianvisningar (klipp 14–180 dagar) minst --andel av den minsta förebildens
//  - aktivitet: minst 4 klipp senaste 90 dagarna
//  - verksamhet: Gemini läser namnet och klipptexterna: restaurang, kafé, bar eller matkedja, inte en kreatör
// Resultat: data/profil/sok.json. Godkända konton plockas upp av profil/natt.mjs.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { listaProfil } from '../bank/forurval.mjs'
import { generera } from '../typer/gemini.mjs'

const DYGN = 86_400_000
const MODELL = 'gemini-3.5-flash-lite'
const SOKMODELL = process.env.SOK_MODELL ?? 'gemini-3.8-flash'
const UT = path.join(DATA, 'profil', 'sok.json')
const KANDIDATLISTOR = path.join(DATA, 'profil', 'sok-listor')
const giltigt = h => /^[a-z0-9._]{2,24}$/.test(h) && /[a-z0-9_]/.test(h)

export function storlek(lista, nu = Date.now()) {
  const alder = k => (nu - new Date(k.datum).getTime()) / DYGN
  const mogna = lista.filter(k => Number.isFinite(k.visningar) && k.datum && alder(k) >= 14 && alder(k) <= 180).map(k => k.visningar).sort((a, b) => a - b)
  return {
    median: mogna.length ? mogna[mogna.length >> 1] : 0,
    aktiva: lista.filter(k => k.datum && alder(k) <= 90).length,
    klipp: lista.length,
  }
}

export function omnamnanden(lista, utom = new Set()) {
  const ut = new Map()
  for (const k of lista) {
    for (const m of (k.text ?? '').toLowerCase().matchAll(/@([a-z0-9._]{2,24})/g)) {
      const h = m[1].replace(/\.+$/, '')
      if (giltigt(h) && !utom.has(h)) ut.set(h, (ut.get(h) ?? 0) + 1)
    }
  }
  return ut
}

async function sokMedGoogle(forebilder) {
  const beskr = forebilder.map(f => `@${f.handtag} (medianvisningar ${f.storlek.median}, ${f.storlek.aktiva} klipp senaste 90 dagarna)`).join(', ')
  const r = await generera({
    modell: SOKMODELL,
    sok: true,
    temperatur: 0.4,
    parts: [{ text: `Jag letar efter TikTok-konton för matverksamheter (restauranger, snabbmat, kaféer, barer, matkedjor och franchises) i Sverige, i andra hand Norden, som satsar lika mycket på TikTok som ${beskr}. De ska ha genomarbetade koncept, bra tempo och produktionsvärde, en blandning av underhållning och marknadsföring, och gärna vara nytänkande. Sök på webben och lista 40 sådana konton. Skriv ett konto per rad som "@handtag — namn — varför". Använd bara handtag du har sett i källorna; gissa inte.` }],
  })
  return [...new Set([...r.text.toLowerCase().matchAll(/@([a-z0-9._]{2,24})/g)].map(m => m[1].replace(/\.+$/, '')).filter(giltigt))]
}

const VERKSAMHET = {
  type: 'object',
  properties: {
    verksamhet: { type: 'boolean', description: 'Kontot tillhör en restaurang, ett kafé, en bar, en matvagn eller en matkedja (inte en matkreatör, influencer, leverantör eller media).' },
    land: { type: 'string', description: 'Troligt land, t.ex. Sverige.' },
    kedja: { type: 'boolean', description: 'Flera enheter eller franchise.' },
    skal: { type: 'string', description: 'Kort motivering.' },
  },
  required: ['verksamhet', 'land', 'kedja', 'skal'],
}

async function bedomVerksamhet(handtag, lista) {
  const texter = lista.slice(0, 15).map(k => `- ${(k.text ?? '').slice(0, 160).replace(/\s+/g, ' ')}`).join('\n')
  const r = await generera({ modell: MODELL, schema: VERKSAMHET, temperatur: 0, parts: [{ text: `TikTok-konto @${handtag}. Senaste klipptexterna:\n${texter}\n\nBedöm kontot.` }] })
  return { ...r.data, ore: r.ore }
}

if (process.argv[1] && import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const args = process.argv.slice(2)
  const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
  const MAX = Number(varde('--max', 30))
  const DJUP = Number(varde('--djup', 2))
  const ANDEL = Number(varde('--andel', 0.3))
  const seeds = args.filter((a, i) => !a.startsWith('--') && !args[i - 1]?.startsWith('--')).map(a => a.replace(/^.*@/, '').replace(/[/?].*$/, '').toLowerCase())
  if (!seeds.length) { console.error('Användning: node profil/sok.mjs <handtag> [...] [--max 30] [--djup 2] [--andel 0.3]'); process.exit(1) }

  const bank = new Set(fs.readdirSync(path.join(DATA, 'bank')).filter(k => fs.existsSync(path.join(DATA, 'bank', k, 'lista.json'))))
  const tidigare = fs.existsSync(UT) ? JSON.parse(fs.readFileSync(UT, 'utf8')) : { kandidater: [] }
  // Kandidater som föll på fel (kvot, nätverk) prövas igen.
  const provade = new Map(tidigare.kandidater.filter(k => !k.skal?.startsWith('fel')).map(k => [k.handtag, k]))
  const logg = t => { console.log(t); fs.appendFileSync(path.join(DATA, 'profil', 'sok-logg.txt'), `${new Date().toISOString()} ${t}\n`) }

  const forebilder = []
  for (const h of seeds) {
    const lista = await listaProfil(h)
    forebilder.push({ handtag: h, storlek: storlek(lista), lista })
    logg(`förebild @${h}: ${lista.length} klipp, median ${storlek(lista).median}, ${storlek(lista).aktiva} senaste 90 d`)
  }
  const golv = Math.min(...forebilder.map(f => f.storlek.median)) * ANDEL
  const kanda = new Set([...seeds, ...bank])

  let ko = []
  const laggTill = (h, kalla) => { if (!kanda.has(h) && !ko.some(k => k.h === h) && !provade.has(h)) ko.push({ h, kalla }) }
  // Google först: omnämnandena är mest privatpersoner (tävlingar), så de prövas sist.
  try {
    for (const h of await sokMedGoogle(forebilder)) laggTill(h, 'google')
  } catch (e) {
    // Utan Google-sökningen blir resultatet bara brusiga omnämnanden: spara inget, så görs sökningen om nästa gång.
    logg(`googlesökningen föll, sökningen görs om nästa körning: ${e.message.slice(0, 200).replace(/\n/g, ' ')}`)
    process.exit(2)
  }
  for (const f of forebilder) for (const [h, n] of omnamnanden(f.lista, kanda)) if (n >= 2 || /burger|kebab|pizza|sushi|cafe|kafe|bar|krog|restaurang|grill|food|mat/.test(h)) laggTill(h, `omnämnd av @${f.handtag}`)
  logg(`${ko.length} kandidater att pröva, golv ${Math.round(golv)} medianvisningar`)

  const godkanda = () => [...provade.values()].filter(k => k.godkand).length
  for (let varv = 1; varv <= DJUP && ko.length && godkanda() < MAX; varv++) {
    const nasta = []
    for (const { h, kalla } of ko) {
      if (godkanda() >= MAX) break
      const rad = { handtag: h, kalla, varv }
      try {
        // Kandidaternas listor hålls utanför banken; bara godkända kopieras in (se nedan).
        const lista = await listaProfil(h, { bank: KANDIDATLISTOR })
        rad.storlek = storlek(lista)
        if (rad.storlek.median < golv) rad.skal = 'för liten'
        else if (rad.storlek.aktiva < 4) rad.skal = 'inte aktiv'
        else {
          rad.bedomning = await bedomVerksamhet(h, lista)
          if (!rad.bedomning.verksamhet) rad.skal = 'inte en verksamhet'
          else {
            rad.godkand = true
            fs.mkdirSync(path.join(DATA, 'bank', h), { recursive: true })
            fs.copyFileSync(path.join(KANDIDATLISTOR, h, 'lista.json'), path.join(DATA, 'bank', h, 'lista.json'))
            for (const [m] of omnamnanden(lista, kanda)) if (!provade.has(m) && m !== h) nasta.push({ h: m, kalla: `omnämnd av @${h}` })
          }
        }
      } catch (e) { rad.skal = `fel: ${e.message.slice(0, 120)}` }
      provade.set(h, rad)
      kanda.add(h)
      logg(`@${h} (${kalla}): ${rad.godkand ? `godkänd, median ${rad.storlek.median}, ${rad.bedomning.land}${rad.bedomning.kedja ? ', kedja' : ''}` : rad.skal}`)
      fs.writeFileSync(UT, JSON.stringify({ uppdaterad: new Date().toISOString(), forebilder: forebilder.map(({ lista, ...f }) => f), golv, kandidater: [...provade.values()] }, null, 1) + '\n')
    }
    ko = nasta.filter((k, i, a) => a.findIndex(x => x.h === k.h) === i && !kanda.has(k.h))
  }
  logg(`sökningen klar: ${godkanda()} godkända konton`)
}
