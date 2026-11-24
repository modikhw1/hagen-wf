// Seriepass, kandidater (förregistrering data/format/serie9/forregistrering.json). Inga anrop.
// Per kund: bibliotekskort (kärna, mitten) med familj ur familjer-lokal.json, repertoarnivå i kundens historik
// och nytta62. Väljer två osedda kort per nivå (hog, lag, aldrig) med högst nytta62, kärna före mitten.
//   node format/repertoar-forslag.mjs [konto1,konto2]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const las = f => JSON.parse(fs.readFileSync(f, 'utf8')), H = path.join(DATA, 'format', 'harness')
const FAM = Object.fromEntries(Object.entries(las(path.join(DATA, 'format', 'familjer', 'familjer-lokal.json'))).map(([k, v]) => [k, v.familj]))
const B = las(path.join(H, 'bibliotek-v6.json')), kort = []
;(function w(o) { if (Array.isArray(o)) o.forEach(w); else if (o && typeof o === 'object') { if (o.id && 'nytta_v62' in o) kort.push(o); else Object.values(o).forEach(w) } })(B)
// sett av ägaren: pass 4–8
const sett = new Set()
const U = las(path.join(H, 'validering', 'urval.json')); Object.values(U).forEach(v => v.klipp.forEach(c => sett.add(c.id)))
Object.values(las(path.join(H, 'pass6', 'ordning.json'))).flat().forEach(id => sett.add(id))
las(path.join(H, 'pass7', 'forregistrering.json')).par.forEach(p => { sett.add(p.vanster.id); sett.add(p.hoger.id) })
las(path.join(H, 'pass8', 'forregistrering.json')).rader.forEach(r => sett.add(r.kalla))
const kunder = (process.argv[2] || fs.readdirSync(path.join(H, 'linje')).map(f => f.replace(/\.json$/, '')).join(',')).split(',')
const niva = n => n >= 10 ? 'hog' : n >= 2 ? 'lag' : 'aldrig', rank = { karna: 2, mitten: 1 }
const ut = {}
for (const k of kunder) {
  const hist = las(path.join(DATA, 'bank', k, 'lista.json')).klipp.map(x => FAM[`${k}-${x.id}`]).filter(Boolean)
  const antal = f => hist.filter(x => x === f).length
  const kand = kort.filter(c => rank[c.hylla] && !sett.has(c.id) && FAM[c.id] && !c.id.startsWith(k + '-'))
    .map(c => ({ id: c.id, url: c.url, hylla: c.hylla, familj: FAM[c.id], antal: antal(FAM[c.id]), niva: niva(antal(FAM[c.id])), nytta62: c.nytta_v62, karna: c.karna }))
  const val = []
  for (const n of ['hog', 'lag', 'aldrig']) val.push(...kand.filter(c => c.niva === n).sort((a, b) => rank[b.hylla] - rank[a.hylla] || b.nytta62 - a.nytta62).filter((c, i, a) => a.findIndex(x => x.familj === c.familj) === i || i < 1).slice(0, 2))
  ut[k] = { historik: hist.length, val }
  console.log(`\n${k} (${hist.length} klipp): ${val.map(c => `${c.niva}/${c.familj}(${c.antal})/${c.hylla}`).join('  ')}`)
}
fs.writeFileSync(path.join(DATA, 'format', 'serie9', 'kandidater.json'), JSON.stringify(ut, null, 1))
