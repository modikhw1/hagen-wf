// Pipelinen som delas av biblioteket (analys/kor.mjs) och bryggan (brygga/kor.mjs):
// samma Mät, samma Se, samma Tolka, oavsett om klippet är en riktig video eller en rendering
// av ett manus. Det är det som gör att talen går att jämföra.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { probe, klippkandidater, utanSlut, bildrutor, rutorRunt, ANALYS_FPS } from './mat.mjs'
import { tolka } from './tolka.mjs'
import { versioner } from './verktyg.mjs'

const HAR = path.dirname(fileURLToPath(import.meta.url))
export const APP = path.resolve(HAR, '..')
export const DATA = path.resolve(APP, '../data')
export const SE_VERSION = 5 // höj när Mät eller Se ändras; då måste videon analyseras igen
export const TMP = path.join(os.tmpdir(), 'letrend-analys')

// Tolka rådata och skriv analysen och nyckelbilderna under `ut` (analys/<id>.json, analys/<id>/scen-i.jpg).
// raDir: där rådatans bildrutor ligger. bildBas: hur analysen pekar på nyckelbilderna (relativt data/).
export function tolkaOchSpara(ra, { ut, raDir, bildBas }) {
  const analys = tolka({ id: ra.id, konto: ra.konto, kalla: ra.kalla, meta: ra.meta, kandidater: ra.kand, sett: ra.sett, fps: ra.fps, motor: ra.motor })
  const nyck = path.join(ut, ra.id)
  fs.mkdirSync(nyck, { recursive: true })
  for (const f of fs.readdirSync(nyck)) if (f.startsWith('scen-')) fs.rmSync(path.join(nyck, f))
  for (const s of analys.scener) {
    const n = Math.min(ra.nyckel.length - 1, Math.round(((s.start + s.slut) / 2) * ra.fps))
    const kalla = path.join(raDir, ra.nyckel[n])
    if (fs.existsSync(kalla)) fs.copyFileSync(kalla, path.join(nyck, `scen-${s.i}.jpg`))
    s.bild = `${bildBas}/${ra.id}/scen-${s.i}.jpg`
  }
  fs.writeFileSync(path.join(ut, `${ra.id}.json`), JSON.stringify(analys))
  return analys
}

// Starta Vite (utan omladdning) och Edge med analysens sida.
export async function startaMotor({ port = 5181 } = {}) {
  const { createServer } = await import('vite')
  const { chromium } = await import('playwright-core')
  fs.mkdirSync(TMP, { recursive: true })
  process.env.LETREND_RAMAR = TMP
  const server = await createServer({ root: APP, configFile: path.join(APP, 'vite.config.js'), server: { port, hmr: false, watch: { ignored: ['**/*'] } }, logLevel: 'warn' })
  await server.listen()
  const bas = server.resolvedUrls.local[0].replace(/\/$/, '')
  const browser = await chromium.launch({ channel: 'msedge', headless: true })
  const page = await browser.newPage()
  page.on('pageerror', e => console.error('sidfel:', e.message))
  page.on('console', m => { if (m.type() === 'warning' && m.text().startsWith('ruta saknas')) console.warn('  ' + m.text()) })
  await page.goto(`${bas}/analys/runner.html`)
  const { delegat } = await page.evaluate(() => window.analysRedo)
  const ver = await versioner()
  const motor = { pose: `mediapipe pose_landmarker_full + hand_landmarker + efficientdet_lite2 + blaze_face_full_range (${delegat})`, ffmpeg: ver.ffmpeg.split(' Copyright')[0], se: SE_VERSION }
  return {
    server, browser, page, bas, motor,
    async stang() { await browser.close(); await server.close() },
  }
}

// Mät och Se för en fil. Rutorna ligger kvar i TMP/<id> tills anroparen städar.
export async function seKlipp(m, { fil, id }) {
  const dir = path.join(TMP, id)
  fs.rmSync(dir, { recursive: true, force: true })
  const meta = await probe(fil)
  const kand = utanSlut(await klippkandidater(fil), meta.langd)
  const ramar = await bildrutor(fil, dir, ANALYS_FPS)
  const runt = await rutorRunt(fil, dir, kand.map(k => k.t), meta.fps ?? 30)
  const arg = { bas: `/__ramar/${id}`, ramar, fps: ANALYS_FPS, kandidater: runt }
  let sett
  try { sett = await m.page.evaluate(a => window.analysera(a), arg) } catch (e) {
    if (!/context was destroyed|Target closed|navigation/i.test(e.message)) throw e
    console.warn(`  sidan laddades om, försöker igen: ${id}`)
    await m.page.goto(`${m.bas}/analys/runner.html`)
    await m.page.evaluate(() => window.analysRedo)
    sett = await m.page.evaluate(a => window.analysera(a), arg)
  }
  return { meta, kand, sett, ramar, dir, fps: ANALYS_FPS }
}

// Spara rådata (rutorna och det som setts) under raRot/<id>.
export function sparaRa({ id, konto, kalla, meta, kand, sett, ramar, dir, fps, motor }, raRot) {
  const raDir = path.join(raRot, id)
  fs.rmSync(raDir, { recursive: true, force: true })
  fs.mkdirSync(raDir, { recursive: true })
  for (const r of ramar) fs.copyFileSync(path.join(dir, r), path.join(raDir, r))
  const ra = { id, konto, kalla, seVersion: SE_VERSION, fps, meta, kand, sett, nyckel: ramar, motor }
  fs.writeFileSync(path.join(raRot, `${id}.json`), JSON.stringify(ra))
  return { ra, raDir }
}
