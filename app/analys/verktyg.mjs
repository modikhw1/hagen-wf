// ffmpeg och ffprobe, med samma kontrakt som hagen-ui (artifacts/api-server/src/lib/ingest-v2/measure.ts):
// FFMPEG_PATH / FFPROBE_PATH om de är satta, annars verktyget på PATH (Docker-imagen i produktion).
// Reserv här: ffmpeg-static / ffprobe-static, så att analysen går att köra på vilken dator som helst.
import { execFile, spawnSync } from 'node:child_process'
import { createRequire } from 'node:module'
import path from 'node:path'

const require = createRequire(import.meta.url)

const fungerar = bin => {
  const r = spawnSync(bin, ['-version'], { windowsHide: true })
  return r.status === 0 && !r.error
}

function valj(env, namn, statisk) {
  if (process.env[env]) return process.env[env]
  if (fungerar(namn)) return namn
  return statisk()
}

export const verktyg = {
  ffmpeg: valj('FFMPEG_PATH', 'ffmpeg', () => require('ffmpeg-static')),
  ffprobe: valj('FFPROBE_PATH', 'ffprobe', () => require('ffprobe-static').path),
}

export function kor(bin, args, cwd) {
  return new Promise((resolve, reject) => {
    execFile(bin, args, { cwd, timeout: 600_000, maxBuffer: 64 * 1024 * 1024, windowsHide: true }, (err, stdout, stderr) => {
      if (err) reject(new Error(`${path.basename(bin)}: ${(stderr || err.message).toString().split('\n').slice(-4).join(' ')}`))
      else resolve(stdout)
    })
  })
}

export const versioner = async () => ({
  ffmpeg: (await kor(verktyg.ffmpeg, ['-version'])).split('\n')[0],
  ffprobe: (await kor(verktyg.ffprobe, ['-version'])).split('\n')[0],
})
