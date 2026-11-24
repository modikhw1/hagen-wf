// H22 (utforskande): finns strategityper på profilnivå? Kontots mix (medel per lager över E4-klippen)
// klustras med k-means (z-värden, 20 starter). Sedan visas var ägarens valda konton hamnar.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const E4 = path.join(DATA, 'format', 'e4'), dir = path.join(E4, 'lager-gemini-3.1-flash-lite')
const urval = new Map(JSON.parse(fs.readFileSync(path.join(E4, 'urval.json'), 'utf8')).map(k => [k.id, k]))
const tal = v => typeof v === 'boolean' ? (v ? 1 : 0) : v
const godk = new Set(fs.readFileSync(path.join(DATA, 'profil', 'godkanda.txt'), 'utf8').split(/\r?\n/).filter(Boolean))
const fore = new Set((fs.readFileSync(path.join(DATA, 'profil', 'forebilder.txt'), 'utf8').match(/@[a-z0-9._]+/g) ?? []).map(h => h.slice(1)))
const L = ['tilltal', 'roll', 'humor', 'dialog', 'sjalvironi', 'andel_person', 'mat_andel', 'montage', 'trendljud', 'uppmaning', 'erbjudande', 'tavling', 'skarmtext', 'utomhus']
const per = new Map()
for (const f of fs.readdirSync(dir)) { const x = { ...JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')) }; const l = per.get(x.konto) ?? []; l.push(x); per.set(x.konto, l) }
const konton = [...per.entries()].filter(([, l]) => l.length >= 8).map(([k, l]) => ({ k, g: godk.has(k) ? 'ja' : fore.has(k) ? 'forebild' : 'bank', typ: [...new Set(l.map(r => r.kontotyp))].sort((a, b) => l.filter(r => r.kontotyp === b).length - l.filter(r => r.kontotyp === a).length)[0], v: L.map(n => l.reduce((s, r) => s + tal(r[n]), 0) / l.length) }))
const mu = L.map((_, j) => konton.reduce((s, k) => s + k.v[j], 0) / konton.length), sd = L.map((_, j) => Math.sqrt(konton.reduce((s, k) => s + (k.v[j] - mu[j]) ** 2, 0) / konton.length) || 1)
for (const k of konton) k.z = k.v.map((x, j) => (x - mu[j]) / sd[j])
let fro = 5; const sl = () => { fro = (fro * 16807) % 2147483647; return fro / 2147483647 }
const d2 = (a, b) => a.reduce((s, x, i) => s + (x - b[i]) ** 2, 0)
function kmeans(K) {
  let bast = null
  for (let start = 0; start < 20; start++) {
    let c = Array.from({ length: K }, () => konton[Math.floor(sl() * konton.length)].z.slice()), tilldelning = []
    for (let it = 0; it < 50; it++) {
      tilldelning = konton.map(k => c.map(ci => d2(k.z, ci)).reduce((b, x, i, a) => x < a[b] ? i : b, 0))
      c = c.map((ci, i) => { const m = konton.filter((_, j) => tilldelning[j] === i); return m.length ? L.map((_, j) => m.reduce((s, k) => s + k.z[j], 0) / m.length) : ci })
    }
    const sse = konton.reduce((s, k, j) => s + d2(k.z, c[tilldelning[j]]), 0)
    if (!bast || sse < bast.sse) bast = { sse, c, tilldelning }
  }
  return bast
}
for (const K of [3, 4, 5]) console.log(`K=${K}: kvarvarande varians ${(kmeans(K).sse / (konton.length * L.length)).toFixed(2)}`)
const K = 4, r = kmeans(K)
console.log(`\n${konton.length} konton, K = ${K}. Kluster: kännetecken (z > 0,6 eller < −0,6), ägarens valda (ja/förebild) och exempel`)
for (let i = 0; i < K; i++) {
  const m = konton.filter((_, j) => r.tilldelning[j] === i)
  const drag = L.map((n, j) => [n, r.c[i][j]]).filter(([, z]) => Math.abs(z) > 0.6).sort((a, b) => b[1] - a[1]).map(([n, z]) => `${n} ${z > 0 ? '+' : ''}${z.toFixed(1)}`).join(', ')
  const valda = m.filter(k => k.g !== 'bank')
  console.log(`\nkluster ${i + 1} (${m.length} konton, ${valda.length} valda = ${Math.round(100 * valda.length / m.length)} %): ${drag}`)
  console.log('  valda:', valda.map(k => k.k).join(', ') || '-')
  console.log('  bank: ', m.filter(k => k.g === 'bank').slice(0, 10).map(k => k.k).join(', '))
}
fs.writeFileSync(path.join(E4, 'typer.json'), JSON.stringify({ lager: L, kluster: Array.from({ length: K }, (_, i) => ({ centrum: Object.fromEntries(L.map((n, j) => [n, +r.c[i][j].toFixed(2)])), konton: konton.filter((_, j) => r.tilldelning[j] === i).map(k => ({ konto: k.k, grupp: k.g })) })) }, null, 1))
