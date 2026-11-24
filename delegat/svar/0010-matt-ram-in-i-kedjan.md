---
id: 0010
status: klart
av: uppdragstagaren (Claude-appen, Sonnet 5.5)
datum: 2026-11-12
---

## Resultat
Alla sex punkter är gjorda och körda på b-tilltal och guacamole med film. Resultatet är **blandat**: kameragrupperna och rutkontrollerna fungerar som provet visade, men disken och vågen hamnar fortfarande fel i x i b-tilltal, och vågen syns nu på fel ställe i s11. Det jag tror på och inte tror på står nedan.

1. **`ingest/rum_grupper.py`** (ny): mätta kameragrupper med nollgräns härledd per klipp. b-tilltal `delar_plats` = {S3,S4}, {S6,S7}, {S8,S10}; guacamole {S1,S3}. Övriga par är inte mätta (S1–S2, S9, S11 och S5 saknar koppling över parets egen nollgräns; det är inte motbevisat). Absolut nollgräns 43,1 (b) och 22,4 (guacamole) ur ett annat klipp; per par 1,5 × vad parets 20 slumpade matchningar högst nådde. Valda trösklar: homografi ≥ 60 %, rotation ≤ 30°, minst hälften av bildrutparen över gränsen.
2. **`rum_konsensus.py --grupper`**: mätta par är givna fakta (andel 1,0), röstat gäller övriga och märks i rapport och `_meta.json`. Kontroll på b-tilltal (samma fem förslag): utan grupper `{S8} | {S9} | {S10, S11}`, med grupper `{S8, S10, S11} | {S9}`. Alltså ändrar mätningen kamerapartitionen.
3. **`ingest/modal_segmentera.py`** och **`ingest/rum_rutor.py`** (nya): Grounding DINO + SAM 2 (Apache-2.0) på Modal med Geminis namn som prompt, och tre kontroller (överlapp IoU ≥ 0,7, homografi IoU ≥ 0,25, null). Valda trösklar. På b-tilltal stoppades `disk_C` S9 (överlapp med vågen) och 2 element blev `null` (bl.a. vågen i S11). Homografikontrollen stoppade inget.
4. **Flagga:** `rum_detektera.py --rutor segment --seg <seg.json> [--grupper <grupper.json>]`; `--rutor gemini` är förvalet och oförändrat.
5. **Körning:** b-tilltal `n06-matt` (segmentering) mot `n06-fler2` (Geminis rutor, samma nya kod), båda `prepare`, och `n06-matt` renderad. Guacamole variant `matt` (`prepare` + `render`) utan handpåläggning.
6. **Dokumentation:** nytt avsnitt "Mätt ram före deklarationen" i `PIPE.md` och ett lägesavsnitt överst i `NASTA.md`.

### b-tilltal, nya mot gamla vägen (`jamfor_matt.json`)
| | `n06-fler2` (Gemini) | `n06-matt` (segmentering) |
|---|---|---|
| spridning disk_C S6,S7,S8,S9,S11 (m) | 2,32 | 1,24 (fyra boxar, S9 stoppad) |
| spridning vågen S8–S11 (m) | 0,92 | **0,42** (tre boxar) |
| uteslutna i passningen | S6, S11 | S5, S8, S11 |
| stoppade rutor | – | `disk_C` S9 (överlapp) |
| ankarrest | 0,057 m | 0,057 m (oförändrat: samma deklaration) |
| disk_C läge (x, y) | (1,18; 1,00) | **(3,09; 0,86)** |
| ordningsnivå / granskonflikt | 2 / ja (S9) | 0 / nej |
| personer mot facit | 55/55 (oförändrat, samma deklaration; inte omräknat) | densamma |
**Projektion i slutkameran** (övre kant i promille av bildhöjden mot segmenterarens ruta i nyckelbilden): disk S6 −112 → **−60**, disk S11 −58 → **+22**, vågen S10 topp 39 → **24** och botten −76 → **+3**. Bättre i alla fem mått.

### Vad som syns i filmen (`b-tilltal-ravara_n06-matt/narvaro/film.mp4`)
**Bättre:** vågen finns med (n06-fler tappade den i s11), `disk_C` får rätt djup (y 0,86, kring 0,65–0,73 enligt rättade S6 och S7), och ingen kamera hamnar i disken (marginal 0,30 m).
**Fortfarande fel:** `disk_C` ligger på x ≈ 3,09 (mitt), alltså bortom sidoväggen (3,28 m); x styrs av en enda vänsterkant (S10 x0 = 213 promille), eftersom disken går utanför bild i övriga tagningar. I `blad/s11.png` står vågen som ett stort grått block över personens högra sida, medan den i originalet står längst ned till vänster. Rutan är rätt, men placeringen i sidled är underbestämd. (Referensläget är x ≈ 2,2.)

### Guacamole (`e-dialog-guacamole_matt/narvaro/film.mp4`)
Går igenom utan handpåläggning: `rum_rutor` gav `bardisk` rutor i S1–S4 (S1 utesluten i passningen), disken flyttades till (−0,66; 0,25), ingen kamera i disken, ankarrest 0,050 m, film renderad. Här stannar det: `fokal_klipp.json` kördes inte, så `kamerakalibrering` visar fortfarande 1 024 px `antagen` i alla tagningar.

## Ändrade eller nya filer
Baslinjen i `scen/3d/kontrakt/ut/fore_mattram_0010/kod/`. Nya: `ingest/rum_grupper.py`, `rum_rutor.py`, `modal_segmentera.py`. Ändrade: `ingest/rum_konsensus.py`, `rum_detektera.py`, `test_rum.py` (+2), `PIPE.md`, `NASTA.md`. Varianter (nya mappar): `kontrakt/ut/b-tilltal-ravara_n06-fler2`, `_n06-matt`, `e-dialog-guacamole_matt`, och `ingest/ut/*/plats_n06-fler2`, `plats_n06-matt`, `plats_matt`. Resultat och logg: `kontrakt/ut/fore_mattram_0010/`. Inga befintliga mappar skrevs över. `klipp_kor.py` och `rum_uppsattning.py` ändrades inte.

## Kontroll mot "Klart när"
- [x] Tester gröna: `test_rum` + `test_deklaration` + `test_scenbrief` 20 OK (var 18), `test_snabb` 27 OK. Nya prov för grupperna och de tre rutkontrollerna.
- [x] b-tilltal nya mot gamla: tabell ovan.
- [x] Projektion i slutkameran (promille): ovan, för s6, s10 och s11.
- [x] Film för b-tilltal i nya varianten, med vad som syns bättre och fortfarande är fel.
- [x] Andra klippet (guacamole) går igenom utan handpåläggning, och var det stannar står ovan.
- [x] `PIPE.md` och `NASTA.md` uppdaterade.

## Avvikelser
- **Kostnad:** Modal för segmentering på b-tilltal och guacamole, uppskattat under 0,05 USD (cirka 2 × 60–100 GPU-sekunder; fakturan kunde jag inte läsa). Gateway: 0 USD (inga nya Gemini-körningar; konsensuskontrollen återanvände befintliga svar).
- **Trösklar:** härledda ur data är den absoluta nollgränsen (p99 mot annat klipp) och parets egen permutationsgräns (faktorn 1,5 är vald). Valda är homografi ≥ 60 %, rotation ≤ 30°, minst hälften av rutparen, överlapp 0,7, homografi 0,25, minsta poäng 0,25. Nollgränsen för grupperna blev striktare än provet (S1–S2 och S9–S10 hamnade under), vilket jag lät stå.
- **Deklarationen** är densamma som `n06` (bara rutorna är nya), så konsensussteget kördes inte om för varianterna. `--grupper` är provat separat på b-tilltal (se punkt 2).
- **Segmenteraren är inte deterministisk** mellan körningar (S8-rutan för `disk_C` blev [712,…] i 0008 och [603,…] här), så rutor ska behandlas som skattningar.
- `rum_uppsattning.py` kopplades inte in (flaggan finns i `rum_detektera.py`).
