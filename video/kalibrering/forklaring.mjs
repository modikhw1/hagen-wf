import { korrigera } from './placering.mjs'

export const SPAKAR = {
  kamera: ['kamera', 'kamera_topp', 'pan', 'tilt', 'zoom', 'roll', 'skak', 'stilla', 'foljer', 'utsnitt_nara', 'u_total', 'ur_mitten', 'vridning', 'ryck_kamera'],
  agerande: ['motiv', 'motiv_topp', 'ryck_motiv', 'hand_fart'],
  bild: ['energi', 'kant', 'symmetri', 'entropi', 'balans'],
  rytm: ['dynamik', 'montage'],
}

const SPAK_FOR = new Map(Object.entries(SPAKAR).flatMap(([spak, namn]) => namn.map(n => [n, spak])))
const SPAKNAMN = { kamera: 'kameran', agerande: 'agerandet', bild: 'bilden', rytm: 'rytmen', ovrigt: 'övrigt' }
const UTSNITT = { total: 'helbild', halvtotal: 'halvtotal', halvbild: 'halvbild', nara: 'närbild', extrem: 'extrem närbild' }
const RORELSER = {
  static: 'stillastående kamera',
  dolly: 'kameran åker in',
  pan: 'kameran panorerar',
  truck: 'kameran glider i sidled',
  arc: 'kameran går i en båge',
  zoom: 'kameran zoomar',
  tilt: 'kameran tiltar',
  pedestal: 'kameran höjs',
}
const NARA_NOLL = 1e-9
const tal = v => String(Number(v.toFixed(2))).replace('.', ',').replace('-', '−')
const medTecken = v => `${v < 0 ? '−' : '+'}${Math.abs(v).toFixed(1).replace('.', ',')}`

function rorelse(p) {
  if (p.rorelse === 'static') return RORELSER.static
  // Vridningar mäts i grader, förflyttningar i meter och zoom som förstoring.
  const mangd = p.rorelse === 'zoom' ? `${tal(p.mangd * 100)} %`
    : ['pan', 'arc', 'tilt'].includes(p.rorelse) ? `${tal(p.mangd)}°`
    : `${tal(p.mangd)} m`
  return `${RORELSER[p.rorelse]} ${mangd}`
}

function kameraAndringar(fore, efter) {
  if (!efter) return fore ? ['originalets kamera'] : []
  const andringar = []
  if (fore?.utsnitt !== efter.utsnitt) {
    const fran = fore ? UTSNITT[fore.utsnitt] : 'originalets kamera'
    andringar.push(`${UTSNITT[efter.utsnitt]} i stället för ${fran}`)
  }
  if (fore?.vinkel !== efter.vinkel) {
    andringar.push(efter.vinkel === 0 ? 'rakt framifrån'
      : `från ${efter.vinkel < 0 ? 'vänster' : 'höger'} ${tal(Math.abs(efter.vinkel))}°`)
  }
  // Originalets okända kamerahöjd går inte att jämföra med en vald höjd.
  if (!fore) {
    andringar.push(efter.hojd === 0 ? 'i ögonhöjd'
      : `${tal(Math.abs(efter.hojd))}° ${efter.hojd > 0 ? 'högre' : 'lägre'} än ögonhöjd`)
  } else if (fore.hojd !== efter.hojd) {
    const skillnad = efter.hojd - fore.hojd
    andringar.push(`${tal(Math.abs(skillnad))}° ${skillnad > 0 ? 'högre' : 'lägre'}`)
  }
  if (fore?.rorelse !== efter.rorelse || (efter.rorelse !== 'static' && fore?.mangd !== efter.mangd)) {
    andringar.push(rorelse(efter))
  }
  if (!fore) {
    if (efter.skak > 0) andringar.push('handhållen')
  } else if (fore.skak !== efter.skak) {
    andringar.push(efter.skak > fore.skak ? 'handhållen' : 'lugnare hand')
  }
  return andringar
}

function agerandeAndringar(fore = 1, efter = 1) {
  if (Math.abs(efter - fore) <= NARA_NOLL) return []
  if (Math.abs(efter - 1) <= NARA_NOLL) return ['agerandet som i originalet']
  // Förstärkningens referens är originalet, även vid byte mellan två varianter.
  return [`rörelserna ${tal(Math.abs(efter - 1) * 100)} % ${efter > 1 ? 'större' : 'mindre'} än i originalet`]
}

export function forklara({ mod, korr, fore, efter }) {
  const fran = mod.st.z(korrigera(fore.e, korr, mod.namn))
  const till = mod.st.z(korrigera(efter.e, korr, mod.namn))
  const bidrag = mod.namn.map((namn, j) => ({ namn, bidrag: mod.w[j] * (till[j] - fran[j]) }))
  // Linjär nytta: summan är nyttaskillnaden, utan bidrag från andra vertikaler.
  const nytta = bidrag.reduce((summa, x) => summa + x.bidrag, 0)
  const steg = efter.steg - fore.steg
  const faktor = Math.abs(nytta) <= NARA_NOLL ? 0 : steg / nytta
  const grupper = new Map()
  for (const x of bidrag) {
    const v = faktor * x.bidrag
    if (v === 0) continue
    const spak = SPAK_FOR.get(x.namn) ?? 'ovrigt'
    if (!grupper.has(spak)) grupper.set(spak, { spak, bidrag: 0, egenskaper: [] })
    const grupp = grupper.get(spak)
    grupp.bidrag += v
    grupp.egenskaper.push({ namn: x.namn, bidrag: v })
  }
  const alla = [...grupper.values()]
  // Andelarna avser alla spakars absoluta bidrag, även dem under visningsgränsen.
  const absolut = alla.reduce((summa, x) => summa + Math.abs(x.bidrag), 0)
  const spakar = alla
    .filter(x => Math.abs(x.bidrag) >= 0.05)
    .sort((a, b) => Math.abs(b.bidrag) - Math.abs(a.bidrag))
    .map(x => ({ ...x, andel: Math.abs(x.bidrag) / absolut }))
  const ord = {
    kamera: kameraAndringar(fore.p, efter.p),
    agerande: agerandeAndringar(fore.amp, efter.amp),
  }
  const andringar = [...ord.kamera, ...ord.agerande]
  const delar = spakar.map(x => {
    const andrat = ord[x.spak] ?? []
    return `${SPAKNAMN[x.spak]} ${medTecken(x.bidrag)}${andrat.length ? ` (${andrat.join(', ')})` : ''}`
  })
  const text = Math.abs(steg) <= NARA_NOLL ? 'ingen ändring'
    : `${medTecken(steg)} steg${delar.length ? `: ${delar.join(', ')}` : ''}`
  return { steg, nytta, spakar, andringar, text }
}
