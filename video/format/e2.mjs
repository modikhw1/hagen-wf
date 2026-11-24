// E2 (3 nov 2026): ingen är facit. Dawid–Skene (1979) skattar ett latent "sant" omdöme per klipp och
// en felmatris per bedömare, ur ägaren och modellvarianterna som oberoende bedömare. Görs för
// funktion (kött/stöd/utanför) och för om personalen klarar klippet (ja/delvis/nej) på klipp 1–27.
//
// v3 med exempel räknas inte, eftersom den har sett ägarens omdömen om klipp 1–20.
// Modellvarianterna är inte oberoende: de är samma modell med olika prompter. Därför körs analysen
// två gånger, med alla varianter och med en variant per familj. Skillnaden visar hur mycket
// modellkonsensus drar.
//
//   node format/e2.mjs
// Resultat: data/format/kalib/e2.json och en rapport i terminalen.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const F = path.join(DATA, 'format')
const urval = JSON.parse(fs.readFileSync(path.join(F, 'kalib', 'urval.json'), 'utf8'))
const agare = JSON.parse(fs.readFileSync(path.join(F, 'kalib', 'agare.json'), 'utf8')).klipp
const NR = Object.keys(agare).map(Number).sort((a, b) => a - b)
const las = (dir, nr) => { const f = path.join(F, dir, `${urval[nr - 1].id}.json`); return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null }

const v1f = { karna: 'kott', inslag: 'stod', utanfor: 'utanfor' }
const v2f = { huvudnummer: 'kott', stomme: 'kott', glitter: 'stod', utfyllnad: 'stod', aterkommande_inslag: 'stod', engangsbit: 'utanfor', annan_kanal: 'utanfor' }
const v1b = x => x.bartest.betyg >= 4 ? 'ja' : x.bartest.betyg === 3 ? 'delvis' : 'nej'
const BEDOMARE = {
  'v1 Pro princip': { dir: 'v1-konst-gemini-3.1-pro-preview', fam: 'v1', fn: x => v1f[x.roll], bar: v1b },
  'v1 Pro omtest': { dir: 'v1-konst-gemini-3.1-pro-preview-b', fam: 'v1', fn: x => v1f[x.roll], bar: v1b },
  'v1 Pro neutral': { dir: 'v1-neutral-gemini-3.1-pro-preview', fam: 'v1n', fn: x => v1f[x.roll], bar: v1b },
  'v1 Lite': { dir: 'v1-konst-gemini-3.1-flash-lite', fam: 'lite', fn: x => v1f[x.roll], bar: v1b },
  'v1 text(Lite)': { dir: 'text-konst-gemini-3.1-pro-preview-fran-gemini-3.1-flash-lite', fam: 'text', fn: x => v1f[x.roll], bar: v1b },
  'v1 text(Pro)': { dir: 'text-konst-gemini-3.1-pro-preview-fran-gemini-3.1-pro-preview', fam: 'text', fn: x => v1f[x.roll], bar: v1b },
  'v2 Pro': { dir: 'v2-gemini-3.1-pro-preview', fam: 'v2', fn: x => v2f[x.roll], bar: x => x.premiss.bar },
  'v2 Pro omtest': { dir: 'v2-gemini-3.1-pro-preview-b', fam: 'v2', fn: x => v2f[x.roll], bar: x => x.premiss.bar },
  'v2 Pro kontext': { dir: 'v2-kontext-gemini-3.1-pro-preview', fam: 'v2k', fn: x => v2f[x.roll], bar: x => x.premiss.bar },
  'v3 Pro princip': { dir: 'v3-gemini-3.1-pro-preview', fam: 'v3', fn: x => x.funktion, bar: x => x.personal.bar },
}

function dawidSkene(klasser, etiketter, { varv = 200, alfa = 0.5 } = {}) {
  // etiketter: { bedömare: { nr: klass } }
  const J = Object.keys(etiketter), K = klasser.length, idx = Object.fromEntries(klasser.map((k, i) => [k, i]))
  const items = [...new Set(J.flatMap(j => Object.keys(etiketter[j])))]
  // Start: majoritetsröst.
  let T = Object.fromEntries(items.map(i => { const v = Array(K).fill(0.01); for (const j of J) { const l = etiketter[j][i]; if (l != null) v[idx[l]]++ } const s = v.reduce((a, b) => a + b); return [i, v.map(x => x / s)] }))
  let pi, theta
  for (let t = 0; t < varv; t++) {
    pi = Array(K).fill(0); for (const i of items) T[i].forEach((p, k) => { pi[k] += p / items.length })
    theta = Object.fromEntries(J.map(j => {
      const m = Array.from({ length: K }, () => Array(K).fill(alfa))
      for (const i of items) { const l = etiketter[j][i]; if (l == null) continue; T[i].forEach((p, k) => { m[k][idx[l]] += p }) }
      return [j, m.map(rad => { const s = rad.reduce((a, b) => a + b); return rad.map(x => x / s) })]
    }))
    T = Object.fromEntries(items.map(i => {
      const v = pi.map((p, k) => { let l = Math.log(p); for (const j of J) { const e = etiketter[j][i]; if (e != null) l += Math.log(theta[j][k][idx[e]]) } return l })
      const mx = Math.max(...v), ex = v.map(x => Math.exp(x - mx)), s = ex.reduce((a, b) => a + b)
      return [i, ex.map(x => x / s)]
    }))
  }
  const tra = Object.fromEntries(J.map(j => [j, pi.reduce((s, p, k) => s + p * theta[j][k][k], 0)]))
  return { pi, theta, T, traffsakerhet: tra }
}

const ut = {}
for (const [mal, klasser, agareFalt] of [['funktion', ['kott', 'stod', 'utanfor'], 'funktion'], ['personal', ['ja', 'delvis', 'nej'], 'bar']]) {
  const alla = { 'ägaren': Object.fromEntries(NR.map(nr => [nr, agare[nr][agareFalt]])) }
  for (const [namn, b] of Object.entries(BEDOMARE)) alla[namn] = Object.fromEntries(NR.map(nr => { const x = las(b.dir, nr); return [nr, x ? b[mal === 'funktion' ? 'fn' : 'bar'](x) : null] }).filter(([, v]) => v))
  const enPerFamilj = { 'ägaren': alla['ägaren'] }
  const sedda = new Set()
  for (const [namn, b] of Object.entries(BEDOMARE)) if (!sedda.has(b.fam)) { sedda.add(b.fam); enPerFamilj[namn] = alla[namn] }
  ut[mal] = {}
  for (const [variant, et] of [['alla', alla], ['en per familj', enPerFamilj]]) {
    const r = dawidSkene(klasser, et)
    const avvik = NR.filter(nr => { const p = r.T[nr]; const k = klasser[p.indexOf(Math.max(...p))]; return k !== agare[nr][agareFalt] })
      .map(nr => { const p = r.T[nr]; const k = klasser[p.indexOf(Math.max(...p))]; return { nr, agare: agare[nr][agareFalt], latent: k, sannolikhet: +Math.max(...p).toFixed(2) } })
    ut[mal][variant] = { bedomare: Object.keys(et).length, traffsakerhet: Object.fromEntries(Object.entries(r.traffsakerhet).map(([j, v]) => [j, +v.toFixed(2)])), agarensMatris: Object.fromEntries(klasser.map((k, ki) => [k, Object.fromEntries(klasser.map((l, li) => [l, +r.theta['ägaren'][ki][li].toFixed(2)]))])), priors: Object.fromEntries(klasser.map((k, i) => [k, +r.pi[i].toFixed(2)])), avvik }
  }
}

// Drift: ägarens fördelning per pass jämfört med v3 Pro (samma prompt för alla klipp).
const pass = { 'pass 1 (1–10)': [1, 10], 'pass 2 (11–20)': [11, 20], 'pass 3 (21–27)': [21, 27] }
ut.drift = Object.fromEntries(Object.entries(pass).map(([p, [lo, hi]]) => {
  const nr = NR.filter(n => n >= lo && n <= hi)
  const andel = (f, v) => +(nr.filter(f).length / nr.length).toFixed(2)
  const v3 = n => las('v3-gemini-3.1-pro-preview', n)
  return [p, {
    'ägaren bibliotek nej': andel(n => agare[n].bibliotek === 'nej'), 'v3 bibliotek nej': andel(n => v3(n).bibliotek.beslut === 'nej'),
    'ägaren utanför': andel(n => agare[n].funktion === 'utanfor'), 'v3 utanför': andel(n => v3(n).funktion === 'utanfor'),
  }]
}))

fs.writeFileSync(path.join(F, 'kalib', 'e2.json'), JSON.stringify(ut, null, 1))
for (const mal of ['funktion', 'personal']) for (const v of ['alla', 'en per familj']) {
  const r = ut[mal][v]
  console.log(`\n== ${mal}, ${v} (${r.bedomare} bedömare). Latent fördelning ${JSON.stringify(r.priors)}`)
  console.log('träffsäkerhet mot latent:', Object.entries(r.traffsakerhet).sort((a, b) => b[1] - a[1]).map(([j, x]) => `${j} ${x}`).join(' | '))
  console.log('ägarens felmatris (rad = latent, kolumn = ägarens svar):', JSON.stringify(r.agarensMatris))
  console.log('där ägaren avviker från latent:', r.avvik.map(a => `${a.nr}: ${a.agare}→${a.latent} (${a.sannolikhet})`).join(', '))
}
console.log('\n== drift per pass'); for (const [p, d] of Object.entries(ut.drift)) console.log(p, JSON.stringify(d))
