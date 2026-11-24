// Den virtuella kameran i 2D: ett beskärningsfönster som rör sig över originalvideon. Originalets
// pixlar är basen (5 = originalet exakt); variationerna är kamerarörelser som en fotograf hade kunnat
// göra: zooma, åka in/ut, panorera, tilta, följa huvudpersonen, skaka (handhållet) eller lugna
// originalets skak (stabilisera). Rent och deterministiskt: samma uttryck och tid ger samma fönster.
//
// Fönstret: { cx, cy, z, rot } där (cx, cy) är mitten i originalets bild (0–1) och z zoomen (fönstret
// är 1/z av bilden på bredd och höjd, samma format). rot i grader.

export const ZOOM = [1, 1.15, 1.3, 1.5]
export const BANOR = [
  ['stilla', 0], ['in', 0.15], ['in', 0.3], ['ut', 0.15], ['ut', 0.3],
  ['pan_v', 0.08], ['pan_h', 0.08], ['tilt_u', 0.06], ['tilt_n', 0.06], ['folj', 0], ['stab', 0],
]
export const SKAK2D = [0, 0.3, 0.7]
export const ANKARE = ['mitt', 'person']

export const id2d = p => `2d|${p.zoom}|${p.bana}:${p.mangd}|${p.skak}|${p.ankare}`
export function parse2d(id) {
  const [, zoom, bana, skak, ankare] = id.split('~a')[0].split('|')
  const [b, m] = bana.split(':')
  return { zoom: Number(zoom), bana: b, mangd: Number(m), skak: Number(skak), ankare }
}
export const ar2d = id => typeof id === 'string' && id.startsWith('2d|')

export function* alla2d() {
  for (const zoom of ZOOM) for (const [bana, mangd] of BANOR) for (const skak of SKAK2D) for (const ankare of ANKARE) {
    // utan zoom är fönstret hela bilden och kan inte flytta sig: bara stilla och åka in är olika
    if (zoom === 1 && !['stilla', 'in'].includes(bana)) continue
    if (ankare === 'person' && zoom === 1 && bana !== 'in') continue
    if (bana === 'ut' && zoom - mangd < 1) continue // kan inte åka ut förbi originalets bild
    yield { zoom, bana, mangd, skak, ankare }
  }
}

const ease = x => (x < 0.5 ? 2 * x * x : 1 - (-2 * x + 2) ** 2 / 2)
// handhållet: summa av sinusar (deterministiskt), samma familj som 3D-kamerans skak
const skakv = (t, seed) => [
  Math.sin(t * 7.3 + seed) * 0.6 + Math.sin(t * 13.1 + seed * 2) * 0.3 + Math.sin(t * 2.1 + seed * 3) * 0.5,
  Math.sin(t * 6.1 + seed * 5) * 0.6 + Math.sin(t * 11.7 + seed * 7) * 0.3 + Math.sin(t * 1.7 + seed) * 0.5,
  Math.sin(t * 4.3 + seed * 11) * 0.7 + Math.sin(t * 9.9 + seed * 13) * 0.3,
]

// sammanhang för en scen: huvudpersonens mitt per ruta (för 'person' och 'folj'), och originalets
// kamerarörelse summerad (för 'stab'), båda i originalets bildkoordinater, med fps.
// { fps, n, person: [[x, y] | null], kamera: [[sx, sy]] } (sx, sy: innehållets förskjutning sedan scenens början)
export function fonster(p, u, dur, ctx = {}, seed = 1) {
  const fps = ctx.fps ?? 10
  const k = Math.max(0, Math.min((ctx.n ?? 1) - 1, Math.round(u * fps)))
  const f = Math.max(0, Math.min(1, u / Math.max(1e-6, dur)))
  let z = p.zoom
  let cx = 0.5, cy = 0.5
  // ankare: fönstret kring huvudpersonen (medel över scenen) i stället för bildens mitt
  if (p.ankare === 'person' && ctx.personMedel) { cx = ctx.personMedel[0]; cy = ctx.personMedel[1] }
  if (p.bana === 'in') z = p.zoom + p.mangd * ease(f)
  if (p.bana === 'ut') z = p.zoom - p.mangd * ease(f)
  if (p.bana === 'pan_v') cx -= p.mangd * (ease(f) - 0.5)
  if (p.bana === 'pan_h') cx += p.mangd * (ease(f) - 0.5)
  if (p.bana === 'tilt_u') cy -= p.mangd * (ease(f) - 0.5)
  if (p.bana === 'tilt_n') cy += p.mangd * (ease(f) - 0.5)
  if (p.bana === 'folj' && ctx.personJamn?.[k]) { cx = ctx.personJamn[k][0]; cy = ctx.personJamn[k][1] }
  if (p.bana === 'stab' && ctx.kameraSkak?.[k]) {
    // stabilisera: följ innehållets snabba förskjutning (originalets skak), så att den tar ut sig
    cx -= ctx.kameraSkak[k][0]
    cy -= ctx.kameraSkak[k][1]
  }
  let rot = 0
  if (p.skak) {
    const [a, b, c] = skakv(u, seed)
    const amp = (p.skak * 0.012) / z
    cx += a * amp
    cy += b * amp * 0.5625
    rot += c * p.skak * 0.8
  }
  // fönstret får aldrig gå utanför originalets bild
  const h = 0.5 / z
  cx = Math.max(h, Math.min(1 - h, cx))
  cy = Math.max(h, Math.min(1 - h, cy))
  return { cx, cy, z, rot }
}

// Originalets punkt (x, y) i fönstrets bild (0–1); utanför [0, 1] syns den inte.
export function iFonster(w, x, y) {
  let dx = (x - w.cx) * w.z, dy = (y - w.cy) * w.z
  if (w.rot) {
    const r = (-w.rot * Math.PI) / 180, c = Math.cos(r), s = Math.sin(r)
    const ax = dx * (16 / 9), nx = ax * c - dy * s, ny = ax * s + dy * c
    dx = nx * (9 / 16); dy = ny
  }
  return [dx + 0.5, dy + 0.5]
}

// Sammanhanget för en scen ur analysens rådata (sett.ramar för scenens rutor).
export function sammanhang(ramar, fps = 10) {
  const person = ramar.map(r => {
    const p = (r.personer ?? []).filter(x => x.bbox).sort((a, b) => (b.bbox[2] - b.bbox[0]) * (b.bbox[3] - b.bbox[1]) - (a.bbox[2] - a.bbox[0]) * (a.bbox[3] - a.bbox[1]))[0]
    if (!p) return null
    const lm = p.lm.flat ? p.lm.flat() : p.lm
    const [x0, y0, x1, y1] = p.bbox
    // huvudet och överkroppen väger mest: mitt mellan näsa och rutans mitt
    const nx = lm[0], ny = lm[1]
    return [((x0 + x1) / 2 + nx) / 2, ((y0 + y1) / 2 + ny) / 2]
  })
  const finns = person.filter(Boolean)
  const personMedel = finns.length ? [finns.reduce((a, p) => a + p[0], 0) / finns.length, finns.reduce((a, p) => a + p[1], 0) / finns.length] : null
  // jämn följning (fönster ±6 rutor), luckor fyllda med närmaste
  const personJamn = person.map((_, k) => {
    const nara = []
    for (let j = Math.max(0, k - 6); j <= Math.min(person.length - 1, k + 6); j++) if (person[j]) nara.push(person[j])
    return nara.length ? [nara.reduce((a, p) => a + p[0], 0) / nara.length, nara.reduce((a, p) => a + p[1], 0) / nara.length] : personMedel
  })
  // originalets kamera: innehållets summerade förskjutning, och den snabba delen (skaket) = summa − jämnad summa
  let sx = 0, sy = 0
  const sum = ramar.map((r, k) => { if (k > 0 && r.kamera) { sx += r.kamera.dx ?? 0; sy += r.kamera.dy ?? 0 } return [sx, sy] })
  const kameraSkak = sum.map((_, k) => {
    let ax = 0, ay = 0, n = 0
    for (let j = Math.max(0, k - 7); j <= Math.min(sum.length - 1, k + 7); j++) { ax += sum[j][0]; ay += sum[j][1]; n++ }
    return [sum[k][0] - ax / n, sum[k][1] - ay / n]
  })
  return { fps, n: ramar.length, personMedel, personJamn, kameraSkak }
}
