// E5: modell × prompt på 40 klipp med ägarens omdöme (förregistrerat i data/format/e5/forregistrering.json).
//   node format/e5.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'

const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), E = path.join(F, 'e5')
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const ids = fs.readFileSync(path.join(E, 'ids.txt'), 'utf8').split(/\r?\n/).filter(Boolean)
const dir = { pro: path.join(H, 'v5'), 'pro-b': path.join(DATA, 'e5', 'pro-b'), 'pro-neutral': path.join(DATA, 'e5', 'pro-neutral'), argon: path.join(DATA, 'e5', 'argon'), flash38: path.join(DATA, 'e5', 'flash38'), 'flash38-kort': path.join(DATA, 'e5', 'flash38-kort'), 'flash38-kort-b': path.join(DATA, 'e5', 'flash38-kort-b'), 'argon-kort': path.join(DATA, 'e5', 'argon-kort'), 'flash35-gratis': path.join(DATA, 'e5', 'flash35-gratis') }
const K = Object.fromEntries(Object.entries(dir).map(([v, d]) => [v, Object.fromEntries(ids.filter(id => fs.existsSync(path.join(d, `${id}.json`))).map(id => [id, las(path.join(d, `${id}.json`))]))]))
const U = las(path.join(H, 'validering', 'urval.json')), A = las(path.join(H, 'validering', 'agare.json'))
const bib = las(path.join(H, 'urval.json')).bibliotek, kalib = las(path.join(F, 'kalib', 'agare.json')).klipp
const par = Object.entries(U).flatMap(([konto, { klipp }]) => klipp.filter(k => Number.isFinite(A.klipp[konto]?.[k.pos]?.passform)).map(k => ({ id: k.id, y: A.klipp[konto][k.pos].passform })))
const bes = bib.filter(k => k.kalla === 'kalib' && kalib[k.nr]?.bibliotek).map(k => ({ id: k.id, y: { ja: 2, villkorat: 1, nej: 0 }[kalib[k.nr].bibliotek] }))
const LAGER = ['grundvarde.premiss', 'grundvarde.hylla', 'grundvarde.bars_av', 'grundvarde.utan_efterarbete', 'grundvarde.krok', 'grundvarde.vandning', 'grundvarde.hojer_taket', 'grundvarde.planerat', 'sprak.strategi', 'sprak.kantighet', 'sprak.tempo', 'sprak.klippberoende', 'sprak.person', 'sprak.tilltal', 'sprak.plattform', 'forlaga.bundna_bilder', 'funktion', 'regler.visning_med_person']
const hamta = (o, p) => p.split('.').reduce((x, k) => x?.[k], o)
const rho = (v, d) => { const m = d.filter(r => K[v][r.id]); return m.length >= 8 ? { r: spearman(m.map(r => grund(K[v][r.id]).p), m.map(r => r.y)), n: m.length } : { r: NaN, n: m.length } }
const medel = a => a.reduce((s, x) => s + x, 0) / a.length
const ut = {}
console.log('villkor'.padEnd(12), 'klipp', 'passform', 'bibliotek', 'tokens', 'sek')
for (const v of Object.keys(dir)) {
  const n = Object.keys(K[v]).length; if (!n) { console.log(v.padEnd(12), 0); continue }
  const a = rho(v, par), b = rho(v, bes), t = Object.values(K[v]).map(x => x.tokens).filter(Number.isFinite), ms = Object.values(K[v]).map(x => x.ms).filter(Number.isFinite)
  ut[v] = { n, passform: a, bibliotek: b, tokens: t.length ? Math.round(medel(t)) : null, sek: ms.length ? +(medel(ms) / 1000).toFixed(1) : null }
  console.log(v.padEnd(12), String(n).padStart(5), `${a.r.toFixed(2)} (${a.n})`.padStart(9), `${b.r.toFixed(2)} (${b.n})`.padStart(10), String(ut[v].tokens ?? '–').padStart(6), String(ut[v].sek ?? '–').padStart(5))
}
console.log('\nexakt överensstämmelse med pro per lager')
console.log('lager'.padEnd(30), Object.keys(dir).filter(v => v !== 'pro').map(v => v.padStart(11)).join(''))
ut.lager = {}
for (const l of LAGER) {
  const rad = Object.keys(dir).filter(v => v !== 'pro').map(v => { const g = ids.filter(id => K.pro[id] && K[v][id]); return g.length ? g.filter(id => JSON.stringify(hamta(K.pro[id], l)) === JSON.stringify(hamta(K[v][id], l))).length / g.length : NaN })
  ut.lager[l] = rad
  console.log(l.padEnd(30), rad.map(x => (Number.isFinite(x) ? `${Math.round(100 * x)} %` : '–').padStart(11)).join(''))
}
fs.writeFileSync(path.join(E, 'analys.json'), JSON.stringify(ut, null, 1))
