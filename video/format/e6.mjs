// E6: preferens mot nytta. v5-lager mot utfall inom konto (förregistrerat i data/format/e6/forregistrering.json).
//   node format/e6.mjs [--kort <katalog under data/format/e6>]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { spearman } from '../profil/baslinje.mjs'
import { grund } from './h-match5.mjs'

const args = process.argv.slice(2)
const E = path.join(DATA, 'format', process.env.E6DIR ?? 'e6'), KD = path.join(E, args.includes('--kort') ? args[args.indexOf('--kort') + 1] : 'kort')
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const urval = las(path.join(E, 'urval.json')).filter(k => fs.existsSync(path.join(KD, `${k.id}.json`))).map(k => ({ ...k, c: las(path.join(KD, `${k.id}.json`)) }))
const hamta = (o, p) => p.split('.').reduce((x, k) => x?.[k], o)
const ORD = { 'grundvarde.premiss': { ingen: 0, svag: 1, medel: 2, stark: 3 }, 'grundvarde.hylla': { ute: 0, capcut_referens: 1, situation: 1, mitten: 2, karna: 3 }, 'grundvarde.utan_efterarbete': { nej: 0, delvis: 1, ja: 2 }, 'grundvarde.krok': { ingen: 0, svag: 1, stark: 2 }, 'sprak.klippberoende': { lite: 0, en_del: 1, mycket: 2 }, 'sprak.kantighet': { familjar: 0, lekfull: 1, kantig: 2, vuxen: 3 }, 'sprak.tempo': { lugnt: 0, medel: 1, hogt: 2 }, 'forlaga.bundna_bilder': { fa: 0, halften: 1, nastan_alla: 2 } }
const BOOL = ['grundvarde.vandning', 'grundvarde.hojer_taket', 'grundvarde.planerat', 'regler.visning_med_person', 'regler.trendljud_i_visning']
const KAT = { 'sprak.strategi': ['sketchvarld', 'tilltal', 'visning', 'premium_stamning', 'kampanj', 'trend'], 'sprak.person': ['fokus', 'behallare', 'roll', 'ingen'], 'sprak.plattform': ['tiktok', 'instagram'], 'grundvarde.bars_av': ['ide', 'struktur', 'karisma', 'produkt', 'produktion', 'trend'], funktion: ['kott', 'stod', 'utanfor'] }
function lager(c, modal) {
  const ut = { grund: grund(c).p }
  for (const [p, m] of Object.entries(ORD)) ut[p] = m[hamta(c, p)]
  for (const p of BOOL) ut[p] = hamta(c, p) ? 1 : 0
  for (const [p, vs] of Object.entries(KAT)) for (const v of vs) ut[`${p}=${v}`] = hamta(c, p) === v ? 1 : 0
  ut['medstroms (kontots vanligaste strategi)'] = c.sprak.strategi === modal ? 1 : 0
  return ut
}
const konton = [...new Set(urval.map(k => k.konto))]
const perKonto = Object.fromEntries(konton.map(k => {
  const l = urval.filter(x => x.konto === k), rakna = {}
  for (const x of l) rakna[x.c.sprak.strategi] = (rakna[x.c.sprak.strategi] ?? 0) + 1
  const modal = Object.entries(rakna).sort((a, b) => b[1] - a[1])[0][0]
  return [k, l.map(x => ({ rv: x.rv, rl: x.rl, x: lager(x.c, modal) }))]
}))
let fro = 66; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const bl = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [b[i], b[j]] = [b[j], b[i]] } return b }
// Medel över konton av Spearman inom konto; konton där lagret inte varierar hoppas över.
function inom(nyckel, utfall, perm = 0) {
  const stat = rows => { const rs = []; for (const l of rows) { const x = l.map(r => r.x[nyckel]), y = l.map(r => r[utfall]); if (new Set(x).size < 2 || x.some(v => !Number.isFinite(v))) continue; rs.push(spearman(x, y)) } return rs.length ? { r: rs.reduce((s, v) => s + v, 0) / rs.length, k: rs.length } : { r: NaN, k: 0 } }
  const rows = Object.values(perKonto), obs = stat(rows)
  if (!perm || !Number.isFinite(obs.r)) return obs
  let ext = 0; for (let t = 0; t < perm; t++) { const p = rows.map(l => { const ys = bl(l.map(r => r[utfall])); return l.map((r, i) => ({ ...r, [utfall]: ys[i] })) }); if (stat(p).r >= obs.r) ext++ }
  return { ...obs, p: (ext + 1) / (perm + 1) }
}
console.log(`${urval.length} kort från ${konton.length} konton (${path.basename(KD)})`)
const f = v => Number.isFinite(v) ? (v >= 0 ? '+' : '') + v.toFixed(3) : '–'
const H = { HE6a: ['grund', 'rv'], HE6b: ['grund', 'rl'], HE6c: ['medstroms (kontots vanligaste strategi)', 'rv'], HE6d: ['grundvarde.hojer_taket', 'rv'], HE6e: ['sprak.klippberoende', 'rv'] }
const ut = { hypoteser: {}, karta: {} }
for (const [h, [n, u]] of Object.entries(H)) { const r = inom(n, u, 3000); ut.hypoteser[h] = r; console.log(`${h} ${n} → ${u}: ${f(r.r)} (${r.k} konton), p ${r.p?.toFixed(4)}`) }
console.log('\nutforskande karta (medel av rho inom konto)\nlager'.padEnd(46), 'visningar', 'gillanden')
for (const n of Object.keys(Object.values(perKonto)[0][0].x)) { const a = inom(n, 'rv'), b = inom(n, 'rl'); ut.karta[n] = { rv: a, rl: b }; console.log(n.padEnd(45), f(a.r).padStart(9), f(b.r).padStart(9), `(${a.k})`) }
fs.writeFileSync(path.join(E, `analys-${path.basename(KD)}.json`), JSON.stringify(ut, null, 1))
