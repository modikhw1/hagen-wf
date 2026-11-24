// Egenskaper: det som mäts per scen (och per klipp), som tal en modell kan tränas på och som text
// Jev kan bedöma. Allt kommer ur analysen (analys/tolka.mjs), inget från en modell.
// Samma funktioner körs i Node (servern, skript) och i webbläsaren.
import { SAKER_SV } from '../analys/tolka.mjs'

const UTSNITT_ORDNING = { total: 0, halvtotal: 1, halvbild: 2, nara: 3, extrem: 4, 'händer': 3.5, objekt: 2 }
const UTSNITT = ['total', 'halvtotal', 'halvbild', 'nara', 'extrem', 'händer', 'objekt']
const p90 = a => { if (!a.length) return 0; const s = a.slice().sort((x, y) => x - y); return s[Math.floor(0.9 * (s.length - 1))] }
const medel = a => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : 0)
const r3 = v => Math.round(v * 1000) / 1000

// Namn och förklaring för varje egenskap. Ordningen är vektorns ordning.
export const EGENSKAPER = [
  ['kamera', 'kamerans rörelse, medel (bildhöjder/s)'],
  ['kamera_topp', 'kamerans rörelse, 90:e percentilen'],
  ['motiv', 'motivets rörelse i bild, medel'],
  ['motiv_topp', 'motivets rörelse, 90:e percentilen'],
  ['pan', '|pan| per mätt sekund (bildbredder/s)'],
  ['tilt', '|tilt| per mätt sekund (bildhöjder/s)'],
  ['zoom', '|ln zoom| per mätt sekund'],
  ['roll', '|roll| per mätt sekund (grader/10/s)'],
  ['skak', 'handhållet skak'],
  ['stilla', 'kameran stilla (0/1)'],
  ['foljer', 'kameran följer personen (0/1)'],
  ['utsnitt_nara', 'utsnittets närhet, 0 = total … 4 = extrem'],
  ...UTSNITT.map(u => [`u_${u}`, `utsnitt ${u} (0/1)`]),
  ['storlek', 'huvudpersonens höjd i bild'],
  ['ur_mitten', 'huvudpersonens avstånd från mitten'],
  ['vridning', 'kroppens vridning mot kameran (0 = rakt mot, 1 = profil)'],
  ['personer', 'antal personer'],
  ['hander', 'andel av scenen med händer i bild'],
  ['hand_fart', 'händernas rörelse i bild'],
  ['saker', 'antal saker i bild (mat, glas, bestick …)'],
  ['langd', 'scenens längd, ln sekunder'],
  ['energi', 'hur mycket bilden ändras mellan rutor (pixlar)'],
  ['kant', 'hur mycket som händer i bilden (andel kanter)'],
  ['symmetri', 'bildens symmetri (1 = spegelsymmetrisk)'],
  ['entropi', 'visuell komplexitet'],
  ['balans', 'tyngdpunktens avstånd från mitten'],
  ['ryck_kamera', 'hur ryckig kamerans rörelse är'],
  ['ryck_motiv', 'hur ryckig personernas rörelse är'],
  ['dynamik', 'hoppklipp, zoomryck och inskott per sekund'],
  ['montage', 'scenen är ett montage (0/1)'],
  // iscensättning (analys/tolka.mjs iscensattning): hur scenen spelas ut, inte kameratrick
  ['andel_bild', 'hur stor del av bilden personerna tar'],
  ['momentum', 'motivets rörelse i kroppslängder per sekund'],
  ['fard', 'huvudpersonens förflyttning genom bilden (entré, korsning)'],
  ['in_ut', 'personer som kommer in i eller går ut ur bild, per sekund'],
  ['bakgrund', 'rörelse hos andra personer än huvudpersonen'],
]
export const NAMN = EGENSKAPER.map(e => e[0])

export function scenEgenskaper(s) {
  const k = s.kamera ?? {}
  const ord = k.ord ?? []
  const kurva = s.kurva ?? []
  // Kamerans rörelse per sekund av den tid som faktiskt är mätt (rutor med tillförlitlig kamera).
  // Summan över scenen blev för kort när analysen saknade rutor; bryggan visade r 0,41 mot 0,89 per ruta.
  const matt = Math.max(0.5, (k.sekunder ?? s.langd ?? 1) * (k.tackning ?? 1))
  const v = {
    kamera: s.aktivitet?.kamera ?? 0,
    kamera_topp: p90(kurva.map(x => x[0]).filter(v => v != null)),
    motiv: s.aktivitet?.motiv ?? 0, // okänt (ingen person) räknas som stilla i modellen; täckningen visas separat
    motiv_topp: p90(kurva.map(x => x[1]).filter(v => v != null)),
    pan: Math.abs(k.pan ?? 0) / matt,
    tilt: Math.abs(k.tilt ?? 0) / matt,
    zoom: Math.abs(Math.log(k.zoom || 1)) / matt,
    roll: Math.abs(k.roll ?? 0) / 10 / matt,
    skak: (k.skak ?? 0) * 100,
    stilla: ord.includes('stilla') ? 1 : 0,
    foljer: ord.includes('följer') ? 1 : 0,
    utsnitt_nara: UTSNITT_ORDNING[s.utsnitt?.varde] ?? 2,
    ...Object.fromEntries(UTSNITT.map(u => [`u_${u}`, s.utsnitt?.varde === u ? 1 : 0])),
    storlek: s.placering?.storlek ?? 0,
    ur_mitten: s.placering ? Math.abs(s.placering.x - 0.5) : 0,
    vridning: s.vridning ? Math.min(1, s.vridning.grader / 90) : 0,
    personer: s.personer ?? 0,
    hander: s.hander?.andel ?? 0,
    hand_fart: s.hander?.fart ?? 0,
    saker: (s.saker ?? []).filter(x => x.k !== 'dining table').length,
    langd: Math.log(Math.max(0.3, s.langd ?? 1)),
    energi: s.bildmatt?.energi ?? 0,
    kant: s.bildmatt?.kant ?? 0,
    symmetri: s.bildmatt?.symmetri ?? 0,
    entropi: s.bildmatt?.entropi ?? 0,
    balans: s.bildmatt?.balans ?? 0,
    ryck_kamera: s.flode?.kamera ?? 0,
    ryck_motiv: s.flode?.motiv ?? 0,
    dynamik: (s.dynamik?.length ?? 0) / Math.max(0.5, s.langd ?? 1),
    montage: s.montage ? 1 : 0,
    andel_bild: s.iscen?.andel ?? 0,
    momentum: s.iscen?.momentum ?? 0,
    fard: s.iscen?.fard ?? 0,
    in_ut: s.iscen?.in_ut ?? 0,
    bakgrund: s.iscen?.bakgrund ?? 0,
  }
  return Object.fromEntries(NAMN.map(n => [n, r3(v[n] ?? 0)]))
}

// Ett klipp som helhet: medel över scenerna viktat med längd, plus rytmen.
export function klippEgenskaper(a) {
  const sc = a.scener.map(s => ({ s, e: scenEgenskaper(s) }))
  const tot = sc.reduce((x, { s }) => x + s.langd, 0) || 1
  const v = Object.fromEntries(NAMN.map(n => [n, r3(sc.reduce((x, { s, e }) => x + e[n] * s.langd, 0) / tot)]))
  v.langd = r3(Math.log(Math.max(0.3, a.meta.langd)))
  v.scener_per_s = r3(a.scener.length / Math.max(1, a.meta.langd))
  v.dynamik = r3((a.sammanfattning.dynamikPerMin ?? 0) / 60)
  v.utsnittsbyten = r3(sc.slice(1).filter(({ s }, i) => s.utsnitt.varde !== sc[i].s.utsnitt.varde).length / Math.max(1, sc.length - 1))
  return v
}
export const KLIPP_NAMN = [...NAMN, 'scener_per_s', 'utsnittsbyten']

// Scenen i ord, för Jev (och för människor som vill förstå siffrorna).
const UTS_TEXT = { total: 'helbild där hela kroppen syns', halvtotal: 'halvtotal från knäna och upp', halvbild: 'halvbild från midjan och upp', nara: 'närbild på huvud och axlar', extrem: 'extrem närbild på ansiktet', 'händer': 'detaljbild på händer', objekt: 'bild utan personer (mat, produkt eller miljö)' }
export function scenText(s) {
  const k = s.kamera ?? {}
  const delar = []
  delar.push(`En scen på ${s.langd?.toFixed(1)} sekunder.`)
  delar.push(`Utsnitt: ${UTS_TEXT[s.utsnitt?.varde] ?? s.utsnitt?.varde}.`)
  if (s.personer) delar.push(`${s.personer} ${s.personer === 1 ? 'person' : 'personer'} i bild${s.placering ? `, huvudpersonen ${s.placering.sida} i bild och ${Math.round(s.placering.storlek * 100)} % av bildhöjden` : ''}${s.vridning ? `, vänd ${s.vridning.ord}` : ''}.`)
  if (s.hander?.andel > 0.3) delar.push(`Händer syns ${Math.round(s.hander.andel * 100)} % av tiden.`)
  if (s.saker?.length) delar.push(`Saker i bild: ${s.saker.map(x => SAKER_SV[x.k] ?? x.k).join(', ')}.`)
  const ord = (k.ord ?? []).filter(o => o !== 'okänd')
  delar.push(`Kameran: ${ord.length ? ord.join(', ') : 'okänd'}.`)
  delar.push(`Rörelse i bild per sekund: kameran ${(s.aktivitet?.kamera ?? 0).toFixed(3)} bildhöjder${s.aktivitet?.motiv != null ? `, personerna ${s.aktivitet.motiv.toFixed(3)}` : ''}.`)
  if (s.dynamik?.length) delar.push(`${s.dynamik.length} snabba klipp inom scenen (${[...new Set(s.dynamik.map(d => d.typ))].join(', ')}).`)
  if (s.montage) delar.push('Scenen är ett montage av mycket korta bilder.')
  return delar.join(' ')
}
