// Iterationer. Öppna localhost:5180/#1, #2 … Varje steg lägger till en sak ovanpå förra.
export const STEPS = [
  'Kund och tidslinje',
  'Ankomst: sedan sist',
  'Mixen och dra',
  'Alternativ 1-2-3',
  'Klistra in ett klipp',
  'Harnessen svarar',
]
export const STEP = Math.max(1, Math.min(STEPS.length, parseInt(location.hash.slice(1)) || 1))
export const on = n => STEP >= n
