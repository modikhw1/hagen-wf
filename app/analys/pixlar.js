// Bildens egna egenskaper per ruta, mätta på pixlarna (OpenCV.js). Samma funktion körs på riktiga
// klipp (analys/runner.js), på renderade manus (bryggan) och på uttrycksrummet (uttryck/matning.js),
// så att talen betyder samma sak överallt. Bilden skalas först till 90×160 gråskala: det räcker för
// helhetsmått och gör dem lika för alla källor oavsett upplösning.
//
//   energi    hur mycket bilden ändras sedan förra rutan (0–1); allt som rör sig, kamera och motiv
//   kant      andel kantpixlar (Canny): hur mycket som händer i bilden, detaljrikedom
//   symmetri  likhet mellan bilden och dess spegelbild (0–1): lugn, ordnad komposition
//   entropi   gråskalans spridning (0–1): visuell komplexitet
//   balans    hur långt bildens tyngdpunkt (kanterna) ligger från mitten (0–0,5)

export const W = 90
export const H = 160

export function forbered(cv, gra) {
  const m = new cv.Mat()
  cv.resize(gra, m, new cv.Size(W, H), 0, 0, cv.INTER_AREA)
  return m
}

export function pixelmatt(cv, liten, forra) {
  const n = W * H
  const d = liten.data
  // energi
  let energi = null
  if (forra) {
    const f = forra.data
    let s = 0
    for (let i = 0; i < n; i++) s += Math.abs(d[i] - f[i])
    energi = s / n / 255
  }
  // kanter och deras tyngdpunkt
  const kanter = new cv.Mat()
  cv.Canny(liten, kanter, 60, 140)
  const k = kanter.data
  let antal = 0
  let sx = 0
  let sy = 0
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (k[y * W + x]) { antal++; sx += x; sy += y }
  kanter.delete()
  const kant = antal / n
  const balans = antal ? Math.hypot(sx / antal / W - 0.5, sy / antal / H - 0.5) : 0
  // symmetri: medelavvikelse mot spegelbilden
  let avv = 0
  for (let y = 0; y < H; y++) for (let x = 0; x < W / 2; x++) avv += Math.abs(d[y * W + x] - d[y * W + (W - 1 - x)])
  const symmetri = 1 - avv / (n / 2) / 255
  // entropi i 32 nivåer
  const hist = new Array(32).fill(0)
  for (let i = 0; i < n; i++) hist[d[i] >> 3]++
  let ent = 0
  for (const h of hist) if (h) { const p = h / n; ent -= p * Math.log2(p) }
  const r3 = v => (v == null ? null : Math.round(v * 1000) / 1000)
  return { energi: r3(energi), kant: r3(kant), symmetri: r3(symmetri), entropi: r3(ent / 5), balans: r3(balans) }
}
