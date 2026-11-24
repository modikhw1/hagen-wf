// Bryggans webbläsardel: renderar ett manus till bildrutor (360×640, samma storlek som analysen
// tittar på) och räknar samtidigt motorns egen syn för samma tidpunkter, inklusive pixelmåtten
// (samma funktion som analysen; motorns sida mäter den orenderade, okomprimerade bilden).
import { Spelare, langd } from '../src/forandring/motor/spelare'
import { skapaSyn, sattHandMin } from '../src/forandring/motor/syn'
import { ORIGINAL } from '../src/forandring/manus/nonna-smakar'
import { allaVerkligheter } from '../src/forandring/manus/regissor'
import cvModule from '@techstark/opencv-js'
import { forbered, pixelmatt } from '../analys/pixlar.js'

const W = 360
const H = 640
const V = allaVerkligheter(ORIGINAL)
export const MANUS = Object.fromEntries(Object.entries(V).map(([k, m]) => [`nonna-v${k}`, m]))

let cv
const cvRedo = (async () => {
  cv = cvModule instanceof Promise ? await cvModule : cvModule
  if (!cv.Mat) await new Promise(res => { cv.onRuntimeInitialized = res })
})()
const yta = new OffscreenCanvas(W, H)
const ytaG = yta.getContext('2d', { willReadFrequently: true })

let sp
function spelare() {
  if (!sp) sp = new Spelare(document.getElementById('c'), { bredd: W, hojd: H, pixelRatio: 1 })
  return sp
}

window.bryggManus = () => Object.keys(MANUS)

// Rendera ett manus: bilder (JPEG) och syn per ruta, plus scengränserna (facit).
window.renderaManus = async ({ id, fps = 10, handMin }) => {
  await cvRedo
  const m = MANUS[id]
  if (!m) throw new Error(`okänt manus ${id}`)
  if (handMin) sattHandMin(handMin)
  const s = spelare()
  s.pause()
  s.load(m)
  const L = langd(m)
  const n = Math.floor(L * fps + 1e-6)
  const bilder = []
  const syn = skapaSyn(s)
  const ramar = []
  let forra = null
  for (let k = 0; k < n; k++) {
    const t = k / fps
    s.renderAt(t)
    const c = document.getElementById('c')
    bilder.push(c.toDataURL('image/jpeg', 0.92))
    ytaG.drawImage(c, 0, 0)
    const rgba = cv.matFromImageData(ytaG.getImageData(0, 0, W, H))
    const gra = new cv.Mat()
    cv.cvtColor(rgba, gra, cv.COLOR_RGBA2GRAY)
    rgba.delete()
    const liten = forbered(cv, gra)
    gra.delete()
    const pix = pixelmatt(cv, liten, forra)
    forra?.delete()
    forra = liten
    ramar.push({ ...syn(t), pix })
  }
  forra?.delete()
  const granser = s.tl.slice(1).map(x => ({ t: Math.round(x.start * 1000) / 1000, typ: x.in?.typ ?? 'klipp' }))
  return { id, langd: L, fps, bilder, syn: ramar, granser, scener: s.tl.map(x => ({ start: x.start, slut: x.slut })), manus: m }
}
window.bryggRedo = cvRedo.then(() => true)
