// Jämför motorns egen syn (native) med analysen av renderingen (samma pipeline som riktiga klipp).
// Två nivåer:
//   rutor:  hittar analysen personerna, hur långt ifrån ligger punkterna, stämmer kameran, händerna
//   scener: samma utsnitt, hittas scengränserna, och för varje egenskap: samband, bias och en
//           linjär korrektion native → analys (det som gör motorns tal jämförbara med biblioteket)
import fs from 'node:fs'
import path from 'node:path'
import { scenEgenskaper, NAMN } from '../kalibrering/egenskaper.mjs'

const KARNA = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
const W = 360
const H = 640
const r3 = v => (v == null || !Number.isFinite(v) ? null : Math.round(v * 1000) / 1000)
const medel = a => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : null)

// Spearman: rangkorrelation, tål enstaka extremvärden
function rang(a) { const s = a.map((v, i) => [v, i]).sort((x, y) => x[0] - y[0]); const r = new Array(a.length); s.forEach(([, i], k) => { r[i] = k }); return r }
export function spearman(par) {
  if (par.length < 3) return null
  const rx = rang(par.map(p => p[0]))
  const ry = rang(par.map(p => p[1]))
  return statistik(rx.map((x, i) => [x, ry[i]]), false).r
}
export function statistik(par, medRang = true) {
  const n = par.length
  if (n < 3) return { n, r: null, rs: null, bias: null, mae: null, a: null, b: null }
  const mx = medel(par.map(p => p[0]))
  const my = medel(par.map(p => p[1]))
  let sxy = 0, sxx = 0, syy = 0
  for (const [x, y] of par) { sxy += (x - mx) * (y - my); sxx += (x - mx) ** 2; syy += (y - my) ** 2 }
  const r = sxx > 1e-12 && syy > 1e-12 ? sxy / Math.sqrt(sxx * syy) : null
  const b = sxx > 1e-12 ? sxy / sxx : null
  return {
    n, r: r3(r), rs: medRang ? r3(spearman(par)) : undefined, bias: r3(my - mx), mae: r3(medel(par.map(([x, y]) => Math.abs(y - x)))),
    a: b == null ? null : r3(my - b * mx), b: r3(b), medelNative: r3(mx), medelAnalys: r3(my),
  }
}

const mitt = b => [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]
const yta = b => Math.max(0, Math.min(1, b[2]) - Math.max(0, b[0])) * Math.max(0, Math.min(1, b[3]) - Math.max(0, b[1]))
const iBild = (x, y) => x >= 0 && x <= 1 && y >= 0 && y <= 1

export function jamforManus(A, N) {
  // rutor nära en scengräns (klipp, tonad övergång, whip) har ingen kamerarörelse att mäta
  const nara = new Set((N.facit?.granser ?? []).flatMap(g => [-3, -2, -1, 0, 1, 2, 3].map(d => Math.round(g.t * 10) + d)))
  const rad = { personer: 0, hittade: 0, analysPersoner: 0, falska: 0, punktFel: [], kam: { dx: [], dy: [], skala: [], rot: [] }, hander: 0, handerHittade: 0, analysHander: 0, handerFalska: 0 }
  const n = Math.min(A.ramar.length, N.ramar.length)
  for (let i = 0; i < n; i++) {
    const a = A.ramar[i]
    const m = N.ramar[i]
    const mp = m.p.filter(p => yta(p.b) >= 0.01)
    rad.personer += mp.length
    rad.analysPersoner += a.p.length
    const tagna = new Set()
    for (const p of mp) {
      const c = mitt(p.b)
      let bast = null
      a.p.forEach((q, k) => { if (tagna.has(k)) return; const d = Math.hypot(c[0] - mitt(q.b)[0], c[1] - mitt(q.b)[1]); if (d < 0.15 && (!bast || d < bast.d)) bast = { k, d } })
      if (!bast) continue
      rad.hittade++
      tagna.add(bast.k)
      const q = a.p[bast.k]
      for (const j of KARNA) {
        const [nx, ny, nv] = [p.lm[j * 3], p.lm[j * 3 + 1], p.lm[j * 3 + 2]]
        const [ax, ay, av] = [q.lm[j * 3], q.lm[j * 3 + 1], q.lm[j * 3 + 2]]
        if (nv >= 0.5 && av >= 0.5 && iBild(nx, ny) && iBild(ax, ay)) rad.punktFel.push(Math.hypot((ax - nx) * W / H, ay - ny))
      }
    }
    rad.falska += a.p.length - tagna.size
    rad.hander += m.h.length
    rad.analysHander += a.h.length
    rad.handerHittade += Math.min(m.h.length, a.h.length)
    rad.handerFalska += Math.max(0, a.h.length - m.h.length)
    const rorelse = k => k && (Math.abs(k[0]) > 0.003 || Math.abs(k[1]) > 0.003 || Math.abs(Math.log(k[3])) > 0.004)
    if (a.k && m.k && !nara.has(i) && (rorelse(a.k) || rorelse(m.k))) {
      rad.kam.dx.push([m.k[0], a.k[0]])
      rad.kam.dy.push([m.k[1], a.k[1]])
      rad.kam.skala.push([Math.log(m.k[3]), Math.log(a.k[3])])
      rad.kam.rot.push([m.k[2], a.k[2]])
    }
  }
  // scener: motorns scener är facit; analysens scen med störst överlapp paras ihop med den
  const scener = N.scener.map(ns => {
    let bast = null
    for (const as of A.scener) {
      const o = Math.max(0, Math.min(ns.slut, as.slut) - Math.max(ns.start, as.start))
      if (!bast || o > bast.o) bast = { as, o }
    }
    return { ns, as: bast?.as, overlapp: bast ? bast.o / Math.max(0.01, ns.slut - ns.start) : 0 }
  })
  // aktivitet per scen, bara på rutor där båda ser en person (motiv) eller båda har kamera (kamera):
  // enheterna jämförs då oberoende av hur ofta analysen ser dockan
  const matchad = scener.map(({ ns }) => {
    const fran = Math.round(ns.start * 10)
    const till = Math.round(ns.slut * 10)
    const mot = []
    const kam = []
    for (let i = fran; i < Math.min(till, n); i++) {
      const ka = A.ramar[i]
      const kn = N.ramar[i]
      const sa = A.scener.findIndex(x => x.start <= ka.t + 1e-6 && x.slut > ka.t)
      const ia = sa >= 0 ? i - Math.round(A.scener[sa].start * 10) : -1
      const vA = sa >= 0 ? A.scener[sa].kurva?.[ia] : null
      const vN = ns.kurva?.[i - fran]
      if (!vA || !vN) continue
      if (vN[1] != null && vA[1] != null) mot.push([vN[1], vA[1]])
      if (vN[0] != null && vA[0] != null) kam.push([vN[0], vA[0]])
    }
    const m = a => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : null)
    return { motiv: mot.length >= 3 ? [m(mot.map(x => x[0])), m(mot.map(x => x[1]))] : null, kamera: kam.length >= 3 ? [m(kam.map(x => x[0])), m(kam.map(x => x[1]))] : null }
  })
  // en övergång (tonad, whip) får hittas var som helst inom sin längd, ett klipp inom 0,15 s
  const granser = (N.facit?.granser ?? []).map(g => ({ ...g, hittad: A.klipp.some(k => (k.typ === 'scen' || k.typ === 'overgang') && Math.abs(k.t - g.t) <= (g.typ === 'klipp' ? 0.15 : 0.35)), typAnalys: A.klipp.find(k => Math.abs(k.t - g.t) <= 0.35)?.typ ?? null }))
  return { rad, scener, granser, matchad }
}

export function jamforAlla(dirs) {
  const ids = fs.readdirSync(dirs.native).filter(f => f.endsWith('.json')).map(f => f.slice(0, -5)).filter(id => fs.existsSync(path.join(dirs.analys, `${id}.json`))).sort()
  const tot = { personer: 0, hittade: 0, analysPersoner: 0, falska: 0, punktFel: [], kam: { dx: [], dy: [], skala: [], rot: [] }, hander: 0, handerHittade: 0, analysHander: 0, handerFalska: 0 }
  const egenskaper = Object.fromEntries(NAMN.map(n => [n, []]))
  const manus = []
  let utsLika = 0
  let utsN = 0
  let gHittade = 0
  let gN = 0
  const utsMatris = {}
  const det = { motor: 0, pose: 0, filter: 0, ansikte: 0, coco: 0 }
  const matchMotiv = []
  const matchKamera = []
  for (const id of ids) {
    const A = JSON.parse(fs.readFileSync(path.join(dirs.analys, `${id}.json`), 'utf8'))
    const N = JSON.parse(fs.readFileSync(path.join(dirs.native, `${id}.json`), 'utf8'))
    const { rad, scener, granser, matchad } = jamforManus(A, N)
    const raFil = path.join(dirs.ra, `${id}.json`)
    if (fs.existsSync(raFil)) {
      const ra = JSON.parse(fs.readFileSync(raFil, 'utf8'))
      const nn = Math.min(ra.sett.ramar.length, N.ramar.length)
      for (let i = 0; i < nn; i++) {
        if (!N.ramar[i].p.length) continue
        det.motor++
        if (ra.sett.ramar[i].personer.length) det.pose++
        if (A.ramar[i]?.p.length) det.filter++
        if (ra.sett.ramar[i].ansikten?.length) det.ansikte++
        if (ra.sett.ramar[i].saker?.some(x => x.k === 'person')) det.coco++
      }
    }
    for (const mt of matchad) { if (mt.motiv) matchMotiv.push(mt.motiv); if (mt.kamera) matchKamera.push(mt.kamera) }
    for (const k of ['personer', 'hittade', 'analysPersoner', 'falska', 'hander', 'handerHittade', 'analysHander', 'handerFalska']) tot[k] += rad[k]
    tot.punktFel.push(...rad.punktFel)
    for (const k of Object.keys(tot.kam)) tot.kam[k].push(...rad.kam[k])
    const sc = []
    for (const { ns, as, overlapp } of scener) {
      if (!as) continue
      const en = scenEgenskaper(ns)
      const ea = scenEgenskaper(as)
      for (const n of NAMN) egenskaper[n].push([en[n], ea[n]])
      utsN++
      if (ns.utsnitt.varde === as.utsnitt.varde) utsLika++
      const nyckel = `${ns.utsnitt.varde}→${as.utsnitt.varde}`
      utsMatris[nyckel] = (utsMatris[nyckel] ?? 0) + 1
      sc.push({ i: ns.i, start: ns.start, slut: ns.slut, overlapp: r3(overlapp), utsnitt: [ns.utsnitt.varde, as.utsnitt.varde], kamera: [ns.kamera.ord, as.kamera.ord], aktivitet: [ns.aktivitet, as.aktivitet], personer: [ns.personer, as.personer], bild: as.bild })
    }
    gN += granser.length
    gHittade += granser.filter(g => g.hittad).length
    manus.push({
      id, langd: N.meta.langd, scenerAnalys: A.scener.length, scenerMotor: N.scener.length,
      personHittad: r3(rad.personer ? rad.hittade / rad.personer : null), punktFel: r3(medel(rad.punktFel)),
      granser, scener: sc,
    })
  }
  return {
    skapad: new Date().toISOString(),
    manus,
    detektion: {
      rutorMedDocka: det.motor,
      pose: r3(det.motor ? det.pose / det.motor : null),
      efterFilter: r3(det.motor ? det.filter / det.motor : null),
      ansikte: r3(det.motor ? det.ansikte / det.motor : null),
      coco: r3(det.motor ? det.coco / det.motor : null),
    },
    matchad: { motiv: statistik(matchMotiv), kamera: statistik(matchKamera) },
    rutor: {
      personHittad: r3(tot.personer ? tot.hittade / tot.personer : null),
      personFalsk: r3(tot.analysPersoner ? tot.falska / tot.analysPersoner : null),
      punktFel: r3(medel(tot.punktFel)),
      handerHittade: r3(tot.hander ? tot.handerHittade / tot.hander : null),
      handerFalska: r3(tot.analysHander ? tot.handerFalska / tot.analysHander : null),
      kamera: Object.fromEntries(Object.entries(tot.kam).map(([k, v]) => [k, statistik(v)])),
    },
    scener: { n: utsN, utsnittLika: r3(utsN ? utsLika / utsN : null), utsnittMatris: utsMatris, granserHittade: r3(gN ? gHittade / gN : null) },
    egenskaper: NAMN.map(n => ({ namn: n, ...statistik(egenskaper[n]), par: egenskaper[n] })),
  }
}
