# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (antagen). Objekt: 3, ankare: 5, avvisade observationer: 10.

| tagning | metod | skala | residual (m) | status |
|---|---|---|---|---|
| S1 | landmark | 1.0 | – | antagen |
| S2 | landmark | 1.0 | – | antagen |
| S3 | landmark | 1.0 | – | antagen |
| S4 | antagande | 1.0 | – | antagen |
| S5 | landmark | 1.0 | – | antagen |
| S6 | landmark | 1.0 | – | antagen |
| S7 | landmark | 1.0 | – | antagen |

| ankare | typ | position (m) | riktning (grad) | status |
|---|---|---|---|---|
| bordskant_A | bordskant | -0.01, 0.47, 0.87 | -88 | antagen |
| bordskant_B | bordskant | -0.03, 1.77, 0.79 | -72 | antagen |
| stol_A | sate | 0.00, 0.00, 0.00 | 90 | antagen |
| stol_B | sate | 0.00, 1.67, 0.00 | -90 | antagen |
| staplats_C | staplats | -1.56, 0.83, 0.00 | -11 | antagen |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvets cues och priorer finns i golv.matning. Konflikt över 10 cm flaggas; 1,45 m kamerahöjd är endast reserv. Ensam tagning behåller sitt tidigare golv tills --tillampa-golv väljs.
- Dialogaxel, motbildskamera vid motpartens huvud och stolsavstånd är scengrammatik (plats_matt.json d_grammatik), inte mätt.
- Deklarerat rum (plats/deklaration.json, deklaration/0.6): Rummet som tittaren uppfattar i S1–S6: A och B sitter mitt emot varandra vid ett gemensamt bord och grälar om notan. C står vid bordet och tittar på dem båda.

## Rumsmall

Mall: dekl_notan-tagningar. Rigid ankarrest RMS: 0.012 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: 
