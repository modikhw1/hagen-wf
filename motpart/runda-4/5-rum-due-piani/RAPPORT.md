# Prov 02: Due Piani, rum och kamera (A/B)

21 november 2026. Agentens tekniska och visuella granskning. **Ingen ägardom på B ännu.**

## Visning

`http://127.0.0.1:5205`: original | A (fryst) | B (bildstöd, utan image-gen). Samma kroppsspår, ljud, tidsbas och renderare. Alla 12 tagningar spelas. Knapparna för S2/S8/S10 är markerade och S1 är kontroll. Bedömningar sparas ordagrant per variant i `ut/svar.jsonl`. Panelen på 5204 är orörd.

Start från repots rot:

    .\scen\.venv\Scripts\python.exe -I -X utf8 motpart\runda-4\5-rum-due-piani\server.py --port 5205

## Ägarens ord (ordagrant, ur AGARFEEDBACK_DUE_PIANI_2026-11-21.md)

> Det verkar synroniserat till personen i rörelser, helt ok. Det den inte klarar lika bra är unika/udda vinklar, rum i bakgrunden och allmän inpaketering i lokal (dvs bänk, spis, storlek av rätten och annat). […] Scener som är konstiga är s2, s8 är en stiliserad inzooming av något som inte zoomar i videon. s10 har ingen anpassad shot för inzooming där heller.

## Diagnos (belagd)

| Fel i A | Belägg |
|---|---|
| Falsk inzoomning | Bildmätning (`kamera_matning.py`, OpenCV): skala första→sista ruta är 0,99–1,03 i S3–S12 och 0,92/0,90 i S1/S2, alltså ingen inzoomning i originalet. A lägger ändå in 0,14 m framåtåkning i 11 av 12 tagningar och 0,22 m + 4 cm sänkning i S8. Källan är schablonen i `modal_ingest_v2.py` cirka rad 873–891. |
| Flacka vinklar | Lodlinjen klampas till högst 18° (`modal_ingest_v2.py` cirka rad 520–524). S2 och S8 ligger exakt på gränsen, men originalet tittar 45–70° ned. |
| Kroppen för högt i bild | Mot oberoende 2D-led (yolo11n-pose) ligger A:s kroppar 60–145 px för högt i alla helbilder. Ingesten flyttar kroppen till golvet efter kamerakartläggningen men flyttar inte kameran med. |
| Påhittade stöd | `bord_1` syns i hela klippet och kommer från handled/bål. `bord_s8` skapas när inga spår finns. Inget av dem syns i originalet. |
| Dubbletter | S2 har fyra spår (A, C, D, E) av samma kvinna, lutade 14–28°. |

## Vad B ändrade (regler B1–B6 i `bygg_b.py`, recept per tagning i `ut/recept_B.json`)

- **B1:** Kameran står still i varje tagning. Kropparna skattades per ruta i kamerans egna koordinater, så verklig kamerarörelse finns redan i motivets rörelse.
- **B2:** Kamerapositionen registreras mot 2D-led med kroppsspåren orörda. Median-felet sjunker från 100–149 px till **16–22 px** i S1, S3–S7, S9, S11 och S12. S2 går från 221 till 51 px.
- **B3:** Lodlinjen ges av bildstöd där A låg på klampgränsen eller där en rätt vilar på en yta. S8: pannans ellips ger 72° nedåt på 0,54 m. S10: tallrikens ellips ger 41° på 0,52 m. S2: bålen rätas upp, vilket ger 46°. Kropp och kamera roteras tillsammans, så projektionen bevaras. Testet visar under 1 px avvikelse i S10.
- **B4:** S2 behåller spår C, det med lägst 2D-fel. A, D och E tas bort ur S2. A-paketet är orört.
- **B5:** `bord_1` och `bord_s8` tas bort. En spis (S8) och en bänk (S10) läggs in där bilden visar dem, i cyan eftersom höjd och mått (0,90 m) är antagna.
- **B6:** Tallriken följer händerna i S1/S3/S11 och följer ellipsen per nyckelruta i S2. A:s schablonskålar i S4–S7, S9 och S12 märks `harledd_mall` (cyan) i stället för `observerad`.

## Rutor (original | A | B), granskade av agenten

- `ut/qa/ark-000.jpg`, **S1:** A har ett bord som döljer underkroppen. B har inget bord, kvinnan står hel och håller tallriken i midjehöjd som i originalet.
- `ut/qa/ark-062.jpg`, **S2:** A visar ett stort huvud, ett bord och ingen tallrik. B tittar ned på tallriken, som fyller bilden, med armarna mot kanten. Kroppen sitter något åt höger, vilket ger 51 px restfel.
- `ut/qa/ark-375.jpg`, **S8:** A visar en flack sidovy av en skål som zoomar in. B tittar ned i pannan och står still, som originalet.
- `ut/qa/ark-436.jpg`, **S10:** A visar ett tomt bord och en kropp utanför bild. B visar tallriken uppifrån på bänken, den antagna pannan (cyan) som korsar tallriken upptill, och armen i övre högra hörnet.

## Fortfarande fel eller ej gjort

- **Rum i bakgrunden saknas.** Det gäller entréns fasad/dörr (S1/S3), kakelvägg, spis och fläkt i köket (S4–S7, S9) samt bänkar (S11/S12). B tar bort falska stöd men lägger inte till de verkliga. Det kräver djup per tagning (MoGe), som saknas lokalt.
- I S8 saknas handen och skeden. Hela kroppen i S10 är bara en hand i originalet, och resten av kroppen är oprövad.
- Kartläggningen av ellipserna i S2/S8/S10 är **manuell** (49 punkter, 5 nyckelrutor). Det automatiska försöket (YOLO-World + SAM2 på CPU) förväxlade tallrik och panna och fastnade på skor. Pannan i S10 är manuellt iscensatt. Allt redovisas i `recept_B.json → manuella_inslag`.
- Antagna storheter: tallrik 0,30 m, panna 0,34 m, bänkhöjd 0,90 m. Tagningarna har fortfarande var sitt rum med gemensamt origo, och ingen rumslig kontinuitet mellan S4–S9 har prövats.
- Ingen ägarbedömning ännu. Kamerarörelse som finns i originalet (S1 drar ut cirka 8 %) återges som motivrörelse, inte som kamerarörelse.

## Image-gen (C)

Inte körd. Felen i S2/S8/S10 berodde på regler (klamp, schablonåkning, golvflytt, påhittade bord), inte på brist på karta. B rättade dem utan generering. Där en karta skulle kunna hjälpa är det enda manuella ledet, ellipserna. Ett bättre segmenteringsverktyg kan göra samma jobb, men det är inte prövat. Möjligt prov: tre genererade kartrutor (83, 386, 462), automatisk ellips ur kartan, jämfört med den manuella. Det kostar krediter och väntar på ägarens ja.

## Tid och kostnad (uppmätt lokalt, CPU)

Bildmätning 29 s · 2D-pose 583 rutor 124 s · bygg B 3,9 s · bildfångst 12 rutor 12 s. Extern kostnad **0 USD**, ingen Modal/GPU/image-gen. Manuell kartläggning och felsökning: agenttid, ej klockad.

## Hashar

A `4eae657a2c45…` (orörd, testad) · B `a474090a975b…` · recept, kod och indata i `ut/recept_B.json`. Kontrakt: `test_bevarande.py`, som passerar med 8 kontroller.

## Nästa beslut som utfallet stöder

1. Om ägaren ser B som närmare: för in B1, B2 och B5 i ingesten. De är allmänna och kräver ingen manuell input. Klampen och schablonåkningen tas bort.
2. Därefter rum i bakgrunden: djup per tagning (MoGe på Modal, eller lokalt på CPU), som ger väggar, spis och bänk med osäkerhet.
3. Gör ellipskartläggningen automatisk. Pröva en segmenterare med punktprompt före image-gen.
