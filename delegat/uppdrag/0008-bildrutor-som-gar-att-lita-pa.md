---
id: 0008
titel: Bildrutor som går att lita på: korskontroll mellan tagningar och segmentering i stället för Geminis rutor
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0004
tillåten_skrivning: [scen/3d/ingest/rutprov/]
---

## Mål
Det ska vara känt hur kedjan får bildrutor för möbler och föremål som är rätt inom några procent av bildhöjden, och hur en felaktig ruta upptäcks utan ägarens ögon.

## Bakgrund
Svar 0001 och 0004 pekar åt samma håll: linsen är ungefär rätt (cirka 1 000 px), och oenigheten mellan tagningarna kommer ur bildrutorna. I `b-tilltal-ravara` pekar S6-rutan för `disk_C` på kassadelen, S7 har övre kanten 85 promille fel, S11-rutan för vågen täcker bara displayen, högerkanten i S8 är vågarmen, och `disk_A` fick ingen ruta alls. Rutorna kommer i dag från Gemini (`box_2d` 0–1000 i uppsättningssteget och `ingest/rum_detektera.py`).

Arbetsfördelningen som ska prövas: Gemini säger **vad** som finns och är relevant (det är den stabil på), en segmenteringsmodell säger **var** i bilden det ligger, och geometri mellan tagningar som delar kameraplats säger om rutorna är inbördes förenliga.

## Underlag
- Nuvarande rutor: `scen/3d/ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning3/deklaration_n06_detekterad.json` och `scen/3d/ingest/rum_detektera.py`
- Avlästa rätta kanter och felbeskrivningar: `delegat/svar/0001-granska-flerbildspassning.md` (Orsak per avvikare), `delegat/svar/0004-lins-och-kameradjup-per-tagning.md`
- Homografier mellan tagningar med samma kameraplats: `scen/3d/ingest/bakgrund_prov/matcha.py`, `b_par.json` (S6–S7, S8–S10, S9–S10, S3–S4, S1–S2)
- Lyft per tagning, för att räkna om till meter: `scen/3d/kontrakt/ut/diag_0001/lyft.py`
- Modal-mönster i repot: befintliga skript som `scen/3d/ingest/modal_sam3db.py`

## Delar
**A. Korskontroll utan modell.** För tagningspar som delar kameraplats: för över rutan från den ena tagningen till den andra med homografin och jämför med den andras ruta (IoU och kantavstånd). Homografin gäller strikt bara för bakgrundsplanet, så redovisa hur stort felet väntas bli för en disk nära kameran och bedöm om kontrollen ändå skiljer rätt från fel. Hittar den S6 mot S7, och S11 mot S8–S10 där koppling finns?

**B. Segmentering med textprompt på Modal.** Kör en öppen-vokabulär segmenterare (SAM 3 med begreppsprompt, eller Grounding DINO + SAM 2) på nyckelbilderna, med Geminis namn på elementen som prompt ("butcher counter", "scale", "meat", "paper"). Ta rutan ur masken. Flera rutor per tagning, median över tiden. Jämför mot Geminis rutor och mot de avlästa kanterna i 0001.

**C. Effekt.** Räkna om lyften per tagning med de nya rutorna (utan kompilering) och redovisa spridningen för `disk_C` över S6–S9, S11 och för vågen över S8–S11, bredvid 0004:s tal (0,54 m och 0,92 m).

## Gränser
- Bara nya filer i `tillåten_skrivning`. Ingenting installeras i `scen/.venv`.
- Modal är förhandsgodkänt enligt `REGLER.md` (läs om filen från disk). Kostnadstak 1,00 dollar. Bara nyckelbilder skickas upp.
- Notera segmenterarens licens i svaret.
- Inga Gemini-anrop behövs; namnen finns redan i deklarationen.
- Masken ger mer än en ruta (till exempel diskens ovansida som polygon). Notera vad som skulle gå att använda senare, men bygg inte det nu.
- Egna trösklar är diagnos och inte krav.

## Klart när
- Del A: tabell över paren med IoU och kantavstånd, och ett tydligt svar på om kontrollen pekar ut de kända felen.
- Del B: per element och tagning, Geminis ruta, segmenterarens ruta och den avlästa kanten där en sådan finns. En bild per tagning S6–S11 med båda rutorna ritade.
- Del B: fick `disk_A` en ruta i S1–S4?
- Del C: spridningstabellen före och efter.
- Bedömning i högst fem rader: vilken källa ska rutorna ha i kedjan, och vilken kontroll ska stoppa en felaktig ruta.

## Leveransform
`delegat/svar/0008-bildrutor-som-gar-att-lita-pa.md` enligt mallen, högst cirka 70 rader, med faktisk Modal-kostnad. Skript, JSON och bilder i `scen/3d/ingest/rutprov/`.
