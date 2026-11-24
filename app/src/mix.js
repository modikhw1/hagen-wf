// Mixen: vilken sorts innehåll klippet är, och hur blandningen ser ut över planen.
// kind härleds ur formatet; ett klipp kan ha egen kind. I riktiga appen härleds det av motorn och CM kan rätta.
export const KINDS = [
  ['ent', 'Underhållning'],
  ['info', 'Info'],
  ['mkt', 'Marknadsföring'],
]
const KIND = {
  POV: 'ent', Fail: 'ent', Test: 'ent', Reaktion: 'ent', Serie: 'ent', Karaktär: 'ent',
  Timelapse: 'info', ASMR: 'info', Stämning: 'info',
  'Före/efter': 'mkt', Gissa: 'mkt',
}
const CAST = { duo: 2, plate: 3, clock: 3, pizza: 2 }

// LeTrends baslinje. Kan i framtiden vara 1–3 baslinjer, eller härledas ur kundens publicerade klipp.
export const BASE = { ent: 0.6, info: 0.2, mkt: 0.2 }

export const kindOf = c => c.kind || KIND[c.format] || 'ent'
export const fp = c => ({ kind: kindOf(c), cast: CAST[c.picto] || 1 })

export function balance(list) {
  const r = { ent: 0, info: 0, mkt: 0 }
  list.forEach(c => { r[kindOf(c)]++ })
  const n = list.length || 1
  return { ent: r.ent / n, info: r.info / n, mkt: r.mkt / n, n: list.length }
}
