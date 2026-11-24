// Rekonstruktionsgraden: manuset renderas ruta för ruta, kodas till video och körs genom samma Se och
// Tolka som originalet. Jämförelsen (rekon/jamfor.mjs) ger ett mått per egenskap och en total.
// Sparas i data/rekon/<id>/grad.json, renderingen i data/rekon/<id>/rendering.mp4.
import fs from 'node:fs'
import path from 'node:path'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { DATA, TMP, seKlipp, sparaRa, tolkaOchSpara } from '../analys/pipeline.mjs'
import { REKON, startaSida, motorBas } from './delat.mjs'
import { identiteter } from './spar.mjs'
import { jamforRekon } from './jamfor.mjs'

const lasJson = f => (fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null)

// Gråskala 18×32 per ruta (10 rutor/s), för att jämföra bildens uppbyggnad.
async function graBilder(fil, fps) {
  const ut = path.join(TMP, `gra-${Date.now()}-${Math.random().toString(36).slice(2)}.raw`)
  await kor(verktyg.ffmpeg, ['-v', 'error', '-y', '-i', fil, '-vf', `fps=${fps},scale=18:32,format=gray`, '-f', 'rawvideo', ut])
  const b = fs.readFileSync(ut)
  fs.rmSync(ut)
  const n = Math.floor(b.length / (18 * 32))
  return Array.from({ length: n }, (_, k) => Float32Array.from(b.subarray(k * 576, (k + 1) * 576), x => x / 255))
}

export async function stegMat(id, om) {
  const dir = path.join(REKON, id)
  const ut = path.join(dir, 'grad.json')
  if (!om && fs.existsSync(ut)) return
  const t0 = Date.now()
  // 1. rendera
  const sida = await startaSida('rekon/rendera.html', 'renderaRedo')
  const r = await sida.evaluate(a => window.renderaRekon(a), { url: `/__data/rekon/${id}/manus.json?${Date.now()}`, fps: 10 })
  const tmp = path.join(TMP, `rekon-r-${id}`)
  fs.rmSync(tmp, { recursive: true, force: true })
  fs.mkdirSync(tmp, { recursive: true })
  r.bilder.forEach((b, k) => fs.writeFileSync(path.join(tmp, `${String(k + 1).padStart(5, '0')}.jpg`), Buffer.from(b.split(',')[1], 'base64')))
  const video = path.join(dir, 'rendering.mp4')
  await kor(verktyg.ffmpeg, ['-v', 'error', '-y', '-framerate', String(r.fps), '-i', '%05d.jpg', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-r', String(r.fps), video], tmp)
  fs.rmSync(tmp, { recursive: true, force: true })
  // 2. samma Se och Tolka som originalet
  const runner = await startaSida('analys/runner.html', 'analysRedo')
  const sid = `rekon-${id}`
  const s = await seKlipp({ page: runner, bas: motorBas() }, { fil: video, id: sid })
  const raRot = path.join(TMP, 'rekon-ra')
  const { ra, raDir } = sparaRa({ id: sid, konto: 'rekon', kalla: 'rekon', ...s, motor: { rekon: true } }, raRot)
  fs.rmSync(s.dir, { recursive: true, force: true })
  const rendering = tolkaOchSpara(ra, { ut: path.join(dir, 'r'), raDir, bildBas: `rekon/${id}/r` })
  // 3. jämför
  const original = lasJson(path.join(DATA, 'analys', `${id}.json`))
  const kalla = lasJson(path.join(DATA, 'kallor.json'))[id].fil
  const sr = lasJson(path.join(dir, 'spar-ra.json'))
  const scener = original.scener.map(sc => ({ i0: Math.round(sc.start * sr.fps), i1: Math.min(sr.ramar.length, Math.max(Math.round(sc.start * sr.fps) + 1, Math.round(sc.slut * sr.fps))) }))
  const personer = identiteter(sr.ramar, scener)
  const bilder = { original: await graBilder(kalla, 10), rendering: await graBilder(video, 10) }
  const g = jamforRekon({ original, rendering, personer, projektioner: r.projektioner, bilder, fps: 10 })
  fs.writeFileSync(ut, JSON.stringify({ id, matt: g.matt, total: g.total, skapad: new Date().toISOString() }, null, 1))
  console.log(`  mat: ${Math.round(g.total * 100)} % · ${Object.entries(g.matt).map(([k, v]) => `${k} ${v.varde == null ? '–' : Math.round(v.varde * 100)}`).join(', ')} · ${((Date.now() - t0) / 1000).toFixed(0)} s`)
}
