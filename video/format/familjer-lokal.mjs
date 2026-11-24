// Lokal klassare för ägarens formatfamiljer (6 nov 2026, inga anrop). Tränas på Flash-etiketterna i
// data/format/familjer/familjer.json (klipp ur sållningen) och märker resten av banken.
// Multinomial naive Bayes på ord (innehåll + skäl), Lite-typ och flaggor. Korsvalideras med hela konton
// utanför träningen (5 vikningar), så att träffsäkerheten gäller nya konton.
//   node format/familjer-lokal.mjs
// Resultat: data/format/familjer/familjer-lokal.json  { id: { familj, kalla: 'flash' | 'lokal', p } }
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const F = path.join(DATA, 'format', 'familjer'), SAL = path.join(DATA, 'bank', 'sallning')
const ETIK = las(path.join(F, 'familjer.json')), FAM = Object.keys(las(path.join(F, 'forregistrering.json')).familjer)
const konto = id => id.replace(/-\d+$/, '')
const ord = t => (t || '').toLowerCase().replace(/[^a-zåäöéü0-9 ]/g, ' ').split(/\s+/).filter(w => w.length > 2)
const NYCKEL = [
  ['trend', /dansar|dansa|dans\b|läppsynk|mimar|playback|till musik|musiken|trendljud|trend/],
  ['text', /text på skärmen|med texten|texten |textöverlägg|skylt|budskap/],
  ['gata', /förbipasserande|slumpmässig|köpcentrum|galleri|intervjuar|reporter|på gatan|besökare|betygsätt|folk på/],
  ['kampanj', /erbjudande|presentkort|tävling|rabatt|kronor|\bkr\b|pund|boka|öppettider|inbjud|lansering|nyhet|event|öppnar/],
  ['ordvits', /ordvits|ordlek|missförst|dubbeltydig/],
  ['absurd', /absurd|surrealist|bisarr/],
]
function drag(s) {
  const w = [...ord(s.innehall), ...ord(s.skal).map(x => 's:' + x)]
  const bi = ord(s.innehall); for (let i = 0; i + 1 < bi.length; i++) w.push(bi[i] + '_' + bi[i + 1])
  w.push('typ:' + s.typ, 'pers:' + Math.min(s.personer_max ?? 0, 3), 'andel:' + Math.round((s.andel_med_person ?? 0) * 2), 'text:' + s.text_tung, 'montage:' + s.montage, 'bildspel:' + s.bildspel, 'inne:' + s.inne_i_verksamheten)
  // nyckelord för de fina familjerna (sållningens mening bär dem bara via enstaka ord), väger som fyra ord
  const t = ((s.innehall || '') + ' ' + (s.skal || '')).toLowerCase()
  for (const [namn, re] of NYCKEL) if (re.test(t)) for (let i = 0; i < 4; i++) w.push('kw:' + namn)
  // typ och flaggor väger som flera ord
  for (let i = 0; i < 2; i++) w.push('typ:' + s.typ, 'text:' + s.text_tung, 'montage:' + s.montage, 'pers:' + Math.min(s.personer_max ?? 0, 3))
  // TikToks metadata (Downloads/letrend-bank/<konto>/<id>.info.json): ljudspår och bildtext
  if (process.env.UTAN_INFO) return w
  const info = INFO(s.id)
  if (info) {
    const lj = ljud(info); for (let i = 0; i < 4; i++) w.push('ljud:' + lj)
    w.push('langd:' + (info.duration < 10 ? 'kort' : info.duration < 30 ? 'mellan' : 'lang'))
    for (const x of ord(info.description || info.title).slice(0, 30)) w.push('c:' + x)
  }
  return w
}
const BANKDL = path.join(process.env.USERPROFILE || process.env.HOME, 'Downloads', 'letrend-bank')
const INFO = id => { const m = id.match(/^(.*)-(\d+)$/); const f = m && path.join(BANKDL, m[1], `${m[2]}.info.json`); try { return f && fs.existsSync(f) ? las(f) : null } catch { return null } }
// eget = kontots eget ljud, lanat = någon annans originalljud (meme- och trendljud), lat = namngiven låt
function ljud(j) {
  const t = (j.track || '').toLowerCase(), a = (j.artist || (j.artists || [])[0] || '').toLowerCase(), u = (j.uploader || '').toLowerCase(), ch = (j.channel || '').toLowerCase()
  if (!t) return 'okant'
  if (/original|orijinal|originalljud|originalton|suono|son original|sonido/.test(t)) return !a || a === u || a === ch || u.includes(a) || a.includes(u) ? 'eget' : 'lanat'
  return 'lat'
}
const alla = fs.readdirSync(SAL).map(f => f.replace(/\.json$/, ''))
const S = new Map(alla.map(id => [id, las(path.join(SAL, id + '.json'))]))
const D = new Map(alla.map(id => [id, drag(S.get(id))]))

function trana(ids) {
  const n = {}, ordn = {}, tot = {}, vocab = new Set()
  for (const id of ids) { const y = ETIK[id]; n[y] = (n[y] || 0) + 1; ordn[y] ??= {}; for (const w of D.get(id)) { ordn[y][w] = (ordn[y][w] || 0) + 1; tot[y] = (tot[y] || 0) + 1; vocab.add(w) } }
  const V = vocab.size, N = ids.length
  return id => {
    const lp = FAM.map(y => { if (!n[y]) return -Infinity; let s = Math.log(n[y] / N); for (const w of D.get(id)) if (vocab.has(w)) s += Math.log(((ordn[y][w] || 0) + 0.5) / (tot[y] + 0.5 * V)); return s })
    const m = Math.max(...lp), e = lp.map(x => Math.exp(x - m)), z = e.reduce((a, b) => a + b, 0)
    const i = lp.indexOf(m); return { familj: FAM[i], p: e[i] / z }
  }
}

// Korsvalidering med konton utanför
const markt = Object.keys(ETIK).filter(id => D.has(id))
const kontonL = [...new Set(markt.map(konto))].sort()
const vik = k => kontonL.indexOf(k) % 5
let ratt = 0; const forv = {}, sakert = { r: 0, n: 0 }
for (let f = 0; f < 5; f++) {
  const tr = markt.filter(id => vik(konto(id)) !== f), te = markt.filter(id => vik(konto(id)) === f)
  const m = trana(tr)
  for (const id of te) { const p = m(id); if (p.familj === ETIK[id]) ratt++; (forv[ETIK[id]] ??= {})[p.familj] = (forv[ETIK[id]]?.[p.familj] || 0) + 1; if (p.p >= 0.8) { sakert.n++; if (p.familj === ETIK[id]) sakert.r++ } }
}
const bas = Math.max(...FAM.map(y => markt.filter(id => ETIK[id] === y).length)) / markt.length
console.log(`${markt.length} märkta klipp från ${kontonL.length} konton. Träffsäkerhet med nya konton: ${(100 * ratt / markt.length).toFixed(1)} % (största klassen ${(100 * bas).toFixed(1)} %). Med p ≥ 0,8: ${(100 * sakert.r / sakert.n).toFixed(1)} % på ${sakert.n} klipp.`)
for (const y of FAM) { const rad = forv[y] || {}, n = Object.values(rad).reduce((a, b) => a + b, 0); if (n) console.log(`  ${y.padEnd(22)} n ${String(n).padStart(4)}  rätt ${(100 * (rad[y] || 0) / n).toFixed(0).padStart(3)} %   oftast fel som ${Object.entries(rad).filter(([k]) => k !== y).sort((a, b) => b[1] - a[1]).slice(0, 2).map(([k, v]) => `${k} ${v}`).join(', ')}`) }

// Märk hela banken
const m = trana(markt), ut = {}
for (const id of alla) ut[id] = ETIK[id] ? { familj: ETIK[id], kalla: 'flash', p: 1 } : { ...m(id), kalla: 'lokal' }
fs.writeFileSync(path.join(F, 'familjer-lokal.json'), JSON.stringify(ut))
const c = {}; Object.values(ut).forEach(x => { c[x.familj] = (c[x.familj] || 0) + 1 }); console.log('hela banken:', c)
