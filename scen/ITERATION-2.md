# Iteration 2 (7 nov 2026): Gemini-språk, kameralager, nivåmodell

Efter ägarens kritik av iteration 1 togs tre saker upp: kameran som egen faktor, bedömning av kärnföremål, och att binda mening och rörelse i ett objekt inom scen inom klipp.

## 1. Scenskrift `ss/0.1` (Gemini)

- Specifikation i `sprak/README.md`, anrop i `sprak/gemini.mjs`, granskning i `sprak/granska.py`.
- REST-API:t avvisar fältet `processing` som dokumentationen visar; `videoMetadata.fps` fungerar.
- Nodes fetch ger upp efter 300 s utan svarshuvud, så anropet görs med curl och SSE.
- Tid: kön på `gemini-3.8-flash` gratis tog 17–195 s före första token. Samma anrop på `3.5-flash-lite` tog 6,4 s totalt. Utskriften går med ca 180 tokens/s.
- En körning fastnade i en loop i ett fritt textfält (32 000 tokens skräp). Alla id- och riktningsfält är nu slutna listor.

| Klipp | Tagningar mot facit | Handling, roller, repliker | Positioner (inom 80/1000 av YOLO) | Täthet |
|---|---|---|---|---|
| C, 5 fps | 1 av 1 | rätt, tider inom ~0,5 s, följde tallriken | 10 % | 7–8 waypoints per person |
| A, 5 fps | 8 tagningar = alla 7 klipp | rätt; såg att en skådespelare spelar båda rollerna; avsikt per tagning rätt; handlingar utan föremål | – | 15 totalt |
| B, 5 fps | 4 av minst 6 | grovt rätt, men tunt (5 repliker) | – | 5 totalt |

Fler bildrutor in (2 → 10 fps) gav inte fler waypoints ut.

## 2. Kameralagret (`py/kamera.py`)

- Kamerans rörelse skattas ur bakgrunden med personerna maskade (optiskt flöde + RANSAC, bildruta för bildruta). Registreringen kedjas inom ett segment, och ett klipp markeras där den brister.
- **Kompensering:** i C ser killen längst bak ut att röra sig 0,33 i bild men 0,14 i scenen. Hans "rörelse" var mest kameran. Kvinnan som sitter still ligger kvar på samma plats i mosaiken (`data/c-sketch-tre/kamera-mosaik-0.jpg`).
- **Klipp som biprodukt:**
  - A: alla 7 handmärkta klipp, plus 1 riktigt klipp mellan detaljbilder och 1 troligt falskt.
  - B: alla 4 handmärkta klipp, plus 2 riktiga som min facit missade (11,33 och 14,13 s). Falska klipp uppstår när köttbiten förs mot linsen (0,47 och 1,0 s), eftersom bara personer maskas.
  - C: inga klipp.
- **Brist:** i närbilder där personen fyller rutan finns för lite bakgrund. Där sätts flaggan `osaker` (bakgrund under 35 %).

## 3. Gemini + YOLO (`sprak/fusera.py`)

I C fick YOLO:s 9 spårfragment Geminis 3 identiteter, och 92 % av detektionerna fick ett id. Avståndsgränsen justerades efter att ha sett utfallet, så det måttet är anpassat till klippet. Video: `data/c-sketch-tre/enhet.mp4`.

## 4. Nivåmodellen v0 (`py/nivaer.py` → `data/<klipp>/klipp.json`)

```
Klipp
 ├ roller (Gemini: id, roll, utseende, funktion)
 └ Scen = Geminis tagning (takt, avsikt, utsnitt)
     ├ kameraavsnitt (kamerans segment: typ statisk/panorering/zoom/handhållen, osäker)
     ├ närvarande (P-id via YOLO-spår; reserv: ensam aktiv person får längsta spåret)
     ├ kärnföremål (nämnda i handlingar + det händerna rör; bord/stol flyttas till rummets inredning)
     └ Handlingsenhet = Gemini-handling (vem, verb, obj, mot, tid) + rörelse i scenkoordinater
                        (förflyttning, riktning, fart, andel sittande, skenbar rörelse i bild)
                        + 'närvaro' där en person syns utan handling
```

**Det som håller:**
- I C binds handlingar och kamerakompenserad rörelse i samma enhet. Exempel: "P3 närvaro 0,8–12,7 s: förflyttning 0,02 i scenen, 0,42 i bild, sitter 82 %", och "P3 går_till P2: 0,25 åt höger".
- B och A får rätt personer i rätt scener med reservregeln, och falska kameraklipp splittrar inte längre scenerna.

**Det som inte håller:**
- **Rörelse i närbilder** är meningslös: kroppspunkten tas från axlarna när höfterna inte syns, till exempel "lagar 0,49 vänster" i A. Den borde ersättas av kroppens eget rörelsemått, inte förflyttning.
- **Kärnföremål** är svaga. Gemini utelämnade föremål i A:s handlingar, och YOLO-World kallar köttbiten "pizza".
- **Ett spårfragment vid 23 s i C** är fel tilldelat, så P3 får fel riktning.
- **Korta handlingar och kamerans "handlingar"** (`K` frågar) saknar rörelsedata.
- **Händernas och kroppens rörelse** (gest, böjning, räcka) finns inte i enheten än. Bara förflyttning och sittande finns med.
