// Analys av sekvenstest C: stämmer Pros rangordning av fem klipp i en sekvens bättre med ägaren än
// Pros omdöme om ett klipp i taget (v3 utan exempel)?
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
const F = path.join(DATA, 'format')
const u = JSON.parse(fs.readFileSync(path.join(F, 'kalib', 'urval.json'), 'utf8')), a = JSON.parse(fs.readFileSync(path.join(F, 'kalib', 'agare.json'), 'utf8')).klipp
const res = JSON.parse(fs.readFileSync(path.join(F, 'sekvens', 'resultat-BC.json'), 'utf8')).filter(r => r.g != null && r.r)
const P = { ja: 2, villkorat: 1, nej: 0 }
const nr = id => u.findIndex(k => k.id === id) + 1
const v3 = id => JSON.parse(fs.readFileSync(path.join(F, 'v3-gemini-3.1-pro-preview', `${id}.json`), 'utf8'))
const medel = x => x.reduce((s, v) => s + v, 0) / x.length
const rows = []; let bS = 0, bE = 0, n = 0
for (const r of res) {
  const ag = r.ids.map(id => P[a[nr(id)].bibliotek])
  const rang = r.r.rangordning
  const poang = r.ids.map((_, i) => 5 - rang.indexOf(i + 1))
  const ensam = r.ids.map(id => P[v3(id).bibliotek.beslut])
  const seqBib = r.r.klipp.map(k => P[k.bibliotek])
  r.ids.forEach((id, i) => { n++; if (seqBib[i] === ag[i]) bS++; if (ensam[i] === ag[i]) bE++ })
  rows.push({ g: r.g + 1, rk: r.riktning, rang: spearman(poang, ag), seqBib: spearman(seqBib, ag), ensam: spearman(ensam, ag), ordning: rang.join('') })
}
const f = x => Number.isFinite(x) ? x.toFixed(2) : ' - '
for (const x of rows) console.log(`grupp ${x.g} ${x.rk}: rangordning ${f(x.rang)} | sekvensens bibliotek ${f(x.seqBib)} | ensam v3 ${f(x.ensam)} | ordning ${x.ordning}`)
const m = k => medel(rows.map(x => x[k]).filter(Number.isFinite)).toFixed(3)
console.log(`\nsnitt rho mot ägaren: rangordning i sekvens ${m('rang')}, biblioteksbeslut i sekvens ${m('seqBib')}, ensam v3 ${m('ensam')}`)
console.log(`exakt biblioteksbeslut: i sekvens ${bS}/${n}, ensam v3 ${bE}/${n}`)
const byId = {}
for (const r of res) r.ids.forEach((id, i) => { (byId[id] ??= {})[r.riktning] = 5 - r.r.rangordning.indexOf(i + 1) })
const fr = Object.values(byId).filter(x => x.fram != null && x.bak != null)
console.log(`rangplats framlänges mot baklänges: rho ${spearman(fr.map(x => x.fram), fr.map(x => x.bak)).toFixed(2)}, samma plats ${fr.filter(x => x.fram === x.bak).length}/${fr.length}`)
// positionsbias: medelplats för klippet på position 1 och 5
const plats = p => medel(res.map(r => 5 - r.r.rangordning.indexOf(p)))
console.log(`medelpoäng (5 = bäst) för klippet som visas först ${plats(1).toFixed(2)}, sist ${plats(5).toFixed(2)}`)
