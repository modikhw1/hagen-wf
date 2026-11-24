---
id: 0009
titel: Fokal per klipp med redovisad källa, och tre småfel ur svaren 0004 och 0007
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0004
tillåten_skrivning: [scen/3d/ingest/regler.py, scen/3d/ingest/ingest_klipp.py, scen/3d/ingest/fokal_klipp.py, scen/3d/ingest/deklaration_till_hand.py, scen/3d/ingest/test_deklaration.py, scen/3d/kontrakt/kompilera.py, scen/3d/kontrakt/test_snabb.py, scen/3d/kontrakt/ut/fore_fokal_0009/, scen/3d/LOGG.md]
---

## Mål
Brännvidden är ett värde per klipp med redovisad källa och status hela vägen till `plan.json`, och S5 i `b-tilltal-ravara` läses inte längre med en fokal som avviker en faktor 2,3 från resten av klippet.

## Bakgrund
`delegat/svar/0004-lins-och-kameradjup-per-tagning.md`: datavägen med fil och rad, och förslaget på rättning. `delegat/svar/0007-ratta-passningen-efter-regelandring.md`, Avvikelser: dubbla `disk_A` och bruten stödkedja för `kottbit`.

Kör efter 0003, 0006 och 0008 om de ligger före i kön. De bygger på dagens planer, och det här uppdraget ändrar ingen befintlig ut-mapp.

## Att göra
1. **Fokal per klipp.** Ny modul `ingest/fokal_klipp.py`: samlar tagningarnas kandidater (COLMAP rå, försvinningspunkter enligt `kontrakt/ut/diag_0004/vp.py`) och ger ett värde för klippet med spridning. En tagnings COLMAP-värde godtas bara om det ligger inom klippets spridning. Saknas allt gäller `max(bredd, höjd)` som i dag, märkt `antagen`.
2. **Redovisning.** `fokal_px`, `fokal_status` (`matt`/`skattad`/`antagen`) och `fokal_kalla` per tagning förs till `plan.json` under `kvalitet.kamerakalibrering`, som i dag är tom.
3. **Rörlig zoom.** Klipp där tagningar faktiskt har olika zoom ska inte tvingas till ett värde. Avvikelsen ska då bäras av en oberoende andra källa i samma tagning. Finns ingen: klippets värde, och avvikelsen loggas.
4. **Dubbla id.** Hitta varför planen `n06-fler` får två byggobjekt `disk_A` och rätta orsaken. Lägg ett prov som kräver unika id.
5. **Stödkedjan för `kottbit`.** Föremål vars stöd inte byggs (inslagspapper) ska få ersättningsstöd redan i `deklaration_till_hand.py`, så att rättningen i `foremallyft.py` (0007) får något att arbeta med.

## Gränser
- Bara filerna i `tillåten_skrivning`. Baslinje först: kopiera berörda filer till `scen/3d/kontrakt/ut/fore_fokal_0009/kod/`.
- **Ingen ny ingest i det här uppdraget.** Att läsa om S5 med ny fokal kräver SAM 3D Body på Modal och ändrar kroppsdata som allt nedströms bygger på. Visa i stället, på minneskopia, vilket fokalvärde varje tagning i de fyra klippen (b-tilltal, guacamole, notan, gelato) skulle få och vilka tagningar som då behöver läsas om. Omläsningen blir ett eget uppdrag.
- Ändra inget medan ett test eller en kompilering kör. Verifiera med tom cache.
- Egna trösklar är diagnos och inte krav. Redovisa dem.

## Klart när
- Snabbtesterna och ingesttesterna är gröna, med antal, inklusive nya prov för punkterna 1, 4 och 5.
- En tabell per klipp: tagning, fokal i dag, fokal enligt nya regeln, status, källa, och om tagningen behöver läsas om.
- Planer för klipp där inget fokalvärde ändras är byteidentiska före och efter, bortsett från det nya fältet `kamerakalibrering`. Visa det på minneskopia.
- Ett avsnitt i `scen/3d/LOGG.md`.

## Leveransform
`delegat/svar/0009-fokal-per-klipp-och-smafel.md` enligt mallen, högst cirka 50 rader.
