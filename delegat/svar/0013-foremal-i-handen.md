---
id: 0013
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-12
---

## Resultat
Ett föremål som hålls följer nu handen i den renderade filmen. Köttbiten sitter i handen i 9 av 11 tagningar i b-tilltal, och provskeden i S1 i gelato.

1. **Vilken hand** (`kontrakt/handforemal.py`): strålen genom maskens tyngdpunkt i slutkameran skärs med handledens kameradjup, för båda händerna hos de personer som är lästa i scenen.
   - Närmaste hand i 3D under 0,25 m håller föremålet i den bilden. Är det minst hälften av nyckelbilderna, räknas tagningen som hållen.
   - Saknas mask, används `halls_av` och den hand som ligger närmast rutan.
   - **Vilka föremål som kan hållas:** de som har `halls_av`, och de som saknar byggt stöd (inget `pa`, eller `stod_ersatt`, som köttbitens inslagspapper). Vågen på disken räknas inte, fast handen är nära. I första körningen gjorde den det; se Avvikelser.
2. **Fästet** (`ingest/mhr_rig.py`, `bygg_handforemal`): förskjutningen i handledens ram är medianen över nyckelbilderna. Byggaren använder Child Of vid `r_wrist`/`l_wrist`, med lokal matris (1/s)·C⁻¹·T(förskjutning). Föremålet följer alltså handens matris i varje ruta, också där handvilan har lugnat handen. **Blenders världsläge i kontrollrutorna är detsamma som Pythons förutsägelse (under 0,1 mm i alla 34 kontrollrutor).**
3. **Storlek:** maskens bredd och höjd på handens djup, inom deklarerat intervall. Formen är en ellipsoid.
4. **Kedjan:** `rum_rutor.py` skriver `nyckelbilder` per tagning. Datavägen är `hand.json` → `plats.json` → `plan.plats[].deklarerat.foremal` → `handforemal.los` (sist i `kompilera.py`) → `plan.handforemal` (id `<roll>:hand:<id>`, en post per tagning) → byggaren. Stödets `:pa:`-kopia döljs där föremålet är i handen. Handposten ligger inte i `plan.objekt`, så skymningen kan inte stryka den (prov).
5. **Två händer och byten:** sådana fall redovisas i `kvalitet.handforemal`. I b S1 väljer bilderna v, h, v, v, och fästet blir vänster hand. Två händer samtidigt förekom inte. Mellan tagningar byter föremålet person (A → B → C), och varje tagning får ett eget fäste.

### b-tilltal `n06-hand`: föremålets projicerade mitt mot maskens tyngdpunkt (promille av bildhöjden) och hand utan bildstöd
| tagn | hand | promille per kontrollruta | mått (m) | rutor utan bildstöd |
|---|---|---|---|---|
| S1 | A vänster | 35, 59, 33 | 0,21 × 0,21 × 0,11 | 19 av 50 |
| S2 | A höger | 16, 7, 33, 17 | 0,25 × 0,25 × 0,19 | **52 av 52** |
| S3 | B höger | 10, 7, 19 | 0,25 × 0,25 × 0,11 | 4 av 42 |
| S4 | B höger | 15, 14, 9, 67 | 0,25 × 0,25 × 0,12 | 5 av 72 |
| S5 | C höger | 59, 21, 47 | 0,25 × 0,25 × 0,19 | 33 av 46 |
| S6 | C höger | 34, 12, 4, 4 | 0,25 × 0,25 × 0,11 | 0 av 32 |
| S7 | C höger | 0, 8, 3 | 0,25 × 0,25 × 0,12 | 0 av 26 |
| S8 | C höger | 26, 38 (2 av 4 bilder i handen) | 0,25 × 0,25 × 0,19 | **20 av 20** |
| S9 | – | ingen mask (stoppad av överlappskontrollen), ligger på disken | | |
| S10 | – | inte i handen (0,52–0,67 m), ligger på vågen, som i originalet | | |
| S11 | C vänster | 37, 44, 30, 124 | 0,15 × 0,15 × 0,17 | 26 av 46 |
Bredden når taket 0,25 m i de flesta tagningar. Masken tar med pappret. Gelato S1: A höger, 81, 129, 55 och 104 promille, 0,04 × 0,01 × 0,08 m, 77 av 156 rutor utan bildstöd. Gelato S2: bara 1 av 3 bilder i handen (0,21–0,28 m), så skeden byggs inte där.

### Vad som syns
Översikt: `scen/3d/kontrakt/ut/fore_hand_0013/oversikt_b.png` och `oversikt_gelato.png`.
- **s2, s4, s6:** köttbiten sitter i händerna i midjehöjd. Storleken är rimlig (originalets bit är mer avlång och ligger på papper), och den skymmer händerna och magen rätt.
- **s11:** biten sitter i vänster hand, men den skyms helt av vågens låda (0012). Det är vågens form, inte fästet, som är fel.
- **Gelato s1, ruta 104:** skeden sitter vid handen som räcks fram och är liten, som i originalet. **Ruta 52:** i originalet står skeden i glassdisken, men fästet sitter ändå vid handen, eftersom en hållen del av tagningen byggs som hela tagningen.
- **Gelato s2:** ingen sked byggs. Originalet visar en större glasspade vid munnen.

Filmer: `scen/3d/kontrakt/ut/b-tilltal-ravara_n06-hand/narvaro/film.mp4` och `scen/3d/kontrakt/ut/kand-kennysgelato_n06-hand/narvaro/film.mp4`.

## Ändrade eller nya filer
Baslinjen ligger i `scen/3d/kontrakt/ut/fore_hand_0013/kod/`.
- **Nya:** `kontrakt/handforemal.py`, och i `fore_hand_0013/` `matt_hand.{py,json}`, `oforandrad.{py,json}`, `kor_gelato.py`, `modal_segmentera_reserv.py`, deklarationer, `seg_gelato.json` och loggar.
- **Ändrade:** `ingest/mhr_rig.py`, `ingest/rum_rutor.py` (`nyckelbilder`), `kontrakt/kompilera.py` (ett anrop), `kontrakt/test_snabb.py` (+5), `ingest/test_rum.py`, `PIPE.md` (nytt avsnitt) och `NASTA.md` (överst).
- **Varianter:** `kontrakt/ut/b-tilltal-ravara_n06-hand/`, `kand-kennysgelato_n06-hand/`, `ingest/ut/*/plats_n06-hand/`.
- Felaktiga första körningar är flyttade till `fore_hand_0013/forsta_korning/`.

## Kontroll mot "Klart när"
- [x] Tester: `test_snabb` 39 OK och ingest 21 OK, med tom cache. Nya prov finns för punkt 1 (hand, avstånd, kandidat), punkt 2 (förskjutningen återfås) och punkt 4 (stödkopian döljs, skymningen ser inte handen, oförändrad plan).
- [x] b-tilltal `n06-hand`: promille per tagning, minst tre rutor i alla tagningar utom S8, där 2 av 4 bilder var i handen.
- [x] Filmer för b-tilltal och gelato, och bilder per tagning med beskrivning.
- [x] Rutor utan bildstöd per tagning (tabellen).
- [x] `PIPE.md` och `NASTA.md`.
- [x] Notan och guacamole: alla 70 planer ger `None` och är byteidentiska (`oforandrad.json`). `mhr_rig` gör ingenting utan `plan.handforemal`.

## Avvikelser
- **Köttbiten saknar `halls_av`.** Masken mot handlederna avgör. Utan regeln om "inget byggt stöd" hade vågen också fästs i handen (första körningen).
- **Gelatos uppsättning angav fel spår:** `spar_id` 1 för S2, men ingestens enda spår där är 5. Jag rättade det i min kopia av deklarationen och märkte det (`spar_id_kalla`). `rum_uppsattning.py` är inte ändrad.
- **Gelato kördes via ett omslag** (`kor_gelato.py`), eftersom videon heter `kand-kennysgelato2.0-….mp4` och `klipp_kor.py` kräver samma namn som ingesten.
- **Segmenteringen** fastnade i kön till L4 i 20 minuter. Den kördes därför med en kopia som tillåter A10G/T4 (fick A10). `modal_segmentera.py` ingår inte i uppdragets filer. Gateway behövdes inte, eftersom gelatos uppsättning hade `halls_av`.
- **Hållen del av en tagning byggs som hela tagningen** (enligt uppdraget). Gelato S1 och b S5/S8 har bilder där föremålet inte är i handen.
- **Trösklar** (valda, diagnostiska): 0,25 m till handleden, minst hälften av bilderna, två händer inom 1,5 × den närmaste, 0,08 m förskjutning utan mask.
- **Kostnad:** Modal 13,4 GPU-sekunder på A10, uppskattat under 0,02 USD. Gateway 0 USD.
