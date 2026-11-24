// Ett påhittat klipp. Miljö, rekvisita, personal och handling är låsta.
// Det enda som rör sig är scenografin: kamerans plats, utsnitt, vinkel, rörelse och övergång.

// Världen är lokalen, ritad en gång. Kameran tittar in i den. Koordinater i världens pixlar.
export const WORLD = { w: 400, h: 300 }
export const BASE_CAM = { cx: 205, cy: 165, z: 1 } // stativet på steg 1: samma utsnitt i alla scener

export const CLIP = {
  name: 'Nonna smakar',
  kund: 'Fratelli',
  orig: [6, 5, 8, 9, 7], // originalets scenografi per scen, 1–10
  scenes: [
    {
      text: 'Marco knådar degen',
      pose: { marco: { x: 245, arms: 'knead' } },
      detail: [245, 176],
      grepp: { z: 4.2, rx: 38, ry: 0, dutch: 0, move: 'push', trans: 'rak' },
    },
    {
      text: 'Nonna kommer in',
      pose: { marco: { x: 245, arms: 'rest' }, nonna: { x: 150, arms: 'cross' } },
      detail: [150, 140],
      grepp: { z: 2.4, rx: 0, ry: -32, dutch: -8, move: 'pan', trans: 'whip' },
    },
    {
      text: 'Marco räcker fram en bit',
      pose: { marco: { x: 238, arms: 'offer' }, nonna: { x: 172, arms: 'rest' } },
      detail: [204, 150],
      grepp: { z: 3, rx: -16, ry: 26, dutch: 0, move: 'hand', trans: 'match' },
    },
    {
      text: 'Nonna smakar',
      pose: { marco: { x: 238, arms: 'rest' }, nonna: { x: 172, arms: 'eat' } },
      detail: [172, 124],
      grepp: { z: 5, rx: -10, ry: 0, dutch: 10, move: 'push', trans: 'zoom' },
    },
    {
      text: 'Tummen upp',
      pose: { marco: { x: 238, arms: 'up' }, nonna: { x: 172, arms: 'thumb' } },
      detail: [205, 155],
      grepp: { z: 1.7, rx: -22, ry: -20, dutch: -5, move: 'orbit', trans: 'whip' },
    },
  ],
}

export const S0 = Math.round(CLIP.orig.reduce((a, b) => a + b, 0) / CLIP.orig.length) // 7

const clamp = (v, a, b) => Math.max(a, Math.min(b, v))
const lerp = (a, b, t) => a + (b - a) * t

// Reglaget flyttar originalets kurva. Vid ändarna plattas den ut: på 1 och 10 är alla scener lika.
export function curve(s) {
  const span = s < S0 ? S0 - 1 : 10 - S0
  const f = span ? ((s - S0) / span) ** 2 : 0
  return CLIP.orig.map(o => clamp(s + (o - S0) * (1 - f), 1, 10))
}

// En scens scenografi vid intensitet v (1–10). a = 0 är stativet, a = 1 är scenens fulla grepp.
export function shot(scene, v) {
  const a = (v - 1) / 9
  const g = scene.grepp
  return {
    v,
    cx: lerp(BASE_CAM.cx, scene.detail[0], a),
    cy: lerp(BASE_CAM.cy, scene.detail[1], a),
    z: BASE_CAM.z * g.z ** a,
    rx: g.rx * a,
    ry: g.ry * a,
    dutch: g.dutch * a,
    move: v < 3 ? 'still' : v < 6 ? 'drift' : g.move,
    amp: a,
    trans: v < 4 ? 'rak' : v < 7 ? 'mjuk' : g.trans,
  }
}

export const shotsAt = s => curve(s).map((v, i) => shot(CLIP.scenes[i], v))
