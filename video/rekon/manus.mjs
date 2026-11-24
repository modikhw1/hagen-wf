// Manuset: personspår, geometri, kamerabana, rörelser, figurer och lokal blir ett manus som motorn
// spelar. Varje scen ställs upp i en egen scen-värld (origo x = 40 · i), med kameran där den stod
// i originalet vid scenens början. Det som inte syns antas (golv, bakvägg, ben bakom en disk) och
// märks som antaget i manuset.
import fs from 'node:fs'
import path from 'node:path'
import * as THREE from 'three'
import { DATA } from '../analys/pipeline.mjs'
import { identiteter } from './spar.mjs'
import { djup, djupUrRuta, iKamera, hojdOchLutning, kameraBana, median, FOV_V, AXEL_HOJD, ANKEL_HOJD } from './geometri.mjs'
import { retargetSpar } from './rorelse.mjs'
import { lyftScen } from './lyft.mjs'

const REKON = path.join(DATA, 'rekon')
const lasJson = f => (fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null)
const r3 = v => Math.round(v * 1000) / 1000
const r4 = v => Math.round(v * 10000) / 10000
export const SCEN_AVSTAND = 40

// Avstånd per ruta i ett spår, utjämnat (median över ±3 rutor), med rutans höjd som reserv.
function djupSerie(ramar) {
  const raa = ramar.map(r => djup(r.lm, r.varld) ?? null)
  return ramar.map((r, k) => {
    const nara = []
    for (let j = Math.max(0, k - 3); j <= Math.min(ramar.length - 1, k + 3); j++) if (raa[j] != null) nara.push(raa[j])
    const d = nara.length ? median(nara) : djupUrRuta(r.b)
    return Math.max(0.3, Math.min(12, d))
  })
}
const synlig = (lm, i, min = 0.6) => lm && lm[i][2] >= min
const axelmitt = lm => [(lm[11][0] + lm[12][0]) / 2, (lm[11][1] + lm[12][1]) / 2]

// MediaPipes synlighet gäller inte skymning: bakom en disk säger den att höfterna syns (0,99) och
// ritar knäna i höfthöjd. Rimlighet i stället: punkter nedanför personens ruta är utanför bild eller
// skymda, och ett knä som inte ligger tydligt under höften (eller en fot under knät) är gissat.
export function rimligSynlighet(lm, b) {
  const v = lm.map(l => l[2])
  const mitt = (i, j) => [(lm[i][0] + lm[j][0]) / 2, (lm[i][1] + lm[j][1]) / 2]
  const [, ay] = mitt(11, 12), [, hy] = mitt(23, 24)
  const bal = Math.max(0.02, hy - ay)
  for (let i = 0; i < 33; i++) if (lm[i][1] > b[3] + 0.02 || lm[i][1] < b[1] - 0.06) v[i] = Math.min(v[i], 0.2)
  for (const [hoft, kna, fot, hal, topp] of [[23, 25, 27, 29, 31], [24, 26, 28, 30, 32]]) {
    if (lm[kna][1] - lm[hoft][1] < 0.45 * bal) for (const k of [kna, fot, hal, topp]) v[k] = 0
    if (lm[fot][1] - lm[kna][1] < 0.35 * bal) for (const k of [fot, hal, topp]) v[k] = 0
  }
  return v
}

// Punkterna i kamerarummet: bildens läge (exakt i bild) och MediaPipes djup relativt axlarna.
function punkterIKamera(lm, varld, d) {
  const z0 = (varld[11][2] + varld[12][2]) / 2
  return lm.map((l, j) => iKamera(l[0], l[1], d + (varld[j][2] - z0)))
}

export function byggManus(id) {
  const analys = lasJson(path.join(DATA, 'analys', `${id}.json`))
  const ra = lasJson(path.join(DATA, 'ra', `${id}.json`))
  const sr = lasJson(path.join(REKON, id, 'spar-ra.json'))
  const forslag = lasJson(path.join(DATA, 'typer', 'forslag', `${id}.json`))
  const lokal2d = lasJson(path.join(REKON, id, 'lokal-2d.json'))
  if (!analys || !ra || !sr) throw new Error(`underlag saknas för ${id} (analys, ra eller spar)`)
  const fps = sr.fps
  const n = sr.ramar.length
  const scener = analys.scener.map(s => ({ i0: Math.round(s.start * fps), i1: Math.min(n, Math.max(Math.round(s.start * fps) + 1, Math.round(s.slut * fps))) }))
  const pers = identiteter(sr.ramar, scener).filter(p => p.spar.some(s => s.ramar.filter(r => r.lm).length >= 3))
  const raRamar = ra.sett.ramar

  const rorelser = {}
  const lokalScener = []
  const mScener = []
  const antaget = []
  for (const [i, sc] of scener.entries()) {
    const origo = new THREE.Vector3(SCEN_AVSTAND * i, 0, 0)
    const spar = pers.flatMap(p => p.spar.filter(s => s.scen === i).map(s => ({ p, s })))
    // 1. kamerans höjd och lutning ur personerna i scenens första sekund (innan kameran rört sig)
    const obs = []
    const djupPer = new Map()
    for (const { s } of spar) {
      const ds = djupSerie(s.ramar)
      djupPer.set(s, ds)
      const tidiga = s.ramar.map((r, k) => ({ r, d: ds[k] })).filter(({ r }) => r.lm && r.i < sc.i0 + fps)
      const w = 1 / Math.max(1, tidiga.length)
      for (const { r, d } of tidiga) {
        if (synlig(r.lm, 11) && synlig(r.lm, 12)) obs.push({ p: iKamera(...axelmitt(r.lm), d), y: AXEL_HOJD, w })
        for (const a of [27, 28]) if (synlig(r.lm, a, 0.75)) obs.push({ p: iKamera(r.lm[a][0], r.lm[a][1], d), y: ANKEL_HOJD, w: w * 0.5, sigma: 0.08 })
      }
    }
    const start = hojdOchLutning(obs)
    if (!obs.length) antaget.push(`scen ${i + 1}: kamerans höjd och lutning antagna (ingen person att mäta mot)`)
    const allaD = [...djupPer.values()].flat()
    const dRef = allaD.length ? median(allaD) : 2
    const bana = kameraBana(raRamar.slice(sc.i0, sc.i1), start, dRef)
    const tillVarld = (k, p) => p.clone().applyQuaternion(bana[Math.min(bana.length - 1, Math.max(0, k))].q).add(bana[Math.min(bana.length - 1, Math.max(0, k))].pos).add(origo)

    // 2. personerna: punkter i världen per ruta, rörelse och bana
    const handling = []
    let djupast = 0
    for (const { p, s } of spar) {
      const ds = djupPer.get(s)
      djupast = Math.max(djupast, median(ds))
      const rutor = []
      for (let k = sc.i0; k < sc.i1; k++) {
        const j = s.ramar.findIndex(r => r.i === k)
        const r = j >= 0 ? s.ramar[j] : null
        if (!r?.lm || !r.varld) { rutor.push(null); continue }
        const pc = punkterIKamera(r.lm, r.varld, ds[j])
        rutor.push({ punkter: pc.map(v => tillVarld(k - sc.i0, v).toArray()), synlighet: rimligSynlighet(r.lm, r.b) })
      }
      // före spårets första ruta och efter dess sista: håll närmaste pose (personen står kvar)
      const forst = rutor.findIndex(Boolean)
      if (forst < 0) continue
      const r = retargetSpar(rutor.slice(forst), { fps, skala: 1 })
      const rid = `rek:${p.id}:s${i}`
      rorelser[rid] = { id: rid, typ: 'leder', kalla: `rekon:${id}#${i}`, fps, loop: false, liv: false, ramar: r.ramar }
      // synlig: från spårets första till sista ruta; nära scenens kanter hela vägen (personen fanns där
      // men hittades sent), annars kommer eller går personen i bild
      const sista = s.sist - sc.i0
      const t0 = forst <= 3 ? 0 : forst / fps
      const t1 = sista >= sc.i1 - sc.i0 - 4 ? (sc.i1 - sc.i0) / fps : (sista + 1) / fps
      handling.push({ roll: p.id, rorelse: rid, start: r3(forst / fps), synlig: [r3(t0), r3(t1)], bana: { fps, ramar: r.bana.map(b => b.map(r4)) } })
    }
    // 3. huvudpersonen (störst i bild i snitt) blir kamerans mål när reglaget byter uttryck
    const medRorelse = new Set(handling.map(h => h.roll))
    const huvud = spar.filter(x => medRorelse.has(x.p.id)).slice().sort((a, b) => median(b.s.ramar.map(r => r.b[3] - r.b[1])) - median(a.s.ramar.map(r => r.b[3] - r.b[1])))[0]?.p.id
    const as = analys.scener[i]
    mScener.push({
      id: `s${i + 1}`,
      text: forslag?.scener?.[i]?.vad ?? `Scen ${i + 1}`,
      tid: r3(as.slut - as.start),
      origo: origo.toArray(),
      ...(i > 0 ? { in: { typ: 'klipp' } } : {}),
      handling,
      kamera: {
        utsnitt: as.utsnitt?.varde && as.utsnitt.varde !== 'objekt' ? as.utsnitt.varde : 'halvbild',
        mal: huvud ? { roll: huvud, led: 'spine3' } : { punkt: [origo.x, 1.2, -2] },
        lins: FOV_V,
        bana: { fps, ramar: bana.map(b => [...b.pos.clone().add(origo).toArray().map(r4), ...b.q.toArray().map(r4)]) },
        start: { hojd: r3(start.h), lutning: start.pitch },
      },
    })
    // 4. lokalen: Geminis utläggning om den finns, annars golv och en bakvägg bakom personerna
    const l2 = lokal2d?.scener?.[i]
    if (l2) {
      // nyckelbildens kamera (lokal.mjs tog rutan strax efter scenens början)
      const kb = bana[Math.max(0, Math.min(bana.length - 1, l2.ruta - sc.i0))]
      // föremål som personerna håller (en bricka, en kopp) hör inte till lokalen: det som ligger framför
      // en person och överlappar hennes ruta tas bort, utom möbler som står mellan kameran och personerna
      const iRutan = spar.map(({ s }) => s.ramar.find(r => r.i === l2.ruta)).filter(Boolean)
      const l2u = { ...l2, element: l2.element.filter(e => {
        if (['disk', 'bord', 'stol', 'hylla', 'skap', 'kassa'].includes(e.kategori)) return true
        const [y0, x0, y1, x1] = e.ruta.map(v => v / 1000)
        const over = iRutan.find(r => Math.min(x1, r.b[2]) - Math.max(x0, r.b[0]) > 0.3 * (x1 - x0) && Math.min(y1, r.b[3]) - Math.max(y0, r.b[1]) > 0.3 * (y1 - y0))
        if (over && e.placering !== 'vagg' && e.placering !== 'tak' && e.placering !== 'golv') { antaget.push(`scen ${i + 1}: "${e.namn}" togs bort (hålls av en person)`); return false }
        return true
      }) }
      const lk = lyftScen(l2u, { pos: kb.pos.toArray(), q: kb.q.toArray() }, { personer: [...djupPer.values()].map(ds => ({ djup: median(ds) })) })
      // ren skiva (platta.mjs): projiceras från nyckelbildens kamera
      const plattaFil = path.join(REKON, id, `platta-s${i}.jpg`)
      const platta = fs.existsSync(plattaFil) ? { url: `/__data/rekon/${id}/platta-s${i}.jpg`, pos: kb.pos.clone().add(origo).toArray(), q: kb.q.toArray(), fov: FOV_V, aspekt: 9 / 16 } : null
      if (!platta) antaget.push(`scen ${i + 1}: ingen ren skiva, lokalen i enkla färger`)
      // det som står framför en person (en disk) måste ligga framför den i 3D, annars syns benen genom
      // disken. Föremålet flyttas mot kameran och skalas längs strålen (likformigt kring kameran), så att
      // det ser exakt likadant ut från originalets kamera.
      const kp = kb.pos, fram = new THREE.Vector3(0, 0, -1).applyQuaternion(kb.q).setY(0).normalize()
      const djupI = ({ s }) => { const j = s.ramar.findIndex(r => r.i === l2.ruta); return j >= 0 ? djupPer.get(s)[j] : null }
      const personerI = spar.map(x => ({ r: x.s.ramar.find(r => r.i === l2.ruta), d: djupI(x) })).filter(x => x.r && x.d)
      lk.element.forEach((e, j) => {
        const e2 = l2u.element[j]
        if (!e2 || !(e2.framfor_personer || e2.kategori === 'disk')) return
        const [y0, x0, y1, x1] = e2.ruta.map(v => v / 1000)
        const framfor = personerI.filter(({ r }) => Math.min(x1, r.b[2]) - Math.max(x0, r.b[0]) > 0.02 && y1 > (r.b[1] + r.b[3]) / 2)
        if (!framfor.length) return
        const dp = Math.min(...framfor.map(x => x.d))
        const rel = new THREE.Vector3(...e.pos).sub(kp)
        const de = rel.dot(fram) + e.storlek[2] / 2
        if (de <= dp - 0.12) return
        const k = Math.max(0.15, Math.min(1, (dp - 0.12) / de))
        e.pos = rel.multiplyScalar(k).add(kp).toArray()
        e.storlek = e.storlek.map(v => v * k)
        // ner till golvet igen: den nya nederdelen syns inte från originalkameran men skymmer benen
        const topp = e.pos[1] + e.storlek[1] / 2
        if (topp > 0.2 && e.pos[1] - e.storlek[1] / 2 > 0.02) { e.storlek[1] = topp; e.pos[1] = topp / 2 }
        antaget.push(`scen ${i + 1}: "${e.namn}" flyttad framför personerna (×${k.toFixed(2)})`)
      })
      lokalScener.push({ origo: origo.toArray(), golv: lk.golv, vagg: lk.vagg, platta, element: lk.element.map(e => ({ ...e, pos: [e.pos[0] + origo.x, e.pos[1], e.pos[2] + origo.z] })) })
      for (const a of lk.antaget) antaget.push(`scen ${i + 1}: ${a}`)
    }
    else {
      lokalScener.push({ origo: origo.toArray(), golv: { farg: '#cfc6b8' }, vagg: { z: -(djupast + 1.5), farg: '#e9e4da' } })
      antaget.push(`scen ${i + 1}: lokalen antagen (golv och bakvägg)`)
    }
  }
  const figurer = Object.fromEntries(pers.map(p => [p.id, {
    skala: 1,
    hud: p.farger.hud ?? '#d9a07c', overdel: p.farger.overdel ?? '#777777', underdel: p.farger.underdel ?? '#3b3d48',
    skor: '#2a2a2a', har: p.farger.har ?? '#3a2a20', tillbehor: [],
  }]))
  return {
    id: `${id}/rekon`, klipp: id, namn: forslag?.typ?.namn ?? id, kund: analys.konto ?? id.split('-')[0],
    verklighet: null, instruktion: null,
    lokal: { id: `rek-${id}`, scener: lokalScener },
    roller: Object.fromEntries(pers.map(p => [p.id, p.id])),
    // fotostil när lokalen är originalets rena skiva: dockorna ska smälta in i ett foto
    stil: lokalScener.some(s => s.platta) ? 'foto' : null,
    figurer, rorelser, scener: mScener, antaget,
  }
}

export async function stegManus(id, om) {
  const ut = path.join(REKON, id, 'manus.json')
  if (!om && fs.existsSync(ut)) return
  const m = byggManus(id)
  fs.writeFileSync(ut, JSON.stringify(m))
  // Modellerad scen (plan 1 nov): samma personer, rörelser och föremål, men rummet byggt helt i 3D i
  // föremålens färger i stället för originalets projicerade bild. Då tål scenen nya vinklar, avstånd och
  // iscensättning: hela scenen är i flux. Tecknade dockor, som passar en modellerad värld.
  const modell = {
    ...m, id: `${id}/modell`, stil: 'modell',
    // statisten finns alltid som roll men syns bara i uttryck med ~b1 (variant.js)
    roller: { ...m.roller, statist: 'statist' },
    figurer: { ...m.figurer, statist: { skala: 1, hud: '#c99a7a', overdel: '#5b6b7a', underdel: '#2f3440', skor: '#222222', har: '#2a2018', tillbehor: [] } },
    lokal: { id: `rek-${id}-modell`, scener: m.lokal.scener.map(s => ({ ...s, rum: true, dekal: !!s.platta })) },
    antaget: [...m.antaget, 'hela rummet modellerat ur Geminis utläggning; originalbilden bara på plana ytor (bakvägg, golv, föremålens framsidor)'],
  }
  fs.writeFileSync(path.join(REKON, id, 'manus-modell.json'), JSON.stringify(modell))
  console.log(`  manus: ${m.scener.length} scener, ${Object.keys(m.figurer).length} personer, ${Object.keys(m.rorelser).length} rörelser · ${(fs.statSync(ut).size / 1e6).toFixed(1)} MB`)
}
