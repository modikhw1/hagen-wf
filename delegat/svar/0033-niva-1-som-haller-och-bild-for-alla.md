---
id: 0033
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
0033 är utfört i den form som 0034 ändrade den till. Punkterna 1, 3 och 4 är gjorda. Punkt 2 (speglingen) och punkt 5 (Dreamina bredvid) är strukna, och skälen står i 0034.

**1. Svar 0031 är ifyllt:**
- **sha256:** samma i åtta fall, med tom cache och före-kod ur `fore_0031`.
- **Tester:** 240, med samma åtta fel som före.
- `SE_KOMPAT` och `SE_TESTER` är borta.

**3. Kunden som roll.**
- **Variant i källan:** `kalla_variant.py` (allmän för en platshållarperson av lådor) ger kundens arm en variant för den andra handen. Axeln speglas över kroppens mittplan, mot samma handpunkt, så kontakten med skeden står kvar. Varianten är märkt antagen.
- **Liggare och källa:** liggaren `liggare_0033.json` gör `fg_kund_hand` till nivå 3d med regi `satt_frihetsgrad` (person kund). Källan är `kalla_0033.json` (revision 9).
- **Kompilatorn:** en platshållarperson får varianten i scenbygget. Planens `kund:arm` får `variant: {kroppsdel: vanster}`.
- **Kontrollen:** `kontrollera.py` godtar platshållarpersoner som har en variant.
- **Bild:** m9 i kontaktbladet. Armen kommer in från andra sidan och möter skeden.

**4. Bild för allt:** [kontaktblad.jpg](../../forvarld/gelato/ut_0033/kontaktblad.jpg) har en rad per mening (m1–m7, m9, m11): original, före, efter, Jevs val och utruta. Planerna och renderingarna ligger i `forvarld/gelato/ut_0033/`.

| # | Ser man det? |
|---|---|
| m1 | ja: mitt i övergången rätar hon på sig där originalet skopar |
| m2 | ja: hon skopar fortfarande i utruta 100, där originalet räcker fram |
| m3 | ja: andra varvet, hon skopar igen i utruta 160 |
| m4 | ja: skeden är gul (platshållare för kakan) |
| m5 | ja: hon böjer sig ned i tomma luften |
| m6 | ja: stillastående kamera i s1, annat utsnitt (ingen inåkning) |
| m7 | ja: sista rutan hålls (281) |
| m9 | ja: kundens arm från andra sidan |
| m11 | nej: nivå 1-speglingen ser fel ut (deformerad axel); ersätts av 0034 |

**Kontroll:**
- **sha256** med före-kod `fore_0033`: åtta fall lika. Fallet "andra handen" (0031) skilde bara i filstämplarna för den härledda speglade sekvensen (`kvalitet.byggunderlag`, tid för filen). Planerna i övrigt är lika (`forvarld/liggare/ut_kompat_0033/`).
- **Tester:** 240, med samma åtta fel.

## Bedömning
- **Nivå 1 räcker för det som inte rör kroppens form:** tid, ordning, föremål, möbler, kamera, och platshållarnas lådor (kunden).
- **Nivå 1 räcker inte för en armändring.** Spegling ger fel kropp (0031). Gränsen går vid att kroppen själv måste anpassa sig. Det är 0034:s kontroller, inte nivå 3, som enligt ägarens besked är struken.

## Ändrade eller nya filer
- **Kontrakt:**
  - ändrade, med före-kopior i `ut/fore_0033/kod/`: `kompilera.py` (variant för platshållarperson) och `kontrollera.py`
  - nya: `kalla_variant.py` och `ut/kand-kennysgelato_n06-hand/{kalla_0033_var,kalla_0033,liggare_0033}.json`
- **Förvärld:** `forvarld/gelato/ut_0033/` och `rendera_0033.py`; `forvarld/liggare/bakatkompatibel_0033.py`.
- **Gennedbrytning:** `d_video/dreamina-paket/vanster_hand/LAS-MIG.md` är märkt återkallad (0034).

## Kontroll mot "Klart när" (med 0034:s ändring)
- [x] Svar 0031 ifyllt.
- [—] `andra_handen.mp4` med spegling: struket. Ersatt av 0034:s prov.
- [x] `fg_kund_hand` med regi och bild.
- [x] Kontaktbladet med alla meningar.
- [x] Bedömning.

## Avvikelser
- **Punkterna 2 och 5 är strukna enligt 0034.**
- **Blender kraschade två gånger** (minnesfel 0xC0000005) när den renderade parallellt med testerna. Omkörningen ensam gick igenom.
- Ingen Jev, Modal, Codex eller generering.
