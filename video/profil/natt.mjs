// Nattkörningen: fler profiler, slumpvisa klipp per konto, hämta → sålla → radera.
// Kan avbrytas och startas om när som helst; det som är klart hoppas över.
//
//   node profil/natt.mjs [--per-konto 50] [--sok-max 30] [--utan-sok]
//
// Faser:
//  1. sök: profil/sok.mjs med förebilderna i data/profil/forebilder.txt (en gång per dygn)
//  2. listor: alla konton (banken, förebilderna, sökningens godkända) får lista.json
//  3. stickprov: residualer per konto, upp till --per-konto slumpvisa behöriga klipp, varvat mellan konton
//  4. hämta och sålla: batchar med yt-dlp, flera parallellt (--hamta-par 6, --batch 12), upp till
//     --salla-par 10 sållningar samtidigt, med vakt mot spärr från TikTok. Klipp som hämtas här raderas efter
//     sållningen (disken är liten); metadata och sållning finns kvar.
//     Under 3 GB ledigt väntar hämtningen. Vid 429 väntar klippet 5 min och försöker igen (upp till ~3 h).
//  5. analys: profil/kor.mjs → data/profil/rapport.txt
// Läget skrivs till data/profil/natt-status.json och loggen till data/profil/natt-logg.txt.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFileSync, spawn, spawnSync } from 'node:child_process'
import { createRequire } from 'node:module'
import { DATA } from '../analys/pipeline.mjs'
import { listaProfil, hamtaValda } from '../bank/forurval.mjs'
import { YTDLP, UT } from '../bank/hamta.mjs'
import { sallaKlipp } from '../bank/sallning.mjs'
import { residualer } from './baslinje.mjs'
import { valjStickprov } from './stickprov.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PER = Number(varde('--per-konto', 50))
const SOK_MAX = Number(varde('--sok-max', 30))
const PROFIL = path.join(DATA, 'profil')
const BANK = path.join(DATA, 'bank')
const SALLNING = path.join(BANK, 'sallning')
const KALLOR = path.join(DATA, 'kallor.json')
const las = (f, d = null) => { try { return JSON.parse(fs.readFileSync(f, 'utf8')) } catch { return d } }
const paus = ms => new Promise(r => setTimeout(r, ms))
const ffmpeg = createRequire(import.meta.url)('ffmpeg-static')

const status = { startad: new Date().toISOString(), fas: 'start', konton: 0, stickprov: 0, kvar: 0, hamtade: 0, sallade: 0, fel: 0, ore: 0 }
function skrivStatus(andring = {}) {
  Object.assign(status, andring, { uppdaterad: new Date().toISOString(), pid: process.pid })
  fs.writeFileSync(path.join(PROFIL, 'natt-status.json'), JSON.stringify(status, null, 1) + '\n')
}
function logg(t) {
  const rad = `${new Date().toISOString()} ${t}`
  console.log(rad)
  fs.appendFileSync(path.join(PROFIL, 'natt-logg.txt'), rad + '\n')
}
const ledigtGB = () => { const s = fs.statfsSync(DATA); return (s.bavail * s.bsize) / 1e9 }

fs.mkdirSync(PROFIL, { recursive: true })
skrivStatus()
logg(`nattkörningen startar (pid ${process.pid}), ${ledigtGB().toFixed(1)} GB ledigt`)

// 1. Sök.
const forebilder = [...new Set(fs.readFileSync(path.join(PROFIL, 'forebilder.txt'), 'utf8').split(/\r?\n/)
  .filter(l => l.trim() && !l.trim().startsWith('#'))
  .map(l => l.match(/@([a-z0-9._]+)/i)?.[1]?.toLowerCase()).filter(Boolean))]
const sok = las(path.join(PROFIL, 'sok.json'))
const sokGammal = !sok || Date.now() - new Date(sok.uppdaterad).getTime() > 86_400_000
if (!args.includes('--utan-sok') && sokGammal) {
  skrivStatus({ fas: 'sök' })
  logg(`söker liknande profiler utifrån ${forebilder.length} förebilder`)
  spawnSync(process.execPath, [path.join(import.meta.dirname, 'sok.mjs'), ...forebilder, '--max', String(SOK_MAX), '--djup', '2'], { stdio: 'inherit' })
}
const godkanda = [
  ...(las(path.join(PROFIL, 'sok.json'))?.kandidater ?? []).filter(k => k.godkand).map(k => k.handtag),
  // Konton som ägaren har behållit i kandidatlistan (profil/kandidater.mjs → profil/godkann.mjs).
  ...(fs.existsSync(path.join(PROFIL, 'godkanda.txt')) ? fs.readFileSync(path.join(PROFIL, 'godkanda.txt'), 'utf8').split(/\r?\n/).filter(Boolean) : []),
]

// 2. Listor.
skrivStatus({ fas: 'listor' })
// Bankens konton: de ursprungliga profilerna (forurval.json) och konton som redan har klipp i kallor.json.
const ursprungliga = new Set((las(path.join(BANK, 'forurval.json'))?.profiler ?? []).map(p => p.handtag))
for (const k of Object.values(las(KALLOR, {}))) if (k.kalla === 'bank') ursprungliga.add(k.konto)
const banken = fs.readdirSync(BANK).filter(k => ursprungliga.has(k) && fs.existsSync(path.join(BANK, k, 'lista.json')))
const konton = [...new Set([...banken, ...forebilder, ...godkanda])].sort()
for (const k of konton) {
  if (fs.existsSync(path.join(BANK, k, 'lista.json'))) continue
  try { const l = await listaProfil(k); logg(`listade @${k}: ${l.length} klipp`) } catch (e) { logg(`@${k}: listningen föll: ${e.message.slice(0, 160)}`) }
}

// 3. Stickprov, varvat mellan konton så att ett avbrott ändå ger jämn täckning.
skrivStatus({ fas: 'stickprov' })
const perKonto = []
for (const k of konton) {
  const lista = las(path.join(BANK, k, 'lista.json'))
  if (!lista?.klipp?.length) continue
  const rader = residualer(lista.klipp, { idag: lista.hamtad }).map(r => ({ konto: k, ...r }))
  perKonto.push(valjStickprov(rader, k, PER).map(r => ({ handtag: k, id: r.id, url: `https://www.tiktok.com/@${k}/video/${r.id}`, rv: r.rv, valt: true })))
}
const stickprov = []
for (let i = 0; perKonto.some(l => i < l.length); i++) for (const l of perKonto) if (i < l.length) stickprov.push(l[i])
const tidigare = las(path.join(PROFIL, 'stickprov.json'))?.klipp ?? []
const allaSp = [...new Map([...tidigare, ...stickprov].map(k => [`${k.handtag}-${k.id}`, k])).values()]
fs.writeFileSync(path.join(PROFIL, 'stickprov.json'), JSON.stringify({ skapad: new Date().toISOString(), perKonto: PER, konton: perKonto.length, klipp: allaSp }, null, 1) + '\n')
const sallat = id => fs.existsSync(path.join(SALLNING, `${id}.json`))
const ko = stickprov.filter(k => !sallat(`${k.handtag}-${k.id}`))
skrivStatus({ konton: perKonto.length, stickprov: stickprov.length, kvar: ko.length })
logg(`${perKonto.length} konton, ${stickprov.length} klipp i stickprovet, ${ko.length} kvar att hämta och sålla`)

// 4. Hämta och sålla.
// Hämtningen: HAMTA_PAR yt-dlp-processer samtidigt, var och en med en batchfil på BATCH klipp
// (en processtart per batch, inga egna pauser). Uppmätt 3 nov: 8 parallella ≈ 0,5 s/klipp utan
// spärr från TikTok; taket är bandbredden. Vakten halverar takten och pausar 10 min om TikTok
// börjar svara 403/429/captcha, och ökar igen efter fem lugna batcher.
// Formatet: minsta 540p (HEVC ≈ 1,8 MB), som skickas oomkodat till Gemini (se bank/sallning.mjs).
skrivStatus({ fas: 'hämta och sålla' })
const typer = las(path.join(DATA, 'typer', 'typer.json')).typer
const HAMTA_PAR = Number(varde('--hamta-par', 6))
const BATCH = Number(varde('--batch', 12))
const SALLA_PAR = Number(varde('--salla-par', 10))
// --utan-salla: bara hämta (t.ex. när Gemini-krediten är slut). Filerna ligger kvar och sållas nästa körning.
const UTAN_SALLA = args.includes('--utan-salla')
const sallaEller = (id, ny) => { if (UTAN_SALLA) { status.kvar--; lage(); skrivStatus() } else salla(id, ny) }
const NED = path.join(os.tmpdir(), 'letrend-natt')
const FORMAT = "b[ext=mp4][height<=1024][vcodec~='^(h265|hevc|bytevc1)']/b[ext=mp4][height<=1024]/b[ext=mp4]/b"
const SPARR = /HTTP Error 403|HTTP Error 429|captcha|rate.?limit|too many requests|blocked/i
const forsok = new Map()
let aktiva = 0, vantande = 0, behandlade = 0, hamtaPar = HAMTA_PAR, lugna = 0

function lage() {
  behandlade++
  if (behandlade % 25 === 0) logg(`läge: ${behandlade}/${ko.length} behandlade, ${status.hamtade} hämtade, ${status.sallade} sållade, ${status.fel} fel, ${status.ore.toFixed(0)} öre, ${hamtaPar} hämtningar parallellt, ${ledigtGB().toFixed(1)} GB ledigt`)
}

function ytdlpBatch(urls, dir) {
  const lista = path.join(dir, 'lista.txt')
  fs.writeFileSync(lista, urls.join('\n'))
  const a = [...YTDLP, '--ffmpeg-location', ffmpeg, '-f', FORMAT, '--merge-output-format', 'mp4', '--write-info-json',
    '--no-write-comments', '--ignore-errors', '--no-progress', '--no-overwrites', '-o', path.join(dir, '%(id)s.%(ext)s'), '-a', lista]
  return new Promise(res => {
    const p = spawn('uvx', a, { windowsHide: true })
    let fel = ''
    const stopp = setTimeout(() => p.kill(), 15 * 60_000)
    p.stdout.on('data', () => {})
    p.stderr.on('data', d => { fel += d })
    p.on('close', () => { clearTimeout(stopp); res(fel.split('\n').filter(l => /ERROR/.test(l))) })
    p.on('error', e => { clearTimeout(stopp); res([`ERROR ${e.message}`]) })
  })
}

async function salla(id, nyHamtad) {
  vantande++
  while (aktiva >= SALLA_PAR) await paus(200)
  vantande--
  aktiva++
  try {
    for (;;) {
      const k = las(KALLOR, {})[id]
      try {
        const r = await sallaKlipp(id, k, typer)
        status.sallade++
        status.ore += r.ore ?? 0
        if (nyHamtad) {
          fs.rmSync(k.fil, { force: true })
          const kallor = las(KALLOR, {})
          kallor[id] = { ...kallor[id], raderad: true }
          fs.writeFileSync(KALLOR, JSON.stringify(kallor, null, 2))
        }
        break
      } catch (e) {
        const n = (forsok.get(id) ?? 0) + 1
        forsok.set(id, n)
        // Kvoten kan vara borta i timmar (fakturering som inte slagit igenom): vänta upp till ~3 h per klipp.
        if (/ 429 /.test(e.message) && n < 36) { if (n === 1 || n % 6 === 0) logg(`${id}: kvot (429), väntar 5 min (försök ${n})`); await paus(300_000); continue }
        if (/ 5\d\d |fetch failed|ECONNRESET|ETIMEDOUT/.test(e.message) && n < 5) { await paus(30_000 * n); continue }
        status.fel++
        logg(`${id}: sållningen föll: ${e.message.slice(0, 160).replace(/\n/g, ' ')}`)
        break
      }
    }
  } finally {
    aktiva--
    status.kvar--
    lage()
    skrivStatus()
  }
}

async function hamtaBatch(batch, nr) {
  const kallor = las(KALLOR, {})
  const behov = []
  for (const k of batch) {
    const id = `${k.handtag}-${k.id}`
    if (kallor[id] && !kallor[id].raderad && fs.existsSync(kallor[id].fil)) sallaEller(id, false)
    else behov.push(k)
  }
  if (!behov.length) return
  const dir = path.join(NED, `b${nr}`)
  fs.rmSync(dir, { recursive: true, force: true })
  fs.mkdirSync(dir, { recursive: true })
  const fel = await ytdlpBatch(behov.map(k => k.url), dir)
  const sparr = fel.filter(l => SPARR.test(l))
  if (sparr.length >= Math.max(2, behov.length / 3)) {
    hamtaPar = Math.max(1, Math.floor(hamtaPar / 2))
    lugna = 0
    logg(`vakt: ${sparr.length} spärrfel i batch ${nr} (${sparr[0].slice(0, 120)}), ${hamtaPar} parallellt och 10 min paus`)
    await paus(600_000)
  } else if (++lugna >= 5 && hamtaPar < HAMTA_PAR) { hamtaPar++; lugna = 0 }
  for (const k of behov) {
    const id = `${k.handtag}-${k.id}`
    const mp4 = path.join(dir, `${k.id}.mp4`)
    if (!fs.existsSync(mp4)) { status.fel++; status.kvar--; logg(`${id}: hämtningen föll (bildpost eller borttaget)`); lage(); continue }
    const utDir = path.join(UT, k.handtag)
    fs.mkdirSync(utDir, { recursive: true })
    for (const f of [`${k.id}.mp4`, `${k.id}.info.json`]) if (fs.existsSync(path.join(dir, f))) fs.renameSync(path.join(dir, f), path.join(utDir, f))
    const kl = las(KALLOR, {})
    if (kl[id]?.raderad) { const { raderad, ...rest } = kl[id]; kl[id] = rest; fs.writeFileSync(KALLOR, JSON.stringify(kl, null, 2)) }
    // Registreringen i kallor.json görs av hamtaValda; filen finns redan, så den laddar inget.
    const r = await hamtaValda([k], { anropa: async () => {}, skriv: () => {} })
    if (!r.nya && !r.befintliga) { status.fel++; status.kvar--; logg(`${id}: registreringen föll`); lage(); continue }
    status.hamtade++
    sallaEller(id, true)
  }
  fs.rmSync(dir, { recursive: true, force: true })
  skrivStatus()
}

const batcher = []
for (let i = 0; i < ko.length; i += BATCH) batcher.push(ko.slice(i, i + BATCH))
let nasta = 0
await Promise.all(Array.from({ length: HAMTA_PAR }, async (_, plats) => {
  while (nasta < batcher.length) {
    if (plats >= hamtaPar) { await paus(5000); continue }
    while (ledigtGB() < 3) { skrivStatus({ fas: 'väntar på disk' }); await paus(60_000) }
    while (vantande > 40) await paus(1000)
    const nr = nasta++
    await hamtaBatch(batcher[nr], nr)
  }
}))
while (aktiva > 0 || vantande > 0) await paus(1000)

// 5. Analys.
skrivStatus({ fas: 'analys' })
const rapport = execFileSync(process.execPath, [path.join(import.meta.dirname, 'kor.mjs')], { encoding: 'utf8' })
fs.writeFileSync(path.join(PROFIL, 'rapport.txt'), rapport)
skrivStatus({ fas: 'klar' })
logg(`klart: ${status.hamtade} hämtade, ${status.sallade} sållade, ${status.fel} fel, ${status.ore.toFixed(0)} öre. Rapport i data/profil/rapport.txt`)
