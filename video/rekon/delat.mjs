// Delat mellan rekonstruktionens steg: kataloger, rutorna i 720 bredd och motorn (Vite + Edge).
import fs from 'node:fs'
import path from 'node:path'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { APP, DATA, TMP } from '../analys/pipeline.mjs'

export const REKON = path.join(DATA, 'rekon')
export const RUTOR = path.join(TMP, 'rekon')
export const FPS = 10
const BREDD = 720
export { BREDD }

const lasJson = f => (fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null)
const kallor = () => lasJson(path.join(DATA, 'kallor.json')) ?? {}

// Rutorna i 720 bredd (Pose på utskurna personer behöver fler pixlar än analysens 360).
export async function rutor(id) {
  const dir = path.join(RUTOR, id)
  if (fs.existsSync(dir) && fs.readdirSync(dir).length) return fs.readdirSync(dir).filter(f => f.endsWith('.jpg')).sort()
  const k = kallor()[id]
  if (!k?.fil) throw new Error(`ingen källa för ${id}`)
  fs.mkdirSync(dir, { recursive: true })
  await kor(verktyg.ffmpeg, ['-v', 'error', '-y', '-i', path.basename(k.fil), '-vf', `fps=${FPS},scale=${BREDD}:-2`, '-q:v', '3', path.join(dir, '%05d.jpg')], path.dirname(k.fil))
  return fs.readdirSync(dir).filter(f => f.endsWith('.jpg')).sort()
}

let motor = null
export async function startaSida(sida, redo) {
  const { createServer } = await import('vite')
  const { chromium } = await import('playwright-core')
  process.env.LETREND_RAMAR = TMP // rekonstruktionens rutor under rekon/, analysens direkt under
  if (!motor) {
    const server = await createServer({ root: APP, configFile: path.join(APP, 'vite.config.js'), server: { port: 5184, hmr: false, watch: { ignored: ['**/*'] } }, logLevel: 'warn' })
    await server.listen()
    const browser = await chromium.launch({ channel: 'msedge', headless: true, args: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'] })
    motor = { server, browser, bas: server.resolvedUrls.local[0].replace(/\/$/, ''), sidor: {} }
  }
  if (!motor.sidor[sida]) {
    const page = await motor.browser.newPage()
    page.on('pageerror', e => console.error('sidfel:', e.message))
    page.on('console', m => { if (m.type() === 'error') console.error('  konsol:', m.text()) })
    await page.goto(`${motor.bas}/${sida}`)
    await page.evaluate(r => window[r], redo)
    motor.sidor[sida] = page
  }
  return motor.sidor[sida]
}
export async function stangMotor() { if (motor) { await motor.browser.close(); await motor.server.close(); motor = null } }

export const motorBas = () => motor?.bas
