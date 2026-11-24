// Modellen per vertikal: Bradley–Terry med linjär nytta på standardiserade egenskaper.
//   P(a har mer X än b) = σ(w · (z(a) − z(b)))
// 'lika' räknas som 0,5. L2-regularisering drar mot startvikterna (inte mot noll), så att få
// bedömningar inte kastar bort det vertikalen är definierad som, och många bedömningar tar över.
//
// Valet av modell: få bedömningar (hundratals), behov av att förstå varför (vikterna går att läsa),
// och samma form som Jev-svaret (ett tal per scen). En större modell blir meningsfull först med
// tusentals bedömningar; formatet på datan ändras inte då.

const sig = x => 1 / (1 + Math.exp(-x))

export function standardisera(items, namn) {
  const m = {}
  const s = {}
  for (const n of namn) {
    const v = items.map(it => it.e[n] ?? 0)
    m[n] = v.reduce((a, b) => a + b, 0) / Math.max(1, v.length)
    s[n] = Math.sqrt(v.reduce((a, b) => a + (b - m[n]) ** 2, 0) / Math.max(1, v.length)) || 1
  }
  return { m, s, z: e => namn.map(n => ((e[n] ?? 0) - m[n]) / s[n]) }
}

const etikett = val => (val === 'a' ? 1 : val === 'b' ? 0 : val === 'lika' ? 0.5 : null)

// bedomningar: [{ a, b, val }] med a/b = item-id. items: [{ id, e }]
export function trana({ items, bedomningar, namn, start = {}, lambda = 1, varv = 400, lr = 0.1 }) {
  const st = standardisera(items, namn)
  const Z = new Map(items.map(it => [it.id, st.z(it.e)]))
  const w0 = namn.map(n => start[n] ?? 0)
  // startvikter är givna i råa enheter som riktning; skala till standardiserade enheter
  const w = w0.slice()
  const data = bedomningar.map(b => ({ za: Z.get(b.a), zb: Z.get(b.b), y: etikett(b.val) })).filter(d => d.za && d.zb && d.y != null)
  for (let it = 0; it < varv && data.length; it++) {
    const g = new Array(namn.length).fill(0)
    for (const d of data) {
      let u = 0
      for (let j = 0; j < namn.length; j++) u += w[j] * (d.za[j] - d.zb[j])
      const err = sig(u) - d.y
      for (let j = 0; j < namn.length; j++) g[j] += err * (d.za[j] - d.zb[j])
    }
    for (let j = 0; j < namn.length; j++) w[j] -= lr * (g[j] / data.length + (lambda / Math.max(1, data.length)) * (w[j] - w0[j]))
  }
  return { namn, w, st, n: data.length }
}

export const nytta = (mod, e) => { const z = mod.st.z(e); return z.reduce((s, v, j) => s + v * mod.w[j], 0) }

// Hur ofta modellen väljer samma som människan (lika räknas inte), och log-förlust.
export function overens(mod, items, bedomningar) {
  const E = new Map(items.map(it => [it.id, it.e]))
  let ratt = 0
  let tot = 0
  let ll = 0
  let nll = 0
  for (const b of bedomningar) {
    const y = etikett(b.val)
    if (y == null || !E.has(b.a) || !E.has(b.b)) continue
    const p = sig(nytta(mod, E.get(b.a)) - nytta(mod, E.get(b.b)))
    ll += -(y * Math.log(Math.max(1e-6, p)) + (1 - y) * Math.log(Math.max(1e-6, 1 - p)))
    nll++
    if (y === 0.5) continue
    tot++
    if ((p > 0.5) === (y === 1)) ratt++
  }
  return { andel: tot ? ratt / tot : null, n: tot, logforlust: nll ? ll / nll : null }
}

// Korsvalidering: bedömningarna delas i k delar; modellen tränas på resten och testas på delen.
// Bedömningar av samma klipp hålls ihop, så att testet mäter något modellen inte sett.
// Korsvalidering per klipp (eller annan grupp, t.ex. konto): varje klipp hamnar i exakt en del.
// Test: bedömningar där båda sidorna hör till testdelen. Träning: bedömningar och items utan något
// klipp i testdelen (standardiseringen räknas också bara på dem). Par som spänner över delar används
// varken i träning eller test för den delen. Så mäts hur modellen klarar klipp den aldrig sett.
export function korsvalidera({ items, bedomningar, namn, start, k = 5, grupp = id => String(id).split('#')[0], ...opt }) {
  const grupper = [...new Set(bedomningar.flatMap(b => [grupp(b.a), grupp(b.b)]))].sort()
  const del = new Map(grupper.map((g, i) => [g, i % k]))
  let ratt = 0
  let tot = 0
  const per = []
  for (let f = 0; f < k; f++) {
    const i = b => del.get(grupp(b.a)) === f || del.get(grupp(b.b)) === f
    const test = bedomningar.filter(b => del.get(grupp(b.a)) === f && del.get(grupp(b.b)) === f)
    const tran = bedomningar.filter(b => !i(b))
    if (!test.length) continue
    const tranItems = items.filter(it => del.get(grupp(it.id)) !== f)
    const mod = trana({ items: tranItems, bedomningar: tran, namn, start, ...opt })
    const o = overens(mod, items, test)
    if (o.andel != null) { ratt += o.andel * o.n; tot += o.n; per.push(o.andel) }
  }
  return { andel: tot ? ratt / tot : null, n: tot, delar: per, grupper: grupper.length }
}

// Skalan 1–10 inom biblioteket: nyttan som percentil (1 = lugnast, 10 = mest).
export function skala(mod, items) {
  const u = items.map(it => ({ id: it.id, u: nytta(mod, it.e) })).sort((a, b) => a.u - b.u)
  const n = Math.max(1, u.length - 1)
  return new Map(u.map((x, i) => [x.id, { u: x.u, steg: 1 + (9 * i) / n }]))
}

// Nästa par att bedöma. Mest lärorikt: par som modellen är osäker på (liten nyttoskillnad),
// bland items som bedömts få gånger, helst från olika klipp, och inte redan jämförda.
export function nastaPar(mod, items, bedomningar, slump = Math.random) {
  if (items.length < 2) return null
  const antal = new Map(items.map(it => [it.id, 0]))
  const gjorda = new Set()
  for (const b of bedomningar) {
    antal.set(b.a, (antal.get(b.a) ?? 0) + 1)
    antal.set(b.b, (antal.get(b.b) ?? 0) + 1)
    gjorda.add([b.a, b.b].sort().join('|'))
  }
  const U = new Map(items.map(it => [it.id, nytta(mod, it.e)]))
  let bast = null
  for (let i = 0; i < 400; i++) {
    const a = items[Math.floor(slump() * items.length)]
    const b = items[Math.floor(slump() * items.length)]
    if (a.id === b.id || gjorda.has([a.id, b.id].sort().join('|'))) continue
    const samma = a.id.split('#')[0] === b.id.split('#')[0]
    const poang = -Math.abs(U.get(a.id) - U.get(b.id)) - 0.35 * ((antal.get(a.id) ?? 0) + (antal.get(b.id) ?? 0)) - (samma ? 0.5 : 0) + slump() * 0.3
    if (!bast || poang > bast.poang) bast = { a: a.id, b: b.id, poang }
  }
  if (!bast) return null
  return slump() < 0.5 ? bast : { a: bast.b, b: bast.a, poang: bast.poang }
}
