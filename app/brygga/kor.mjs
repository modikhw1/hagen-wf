#!/usr/bin/env node
// Bryggan: gör 3D-motorns mätning jämförbar med analysen av riktiga klipp.
//
// För varje manus:
//   1. Rendera bildrutorna (Edge headless, samma 360×640 som analysen) och koda till video.
//   2. Analysera videon med EXAKT samma pipeline som biblioteket (Mät + Se + Tolka).
//   3. Tolka motorns egen syn (motor/syn.js) med samma tolkning.
//   4. Jämför: per ruta (punkter, kamera, personer, händer) och per scen (alla egenskaper).
// Resultat i data/brygga/: video/, ra/, analys/ (renderingens analys), native/ (motorns syn),
// och rapport.json med samband, bias och korrektion per egenskap.
//
//   npm run brygga [-- --bara <id>] [--om] [--rapport] [--tolka]
//     --rapport  bara jämför det som finns
//     --tolka    tolka om båda sidor från rådata (analysens och motorns), utan ny rendering
import fs from 'node:fs'
import path from 'node:path'
import { DATA, TMP, startaMotor, seKlipp, sparaRa, tolkaOchSpara, SE_VERSION } from '../analys/pipeline.mjs'
import { tolka } from '../analys/tolka.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { jamforAlla } from './jamfor.mjs'

const B = path.join(DATA, 'brygga')
const dirs = Object.fromEntries(['video', 'ra', 'analys', 'native', 'raNative'].map(d => [d, path.join(B, d === 'raNative' ? 'ra-native' : d)]))
for (const d of Object.values(dirs)) fs.mkdirSync(d, { recursive: true })
const args = process.argv.slice(2)
const flagga = f => args.includes(f)
const varde = f => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : null }

// Motorns syn genom samma tolkning som analysen; scengränserna är kända, så klippen är facit.
function tolkaNative(rn, analys) {
  const native = tolka({ id: rn.id, konto: 'motor', kalla: 'native', meta: rn.meta, kandidater: rn.kand, sett: rn.sett, fps: rn.fps, motor: { syn: 'motor/syn.js', se: SE_VERSION } })
  native.scener.forEach((sc, i) => { sc.bild = analys.scener.find(a => a.start <= sc.start + 0.05 && a.slut > sc.start)?.bild ?? null; sc.facit = rn.facit.scener[i] })
  native.facit = rn.facit
  fs.writeFileSync(path.join(dirs.native, `${rn.id}.json`), JSON.stringify(native))
  return native
}

if (flagga('--tolka')) {
  for (const f of fs.readdirSync(dirs.raNative).filter(f => f.endsWith('.json'))) {
    const rn = JSON.parse(fs.readFileSync(path.join(dirs.raNative, f), 'utf8'))
    const ra = JSON.parse(fs.readFileSync(path.join(dirs.ra, f), 'utf8'))
    const analys = tolkaOchSpara(ra, { ut: dirs.analys, raDir: path.join(dirs.ra, ra.id), bildBas: 'brygga/analys' })
    tolkaNative(rn, analys)
  }
} else if (!flagga('--rapport')) {
  const m = await startaMotor({ port: 5182 })
  const sida = await m.browser.newPage()
  sida.on('pageerror', e => console.error('renderingsfel:', e.message))
  await sida.goto(`${m.bas}/brygga/rendera.html`)
  await sida.evaluate(() => window.bryggRedo)
  const alla = await sida.evaluate(() => window.bryggManus())
  const lista = alla.filter(id => !varde('--bara') || id === varde('--bara'))
  const kallorFil = path.join(DATA, 'kallor.json')
  for (const id of lista) {
    if (!flagga('--om') && fs.existsSync(path.join(dirs.native, `${id}.json`)) && fs.existsSync(path.join(dirs.analys, `${id}.json`))) { console.log(`${id}: finns`); continue }
    const t0 = Date.now()
    // 1. rendera
    const r = await sida.evaluate(a => window.renderaManus(a), { id, fps: 10 })
    const dir = path.join(TMP, `brygga-${id}`)
    fs.rmSync(dir, { recursive: true, force: true })
    fs.mkdirSync(dir, { recursive: true })
    r.bilder.forEach((b, k) => fs.writeFileSync(path.join(dir, `${String(k + 1).padStart(5, '0')}.jpg`), Buffer.from(b.split(',')[1], 'base64')))
    const video = path.join(dirs.video, `${id}.mp4`)
    await kor(verktyg.ffmpeg, ['-v', 'error', '-y', '-framerate', String(r.fps), '-i', '%05d.jpg', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-r', String(r.fps), video], dir)
    fs.rmSync(dir, { recursive: true, force: true })
    const kallor = fs.existsSync(kallorFil) ? JSON.parse(fs.readFileSync(kallorFil, 'utf8')) : {}
    kallor[id] = { fil: video.replaceAll('\\', '/'), konto: 'motor', kalla: 'brygga' }
    fs.writeFileSync(kallorFil, JSON.stringify(kallor, null, 2))
    // 2. samma pipeline som biblioteket
    const s = await seKlipp(m, { fil: video, id })
    const { ra, raDir } = sparaRa({ id, konto: 'motor', kalla: 'brygga', ...s, motor: m.motor }, dirs.ra)
    fs.rmSync(s.dir, { recursive: true, force: true })
    const analys = tolkaOchSpara(ra, { ut: dirs.analys, raDir, bildBas: 'brygga/analys' })
    // 3. motorns egen syn genom samma tolkning; scengränserna är kända, så klippen är facit
    const kand = r.granser.map(g => ({ t: g.t, styrka: 1 }))
    const sett = { ramar: r.syn.map(({ scen, ...f }) => ({ ...f, personer: f.personer.map(({ roll, ...p }) => p) })), kandidater: kand.map(() => ({ inliers: 0, inl: 0 })) }
    const meta = { langd: Math.round(r.langd * 1000) / 1000, bredd: 360, hojd: 640, fps: r.fps, ljud: false }
    const rn = { id, meta, kand, sett, fps: r.fps, facit: { granser: r.granser, scener: r.scener } }
    fs.writeFileSync(path.join(dirs.raNative, `${id}.json`), JSON.stringify(rn))
    const native = tolkaNative(rn, analys)
    console.log(`${id}: ${r.bilder.length} rutor · analysen ${analys.scener.length} scener, motorn ${native.scener.length} · ${((Date.now() - t0) / 1000).toFixed(0)} s`)
  }
  await m.stang()
}

// 4. jämför allt som finns
const rapport = jamforAlla(dirs)
fs.writeFileSync(path.join(B, 'rapport.json'), JSON.stringify(rapport, null, 1))
// Korrektionen: motorns tal → analysens skala (analys ≈ a + b · motor), bara där sambandet håller.
// Kameran och motivet mäts där båda ser samma sak (matchad), övriga egenskaper per scen.
const GILTIG = { minR: 0.5, minN: 20 }
const korr = { skapad: rapport.skapad, gräns: GILTIG, egenskaper: {} }
const satt = (namn, st, kalla) => {
  const ok = st.n >= GILTIG.minN && st.r != null && st.r >= GILTIG.minR && st.b != null
  const orsak = ok ? null : st.n < GILTIG.minN ? `för få par (${st.n})` : st.r == null ? 'ingen variation' : `svagt samband (r = ${st.r})`
  korr.egenskaper[namn] = { a: st.a, b: st.b, r: st.r, rs: st.rs ?? null, n: st.n, kalla, giltig: ok, orsak }
}
for (const e of rapport.egenskaper) satt(e.namn, e, 'scen')
satt('kamera', rapport.matchad.kamera, 'matchad')
satt('motiv', rapport.matchad.motiv, 'matchad')
fs.writeFileSync(path.join(B, 'korrektion.json'), JSON.stringify(korr, null, 1))
const giltiga = Object.entries(korr.egenskaper).filter(([, v]) => v.giltig).map(([k]) => k)
console.log(`\nRapport: ${rapport.manus.length} manus, ${rapport.scener.n} scenpar`)
console.log(`  detektion av dockorna: pose ${pct(rapport.detektion.pose)}, ansikte ${pct(rapport.detektion.ansikte)}, coco ${pct(rapport.detektion.coco)}, kvar efter filter ${pct(rapport.detektion.efterFilter)}`)
console.log(`  personer: analysen hittar ${pct(rapport.rutor.personHittad)} av de personer motorn har i bild (falska ${pct(rapport.rutor.personFalsk)})`)
console.log(`  enheter där båda ser samma: motiv r=${fx(rapport.matchad.motiv.r)} b=${fx(rapport.matchad.motiv.b)} (n=${rapport.matchad.motiv.n}) · kamera r=${fx(rapport.matchad.kamera.r)} b=${fx(rapport.matchad.kamera.b)} (n=${rapport.matchad.kamera.n})`)
console.log(`  punkter: medelfel ${rapport.rutor.punktFel?.toFixed(3)} bildhöjder (kärnpunkter)`)
console.log(`  kamera per ruta (utanför övergångar): dx r=${fx(rapport.rutor.kamera.dx.r)} rs=${fx(rapport.rutor.kamera.dx.rs)}, dy r=${fx(rapport.rutor.kamera.dy.r)} rs=${fx(rapport.rutor.kamera.dy.rs)}, skala r=${fx(rapport.rutor.kamera.skala.r)} rs=${fx(rapport.rutor.kamera.skala.rs)} (n=${rapport.rutor.kamera.dx.n})`)
console.log(`  utsnitt lika: ${pct(rapport.scener.utsnittLika)} · scengränser hittade: ${pct(rapport.scener.granserHittade)}`)
console.log(`  korrektion giltig för ${giltiga.length} egenskaper: ${giltiga.join(', ')}`)
for (const [n, v] of Object.entries(korr.egenskaper).filter(([, v]) => !v.giltig && v.n >= 5)) console.log(`  ogiltig: ${n.padEnd(14)} ${v.orsak}`)
function pct(x) { return x == null ? '–' : `${Math.round(x * 100)} %` }
function fx(x) { return x == null ? '–' : x.toFixed(2) }
