// Serieprofil ur bankens sållning (Lite-typ per klipp) och kontots lista: hela historiken i block om 10,
// nyast först. Inga modellanrop. Används för att se om den billiga sållningen bär ägarens läsning av en serie
// (faser, repertoar, hur ofta en typ återkommer).
//   node format/serieprofil.mjs konto1,konto2 [--block 10]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const arg = n => { const i = process.argv.indexOf(n); return i > 0 ? process.argv[i + 1] : null }
const B = +(arg('--block') ?? 10)
const KORT = { matporr_och_process: 'M', direkt_tilltal: 'T', relaterbar_sketch: 'S', vardens_provsmakning: 'G', annat: '.' }
// --familj: ägarens formatfamiljer (Flash där de finns, annars den lokala klassaren)
const FAM = process.argv.includes('--familj') ? Object.fromEntries(Object.entries(las(path.join(DATA, 'format', 'familjer', 'familjer-lokal.json'))).map(([k, v]) => [k, v.familj])) : null
const FKORT = { dialogsketch: 'D', ordvits: 'O', absurd_improvisation: 'A', gatuinslag: 'G', tilltal_med_mat: 'T', text_utan_tal: 'X', trend: 'R', stamningsmontage: 'M', kampanj: 'K', annat: '.' }
export function historik(k) {
  const L = las(path.join(DATA, 'bank', k, 'lista.json')).klipp
  return L.map(x => { const f = path.join(DATA, 'bank', 'sallning', `${k}-${x.id}.json`); return fs.existsSync(f) ? { ...x, s: las(f) } : null })
    .filter(Boolean).sort((a, b) => (b.datum || '').localeCompare(a.datum || ''))
}
if (path.resolve(process.argv[1] ?? '') === path.resolve(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'))) {
  for (const k of (process.argv[2] || '').split(',').filter(Boolean)) {
    const L = historik(k)
    console.log(`\n## ${k}: ${L.length} klipp ${FAM ? '(D dialogsketch, O ordvits, A absurd, G gata, T tilltal med mat, X text utan tal, R trend, M stämning/mat, K kampanj)' : '(M mat, T tilltal, S sketch, G gata/provsmakning, . annat)'}. Nyast först.`)
    for (let i = 0; i < L.length; i += B) {
      const b = L.slice(i, i + B), seq = b.map(x => FAM ? (FKORT[FAM[x.s.id]] ?? '?') : (KORT[x.s.typ] ?? '?')).join('')
      const pers = b.reduce((s, x) => s + (x.s.andel_med_person ?? 0), 0) / b.length
      const v = b.map(x => x.visningar).sort((a, c) => a - c)[Math.floor(b.length / 2)]
      console.log(`${String(i + 1).padStart(4)}–${String(i + b.length).padEnd(4)} ${b.at(-1).datum}..${b[0].datum}  ${seq.padEnd(B)}  person ${pers.toFixed(2)}  median visn ${v}`)
    }
  }
}
