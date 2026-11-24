// Lös transkriberade profilnamn och verifiera att kontona har klipp.
// node bank/profiler.mjs <profilfil>
import fs from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import { pathToFileURL } from 'node:url'
import { DATA } from '../analys/pipeline.mjs'
import { PROJEKT, PLATS } from '../typer/gemini.mjs'
import { ytdlp, lasJson } from './hamta.mjs'

const giltigt = h => typeof h === 'string' && /^[a-z0-9._]+$/.test(h) && /[a-z0-9_]/.test(h)
const avkortat = h => /(?:\.{3,}|…)$/u.test(h)
const ascii = h => h.toLowerCase().replaceAll('ø', 'o').normalize('NFKD').replace(/\p{M}/gu, '').replace(/\s+/gu, '')
const paus = ms => new Promise(resolve => setTimeout(resolve, ms))

export function lasProfillista(text) {
  const profiler = []
  for (const original of text.split(/\r?\n/u)) {
    const rad = original.trim()
    if (!rad || rad.startsWith('#') || !rad.includes('@')) continue
    const efter = rad.slice(rad.indexOf('@') + 1).trim()
    const delar = efter.match(/^([^(/]+?)(?:\s*\/\s*(.*)|\s*\((.*)\))?$/u)
    if (!delar) continue
    const handtag = delar[1].trim()
    // Efter snedstreck kan en parentes vara en beskrivning, inte själva namnet.
    const namn = (delar[2]?.replace(/\s*\([^)]*\)\s*$/u, '') ?? delar[3] ?? '').trim() || null
    // Originalraden bevaras för spårbarhet och som nyckel i cachen.
    profiler.push({ rad, handtag, namn, avkortat: avkortat(handtag), ogiltigt: !giltigt(handtag) })
  }
  return profiler
}

export function kandidater(p) {
  if (p.avkortat || avkortat(p.handtag)) return []
  return [...new Set([p.handtag, ascii(p.handtag)].filter(giltigt))]
}

function rentHandtag(forslag) {
  if (typeof forslag !== 'string') return null
  const h = forslag.trim().replace(/^https?:\/\/(?:www\.)?tiktok\.com\/@/i, '').replace(/^@/, '').replace(/\/$/, '').toLowerCase()
  return giltigt(h) && !avkortat(h) ? h : null
}

export async function losHandtag(p, { prova, sok }) {
  const provade = []
  const forsok = async (h, hur) => {
    if (!h || provade.includes(h)) return null
    provade.push(h)
    try {
      const svar = await prova(h)
      if (svar?.ok && Number.isFinite(svar.antal) && svar.antal > 0) return { handtag: h, hur, provade }
    } catch {
      // Ett saknat konto eller nätfel får inte stoppa återstående kandidater.
    }
    return null
  }
  for (const h of kandidater(p)) {
    const svar = await forsok(h, h === p.handtag ? 'direkt' : 'ascii')
    if (svar) return svar
  }
  let forslag
  try {
    forslag = await sok(p)
  } catch {
    return { handtag: null, hur: 'misslyckad', provade }
  }
  const sokta = [...new Set((Array.isArray(forslag) ? forslag : []).map(rentHandtag).filter(Boolean))].slice(0, 3)
  for (const h of sokta) {
    const svar = await forsok(h, 'sokning')
    if (svar) return svar
  }
  return { handtag: null, hur: 'misslyckad', provade }
}

// Gemensam kö för anropsstarter: minst en sekund emellan, även med tre profiler.
let ko = Promise.resolve()
let nastaStart = 0
export async function ytdlpMedPaus(args, alternativ) {
  const tur = ko.then(async () => {
    await paus(Math.max(0, nastaStart - Date.now()))
    nastaStart = Date.now() + 1000
  })
  ko = tur.catch(() => {})
  await tur
  return ytdlp(args, alternativ)
}

async function provaProfil(handtag) {
  try {
    const json = await ytdlpMedPaus(['--flat-playlist', '-J', '--playlist-end', '1', `https://www.tiktok.com/@${handtag}`], { timeout: 120_000 })
    const antal = (JSON.parse(json).entries ?? []).filter(e => e?.id).length
    return { ok: antal > 0, antal }
  } catch (e) {
    console.warn(`  @${handtag}: verifieringen misslyckades: ${e.message.slice(0, 220)}`)
    return { ok: false, antal: 0 }
  }
}

let token = null
let tokenTid = 0
function hamtaToken() {
  if (token && Date.now() - tokenTid < 45 * 60_000) return token
  token = execSync('gcloud auth print-access-token', { encoding: 'utf8', windowsHide: true }).trim()
  tokenTid = Date.now()
  return token
}

// Hitta även JSON inuti kodstaket eller omgiven av förklaringar och källhänvisningar.
export function tolkaSokSvar(text) {
  const delar = [text.trim()]
  for (const [start, tecken] of text.split('').entries()) {
    if (tecken !== '[' && tecken !== '{') continue
    let djup = 0
    let strang = false
    let escape = false
    for (const [offset, c] of text.slice(start).split('').entries()) {
      if (strang) {
        if (escape) escape = false
        else if (c === '\\') escape = true
        else if (c === '"') strang = false
      } else if (c === '"') strang = true
      else if (c === '[' || c === '{') djup++
      else if (c === ']' || c === '}') djup--
      if (djup === 0) {
        delar.push(text.slice(start, start + offset + 1))
        break
      }
    }
  }
  for (const del of delar) {
    let data
    try { data = JSON.parse(del) } catch { continue }
    const lista = Array.isArray(data) ? data : data?.kandidater
    if (!Array.isArray(lista) || !lista.every(h => typeof h === 'string')) continue
    return [...new Set(lista.map(rentHandtag).filter(Boolean))].slice(0, 3)
  }
  throw new Error('Söksvaret saknar en läsbar JSON-lista med kandidater')
}

async function sokHandtag(p) {
  const vard = PLATS === 'global' ? 'aiplatform.googleapis.com' : `${PLATS}-aiplatform.googleapis.com`
  const url = `https://${vard}/v1/projects/${PROJEKT}/locations/${PLATS}/publishers/google/models/gemini-3-flash-preview:generateContent`
  const prompt = `Hitta det riktiga TikTok-handtaget för en restaurang, bar eller ett kafé.
Listan gäller främst svenska verksamheter, men enstaka nordiska eller andra konton kan förekomma.
Visningsnamn: ${JSON.stringify(p.namn)}
Felaktigt eller avkortat handtag från skärmbild: ${JSON.stringify(p.handtag)}
Använd Google-sökning och leta efter verksamhetens TikTok-profil och länkar från dess webbplats.
Välj kandidater som stämmer med både namn, ort och den synliga delen av handtaget.
Gissa inte bara utifrån stavningen. Om det är oklart, svara med en tom lista.
Svara som en enda rad JSON: {"kandidater":["handtag1","handtag2"]}.
Högst tre kandidater, utan @ eller URL. Handtag får bara innehålla a-z, 0-9, punkt och understreck.`
  const body = {
    contents: [{ role: 'user', parts: [{ text: prompt }] }],
    tools: [{ googleSearch: {} }],
    generationConfig: { temperature: 0.2 },
  }
  let forsok = 0
  let svarsforsok = 0
  while (true) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${hamtaToken()}`, 'Content-Type': 'application/json', 'x-goog-user-project': PROJEKT },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(180_000),
    })
    const text = await res.text()
    if (res.status === 401 && forsok === 0) {
      token = null
      forsok++
      continue
    }
    if ((res.status === 429 || res.status >= 500) && forsok < 4) {
      await paus(2000 * 2 ** forsok)
      forsok++
      continue
    }
    if (!res.ok) throw new Error(`Vertex ${res.status}: ${text.slice(0, 400)}`)
    const json = JSON.parse(text)
    const svar = (json.candidates?.[0]?.content?.parts ?? []).filter(del => !del.thought).map(del => del.text ?? '').join('')
    try {
      return tolkaSokSvar(svar)
    } catch (e) {
      if (svarsforsok++ === 0) {
        await paus(1000)
        continue
      }
      throw new Error(`${e.message} (${json.candidates?.[0]?.finishReason ?? 'okänd orsak'}): ${svar.slice(0, 240) || 'tomt svar'}`)
    }
  }
}

export async function losProfiler(profiler, {
  fil = path.join(DATA, 'bank', 'profiler.json'),
  prova = provaProfil,
  sok = sokHandtag,
  skriv = console.log,
} = {}) {
  let tidigare = []
  try { tidigare = lasJson(fil) ?? [] } catch { skriv('Profilcachen kunde inte läsas, profilerna provas igen') }
  const cache = new Map((Array.isArray(tidigare) ? tidigare : []).map(p => [p.rad, p]))
  const resultat = profiler.map(p => {
    const sparad = cache.get(p.rad)
    if (sparad && giltigt(sparad.handtag) && !avkortat(sparad.handtag) && sparad.antal > 0 && ['direkt', 'ascii', 'sokning'].includes(sparad.hur)) {
      return { rad: p.rad, handtag: sparad.handtag, namn: p.namn, hur: sparad.hur, antal: sparad.antal }
    }
    return { rad: p.rad, handtag: null, namn: p.namn, hur: 'misslyckad', antal: 0 }
  })
  fs.mkdirSync(path.dirname(fil), { recursive: true })
  const spara = () => fs.writeFileSync(fil, JSON.stringify(resultat, null, 2) + '\n')
  const prov = new Map()
  // Samma konto kan finnas på flera rader eller föreslås av flera sökningar.
  for (const p of resultat.filter(p => p.handtag)) prov.set(p.handtag, Promise.resolve({ ok: true, antal: p.antal }))
  let nasta = 0
  const arbetare = async () => {
    while (nasta < profiler.length) {
      const i = nasta++
      const p = profiler[i]
      if (resultat[i].handtag) {
        skriv(`@${p.handtag} → @${resultat[i].handtag} (${resultat[i].hur}, cache)`)
        continue
      }
      let antal = 0
      const lost = await losHandtag(p, {
        prova: async h => {
          if (!prov.has(h)) prov.set(h, Promise.resolve().then(() => prova(h)))
          const svar = await prov.get(h)
          if (svar?.ok) antal = svar.antal
          return svar
        },
        sok: async profil => {
          skriv(`@${profil.handtag}: söker efter rätt handtag`)
          try { return await sok(profil) } catch (e) {
            skriv(`  Sökningen misslyckades: ${e.message.slice(0, 400)}`)
            throw e
          }
        },
      })
      resultat[i] = { rad: p.rad, handtag: lost.handtag, namn: p.namn, hur: lost.hur, antal: lost.handtag ? antal : 0 }
      spara()
      skriv(`@${p.handtag} → ${lost.handtag ? `@${lost.handtag} (${lost.hur})` : 'misslyckad'}${lost.provade.length ? `, provade: ${lost.provade.join(', ')}` : ''}`)
    }
  }
  await Promise.all(Array.from({ length: Math.min(3, profiler.length) }, arbetare))
  spara()
  return resultat
}

async function main() {
  const args = process.argv.slice(2)
  if (args.length !== 1) throw new Error('Användning: node bank/profiler.mjs <profilfil>')
  const profiler = lasProfillista(fs.readFileSync(args[0], 'utf8'))
  if (!profiler.length) throw new Error('Inga profiler hittades i filen')
  console.log(`${profiler.length} profiler, högst tre samtidigt`)
  const resultat = await losProfiler(profiler)
  const antal = hur => resultat.filter(p => p.hur === hur).length
  console.log(`Lösta: ${resultat.filter(p => p.handtag).length}/${resultat.length}. Direkt: ${antal('direkt')}, ASCII: ${antal('ascii')}, sökning: ${antal('sokning')}, misslyckade: ${antal('misslyckad')}.`)
  console.log(`Sparat i ${path.join(DATA, 'bank', 'profiler.json')}`)
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch(e => {
    console.error(`Fel: ${e.message}`)
    process.exitCode = 1
  })
}
