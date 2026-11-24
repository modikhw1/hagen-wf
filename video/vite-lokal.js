// Lokala filer och kalibrering, bara i utvecklingsservern:
//   GET  /__index             biblioteket i korthet
//   GET  /__data/...          analysdata och nyckelbilder i hagen-wf/data
//   GET  /__video/<id>        källvideon för ett klipp (med Range, så att spelaren kan spola)
//   GET  /__ramar/...         analysens tillfälliga rutor (bara när analysen körs, LETREND_RAMAR)
//   POST /__ratta/<id>        sparar en rättelse i data/rattelser/<id>.json
//   GET  /__kalib             vertikaler, items (scener och klipp med egenskaper) och Jev-status
//   GET  /__bedomningar/<v>   parvisa bedömningar för en vertikal
//   POST /__bedom/<v>         lägger till en bedömning (data/bedomningar/<v>.jsonl)
//   POST /__vertikal/<v>      sparar egna kriterier eller egen fråga (data/vertikaler.json)
//   POST /__jev/<v>           kör Jev (score eller par) på det som bedömts; nyckeln stannar här
//   GET  /__bank/bedomningar  egna bedömningar av bankens klipp
//   POST /__bank/bedom       sparar en bedömning atomiskt för en känd källa
//   GET  /__bank/video/<id>  cachad H.264-reserv för webbläsare utan stöd för källans videokodek
// Allt slås upp mot kända kataloger; inga godtyckliga sökvägar.
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { randomUUID, createHash } from 'node:crypto'
import os from 'node:os'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import ffmpeg from 'ffmpeg-static'
import { scenEgenskaper, klippEgenskaper, scenText } from './kalibrering/egenskaper.mjs'
import { VERTIKALER } from './kalibrering/vertikaler.mjs'
import { nyckel, jevScore, jevPar, jevUttryck, MODELL } from './kalibrering/jev.mjs'

const HAR = path.dirname(fileURLToPath(import.meta.url))
export const DATA = path.resolve(HAR, '../data')
const TYPER = { '.json': 'application/json', '.jsonl': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.mp4': 'video/mp4', '.webp': 'image/webp' }
const ID = /^[\w.\-]+$/

function inom(rot, rel) {
  const fil = path.resolve(rot, '.' + path.sep + decodeURIComponent(rel))
  return fil.startsWith(path.resolve(rot) + path.sep) ? fil : null
}

function skicka(req, res, fil) {
  if (!fil || !fs.existsSync(fil) || !fs.statSync(fil).isFile()) { res.statusCode = 404; return res.end('saknas') }
  const stat = fs.statSync(fil)
  res.setHeader('Content-Type', TYPER[path.extname(fil).toLowerCase()] ?? 'application/octet-stream')
  res.setHeader('Accept-Ranges', 'bytes')
  res.setHeader('Cache-Control', 'no-cache')
  const m = /bytes=(\d*)-(\d*)/.exec(req.headers.range ?? '')
  if (m) {
    let start = m[1] ? Number(m[1]) : stat.size - Number(m[2])
    let slut = m[1] && m[2] ? Number(m[2]) : stat.size - 1
    start = Math.max(0, start)
    slut = Math.min(stat.size - 1, slut)
    res.statusCode = 206
    res.setHeader('Content-Range', `bytes ${start}-${slut}/${stat.size}`)
    res.setHeader('Content-Length', slut - start + 1)
    return fs.createReadStream(fil, { start, end: slut }).pipe(res)
  }
  res.setHeader('Content-Length', stat.size)
  fs.createReadStream(fil).pipe(res)
}

const kallor = () => {
  try { return JSON.parse(fs.readFileSync(path.join(DATA, 'kallor.json'), 'utf8')) } catch { return {} }
}
const lasKropp = req => new Promise((res, rej) => {
  let b = ''
  req.on('data', d => { b += d; if (b.length > 4e6) req.destroy() })
  req.on('end', () => { try { res(JSON.parse(b || '{}')) } catch (e) { rej(e) } })
})
const json = (res, o, kod = 200) => {
  res.statusCode = kod
  res.setHeader('Content-Type', 'application/json')
  res.setHeader('Cache-Control', 'no-cache')
  res.end(JSON.stringify(o))
}

const bankBedomFil = path.join(DATA, 'bank', 'bedomningar.json')
function bankBedomningar() {
  if (!fs.existsSync(bankBedomFil)) return {}
  const data = JSON.parse(fs.readFileSync(bankBedomFil, 'utf8'))
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('Ogiltig bedömningsfil')
  return data
}

function sparaBankBedomning(id, bedomning) {
  const data = { ...bankBedomningar(), [id]: bedomning }
  const tillfallig = `${bankBedomFil}.${randomUUID()}.tmp`
  fs.mkdirSync(path.dirname(bankBedomFil), { recursive: true })
  try {
    fs.writeFileSync(tillfallig, JSON.stringify(data, null, 2), { flag: 'wx' })
    fs.renameSync(tillfallig, bankBedomFil)
  } finally {
    if (fs.existsSync(tillfallig)) fs.unlinkSync(tillfallig)
  }
}

const bankVideoDir = path.join(os.tmpdir(), 'letrend-bank-video')
const bankVideoJobb = new Map()
const korBankVideo = promisify(execFile)
let bankVideoKo = Promise.resolve()
async function bankVideo(kalla) {
  const stat = fs.statSync(kalla.fil)
  const nyckel = createHash('sha256').update(`${kalla.fil}:${stat.size}:${stat.mtimeMs}`).digest('hex')
  const fil = path.join(bankVideoDir, `${nyckel}.mp4`)
  if (fs.existsSync(fil)) return fil
  if (bankVideoJobb.has(nyckel)) return bankVideoJobb.get(nyckel)
  // En konvertering åt gången håller resursåtgången nere när många kort blir synliga.
  const jobb = bankVideoKo.catch(() => {}).then(async () => {
    fs.mkdirSync(bankVideoDir, { recursive: true })
    const tillfallig = path.join(bankVideoDir, `${nyckel}.${randomUUID()}.mp4`)
    try {
      await korBankVideo(ffmpeg, ['-v', 'error', '-nostdin', '-i', kalla.fil, '-vf', 'scale=480:-2,fps=30', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '28', '-pix_fmt', 'yuv420p', '-threads', '2', '-an', '-movflags', '+faststart', tillfallig], { windowsHide: true, timeout: 180000 })
      fs.renameSync(tillfallig, fil)
      return fil
    } finally {
      if (fs.existsSync(tillfallig)) fs.unlinkSync(tillfallig)
    }
  })
  bankVideoJobb.set(nyckel, jobb)
  bankVideoKo = jobb
  try {
    return await jobb
  } finally {
    bankVideoJobb.delete(nyckel)
  }
}

// ---------- kalibrering ----------
// Items: varje scen och varje klipp i biblioteket, med mätta egenskaper och en text för Jev.
let itemCache = { nyckel: null, data: null }
function items() {
  const dir = path.join(DATA, 'analys')
  const filer = fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith('.json')) : []
  const k = filer.map(f => f + fs.statSync(path.join(dir, f)).mtimeMs).join('|')
  if (itemCache.nyckel === k) return itemCache.data
  const scen = []
  const klipp = []
  for (const f of filer) {
    let a
    try { a = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')) } catch { continue }
    if (!a.meta || !a.scener || !a.sammanfattning) continue
    for (const sc of a.scener) {
      scen.push({ id: `${a.id}#${sc.i}`, klipp: a.id, konto: a.konto, i: sc.i, start: sc.start, slut: sc.slut, bild: sc.bild, utsnitt: sc.utsnitt.varde, kamera: sc.kamera.ord, e: scenEgenskaper(sc), text: scenText(sc) })
    }
    const ordning = a.scener.map(sc => `${sc.langd.toFixed(1)} s ${sc.utsnitt.varde} (${sc.kamera.ord.join(', ')})`).join('; ')
    const text = `Ett klipp på ${a.meta.langd.toFixed(0)} sekunder med ${a.scener.length} scener och ${(a.sammanfattning.dynamikPerMin ?? 0).toFixed(0)} snabba klipp per minut. Scenerna i ordning: ${ordning}.`
    klipp.push({ id: a.id, klipp: a.id, konto: a.konto, start: 0, slut: a.meta.langd, bild: a.scener[0]?.bild, e: klippEgenskaper(a), text })
  }
  itemCache = { nyckel: k, data: { scen, klipp } }
  return itemCache.data
}
const vertikalFil = path.join(DATA, 'vertikaler.json')
function vertikaler() {
  let egna = {}
  try { egna = JSON.parse(fs.readFileSync(vertikalFil, 'utf8')) } catch {}
  return VERTIKALER.map(v => ({ ...v, ...(egna[v.id] ?? {}), andrad: Boolean(egna[v.id]) }))
}
const bedFil = v => path.join(DATA, 'bedomningar', `${v}.jsonl`)
function bedomningar(v) {
  try { return fs.readFileSync(bedFil(v), 'utf8').split(/\r?\n/).filter(Boolean).map(l => JSON.parse(l)) } catch { return [] }
}

export default function lokalaFiler() {
  return {
    name: 'letrend-lokala-filer',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = (req.url ?? '').split('?')[0]
        const vid = pre => { const v = decodeURIComponent(url.slice(pre.length)); return ID.test(v) ? v : null }

        if (url.startsWith('/__bank/video/')) {
          if (req.method !== 'GET') {
            res.setHeader('Allow', 'GET')
            return json(res, { fel: 'Använd GET' }, 405)
          }
          const id = vid('/__bank/video/')
          const lista = kallor()
          const kalla = id && Object.hasOwn(lista, id) ? lista[id] : null
          if (!kalla?.fil || !fs.existsSync(kalla.fil) || !fs.statSync(kalla.fil).isFile()) return json(res, { fel: 'Videon saknas' }, 404)
          bankVideo(kalla).then(fil => {
            if (!res.destroyed) skicka(req, res, fil)
          }).catch(() => {
            if (!res.destroyed) json(res, { fel: 'Kunde inte förbereda videon' }, 500)
          })
          return
        }
        if (url === '/__bank/bedomningar') {
          if (req.method !== 'GET') {
            res.setHeader('Allow', 'GET')
            return json(res, { fel: 'Använd GET' }, 405)
          }
          try {
            return json(res, bankBedomningar())
          } catch {
            return json(res, { fel: 'Kunde inte läsa bedömningarna' }, 500)
          }
        }
        if (url === '/__bank/bedom') {
          if (req.method !== 'POST') {
            res.setHeader('Allow', 'POST')
            return json(res, { fel: 'Använd POST' }, 405)
          }
          lasKropp(req).then(b => {
            if (!b || typeof b.id !== 'string' || !ID.test(b.id) || !Object.hasOwn(kallor(), b.id)) {
              return json(res, { fel: 'Okänt eller ogiltigt klipp-id' }, 400)
            }
            if (!['med', 'osaker', 'inte'].includes(b.beslut)) {
              return json(res, { fel: 'Beslut måste vara med, osaker eller inte' }, 400)
            }
            const kommentar = b.kommentar ?? ''
            if (typeof kommentar !== 'string' || kommentar.length > 500) {
              return json(res, { fel: 'Kommentaren får vara högst 500 tecken' }, 400)
            }
            const bedomning = { beslut: b.beslut, kommentar, tid: new Date().toISOString() }
            try {
              sparaBankBedomning(b.id, bedomning)
              json(res, { ok: true, bedomning })
            } catch {
              json(res, { fel: 'Kunde inte spara bedömningen' }, 500)
            }
          }).catch(() => json(res, { fel: 'Ogiltig JSON i anropet' }, 400))
          return
        }
        if (url === '/__kalib') return json(res, { vertikaler: vertikaler(), items: items(), jev: { nyckel: Boolean(nyckel(HAR)), modell: MODELL } })
        if (url.startsWith('/__bedomningar/')) { const v = vid('/__bedomningar/'); return v ? json(res, bedomningar(v)) : json(res, { fel: 'id' }, 400) }
        if (url.startsWith('/__bedom/') && req.method === 'POST') {
          const v = vid('/__bedom/')
          if (!v) return json(res, { fel: 'id' }, 400)
          lasKropp(req).then(b => {
            if (!b.a || !b.b || !['a', 'b', 'lika', 'hoppa'].includes(b.val)) return json(res, { fel: 'a, b och val (a/b/lika/hoppa) krävs' }, 400)
            fs.mkdirSync(path.dirname(bedFil(v)), { recursive: true })
            // uttrycksbedömningar (kalibrering/par.mjs) bär egenskaperna och parets sort; bara tal och korta ord
            const tal = e => (e && typeof e === 'object' ? Object.fromEntries(Object.entries(e).filter(([k, x]) => /^[a-z_]{1,30}$/.test(k) && Number.isFinite(x)).slice(0, 60)) : undefined)
            const extra = { ea: tal(b.ea), eb: tal(b.eb), sort: ['kamera', 'agerande', 'ankare'].includes(b.sort) ? b.sort : undefined }
            fs.appendFileSync(bedFil(v), JSON.stringify({ a: b.a, b: b.b, val: b.val, ms: b.ms ?? null, bedomare: String(b.bedomare ?? 'cm').slice(0, 40), ...extra, tid: new Date().toISOString() }) + '\n')
            json(res, { ok: true })
          }).catch(e => json(res, { fel: e.message }, 400))
          return
        }
        if (url.startsWith('/__vertikal/') && req.method === 'POST') {
          const v = vid('/__vertikal/')
          if (!v) return json(res, { fel: 'id' }, 400)
          lasKropp(req).then(b => {
            let egna = {}
            try { egna = JSON.parse(fs.readFileSync(vertikalFil, 'utf8')) } catch {}
            const ny = {}
            if (Array.isArray(b.kriterier) && b.kriterier.length >= 2 && b.kriterier.length <= 10) ny.kriterier = b.kriterier.map(String)
            if (typeof b.fraga === 'string' && b.fraga.trim()) ny.fraga = b.fraga.trim()
            egna[v] = { ...(egna[v] ?? {}), ...ny }
            fs.writeFileSync(vertikalFil, JSON.stringify(egna, null, 2))
            json(res, { ok: true })
          }).catch(e => json(res, { fel: e.message }, 400))
          return
        }
        if (url === '/__jev-uttryck' && req.method === 'POST') {
          const key = nyckel(HAR)
          if (!key) return json(res, { fel: 'TYPESAFE_API_KEY saknas' }, 400)
          lasKropp(req).then(async b => {
            const v = vertikaler().find(x => x.id === (b.vertikal ?? 'rorlighet'))
            const scener = (b.scener ?? []).filter(s => s.kandidater?.length).map(s => ({ ...s, kandidater: s.kandidater.slice(0, 255) }))
            return json(res, await jevUttryck({ key, vertikal: v, mal: b.mal, scener }))
          }).catch(e => json(res, { fel: e.message }, 500))
          return
        }
        if (url.startsWith('/__jev/') && req.method === 'POST') {
          const v = vertikaler().find(x => x.id === vid('/__jev/'))
          const key = nyckel(HAR)
          if (!v) return json(res, { fel: 'okänd vertikal' }, 400)
          if (!key) return json(res, { fel: 'TYPESAFE_API_KEY saknas (app/.env.local eller miljön)' }, 400)
          lasKropp(req).then(async b => {
            const it = items()[v.enhet] ?? []
            const T = new Map(it.map(x => [x.id, x.text]))
            const bed = bedomningar(v.id).filter(x => x.val !== 'hoppa' && T.has(x.a) && T.has(x.b))
            if (b.typ === 'par') {
              const par = bed.slice(-(b.max ?? 200)).map(x => ({ a: x.a, b: x.b, textA: T.get(x.a), textB: T.get(x.b) }))
              return json(res, await jevPar({ key, dataDir: DATA, vertikal: v, par }))
            }
            const ids = [...new Set(bed.flatMap(x => [x.a, x.b]))].slice(0, b.max ?? 300)
            return json(res, await jevScore({ key, dataDir: DATA, vertikal: v, items: ids.map(id => ({ id, text: T.get(id) })) }))
          }).catch(e => json(res, { fel: e.message }, 500))
          return
        }
        if (url === '/__index') {
          // Biblioteket i korthet: allt utom rutorna, plus om klippet har rättelser.
          const dir = path.join(DATA, 'analys')
          const lista = fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith('.json') && !f.endsWith('.ra.json')) : []
          const ut = lista.map(f => {
            try {
              const a = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'))
              if (!a.meta || !a.sammanfattning) return null // ofullständig eller äldre analys
              const { ramar, ...rest } = a
              rest.scener = (rest.scener ?? []).map(({ kurva, ...s }) => s)
              rest.rattad = fs.existsSync(path.join(DATA, 'rattelser', `${a.id}.json`))
              return rest
            } catch { return null }
          }).filter(Boolean)
          return json(res, ut)
        }
        if (url === '/__uttryck2d') {
          const dir = path.join(DATA, 'uttryck2d')
          const lista = fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith('.json')).map(f => { const u = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); return { id: f.slice(0, -5), scener: (u.scener ?? []).filter(Boolean).length } }) : []
          return json(res, lista)
        }
        if (url === '/__rekon') {
          const dir = path.join(DATA, 'rekon')
          const lista = fs.existsSync(dir) ? fs.readdirSync(dir).filter(d => fs.existsSync(path.join(dir, d, 'manus.json'))).map(d => {
            const g = path.join(dir, d, 'grad.json')
            return { id: d, grad: fs.existsSync(g) ? JSON.parse(fs.readFileSync(g, 'utf8')).total : null }
          }) : []
          return json(res, lista)
        }
        if (url.startsWith('/__data/')) return skicka(req, res, inom(DATA, url.slice('/__data/'.length)))
        if (url.startsWith('/__ramar/') && process.env.LETREND_RAMAR) return skicka(req, res, inom(process.env.LETREND_RAMAR, url.slice('/__ramar/'.length)))
        if (url.startsWith('/__video/')) {
          const id = decodeURIComponent(url.slice('/__video/'.length))
          const k = ID.test(id) ? kallor()[id] : null
          return skicka(req, res, k ? k.fil : null)
        }
        if (url.startsWith('/__ratta/') && req.method === 'POST') {
          const id = vid('/__ratta/')
          if (!id) { res.statusCode = 400; return res.end('ogiltigt id') }
          lasKropp(req).then(data => {
            const dir = path.join(DATA, 'rattelser')
            fs.mkdirSync(dir, { recursive: true })
            fs.writeFileSync(path.join(dir, `${id}.json`), JSON.stringify({ ...data, sparad: new Date().toISOString() }, null, 2))
            json(res, { ok: true })
          }).catch(e => json(res, { fel: e.message }, 400))
          return
        }
        next()
      })
    },
  }
}
