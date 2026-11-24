// H17 (utforskande): är ägarens "balans" en blandning inom kontot snarare än ett medel?
// Varje E4-klipp får en grov roll ur stabila lager:
//   kott   = spelad situation eller humor ≥ 1, med person i bild minst halva tiden
//   fraga  = tävling, uppmaning eller erbjudande (och inte kött)
//   visning = matandel ≥ 3 eller montage (och inte kött eller fråga)
//   annat  = resten
// Per konto: andelar, blandningsentropi (bitar), och hur många av de tre huvudrollerna som finns med
// minst 15 %.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const E4 = path.join(DATA, 'format', 'e4'), dir = path.join(E4, 'lager-gemini-3.1-flash-lite')
const godk = new Set(fs.readFileSync(path.join(DATA, 'profil', 'godkanda.txt'), 'utf8').split(/\r?\n/).filter(Boolean))
const fore = new Set((fs.readFileSync(path.join(DATA, 'profil', 'forebilder.txt'), 'utf8').match(/@[a-z0-9._]+/g) ?? []).map(h => h.slice(1)))
const BALANS = new Set(['mondocoatbridge', 'babulsofficial'])
const roll = x => (x.roll || x.humor >= 1) && x.andel_person >= 2 ? 'kott' : (x.tavling || x.uppmaning || x.erbjudande) ? 'fraga' : (x.mat_andel >= 3 || x.montage) ? 'visning' : 'annat'
const per = new Map()
for (const f of fs.readdirSync(dir)) { const x = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); const l = per.get(x.konto) ?? []; l.push(roll(x)); per.set(x.konto, l) }
const R = ['kott', 'fraga', 'visning', 'annat']
const konton = [...per.entries()].filter(([, l]) => l.length >= 8).map(([k, l]) => {
  const a = Object.fromEntries(R.map(r => [r, l.filter(x => x === r).length / l.length]))
  const H = -R.reduce((s, r) => s + (a[r] ? a[r] * Math.log2(a[r]) : 0), 0)
  const bredd = ['kott', 'fraga', 'visning'].filter(r => a[r] >= 0.15).length
  return { k, g: BALANS.has(k) ? 'balans' : godk.has(k) ? 'ja' : fore.has(k) ? 'forebild' : 'bank', n: l.length, ...a, H, bredd }
})
const medel = a => a.reduce((s, v) => s + v, 0) / a.length
const grupper = ['balans', 'ja', 'forebild', 'bank']
console.log('grupp     konton  kött  fråga  visning  annat  entropi  har ≥2 roller')
for (const g of grupper) { const m = konton.filter(k => k.g === g); if (!m.length) continue; console.log(`${g.padEnd(9)} ${String(m.length).padStart(4)}   ${['kott', 'fraga', 'visning', 'annat'].map(r => medel(m.map(k => k[r])).toFixed(2)).join('   ')}   ${medel(m.map(k => k.H)).toFixed(2)}     ${(m.filter(k => k.bredd >= 2).length / m.length * 100).toFixed(0)} %`) }
console.log('\nbalanskontona:'); for (const k of konton.filter(k => k.g === 'balans')) console.log(k.k, JSON.stringify(Object.fromEntries(R.map(r => [r, +k[r].toFixed(2)]))), 'H', k.H.toFixed(2))
// permutation: entropi valda (ja+förebild+balans) mot bank
const v = konton.filter(k => k.g !== 'bank').map(k => k.H), b = konton.filter(k => k.g === 'bank').map(k => k.H), d = medel(v) - medel(b), alla = [...v, ...b]
let fro = 9, ext = 0; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
for (let t = 0; t < 5000; t++) { const p = [...alla]; for (let i = p.length - 1; i > 0; i--) { const j = Math.floor(sl() * (i + 1)); [p[i], p[j]] = [p[j], p[i]] } if (Math.abs(medel(p.slice(0, v.length)) - medel(p.slice(v.length))) >= Math.abs(d)) ext++ }
console.log(`\nentropi valda ${medel(v).toFixed(2)} mot bank ${medel(b).toFixed(2)}, skillnad ${d.toFixed(2)}, p ${((ext + 1) / 5001).toFixed(3)}`)
// topp-entropi-konton
console.log('\nmest blandade konton:', konton.sort((a, b) => b.H - a.H).slice(0, 12).map(k => `${k.k}(${k.g[0]}) ${k.H.toFixed(2)}`).join(', '))
fs.writeFileSync(path.join(E4, 'mix.json'), JSON.stringify(konton, null, 1))
