# Motprov 3–4: oberoende bildlinjer och spridningsdiagnos

Kör från `6-lokalitet/`, ett kommando åt gången:

```powershell
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py frames
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py duepiani
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py spanjorskan
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py 08burgerkebab
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py babasburgers
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py kennysgelato2.0
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py --selftest
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/diagnosis_injection.py
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/report.py
```

Alla 114 nyckelrutor hämtades ur originalvideorna i `data/format/kontroll/klipp/` enligt `obs_gpu.json`. Videornas SHA256 kontrollerades mot metadata. Originalbilderna ligger i `frames/`; linjer och accepterade inliers visas i `vp-images/` och kontaktkartorna nedan. Samtliga kontaktkartor granskades visuellt.

OpenCV LSD hittar raka segment. Manuellt valda bildregioner begränsar urvalet till synliga vertikaler, framför allt väggar, fönster, dörrar, skåp och upprätta föremål. Regionen och varje segments pixelkoordinater sparas i `vp-<klipp>.json` och i skriptet. Detta är ett manuellt granskat motprov, inte ett nytt autonomt ingestlöfte. Varken `lutning_grader`, MoGe-normaler, GeoCalib-gravitation, kroppsbål eller rapportens ”cirka −25°” används i anpassningen. Målutdata läses separat för jämförelsen.

Geometrin: segmentets mittpunkt `(x,y)` normaliseras med kamerans fokal; dess bildlutning `a=dx/dy` ger ekvationen `u_x + (a*y-x)*u_z = -a` med `u_y=-1`. Robust linjekonsensus följs av vinkelanpassning; `pitch=asin(u_z/||u||)`, negativt nedåt. Flyktpunkter i oändligheten kan representeras. Fokalen tas ur `lins_mm.anvand`, med samma virtuella 36 mm-sensor som systemet; vittnet är därför oberoende av gravitationsskattningen men **villkorat på dess intrinsik**, inte en oberoende objektivkalibrering. Huvudpunkt i bildcentrum, kvadratiska pixlar och försumbar linsdistorsion antas. Fokalen varieras även ±20 % i råresultaten och tabellen.

Grindar: längd minst 40 px (25 px för korta kakelfogar i Due Piani S9/S11/S12), riktning inom 35° från bildvertikalen, dublettkanter inom 6 px/0,5° samlas, inlierfel <0,8°, minst fem inlierlinjer över minst 25 % av bildbredden. Bootstrap med 150 återdragningar får ha högst 10° brett 95 %-intervall. Frön är fasta (829 och 54). Tagningens siffra är medianen av minst två godkända rutor; en enda ruta räcker inte. Bootstrap gäller slumpvariation hos linjerna och täcker inte systematiskt fel eller felmärkt linjefamilj.

Visuell prövning underkände babasburgers S10:s numeriskt starka positiva VP: inliers satt på lutande stolsben, kläder och skärmar. S11 saknar också tillräckliga säkra vertikaler. Råhypoteserna finns kvar men räknas inte som kamerafel. Matnärbildernas bordskanter, avsmalnande kärl och enstaka burkar får inte ersätta ett saknat vertikalvittne. Due Piani S9 är tvetydig: 25/40 px linjelängd ger −13,3/−4,5° i ruta 399 och −14,7/−6,7° i ruta 416. Endast ruta 433 återstår; inget tagningsvärde godtas. Ändringar efter bildgranskning gäller vittnets linjeurval, aldrig ingestens utdata.

Kameran rör sig dessutom i flera intervall som ingesten kallar statiska: tydlig taksvepning i 08burgerkebab S8 ruta 513, bordsvy i Spanjorskan S1 ruta 165 och kraftigt annan vy i kennysgelato S1 ruta 412. Dessa rutor saknar här godkänd VP; tagningarnas median är inte en verifiering av hela intervallet.

Utfall: **24/38 tagningar mätbara, 14 saknar tillräckligt vittne. Inga accepterade tagningsmedianer eller enskilda accepterade rutor avviker över 10°.** Median absolutavvikelse 1.8°, största 7.6° (Due Piani S7). De 14 luckorna är inte godkända vinklar.

| Klipp/tagning | Rutor | Ingest ° | VP ° per godkänd ruta | VP-median ° | Absolut avvikelse ° | Median med fokal −20/+20 % | Saknat/anmärkning |
|---|---|---:|---|---:|---:|---|---|
| duepiani S1 | 2, 31, 59 | -8.7 | 2: -7.2, 31: -8.7, 59: -7.8 | -7.8 | 0.9 | -6.2/-9.3 |  |
| duepiani S2 | 64, 83, 102 | -60.7 | saknas | — | — | — | Tallriksnärbild: inga spridda, säkert vertikala byggnadslinjer. |
| duepiani S3 | 107, 119, 131 | -8.4 | 107: -7.4, 119: -8.3, 131: -8.3 | -8.3 | 0.1 | -6.6/-9.9 |  |
| duepiani S4 | 136, 162, 188 | -7.1 | 136: -4.5, 162: -5.1, 188: -3.9 | -4.5 | 2.6 | -3.6/-5.4 |  |
| duepiani S5 | 193, 211, 229 | -9.5 | 193: -2.1, 211: -5.8, 229: -3.6 | -3.6 | 5.9 | -2.8/-4.3 |  |
| duepiani S6 | 234, 270, 306 | -9.5 | 234: -5.1, 270: -6.1, 306: -7.3 | -6.1 | 3.4 | -4.9/-7.4 |  |
| duepiani S7 | 311, 342, 372 | -7.7 | 311: -0.1, 342: 1.4, 372: -3.4 | -0.1 | 7.6 | -0.1/-0.1 |  |
| duepiani S8 | 377, 386, 394 | -51.0 | saknas | — | — | — | Panna ovanifrån: inga säkra vertikala linjer. |
| duepiani S9 | 399, 416, 433 | -12.2 | 433: -4.6 | — | — | — | Endast en robust ruta; VP-kandidater parameterkänsliga. |
| duepiani S10 | 438, 449, 460 | -51.9 | saknas | — | — | — | Mat/panna ovanifrån: inga säkra vertikala linjer. |
| duepiani S11 | 465, 491, 517 | -12.5 | 465: -15.2, 491: -16.0, 517: -14.3 | -15.2 | 2.7 | -12.3/-18.1 |  |
| duepiani S12 | 522, 551, 580 | -9.3 | 522: -9.9, 551: -11.0, 580: -10.9 | -10.9 | 1.6 | -8.8/-13.1 |  |
| spanjorskan S1 | 2, 84, 165 | -14.7 | 2: -8.3, 84: -11.7 | -10.0 | 4.7 | -8.0/-11.9 | Ruta 165: bordsnärbild, VP saknas. |
| spanjorskan S2 | 170, 261, 352 | -73.2 | saknas | — | — | — | Bordsnärbild ovanifrån: bordskanter är inte lodlinjer. |
| spanjorskan S3 | 357, 383, 408 | -13.3 | 357: -11.6, 383: -14.2, 408: -11.5 | -11.6 | 1.7 | -9.3/-13.9 |  |
| 08burgerkebab S1 | 2, 32, 62 | -15.4 | 2: -10.8, 32: -13.3, 62: -13.1 | -13.1 | 2.3 | -10.5/-15.6 |  |
| 08burgerkebab S2 | 67, 91, 114 | -13.9 | 67: -5.1, 91: -16.0, 114: -15.3 | -15.3 | 1.4 | -12.3/-18.2 |  |
| 08burgerkebab S3 | 119, 137, 155 | -17.8 | 119: -24.3, 137: -15.3, 155: -19.3 | -19.3 | 1.5 | -15.6/-22.8 |  |
| 08burgerkebab S4 | 160, 194, 227 | -10.7 | 160: -10.2, 194: -7.3, 227: -8.6 | -8.6 | 2.1 | -6.9/-10.3 |  |
| 08burgerkebab S5 | 232, 246, 260 | -11.3 | 232: -8.6, 246: -8.5, 260: -8.5 | -8.5 | 2.8 | -6.8/-10.1 |  |
| 08burgerkebab S6 | 265, 302, 338 | -11.0 | 265: -6.5, 302: -9.2, 338: -9.4 | -9.2 | 1.8 | -7.4/-11.0 |  |
| 08burgerkebab S7 | 343, 399, 455 | -8.2 | 343: -10.3, 399: -9.9, 455: -9.4 | -9.9 | 1.7 | -8.0/-11.8 |  |
| 08burgerkebab S8 | 460, 513, 565 | -15.4 | 460: -17.0, 565: -11.7 | -14.3 | 1.1 | -11.6/-17.0 | Ruta 513: taksvep, VP saknas. |
| 08burgerkebab S9 | 570, 580, 590 | -64.9 | saknas | — | — | — | Maträtt ovanifrån: inga säkra vertikala linjer. |
| 08burgerkebab S10 | 595, 613, 630 | -14.0 | 595: -9.2, 613: -12.3, 630: -11.6 | -11.6 | 2.4 | -9.4/-13.9 |  |
| 08burgerkebab S11 | 635, 658, 680 | -10.6 | 635: -10.1, 658: -10.8, 680: -10.8 | -10.8 | 0.2 | -8.7/-12.9 |  |
| babasburgers S1 | 2, 47, 92 | -13.3 | 2: -12.7, 47: -14.4, 92: -14.4 | -14.4 | 1.1 | -11.6/-17.2 |  |
| babasburgers S2 | 97, 120, 143 | -32.4 | saknas | — | — | — | Bords-/matnärbild: för få säkra, separerade vertikaler; burk, koniskt kärl och stolsben räcker inte. |
| babasburgers S3 | 148, 167, 186 | -52.6 | saknas | — | — | — | Bords-/matnärbild: för få säkra, separerade vertikaler; burk, koniskt kärl och stolsben räcker inte. |
| babasburgers S4 | 191, 207, 222 | -58.0 | saknas | — | — | — | Bords-/matnärbild: för få säkra, separerade vertikaler; burk, koniskt kärl och stolsben räcker inte. |
| babasburgers S5 | 227, 256, 285 | -14.0 | 227: -15.2, 256: -14.8, 285: -16.6 | -15.2 | 1.2 | -12.3/-18.1 |  |
| babasburgers S6 | 290, 322, 354 | -36.7 | saknas | — | — | — | Bords-/matnärbild: för få säkra, separerade vertikaler; burk, koniskt kärl och stolsben räcker inte. |
| babasburgers S7 | 359, 387, 414 | -50.0 | saknas | — | — | — | Bords-/matnärbild: för få säkra, separerade vertikaler; burk, koniskt kärl och stolsben räcker inte. |
| babasburgers S8 | 419, 451, 482 | -15.4 | 419: -15.0, 451: -13.7, 482: -18.2 | -15.0 | 0.4 | -12.1/-17.9 |  |
| babasburgers S9 | 487, 506, 524 | -59.1 | saknas | — | — | — | Bords-/matnärbild: för få säkra, separerade vertikaler; burk, koniskt kärl och stolsben räcker inte. |
| babasburgers S10 | 529, 608, 687 | -18.4 | saknas | — | — | — | Visuell kontroll: LSD-konsensus på lutande stolsben, kläder eller koniska lampskärmar. För få säkra vertikaler. |
| babasburgers S11 | 692, 760, 828 | -10.5 | saknas | — | — | — | Visuell kontroll: LSD-konsensus på lutande stolsben, kläder eller koniska lampskärmar. För få säkra vertikaler. |
| kennysgelato2.0 S1 | 2, 207, 412 | -23.0 | 2: -28.2, 207: -24.7 | -26.4 | 3.4 | -21.7/-30.8 | Ruta 412: ändrad vy, VP saknas. |

**Diagnosen:** `lokalitet.py:721–726` mäter vinkeln mellan varje rutas MoGe-lod och den gemensamma MoGe-loden, före fusion. Listan är inte standardavvikelsen hos slutlig `lutning_grader`. Saknade per-rutelodlinjer utelämnas dessutom; listans index är därför inte alltid ett frame-id. `fusera_lodlinje`, rader 407–432, använder medianen, minst 3°, som MoGe-σ.

| Verkligt exempel | spridning_per_ruta_grader | Median/max ° | Avvikelse mot VP ° | Vad exemplet visar |
|---|---|---|---:|---|
| duepiani S3 | [0.4, 0.4, 0.1] | 0.4/0.4 | 0.1 | Båda små. |
| duepiani S1 | [1.0, 0.6, 89.4] | 1.0/89.4 | 0.9 | Maxspridning mycket stor, slutvinkelfelet litet. |
| spanjorskan S1 | [8.5, 9.0, 9.9] | 9.0/9.9 | 4.7 | Medianspridning stor, slutvinkelfelet under 10°. |
| 08burgerkebab S8 | [1.0, 72.3, 1.9] | 1.9/72.3 | 1.1 | Stor maxspridning sammanfaller med verklig kamerarörelse; mittvittnet saknas. |
| duepiani S7 | [0.6, 0.3, 0.8] | 0.6/0.8 | 7.6 | Liten spridning trots störst uppmätt tagningsavvikelse. |

Något belagt exempel där både stor spridning och ett VP-fel >10° föreligger finns **inte** i denna ögonblicksbild. Babasburgers S6 har [68,5; 92,1; 0,1]° men saknar VP, så dess fel kan inte anges. Rapportens äldre babasburgers S1 med −46° och 32–34° spridning beskriver tidigare tagningsgränser; aktuella utdata är −13,3° och [0,8; 0,3; 0,7]°. Det gamla exemplet kan inte användas som aktuellt testresultat.

I de 24 mätbara tagningarna är Spearman ρ=0.249 (p=0.240) för medianspridning och ρ=0.276 (p=0.191) för maxspridning mot absolut slutvinkelfel. Inget tillförlitligt samband beläggs här; urvalet saknar de svåra närbilderna och är inte ett kalibreringsmaterial. En svag positiv korrelation ska inte beskrivas som bevis för att inget samband kan finnas.

**Körbar falsifiering:** `diagnosis_injection.py` exekverar de oförändrade funktionerna `dominant_axel` och `lodlinje` från AST:n och injicerar samma 30° normalbias i tre syntetiska rutor. Rätt lod har spridning [0;0;0]° och fel 0°; fel lod har också [0;0;0]° men fel 30°. Därmed faller spridning som ensam absolut tillförlitlighetsgaranti. Testet prövar MoGe-diagnosen; fusion med ett annat vittne kan fortfarande korrigera biasen. Se [diagnosis-injection.json](diagnosis-injection.json).

Vittnets egen geometrikontroll passerade för kända vinklar −50°, −15°, 0° och +15° (inklusive flyktpunkt i oändligheten). En injicerad avvikelse 15° utlöste jämförelsegrinden >10°: [vp-selftest.json](vp-selftest.json). Kontrollen kalibrerar inte verkliga kamerors fokal eller linsdistorsion.

Bildbevis, tre nyckelrutor per rad:

- duepiani: [vp-duepiani-1](vp-duepiani-1.jpg), [vp-duepiani-2](vp-duepiani-2.jpg), [vp-duepiani-3](vp-duepiani-3.jpg)
- spanjorskan: [vp-spanjorskan-1](vp-spanjorskan-1.jpg)
- 08burgerkebab: [vp-08burgerkebab-1](vp-08burgerkebab-1.jpg), [vp-08burgerkebab-2](vp-08burgerkebab-2.jpg), [vp-08burgerkebab-3](vp-08burgerkebab-3.jpg)
- babasburgers: [vp-babasburgers-1](vp-babasburgers-1.jpg), [vp-babasburgers-2](vp-babasburgers-2.jpg), [vp-babasburgers-3](vp-babasburgers-3.jpg)
- kennysgelato2.0: [vp-kennysgelato2.0-1](vp-kennysgelato2.0-1.jpg)

Alla 114 rutor och avslagsorsaker: [RUTOR.csv](RUTOR.csv). Exakta pixelkoordinater, inliers, bootstrapintervall och fokalkänslighet: `vp-<klipp>.json`.
