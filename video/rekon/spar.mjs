// Följning: personerna per ruta (rekon/spar.js) blir spår inom varje scen och identiteter över
// hela klippet. Rena funktioner, testade i spar.test.mjs.
//
// Inom en scen: girig matchning på överlapp (IoU) och närhet, med färgen som andra bevis.
// Luckor upp till LUCKA rutor fylls (rutan interpoleras, posen saknas och fylls senare av rörelsen).
// Över scener: spår med lika färger (överdel, hud, hår) slås ihop till samma person, men aldrig två
// spår som syns samtidigt.

export const LUCKA = 6
export const MIN_SPAR = 4 // rutor; kortare spår är oftast felträffar
const POSE_INOM = 0.6

const iou = (a, b) => {
  const x0 = Math.max(a[0], b[0]), y0 = Math.max(a[1], b[1]), x1 = Math.min(a[2], b[2]), y1 = Math.min(a[3], b[3])
  const i = Math.max(0, x1 - x0) * Math.max(0, y1 - y0)
  const u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
  return u > 0 ? i / u : 0
}
const mitt = b => [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]
const hex = h => (h ? [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16)) : null)
export const fargAvstand = (a, b) => {
  const A = hex(a), B = hex(b)
  if (!A || !B) return null
  // ungefär perceptuellt: viktad RGB (redmean)
  const r = (A[0] + B[0]) / 2
  const d = [A[0] - B[0], A[1] - B[1], A[2] - B[2]]
  return Math.sqrt((2 + r / 256) * d[0] ** 2 + 4 * d[1] ** 2 + (2 + (255 - r) / 256) * d[2] ** 2) / 765
}
const medianHex = lista => {
  const ok = lista.map(hex).filter(Boolean)
  if (!ok.length) return null
  const med = k => ok.map(c => c[k]).sort((a, b) => a - b)[ok.length >> 1]
  return '#' + [0, 1, 2].map(k => med(k).toString(16).padStart(2, '0')).join('')
}

// Två personer som överlappar (en räcker över disken) kan få samma pose: Pose på den enes
// utskurna bild låser på den andre. Två nästan lika poser blir en, och den hör till rutan vars
// mitt ligger närmast bålen; den andra rutan behåller sin plats men utan pose.
const balMitt = lm => {
  const pts = [11, 12, 23, 24].filter(i => lm[i][2] > 0.5)
  if (!pts.length) return [lm[0][0], lm[0][1]]
  return [pts.reduce((a, i) => a + lm[i][0], 0) / pts.length, pts.reduce((a, i) => a + lm[i][1], 0) / pts.length]
}
export function rensaRuta(personer) {
  const ut = personer.map(p => ({ ...p }))
  // en pose vars bål ligger närmare en annan rutas mitt än den egna hör till grannen
  const avstTill = (b, [x, y]) => Math.hypot(((b[0] + b[2]) / 2 - x) / Math.max(0.05, b[2] - b[0]), ((b[1] + b[3]) / 2 - y) / Math.max(0.05, b[3] - b[1]) * 0.5)
  for (const p of ut) {
    if (!p.lm) continue
    const c = balMitt(p.lm)
    const egen = avstTill(p.b, c)
    if (ut.some(q => q !== p && avstTill(q.b, c) < egen * 0.7)) { p.lm = null; p.varld = null }
  }
  for (let a = 0; a < ut.length; a++) for (let b = a + 1; b < ut.length; b++) {
    const A = ut[a].lm, B = ut[b].lm
    if (!A || !B) continue
    const gem = [0, 11, 12, 13, 14, 15, 16].filter(i => A[i][2] > 0.5 && B[i][2] > 0.5)
    if (gem.length < 3) continue
    const d = gem.reduce((s, i) => s + Math.hypot(A[i][0] - B[i][0], A[i][1] - B[i][1]), 0) / gem.length
    if (d > 0.04) continue
    const [bx, by] = balMitt(A)
    const avst = p => Math.hypot((p.b[0] + p.b[2]) / 2 - bx, ((p.b[1] + p.b[3]) / 2 - by) * 0.5)
    const forlorare = avst(ut[a]) <= avst(ut[b]) ? ut[b] : ut[a]
    forlorare.lm = null
    forlorare.varld = null
  }
  return ut
}

// Färger som inte kan stämma tas bort innan de räknas: hud ska se ut som hud (färgton och mättnad),
// och underdelens färg räknas bara när knäna syns, ligger under höften och inom personens ruta
// (annars provtas det personen håller, eller disken).
function hsv(h) {
  const [r, g, b] = hex(h).map(v => v / 255)
  const M = Math.max(r, g, b), m = Math.min(r, g, b), d = M - m
  let t = 0
  if (d) t = M === r ? ((g - b) / d) % 6 : M === g ? (b - r) / d + 2 : (r - g) / d + 4
  return [(t * 60 + 360) % 360, M ? d / M : 0, M]
}
export function rimligaFarger(p) {
  const f = { ...(p.farger ?? {}) }
  if (f.hud) { const [h, sat, v] = hsv(f.hud); if (!((h <= 50 || h >= 340) && sat >= 0.12 && sat <= 0.7 && v >= 0.2)) delete f.hud }
  // hår: provtas ovanför pannan och träffar lätt fönster eller vägg bakom; mycket ljust eller lika
  // överdelens färg räknas inte (ljust hår finns, men felträffarna är vanligare)
  if (f.har) { const [, sat, v] = hsv(f.har); if (v > 0.6 && sat < 0.3) delete f.har }
  const lm = p.lm
  const knan = lm && [25, 26].every(i => lm[i][2] >= 0.7 && lm[i][1] <= p.b[3] + 0.01 && lm[i][1] - lm[i - 2][1] > 0.05)
  if (!knan) delete f.underdel
  return f
}

// Kostnad att koppla en detektion till ett spår (lägre är bättre), eller Infinity.
function kostnad(spar, d, glapp) {
  const sist = spar.ramar[spar.ramar.length - 1]
  const o = iou(sist.b, d.b)
  const [ax, ay] = mitt(sist.b), [bx, by] = mitt(d.b)
  const w = Math.max(sist.b[2] - sist.b[0], d.b[2] - d.b[0])
  const dist = Math.hypot(ax - bx, (ay - by) * 0.6) / Math.max(0.05, w)
  if (o < 0.1 && dist > 0.6 + 0.15 * glapp) return Infinity
  const f = fargAvstand(spar.farg, d.farger?.overdel)
  return (1 - o) + 0.5 * dist + (f == null ? 0.15 : f * 1.5)
}

// Spår inom ett tidsintervall [i0, i1) av rutor.
export function sparIScen(ramar, i0, i1) {
  const spar = []
  let nasta = 0
  for (let i = i0; i < i1; i++) {
    const det = rensaRuta(ramar[i]?.personer ?? []).map(p => ({ ...p, farger: rimligaFarger(p), lm: p.lm && (p.inom ?? 1) >= POSE_INOM ? p.lm : null }))
    const levande = spar.filter(s => i - s.sist <= LUCKA)
    const par = []
    for (const s of levande) for (const [k, d] of det.entries()) {
      const c = kostnad(s, d, i - s.sist - 1)
      if (c < Infinity) par.push({ s, k, c })
    }
    par.sort((a, b) => a.c - b.c)
    const tagenS = new Set(), tagenD = new Set()
    for (const { s, k } of par) {
      if (tagenS.has(s) || tagenD.has(k)) continue
      tagenS.add(s); tagenD.add(k)
      const d = det[k]
      // fyll luckan med interpolerade rutor
      const sist = s.ramar[s.ramar.length - 1]
      for (let j = s.sist + 1; j < i; j++) {
        const f = (j - s.sist) / (i - s.sist)
        s.ramar.push({ i: j, b: sist.b.map((v, n) => v + (d.b[n] - v) * f), lm: null, varld: null, fylld: true })
      }
      s.ramar.push({ i, b: d.b, lm: d.lm, varld: d.lm ? d.varld : null, farger: d.farger })
      s.sist = i
      if (d.farger?.overdel) s.fargLista.push(d.farger.overdel)
      s.farg = medianHex(s.fargLista) ?? s.farg
    }
    for (const [k, d] of det.entries()) {
      if (tagenD.has(k)) continue
      spar.push({ nr: nasta++, forst: i, sist: i, ramar: [{ i, b: d.b, lm: d.lm, varld: d.lm ? d.varld : null, farger: d.farger }], fargLista: d.farger?.overdel ? [d.farger.overdel] : [], farg: d.farger?.overdel ?? null })
    }
  }
  return spar.filter(s => s.ramar.filter(r => !r.fylld).length >= Math.min(MIN_SPAR, Math.max(1, Math.floor((i1 - i0) / 3))))
}

// Sammanfattade färger för ett spår.
function sparFarger(s) {
  const per = k => medianHex(s.ramar.map(r => r.farger?.[k]).filter(Boolean))
  return { overdel: per('overdel'), underdel: per('underdel'), hud: per('hud'), har: per('har') }
}
function likhet(a, b) {
  const d = ['overdel', 'har', 'hud', 'underdel'].map((k, n) => [fargAvstand(a[k], b[k]), [1, 0.5, 0.3, 0.5][n]]).filter(([v]) => v != null)
  if (!d.length) return Infinity
  return d.reduce((s, [v, w]) => s + v * w, 0) / d.reduce((s, [, w]) => s + w, 0)
}
const overlappar = (a, b) => a.forst <= b.sist && b.forst <= a.sist

// Hela klippet: scener (rutintervall) → identiteter med spår per scen.
// Returnerar [{ id: 'p1', farger, storlek (median av rutans höjd), spar: [{ scen, ramar }] }].
export function identiteter(ramar, scener, { grans = 0.18 } = {}) {
  const alla = []
  for (const [si, sc] of scener.entries()) for (const s of sparIScen(ramar, sc.i0, sc.i1)) alla.push({ ...s, scen: si, farger: sparFarger(s) })
  // längst spår först: de är säkrast och blir identitetens ansikte utåt
  alla.sort((a, b) => b.ramar.length - a.ramar.length)
  const grupper = []
  for (const s of alla) {
    let bast = null
    for (const g of grupper) {
      if (g.spar.some(t => overlappar(t, s))) continue
      const l = likhet(g.farger, s.farger)
      if (l < grans && (!bast || l < bast.l)) bast = { g, l }
    }
    if (bast) { bast.g.spar.push(s); bast.g.farger = sammanslagna(bast.g.spar) }
    else grupper.push({ spar: [s], farger: s.farger })
  }
  // ordning: den som syns mest först
  const synlig = g => g.spar.reduce((a, s) => a + s.ramar.length, 0)
  grupper.sort((a, b) => synlig(b) - synlig(a))
  return grupper.map((g, n) => ({
    id: `p${n + 1}`,
    farger: g.farger,
    rutor: synlig(g),
    spar: g.spar.sort((a, b) => a.forst - b.forst).map(s => ({ scen: s.scen, forst: s.forst, sist: s.sist, ramar: s.ramar.map(({ farger, ...r }) => r) })),
  }))
}
function sammanslagna(spar) {
  const per = k => medianHex(spar.flatMap(s => s.ramar.map(r => r.farger?.[k])).filter(Boolean))
  return { overdel: per('overdel'), underdel: per('underdel'), hud: per('hud'), har: per('har') }
}
