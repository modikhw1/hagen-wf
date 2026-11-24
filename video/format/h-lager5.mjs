// Vilka v5-lager bär vad? Tre facit hålls isär (4 nov 2026):
//   preferens = ägarens omdöme: passform i pass 4–5 (35 par) och biblioteksbeslutet för klipp 1–27
//   nytta     = utfall mot kontots egen norm (rv = residual för visningar, rl = gillanden; profil/baslinje.json)
//   sanning   = stabilitet mellan körningar och modeller (mäts i e5.mjs)
// Utforskande: många test på litet n, så |rho| < 0,35 ska läsas som brus.
//   node format/h-lager5.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'

const H = path.join(DATA, 'format', 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const V5 = Object.fromEntries(fs.readdirSync(path.join(H, 'v5')).map(f => [f.replace(/\.json$/, ''), las(path.join(H, 'v5', f))]))
const bib = las(path.join(H, 'urval.json')).bibliotek
const kalib = las(path.join(DATA, 'format', 'kalib', 'agare.json')).klipp
const bas = new Map(las(path.join(DATA, 'profil', 'baslinje.json')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const U = las(path.join(H, 'validering', 'urval.json')), A = las(path.join(H, 'validering', 'agare.json'))

// Lager som tal (ordinalt eller 0/1).
const ORD = {
  'grundvarde.premiss': { ingen: 0, svag: 1, medel: 2, stark: 3 }, 'grundvarde.utan_efterarbete': { nej: 0, delvis: 1, ja: 2 },
  'grundvarde.krok': { ingen: 0, svag: 1, stark: 2 }, 'grundvarde.hylla': { ute: 0, capcut_referens: 1, situation: 1, mitten: 2, karna: 3 },
  'sprak.kantighet': { familjar: 0, lekfull: 1, kantig: 2, vuxen: 3 }, 'sprak.tempo': { lugnt: 0, medel: 1, hogt: 2 },
  'sprak.klippberoende': { lite: 0, en_del: 1, mycket: 2 }, 'forlaga.bundna_bilder': { fa: 0, halften: 1, nastan_alla: 2 },
  'krav.skadespel': null, 'krav.produktion': null, 'krav.personer_min': null,
}
const BOOL = ['grundvarde.vandning', 'grundvarde.planerat', 'grundvarde.hojer_taket', 'regler.visning_med_person', 'evergreen']
const KAT = { 'grundvarde.bars_av': ['ide', 'struktur', 'karisma', 'produkt', 'produktion'], 'sprak.strategi': ['sketchvarld', 'tilltal', 'visning', 'premium_stamning', 'kampanj'], 'sprak.person': ['fokus', 'behallare', 'roll', 'ingen'], 'sprak.plattform': ['tiktok', 'instagram'], funktion: ['kott', 'stod', 'utanfor'] }
const hamta = (o, p) => p.split('.').reduce((x, k) => x?.[k], o)
function lager(c) {
  const ut = {}
  for (const [p, m] of Object.entries(ORD)) { const v = hamta(c, p); ut[p] = m ? m[v] : v }
  for (const p of BOOL) ut[p] = hamta(c, p) ? 1 : 0
  for (const [p, vs] of Object.entries(KAT)) for (const v of vs) ut[`${p}=${v}`] = hamta(c, p) === v ? 1 : 0
  ut.grund = grund(c).p
  return ut
}

// Tre datamängder.
const pref1 = Object.entries(U).flatMap(([konto, { klipp }]) => klipp.filter(k => Number.isFinite(A.klipp[konto]?.[k.pos]?.passform) && V5[k.id]).map(k => ({ y: A.klipp[konto][k.pos].passform, x: lager(V5[k.id]) })))
const pref2 = bib.filter(k => k.kalla === 'kalib' && kalib[k.nr] && V5[k.id]).map(k => ({ y: { ja: 2, villkorat: 1, nej: 0 }[kalib[k.nr].bibliotek], x: lager(V5[k.id]) })).filter(r => Number.isFinite(r.y))
const nytta = bib.filter(k => V5[k.id] && bas.has(k.id)).map(k => ({ y: bas.get(k.id).rv, yl: bas.get(k.id).rl, kalla: k.kalla, x: lager(V5[k.id]) }))
const nyttaOpartisk = nytta.filter(r => r.kalla === 'kalib')

const nycklar = Object.keys(pref1[0].x)
const r = (d, k, f = x => x.y) => { const m = d.filter(x => Number.isFinite(x.x[k]) && Number.isFinite(f(x))); const v = new Set(m.map(x => x.x[k])); return m.length >= 8 && v.size > 1 ? spearman(m.map(x => x.x[k]), m.map(f)) : NaN }
const rad = nycklar.map(k => ({ k, p1: r(pref1, k), p2: r(pref2, k), n: r(nyttaOpartisk, k), nl: r(nyttaOpartisk, k, x => x.yl) }))
const f = v => Number.isFinite(v) ? (v >= 0 ? '+' : '') + v.toFixed(2) : '  – '
console.log(`preferens 1: passform pass 4–5 (n ${pref1.length}); preferens 2: bibliotek klipp 1–27 (n ${pref2.length}); nytta: visningar och gillanden mot kontots norm, kalibreringsklippen (n ${nyttaOpartisk.length}, ej valda på utfall)`)
console.log('lager'.padEnd(34), 'passform', 'bibliotek', 'visningar', 'gillanden')
for (const x of rad.sort((a, b) => Math.abs(b.p1 || 0) + Math.abs(b.p2 || 0) - Math.abs(a.p1 || 0) - Math.abs(a.p2 || 0))) console.log(x.k.padEnd(34), f(x.p1).padStart(8), f(x.p2).padStart(9), f(x.n).padStart(9), f(x.nl).padStart(9))
fs.writeFileSync(path.join(H, 'lager5.json'), JSON.stringify({ n: { pref1: pref1.length, pref2: pref2.length, nytta: nyttaOpartisk.length }, rad }, null, 1))
