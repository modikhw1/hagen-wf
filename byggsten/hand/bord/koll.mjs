// Kontroll av regibordet i en huvudlös webbläsare: laddar in ett klipp mot en kund, gör planens drag,
// fyller en plats i mallen, skriver meningar, och sparar skärmbilder i ut/bord/.
// Kör med servern igång: node bord/koll.mjs [port] [klipp-id] [konto] [mening ...]
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from '../../../app/node_modules/playwright-core/index.mjs'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const UT = path.join(HERE, '..', 'ut', 'bord')
fs.mkdirSync(UT, { recursive: true })
const [port = '5197', klipp = 'blubnan.liljeholm-7520230113443663126', kund = 'kappabar', ...egna] = process.argv.slice(2)
const kandidater = [process.env.CHROME_PATH, path.join(process.env.LOCALAPPDATA ?? '', 'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),
  'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].filter(Boolean)
const executablePath = kandidater.find(p => fs.existsSync(p))
if (!executablePath) throw new Error('ingen webbläsare hittad')

const browser = await chromium.launch({ executablePath, headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-first-run'] })
const page = await browser.newPage({ viewport: { width: 1560, height: 1100 } })
const fel = []
page.on('pageerror', e => fel.push(String(e)))
page.on('console', m => { if (m.type() === 'error') fel.push(m.text()) })
const t0 = Date.now()
await page.goto(`http://127.0.0.1:${port}/?klipp=${encodeURIComponent(klipp)}&kund=${encodeURIComponent(kund)}`)
await page.waitForSelector('#nu .takt canvas', { timeout: 60000 })
const laddning = Date.now() - t0
await page.screenshot({ path: path.join(UT, `1_start_${kund}.png`), fullPage: true })

const vanta = async gor => { const n = await page.locator('#logg .sv').count(); const t = Date.now(); await gor()
  await page.waitForFunction(k => document.querySelectorAll('#logg .sv').length > k, n); await page.waitForTimeout(60); return Date.now() - t }
const tider = []
// planens drag, ett i taget, tills planen är tom (högst 8)
for (let i = 0; i < 8 && await page.locator('#plan button').count(); i++) {
  const text = await page.locator('#plan .plan div').first().innerText()
  tider.push({ plan: text.split('\n')[0], ms: await vanta(() => page.locator('#plan button').first().click()) })
}
// en plats i mallen
const falt = page.locator('#mall input.inaktuell, #platser input.inaktuell').first()
if (await falt.count()) { tider.push({ plats: await falt.getAttribute('title'), ms: await vanta(async () => { await falt.fill('199 kr'); await falt.press('Enter') }) }) }
for (const m of egna.length ? egna : ['gör det kortare', 'ta bort första scenen']) {
  tider.push({ mening: m, ms: await vanta(async () => { await page.fill('#text', m); await page.press('#text', 'Enter') }) })
}
await page.screenshot({ path: path.join(UT, `2_efter_${kund}.png`), fullPage: true })
console.log(JSON.stringify({ klipp, kund, laddning_ms: laddning, fel, tider }, null, 1))
await browser.close()
