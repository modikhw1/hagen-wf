# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (modellbedomd). Objekt: 5, ankare: 5, avvisade observationer: 13.

| tagning | metod | skala | residual (m) | status |
|---|---|---|---|---|
| S1 | landmark | 1.0 | – | antagen |
| S2 | landmark | 1.0 | – | antagen |
| S3 | matchning | 1.0 | 0.127 | uppmatt |
| S4 | antagande | 1.0 | – | antagen |
| S5 | landmark | 1.0 | – | antagen |
| S6 | matchning | 1.0 | 0.238 | uppmatt |
| S7 | landmark | 1.0 | – | antagen |

| ankare | typ | position (m) | riktning (grad) | status |
|---|---|---|---|---|
| bordskant_A | bordskant | 0.03, 0.13, 0.99 | -96 | antagen |
| bordskant_B | bordskant | 0.04, 2.28, 0.60 | 100 | antagen |
| stol_A | sate | 0.01, -0.03, 0.00 | 92 | antagen |
| stol_B | sate | 0.00, 2.48, 0.00 | -90 | antagen |
| staplats_C | staplats | -0.95, 0.55, 0.00 | 10 | antagen |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvets cues och priorer finns i golv.matning. Konflikt över 10 cm flaggas; 1,45 m kamerahöjd är endast reserv. Ensam tagning behåller sitt tidigare golv tills --tillampa-golv väljs.
- Dialogaxel, motbildskamera vid motpartens huvud och stolsavstånd är scengrammatik (plats_matt.json d_grammatik), inte mätt.
- S7 visar B vid ett eget bord med en tydlig bortre bordskant, ben och stolar. A:s bord med gul Bonaqua-burk och matpapper ligger i förgrunden; mellan borden finns en passage och stolar. S1 har burk och stor vit mugg; S2 har en annan mugg, pommeskartong och såskopp, ingen burk. Inga axlar eller händer från motparten förenar motbilderna. S4 visar servitören i en gång med andra gäster vid separata bord men knyter inte ihop A och B geometriskt. Två bord är därför den starkaste tolkningen. Avstånd 2,48 m är antaget, avrundat från den tidigare skattningen 2,476 m; inte en oberoende mätning. Att addera kameraavstånd är inte generellt giltigt för motbilder.

## Rumsmall

Mall: notan_tva_bord. Rigid ankarrest RMS: 0.076 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: okand_s4_4: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd.
