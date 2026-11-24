// Uttrycksrummet: alla sätt att filma en scen, med innehållet låst. Bara kameran varierar:
// utsnitt × vinkel × höjd × rörelse (med mängd) × skak. Det blir 7 875 uttryck per scen.
// Uttrycken förrenderas inte; motorn spelar vilket som helst direkt. De mäts en gång med motorns
// syn (npm run uttrycksrum) och placeras på vertikalen när reglaget används.

export const UTSNITT = ['total', 'halvtotal', 'halvbild', 'nara', 'extrem']
export const VINKLAR = [-50, -35, -20, 0, 20, 35, 50]
export const HOJDER = [-18, -8, 0, 10, 22]
export const RORELSER = [
  ['static', 0],
  ['dolly', 0.2], ['dolly', 0.5],
  ['pan', 12], ['pan', 30],
  ['truck', 0.15], ['truck', 0.35],
  ['arc', 20], ['arc', 45],
  ['zoom', 0.2], ['zoom', 0.5],
  ['tilt', 8], ['tilt', 18],
  ['pedestal', 0.15], ['pedestal', 0.35],
]
export const SKAK = [0, 0.3, 0.7]

// Rekonstruerade klipp: världen finns bara sedd från originalkamerans håll, så uttrycken är relativa
// till den: vinkel och höjd är avvikelser (grader) från originalets riktning mot huvudpersonen, och
// utsnittet skalar originalets avstånd. Täckningen (uttryck/matning.js) avgör sedan vad som håller.
export const VINKLAR_REKON = [-15, -8, 0, 8, 15]
export const HOJDER_REKON = [-6, 0, 6]
// Modellerad scen (ingen fotoprojektion): världen finns runt om, så vinklarna kan vara bredare.
export const VINKLAR_MODELL = [-35, -20, -8, 0, 8, 20, 35]
export const HOJDER_MODELL = [-10, 0, 10]
export function* rekonUttryck({ bred = false } = {}) {
  for (const utsnitt of UTSNITT) for (const vinkel of bred ? VINKLAR_MODELL : VINKLAR_REKON) for (const hojd of bred ? HOJDER_MODELL : HOJDER_REKON)
    for (const [rorelse, mangd] of RORELSER) for (const skak of [0, 0.3])
      yield { utsnitt, vinkel, hojd, rorelse, mangd, skak }
}

// Agerandet (amp): hur stort personerna rör sig, relativt originalet. Bara för rekonstruerade klipp,
// där rörelserna är riktiga: samma scen men lugnare (0,6) eller mer energisk (1,4).
export const AMP = [0.5, 0.7, 0.85, 1, 1.2, 1.4, 1.7]

// Id: kamerans del, eller 'original' för originalets kamera, och ~a<amp> om agerandet ändrats.
export const kameraId = p => `${p.utsnitt}|${p.vinkel}|${p.hojd}|${p.rorelse}:${p.mangd}|${p.skak}`
// ~b1: en statist går förbi i bakgrunden (iscensättning: det som händer runt personerna)
export const uttryckId = (p, amp = 1, bakgrund = 0) => `${p ? kameraId(p) : 'original'}${amp !== 1 ? `~a${amp}` : ''}${bakgrund ? `~b${bakgrund}` : ''}`
// Delar ett id i kamera (null = originalets) och amp.
export function delaId(id) {
  const [k, ...till] = String(id ?? 'original').split('~')
  const varde = c => { const t = till.find(x => x[0] === c); return t ? Number(t.slice(1)) : null }
  // 2D-uttryck (virtuell kamera på originalvideon, manus/kamera2d.js) är ingen 3D-kamera
  const tva = k.startsWith('2d|') ? k : null
  return { kamera: k === 'original' || tva || k.split('|').length !== 5 ? null : parseId(k), amp: varde('a') ?? 1, bakgrund: varde('b') ?? 0, tva }
}
export function parseId(id) {
  id = id.split('~')[0]
  const [utsnitt, vinkel, hojd, ror, skak] = id.split('|')
  const [rorelse, mangd] = ror.split(':')
  return { utsnitt, vinkel: Number(vinkel), hojd: Number(hojd), rorelse, mangd: Number(mangd), skak: Number(skak) }
}

export function* allaUttryck() {
  for (const utsnitt of UTSNITT) for (const vinkel of VINKLAR) for (const hojd of HOJDER)
    for (const [rorelse, mangd] of RORELSER) for (const skak of SKAK)
      yield { utsnitt, vinkel, hojd, rorelse, mangd, skak }
}

// Kameran för ett uttryck i en given scen. Målet följer regissörens regler: närbilder siktar på
// huvudpersonens huvud, och rör sig någon i scenen följer kameran med (annars filmar den tomrum).
export function kameraFor(sc, p) {
  const huvud = sc.kamera.mal?.roll ?? sc.handling[0].roll
  const nara = p.utsnitt === 'nara' || p.utsnitt === 'extrem'
  const mal = nara ? { roll: huvud, led: 'head' } : sc.kamera.mal
  // följ med om någon rör sig: en väg, eller en rekonstruerad bana som flyttar sig mer än 30 cm
  const flyttar = h => {
    if (h.vag) return true
    const B = h.bana?.ramar
    return !!B && B.some(b => Math.hypot(b[0] - B[0][0], b[1] - B[0][1]) > 0.3)
  }
  const folj = (sc.kamera.ops ?? []).some(o => o.op === 'tracking') || sc.handling.some(flyttar)
  const ops = p.rorelse === 'static' ? [] : [{ op: p.rorelse, mangd: p.mangd }]
  if (folj) ops.push({ op: 'tracking', mangd: 0.9 })
  if (sc.kamera.bana) return relativKamera(sc, p, mal, ops)
  return { utsnitt: p.utsnitt, mal, vinkel: p.vinkel, hojd: p.hojd, skak: p.skak, ops, lins: sc.kamera.lins }
}

// Originalets eget uttryck, så att det kan ligga i rummet och vara 5 på skalan.
export function originalUttryck(sc) {
  const k = sc.kamera
  const op = (k.ops ?? []).find(o => o.op !== 'tracking')
  return { utsnitt: k.utsnitt, vinkel: k.vinkel ?? 0, hojd: k.hojd ?? 0, rorelse: op?.op ?? 'static', mangd: op?.mangd ?? 0, skak: k.skak ?? 0, original: true }
}

// Originalkamerans läge vid scenens början relativt huvudpersonen (bröst, 1,3 m), som riktning
// (gir, höjdvinkel) och avstånd; uttrycket läggs ovanpå: vinkel och höjd som avvikelser, utsnittet
// som skala på avståndet (relativt originalets utsnitt).
function relativKamera(sc, p, mal, ops) {
  const b = sc.kamera.bana.ramar[0]
  const h = sc.handling.find(x => x.roll === (sc.kamera.mal?.roll ?? sc.handling[0]?.roll)) ?? sc.handling[0]
  const tx = h?.bana?.ramar?.[0]?.[0] ?? b[0], tz = h?.bana?.ramar?.[0]?.[1] ?? b[2] - 2, ty = 1.3
  const dx = b[0] - tx, dz = b[2] - tz, dy = b[1] - ty
  const horis = Math.hypot(dx, dz)
  const gir = Math.atan2(dx, dz) * 180 / Math.PI
  const elev = Math.atan2(dy, horis) * 180 / Math.PI
  const avst = Math.hypot(horis, dy)
  const skalning = (UTSNITT_HOJD[p.utsnitt] ?? 1) / (UTSNITT_HOJD[sc.kamera.utsnitt] ?? UTSNITT_HOJD.halvbild)
  return { utsnitt: p.utsnitt, mal, vinkel: gir + p.vinkel, hojd: elev + p.hojd, skak: p.skak, ops, lins: sc.kamera.lins, dist: Math.max(0.4, avst * skalning) }
}
// samma tal som motor/kamera.js UTSNITT (hur mycket som syns på höjden); här för att slippa importera three
const UTSNITT_HOJD = { total: 3.3, halvtotal: 1.95, halvbild: 1.2, nara: 0.62, extrem: 0.3 }
