#!/usr/bin/env node
// Mät 2D-uttrycken (virtuell kamera på originalvideon) för riktiga klipp: data/uttryck2d/<id>.json.
//   node uttryck/kor2d.mjs <id> [<id> …] [--scen 1] [--max 50]
import fs from 'node:fs'
import path from 'node:path'
import { APP, DATA } from '../analys/pipeline.mjs'

export const VERSION_2D = 1
const args = process.argv.slice(2)
const varde = f => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : null }
const ids = args.filter((a, i) => !a.startsWith('--') && !['--scen', '--max'].includes(args[i - 1]))
const { createServer } = await import('vite')
const { chromium } = await import('playwright-core')
const server = await createServer({ root: APP, configFile: path.join(APP, 'vite.config.js'), server: { port: 5186, hmr: false, watch: { ignored: ['**/*'] } }, logLevel: 'warn' })
await server.listen()
const bas = server.resolvedUrls.local[0].replace(/\/$/, '')
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const page = await browser.newPage()
page.on('pageerror', e => console.error('sidfel:', e.message))
page.setDefaultTimeout(0)
await page.goto(`${bas}/uttryck/matning2d.html`)
await page.evaluate(() => window.mat2dRedo)
const ut = path.join(DATA, 'uttryck2d')
fs.mkdirSync(ut, { recursive: true })
for (const id of ids) {
  const r = await page.evaluate(a => window.mat2d(a), { id, scen: varde('--scen') != null ? Number(varde('--scen')) : null, max: varde('--max') ? Number(varde('--max')) : Infinity })
  const fil = path.join(ut, `${id}.json`)
  const fore = fs.existsSync(fil) ? JSON.parse(fs.readFileSync(fil, 'utf8')) : { klipp: id, scener: [] }
  for (const s of r.scener) { fore.scener[s.i] = { ...s, version: VERSION_2D }; console.log(`${id} scen ${s.i + 1}: ${s.antal} uttryck, ${s.giltiga} giltiga · ${(s.ms / 1000).toFixed(1)} s`) }
  fore.maxZoom = r.maxZoom
  fore.skapad = new Date().toISOString()
  fs.writeFileSync(fil, JSON.stringify(fore))
}
await browser.close()
await server.close()
