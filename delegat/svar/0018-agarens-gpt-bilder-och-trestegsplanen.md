---
id: 0018
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-12
---

> **13 nov:** det som återstår (0017 del G, 0018 punkterna 4–6, 0019 varianterna b och c) redovisas i `delegat/svar/0021-kamerafri-kalla-och-in-i-forvarlden.md`.

## Resultat
0018 är invävt i 0017, eftersom 0017 inte var förbi del D. Se `delegat/svar/0017-generativ-nedbrytning-vid-ingest.md`.
- **Punkterna 1 och 2 är klara:** storleken rättas lokalt med `scen/3d/gennedbrytning/passa.py`. Tabellerna för tom scen och isolerad person finns i svar 0017.
- **Punkterna 3–6 väntar:** stillbildsläsning, segmenterare, rum med kamera och kombination. De görs tillsammans med 0019:s nyckelbilder.

**13 nov:**
- **Punkt 3 är klar** (svar 0019): ruta 0 ur den passade GPT-bilden ger överkroppen 7,5 promille från dagens läsning, och ben mot överkropp 1,68 mot 1,65. Underkroppen syns nu: lår 0,44 m och underben 0,39 m, samma på båda sidor.
- **Rutor för ägaren:** steg B för rutorna 55, 112 och 146 bör ägaren köra i GPT, eftersom Codex inte gör det. Indata är `nyckel/ruta_NNN.png` och `nyckel/A_NNN.png`, och prompten är `nyckel/prompt/B3.txt`. Rutorna är dock så nära att hela kroppen inte får plats.
- **Punkterna 4–6 är inte gjorda:** segmenterare, rum med kamera och kombination.
