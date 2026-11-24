---
id: 0039
status: klart
från: uppdragstagaren (Fable, med Codex för tre delar)
datum: 2026-11-16
---

## Läge
MaskedMimic kör på Modal som en varm tjänst, följer referensen, tar villkor ur en fri mening för vilken tagning som helst, och utfallet renderas i förvärlden. Allt läge står i `forvarld/kropp/forskning/mm/FELSOK.md`. Läs den först.

FORSKNING: kontrollpunkten är AMASS-tränad och får inte användas kommersiellt. Allt som kommer ut är märkt så.

## Mot "Klart när"
| krav | läge |
|---|---|
| ProtoMotions med MaskedMimic kör på Modal, kommando och avbildning beskrivna | ja: `mm/tjanst.py` (appen `hagen-mm-tjanst`), `mm/kropp.py`, FELSOK.md. PROTOMOTIONS.md beskriver avbildningen. |
| Rundresan MHR–SMPL–MHR mätt | ja: 0,1 cm relativt bäckenet. I världen ligger roten 7–9 cm från originalets plats efter rättningen av `aterflytt`. |
| Steget `kroppsmodell` i kedjan bakom flaggan | **nej.** `kroppsmodell.py` pekar fortfarande på den gamla vägen (`modal run`). Den nya vägen är `mening.py` och `tagning.py`. Att byta steget i kedjan är en kedjeändring och bör ske efter att ägaren har sett utfallen. |
| Filmen med fyra bredvid varandra, mått, vad man ser, tider | delvis: `mm/ut/mening_andra_handen3/forvarld.mp4` har original, läst kropp och tre meningar (andra handen, blyg, stressad). 0034 och 0036 är inte med. |

## Vad man ser (andra handen, i förvärlden)
- Skopandet (ruta 45): hon står upprätt och vriden, och vänster arm går ner mot tråget. Originalet böjer sig fram.
- Räcka fram (ruta 125): kroppen är vänd åt sin högra sida och vänster arm når fram mot kunden.
- Hon flyttar fötterna och vrider bålen utan att glida. Det ser ut som en människa som löser uppgiften på ett annat sätt, inte som en speglad arm. Böjningen saknas.

## Mått
- Referensen genom kontrollern: alla leder 8 cm (var 107), bäcken 4–5, höger hand 5,5 vid skopa och 8 vid ge.
- Andra handen: vänster hand 9 cm från målet (skopa 15, räcka 7), på första varvet.
- Ryck efter utjämning: i nivå med originalet.

## Tider
- Kall container: 1–2 min. Varm: 13 s för 150 rutor, 5,7 s för 48.
- En hel mening (förstånd, kropp, bedömning): 28–32 s. Rendering i förvärlden: cirka 2,5 min per mening i lokal Blender.
- För att en ändring ska ta några sekunder återstår inferensen (65 ms per steg) och renderingen.

## Fel som hittades (belägg i FELSOK.md)
1. Kamerans inåkning låg som rotförflyttning i gelato S1, med fötterna förankrade.
2. Benen var gissade vid läsningen (fotlederna 31–37 cm framför bäckenet).
3. Ingen kropp var bunden: maskupprepning 1.0 upprepade startens tomma mask.
4. Målens tidssampling låg för långt fram, så snabba delar följdes inte.
5. Slumpad startfas (Codex).
6. Vägen tillbaka satte kroppen 65 cm fel i scenen. Min första kontroll missade det.

## Filer (alla under `forvarld/kropp/forskning/mm/`)
- Ändrade: `kor_mm.py`, `modal_mm.py` (bara två monterade filer till, ingen ombyggnad).
- Nya: `tjanst.py`, `arbetare.py`, `kropp.py`, `tagning.py`, `mening.py`, `erfarenheter.json`, `streck.py`, `jamfor.py`, `folj.py`, `forvarld_film.py`, `FELSOK.md`, `RATTNING-0039.md`, `DIAG-0039.md`.
- Utanför: `byggsten/hand/forstand.py`, `bord.py`, `bord/index.html` (knappen "Kör på kroppen").
- Baslinje före ändringar: `forskning/kontrakt/ut/fore_rattning_0039/`.

## Avvikelser
- "Ingen LLM som skriver rörelsen": språkmodellen skriver villkoren, inte rörelsen. Ägarens besked 16 nov.
- Disken finns inte som hinder i simuleringen.
- Rättningarna 1 och 2 görs i en rimlighetsgrind i `tagning.py`. De hör hemma i kedjan (kameralösningen, `ben_synliga`). Förslag, kräver ägaren.
- Uppdragets tak var 10 dollar. Förbrukat: uppskattat 2–3 dollar på Modal över dagen.

## Kostnad
Modal: cirka 100 korta körningar och en varm container under kvällen, uppskattat 2–3 dollar. Codex: tre uppdrag på ägarens planer. Förståndet: bryggan till Google Cloud, bråkdelar av ett öre per anrop.
