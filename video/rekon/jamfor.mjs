import { rimligSynlighet } from './manus.mjs'
import { FOV_H, FOV_V } from './geometri.mjs'

const POSEPUNKTER = [0, 11, 12, 13, 14, 15, 16, 23, 24]
const UTSNITT = ['extrem', 'nara', 'halvbild', 'halvtotal', 'total']
const BILDMATT = ['energi', 'kant', 'symmetri', 'entropi', 'balans']
const PIXLAR = 18 * 32
const punkt = p => Number.isFinite(p?.[0]) && Number.isFinite(p?.[1])
const iBild = p => punkt(p) && p[0] >= 0 && p[0] <= 1 && p[1] >= 0 && p[1] <= 1
const medel = tal => tal.length ? tal.reduce((summa, v) => summa + v, 0) / tal.length : null
const likhet = (a, b, golv) => 1 - Math.min(1, Math.abs(a - b) / Math.max(golv, Math.abs(a), Math.abs(b)))
const f1 = (traffar, extra, missade) => {
  const antal = 2 * traffar + extra + missade
  return antal ? 2 * traffar / antal : 1
}

function median(tal) {
  if (!tal.length) return null
  const ordnade = tal.slice().sort((a, b) => a - b)
  const mitt = Math.floor(ordnade.length / 2)
  return ordnade.length % 2 ? ordnade[mitt] : (ordnade[mitt - 1] + ordnade[mitt]) / 2
}

// Rutantalet i analysen har företräde. Tiden används när bara scensammanfattningar finns.
function rutantal(analys, fps) {
  if (Array.isArray(analys?.ramar)) return analys.ramar.length
  const tider = (analys?.scener ?? []).map(s => s.slut).filter(Number.isFinite)
  const langd = Number.isFinite(analys?.meta?.langd) ? analys.meta.langd : tider.length ? Math.max(...tider) : null
  return langd == null ? Infinity : Math.max(0, Math.round(langd * fps))
}

function personMatt(personer, projektioner, n) {
  const perPerson = new Map(personer.map(p => [
    p.id,
    new Map(p.spar.flatMap(s => s.ramar.map(r => [r.i, { ...r, scen: s.scen }]))),
  ]))
  const avstand = []
  let punkter = 0
  let ratt = 0
  const perPunkt = {}, perId = {} // uppdelning för felsökning: var missar rörelserna
  let traffar = 0
  let extra = 0
  let missade = 0

  for (const [i, proj] of (projektioner ?? []).entries()) {
    if (i >= n) break
    // Även en oväntad person i renderingen räknas som ett falskt positivt fynd.
    const idn = new Set([...perPerson.keys(), ...Object.keys(proj ?? {})])
    for (const id of idn) {
      const ruta = perPerson.get(id)?.get(i)
      const docka = proj?.[id]
      const finns = Boolean(ruta?.b && !ruta.fylld)
      const syns = Boolean(docka?.synlig && [0, 11, 12].some(k => iBild(docka.punkter?.[k])))
      if (finns && syns) traffar += 1
      else if (syns) extra += 1
      else if (finns) missade += 1

      const lm = ruta?.lm
      const hojd = ruta?.b?.[3] - ruta?.b?.[1]
      if (!docka?.synlig || !(hojd > 0) || !Number.isFinite(hojd)) continue
      if (lm?.length !== 33 || !lm.every(p => p?.length >= 3)) continue
      const synlighet = rimligSynlighet(lm, ruta.b)
      for (const k of POSEPUNKTER) {
        if (!(synlighet[k] >= 0.6) || !punkt(lm[k])) continue
        punkter += 1
        const pp = (perPunkt[k] ||= { n: 0, ratt: 0 }), pi = (perId[`${id}@s${ruta.scen}`] ||= { n: 0, ratt: 0 })
        pp.n++; pi.n++
        const p = docka.punkter?.[k]
        // En saknad projektion av en mätbar originalpunkt är en miss i PCK.
        if (!punkt(p)) continue
        const d = Math.hypot((p[0] - lm[k][0]) * 9 / 16, p[1] - lm[k][1])
        avstand.push(d)
        if (d < 0.2 * hojd) { ratt += 1; pp.ratt++; pi.ratt++ }
      }
    }
  }
  return {
    pose: {
      varde: punkter ? ratt / punkter : null,
      detalj: { punkter, ratt, medianAvstand: median(avstand), saknadePunkter: punkter - avstand.length, perPunkt: Object.fromEntries(Object.entries(perPunkt).map(([k, v]) => [k, +(v.ratt / v.n).toFixed(2)])), perPerson: Object.fromEntries(Object.entries(perId).map(([k, v]) => [k, `${(v.ratt / v.n).toFixed(2)} (${v.n})`])) },
    },
    narvaro: {
      varde: n > 0 ? f1(traffar, extra, missade) : null,
      detalj: { rutor: n, traffar, extra, missade },
    },
  }
}

function gransMatt(original, rendering) {
  const a = original.slice(1).map(s => s.start).filter(Number.isFinite).sort((x, y) => x - y)
  const b = rendering.slice(1).map(s => s.start).filter(Number.isFinite).sort((x, y) => x - y)
  let i = 0
  let j = 0
  let traffar = 0
  // Tidigaste möjliga matchning ger flest par utan att återanvända någon gräns.
  while (i < a.length && j < b.length) {
    if (Math.abs(a[i] - b[j]) <= 0.2 + 1e-9) {
      traffar += 1
      i += 1
      j += 1
    } else if (a[i] < b[j]) i += 1
    else j += 1
  }
  const extra = b.length - traffar
  const missade = a.length - traffar
  return {
    varde: original.length && rendering.length ? f1(traffar, extra, missade) : null,
    detalj: { original: a.length, rendering: b.length, traffar, extra, missade },
  }
}

// Varje originalscen paras med störst positiv överlapp. Vid lika överlapp väljs den första.
// Samma renderingsscen får användas flera gånger. Vikten är originalscenens hela längd.
function scenpar(original, rendering) {
  const par = []
  for (const a of original) {
    const langd = a.slut - a.start
    if (!Number.isFinite(langd) || langd <= 0) continue
    let vald = null
    let storst = 0
    for (const b of rendering) {
      const overlapp = Math.min(a.slut, b.slut) - Math.max(a.start, b.start)
      if (overlapp > storst) {
        storst = overlapp
        vald = b
      }
    }
    if (vald) par.push({ a, b: vald, langd })
  }
  return par
}

function scenMatt(par, berakna, langdviktat = true) {
  let summa = 0
  let vikt = 0
  let scener = 0
  let sekunder = 0
  for (const { a, b, langd } of par) {
    const varde = berakna(a, b)
    if (!Number.isFinite(varde)) continue
    const w = langdviktat ? langd : 1
    summa += varde * w
    vikt += w
    scener += 1
    sekunder += langd
  }
  return { varde: vikt ? summa / vikt : null, detalj: { scener, sekunder } }
}

function utsnittsLikhet(a, b) {
  const x = UTSNITT.indexOf(a.utsnitt?.varde)
  const y = UTSNITT.indexOf(b.utsnitt?.varde)
  if (x < 0 || y < 0) return null
  const steg = Math.abs(x - y)
  return steg === 0 ? 1 : steg === 1 ? 0.5 : 0
}

function antalsLikhet(a, b) {
  const x = a.personer
  const y = b.personer
  if (!Number.isFinite(x) || !Number.isFinite(y) || x < 0 || y < 0) return null
  return x === 0 && y === 0 ? 1 : Math.min(x, y) / Math.max(x, y)
}

function kameraVarde(scen, falt) {
  const kamera = scen.kamera
  if (!Number.isFinite(kamera?.[falt])) return null
  if (falt === 'zoom') return kamera.zoom - 1
  const sekunder = kamera.sekunder ?? (scen.slut - scen.start)
  if (!Number.isFinite(sekunder) || sekunder <= 0) return null
  // Pan och tilt är bildandelar i analysen. Samma synfält som kameraBana ger grader.
  // Roll anges redan i grader. Mätt tid har företräde framför scenens klipptider.
  const grader = falt === 'pan' ? FOV_H : falt === 'tilt' ? FOV_V : 1
  return kamera[falt] * grader / sekunder
}

function kameraLikhet(a, b) {
  const varden = []
  for (const falt of ['pan', 'tilt', 'roll', 'zoom']) {
    const x = kameraVarde(a, falt)
    const y = kameraVarde(b, falt)
    if (x != null && y != null) varden.push(likhet(x, y, falt === 'zoom' ? 0.03 : 2))
  }
  return medel(varden)
}

function bildmattsLikhet(a, b) {
  if (!BILDMATT.every(k => Number.isFinite(a.bildmatt?.[k]) && Number.isFinite(b.bildmatt?.[k]))) return null
  return medel(BILDMATT.map(k => likhet(a.bildmatt[k], b.bildmatt[k], 0.05)))
}

function korrelation(a, b) {
  if (a?.length !== PIXLAR || b?.length !== PIXLAR) return null
  if (!a.every(Number.isFinite) || !b.every(Number.isFinite)) return null
  const ma = a.reduce((summa, v) => summa + v, 0) / PIXLAR
  const mb = b.reduce((summa, v) => summa + v, 0) / PIXLAR
  let va = 0
  let vb = 0
  let kovarians = 0
  for (const [i, v] of a.entries()) {
    const x = v - ma
    const y = b[i] - mb
    va += x * x
    vb += y * y
    kovarians += x * y
  }
  if (va === 0 || vb === 0) return null
  // Detta motsvarar medelprodukten efter normalisering till medel 0 och std 1.
  const r = kovarians / Math.sqrt(va * vb)
  return r >= 1 - 1e-12 ? 1 : Math.max(0, Math.min(1, r))
}

function bildMatt(bilder, rutgrans) {
  const n = Math.min(rutgrans, bilder?.original?.length ?? 0, bilder?.rendering?.length ?? 0)
  const varden = []
  for (const [i, bild] of (bilder?.original ?? []).entries()) {
    if (i >= n) break
    const r = korrelation(bild, bilder.rendering[i])
    if (r != null) varden.push(r)
  }
  return { varde: medel(varden), detalj: { rutor: varden.length, overhoppade: n - varden.length } }
}

// Rena jämförelser utan att ändra indata. Saknade underlag ger null och får ingen totalvikt.
// Bildmåtten medelvärdesbildas över kompletta scenpar, övriga scenmått viktas med längd.
export function jamforRekon({ original, rendering, personer = [], projektioner, bilder, fps = 10 }) {
  if (!Number.isFinite(fps) || fps <= 0) throw new RangeError('fps måste vara positivt och ändligt')
  const a = original?.scener ?? []
  const b = rendering?.scener ?? []
  const par = scenpar(a, b)
  const rutgrans = Math.min(rutantal(original, fps), rutantal(rendering, fps))
  const n = Math.min(rutgrans, projektioner?.length ?? 0)
  const person = personMatt(personer, projektioner, n)
  const matt = {
    pose: { namn: 'Rörelser (pose)', vikt: 2, ...person.pose },
    narvaro: { namn: 'Personer på plats', vikt: 1, ...person.narvaro },
    granser: { namn: 'Scengränser', vikt: 1, ...gransMatt(a, b) },
    utsnitt: { namn: 'Utsnitt per scen', vikt: 1, ...scenMatt(par, utsnittsLikhet) },
    antal: { namn: 'Antal personer', vikt: 1, ...scenMatt(par, antalsLikhet) },
    kamera: { namn: 'Kamerarörelse', vikt: 1, ...scenMatt(par, kameraLikhet) },
    bildmatt: { namn: 'Bildens rörlighet', vikt: 1.5, ...scenMatt(par, bildmattsLikhet, false) },
    bild: { namn: 'Bildens uppbyggnad', vikt: 1.5, ...bildMatt(bilder, rutgrans) },
  }
  let summa = 0
  let vikt = 0
  for (const m of Object.values(matt)) {
    if (m.varde == null) continue
    summa += m.varde * m.vikt
    vikt += m.vikt
  }
  return { total: vikt ? summa / vikt : null, matt }
}
