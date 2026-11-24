// Mät 2D-uttrycken för ett riktigt klipp (kör: uttryck/kor2d.mjs). För varje scen och varje uttryck
// (manus/kamera2d.js) transformeras analysens rådata genom den virtuella kamerans fönster: poser,
// händer, saker, ansikten och kamerarörelse per ruta. Pixelmåtten mäts om på de beskurna rutorna
// (originalets rutor, 10/s, samma tidssteg som analysen). Sedan körs exakt samma tolkning och samma
// egenskaper som för originalet. Ingen detektor körs om: det som syns i fönstret är det originalet såg.
//
// Innehållsvakten skyddar det som bär innehållet, inte hela kroppen: ansiktena, händerna (det de håller:
// mat, pengar, verktyg) och huvudpersonens överkropp (huvud till bröst) ska ligga i bild i minst 95 % av
// rutorna; ben och bakgrund får beskäras. Zoomen får inte gå över källans upplösning (640 i höjd).
import { tolka } from '../analys/tolka.mjs'
import { scenEgenskaper } from '../kalibrering/egenskaper.mjs'
import { alla2d, id2d, fonster, iFonster, sammanhang, parse2d } from '../src/forandring/manus/kamera2d.js'
import cvModule from '@techstark/opencv-js'
import { forbered, pixelmatt } from '../analys/pixlar.js'

let cv
const cvRedo = (async () => {
  cv = cvModule instanceof Promise ? await cvModule : cvModule
  if (!cv.Mat) await new Promise(res => { cv.onRuntimeInitialized = res })
})()
const W = 90, H = 160
const yta = new OffscreenCanvas(W, H)
const g = yta.getContext('2d', { willReadFrequently: true })
const status = t => { document.getElementById('status').textContent = t }
const r3 = v => Math.round(v * 1000) / 1000

async function bild(url) {
  const r = await fetch(url)
  return r.ok ? createImageBitmap(await r.blob()) : null
}

// Rita fönstret ur originalrutan till 90×160 och ta fram den förberedda gråbilden.
function litenAv(bmp, w) {
  g.save()
  g.fillStyle = '#000'
  g.fillRect(0, 0, W, H)
  g.translate(W / 2, H / 2)
  g.rotate((-w.rot * Math.PI) / 180)
  g.scale(w.z, w.z)
  g.translate(-w.cx * W, -w.cy * H)
  g.drawImage(bmp, 0, 0, W, H)
  g.restore()
  const rgba = cv.matFromImageData(g.getImageData(0, 0, W, H))
  const gra = new cv.Mat()
  cv.cvtColor(rgba, gra, cv.COLOR_RGBA2GRAY)
  rgba.delete()
  const l = forbered(cv, gra)
  gra.delete()
  return l
}

const mapB = (w, b) => { const [x0, y0] = iFonster(w, b[0], b[1]); const [x1, y1] = iFonster(w, b[2], b[3]); return [x0, y0, x1, y1].map(r3) }
const andelInne = b => {
  const a = Math.max(1e-6, (b[2] - b[0]) * (b[3] - b[1]))
  const i = Math.max(0, Math.min(1, b[2]) - Math.max(0, b[0])) * Math.max(0, Math.min(1, b[3]) - Math.max(0, b[1]))
  return i / a
}

// Det som bär innehållet i en ruta: ansikten, händer och huvudpersonens överkropp.
function viktigaRutor(r) {
  const ut = (r.ansikten ?? []).filter(a => a.s >= 0.6).map(a => a.b)
  for (const h of r.hander ?? []) {
    const xs = [], ys = []
    for (let i = 0; i < h.lm.length; i += 2) { xs.push(h.lm[i]); ys.push(h.lm[i + 1]) }
    if (xs.length) ut.push([Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)])
  }
  const p = (r.personer ?? []).filter(q => q.bbox).sort((a, b) => (b.bbox[2] - b.bbox[0]) * (b.bbox[3] - b.bbox[1]) - (a.bbox[2] - a.bbox[0]) * (a.bbox[3] - a.bbox[1]))[0]
  if (p) { const [x0, y0, x1, y1] = p.bbox; ut.push([x0 + (x1 - x0) * 0.15, y0, x1 - (x1 - x0) * 0.15, y0 + (y1 - y0) * 0.45]) }
  return ut
}

// Rådatan för en ruta, sedd genom fönstret w (och förra fönstret wf för kamerarörelsen).
function genomFonster(r, w, wf) {
  const pt = (x, y) => iFonster(w, x, y).map(r3)
  const personer = (r.personer ?? []).map(p => {
    const lm = p.lm.flat ? p.lm : p.lm
    return { lm: lm.map(l => [...pt(l[0], l[1]), l[2]]), varld: p.varld, bbox: p.bbox ? mapB(w, p.bbox) : null }
  })
  const hander = (r.hander ?? []).map(h => {
    const lm = []
    for (let i = 0; i < h.lm.length; i += 2) lm.push(...pt(h.lm[i], h.lm[i + 1]))
    return { ...h, lm }
  })
  let kamera = r.kamera
  if (kamera && wf) {
    // innehållet i fönstret: originalets förskjutning förstorad med zoomen, minus fönstrets egen rörelse
    kamera = {
      ...kamera,
      dx: r3((kamera.dx ?? 0) * w.z - (w.cx - wf.cx) * w.z),
      dy: r3((kamera.dy ?? 0) * w.z - (w.cy - wf.cy) * w.z),
      rot: r3((kamera.rot ?? 0) - (w.rot - wf.rot)),
      skala: r3((kamera.skala ?? 1) * (w.z / wf.z)),
    }
  }
  return {
    t: r.t, personer, hander, kamera,
    saker: (r.saker ?? []).map(s => ({ ...s, b: mapB(w, s.b) })),
    ansikten: (r.ansikten ?? []).map(a => ({ ...a, b: mapB(w, a.b) })),
  }
}

window.mat2d = async ({ id, scen, max = Infinity }) => {
  await cvRedo
  const ra = await (await fetch(`/__data/ra/${id}.json`, { cache: 'no-store' })).json()
  const an = await (await fetch(`/__data/analys/${id}.json`, { cache: 'no-store' })).json()
  const fps = ra.fps
  const maxZoom = (ra.meta?.hojd ?? 1024) / 640
  const ut = []
  for (const [i, sc] of an.scener.entries()) {
    if (scen != null && i !== scen) continue
    const t0 = performance.now()
    const k0 = Math.round(sc.start * fps), k1 = Math.min(ra.sett.ramar.length, Math.max(k0 + 2, Math.round(sc.slut * fps)))
    const ramar = ra.sett.ramar.slice(k0, k1)
    const bilder = await Promise.all(ramar.map((_, j) => bild(`/__data/ra/${id}/${ra.nyckel[k0 + j]}`)))
    const ctx = sammanhang(ramar, fps)
    const dur = (k1 - k0) / fps
    const uttryck = []
    const lista = [{ id: 'original', p: null }, ...[...alla2d()].map(p => ({ id: id2d(p), p }))]
    let n = 0
    const sedda = new Set() // fönsterbanor som redan mätts: samma bana är samma bild, oavsett id
    for (const x of lista) {
      if (n++ > max) break
      const fon = ramar.map((_, j) => (x.p ? fonster(x.p, j / fps, dur, ctx, i + 1) : { cx: 0.5, cy: 0.5, z: 1, rot: 0 }))
      const sig = fon.map(w => [w.cx, w.cy, w.z, w.rot].map(v => v.toFixed(3)).join(',')).join(';')
      if (sedda.has(sig)) continue
      sedda.add(sig)
      // vakt
      let okRutor = 0, medInnehall = 0
      for (const [j, r] of ramar.entries()) {
        const viktiga = viktigaRutor(r)
        if (!viktiga.length) continue
        medInnehall++
        // det som syntes i originalet ska synas i fönstret (det som redan var delvis utanför räknas för sig)
        if (viktiga.every(b => andelInne(mapB(fon[j], b)) >= 0.95 * andelInne(b))) okRutor++
      }
      const vakt = medInnehall ? okRutor / medInnehall : 1
      const zMax = Math.max(...fon.map(w => w.z))
      const giltig = x.id === 'original' || (vakt >= 0.95 && zMax <= maxZoom + 1e-6)
      // rådata genom fönstret, pixlar mätta om
      const nya = []
      let forra = null
      for (const [j, r] of ramar.entries()) {
        const f = genomFonster(r, fon[j], j ? fon[j - 1] : null)
        f.t = r3(j / fps)
        if (bilder[j]) {
          const l = litenAv(bilder[j], fon[j])
          f.pix = pixelmatt(cv, l, forra)
          forra?.delete()
          forra = l
        }
        nya.push(f)
      }
      forra?.delete()
      const a = tolka({ id: 'u', meta: { langd: dur, bredd: 360, hojd: 640, fps }, kandidater: [], sett: { ramar: nya, kandidater: [] }, fps })
      const s = a.scener[0]
      uttryck.push({ id: x.id, e: Object.fromEntries(Object.entries(scenEgenskaper(s)).map(([k, v]) => [k, v == null ? null : r3(v)])), ord: s.kamera.ord, utsnitt: s.utsnitt.varde, giltig, vakt: r3(vakt), zMax: r3(zMax) })
      if (n % 40 === 0) { status(`scen ${i + 1}: ${n}/${lista.length}`); await new Promise(r => setTimeout(r, 0)) }
    }
    bilder.forEach(b => b?.close())
    ut.push({ i, text: null, antal: uttryck.length, giltiga: uttryck.filter(u => u.giltig).length, ms: Math.round(performance.now() - t0), uttryck })
  }
  return { id, fps, maxZoom: r3(maxZoom), scener: ut }
}
window.mat2dRedo = cvRedo.then(() => true)

// Rendera en scen genom ett 2D-uttryck till JPEG-rutor (360×640, originalets 10 rutor/s): för
// maskindomaren (kalibrering/domare2d.mjs), som ser varianterna som video.
const stor = new OffscreenCanvas(360, 640)
const sg = stor.getContext('2d')
window.rendera2d = async ({ id, scen, uttryck }) => {
  const ra = await (await fetch(`/__data/ra/${id}.json`)).json()
  const an = await (await fetch(`/__data/analys/${id}.json`)).json()
  const fps = ra.fps, sc = an.scener[scen]
  const k0 = Math.round(sc.start * fps), k1 = Math.min(ra.sett.ramar.length, Math.max(k0 + 2, Math.round(sc.slut * fps)))
  const ramar = ra.sett.ramar.slice(k0, k1)
  const ctx = sammanhang(ramar, fps)
  const dur = (k1 - k0) / fps
  const p = uttryck && uttryck.startsWith('2d|') ? parse2d(uttryck) : null
  const ut = []
  for (let j = 0; j < ramar.length; j++) {
    const bmp = await bild(`/__data/ra/${id}/${ra.nyckel[k0 + j]}`)
    if (!bmp) continue
    const w = p ? fonster(p, j / fps, dur, ctx, scen + 1) : { cx: 0.5, cy: 0.5, z: 1, rot: 0 }
    sg.save(); sg.fillStyle = '#000'; sg.fillRect(0, 0, 360, 640)
    sg.translate(180, 320); sg.rotate((-w.rot * Math.PI) / 180); sg.scale(w.z, w.z); sg.translate(-w.cx * 360, -w.cy * 640)
    sg.drawImage(bmp, 0, 0, 360, 640); sg.restore()
    bmp.close()
    const blob = await stor.convertToBlob({ type: 'image/jpeg', quality: 0.9 })
    ut.push(await new Promise(res => { const r = new FileReader(); r.onload = () => res(r.result); r.readAsDataURL(blob) }))
  }
  return { fps, bilder: ut }
}
