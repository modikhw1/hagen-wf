# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (antagen). Objekt: 0, ankare: 0, avvisade observationer: 0.

| tagning | metod | skala | residual (m) | status |
|---|---|---|---|---|
| S1 | identitet | 1.0 | – | uppmatt |
| S2 | identitet | 1.0 | – | uppmatt |

| ankare | typ | position (m) | riktning (grad) | status |
|---|---|---|---|---|

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvets cues och priorer finns i golv.matning. Konflikt över 10 cm flaggas; 1,45 m kamerahöjd är endast reserv. Ensam tagning behåller sitt tidigare golv tills --tillampa-golv väljs.
- Ingen scengrammatik kunde tillämpas: semantiken anger ingen dialogaxel mellan kolleger
