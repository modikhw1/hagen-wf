// Rendera ett rekonstruerat manus ruta för ruta (360×640, samma storlek som analysen tittar på),
// och projicera dockornas leder genom kameran, för att jämföra rörelserna direkt med originalets
// pose (rekon/jamfor.mjs). Körs av rekon/mat.mjs i Edge.
import * as THREE from 'three'
import { Spelare } from '../src/forandring/motor/spelare'
import { INDEX } from '../src/forandring/motor/skelett'

const W = 360
const H = 640
// MediaPipe-index → dockans led (näsan approximeras med huvudet)
const LEDER = { 0: 'head', 11: 'left_shoulder', 12: 'right_shoulder', 13: 'left_elbow', 14: 'right_elbow', 15: 'left_wrist', 16: 'right_wrist', 23: 'left_hip', 24: 'right_hip' }

let sp
window.renderaRekon = async ({ url, fps = 10 }) => {
  const manus = await (await fetch(url, { cache: 'no-store' })).json()
  if (!sp) sp = new Spelare(document.getElementById('c'), { bredd: W, hojd: H, pixelRatio: 1 })
  sp.pause()
  sp.load(manus)
  await sp.redo // rena skivor (texturer) måste vara laddade innan första rutan
  const n = Math.floor(sp.dur * fps + 1e-6)
  const bilder = []
  const projektioner = []
  const v = new THREE.Vector3()
  for (let k = 0; k < n; k++) {
    const t = k / fps
    sp.renderAt(t)
    bilder.push(document.getElementById('c').toDataURL('image/jpeg', 0.92))
    const p = {}
    for (const [r, d] of Object.entries(sp.dockor)) {
      const j = d.joints()
      const punkter = {}
      for (const [mp, led] of Object.entries(LEDER)) {
        // näsan: en punkt på huvudet (dockans näsa, se docka.js), inte huvudleden mitt i huvudet
        if (mp === '0') { d.bones[INDEX.head].updateMatrixWorld(true); v.set(0, 0.06 * d.skala, 0.12 * d.skala); d.bones[INDEX.head].localToWorld(v) } else v.copy(j[INDEX[led]])
        v.project(sp.cam)
        punkter[mp] = [Math.round(((v.x + 1) / 2) * 1000) / 1000, Math.round(((1 - v.y) / 2) * 1000) / 1000]
      }
      p[r] = { synlig: d.root.visible, punkter }
    }
    projektioner.push(p)
  }
  return { fps, langd: sp.dur, bilder, projektioner }
}
window.renderaRedo = Promise.resolve(true)
