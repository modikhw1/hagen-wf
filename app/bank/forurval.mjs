// Välj klipp utifrån profilens metadata före nedladdning.
// node bank/forurval.mjs [--per-profil 25] [--hamta]
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { DATA } from '../analys/pipeline.mjs'
import { lasJson, UT } from './hamta.mjs'
import { ytdlpMedPaus } from './profiler.mjs'

const DYGN = 86_400_000
const tidFor = datum => datum == null || datum === '' ? NaN : new Date(datum).getTime()
const harVisningar = k => Number.isFinite(k.visningar) && k.visningar > 0
const harGillanden = k => Number.isFinite(k.gillanden) && k.gillanden >= 0
const gruppFor = (k, i) => typeof k.text === 'string' && k.text.trim() ? k.text.trim().toLowerCase().slice(0, 25) : Symbol(i)

// Medelrang för lika värden. Saknade värden ger noll, ett ensamt känt värde ger ett.
function percentiler(varden) {
  const sorterade = varden.filter(Number.isFinite).sort((a, b) => a - b)
  const rang = new Map()
  let i = 0
  while (i < sorterade.length) {
    let slut = i + 1
    while (slut < sorterade.length && sorterade[slut] === sorterade[i]) slut++
    rang.set(sorterade[i], sorterade.length === 1 ? 1 : ((i + slut - 1) / 2) / (sorterade.length - 1))
    i = slut
  }
  return varden.map(v => rang.get(v) ?? 0)
}

export function forurvalProfil(klipp, { perProfil = 25, idag = new Date(), minLangd = 5, maxLangd = 90, maxAlderDagar = 900 } = {}) {
  if (!Number.isInteger(perProfil) || perProfil < 0) throw new Error('perProfil måste vara ett heltal från noll')
  if (!(idag instanceof Date) || !Number.isFinite(idag.getTime())) throw new Error('idag måste vara ett giltigt datum')
  if (![minLangd, maxLangd, maxAlderDagar].every(Number.isFinite) || minLangd < 0 || maxLangd < minLangd || maxAlderDagar < 0) {
    throw new Error('Längd- och åldersgränserna måste vara giltiga och icke-negativa')
  }
  const resultat = klipp.map(k => {
    const skal = []
    if (!Number.isFinite(k.langd)) skal.push('Längd saknas')
    else if (k.langd < minLangd) skal.push('För kort')
    else if (k.langd > maxLangd) skal.push('För långt')
    const tid = tidFor(k.datum)
    if (Number.isFinite(tid) && idag.getTime() - tid > maxAlderDagar * DYGN) skal.push('För gammalt')
    return { ...k, poang: 0, skal, valt: false }
  })
  // Endast klipp som klarat spärrarna påverkar de andra klippens rang inom profilen.
  const godkanda = resultat.filter(k => k.skal.length === 0)
  const nyhet = godkanda.filter(harVisningar).length < 5
  const visningar = percentiler(godkanda.map(k => harVisningar(k) ? k.visningar : NaN))
  const engagemang = percentiler(godkanda.map(k => harVisningar(k) && harGillanden(k) ? k.gillanden / k.visningar : NaN))
  const datum = percentiler(godkanda.map(k => tidFor(k.datum)))
  for (const [i, k] of godkanda.entries()) {
    k.poang = nyhet ? datum[i] : 0.6 * visningar[i] + 0.4 * engagemang[i]
    k.skal.push(nyhet ? 'Nyhet (färre än 5 klipp med visningar)' : 'Visningar och engagemang')
    if (!Number.isFinite(tidFor(k.datum))) k.skal.push('Datum saknas')
    if (!harVisningar(k)) k.skal.push('Visningar saknas')
    if (!nyhet && !harGillanden(k)) k.skal.push('Gillanden saknas')
  }
  const grupper = new Map(godkanda.map((k, i) => [k, gruppFor(k, i)]))
  const storlekar = new Map()
  for (const grupp of grupper.values()) storlekar.set(grupp, (storlekar.get(grupp) ?? 0) + 1)
  let mal = Math.min(perProfil, godkanda.length)
  // Räkna 40 % av det faktiska urvalet, även om en serie annars skulle ge underfyllnad.
  // För urval med ett eller två klipp behövs avrundning till minst ett per grupp.
  const takFor = n => Math.max(1, Math.floor(0.4 * n))
  while (mal > 0 && [...storlekar.values()].reduce((summa, n) => summa + Math.min(n, takFor(mal)), 0) < mal) mal--
  const grupptak = takFor(mal)
  const sorterade = [...godkanda].sort((a, b) => b.poang - a.poang || (tidFor(b.datum) || 0) - (tidFor(a.datum) || 0))
  const antal = new Map()
  let valda = 0
  for (const k of sorterade) {
    const grupp = grupper.get(k)
    const tagna = antal.get(grupp) ?? 0
    if (tagna >= grupptak) k.skal.push('Liknande text: mångfaldstak')
    else if (valda >= mal) k.skal.push('Utanför profiltaket')
    else {
      k.valt = true
      k.skal.push('Valt')
      antal.set(grupp, tagna + 1)
      valda++
    }
  }
  return resultat
}

export async function listaProfil(handtag, { bank = path.join(DATA, 'bank'), nu = new Date(), anropa = ytdlpMedPaus } = {}) {
  const fil = path.join(bank, handtag, 'lista.json')
  let sparad
  try { sparad = lasJson(fil) } catch { /* En trasig listcache ersätts genom ny listning. */ }
  const alder = nu.getTime() - tidFor(sparad?.hamtad)
  if (sparad?.konto === handtag && Array.isArray(sparad.klipp) && alder >= 0 && alder < DYGN) return sparad.klipp
  const json = await anropa(['--flat-playlist', '-J', '--playlist-end', '300', `https://www.tiktok.com/@${handtag}`])
  const pl = JSON.parse(json)
  if (!Array.isArray(pl.entries)) throw new Error('Listningen saknar klipplista')
  const sedda = new Set()
  const lista = pl.entries.filter(e => {
    if (!e?.id || sedda.has(String(e.id))) return false
    sedda.add(String(e.id))
    return true
  }).map(e => ({
    id: String(e.id),
    url: e.url ?? `https://www.tiktok.com/@${handtag}/video/${e.id}`,
    langd: e.duration,
    visningar: e.view_count,
    gillanden: e.like_count,
    kommentarer: e.comment_count,
    delningar: e.repost_count,
    datum: e.timestamp ? new Date(e.timestamp * 1000).toISOString().slice(0, 10) : null,
    text: e.title ?? e.description ?? '',
  }))
  fs.mkdirSync(path.dirname(fil), { recursive: true })
  fs.writeFileSync(fil, JSON.stringify({ konto: handtag, hamtad: nu.toISOString(), antal: lista.length, klipp: lista }, null, 1) + '\n')
  return lista
}

export async function hamtaValda(klipp, { data = DATA, ut = UT, anropa = ytdlpMedPaus, skriv = console.log } = {}) {
  const bank = path.join(data, 'bank')
  fs.mkdirSync(bank, { recursive: true })
  const logga = text => {
    fs.appendFileSync(path.join(bank, 'hamta-logg.txt'), `${new Date().toISOString()} ${text}\n`)
    skriv(text)
  }
  const sammanfattning = { nya: 0, befintliga: 0, fel: 0 }
  const sedda = new Set()
  logga(`Hämtningen startar: ${klipp.filter(k => k.valt).length} valda klipp`)
  for (const k of klipp.filter(k => k.valt)) {
    const konto = k.handtag
    const id = `${konto}-${k.id}`
    if (sedda.has(id)) continue
    sedda.add(id)
    try {
      if (!/^[a-z0-9._]+$/.test(konto) || !/[a-z0-9_]/.test(konto) || !/^[a-zA-Z0-9_-]+$/.test(k.id)) throw new Error('Ogiltigt konto eller video-id')
      const utDir = path.join(ut, konto)
      fs.mkdirSync(utDir, { recursive: true })
      const fil = path.join(utDir, `${k.id}.mp4`)
      const befintlig = fs.existsSync(fil)
      if (!befintlig) {
        // Samma flaggor som i hamta.mjs, genom dess exporterade yt-dlp-anrop.
        await anropa(['-f', 'bv*[height<=1280][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b', '--merge-output-format', 'mp4', '--write-info-json', '--no-write-comments', '--sleep-requests', '1', '--sleep-interval', '2', '--max-sleep-interval', '5', '-o', path.join(utDir, '%(id)s.%(ext)s'), k.url])
      }
      if (!fs.existsSync(fil)) throw new Error('Nedladdningen skapade ingen mp4-fil')
      // Samma registrering som i hamta.mjs. Läs om källorna för varje klipp.
      const kallorFil = path.join(data, 'kallor.json')
      const kallor = lasJson(kallorFil) ?? {}
      if (!kallor[id]) {
        const info = lasJson(path.join(utDir, `${k.id}.info.json`)) ?? {}
        kallor[id] = {
          fil: fil.replaceAll('\\', '/'),
          konto,
          kalla: 'bank',
          video: k.id,
          url: k.url,
          langd: info.duration ?? k.langd,
          visningar: info.view_count ?? k.visningar,
          gillanden: info.like_count ?? k.gillanden,
          kommentarer: info.comment_count ?? k.kommentarer,
          delningar: info.repost_count ?? k.delningar,
          datum: info.upload_date ? `${info.upload_date.slice(0, 4)}-${info.upload_date.slice(4, 6)}-${info.upload_date.slice(6, 8)}` : k.datum,
          text: info.description ?? k.text,
          ljud: info.track ?? info.artist ?? null,
        }
        fs.writeFileSync(kallorFil, JSON.stringify(kallor, null, 2))
      }
      sammanfattning[befintlig ? 'befintliga' : 'nya']++
      logga(`@${konto} ${k.id}: ${befintlig ? 'befintligt klipp, hoppades över' : 'hämtat och registrerat'}`)
    } catch (e) {
      sammanfattning.fel++
      logga(`@${konto} ${k.id}: fel: ${e.message.slice(0, 400)}`)
    }
  }
  logga(`Klart: ${sammanfattning.nya} nya, ${sammanfattning.befintliga} befintliga, ${sammanfattning.fel} fel`)
  return sammanfattning
}

async function main() {
  const args = process.argv.slice(2)
  let perProfil = 25
  let hamta = false
  while (args.length) {
    const arg = args.shift()
    if (arg === '--hamta') hamta = true
    else if (arg === '--per-profil' && /^\d+$/.test(args[0] ?? '')) perProfil = Number(args.shift())
    else throw new Error('Användning: node bank/forurval.mjs [--per-profil 25] [--hamta]')
  }
  if (!Number.isSafeInteger(perProfil)) throw new Error('Ogiltigt antal klipp per profil')
  const bank = path.join(DATA, 'bank')
  const profiler = lasJson(path.join(bank, 'profiler.json'))
  if (!Array.isArray(profiler)) throw new Error('Kör bank/profiler.mjs först så att profiler.json finns')
  const konton = [...new Set(profiler.filter(p => p.handtag && ['direkt', 'ascii', 'sokning'].includes(p.hur)).map(p => p.handtag))]
  const resultat = { profiler: [], klipp: [] }
  const metadata = []
  for (const handtag of konton) {
    try {
      if (!/^[a-z0-9._]+$/.test(handtag) || !/[a-z0-9_]/.test(handtag)) throw new Error('Ogiltigt handtag i profilcachen')
      const lista = await listaProfil(handtag)
      const urval = forurvalProfil(lista, { perProfil })
      const valda = urval.filter(k => k.valt).length
      resultat.profiler.push({ handtag, listade: lista.length, valda })
      for (const k of urval) {
        const url = k.url ?? `https://www.tiktok.com/@${handtag}/video/${k.id}`
        resultat.klipp.push({ handtag, id: k.id, url, poang: k.poang, skal: k.skal, valt: k.valt })
        if (k.valt) metadata.push({ ...k, handtag, url })
      }
      console.log(`@${handtag}: ${lista.length} listade, ${valda} valda`)
    } catch (e) {
      resultat.profiler.push({ handtag, listade: 0, valda: 0, fel: e.message })
      console.warn(`@${handtag}: listningen misslyckades: ${e.message.slice(0, 240)}`)
      process.exitCode = 1
    }
  }
  fs.mkdirSync(bank, { recursive: true })
  fs.writeFileSync(path.join(bank, 'forurval.json'), JSON.stringify(resultat, null, 2) + '\n')
  console.log(`Totalt: ${konton.length} profiler, ${resultat.klipp.length} listade klipp, ${metadata.length} valda`)
  const skal = new Map()
  for (const k of resultat.klipp) for (const s of k.skal) skal.set(s, (skal.get(s) ?? 0) + 1)
  for (const [s, antal] of skal) console.log(`  ${s}: ${antal}`)
  if (hamta) {
    const hamtade = await hamtaValda(metadata)
    if (hamtade.fel) process.exitCode = 1
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch(e => {
    console.error(`Fel: ${e.message}`)
    process.exitCode = 1
  })
}
