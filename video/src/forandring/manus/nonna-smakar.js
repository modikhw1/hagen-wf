// Originalet, rekonstruerat ur det riktiga klippet. I biblioteket görs detta automatiskt
// (scendelning, GVHMR för rörelser och kamerabana, CameraBench-ord för kameran).
// Här är det handskrivet. Det är ground truth: verkligheterna 1–10 skrivs om utifrån det här.

export const ORIGINAL = {
  id: 'nonna-smakar/original',
  klipp: 'nonna-smakar',
  namn: 'Nonna smakar',
  kund: 'Fratelli',
  verklighet: null,
  instruktion: null,
  lokal: 'fratelli',
  roller: { marco: 'marco', nonna: 'nonna' },
  scener: [
    {
      id: 's1',
      text: 'Marco knådar degen',
      tid: 2.4,
      handling: [
        { roll: 'marco', rorelse: 'knada', start: 0, plats: [0.85, -2.02], riktning: 0 },
      ],
      kamera: { utsnitt: 'halvtotal', mal: { roll: 'marco', led: 'spine3' }, vinkel: 15, hojd: 18, skak: 0.25, ops: [{ op: 'dolly', mangd: 0.35 }] },
    },
    {
      id: 's2',
      text: 'Nonna kommer in',
      tid: 2.6,
      in: { typ: 'klipp' },
      handling: [
        { roll: 'nonna', rorelse: 'ga', start: 0, slut: 1.7, vag: [[-1.6, -2.25], [-0.2, -1.3]] },
        { roll: 'nonna', rorelse: 'armar_i_kors', start: 1.7, plats: [-0.2, -1.3], riktning: 125, blick: 'marco' },
        { roll: 'marco', rorelse: 'sta', start: 0, plats: [0.6, -2.02], riktning: -40, blick: 'nonna' },
      ],
      kamera: { utsnitt: 'halvtotal', mal: { roll: 'nonna', led: 'spine2' }, vinkel: 30, hojd: 4, skak: 0.15, ops: [{ op: 'tracking', mangd: 0.8 }, { op: 'pan', mangd: 6 }] },
    },
    {
      id: 's3',
      text: 'Marco räcker fram en bit',
      tid: 2.1,
      in: { typ: 'klipp' },
      handling: [
        { roll: 'marco', rorelse: 'racka_fram', start: 0, plats: [0.5, -1.98], riktning: -50, blick: 'nonna', har: 'pizzabit' },
        { roll: 'nonna', rorelse: 'armar_i_kors', start: -5, plats: [-0.15, -1.32], riktning: 128, blick: 'marco' },
      ],
      kamera: { utsnitt: 'halvtotal', mal: { punkt: [0.15, 1.3, -1.65] }, vinkel: -10, hojd: 2, skak: 0.45, ops: [{ op: 'truck', mangd: 0.12 }] },
    },
    {
      id: 's4',
      text: 'Nonna smakar',
      tid: 2.4,
      in: { typ: 'mjuk', tid: 0.25 },
      handling: [
        { roll: 'nonna', rorelse: 'smaka', start: 0, plats: [-0.15, -1.32], riktning: 120, blick: 'marco', har: 'pizzabit' },
        { roll: 'marco', rorelse: 'sta', start: 1, plats: [0.5, -1.98], riktning: -50, blick: 'nonna' },
      ],
      kamera: { utsnitt: 'nara', mal: { roll: 'nonna', led: 'head' }, vinkel: 95, hojd: 2, skak: 0.2, ops: [{ op: 'zoom', mangd: 0.15 }] },
    },
    {
      id: 's5',
      text: 'Tummen upp',
      tid: 2.2,
      in: { typ: 'whip', tid: 0.3 },
      handling: [
        { roll: 'nonna', rorelse: 'tummen_upp', start: 0, plats: [-0.15, -1.25], riktning: 25 },
        { roll: 'marco', rorelse: 'jubla', start: 0.3, plats: [0.55, -2.0], riktning: -15 },
      ],
      kamera: { utsnitt: 'halvtotal', mal: { punkt: [0.2, 1.25, -1.62] }, vinkel: -25, hojd: -5, ops: [{ op: 'arc', mangd: 24 }] },
    },
  ],
}
