// Osållat stickprov: slumpvisa klipp per konto oavsett utfall, så att normen inte byggs på
// klipp som valdes för att de gick bra (se karta/videoforandring/residual.md).
//
//   node profil/stickprov.mjs [--per-konto 10] [--hamta]
//
// Urvalet är reproducerbart (fröet är kontots namn). Klipp som redan är nedladdade räknas in
// utan ny hämtning. --hamta laddar ner resten och registrerar dem i kallor.json, så att
// bank/sallning.mjs tar dem i nästa körning.
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { hamtaValda } from '../bank/forurval.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PER = Number(varde('--per-konto', 10))
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))

export function fro(text) {
  let h = 2166136261
  for (const c of text) h = Math.imul(h ^ c.charCodeAt(0), 16777619)
  return h >>> 0
}

export function slump(seed) {
  let a = seed
  return () => {
    a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// Behörigt: med i residualen (minst 14 dagar, visningar finns), 5–90 s, högst 900 dagar gammalt.
export function valjStickprov(rader, konto, n) {
  const behoriga = rader.filter(r => r.konto === konto && r.langd >= 5 && r.langd <= 90 && r.alder <= 900)
  const s = slump(fro(konto))
  const blandade = behoriga.map(r => [s(), r]).sort((a, b) => a[0] - b[0]).map(x => x[1])
  return blandade.slice(0, n)
}

if (import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const bas = las(path.join(DATA, 'profil', 'baslinje.json'))
  const sallade = new Set(fs.readdirSync(path.join(DATA, 'bank', 'sallning')).map(f => f.replace(/\.json$/, '')))
  // Samma konton som det sållade urvalet, så att jämförelsen gäller samma konton.
  const konton = [...new Set([...sallade].map(id => bas.rader.find(r => `${r.konto}-${r.id}` === id)?.konto).filter(Boolean))].sort()
  const klipp = []
  for (const konto of konton) {
    for (const r of valjStickprov(bas.rader, konto, PER)) {
      klipp.push({ handtag: konto, id: r.id, url: `https://www.tiktok.com/@${konto}/video/${r.id}`, rv: r.rv, valt: true, sallat: sallade.has(`${konto}-${r.id}`) })
    }
  }
  fs.writeFileSync(path.join(DATA, 'profil', 'stickprov.json'), JSON.stringify({ skapad: new Date().toISOString(), perKonto: PER, konton: konton.length, klipp }, null, 1) + '\n')
  const median = v => { const s = [...v].sort((a, b) => a - b); return s[s.length >> 1] }
  console.log(`${klipp.length} klipp från ${konton.length} konton, ${klipp.filter(k => k.sallat).length} redan sållade; median rv ${median(klipp.map(k => k.rv)).toFixed(2)}`)
  if (args.includes('--hamta')) {
    // yt-dlp hittar inte systemets ffmpeg (tom ACL), så bild och ljud slogs inte ihop. Peka på ffmpeg-static.
    const { createRequire } = await import('node:module')
    const ffmpeg = createRequire(import.meta.url)('ffmpeg-static')
    const { ytdlpMedPaus } = await import('../bank/profiler.mjs')
    await hamtaValda(klipp.filter(k => !k.sallat), { anropa: (a, o) => ytdlpMedPaus(['--ffmpeg-location', ffmpeg, ...a], o) })
  }
}
