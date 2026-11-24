// Vertikalerna: dimensioner som ett klipp kan röra sig längs. Varje vertikal kalibreras för sig
// innan den får ingå i en kombinerad vertikal.
//
// - fraga:       vad människan svarar på i parvis bedömning (vilken av två har mer av X?)
// - kriterier:   nivåerna Jev får, från lägst till högst (TypeSafe score, 1–10 nivåer)
// - egenskaper:  vilka mätta egenskaper modellen får använda (tom = alla)
// - start:       en första vikt per egenskap, från hur vertikalen är definierad. Används innan det
//                finns bedömningar och som baslinje: tränad modell och Jev ska slå den.
// - grind:       när vertikalen räknas som kalibrerad
// - byggerPa:    för kombinerade vertikaler, vilka centrala som måste vara kalibrerade först

export const GRIND = { minBedomningar: 150, minOverens: 0.8, minKlipp: 20 }

export const VERTIKALER = [
  {
    // Scenografins rörlighet som helhet (användarens precisering 2026-10-31): hur aktiv, rörlig och
    // expansiv kontra subtil och lugn bilden är, sammansatt av alla delar: kamerans rörelse, hur
    // mycket bilden ändras, hur ryckigt, hur mycket som händer i bilden och hur ordnad den är.
    // Innehållet (vad personerna gör) räknas bara så som det syns i bild, inte som agerande.
    id: 'rorlighet',
    namn: 'Rörlighet',
    niva: 'central',
    enhet: 'scen',
    // Ägarens definition (1 nov 2026): fart i iscensättningen, hur samma händelse spelas ut. Inte
    // efterbearbetning (skak, zoomeffekter) och inte scenens längd. Skalan är asymmetrisk: det går
    // alltid att bli vildare, men lugnare har ett golv.
    fraga: 'Vilken av de två scenerna spelas ut med mer fart: personernas rörelse och momentum, entréer, det som händer runt dem, hur mycket de fyller bilden och varifrån scenen ses? Inte effekter eller skak.',
    andar: ['subtil, lugn: personerna står still, små i bild, inget händer runt dem', 'rörlig, expansiv: personerna rör sig med fart, fyller bilden, kommer in, det händer saker runt dem'],
    kriterier: [
      'Stilla: personerna står still och tar liten plats i bilden, inget händer runt dem.',
      'Lugn: små rörelser, personerna står kvar, bilden är luftig.',
      'Måttlig: tydliga gester eller en person som rör sig, eller personerna fyller bilden.',
      'Rörlig: personer som går in eller ut, rörelse med fart, något händer runt dem.',
      'Mycket rörlig och expansiv: rörelse med fart som tar bilden, entréer, mycket som händer samtidigt.',
    ],
    egenskaper: ['momentum', 'motiv', 'motiv_topp', 'andel_bild', 'fard', 'in_ut', 'bakgrund', 'hand_fart', 'utsnitt_nara', 'kamera', 'foljer', 'energi', 'skak', 'ryck_kamera', 'pan', 'zoom'],
    start: { momentum: 1, andel_bild: 0.8, fard: 0.7, in_ut: 0.5, bakgrund: 0.4, motiv: 0.4, hand_fart: 0.3, utsnitt_nara: 0.3, kamera: 0.3, foljer: 0.2, energi: 0.2, skak: 0, ryck_kamera: 0, pan: 0.1, zoom: 0.1 },
  },
  {
    id: 'agerande',
    namn: 'Agerande',
    niva: 'central',
    enhet: 'scen',
    fraga: 'I vilken scen agerar personerna (eller händerna) mer: rörelse, gester, energi?',
    andar: ['står still, inga gester', 'mycket rörelse och energi'],
    kriterier: [
      'Ingen person eller hand rör sig nämnvärt.',
      'Små rörelser: pratar, nickar, lugna gester.',
      'Tydliga gester eller en handling (äter, lagar mat, visar något).',
      'Mycket rörelse: går, dansar, stora gester.',
      'Hela scenen bärs av energiskt, överdrivet agerande.',
    ],
    egenskaper: ['motiv', 'motiv_topp', 'personer', 'hander', 'hand_fart', 'storlek', 'utsnitt_nara', 'u_objekt', 'langd'],
    start: { motiv: 1, motiv_topp: 0.6, hand_fart: 0.6, hander: 0.2, personer: 0.2, u_objekt: -0.8 },
  },
  {
    id: 'rytm',
    namn: 'Klipprytm',
    niva: 'central',
    enhet: 'klipp',
    fraga: 'Vilket klipp har högre tempo i klippningen: fler scener, hopp och byten av utsnitt?',
    andar: ['en lång tagning', 'snabbt klippt, många byten'],
    kriterier: [
      'En enda lång tagning utan klipp.',
      'Få scener, lugnt tempo.',
      'Flera scener eller några hoppklipp.',
      'Många scener och hopp, tydligt tempo.',
      'Mycket snabbt klippt, montagekänsla genom hela klippet.',
    ],
    egenskaper: ['scener_per_s', 'dynamik', 'utsnittsbyten', 'montage', 'langd'],
    start: { scener_per_s: 1, dynamik: 0.8, utsnittsbyten: 0.5, montage: 0.4 },
  },
  {
    id: 'energi',
    namn: 'Energi (kombinerad)',
    niva: 'kombinerad',
    enhet: 'klipp',
    byggerPa: ['rorlighet', 'agerande', 'rytm'],
    fraga: 'Vilket klipp känns mer energiskt som helhet?',
    andar: ['lugnt och stilla', 'högt tempo och mycket energi'],
    kriterier: ['Lugnt', 'Ganska lugnt', 'Mellan', 'Energiskt', 'Mycket energiskt'],
  },
  {
    id: 'humor',
    namn: 'Humor ↔ marknadsföring (kombinerad)',
    niva: 'kombinerad',
    enhet: 'klipp',
    byggerPa: ['rorlighet', 'agerande', 'rytm'],
    kraver: 'semantik: vad som sägs och händer (Gemini per scen), inte bara rörelse',
    fraga: 'Vilket klipp drar mer åt humor än åt rak marknadsföring?',
    andar: ['rak marknadsföring', 'ren humor'],
    kriterier: ['Rak produktvisning', 'Mest information', 'Blandat', 'Mest underhållning', 'Ren humor'],
  },
]

export const vertikal = id => VERTIKALER.find(v => v.id === id)
