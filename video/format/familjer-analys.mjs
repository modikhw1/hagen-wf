// HF1/HF2 (data/format/familjer/forregistrering.json): repertoaren med ägarens formatfamiljer i stället för Lite-typen.
// Samma par och samma mått som format/repertoar.mjs. Familjerna låstes innan klassningen.
//   node format/familjer-analys.mjs [--dump]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'

const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const H = path.join(DATA, 'format', 'harness')
const SAL = path.join(DATA, 'bank', 'sallning')
const FAMJ = las(path.join(DATA, 'format', 'familjer', 'familjer.json'))
const sal = id => { const f = path.join(SAL, id + '.json'); if (!fs.existsSync(f) || !FAMJ[id]) return null; return { ...las(f), typ: FAMJ[id] } }

// 1. Paren
const par = []
const V = las(path.join(H, 'validering', 'agare.json')), U = las(path.join(H, 'validering', 'urval.json'))
for (const [k, svar] of Object.entries(V.klipp)) for (const [pos, s] of Object.entries(svar)) {
  const c = U[k].klipp.find(x => String(x.pos) === pos); if (!c || !Number.isFinite(s.passform)) continue
  par.push({ pass: '4-5', konto: k, pos: +pos, id: c.id, agare: s.passform, rek: s.rek })
}
const O6 = las(path.join(H, 'pass6', 'ordning.json')), A6 = las(path.join(H, 'pass6', 'agare.json'))
for (const [k, ids] of Object.entries(O6)) ids.forEach((id, i) => {
  const s = A6.klipp[k]?.[i + 1]; if (s) par.push({ pass: '6', konto: k, pos: i + 1, id, agare: s.passform, rek: s.rek })
})

// 2. Kundens historik: lista (datum, nyast först) + sållningstyp
const hist = {}
for (const k of new Set(par.map(p => p.konto))) {
  const L = las(path.join(DATA, 'bank', k, 'lista.json')).klipp
    .map(x => ({ ...x, s: sal(`${k}-${x.id}`) })).filter(x => x.s)
    .sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
  hist[k] = L
}
const andel = (L, typ) => L.length ? L.filter(x => x.s.typ === typ).length / L.length : NaN

// 3. Särdrag per par
for (const p of par) {
  const c = sal(p.id); p.typ = c?.typ ?? null; p.c = c
  const L = hist[p.konto]
  if (!p.typ || !L.length) continue
  p.hel = andel(L, p.typ)
  p.s10 = andel(L.slice(0, 10), p.typ)
  p.s30 = andel(L.slice(0, 30), p.typ)
  p.antal = L.filter(x => x.s.typ === p.typ).length
  p.nagonsin = p.antal >= 2 ? 1 : 0
  // närmast i tid: hur många klipp sedan senast samma typ (0 = senaste)
  const j = L.findIndex(x => x.s.typ === p.typ); p.sedan = j < 0 ? L.length : j
  // personnärvaro: klippet har person, kunden har person i historiken
  p.kundPerson = L.reduce((s, x) => s + (x.s.andel_med_person ?? 0), 0) / L.length
  p.klippPerson = c.andel_med_person ?? NaN
  p.personGap = Math.abs(p.klippPerson - p.kundPerson)
  p.inne = c.inne_i_verksamheten ? 1 : 0
}

const ok = par.filter(p => Number.isFinite(p.hel))
console.log(`${par.length} par, ${ok.length} med sållningstyp för klipp och kund (${par.length - ok.length} saknar: ${par.filter(p => !Number.isFinite(p.hel)).map(p => p.id).join(', ')})`)

// Kundcentrering: ägarens betyg minus kundens medel (det inom kund som ska förklaras)
const medel = {}; for (const k of new Set(ok.map(p => p.konto))) { const x = ok.filter(p => p.konto === k); medel[k] = x.reduce((s, p) => s + p.agare, 0) / x.length }
ok.forEach(p => { p.agareC = p.agare - medel[p.konto] })
const cen = f => { const m = {}; for (const k in medel) { const x = ok.filter(p => p.konto === k).map(f).filter(Number.isFinite); m[k] = x.reduce((a, b) => a + b, 0) / x.length } return p => f(p) - m[p.konto] }

let fro = 7; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
// Permutation inom kund (behåller kundnivån), ensidigt
function permInom(f) {
  const x = ok.map(f), y = ok.map(p => p.agare), obs = spearman(x, y)
  const grupper = {}; ok.forEach((p, i) => (grupper[p.konto] ??= []).push(i))
  let e = 0
  for (let t = 0; t < 5000; t++) {
    const z = [...y]
    for (const idx of Object.values(grupper)) { const v = idx.map(i => y[i]); for (let i = v.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [v[i], v[j]] = [v[j], v[i]] } idx.forEach((i, n) => { z[i] = v[n] }) }
    if (spearman(x, z) >= obs) e++
  }
  return { rho: obs, p: (e + 1) / 5001 }
}
const rad = (namn, f) => {
  const a = permInom(f), w = spearman(ok.map(cen(f)), ok.map(p => p.agareC))
  console.log(`${namn.padEnd(34)} rho ${a.rho.toFixed(2)}  inom kund ${w.toFixed(2)}  p(inom) ${a.p.toFixed(3)}`)
}
console.log('\nSärdrag mot ägarens passform (n ' + ok.length + ', ' + Object.keys(medel).length + ' kunder)')
rad('andel samma typ, hela historiken', p => p.hel)
rad('andel samma typ, senaste 30', p => p.s30)
rad('andel samma typ, senaste 10', p => p.s10)
rad('typen förekommer (minst 2 gånger)', p => p.nagonsin)
rad('log antal av samma typ', p => Math.log1p(p.antal))
rad('klipp sedan senast samma typ (neg)', p => -p.sedan)
rad('personglapp klipp mot kund (neg)', p => -p.personGap)
rad('inne i verksamheten', p => p.inne)

console.log('\nKundmedel (ägaren):', Object.entries(medel).map(([k, m]) => `${k} ${m.toFixed(2)}`).join(', '))
if (process.argv.includes('--dump')) for (const p of ok) console.log(`${p.pass} ${p.konto.padEnd(22)} ${String(p.pos)} ${p.typ.padEnd(22)} ägare ${p.agare}  hel ${p.hel.toFixed(2)} s10 ${p.s10.toFixed(1)} antal ${p.antal} sedan ${p.sedan}`)
