// Platshållardata. Ett klipp = scener med längd (det en ffmpeg-klippning ger), plus metadata.
// touched: CM har gjort klippet till kundens (tanke, ändrade scener). Annars ser det ut som originalet.
let n = 0
export const newId = () => 'c' + ++n

const s = (dur, lock = false) => ({ dur, lock })

const clip = (title, picto, format, scenes, extra = {}) => ({
  id: newId(), title, picto, format, scenes,
  status: 'ready', alts: null, chosen: null, mark: null, note: '', series: null, views: null, fresh: false,
  touched: false, cmNote: '', changed: [], handle: null,
  ...extra,
})
// Ett klipp CM har gjort till kundens.
const mine = (cmNote, changed) => ({ touched: true, cmNote, changed })

export function makeCustomers() {
  const nonna3 = clip('Nonnas regler #3', 'nonna', 'Serie', [s(1, true), s(2), s(2)], { series: 'Nonnas regler', ...mine('ketchup = förbjudet', [1, 2]) })
  const ananas = clip('Kunden som vill ha ananas', 'pizza', 'POV', [s(1.5, true), s(2), s(2.5), s(2, true)], mine('Nonna slänger ananasen', [2]))
  const gissa = clip('Gissa priset', 'plate', 'Gissa', [s(1.5), s(3), s(2)], {
    ...mine('stamgästerna gissar', [1]),
    alts: {
      1: clip('Veckans pizza på 15 sek', 'pizza', 'Före/efter', [s(1), s(2)], mine('tryffeln i närbild', [1])),
      3: clip('Marco dansar med degen', 'person', 'POV', [s(1.5), s(3)], { handle: '@dancingchef' }),
    },
  })
  const tusen = clip('1000 pizzor på 60 sek', 'clock', 'Timelapse', [s(1), s(4), s(1.5)], mine('Marco somnar i slutet', [2]))
  const n4 = clip('Nonnas regler #4', 'nonna', 'Serie', [s(1, true), s(2), s(2)], {
    series: 'Nonnas regler', ...mine('ingen gaffel', [1, 2]),
    alts: { 1: clip('Nonnas regler: bonus', 'nonna', 'Serie', [s(1), s(2)], { series: 'Nonnas regler', ...mine('ingen ost på fisk', [1]) }), 3: null },
  })
  const n5 = clip('Nonnas regler #5', 'nonna', 'Serie', [s(1, true), s(2.5), s(1.5)], { series: 'Nonnas regler', ...mine('aldrig kall pizza', [1, 2]) })
  const fratelli = {
    id: 'fratelli', name: 'Fratelli', initial: 'F',
    before: {
      history: [
        clip('Degen som inte ville', 'pizza', 'POV', [s(1), s(2), s(2)], { views: 0.55 }),
        clip('Nonnas regler #1', 'nonna', 'Serie', [s(1), s(2), s(2)], { views: 0.9, series: 'Nonnas regler' }),
        clip('Marco sjunger beställningen', 'person', 'POV', [s(2), s(3)], { views: 0.3 }),
        clip('Nonnas regler #2', 'nonna', 'Serie', [s(1), s(2), s(2)], { views: 0.75, series: 'Nonnas regler' }),
        clip('Kartongen som inte räckte', 'box', 'Fail', [s(1.5), s(2.5)], { views: 0.2, kind: 'mkt' }),
      ],
      plan: [nonna3, ananas, gissa, tusen, n4, n5],
      bench: [
        clip('Chefen testar nyanställd', 'duo', 'Test', [s(1.5, true), s(2), s(2), s(1.5)], mine('Marco testar Sami', [1, 2])),
        clip('Telefonen under rusningen', 'phone', 'POV', [s(1, true), s(2), s(2), s(1.5)], { handle: '@nonnaenergy' }),
        clip('Degkast i slowmo', 'pizza', 'ASMR', [s(2), s(3)], { handle: '@pizzaschool', mark: 'no' }),
      ],
    },
    events: [
      { type: 'published', id: nonna3.id },
      { type: 'back', id: ananas.id },
      { type: 'chose', id: gissa.id, n: 3 },
    ],
  }

  const fe1 = clip('Före och efter: lockarna', 'mirror', 'Före/efter', [s(1, true), s(3), s(1, true)], mine('Vera berättar inget, bara visar', [1]))
  const min = clip('Kundens min i spegeln', 'mirror', 'Reaktion', [s(1.5), s(2.5)], {
    ...mine('stamkunden Gun', [0]),
    alts: { 1: clip('Kunden som inte vågar titta', 'mirror', 'Reaktion', [s(2), s(2)], mine('ögonen stängda till sista sek', [0])), 3: clip('Veras tips: lockar i regn', 'scissors', 'Info', [s(2), s(3)], { kind: 'info', handle: '@hairbyjo' }) },
  })
  const vera = {
    id: 'vera', name: 'Salong Vera', initial: 'V',
    before: {
      history: [
        clip('Saxen som försvann', 'scissors', 'POV', [s(1), s(3)], { views: 0.4 }),
        clip('Vera gissar ditt jobb', 'person', 'Gissa', [s(2), s(2), s(1)], { views: 0.65 }),
        clip('Lugnet innan stängning', 'cup', 'Stämning', [s(4)], { views: 0.25 }),
      ],
      plan: [
        fe1, min,
        clip('Stylistens fel som blev rätt', 'scissors', 'Fail', [s(1), s(2), s(2)], mine('lärlingen Ida', [1, 2])),
        clip('Före och efter: färgen', 'mirror', 'Före/efter', [s(1, true), s(3), s(1, true)], mine('kopparrött', [1])),
      ],
      bench: [
        clip('Frisören som läser tankar', 'person', 'POV', [s(1, true), s(2), s(2)], { handle: '@saxochkam' }),
      ],
    },
    events: [
      { type: 'published', id: fe1.id },
      { type: 'chose', id: min.id, n: 1 },
    ],
  }

  const morgon = clip('Morgonbaket kl 04', 'bread', 'Timelapse', [s(1), s(4)], mine('mörkret utanför', [0]))
  const gosta = clip('Surdegen Gösta fyller år', 'bread', 'Karaktär', [s(1.5), s(2), s(2)], mine('tårta åt degen', [1, 2]))
  const bulle = clip('Kanelbullen som flög', 'bread', 'Fail', [s(1), s(2)], mine('Eva kastar', [1]))
  const ljung = {
    id: 'ljung', name: 'Bageri Ljung', initial: 'L',
    before: {
      history: [
        clip('Ugnen öppnas', 'bread', 'ASMR', [s(3)], { views: 0.5 }),
        clip('Gösta presenteras', 'bread', 'Karaktär', [s(2), s(2)], { views: 0.8 }),
      ],
      plan: [morgon, gosta, bulle],
      bench: [
        clip('Kökets ASMR', 'knife', 'ASMR', [s(1.5, true), s(2), s(2)], { handle: '@cheflove' }),
        clip('Gissa vikten på degen', 'plate', 'Gissa', [s(1.5, true), s(2.5), s(2)], { handle: '@foodbyamir' }),
      ],
    },
    events: [
      { type: 'published', id: morgon.id },
      { type: 'published', id: gosta.id },
      { type: 'no', id: bulle.id },
    ],
  }

  return [fratelli, vera, ljung]
}

// Det inklistrade klippet "blir" ett av dessa när analysen är klar.
export const POOL = [
  { title: 'Gissa vikten på degen', picto: 'plate', format: 'Gissa', scenes: [s(1.5, true), s(2.5), s(2)] },
  { title: 'Kockens ASMR', picto: 'knife', format: 'ASMR', scenes: [s(1.5, true), s(2), s(2)] },
  { title: 'Telefonen under rusningen', picto: 'phone', format: 'POV', scenes: [s(1, true), s(2), s(2), s(1.5)] },
  { title: 'Chefen testar nyanställd', picto: 'duo', format: 'Test', scenes: [s(1.5, true), s(2), s(2), s(1.5)] },
]
