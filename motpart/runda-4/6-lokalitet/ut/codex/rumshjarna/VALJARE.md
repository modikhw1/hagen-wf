Alla fem klipp är omkörda utan GPU-anrop och har samma kod-SHA.

Måttet kräver **alla identifierbara instanser i ”viktigast”**, med samma dokumenterade instansnyckel före och efter. Det är striktare än rapportens kärnmeningsbedömning på 18/38.

| Klipp | Före | Efter |
|---|---:|---:|
| duepiani | 0/12 (0 %) | 11/12 (91,7 %) |
| spanjorskan | 0/3 (0 %) | 2/3 (66,7 %) |
| 08burgerkebab | 1/11 (9,1 %) | 7/11 (63,6 %) |
| babasburgers | 4/11 (36,4 %) | 7/11 (63,6 %) |
| kennysgelato2.0 | 0/1 (0 %) | 0/1 (0 %) |
| **Totalt** | **5/38 (13,2 %)** | **27/38 (71,1 %)** |

`duepiani s8` saknar meningsfulla motivinstanser och räknas som miss. Bland enbart mätbara tagningar blir efterresultatet **27/37 (73,0 %)**.

Ändringarna i `valjare.py`, med generella skäl kommenterade i koden:

- Kopplar 2D- och 3D-händer till valda huvudpersoner utifrån yta, djup och projektion.
- Mäter storlek robust med 5–95-percentiler och tillåter stora handobjekt vid starkt 2D-stöd.
- Höjer bildstorlekens mättnad till 40 %, halverar skärpevikten och dämpar små segments skärpeutslag.
- Jämför stödobjekt utan handpoäng, dämpar etikettupprepningar och inför areagolv per roll. Dekor kan inte ensam bära platsmarkören.
- Upptäcker grafik konservativt med rektangelform, befintlig OCR och grannrutor. Sedeln hamnar i `overlagg`.

Budgeten är nu högst sex objekt och tre kompletterande rumsankare. Genomsnittsurvalet ökade från **3,63 till 5,16 instanser**. Rollgränser, personkoppling, SHA och grafikdetektorns positiva/negativa fall är kontrollerade.

Mätskriptet är `rumshjarna/valjare_matt.py`. Återskapa jämförelsen med:

```powershell
.venv/Scripts/python.exe -I -X utf8 rumshjarna/valjare_matt.py --jamfor fore
```

Vissa befintliga instanser väljs fortfarande bort, exempelvis Kennys dörr och små brickdelar. Mat, redskap och skyltar som OneFormer slukat i `wall`/`person` kan inte återställas som egna objekt utan ny segmenteringssignal. Grepp kontra pekning och okända grafiköverlägg är fortsatt osäkra.

KLAR