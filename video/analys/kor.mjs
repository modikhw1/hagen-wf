#!/usr/bin/env node
// Analysera klipp lokalt i tre steg (pipelinen ligger i pipeline.mjs och delas med bryggan):
//   Mät  (ffmpeg/ffprobe)          längd, klippkandidater med styrka, bildrutor
//   Se   (Edge headless)           MediaPipe pose/hand/objekt + OpenCV: kroppar, kamera, likhet över klipp
//   Tolka (tolka.mjs, rena funktioner) scener, komposition, kameraord, aktivitet
// Mät och Se är dyra och sparas som rådata i data/ra/<id>.json. Tolka är billigt och körs om
// när gränserna kalibreras, utan att videon analyseras igen.
//
//   npm run analysera -- <mapp> [--monster ssstik*.mp4] [--bara <id>] [--om]
//   npm run analysera -- --tolka [--bara <id>]      tolka om allt som har rådata
//   npm run analysera -- --kallor [--kalla bank,import] [--konto x]   klipp som redan står i kallor.json
//
// Resultat: data/analys/<id>.json, nyckelbilder i data/analys/<id>/, källorna i data/kallor.json.
import fs from 'node:fs'
import path from 'node:path'
import { VERSION } from './tolka.mjs'
import { DATA, SE_VERSION, tolkaOchSpara, startaMotor, seKlipp, sparaRa } from './pipeline.mjs'

const ANALYS = path.join(DATA, 'analys')
const RA = path.join(DATA, 'ra')
const args = process.argv.slice(2)
const flagga = f => args.includes(f)
const varde = f => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : null }
const bara = varde('--bara')
fs.mkdirSync(ANALYS, { recursive: true })
fs.mkdirSync(RA, { recursive: true })
const spara = ra => tolkaOchSpara(ra, { ut: ANALYS, raDir: path.join(RA, ra.id), bildBas: 'analys' })

if (flagga('--tolka')) {
  const filer = fs.readdirSync(RA).filter(f => f.endsWith('.json')).filter(f => !bara || f === `${bara}.json`)
  for (const f of filer) {
    const ra = JSON.parse(fs.readFileSync(path.join(RA, f), 'utf8'))
    const a = spara(ra)
    console.log(`${ra.id}: ${a.scener.length} scener, ${a.klipp.filter(k => k.typ !== 'scen').length} övriga klipp`)
  }
  process.exit(0)
}

const mapp = flagga('--kallor') ? null : args.find(a => !a.startsWith('--') && a !== varde('--monster') && a !== bara)
if (!mapp && !flagga('--kallor')) { console.error('ange en mapp med klipp, --kallor eller --tolka'); process.exit(1) }
const monster = new RegExp('^' + (varde('--monster') ?? 'ssstik*.mp4').replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*') + '$', 'i')

// id ur filnamnet: ssstik.io_@konto_tid.mp4 → konto-tid
function idFor(fil) {
  const b = path.basename(fil, path.extname(fil))
  const m = /^ssstik\.io_@(.+)_(\d+)$/.exec(b)
  return m ? { id: `${m[1]}-${m[2]}`.replace(/[^\w.\-]/g, '_'), konto: m[1], kalla: 'ssstik' } : { id: b.replace(/[^\w.\-]/g, '_'), konto: null, kalla: 'fil' }
}

const kallorFil = path.join(DATA, 'kallor.json')
const kallor = fs.existsSync(kallorFil) ? JSON.parse(fs.readFileSync(kallorFil, 'utf8')) : {}
let jobb
if (flagga('--kallor')) {
  // klipp som redan står i kallor.json (bank/hamta.mjs, bank/importera.mjs); kallor.json lämnas orörd
  const kallaSet = new Set((varde('--kalla') ?? 'bank,import').split(','))
  jobb = Object.entries(kallor)
    .filter(([, k]) => kallaSet.has(k.kalla) && (!varde('--konto') || k.konto === varde('--konto')) && fs.existsSync(k.fil))
    .map(([id, k]) => ({ fil: k.fil, id, konto: k.konto, kalla: k.kalla }))
    .filter(j => !bara || j.id === bara)
  // --urval: bara klipp som bankens urval valt (data/bank/urval.json), inte hela banken
  if (flagga('--urval')) {
    const u = JSON.parse(fs.readFileSync(path.join(DATA, 'bank', 'urval.json'), 'utf8'))
    const valda = new Set(u.klipp.filter(k => k.valt).map(k => k.id))
    jobb = jobb.filter(j => valda.has(j.id))
  }
} else {
  const filer = fs.readdirSync(mapp).filter(f => monster.test(f)).sort().map(f => path.join(mapp, f))
  jobb = filer.map(f => ({ fil: f, ...idFor(f) })).filter(j => !bara || j.id === bara)
  for (const j of jobb) kallor[j.id] = { ...(kallor[j.id] ?? {}), fil: j.fil.replaceAll('\\', '/'), konto: j.konto, kalla: j.kalla }
  fs.writeFileSync(kallorFil, JSON.stringify(kallor, null, 2))
}

const raFil = id => path.join(RA, `${id}.json`)
const att = jobb.filter(j => {
  if (flagga('--om') || !fs.existsSync(raFil(j.id))) return true
  try { return JSON.parse(fs.readFileSync(raFil(j.id), 'utf8')).seVersion !== SE_VERSION } catch { return true }
})
console.log(`${jobb.length} klipp, ${att.length} att se (se v${SE_VERSION}, tolka v${VERSION})`)

if (att.length) {
  const m = await startaMotor()
  console.log(`motor: ${m.motor.pose}, ${m.motor.ffmpeg}`)
  let i = 0
  for (const j of att) {
    i++
    const t0 = Date.now()
    let dir
    try {
      const s = await seKlipp(m, j)
      dir = s.dir
      const { ra } = sparaRa({ ...j, ...s, motor: m.motor }, RA)
      const a = spara(ra)
      const saknas = s.sett.ramar.filter(r => r.saknas).length
      console.log(`[${i}/${att.length}] ${j.id}: ${s.meta.langd}s, ${a.scener.length} scener, ${a.klipp.filter(k => k.typ !== 'scen').length} övriga klipp${saknas ? `, ${saknas} rutor saknas` : ''} · ${((Date.now() - t0) / 1000).toFixed(0)} s`)
    } catch (e) {
      console.error(`[${i}/${att.length}] ${j.id}: FEL ${e.message.split('\n').slice(0, 6).join(' ')}`)
    } finally {
      if (dir) fs.rmSync(dir, { recursive: true, force: true })
    }
  }
  await m.stang()
}
