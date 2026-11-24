// Tolka: från mätningar och det som setts till scener, komposition, kamera och rörelse.
// Rena funktioner, inga filer, så att de kan testas och flyttas in i hagen-uis ingest.
//
// Gränser och var de kommer ifrån (kalibreras mot rättelser i data/rattelser):
// - HARD 0,3: samma tröskel som hagen-ui använder för klipp (DEFAULT_SCENE_THRESHOLD).
// - SAMMA_*: samma uppställning före och efter ett klipp. Satt efter tre klipp 2026-10-31:
//   riktiga scenbyten gav 0,03–0,04, hoppklipp och zoomryck 0,11–0,25.
// - ZOOMRYCK: |ln skala| över 0,05, alltså mer än cirka 5 % inzoomning i ett klipp.
// - MIN_SCEN 0,5 s: kortare bitar är dynamik (inskott) och slås ihop med grannen.
// - Övergång: en svag kandidat (under HARD) där bilden en halv sekund före och efter inte är
//   samma uppställning. Tonade övergångar och whip sprids över flera rutor och syns inte som ett
//   starkt klipp mellan två grannrutor. Hittat med bryggan (renderade övergångar missades).

export const VERSION = 13

// Ryck: medel av |andra differensen| delat med medel av |första|, över sammanhängande rutor
// (null bryter). 0 = helt jämn rörelse, högre = hackigare. Under ett golv i fart räknas det inte.
export function ryck(serie) {
  const d1 = []
  const d2 = []
  for (let i = 2; i < serie.length; i++) {
    const [a, b, c] = [serie[i - 2], serie[i - 1], serie[i]]
    if (!a || !b || !c) continue
    d1.push(Math.hypot(c[0] - b[0], c[1] - b[1]) + Math.hypot(b[0], b[1]))
    d2.push(Math.hypot(c[0] - 2 * b[0] + a[0], c[1] - 2 * b[1] + a[1]))
  }
  if (d2.length < 3) return null
  const m = arr => arr.reduce((s, x) => s + x, 0) / arr.length
  const fart = m(d1)
  if (fart < 0.004) return 0
  return Math.round((m(d2) / fart) * 1000) / 1000
}
export const GRANSER = { KAMERA_INL: 0.4, KAMERA_N: 30, HARD: 0.3, SAMMA_ANDEL: 0.08, SAMMA_INLIERS: 20, ZOOMRYCK: 0.05, MIN_SCEN: 0.5, SLA_IHOP: 0.15 }

const r3 = v => Math.round(v * 1000) / 1000
const median = a => { if (!a.length) return null; const s = a.slice().sort((x, y) => x - y); return s[Math.floor(s.length / 2)] }
const medel = a => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : 0)

// MediaPipe-punkter (33)
const P = { nasa: 0, vOga: 2, hOga: 5, vAxel: 11, hAxel: 12, vHoft: 23, hHoft: 24, vKna: 25, hKna: 26, vFot: 27, hFot: 28, vTa: 31, hTa: 32 }

// ---------- klipp ----------
export function klassaKlipp(kandidater, jamforelser, G = GRANSER) {
  const ut = []
  kandidater.forEach((k, i) => {
    const j = jamforelser[i] ?? {}
    const prev = ut[ut.length - 1]
    if (prev && k.t - prev.t < G.SLA_IHOP) { if (k.styrka > prev.styrka) Object.assign(prev, { t: k.t, styrka: k.styrka }); return }
    const samma = (j.inliers ?? 0) >= G.SAMMA_INLIERS && (j.inl ?? 0) >= G.SAMMA_ANDEL
    const lnS = j.skala ? Math.log(j.skala) : 0
    const vid = j.vid
    const vidSamma = vid && (vid.inliers ?? 0) >= G.SAMMA_INLIERS && (vid.inl ?? 0) >= G.SAMMA_ANDEL
    const typ = samma ? (Math.abs(lnS) >= G.ZOOMRYCK ? 'zoomryck' : 'hopp') : k.styrka >= G.HARD ? 'scen' : vid && !vidSamma ? 'overgang' : 'svag'
    ut.push({ t: k.t, styrka: k.styrka, typ, likhet: { andel: j.inl ?? 0, inliers: j.inliers ?? 0, skala: j.skala ?? null, vid: vid ? { andel: vid.inl ?? 0, inliers: vid.inliers ?? 0 } : null } })
  })
  return ut
}

// Scener ur klippen. Bitar kortare än MIN_SCEN slås ihop med föregående (eller nästa) scen,
// och klippet som avgränsade dem blir 'inskott'.
export function scenindelning(langd, klipp, G = GRANSER) {
  const granser = klipp.filter(k => k.typ === 'scen' || k.typ === 'overgang').map(k => k.t)
  let bitar = [0, ...granser, langd].slice(0, -1).map((s, i, a) => ({ start: s, slut: i + 1 < a.length ? a[i + 1] : langd }))
  let andrat = true
  while (andrat && bitar.length > 1) {
    andrat = false
    const i = bitar.findIndex(b => b.slut - b.start < G.MIN_SCEN)
    if (i < 0) break
    const k = i > 0 ? i - 1 : i
    const sam = { start: bitar[k].start, slut: bitar[k + 1].slut }
    const grans = bitar[k].slut
    const kl = klipp.find(x => Math.abs(x.t - grans) < 1e-6)
    if (kl) kl.typ = 'inskott'
    bitar = [...bitar.slice(0, k), sam, ...bitar.slice(k + 2)]
    andrat = true
  }
  return bitar.map((b, i) => {
    const inne = klipp.filter(k => k.t > b.start + 1e-6 && k.t < b.slut - 1e-6 && k.typ !== 'svag')
    return { i, start: r3(b.start), slut: r3(b.slut), langd: r3(b.slut - b.start), dynamik: inne.map(k => ({ t: k.t, typ: k.typ })), montage: inne.filter(k => k.typ === 'inskott').length >= 2 }
  })
}

// ---------- personer ----------
// En kropp från Pose räknas bara med ett andra, oberoende bevis: objektdetektorn ser en person på
// samma ställe, eller ansiktsdetektorn ser ett ansikte vid kroppens huvud. Pose hittar falska
// kroppar i mat och skyltar med synlighet 0,95–1,0; storleken skiljer dem inte från riktiga
// personer (granskat 2026-10-31: 150 stora avvisade var både riktiga och falska), men ansikten
// uppstår nästan aldrig i mat. Sista undantaget: stor kropp med säker näsa (extrem närbild).
const snitt = (a, b) => Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]))
const yta = b => Math.max(1e-6, (b[2] - b[0]) * (b[3] - b[1]))
export function arPerson(p, saker, ansikten) {
  const b = p.bbox ?? p.b
  if (saker?.some(d => d.k === 'person' && d.s >= 0.35 && snitt(b, d.b) / yta(b) >= 0.5)) return true
  const lmA = p.lm.flat ? p.lm.flat() : p.lm
  const [nx, ny] = [lmA[0], lmA[1]]
  if (ansikten?.some(a => { const px = (a.b[2] - a.b[0]) * 0.4; const py = (a.b[3] - a.b[1]) * 0.4; return nx >= a.b[0] - px && nx <= a.b[2] + px && ny >= a.b[1] - py && ny <= a.b[3] + py })) return true
  const lm = p.lm.flat ? p.lm.flat() : p.lm
  return (Math.min(1, b[3]) - Math.max(0, b[1])) >= 0.55 && lm[2] > 0.8
}
export const SAKER_SV = { person: 'person', pizza: 'pizza', 'dining table': 'bord', bowl: 'skål', cup: 'kopp', 'wine glass': 'vinglas', bottle: 'flaska', fork: 'gaffel', knife: 'kniv', spoon: 'sked', cake: 'tårta', sandwich: 'smörgås', 'hot dog': 'korv', donut: 'munk', oven: 'ugn', chair: 'stol', 'cell phone': 'mobil', bench: 'bänk', laptop: 'dator', 'potted plant': 'växt', vase: 'vas', clock: 'klocka', handbag: 'väska', tv: 'tv', couch: 'soffa', broccoli: 'broccoli', carrot: 'morot', orange: 'apelsin', banana: 'banan', apple: 'äpple', sink: 'diskho', refrigerator: 'kylskåp', microwave: 'mikro', toaster: 'brödrost', book: 'bok' }
const inne = (lm, i, marg = 0.02) => {
  const [x, y, v] = [lm[i * 3], lm[i * 3 + 1], lm[i * 3 + 2]]
  return v > 0.5 && x >= -marg && x <= 1 + marg && y >= -marg && y <= 1 + marg
}
export function utsnittFor(lm) {
  if ([P.vFot, P.hFot, P.vTa, P.hTa].some(i => inne(lm, i))) return 'total'
  if ([P.vKna, P.hKna].some(i => inne(lm, i))) return 'halvtotal'
  if ([P.vHoft, P.hHoft].some(i => inne(lm, i))) return 'halvbild'
  if ([P.vAxel, P.hAxel].some(i => inne(lm, i))) return 'nara'
  if ([P.nasa, P.vOga, P.hOga].some(i => inne(lm, i))) return 'extrem'
  return null
}
// Kroppens vridning mot kameran ur 3D-punkterna (axellinjen). 0 = rakt mot kameran, 90 = profil.
// MediaPipe skiljer dåligt på fram och bak, så 'bakifrån' är osäkert.
export function vridning(v) {
  if (!v?.length) return null
  const dx = v[P.vAxel * 3] - v[P.hAxel * 3]
  const dz = v[P.vAxel * 3 + 2] - v[P.hAxel * 3 + 2]
  return Math.abs((Math.atan2(dz, dx) * 180) / Math.PI)
}
const vridOrd = g => (g == null ? null : g < 35 ? 'framifrån' : g < 65 ? 'snett' : g < 115 ? 'profil' : 'bakifrån')

// Personer följs mellan rutor inom en scen: närmaste rutmitt, annars ny person.
function folj(ramar, fran, till) {
  let nasta = 0
  let forra = []
  for (let n = fran; n < till; n++) {
    const nu = ramar[n].p
    const tagna = new Set()
    for (const p of nu) {
      const c = [(p.b[0] + p.b[2]) / 2, (p.b[1] + p.b[3]) / 2]
      let bast = null
      for (const q of forra) {
        if (tagna.has(q.id)) continue
        const d = Math.hypot(c[0] - q.c[0], c[1] - q.c[1])
        // samma person: nära (vid 10 rutor/s rör sig ingen en kvarts bild) och ungefär lika stor.
        // Bryggan: lösare följning bytte mellan personer och gav falska rörelsespikar.
        const hp = p.b[3] - p.b[1]
        const hq = q.b[3] - q.b[1]
        const lik = hq > 0 && hp / hq > 0.7 && hp / hq < 1.4
        if (d < FOLJ_MAX && lik && (!bast || d < bast.d)) bast = { id: q.id, d }
      }
      p.id = bast ? bast.id : nasta++
      tagna.add(p.id)
      p.c = c
    }
    if (nu.length) forra = nu
  }
}

// ---------- kamera och rörelse ----------
// En rutas kameratransform flyttar en punkt (i pixlar) så här:
function flytta([x, y], k, W, H) {
  if (!k) return [x, y]
  const [dx, dy, rot, s] = k
  const cx = W / 2
  const cy = H / 2
  const a = (rot * Math.PI) / 180
  const px = x - cx
  const py = y - cy
  return [cx + s * (Math.cos(a) * px - Math.sin(a) * py) + dx * W, cy + s * (Math.sin(a) * px + Math.cos(a) * py) + dy * H]
}
const RUTNAT = [0.2, 0.5, 0.8].flatMap(x => [0.2, 0.5, 0.8].map(y => [x, y]))

// Aktivitet per ruta, i bildhöjder per sekund: kameran (ett rutnät flyttas) och motivet
// (personernas punkter, efter att kamerans rörelse dragits bort).
// Aktivitet per ruta, i bildhöjder per sekund: kameran (ett rutnät flyttas) och motivet
// (personernas punkter, efter att kamerans rörelse dragits bort).
// Motivet mäts över en baslinje på BASLINJE rutor: punkten för BASLINJE rutor sedan förs fram
// genom varje rutas kameratransform och jämförs med nu. Pose-punkternas skak mellan rutor är
// oberoende och tar ut sig över baslinjen; verklig rörelse gör det inte. Bryggan visade ett
// brusgolv på cirka 0,15 bildhöjder/s med baslinje 1 (stativklipp där motorn mätte 0,004).
export const BASLINJE = 3
// Följning mellan rutor: största hopp (andel av bilden) och rimlig fart (bildhöjder/s) för en kropp.
export const FOLJ_MAX = 0.12
export const RIMLIG_FART = 0.6
// Ansiktets höjd (andel av bilden) från vilken en närbild räknas som extrem.
export const ANSIKTE_EXTREM = 0.3
function aktivitetRuta(ramar, n, W, H, fps, fran = 0) {
  const k = ramar[n].k
  // null = okänt (ingen tillförlitlig kamera, ingen person att följa), inte stilla
  const kam = k ? medel(RUTNAT.map(([x, y]) => { const [a, b] = flytta([x * W, y * H], k, W, H); return Math.hypot(a - x * W, b - y * H) / H })) * fps : null
  let mot = 0
  const varden = []
  for (const p of ramar[n].p) {
    // längsta baslinje (högst BASLINJE) där samma person finns och kameran är känd hela vägen
    let bas = 0
    let q = null
    for (let b = Math.min(BASLINJE, n - fran); b >= 1; b--) {
      const kand = ramar[n - b].p.find(x => x.id === p.id)
      // kameran måste vara känd på hela vägen, annars räknas okänd kamerarörelse som personens
      let kanda = true
      for (let j = n - b + 1; j <= n; j++) if (!ramar[j].k) kanda = false
      if (kand && kanda) { bas = b; q = kand; break }
    }
    if (!q) continue
    const d = []
    for (let i = 0; i < 33; i++) {
      if (p.lm[i * 3 + 2] < 0.5 || q.lm[i * 3 + 2] < 0.5) continue
      let pt = [q.lm[i * 3] * W, q.lm[i * 3 + 1] * H]
      for (let j = n - bas + 1; j <= n; j++) pt = flytta(pt, ramar[j].k, W, H)
      d.push(Math.hypot(p.lm[i * 3] * W - pt[0], p.lm[i * 3 + 1] * H - pt[1]) / H / bas)
    }
    // en förflyttning över RIMLIG_FART är ett följningsfel (fel person, vänd kropp), inte rörelse
    if (d.length >= 5 && median(d) * fps <= RIMLIG_FART) varden.push(median(d))
  }
  mot = varden.length ? Math.max(...varden) * fps : null
  // näst största personens rörelse: det som händer runt huvudpersonen (bakgrund, andra personer)
  const andra = varden.length >= 2 ? varden.slice().sort((a, b) => b - a)[1] * fps : null
  return [kam == null ? null : r3(kam), mot == null ? null : r3(mot), andra == null ? null : r3(andra)]
}

// Iscensättning: hur scenen spelas ut, oberoende av kameratrick och efterbearbetning.
//   andel     hur stor del av bilden personerna tar (summan av rutorna, högst 1)
//   momentum  motivets rörelse i kroppslängder per sekund (motivet / huvudpersonens höjd i bild):
//             små personer i en vid bild räknas inte som lugna bara för att de är små
//   fard      huvudpersonens förflyttning genom bilden (bildhöjder per sekund), t.ex. en entré
//   in_ut     personer som kommer in i eller går ut ur bild under scenen, per sekund
//   bakgrund  rörelsen hos de andra personerna (näst största), bildhöjder per sekund
export function iscensattning({ rutor, kurva, huvud, storlek, fps, fran, till }) {
  const n = Math.max(1, rutor.length)
  const sek = n / fps
  const yta = b => Math.max(0, Math.min(1, b[2]) - Math.max(0, b[0])) * Math.max(0, Math.min(1, b[3]) - Math.max(0, b[1]))
  const andel = medel(rutor.map(r => Math.min(1, r.p.reduce((s, p) => s + yta(p.b), 0))))
  const mot = kurva.map(k => k[1]).filter(v => v != null)
  const momentum = storlek > 0.05 && mot.length ? medel(mot) / storlek : null
  // huvudpersonens väg (mitt på rutan), jämnad över tre rutor så att posens skak inte blir väg
  let fard = null
  if (huvud) {
    // bålens mitt (axlar och höfter som syns), inte rutans: rutan växer när armarna gestikulerar
    const bal = p => {
      const pts = [P.vAxel, P.hAxel, P.vHoft, P.hHoft].filter(i => p.lm[i * 3 + 2] > 0.5)
      if (pts.length < 2) return null
      return [medel(pts.map(i => p.lm[i * 3])), medel(pts.map(i => p.lm[i * 3 + 1]))]
    }
    const c = rutor.map(r => r.p.find(p => p.id === huvud.id)).map(p => (p ? bal(p) : null))
    const j = c.map((_, i) => { const v = c.slice(Math.max(0, i - 1), i + 2).filter(Boolean); return v.length ? [medel(v.map(x => x[0])), medel(v.map(x => x[1]))] : null })
    let vag = 0, tid = 0
    // steg över 0,04 bildhöjder per ruta (0,4 per sekund vid 10 rutor/s) är spårbyten mellan personer, inte gång
    for (let i = 1; i < j.length; i++) if (j[i] && j[i - 1]) { const d = Math.hypot((j[i][0] - j[i - 1][0]) * 9 / 16, j[i][1] - j[i - 1][1]); if (d * 10 / fps <= 0.04) vag += d; tid += 1 / fps }
    fard = tid > 0.3 ? vag / tid : null
  }
  // in och ut: spår som börjar eller slutar inne i scenen vid bildkanten
  const spar = new Map()
  rutor.forEach((r, i) => r.p.forEach(p => { const x = spar.get(p.id) ?? { forst: i, sist: i, bf: p.b, bs: p.b }; if (i < x.forst) { x.forst = i; x.bf = p.b } if (i >= x.sist) { x.sist = i; x.bs = p.b } spar.set(p.id, x) }))
  const kant = b => b[0] < 0.06 || b[2] > 0.94 || b[3] > 0.97
  let inut = 0
  for (const x of spar.values()) {
    if (x.sist - x.forst < 3) continue
    if (x.forst > 2 && kant(x.bf)) inut++
    if (x.sist < n - 3 && kant(x.bs)) inut++
  }
  const bak = kurva.map(k => k[2]).filter(v => v != null)
  return { andel: r3(andel), momentum: momentum == null ? null : r3(momentum), fard: fard == null ? null : r3(fard), in_ut: r3(inut / sek), bakgrund: bak.length ? r3(medel(bak)) : 0 }
}

// Kameraord för en scen, ur summan av rutornas transformer. Ord som i CameraBench där 2D räcker:
// pan/truck och tilt/pedestal går inte att skilja utan djup, så de anges som riktning.
// Brusgolv per ruta (mätt på stativklipp: |ln skala| ~0,002, |dx| ~0,001 per ruta). Under golvet räknas
// det som stilla, annars summeras bruset till en rörelse som inte finns.
export const BRUS = { d: 0.0015, lnS: 0.003, rot: 0.35 }
const golv = k => [Math.abs(k[0]) > BRUS.d ? k[0] : 0, Math.abs(k[1]) > BRUS.d ? k[1] : 0, Math.abs(k[2]) > BRUS.rot ? k[2] : 0, Math.abs(Math.log(k[3] || 1)) > BRUS.lnS ? k[3] : 1]
export function kameraOrd(rutor, fps) {
  const k = rutor.map(r => r.k).filter(Boolean).map(golv)
  const tackning = rutor.length ? k.length / rutor.length : 0
  if (!k.length) return { ord: ['okänd'], tackning: r3(tackning) }
  const pan = -k.reduce((s, x) => s + x[0], 0)
  const tilt = -k.reduce((s, x) => s + x[1], 0)
  const zoom = Math.exp(k.reduce((s, x) => s + Math.log(x[3] || 1), 0))
  // roll: rutornas rotation jämnas ut över fem rutor först, så att handhållet skak inte summeras till roll
  const rots = k.map(x => x[2])
  const roll = -rots.reduce((s, _, i) => s + medel(rots.slice(Math.max(0, i - 2), i + 3)), 0)
  // skak: det som blir kvar när rörelsen jämnats ut över fem rutor
  const jamn = (arr, i) => medel(arr.slice(Math.max(0, i - 2), i + 3))
  const xs = k.map(x => x[0])
  const ys = k.map(x => x[1])
  const skak = Math.sqrt(medel(xs.map((v, i) => (v - jamn(xs, i)) ** 2)) + medel(ys.map((v, i) => (v - jamn(ys, i)) ** 2)))
  const ord = []
  if (Math.abs(pan) > 0.12) ord.push(pan > 0 ? 'pan höger' : 'pan vänster')
  if (Math.abs(tilt) > 0.12) ord.push(tilt > 0 ? 'tilt upp' : 'tilt ned')
  if (Math.abs(Math.log(zoom)) > 0.08) ord.push(zoom > 1 ? 'in' : 'ut')
  if (Math.abs(roll) > 6) ord.push('roll')
  if (skak > 0.004) ord.push('handhållen')
  if (!ord.length) ord.push('stilla')
  return { ord, pan: r3(pan), tilt: r3(tilt), zoom: r3(zoom), roll: r3(roll), skak: r3(skak), tackning: r3(tackning), sekunder: r3(rutor.length / fps) }
}

// ---------- hela klippet ----------
export function tolka({ id, konto, kalla, meta, kandidater, sett, fps, motor }) {
  const W = 360
  const H = Math.round((360 * (meta.hojd ?? 640)) / (meta.bredd ?? 360))
  const klipp = klassaKlipp(kandidater, sett.kandidater)
  const scener = scenindelning(meta.langd, klipp)
  // kompakta rutor: personer (ruta, punkter i bild och 3D) och kamera
  const ramar = sett.ramar.map(f => ({
    t: f.t,
    p: f.personer.filter(p => p.bbox && (!f.saker || arPerson(p, f.saker, f.ansikten))).map(p => ({ b: p.bbox, lm: p.lm.flat(), v: p.varld.flat() })),
    o: (f.saker ?? []).filter(d => d.k !== 'person').map(d => [d.k, d.s]),
    a: (f.ansikten ?? []).filter(x => x.s >= 0.6).map(x => x.b),
    x: f.pix ?? null,
    h: (f.hander ?? []).map(h => ({ lm: h.lm, sida: h.sida })),
    // kameran räknas bara när skattningen håller: få punkter eller låg inlier-andel ger skräp
    // (bryggan: alla stora avvikelser hade inl < 0,36; i biblioteket faller 5 % av rutorna bort)
    k: f.kamera && f.kamera.inl >= GRANSER.KAMERA_INL && f.kamera.n >= GRANSER.KAMERA_N ? [f.kamera.dx, f.kamera.dy, f.kamera.rot, f.kamera.skala] : null,
  }))
  const iScen = t => scener.findIndex(s => t >= s.start - 1e-6 && t < s.slut)
  for (const s of scener) {
    const fran = Math.max(0, Math.ceil(s.start * fps - 1e-6))
    const till = Math.min(ramar.length, Math.ceil(s.slut * fps - 1e-6))
    folj(ramar, fran, till)
    // första rutan efter ett klipp jämför över klippet: ingen kamerarörelse där
    if (ramar[fran]) ramar[fran].k = null
    for (const d of s.dynamik) { const n = Math.round(d.t * fps); if (ramar[n]) ramar[n].k = null; if (ramar[n + 1]) ramar[n + 1].k = null }
    const rutor = ramar.slice(fran, till)
    const n = rutor.length || 1
    // personer: de som finns i minst 30 % av scenen; huvudpersonen är störst över tid
    const sp = new Map()
    rutor.forEach(r => r.p.forEach(p => {
      const a = (p.b[2] - p.b[0]) * (p.b[3] - p.b[1])
      const x = sp.get(p.id) ?? { id: p.id, n: 0, yta: 0 }
      x.n++; x.yta += a
      sp.set(p.id, x)
    }))
    const pers = [...sp.values()].filter(x => x.n / n >= 0.3).sort((a, b) => b.yta - a.yta)
    // huvudpersonen: störst över tid; finns inget spår över 30 % (följningen bröts) tas det största ändå
    const huvud = pers[0] ?? [...sp.values()].sort((a, b) => b.yta - a.yta)[0]
    const huvudRutor = huvud ? rutor.flatMap(r => r.p.filter(p => p.id === huvud.id)) : []
    const utsnitt = {}
    huvudRutor.forEach(p => { const u = utsnittFor(p.lm); if (u) utsnitt[u] = (utsnitt[u] ?? 0) + 1 })
    const [uVal, uN] = Object.entries(utsnitt).sort((a, b) => b[1] - a[1])[0] ?? ['objekt', n]
    const medPerson = rutor.filter(r => r.p.length).length / n
    const medHand = rutor.filter(r => r.h.length).length / n
    // händernas rörelse i bild (bildhöjder/s), kamerans rörelse bortdragen; bara mellan rutor med lika många händer
    const handFart = []
    for (let i = fran + 1; i < till; i++) {
      const a = ramar[i - 1].h
      const b = ramar[i].h
      if (!a.length || a.length !== b.length) continue
      const d = b.map((h, j) => { const [ex, ey] = flytta([a[j].lm[0] * W, a[j].lm[1] * H], ramar[i].k, W, H); return Math.hypot(h.lm[0] * W - ex, h.lm[1] * H - ey) / H })
      handFart.push(Math.min(3, medel(d) * fps))
    }
    s.hander = { andel: r3(medHand), fart: r3(medel(handFart)) }
    // vad som syns: saker som finns i minst 30 % av rutorna
    const sak = {}
    rutor.forEach(r => new Set(r.o.map(o => o[0])).forEach(k => { sak[k] = (sak[k] ?? 0) + 1 }))
    s.saker = Object.entries(sak).map(([k, c]) => ({ k, andel: r3(c / n) })).filter(x => x.andel >= 0.3).sort((a, b) => b.andel - a.andel).slice(0, 5)
    const objekt = medPerson < 0.4
    const cx = median(huvudRutor.map(p => (p.b[0] + p.b[2]) / 2))
    const huvudY = median(huvudRutor.map(p => p.lm[P.nasa * 3 + 1]))
    const storlek = median(huvudRutor.map(p => Math.min(1, p.b[3]) - Math.max(0, p.b[1])))
    const vrid = median(huvudRutor.map(p => vridning(p.v)).filter(v => v != null))
    // ingen kropp men ett ansikte: närbilder där Pose inte hittar kroppen. Ansiktets höjd ger utsnittet.
    const medAnsikte = rutor.filter(r => r.a?.length).length / n
    const ansiktsH = median(rutor.flatMap(r => (r.a ?? []).map(b => Math.min(1, b[3]) - Math.max(0, b[1]))))
    const franAnsikte = objekt && medAnsikte >= 0.4
    s.personer = franAnsikte ? Math.round(median(rutor.filter(r => r.a?.length).map(r => r.a.length))) : pers.length
    s.utsnitt = franAnsikte ? { varde: ansiktsH >= ANSIKTE_EXTREM ? 'extrem' : 'nara', andel: r3(medAnsikte), kalla: 'ansikte' } : objekt ? (medHand >= 0.4 ? { varde: 'händer', andel: r3(medHand) } : { varde: 'objekt', andel: r3(1 - Math.max(medPerson, medHand)) }) : { varde: uVal, andel: r3(uN / Math.max(1, huvudRutor.length)), per: utsnitt }
    s.placering = huvud ? { x: r3(cx), huvudY: r3(huvudY), storlek: r3(storlek), sida: cx < 0.38 ? 'vänster' : cx > 0.62 ? 'höger' : 'mitten' } : null
    s.vridning = vrid != null ? { grader: Math.round(vrid), ord: vridOrd(vrid) } : null
    s.kamera = kameraOrd(rutor, fps)
    // följer kameran huvudpersonen? (kameran rör sig men personen ligger kvar i bild)
    if (huvud && s.kamera.ord.some(o => o.startsWith('pan') || o.startsWith('tilt'))) {
      const xs = huvudRutor.map(p => (p.b[0] + p.b[2]) / 2)
      const sd = Math.sqrt(medel(xs.map(x => (x - medel(xs)) ** 2)))
      if (sd < 0.08) s.kamera.ord.push('följer')
    }
    const kurva = []
    // rutan efter ett klipp jämför två olika bilder: där hoppar personen, men rör sig inte
    const bryt = new Set([fran, ...s.dynamik.flatMap(d => [Math.round(d.t * fps), Math.round(d.t * fps) + 1])])
    for (let i = fran; i < till; i++) { const v = aktivitetRuta(ramar, i, W, H, fps, fran); if (bryt.has(i)) v[1] = null; kurva.push(v) }
    s.kurva = kurva
    // medel bara över rutor där värdet är känt; tackning säger hur stor del av scenen det gäller
    const kand = j => kurva.map(k => k[j]).filter(v => v != null)
    s.aktivitet = { kamera: r3(medel(kand(0))), motiv: kand(1).length ? r3(medel(kand(1))) : null, tackningMotiv: r3(kand(1).length / Math.max(1, kurva.length)) }
    // Bilden själv (pixlar): energi utan rutorna efter klipp (där ändras allt), övrigt över hela scenen
    const pix = rutor.map((r, j) => (r.x ? { ...r.x, energi: bryt.has(fran + j) ? null : r.x.energi } : null)).filter(Boolean)
    const pm = n => { const v = pix.map(x => x[n]).filter(x => x != null); return v.length ? r3(medel(v)) : null }
    s.bildmatt = { energi: pm('energi'), kant: pm('kant'), symmetri: pm('symmetri'), entropi: pm('entropi'), balans: pm('balans') }
    // Flöde: hur ryckig rörelsen är. Andra differensen (ändring av farten) mot farten själv;
    // jämn panorering ger lågt värde, handhållet eller hackigt högt.
    s.flode = { kamera: ryck(rutor.map(r => (r.k ? [r.k[0], r.k[1]] : null))), motiv: ryck(kurva.map(k => (k[1] == null ? null : [k[1], 0]))) }
    s.iscen = iscensattning({ rutor, kurva, huvud, storlek, fps, fran, till })
  }
  const tot = meta.langd || 1
  const dyn = klipp.filter(k => ['hopp', 'zoomryck', 'inskott'].includes(k.typ)).length
  const utsTid = {}
  scener.forEach(s => { utsTid[s.utsnitt.varde] = (utsTid[s.utsnitt.varde] ?? 0) + s.langd })
  return {
    id, version: VERSION, konto, kalla, analyserad: new Date().toISOString(), motor, granser: GRANSER,
    meta, analys: { fps, bredd: W, hojd: H },
    sammanfattning: {
      scener: scener.length,
      medelScen: r3(tot / scener.length),
      dynamikPerMin: r3((dyn / tot) * 60),
      personAndel: r3(ramar.filter(r => r.p.length).length / Math.max(1, ramar.length)),
      utsnitt: Object.entries(utsTid).sort((a, b) => b[1] - a[1])[0]?.[0] ?? null,
      kameraRorlig: r3(scener.filter(s => !s.kamera.ord.includes('stilla')).reduce((a, s) => a + s.langd, 0) / tot),
      aktivitet: { kamera: r3(medel(scener.flatMap(s => s.kurva.map(k => k[0])).filter(v => v != null))), motiv: r3(medel(scener.flatMap(s => s.kurva.map(k => k[1])).filter(v => v != null))) },
    },
    klipp, scener,
    ramar: ramar.map(r => ({ t: r.t, s: iScen(r.t), p: r.p.map(p => ({ id: p.id, b: p.b, lm: p.lm, v: p.v })), h: r.h, o: r.o, a: r.a, k: r.k, x: r.x })),
  }
}
