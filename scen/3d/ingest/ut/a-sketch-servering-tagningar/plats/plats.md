# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (antagen). Objekt: 2, ankare: 0, avvisade observationer: 17.

| tagning | metod | skala | residual (m) | status |
|---|---|---|---|---|
| S1 | landmark | 1.0 | – | antagen |
| S2 | landmark | 1.0 | – | antagen |
| S3 | landmark | 1.0 | – | antagen |
| S4 | landmark | 1.0 | – | antagen |
| S5 | landmark | 1.0 | – | antagen |
| S6 | antagande | 1.0 | – | antagen |
| S7 | landmark | 1.0 | – | antagen |

| ankare | typ | position (m) | riktning (grad) | status |
|---|---|---|---|---|

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvets cues och priorer finns i golv.matning. Konflikt över 10 cm flaggas; 1,45 m kamerahöjd är endast reserv. Ensam tagning behåller sitt tidigare golv tills --tillampa-golv väljs.
- Dialogaxel, motbildskamera vid motpartens huvud och stolsavstånd är scengrammatik (plats_matt.json d_grammatik), inte mätt.
