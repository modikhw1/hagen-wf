// Ren skiva: nyckelbilden per scen utan personer och utan text på skärmen (Gemini bildmodell).
// Den projiceras på lokalens geometri från originalkamerans läge (motor/lokal.js), så att väggar,
// disk och golv får originalets utseende medan dockorna står framför.
//
// Två kontroller, eftersom bildmodellen varken är fullständig eller exakt:
// 1. Personer kvar? Samma persondetektor som personspåren (rekon/spar.js) körs på skivan; hittar den
//    någon tvättas skivan igen (högst två gånger till). Kvarvarande personer blir spöken på väggen.
// 2. Registrering: modellen svarar i eget format och flyttar eller skalar bilden lite. Skala och
//    förskjutning söks så att skivan ligger på originalrutan (personerna maskade), och skivan
//    transformeras därefter.
import fs from 'node:fs'
import path from 'node:path'
import { redigeraBild } from '../typer/gemini.mjs'
import { verktyg, kor } from '../analys/verktyg.mjs'
import { TMP } from '../analys/pipeline.mjs'
import { REKON, RUTOR, rutor, startaSida } from './delat.mjs'

const TEXT = `Remove ALL people from this photo: every person, including staff behind counters, customers, and any partially visible person or body part (hands, arms). Also remove all overlaid captions, subtitles and on-screen text that were added in editing (keep real signs, menus and logos in the room). Fill in what was behind them so the place looks empty and natural. Keep everything else exactly as it is: same camera position, framing, perspective, lighting, colors and objects. Do not add anything new.`
const IGEN = `There are still people (or parts of people) in this photo. Remove every remaining person and body part completely and fill in the background naturally. Keep everything else exactly as it is.`

const W = 90, H = 160
async function gra(fil) {
  const ut = path.join(TMP, `pl-${Date.now()}-${Math.random().toString(36).slice(2)}.raw`)
  await kor(verktyg.ffmpeg, ['-v', 'error', '-y', '-i', fil, '-vf', `scale=${W}:${H},format=gray`, '-f', 'rawvideo', ut])
  const b = fs.readFileSync(ut)
  fs.rmSync(ut)
  return Float32Array.from(b.subarray(0, W * H), v => v / 255)
}
// Korrelation mellan originalet och skivan transformerad (s, dx, dy), där masken är 1.
function korr(o, p, mask, s, dx, dy) {
  const cx = W / 2, cy = H / 2
  let n = 0, so = 0, sp = 0, soo = 0, spp = 0, sop = 0
  for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) {
    if (!mask[y * W + x]) continue
    const px = Math.round((x - cx - dx * W) / s + cx), py = Math.round((y - cy - dy * H) / s + cy)
    if (px < 0 || py < 0 || px >= W || py >= H) continue
    const a = o[y * W + x], b = p[py * W + px]
    n++; so += a; sp += b; soo += a * a; spp += b * b; sop += a * b
  }
  if (n < 200) return -1
  const va = soo - so * so / n, vb = spp - sp * sp / n
  return va > 0 && vb > 0 ? (sop - so * sp / n) / Math.sqrt(va * vb) : -1
}
export function registrera(o, p, mask) {
  let bast = { s: 1, dx: 0, dy: 0, r: korr(o, p, mask, 1, 0, 0) }
  // grovt, sedan fint
  for (const [steg, sSteg, omr, sOmr] of [[0.01, 0.02, 0.08, 0.1], [0.0025, 0.005, 0.012, 0.02]]) {
    const b0 = { ...bast }
    for (let s = b0.s - sOmr; s <= b0.s + sOmr + 1e-9; s += sSteg) for (let dx = b0.dx - omr; dx <= b0.dx + omr + 1e-9; dx += steg) for (let dy = b0.dy - omr; dy <= b0.dy + omr + 1e-9; dy += steg) {
      const r = korr(o, p, mask, s, dx, dy)
      if (r > bast.r) bast = { s, dx, dy, r }
    }
  }
  return bast
}

async function personerPa(id, filer) {
  // persondetektorn i rekon/spar.js, på skivorna
  const dir = path.join(RUTOR, `${id}-plattor`)
  fs.rmSync(dir, { recursive: true, force: true })
  fs.mkdirSync(dir, { recursive: true })
  const namn = filer.map((f, k) => { const n = `${String(k + 1).padStart(5, '0')}.jpg`; fs.copyFileSync(f, path.join(dir, n)); return n })
  const page = await startaSida('rekon/spar.html', 'sparRedo')
  const r = await page.evaluate(a => window.spara(a), { bas: `/__ramar/rekon/${id}-plattor`, ramar: namn, fps: 10 })
  fs.rmSync(dir, { recursive: true, force: true })
  return r.ramar.map(f => f.personer.filter(p => p.s >= 0.45).length)
}

export async function stegPlatta(id, om) {
  const l2 = JSON.parse(fs.readFileSync(path.join(REKON, id, 'lokal-2d.json'), 'utf8'))
  const sr = JSON.parse(fs.readFileSync(path.join(REKON, id, 'spar-ra.json'), 'utf8'))
  const ramar = await rutor(id)
  let ore = 0
  const info = []
  for (const [i, sc] of l2.scener.entries()) {
    const ut = path.join(REKON, id, `platta-s${i}.jpg`)
    if (!om && fs.existsSync(ut)) continue
    const kalla = path.join(RUTOR, id, ramar[sc.ruta])
    const ra = path.join(REKON, id, `platta-s${i}.ra.jpg`) // obehandlad skiva, för felsökning
    // 1. tvätta, kontrollera, tvätta igen
    let bild = fs.readFileSync(kalla).toString('base64')
    let mime = 'image/jpeg'
    let kvar = null
    for (let varv = 0; varv < 3; varv++) {
      const r = await redigeraBild({ bild, mimeType: mime, text: varv === 0 ? TEXT : IGEN })
      ore += r.ore
      bild = r.data
      mime = r.mimeType
      fs.writeFileSync(ra + '.png', Buffer.from(bild, 'base64'))
      await kor(verktyg.ffmpeg, ['-v', 'error', '-y', '-i', ra + '.png', '-vf', 'scale=720:1280', '-q:v', '3', ra])
      fs.rmSync(ra + '.png')
      ;[kvar] = await personerPa(id, [ra])
      if (!kvar) break
    }
    // 2. registrera mot originalrutan (personernas rutor maskade)
    const o = await gra(kalla)
    const p = await gra(ra)
    const mask = new Uint8Array(W * H).fill(1)
    for (const pe of sr.ramar[sc.ruta]?.personer ?? []) {
      const [x0, y0, x1, y1] = pe.b
      for (let y = Math.floor(y0 * H) - 2; y <= Math.ceil(y1 * H) + 2; y++) for (let x = Math.floor(x0 * W) - 2; x <= Math.ceil(x1 * W) + 2; x++) if (x >= 0 && y >= 0 && x < W && y < H) mask[y * W + x] = 0
    }
    const reg = registrera(o, p, mask)
    // transformera: skala s kring mitten, förskjut (dx, dy) andelar av bilden
    const S = 720 * reg.s, T = 1280 * reg.s, PAD = 600
    const W2 = Math.round(S / 2) * 2, H2 = Math.round(T / 2) * 2
    const x0 = Math.round(PAD + (W2 - 720) / 2 - reg.dx * 720), y0 = Math.round(PAD + (H2 - 1280) / 2 - reg.dy * 1280)
    await kor(verktyg.ffmpeg, ['-v', 'error', '-y', '-i', ra, '-vf', `scale=${W2}:${H2},pad=${W2 + 2 * PAD}:${H2 + 2 * PAD}:${PAD}:${PAD}:color=gray,crop=720:1280:${x0}:${y0}`, '-q:v', '3', ut])
    info.push({ scen: i, personerKvar: kvar, registrering: { s: +reg.s.toFixed(4), dx: +reg.dx.toFixed(4), dy: +reg.dy.toFixed(4), r: +reg.r.toFixed(3) } })
  }
  if (info.length) fs.writeFileSync(path.join(REKON, id, 'platta.json'), JSON.stringify({ ore, info }, null, 1))
  console.log(`  platta: ${info.map(x => `s${x.scen} r ${x.registrering.r} (s ${x.registrering.s}, ${x.registrering.dx}, ${x.registrering.dy})${x.personerKvar ? ` · ${x.personerKvar} personer kvar` : ''}`).join(' · ')} · ${ore.toFixed(0)} öre`)
}
