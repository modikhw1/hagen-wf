import { ORDBOK } from '../motor/ordbok'

// Galleriet: varje rörelse i ordboken två gånger, rakt framifrån och från sidan (figurens vänster),
// samma lokal. Ett verktyg för att kalibrera rörelserna, byggt på samma motor och samma manusformat.

const VEM = { smaka: 'nonna', armar_i_kors: 'nonna', tummen_upp: 'nonna', ga: 'nonna' }
const HAR = { smaka: 'pizzabit', racka_fram: 'pizzabit' }
const VINKLAR = [['fram', 0], ['sida', 90]]

export const GALLERI = {
  id: 'galleri',
  klipp: 'galleri',
  namn: 'Alla rörelser',
  kund: 'Ordboken',
  verklighet: null,
  lokal: 'fratelli',
  roller: { marco: 'marco', nonna: 'nonna' },
  scener: Object.values(ORDBOK).flatMap(c => VINKLAR.map(([namn, vinkel]) => {
    const roll = VEM[c.id] ?? 'marco'
    return {
      id: `${c.id}-${namn}`,
      text: `${c.id} · ${namn}`,
      tid: Math.max(1.4, c.langd),
      tumme: c.loop ? c.langd * 0.25 : c.langd * 0.6,
      handling: [{ roll, rorelse: c.id, start: 0, plats: [-1.2, 0.2], riktning: 0, har: HAR[c.id] }],
      kamera: { utsnitt: 'halvtotal', mal: { roll, led: 'spine2' }, vinkel, hojd: 4, ops: [] },
    }
  })),
}
