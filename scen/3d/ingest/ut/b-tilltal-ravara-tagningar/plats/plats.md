# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (antagen). Objekt: 5, ankare: 1, avvisade observationer: 12.

| tagning | metod | skala | residual (m) | status |
|---|---|---|---|---|
| S1 | identitet | 1.0 | – | uppmatt |
| S2 | identitet | 1.0 | – | uppmatt |
| S3 | identitet | 1.0 | – | uppmatt |
| S4 | identitet | 1.0 | – | uppmatt |
| S5 | identitet | 1.0 | – | uppmatt |
| S6 | identitet | 1.0 | – | uppmatt |
| S7 | identitet | 1.0 | – | uppmatt |
| S8 | identitet | 1.0 | – | uppmatt |
| S9 | identitet | 1.0 | – | uppmatt |
| S10 | identitet | 1.0 | – | uppmatt |
| S11 | identitet | 1.0 | – | uppmatt |

| ankare | typ | position (m) | riktning (grad) | status |
|---|---|---|---|---|
| staplats_B | staplats | 0.06, 1.49, 0.00 | -116 | uppmatt |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvets cues och priorer finns i golv.matning. Konflikt över 10 cm flaggas; 1,45 m kamerahöjd är endast reserv. Ensam tagning behåller sitt tidigare golv tills --tillampa-golv väljs.
- Ingen scengrammatik kunde tillämpas: semantiken anger ingen dialogaxel mellan kolleger

## Rumsmall

Mall: bar_disk. Rigid ankarrest RMS: 0.000 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: 
