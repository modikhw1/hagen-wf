// Utvecklingsutvärdering av harnessen v5 mot ägarens 35 bedömningar i Miles-pass 4–5.
// OBS: det här är inte ett test. Doktrinen skrevs med ägarens ord om just de här klippen, och vikterna i
// h-match5.mjs justerades en gång efter pizzeriamums. Testet är pass 6 med låsta prognoser.
//   node format/h-dev5.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund, poang } from './h-match5.mjs'

const H = path.join(DATA, 'format', 'harness'), V = path.join(H, 'validering')
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const U = las(path.join(V, 'urval.json')), A = las(path.join(V, 'agare.json'))
const kortFil = id => path.join(H, 'v5', `${id}.json`)
const rader = []
for (const [konto, { klipp }] of Object.entries(U)) {
  const lf = path.join(H, 'linje', `${konto}.json`), L = fs.existsSync(lf) ? las(lf) : null
  const mf = path.join(H, 'match5', `${konto}.json`), M = fs.existsSync(mf) ? las(mf) : null
  for (const k of klipp) {
    const a = A.klipp?.[konto]?.[k.pos]; if (!Number.isFinite(a?.passform)) continue
    const c = fs.existsSync(kortFil(k.id)) ? las(kortFil(k.id)) : null
    rader.push({ konto, id: k.id, grupp: k.grupp, agare: a.passform, v0_pro: k.pro_passform, grund: c ? grund(c).p : null, total: c && L ? poang(c, L).total : null, pro5: M?.pro?.find(x => x.id === k.id)?.passform ?? null })
  }
}
const rho = (f, g = r => r.agare) => { const m = rader.filter(r => Number.isFinite(f(r))); return m.length >= 4 ? `${spearman(m.map(g), m.map(f)).toFixed(2)} (n ${m.length})` : `– (n ${m.length})` }
console.log(`${rader.length} bedömningar, ${rader.filter(r => r.grund !== null).length} med kort v5, ${rader.filter(r => r.total !== null).length} med kort och linje`)
console.log(`ägaren mot v0 Pro:            ${rho(r => r.v0_pro)}`)
console.log(`ägaren mot v5 grundvärde:     ${rho(r => r.grund)}`)
console.log(`ägaren mot v5 total:          ${rho(r => r.total)}`)
console.log(`ägaren mot v5 Pro som CM:     ${rho(r => r.pro5)}`)
// Inom klipp: samma klipp hos flera kunder. Säger v5 rätt vilken kund som passar bäst?
const per = {}; for (const r of rader) (per[r.id] ??= []).push(r)
let ratt = 0, fel = 0, lika = 0
for (const x of Object.values(per)) for (let i = 0; i < x.length; i++) for (let j = i + 1; j < x.length; j++) {
  const a = x[i], b = x[j]; if (a.agare === b.agare || a.total === null || b.total === null) continue
  const d = Math.sign(a.agare - b.agare) * Math.sign(a.total - b.total); if (d > 0) ratt++; else if (d < 0) fel++; else lika++
}
console.log(`inom klipp (vilken kund passar bäst): ${ratt} rätt, ${fel} fel, ${lika} lika`)
