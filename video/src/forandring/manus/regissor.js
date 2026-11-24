// Regissörerna: tio oberoende omskrivningar av originalet, en per steg på vertikalen
// "kreativ scenografi". Varje regissör får samma förutsättningar (lokal, roller, handling låsta)
// och en egen instruktion. Här är regissören en regel med slump per regissör (seedad), så att
// verkligheterna skiljer sig åt som om de skrivits av olika personer. I biblioteket är det en AI.
// Originalet är steg 5, mitt på skalan, och skrivs inte om: 1–4 lugnare, 6–10 mer scenografi.

export const ORIGINAL_STEG = 5

export const INSTRUKTION = {
  1: 'Ett stativ, rakt framifrån, samma utsnitt hela vägen. Personerna gör minsta möjliga.',
  2: 'Stilla kamera, raka klipp. Lugnt agerande.',
  3: 'Stilla kamera men olika utsnitt per scen.',
  4: 'Små, mjuka kamerarörelser. Lite lugnare agerande.',
  6: 'Följ handlingen med kameran, lite handhållet.',
  7: 'Rörlig kamera, tydliga utsnittsbyten.',
  8: 'Varje scen får ett eget grepp. Mer energi i agerandet.',
  9: 'Vågat: låga och höga vinklar, snabba övergångar, överspelat.',
  10: 'Allt i rörelse: whip, arc, roll, närbilder. Maxat men filmbart.',
}

// Liten deterministisk slump: samma regissör och scen ger alltid samma val.
const rng = seed => () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646
const pick = (r, a) => a[Math.floor(r() * a.length)]

function kamera(steg, sc, r) {
  const k = sc.kamera
  const huvud = sc.handling[0].roll
  // Rör sig någon i scenen (en väg) följer kameran med, annars blir bilden kvar där personen började.
  const folj = (k.ops ?? []).some(o => o.op === 'tracking') || sc.handling.some(h => h.vag)
  const malFor = utsnitt => (utsnitt === 'nara' || utsnitt === 'extrem' ? { roll: huvud, led: 'head' } : k.mal)
  const mal = k.mal
  const med = (ut, ops) => (folj ? [...ops.filter(o => o.op !== 'tracking'), { op: 'tracking', mangd: 0.9 }] : ops)
  if (steg <= 1) return { utsnitt: 'total', mal: { punkt: [0.35, 1.0, -1.6] }, vinkel: 0, hojd: 0, ops: [] }
  if (steg === 2) return { utsnitt: pick(r, ['total', 'halvtotal']), mal, vinkel: 0, hojd: 0, ops: med(null, []) }
  if (steg === 3) { const u = pick(r, ['halvtotal', 'halvbild', 'total']); return { utsnitt: u, mal: malFor(u), vinkel: pick(r, [-10, 0, 10]), hojd: 0, ops: med(u, []) } }
  if (steg <= 7) {
    const a = (steg - 3) / 4
    const op = pick(r, ['dolly', 'pan', 'truck', 'tracking'])
    const mangd = { dolly: 0.25 * a, pan: 12 * a, truck: 0.2 * a, tracking: 0.8 }[op]
    const u = pick(r, ['halvtotal', 'halvbild', steg >= 6 ? 'nara' : 'halvtotal'])
    return {
      utsnitt: u,
      mal: malFor(u), vinkel: pick(r, [-25, -10, 10, 25]) * a, hojd: pick(r, [-6, 0, 8]) * a,
      skak: steg >= 6 ? 0.15 * a : 0, ops: med(u, [{ op, mangd }]),
    }
  }
  // 8–10: eget grepp per scen
  const a = (steg - 7) / 3
  const ops = [
    { op: pick(r, ['arc', 'dolly', 'pan', 'zoom']), mangd: 0 },
    ...(steg >= 9 ? [{ op: pick(r, ['roll', 'pedestal', 'tilt']), mangd: 0 }] : []),
  ].map(o => ({ ...o, mangd: { arc: 24 + 16 * a, dolly: 0.4 + 0.3 * a, pan: 20 + 20 * a, zoom: 0.3 + 0.4 * a, roll: 8 + 8 * a, pedestal: 0.3, tilt: 12 + 10 * a }[o.op] }))
  const u = pick(r, steg >= 10 ? ['nara', 'extrem', 'halvbild'] : ['nara', 'halvbild', 'halvtotal'])
  return {
    utsnitt: u,
    // Vinklar inom rummet: bakväggen ligger bakom alla, så kameran håller sig framför (±50°).
    mal: malFor(u), vinkel: pick(r, [-50, -30, 30, 50]) * (0.6 + 0.4 * a), hojd: pick(r, [-18, -10, 15, 24]) * (0.6 + 0.4 * a),
    roll: steg >= 10 ? pick(r, [-10, 8]) : 0,
    skak: 0.4 + 0.4 * a, ops: med(u, ops),
  }
}

const OVERGANG = steg =>
  steg <= 3 ? { typ: 'klipp' } : steg <= 7 ? { typ: 'mjuk', tid: 0.3 } : null

export function verklighet(original, steg) {
  if (steg === ORIGINAL_STEG) return { ...original, verklighet: ORIGINAL_STEG, instruktion: 'Originalet.' }
  const r = rng(1000 + steg * 97)
  const amp = steg <= 1 ? 0.45 : steg <= 3 ? 0.7 : steg === 4 ? 0.85 : steg <= 7 ? 1 : 1.1 + 0.15 * (steg - 8)
  const tempo = steg <= 2 ? 0.85 : steg >= 9 ? 1.15 : 1
  return {
    ...original,
    id: `${original.klipp}/v${steg}`,
    verklighet: steg,
    instruktion: INSTRUKTION[steg],
    scener: original.scener.map((sc, i) => ({
      ...sc,
      in: i === 0 ? undefined : (OVERGANG(steg) ?? { typ: pick(r, ['whip', 'zoom', 'klipp']), tid: 0.3 }),
      handling: sc.handling.map(h => ({ ...h, amp: (h.amp ?? 1) * amp, tempo: (h.tempo ?? 1) * tempo })),
      kamera: kamera(steg, sc, r),
    })),
  }
}

export const allaVerkligheter = original =>
  Object.fromEntries(Array.from({ length: 10 }, (_, k) => [k + 1, verklighet(original, k + 1)]))
