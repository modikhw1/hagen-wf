// Masshämtning av klipp från profiler, för träningsdata.
//
//   node bank/hamta.mjs <fil med profiler | @konto | url> [...] [--max 60] [--ut <katalog>] [--bara-lista]
//
// Profilfilen: en profil per rad (https://www.tiktok.com/@konto, @konto eller konto), # för kommentar.
// Per profil: listan (yt-dlp --flat-playlist) sparas i data/bank/<konto>/lista.json, sedan laddas
// klippen ner (högst --max per profil, nyast först) till <ut>/<konto>/<videoid>.mp4 med
// metadata (<videoid>.info.json: visningar, gillanden, kommentarer, datum, text, ljud). Varje klipp
// registreras i data/kallor.json som <konto>-<videoid>, så att analysen (npm run analysera) och
// urvalet (bank/urval.mjs) hittar det. Klipp som redan finns hoppas över, så körningen kan avbrytas
// och startas om.
//
// yt-dlp körs med uvx (ingen installation; samma version varje gång tills den byts här).
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFile } from 'node:child_process'
import { DATA } from '../analys/pipeline.mjs'

export const YTDLP = ['--from', 'yt-dlp[default,curl-cffi]==2026.10.26', 'yt-dlp']
const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const MAX = Number(varde('--max', 60))
const UT = varde('--ut', path.join(os.homedir(), 'Downloads', 'letrend-bank'))
const baraLista = args.includes('--bara-lista')

function ytdlp(a, { timeout = 600_000 } = {}) {
  return new Promise((res, rej) => execFile('uvx', [...YTDLP, ...a], { maxBuffer: 256 * 1024 * 1024, timeout, windowsHide: true }, (err, stdout, stderr) => {
    if (err) rej(new Error((stderr || err.message).toString().split('\n').filter(l => /ERROR/.test(l)).slice(-2).join(' ') || err.message))
    else res(stdout.toString())
  }))
}

export function profiler(lista) {
  const ut = []
  for (const a of lista) {
    const rader = fs.existsSync(a) && fs.statSync(a).isFile() ? fs.readFileSync(a, 'utf8').split(/\r?\n/) : [a]
    for (let r of rader) {
      r = r.replace(/#.*/, '').trim()
      if (!r) continue
      const m = r.match(/@([\w.\-]+)/) ?? r.match(/^([\w.\-]+)$/)
      if (m) ut.push(m[1])
    }
  }
  return [...new Set(ut)]
}

const lasJson = f => (fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null)

export { ytdlp, lasJson, UT }

async function hamtaProfil(konto) {
  const dir = path.join(DATA, 'bank', konto)
  fs.mkdirSync(dir, { recursive: true })
  // 1. listan
  const json = await ytdlp(['--flat-playlist', '-J', '--playlist-end', String(Math.max(MAX, 200)), `https://www.tiktok.com/@${konto}`])
  const pl = JSON.parse(json)
  const lista = (pl.entries ?? []).map(e => ({ id: e.id, url: e.url ?? `https://www.tiktok.com/@${konto}/video/${e.id}`, langd: e.duration, visningar: e.view_count, gillanden: e.like_count, kommentarer: e.comment_count, delningar: e.repost_count, datum: e.timestamp ? new Date(e.timestamp * 1000).toISOString().slice(0, 10) : null, text: e.title ?? e.description ?? '' }))
  fs.writeFileSync(path.join(dir, 'lista.json'), JSON.stringify({ konto, hamtad: new Date().toISOString(), antal: lista.length, klipp: lista }, null, 1))
  console.log(`@${konto}: ${lista.length} klipp i listan`)
  if (baraLista) return { konto, lista: lista.length, nya: 0 }
  // 2. klippen (nyast först, högst MAX), bildspel och mycket långa klipp hoppas över
  const kallorFil = path.join(DATA, 'kallor.json')
  const utDir = path.join(UT, konto)
  fs.mkdirSync(utDir, { recursive: true })
  let nya = 0, fel = 0
  for (const k of lista.slice(0, MAX)) {
    if (k.langd != null && (k.langd < 3 || k.langd > 180)) continue
    const fil = path.join(utDir, `${k.id}.mp4`)
    if (!fs.existsSync(fil)) {
      try {
        await ytdlp(['-f', 'bv*[height<=1280][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b', '--merge-output-format', 'mp4', '--write-info-json', '--no-write-comments', '--sleep-requests', '1', '--sleep-interval', '2', '--max-sleep-interval', '5', '-o', path.join(utDir, '%(id)s.%(ext)s'), k.url])
        nya++
      } catch (e) { fel++; console.warn(`  ${k.id}: ${e.message.slice(0, 160)}`); continue }
    }
    // registrera (läses om varje gång: flera körningar kan gå samtidigt)
    const kallor = lasJson(kallorFil) ?? {}
    const id = `${konto}-${k.id}`
    if (!kallor[id] && fs.existsSync(fil)) {
      const info = lasJson(path.join(utDir, `${k.id}.info.json`)) ?? {}
      kallor[id] = { fil: fil.replaceAll('\\', '/'), konto, kalla: 'bank', video: k.id, url: k.url, langd: info.duration ?? k.langd, visningar: info.view_count ?? k.visningar, gillanden: info.like_count ?? k.gillanden, kommentarer: info.comment_count ?? k.kommentarer, delningar: info.repost_count ?? k.delningar, datum: info.upload_date ? `${info.upload_date.slice(0, 4)}-${info.upload_date.slice(4, 6)}-${info.upload_date.slice(6, 8)}` : k.datum, text: info.description ?? k.text, ljud: info.track ?? info.artist ?? null }
      fs.writeFileSync(kallorFil, JSON.stringify(kallor, null, 2))
    }
  }
  console.log(`  @${konto}: ${nya} nya klipp${fel ? `, ${fel} fel` : ''} → ${utDir}`)
  return { konto, lista: lista.length, nya, fel }
}

if (import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const konton = profiler(args.filter((a, i) => !a.startsWith('--') && !['--max', '--ut'].includes(args[i - 1])))
  if (!konton.length) { console.error('inga profiler'); process.exit(1) }
  console.log(`${konton.length} profiler, högst ${MAX} klipp per profil → ${UT}`)
  const sammanfattning = []
  for (const k of konton) {
    try { sammanfattning.push(await hamtaProfil(k)) } catch (e) { console.warn(`@${k}: ${e.message.slice(0, 200)}`); sammanfattning.push({ konto: k, fel: e.message }) }
  }
  fs.writeFileSync(path.join(DATA, 'bank', 'senaste.json'), JSON.stringify({ tid: new Date().toISOString(), sammanfattning }, null, 1))
}
