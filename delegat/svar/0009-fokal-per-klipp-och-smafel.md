---
id: 0009
status: klart
av: uppdragstagaren (Claude-appen, Sonnet 5.5)
datum: 2026-11-12
---

## Resultat
Brännvidden är nu ett värde per klipp med redovisad status och källa hela vägen till `plan.json`, och en COLMAP-fokal som avviker från klippets spridning (S5: 2,3 gånger) avvisas. Ingen ingest kördes om. Det som ändras visas på minneskopia nedan.

1. **Fokal per klipp:** `ingest/fokal_klipp.py` (ny). `bestam` tar klippets median av försvinningspunktskandidater som värde och kvartilerna som spridning. En tagnings COLMAP-värde godtas (`matt`) bara inom spridningen, annars får tagningen klippvärdet (`skattad`). Saknas allt gäller `max(bredd, höjd)` (`antagen`).
2. **Redovisning:** `fokal_px`, `fokal_status`, `fokal_kalla` per scen i `kvalitet.kamerakalibrering` (`kontrakt/kompilera.py`, `fokalredovisning`).
3. **Rörlig zoom:** en tagning behåller sitt eget värde när dess egna försvinningspunkter (minst tre) och COLMAP stämmer med varandra inom 15 % men avviker mer än 35 % från klippet. Avvikelsen loggas. Annars klippvärdet.
4. **Dubbla `disk_A`:** ingen bugg att rätta. `kontrakt/skymning.py:269–279` delar ett objekt som utelämnas i vissa scener i en post per synlighetsintervall (disk_A `[0,102]` och `[216,470]`, utelämnad i s3 och s4). Det nya provet kräver att varje `(id, synlig_ut)` är unikt och intervallen disjunkta.
5. **Stödkedjan för `kottbit`:** `ingest/deklaration_till_hand.py` (`ersatt_stod`) ersätter ett stöd som inte byggs med bordet vars `tagningar_i_bild` täcker flest av föremålets tagningar. `kottbit` blir `disk_C:pa:kottbit` och loggas som `stod_ersatt`.

## Fokal per klipp i dag och med nya regeln (`fyra_klipp.md`, minneskopia)
| klipp | klippvärde (spridning), kandidater | tagning: i dag → ny, status | läses om |
|---|---|---|---|
| b-tilltal (1024 px) | 1 021 px (905–1 255), 51 | S1–S4, S6–S11: 1 024 → 1 021 `skattad`. **S5: 2 335 → 1 021** `skattad` (COLMAP 2,29 × klippet avvisas) | **S5** |
| guacamole (1024) | 750 px (606–908), 20 | S1–S4: 1 024 → 750 `skattad` | **alla fyra** |
| notan (1024) | 984 px (860–1 132), 17 | **S2: 1 566 → 984, S5: 1 169 → 984**, övriga 1 024 → 984 | **S2, S5** (övriga inom 10 %) |
| gelato (1920) | 1 523 px (1 457–1 629), 8 ur 2 tagningar | **S1: 1 920 → 1 523** `skattad` (COLMAP 770 underkänd); S2 1 506 `matt` | **S1** |
Guacamole är den största förändringen (0,73 × dagens värde) och bygger på 20 kandidater med bred spridning. Notan S2 och S5 hade COLMAP-värden från bara 2 av 14 respektive 9 rutor. Behandla de nya värdena som skattningar, inte mått.

## Ändrade eller nya filer
Baslinjen kopierad först till `scen/3d/kontrakt/ut/fore_fokal_0009/kod/`.
- Ny: `scen/3d/ingest/fokal_klipp.py`, `kontrakt/ut/fore_fokal_0009/{fyra_klipp.py, fyra_klipp.json, fyra_klipp.md, identitet.py}`.
- Ändrade: `ingest/regler.py` (`kamerabeslut(k, m, klipp=None)`), `ingest/ingest_klipp.py` (`klippfokal`: `steg_kropp` läser `fokal_klipp.json` om den finns), `ingest/deklaration_till_hand.py`, `ingest/test_deklaration.py` (+3), `kontrakt/kompilera.py`, `kontrakt/test_snabb.py` (+2), `scen/3d/LOGG.md`.

## Kontroll mot "Klart när"
- [x] `test_snabb` 27 OK (var 25), `test_deklaration`, `test_rum`, `test_scenbrief` 18 OK (var 15). Körda med tom bytekodscache, och nya prov täcker punkt 1, 4 och 5.
- [x] Tabell per klipp (ovan).
- [x] Planen för exempelklippet `bar` (fokal oförändrad, 1 042 px `matt`) har samma hash före och efter (`af56b38df2563c2d`), bortsett från `kamerakalibrering` (tom → `[{scen: s1, fokal_px: 1042.3, fokal_status: matt, fokal_kalla: COLMAP (kamera.json)}]`). Jämfört med baslinjens `kompilera.py`.
- [x] Avsnitt i `scen/3d/LOGG.md`.

## Avvikelser
- **Punkt 4:** orsaken ligger i `skymning.py` (utanför mina filer) och är avsiktlig, så jag rättade inget där. Poster med samma id finns kvar med olika `synlig_ut`, och en uppslagning via enbart id ger den sista posten. Vill ägaren ha unika id krävs ett eget uppdrag som rör `skymning.py`, `proptid` och byggaren.
- **Punkt 5:** vilket bord som ersätter stödet är mitt val (flest delade tagningar). `kottbit` hålls i handen i de flesta tagningar, så "står på `disk_C`" är en byggplats, inte en sanning. Utan bord som delar tagning med föremålet förblir kedjan bruten som förut.
- **Egna trösklar** (diagnos, inte krav): försvinningspunkter minst 12 inliers, kandidater 0,3–3 × längsta sidan, minst 6 kandidater ur minst 2 tagningar, spridning = kvartiler, zoommatch 15 %, zoomavvikelse 35 %, omläsning när fokalen ändras över 10 %.
- `fokal_klipp.json` skrivs bara av `python fokal_klipp.py <ingestmapp>`. Tills någon kör det är ingestens beteende oförändrat.
