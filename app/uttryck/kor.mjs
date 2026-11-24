#!/usr/bin/env node
// Mät uttrycksrummet för originalet (alla scener × alla uttryck) med motorns syn och samma
// tolkning som analysen. Resultat: data/uttryck/<klipp>.json. Placeringen på vertikalen görs i
// webbläsaren när reglaget används, med bryggans korrektion och scenografi-modellen, så att nya
// bedömningar och en ny brygga slår igenom utan att mäta om.
//
//   npm run uttrycksrum [-- --max 200] [--scen 2] [--klipp <id>]
// --klipp: ett rekonstruerat klipp (data/rekon/<id>/manus.json) i stället för Nonna; kamera och agerande.
import fs from 'node:fs'
import path from 'node:path'
import { APP, DATA } from '../analys/pipeline.mjs'
import { MATNING_VERSION } from '../kalibrering/placering.mjs'

const args = process.argv.slice(2)
const varde = f => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : null }
const max = varde('--max') ? Number(varde('--max')) : Infinity
const bara = varde('--scen') != null ? Number(varde('--scen')) : null
const klipp = varde('--klipp')
// <id>~modell: den modellerade scenen (manus-modell.json)
const url = klipp ? (klipp.endsWith('~modell') ? `/__data/rekon/${klipp.slice(0, -7)}/manus-modell.json` : `/__data/rekon/${klipp}/manus.json`) : null

const { createServer } = await import('vite')
const { chromium } = await import('playwright-core')
const server = await createServer({ root: APP, configFile: path.join(APP, 'vite.config.js'), server: { port: 5183, hmr: false, watch: { ignored: ['**/*'] } }, logLevel: 'warn' })
await server.listen()
const bas = server.resolvedUrls.local[0].replace(/\/$/, '')
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const page = await browser.newPage()
page.on('pageerror', e => console.error('sidfel:', e.message))
await page.goto(`${bas}/uttryck/matning.html`)
await page.evaluate(() => window.matningRedo)
page.setDefaultTimeout(0) // en scen kan ta många minuter

const ut = path.join(DATA, 'uttryck')
fs.mkdirSync(ut, { recursive: true })
const namn = klipp ?? 'nonna-smakar'
const fil = path.join(ut, `${namn}.json`)
const resultat = fs.existsSync(fil) ? JSON.parse(fs.readFileSync(fil, 'utf8')) : { klipp: namn, scener: [] }
const antalScener = await page.evaluate(u => window.antalScener(u), url)
for (let i = 0; i < antalScener; i++) {
  if (bara != null && i !== bara) continue
  const r = await page.evaluate(a => window.matScen(a), { i, max, url })
  resultat.scener[i] = { ...r, version: MATNING_VERSION }
  const giltiga = r.uttryck.filter(x => x.giltig).length
  console.log(`scen ${i + 1} (${r.text}): ${r.antal} uttryck, ${giltiga} giltiga · ${(r.ms / 1000).toFixed(0)} s (${(r.ms / r.antal).toFixed(1)} ms/uttryck)`)
}
resultat.skapad = new Date().toISOString()
resultat.fps = 5
fs.writeFileSync(fil, JSON.stringify(resultat))
console.log(`sparat: ${fil} (${(fs.statSync(fil).size / 1e6).toFixed(1)} MB)`)
await browser.close()
await server.close()
