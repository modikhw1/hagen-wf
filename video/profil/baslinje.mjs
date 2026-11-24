// Kontots baslinje och klippets residual: hur mycket bättre eller sämre ett klipp gick
// än väntat för sitt konto vid sin tid. Se karta/videoforandring/inlarning.md, avsnitt 2.6 och 8.1.

const DYGN = 86_400_000

export function median(varden) {
  const s = varden.filter(Number.isFinite).sort((a, b) => a - b)
  if (!s.length) return NaN
  const m = s.length >> 1
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2
}

export function medel(varden) {
  const s = varden.filter(Number.isFinite)
  return s.length ? s.reduce((a, b) => a + b, 0) / s.length : NaN
}

export function pearson(x, y) {
  const par = x.map((v, i) => [v, y[i]]).filter(([a, b]) => Number.isFinite(a) && Number.isFinite(b))
  if (par.length < 3) return NaN
  const mx = medel(par.map(p => p[0])), my = medel(par.map(p => p[1]))
  let sxy = 0, sxx = 0, syy = 0
  for (const [a, b] of par) { sxy += (a - mx) * (b - my); sxx += (a - mx) ** 2; syy += (b - my) ** 2 }
  return sxx && syy ? sxy / Math.sqrt(sxx * syy) : NaN
}

// Medelrang för lika värden; saknade värden förblir NaN.
export function rang(varden) {
  const idx = varden.map((v, i) => [v, i]).filter(([v]) => Number.isFinite(v)).sort((a, b) => a[0] - b[0])
  const ut = varden.map(() => NaN)
  let i = 0
  while (i < idx.length) {
    let j = i + 1
    while (j < idx.length && idx[j][0] === idx[i][0]) j++
    for (let t = i; t < j; t++) ut[idx[t][1]] = (i + j - 1) / 2
    i = j
  }
  return ut
}

export function spearman(x, y) {
  const ok = x.map((v, i) => Number.isFinite(v) && Number.isFinite(y[i]))
  return pearson(rang(x.map((v, i) => ok[i] ? v : NaN)), rang(y.map((v, i) => ok[i] ? v : NaN)))
}

// För varje klipp: medianen av de k tidsmässigt närmaste andra klippen i samma konto.
// Rullande i stället för en fast median, eftersom konton växer och krymper.
export function rullandeBaslinje(varden, tider, k = 15) {
  return varden.map((_, i) => {
    const grannar = varden
      .map((v, j) => ({ v, d: Math.abs(tider[j] - tider[i]), j }))
      .filter(g => g.j !== i && Number.isFinite(g.v))
      .sort((a, b) => a.d - b.d)
      .slice(0, k)
    return grannar.length >= Math.min(k, 5) ? median(grannar.map(g => g.v)) : NaN
  })
}

const andel = (taljare, namnare) =>
  Number.isFinite(taljare) && Number.isFinite(namnare) && namnare > 0 ? Math.log10((taljare + 1) / (namnare + 1)) : NaN

// klipp: [{ id, langd, visningar, gillanden, kommentarer, delningar, datum }] för ett konto.
// Klipp yngre än minAlderDagar räknas inte: visningarna har inte satt sig.
export function residualer(klipp, { idag, k = 15, minAlderDagar = 14 } = {}) {
  const nu = new Date(idag).getTime()
  const giltiga = klipp
    .map(c => ({ ...c, tid: new Date(c.datum).getTime() }))
    .filter(c => Number.isFinite(c.tid) && Number.isFinite(c.visningar) && c.visningar > 0)
    .filter(c => nu - c.tid >= minAlderDagar * DYGN)
    .sort((a, b) => a.tid - b.tid)
  const tider = giltiga.map(c => c.tid)
  const matt = {
    v: giltiga.map(c => Math.log10(c.visningar)),
    l: giltiga.map(c => andel(c.gillanden, c.visningar)),
    c: giltiga.map(c => andel(c.kommentarer, c.visningar)),
    s: giltiga.map(c => andel(c.delningar, c.visningar)),
  }
  const bas = Object.fromEntries(Object.entries(matt).map(([n, v]) => [n, rullandeBaslinje(v, tider, k)]))
  return giltiga.map((c, i) => ({
    id: c.id,
    datum: c.datum,
    alder: Math.round((nu - c.tid) / DYGN),
    langd: c.langd,
    visningar: c.visningar,
    logv: matt.v[i],
    bas_v: bas.v[i],
    rv: matt.v[i] - bas.v[i],
    rl: matt.l[i] - bas.l[i],
    rc: matt.c[i] - bas.c[i],
    rs: matt.s[i] - bas.s[i],
  })).filter(r => Number.isFinite(r.rv))
}

// Inom varje konto: medelresidual för klipp med egenskapen minus utan.
// Konton med färre än minPer klipp på någon sida räknas inte.
export function effektPerKonto(rader, harEgenskap, { falt = 'rv', minPer = 2 } = {}) {
  const perKonto = new Map()
  for (const r of rader) {
    const e = harEgenskap(r)
    if (e == null) continue
    if (!perKonto.has(r.konto)) perKonto.set(r.konto, { med: [], utan: [] })
    perKonto.get(r.konto)[e ? 'med' : 'utan'].push(r[falt])
  }
  const effekter = []
  for (const [konto, { med, utan }] of perKonto) {
    if (med.length >= minPer && utan.length >= minPer) effekter.push({ konto, effekt: medel(med) - medel(utan), n: med.length + utan.length })
  }
  return {
    konton: effekter.length,
    medel: medel(effekter.map(e => e.effekt)),
    andelPositiv: effekter.length ? effekter.filter(e => e.effekt > 0).length / effekter.length : NaN,
    effekter,
  }
}
