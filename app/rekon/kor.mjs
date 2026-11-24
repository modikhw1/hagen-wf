// Rekonstruktion: ett analyserat klipp blir ett manus som motorn kan spela, och mäts mot originalet.
//
//   node rekon/kor.mjs <id> [<id> …] [--steg spar,lokal,manus,mat] [--om]
//
// Stegen (varje steg sparar i data/rekon/<id>/ och hoppas över om resultatet redan finns):
//   spar   personspår: rutor i 720 bredd, personer, pose per person, färger (Edge, rekon/spar.js)
//   platta ren skiva per scen (utan personer), projiceras på lokalen (rekon/platta.mjs)
//   lokal  lokalen: Gemini lägger ut föremål i nyckelbilder (rekon/lokal.mjs)
//   manus  manuset: geometri, kamerabana, rörelser, figurer, lokal (rekon/manus.mjs)
//   mat    rendera manuset och mät det med samma Se och Tolka som originalet (rekon/mat.mjs)
import fs from 'node:fs'
import path from 'node:path'
import { REKON, FPS, BREDD, rutor, startaSida, stangMotor } from './delat.mjs'

async function stegSpar(id, om) {
  const ut = path.join(REKON, id, 'spar-ra.json')
  if (!om && fs.existsSync(ut)) return
  const ramar = await rutor(id)
  const page = await startaSida('rekon/spar.html', 'sparRedo')
  const t0 = Date.now()
  const r = await page.evaluate(a => window.spara(a), { bas: `/__ramar/rekon/${id}`, ramar, fps: FPS })
  fs.mkdirSync(path.dirname(ut), { recursive: true })
  fs.writeFileSync(ut, JSON.stringify({ id, fps: FPS, bredd: BREDD, delegat: r.delegat, ramar: r.ramar }))
  const n = r.ramar.reduce((a, f) => a + f.personer.filter(p => p.lm).length, 0)
  console.log(`  spar: ${ramar.length} rutor, ${n} poser · ${((Date.now() - t0) / 1000).toFixed(0)} s`)
}

const STEG = {
  spar: stegSpar,
  lokal: async (id, om) => (await import('./lokal.mjs')).stegLokal(id, om),
  platta: async (id, om) => (await import('./platta.mjs')).stegPlatta(id, om),
  manus: async (id, om) => (await import('./manus.mjs')).stegManus(id, om),
  mat: async (id, om) => (await import('./mat.mjs')).stegMat(id, om),
}

if (import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const args = process.argv.slice(2)
  const om = args.includes('--om')
  const si = args.indexOf('--steg')
  const steg = si >= 0 ? args[si + 1].split(',') : Object.keys(STEG)
  const ids = args.filter((a, i) => !a.startsWith('--') && args[i - 1] !== '--steg')
  try {
    for (const id of ids) {
      console.log(id)
      for (const s of steg) await STEG[s](id, om)
    }
  } finally { await stangMotor() }
}
