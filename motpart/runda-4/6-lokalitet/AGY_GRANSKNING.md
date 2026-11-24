# Uppdrag: oberoende visuell granskning av 0.0 (Gemini, via agy)

Du granskar en allmän 3D-ingest av korta 9:16-videoklipp. Arbetsmapp: `motpart/runda-4/6-lokalitet/` i repot. Det här är en oberoende kontroll. Du är inte ägaren, och din bedömning är ingen ägardom. Var konkret och kritisk; beröm behövs inte.

**Regler:**
- Läs bara de filer som anges nedan.
- Skriv bara till `ut/agy/` (skapa mappen).
- Installera inget, starta inga servrar, gör inga nätverksanrop.
- Ändra inga andra filer.
- Arbeta i högst cirka 20 minuter.

**Underlag per klipp** (`duepiani`, `spanjorskan`, `08burgerkebab`, `babasburgers`, `kennysgelato2.0`):
- `ut/<klipp>/qa/ruta-*.png` är en bild per tagning (mittrutan). Kolumnerna har rubriker: "Original" är videon. "A · ingest_v2" är en äldre ingest, endast som jämförelse. "B" finns bara för Due Piani och är handkartlagd. "L · lådlager" är den allmänna ingestens redigerbara lådor. "L · texturerade instanser" är den allmänna ingestens rum, där originalets pixlar ligger på 3D-bitar och kropparna är 3D-dockor.
- `ut/<klipp>/lokalitet.json` innehåller `tagningar.<id>.tillforlitlighet` (dom och signaler) och `lutning_grader`. Rutans nummer i filnamnet ligger inom tagningens `ut`-intervall i `ut/<klipp>/paket_L.json`.

**Bedöm per tagning, i kolumnen "L · texturerade instanser" mot "Original":**
1. **Kamera:** stämmer vinkel och utsnitt? Svara ja, delvis eller nej, med en mening.
2. **Rum:** ligger väggar, golv, bänkar, bord och spis där de syns i originalet? Saknas något viktigt eller finns något som inte finns? Svara ja, delvis eller nej.
3. **Personer:** stämmer dockornas antal, position, storlek och hållning med personerna i originalet? Svara ja, delvis eller nej, eller "ingen person".
4. **Föremål i händer och på bord** (tallrik, kartong, burk): ja, delvis eller nej.
5. **Det allvarligaste felet** i tagningen, i en mening. Skriv "inget tydligt" om inget finns.

**Leverans:** `ut/agy/GRANSKNING.md` med:
- En tabell med klipp, tagning, ruta, kamera, rum, personer, föremål, allvarligaste fel och L8-dom (ur lokalitet.json).
- Ett stycke om var din bild säger emot L8-domen. Gäller det fall där domen är "hög" men du ser tydliga fel, eller "låg" eller "konflikt" men det ser rätt ut? Lista tagningarna.
- Högst fem rader om de mest återkommande felen, ordnade efter hur mycket de hindrar att scenen används som utgångspunkt för iscensättning.
