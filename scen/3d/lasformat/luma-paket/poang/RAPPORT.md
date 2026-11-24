# Steg 1, poäng för Luma-stillbilderna (11 nov 2026)

Bilderna är F1–F7a på S1 och S4. F7b var inte körd. Varje bild läses med SAM 3D Body (Modal, cirka 0,5 s per bild), Depth Anything V2 Small (lokalt) och Gemini 3.5 Flash-Lite, och jämförs med originalrutan. Posen jämförs efter Procrustes, så att ändrad beskärning och vinkel inte räknas som drift. Skript: `../poang.py`. Panel: `panel.jpg`, där röda punkter är SAM:s leder.

| Format | Bild | Posedrift 2D (% kroppshöjd) | Pose 3D (cm) | Längd SAM (m) | Ben i bild (av 4) | Djup ρ mot original |
|---|---|---|---|---|---|---|
| original | S1 / S4 | – | – | 1,28 sittande / 1,77 | 0 / 0 | – |
| F1 städat | S1 | 0,8 | 0,6 | 1,28 | 0 | 0,997 |
| F1 städat | S4 / S4_b | 0,4 / 0,4 | 0,6 / 0,7 | 1,77 / 1,77 | 0 | 0,98 |
| **F2 breddat** | S1 | **16,0** | 10,7 | 1,34 | 2 | – |
| **F2 breddat** | S4 | **1,0** | 3,4 | 1,80 | **4** | – |
| F3 djupbild | S1 / S4 | 1,2 / 1,0 | 1,1 / 2,4 | 1,29 / 1,78 | 0 | **0,996 / 0,990** |
| F4 skyltdocka | S1 / S4 | 2,3 / 0,8 | 2,6 / 1,5 | 1,35 / 1,76 | 0 | 0,98 / 0,96 |
| F5 rumsskal | S1 / S4 | ingen person | – | – | – | 0,68 / 0,36 |
| F6 färgytor | S1 (två) / S4 | 32 / 33 / 1,0 | 17 / 16 / 2,9 | 1,61 / 1,59 / 1,73 | 0 | 0,83 / 0,81 / 0,85 |
| F7a sidovy | S1 / S4 | 4,4 / 8,8 (väntat, ny vinkel) | 2,6 / 2,5 | 1,27 / 1,78 | 0 | – |

## Vad det betyder

- **F1 städat: nästan ingen drift.** Posen avviker under 1 %. Gäster och undertext är borta. Ansikten och mat finns kvar, men logotypen blev en kaffekedjas.
- **F2 breddat fungerar för servitören och inte för kvinnan.** I S4 syns hela kroppen, alla fyra benleder ligger i bild, posen håller (1 %) och längden blir 1,80 m. Skorna är påhittade: vita sneakers här, svarta i Wan. I S1 ritade Luma om kvinnan som sittande i helfigur och ändrade händerna (16 %). Det är samma "egna beslut" som i 7 nov-teckningarna.
- **F3 djupbild är en överraskning.** SAM läser kroppen ur Lumas djupbild nästan lika bra som ur fotot (1–2 %), och djupet stämmer med originalets djupskattning (ρ 0,99–0,996). Lumas djup ser alltså ut att vara en ren djupskattning av fotot, inte en fri omtolkning. Vattenstämpeln ligger i bilden och stör.
- **F4 skyltdocka:** posen håller, men det ger ingen vinst över F1.
- **F5 rumsskal är inte troget.** Luma byggde ett nytt rum (ρ 0,36–0,68), och rutorna är fel storlek enligt Lumas egen agent.
- **F6 färgytor:** i S1 läser SAM inte den röda klumpen som kropp (32 %). S4 fungerar. Formatet är inte pålitligt.
- **F7a sidovy:** Luma vred bara kameran cirka 20–30°, inte 90°. Kroppens 3D-pose är densamma (2,5 cm), så den nya vinkeln är konsekvent, men för liten för att ge mycket djup.
- **Föremål (Gemini):** Geminis egna svar varierar så mycket mellan körningar (dörr och mobil försvinner i F1 S4) att föremålslistorna inte skiljer formaten åt. Det är inget mått att lita på i den här formen.

## Kandidater för steg 2 (video)

1. **F2 breddat på S4**, naken och regisserad. Det är direkt jämförbart med Wan A: håller Luma gången och fötterna över tid?
2. **F2 breddat på S1, regisserad.** Hjälper scenbeskrivningen gesterna, som stillbilden tappade?
3. **F3 djup på S4.** Är Lumas djupvideo stabil över tid? Wans breddade bakgrund gav ett instabilt rum (MoGe 23 %).
4. Möjligen F1 på S1 som kontroll med liten risk.

F5, F6 och F7a utgår.
