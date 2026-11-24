# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (antagen). Objekt: 0, ankare: 2, avvisade observationer: 3.

| tagning | metod | skala | residual (m) | status |
|---|---|---|---|---|
| S1 | landmark | 1.0 | – | antagen |
| S2 | landmark | 1.0 | – | antagen |
| S3 | landmark | 1.0 | – | antagen |
| S4 | landmark | 1.0 | – | antagen |

| ankare | typ | position (m) | riktning (grad) | status |
|---|---|---|---|---|
| stol_A | sate | -0.51, 0.01, 0.00 | 70 | antagen |
| staplats_B | staplats | 0.00, 1.30, 0.00 | -90 | antagen |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvets cues och priorer finns i golv.matning. Konflikt över 10 cm flaggas; 1,45 m kamerahöjd är endast reserv. Ensam tagning behåller sitt tidigare golv tills --tillampa-golv väljs.
- Dialogaxel, motbildskamera vid motpartens huvud och stolsavstånd är scengrammatik (plats_matt.json d_grammatik), inte mätt.
- Deklarerat rum (plats/deklaration.json, deklaration/0.6): Kund A sitter vid en bardisk, personal B står mitt emot. De missförstår frågan om guacamole och tillbehör. S4 visar båda i samma rum; inget rumsligt avslöjande som i notan.

## Rumsmall

Mall: dekl_e-dialog-guacamole-tagningar. Rigid ankarrest RMS: 0.176 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: 
