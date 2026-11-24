// Utforskande: följer ägarens passform K2 (sketch/roll mot tilltal/stöd/karisma) olika beroende på kundens linje?
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const D = las(path.join(F, 'e6', 'djup.json')).komponenter
const ORD = { premiss: c => ({ ingen: 0, svag: 1, medel: 2, stark: 3 })[c.grundvarde.premiss], utan_efterarbete: c => ({ nej: 0, delvis: 1, ja: 2 })[c.grundvarde.utan_efterarbete], krok: c => ({ ingen: 0, svag: 1, stark: 2 })[c.grundvarde.krok], vandning: c => +c.grundvarde.vandning, hojer_taket: c => +c.grundvarde.hojer_taket, kantighet: c => ({ familjar: 0, lekfull: 1, kantig: 2, vuxen: 3 })[c.sprak.kantighet], tempo: c => ({ lugnt: 0, medel: 1, hogt: 2 })[c.sprak.tempo], klippberoende: c => ({ lite: 0, en_del: 1, mycket: 2 })[c.sprak.klippberoende], bundna_bilder: c => ({ fa: 0, halften: 1, nastan_alla: 2 })[c.forlaga.bundna_bilder], sketch: c => +(c.sprak.strategi === 'sketchvarld'), tilltal: c => +(c.sprak.strategi === 'tilltal' || c.sprak.tilltal === 'till_kamera'), visning: c => +(c.sprak.strategi === 'visning'), karisma: c => +(c.grundvarde.bars_av === 'karisma' || c.sprak.person === 'fokus'), roll: c => +(c.sprak.person === 'roll'), ingen_person: c => +(c.sprak.person === 'ingen'), instagram: c => +(c.sprak.plattform !== 'tiktok'), skadespel: c => c.krav.skadespel, produktion: c => c.krav.produktion, personer: c => c.krav.personer_min, kott: c => +(c.funktion === 'kott'), stod: c => +(c.funktion === 'stod') }
const N = Object.keys(ORD)
const alla = fs.readdirSync(path.join(H, 'v5')).map(f => las(path.join(H, 'v5', f)))
const X = alla.map(c => N.map(n => ORD[n](c) ?? 0)), mu = N.map((_, j) => X.reduce((s, r) => s + r[j], 0) / X.length), sd = N.map((_, j) => Math.sqrt(X.reduce((s, r) => s + (r[j] - mu[j]) ** 2, 0) / X.length) || 1)
const K = (c, i) => N.reduce((s, n, j) => s + ((ORD[n](c) ?? 0) - mu[j]) / sd[j] * D[i].laddningar[n], 0)
const U = las(path.join(H, 'validering', 'urval.json')), A = las(path.join(H, 'validering', 'agare.json'))
const rows = Object.entries(U).flatMap(([k, { klipp }]) => klipp.filter(c => Number.isFinite(A.klipp[k]?.[c.pos]?.passform)).map(c => { const v = las(path.join(H, 'v5', `${c.id}.json`)); return { kund: k, strat: las(path.join(H, 'linje', `${k}.json`)).strategi, y: A.klipp[k][c.pos].passform, k1: K(v, 0), k2: K(v, 1) } }))
for (const [n, f] of [['tilltalskunder (pizzeriamums, kebabbabes, anettesrestaurang)', r => r.strat === 'tilltal'], ['sketchkunder (babulsofficial, chickenstreet, blackstone)', r => r.strat === 'sketchvarld']]) {
  const m = rows.filter(f); console.log(`${n}: n ${m.length}, K1 ${spearman(m.map(r => r.k1), m.map(r => r.y)).toFixed(2)}, K2 ${spearman(m.map(r => r.k2), m.map(r => r.y)).toFixed(2)}`)
}
