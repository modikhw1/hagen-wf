// Videoförändring, egna iterationer: localhost:5180/#v1, #v2 … Varje steg lägger till en sak.
export const VSTEPS = [
  'Klippet i originalets scenografi',
  'Reglaget',
  'Kurvan',
  'Spela upp',
]
export const isV = () => /^#v\d*$/.test(location.hash)
export const VSTEP = Math.max(1, Math.min(VSTEPS.length, parseInt(location.hash.slice(2)) || 1))
export const von = n => VSTEP >= n
