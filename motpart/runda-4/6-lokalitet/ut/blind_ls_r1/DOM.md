# Blind parvis bedömning: 3D-rekonstruktioner (54 tagningar)

## Resultat per kategori (antal X / Y / lika)

| Kategori | X | Y | lika | Totalt |
|---|---:|---:|---:|---:|
| Från originalkameran (`original`) | 25 | 28 | 1 | 54 |
| Rummet vid vridning (`rum`) | 20 | 28 | 6 | 54 |
| Föremålen vid vridning (`foremal`) | 3 | 6 | 45 | 54 |
| Helhet för att regissera om (`helhet`) | 18 | 29 | 7 | 54 |

## God nog som utgångspunkt (`ja` / `delvis` / `nej`)

| Variant | ja | delvis | nej | Totalt |
|---|---:|---:|---:|---:|
| X (`god_nog_X`) | 0 | 17 | 37 | 54 |
| Y (`god_nog_Y`) | 0 | 19 | 35 | 54 |

Parvis: 36 tagningar har exakt en `delvis` (17 X, 19 Y), 18 har `nej` för båda, 0 når `ja`.

## Vanligaste fel i X och Y

Eftersom X och Y är slumpade per tagning uppträder två tydliga, återkommande felprofiler i både X och Y (i 38 av 54 tagningar vinner den ena `original` och den andra `helhet`):

- **Originaltrogen men trasig vid vridning (oftast den sämre i helhet):**
  - Stora taggiga hål rakt genom väggar, bänkar, bord och golv vid 35°/50°.
  - Rum, tak, stolar och mat spricker i papperstunna svävande skärvor och krökta remsor utan golv.
  - Kvarvarande rester av borttagna personer (hår, ansikte, kläder) och överlagrad text som vrids ut i 3D.
- **Rumstabil/plan men grov och destruktiv i detaljer (oftast den bättre i helhet):**
  - Stora enfärgade polygonblock och sågtandade utfyllnader redan i 0°-vyn som täcker fläktar, skyltar, lampor och mat.
  - Mat, tallrikar och kärl raderas helt, plattas ut till 2D-klistermärken på bord/golv eller blir grova klossar/cylindrar.
  - Kollapsar helt i matnärbilder och mörka scener (där stora täckande block slukar motivet; här vinner ibland den andra, t.ex. `duepiani/s8`, `duepiani/s10`, `08burgerkebab/s7`, `babasburgers/s6`, `fratelli/s5`, men båda är ändå `nej`).

## Vad den bättre fortfarande gör fel

Även i de 36 tagningar som når `delvis` räcker den vinnande rekonstruktionen inte till `ja` för omregissering:

1. **Föremålen fallerar nästan alltid:** 45/54 är `lika` (oftast lika dåliga). Tallrikar, matlådor, glas, pizzor och flaskor försvinner, blir platta 2D-projektioner på bords-/golvytan eller ersätts av grova cylindrar (ibland direkt på golvet eller med text påklistrad).
2. **Enfärgade utfyllnadsblock förstör 0°-vyn och baksidor:** Stora bruna/grå/beige polygonlappar kapar lampor, skyltar, bänkfronter och förgrundsmat.
3. **Saknade rumselement och skarvar:** Sidoväggar, stolar, förgrundsbord, dörrkarmar och bänkpartier saknas ofta i 35°/50°, med mörka glapp i hörn, flerskiktade väggskivor eller tomma enfärgade golvytor.
4. **Matnärbilder och svaga källrutor saknar 3D-grund:** När scenen saknar tydliga rumsplan (närbilder på pasta/burgare eller mörker/oskärpa) faller även den bättre ihop till oanvändbara block eller skärvor.
