// Utforskande (4 nov 2026): bär ägarens omdöme nytta via likhet? Ägarens klippvärde (biblioteksbeslut 1–27
// och medelpassform i pass 4–5, rangnormerat per källa) sprids till E6-klippen med k närmaste grannar i
// v5-lagren (standardiserade, cosinus). Prövas mot visningar inom konto, jämfört med grund().
//   node format/knn.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'
const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), E = path.join(F, 'e6'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const D = las(path.join(E, 'djup.json')).komponenter
const N = Object.keys(D[0].laddningar)
const ORD = { premiss: c => ({ ingen: 0, svag: 1, medel: 2, stark: 3 })[c.grundvarde.premiss], utan_efterarbete: c => ({ nej: 0, delvis: 1, ja: 2 })[c.grundvarde.utan_efterarbete], krok: c => ({ ingen: 0, svag: 1, stark: 2 })[c.grundvarde.krok], vandning: c => +c.grundvarde.vandning, hojer_taket: c => +c.grundvarde.hojer_taket, kantighet: c => ({ familjar: 0, lekfull: 1, kantig: 2, vuxen: 3 })[c.sprak.kantighet], tempo: c => ({ lugnt: 0, medel: 1, hogt: 2 })[c.sprak.tempo], klippberoende: c => ({ lite: 0, en_del: 1, mycket: 2 })[c.sprak.klippberoende], bundna_bilder: c => ({ fa: 0, halften: 1, nastan_alla: 2 })[c.forlaga.bundna_bilder], sketch: c => +(c.sprak.strategi === 'sketchvarld'), tilltal: c => +(c.sprak.strategi === 'tilltal' || c.sprak.tilltal === 'till_kamera'), visning: c => +(c.sprak.strategi === 'visning'), karisma: c => +(c.grundvarde.bars_av === 'karisma' || c.sprak.person === 'fokus'), roll: c => +(c.sprak.person === 'roll'), ingen_person: c => +(c.sprak.person === 'ingen'), instagram: c => +(c.sprak.plattform !== 'tiktok'), skadespel: c => c.krav.skadespel, produktion: c => c.krav.produktion, personer: c => c.krav.personer_min, kott: c => +(c.funktion === 'kott'), stod: c => +(c.funktion === 'stod') }
const vek = c => N.map(n => ORD[n](c) ?? 0)
const rang = a => { const s = a.map((v, i) => [v, i]).sort((x, y) => x[0] - y[0]), r = []; let i = 0; while (i < s.length) { let j = i; while (j + 1 < s.length && s[j + 1][0] === s[i][0]) j++; for (let k = i; k <= j; k++) r[s[k][1]] = (i + j) / 2 / (a.length - 1); i = j + 1 } return r }
// Ägarens klippvärde.
const bib = las(path.join(H, 'urval.json')).bibliotek, kalib = las(path.join(F, 'kalib', 'agare.json')).klipp
const U = las(path.join(H, 'validering', 'urval.json')), A = las(path.join(H, 'validering', 'agare.json'))
const b1 = bib.filter(k => k.kalla === 'kalib' && kalib[k.nr]?.bibliotek).map(k => ({ id: k.id, y: { ja: 2, villkorat: 1, nej: 0 }[kalib[k.nr].bibliotek] }))
const pm = {}; for (const [k, { klipp }] of Object.entries(U)) for (const c of klipp) { const p = A.klipp[k]?.[c.pos]?.passform; if (Number.isFinite(p)) (pm[c.id] ??= []).push(p) }
const b2 = Object.entries(pm).map(([id, v]) => ({ id, y: v.reduce((s, x) => s + x, 0) / v.length }))
const agare = new Map(); for (const src of [b1, b2]) { const r = rang(src.map(x => x.y)); src.forEach((x, i) => agare.set(x.id, agare.has(x.id) ? (agare.get(x.id) + r[i]) / 2 : r[i])) }
const ref = [...agare.keys()].map(id => ({ id, v: vek(las(path.join(H, 'v5', `${id}.json`))), y: agare.get(id) }))
const urval = las(path.join(E, 'urval.json')).filter(k => fs.existsSync(path.join(E, 'kort', `${k.id}.json`))).map(k => ({ ...k, c: las(path.join(E, 'kort', `${k.id}.json`)) }))
const allaV = [...ref.map(r => r.v), ...urval.map(x => vek(x.c))]
const mu = N.map((_, j) => allaV.reduce((s, v) => s + v[j], 0) / allaV.length), sd = N.map((_, j) => Math.sqrt(allaV.reduce((s, v) => s + (v[j] - mu[j]) ** 2, 0) / allaV.length) || 1)
const z = v => v.map((x, j) => (x - mu[j]) / sd[j]), cos = (a, b) => { let s = 0, na = 0, nb = 0; for (let i = 0; i < a.length; i++) { s += a[i] * b[i]; na += a[i] ** 2; nb += b[i] ** 2 } return s / Math.sqrt(na * nb) }
const refZ = ref.map(r => ({ ...r, z: z(r.v) }))
const knn = (v, k) => { const zv = z(v); const g = refZ.map(r => ({ y: r.y, s: cos(zv, r.z) })).sort((a, b) => b.s - a.s).slice(0, k); const w = g.map(x => Math.max(x.s, 0) + 1e-6); return g.reduce((s, x, i) => s + x.y * w[i], 0) / w.reduce((s, x) => s + x, 0) }
// Självtest: leave-one-out på ägarens egna klipp.
for (const k of [3, 5, 8]) { const loo = refZ.map(r => { const other = refZ.filter(x => x.id !== r.id); const g = other.map(x => ({ y: x.y, s: cos(r.z, x.z) })).sort((a, b) => b.s - a.s).slice(0, k); return g.reduce((s, x) => s + x.y, 0) / k }); console.log(`leave-one-out på ägarens ${refZ.length} klipp, k ${k}: rho ${spearman(loo, refZ.map(r => r.y)).toFixed(2)}`) }
const konton = [...new Set(urval.map(k => k.konto))]
const inom = fx => { const rs = []; for (const k of konton) { const l = urval.filter(x => x.konto === k), x = l.map(fx); if (new Set(x).size > 1) rs.push(spearman(x, l.map(r => r.rv))) } return rs.reduce((s, v) => s + v, 0) / rs.length }
for (const k of [3, 5, 8]) console.log(`E6 nytta inom konto, ägarens omdöme spritt med k ${k}: ${inom(x => knn(vek(x.c), k)).toFixed(3)}`)
console.log(`E6 nytta inom konto, grund(): ${inom(x => grund(x.c).p).toFixed(3)}`)
