// Analys av serietestet enligt data/format/serie/forregistrering.json.
//   node format/serie-analys.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
const DIRS = (process.argv.includes('--dir') ? process.argv[process.argv.indexOf('--dir') + 1] : 'serie').split(',')
const S = path.join(DATA, 'format', DIRS[0])
const bas = new Map(JSON.parse(fs.readFileSync(path.join(DATA, 'profil', 'baslinje.json'), 'utf8')).rader.map(r => [`${r.konto}-${r.id}`, r]))
const lite = path.join(DATA, 'format', 'e4', 'lager-gemini-3.1-flash-lite')
const serier = DIRS.flatMap(d => { const D = path.join(DATA, 'format', d); return fs.readdirSync(D).filter(f => f.endsWith('.json') && !['forregistrering.json', 'analys.json'].includes(f)).map(f => JSON.parse(fs.readFileSync(path.join(D, f), 'utf8'))) })
const medel = a => { const v = a.filter(Number.isFinite); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : NaN }
let fro = 21; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }

// Per klipp: utfall och seriens märkning.
const konton = serier.map(x => {
  const huvud = [...x.frontfigurer].sort((a, b) => b.klipp.length - a.klipp.length)[0]
  const iFormat = new Set(x.format.flatMap(f => f.klipp)), medPerson = new Set(x.frontfigurer.flatMap(p => p.klipp))
  const klipp = x.ids.map((id, i) => {
    const r = bas.get(id) ?? {}, nr = i + 1, k = x.klipp.find(c => c.nr === nr) ?? {}
    const l = fs.existsSync(path.join(lite, `${id}.json`)) ? JSON.parse(fs.readFileSync(path.join(lite, `${id}.json`), 'utf8')) : null
    return { id, nr, rv: r.rv, rl: r.rl, rs: r.rs, huvud: huvud ? huvud.klipp.includes(nr) : null, person: medPerson.has(nr), format: iFormat.has(nr), anknyter: !!k.anknyter, roll: k.roll, lite_personal: l ? l.personal : null, lite_sketch_person: l ? (l.roll && l.andel_person >= 2) : null }
  })
  return { konto: x.konto, grupp: x.grupp, n: klipp.length, frontfigurer: x.frontfigurer.length, format: x.format.length, planerat: x.planerat, inside: x.inside, klipp, huvudetikett: huvud?.etikett, andelPerson: medel(klipp.map(k => k.person ? 1 : 0)), rvSd: Math.sqrt(medel(klipp.map(k => (k.rv - medel(klipp.map(c => c.rv))) ** 2))) }
})

function inomKonto(falt, utfall, perm = 5000, filt = () => true, min = 2) {
  const par = konton.map(k => ({ v: k.klipp.filter(c => Number.isFinite(c[utfall]) && c[falt] != null && filt(c)) })).map(o => ({ ...o, a: o.v.filter(c => c[falt]).map(c => c[utfall]), b: o.v.filter(c => !c[falt]).map(c => c[utfall]) })).filter(o => o.a.length >= min && o.b.length >= min)
  const eff = medel(par.map(o => medel(o.a) - medel(o.b)))
  let ext = 0
  for (let t = 0; t < perm; t++) { const e = medel(par.map(o => { const all = bl([...o.a, ...o.b]); return medel(all.slice(0, o.a.length)) - medel(all.slice(o.a.length)) })); if (Math.abs(e) >= Math.abs(eff)) ext++ }
  return { konton: par.length, effekt: eff, ggr: 10 ** eff, andelPositiv: par.filter(o => medel(o.a) > medel(o.b)).length / par.length, p: (ext + 1) / (perm + 1) }
}
function mellanGrupper(falt) {
  const a = konton.filter(k => k.grupp !== 'bank').map(k => k[falt]), b = konton.filter(k => k.grupp === 'bank').map(k => k[falt])
  const d = medel(a) - medel(b), all = [...a, ...b]; let ext = 0
  for (let t = 0; t < 5000; t++) { const p = bl(all); if (Math.abs(medel(p.slice(0, a.length)) - medel(p.slice(a.length))) >= Math.abs(d)) ext++ }
  return { valda: medel(a), bank: medel(b), p: (ext + 1) / 5001 }
}
const f = x => Number.isFinite(x) ? (x >= 0 ? '+' : '') + x.toFixed(3) : ' - '
console.log(`${konton.length} serier (${konton.filter(k => k.grupp !== 'bank').length} valda, ${konton.filter(k => k.grupp === 'bank').length} bank), ${konton.reduce((s, k) => s + k.n, 0)} klipp`)
console.log(`konton med minst en frontfigur: ${konton.filter(k => k.frontfigurer).length}; med ett återkommande format: ${konton.filter(k => k.format).length}`)
const ut = { HS: {} }
for (const [h, falt] of [['HS1', 'huvud'], ['HS2', 'format'], ['HS3', 'anknyter']]) for (const u of ['rv', 'rl', 'rs']) {
  const r = inomKonto(falt, u); ut.HS[`${h} ${u}`] = r
  console.log(`${h} ${falt.padEnd(9)} → ${u}: konton ${r.konton}, skillnad ${f(r.effekt)} log10 (×${r.ggr.toFixed(2)}), andel konton + ${r.andelPositiv.toFixed(2)}, p ${r.p.toFixed(4)}`)
}
{ const r = inomKonto('person', 'rv', 5000, c => c.lite_sketch_person, 1); ut.HS.HS6 = r; console.log(`HS6 återkommande person bland sketcher med person → rv: konton ${r.konton}, ×${r.ggr.toFixed(2)}, andel konton + ${r.andelPositiv.toFixed(2)}, p ${r.p.toFixed(4)}`) }
{ const r = inomKonto('person', 'rv', 5000, c => c.lite_personal, 1); console.log(`   (kontroll) återkommande person bland alla klipp med personal → rv: konton ${r.konton}, ×${r.ggr.toFixed(2)}, p ${r.p.toFixed(4)}`) }
for (const falt of ['andelPerson', 'inside', 'planerat', 'frontfigurer', 'format']) { const r = mellanGrupper(falt); ut.HS[`HS4 ${falt}`] = r; console.log(`HS4 ${falt.padEnd(13)} valda ${r.valda.toFixed(2)}  bank ${r.bank.toFixed(2)}  p ${r.p.toFixed(4)}`) }
const r5 = spearman(konton.map(k => k.andelPerson), konton.map(k => k.rvSd)); ut.HS.HS5 = r5
console.log(`HS5 andel med återkommande person mot spridning i rv: rho ${f(r5)}`)
// Rimlighetskoll: frontfigur i serien mot Lites "personal" i samma klipp
const kk = konton.flatMap(k => k.klipp).filter(c => c.lite_personal != null)
console.log(`\nrimlighet: klipp med återkommande person som Lite (ensam) säger har personal ${(medel(kk.filter(c => c.person).map(c => c.lite_personal ? 1 : 0)) * 100).toFixed(0)} %, utan ${(medel(kk.filter(c => !c.person).map(c => c.lite_personal ? 1 : 0)) * 100).toFixed(0)} %`)
console.log('\nfrontfigurer (exempel):', konton.filter(k => k.huvudetikett).slice(0, 14).map(k => `${k.konto}: ${k.huvudetikett} (${k.klipp.filter(c => c.huvud).length}/${k.n})`).join(' | '))
fs.writeFileSync(path.join(S, DIRS.length > 1 ? 'analys-sammanslagen.json' : 'analys.json'), JSON.stringify({ ...ut, konton }, null, 1))
