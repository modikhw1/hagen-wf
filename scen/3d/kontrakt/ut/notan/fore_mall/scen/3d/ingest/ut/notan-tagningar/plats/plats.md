# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (uppmatt). Objekt: 5, ankare: 5, avvisade observationer: 11.

| tagning | metod | skala | residual (m) | status |
|---|---|---|---|---|
| S1 | landmark | 1.0 | – | antagen |
| S2 | landmark | 1.0 | – | antagen |
| S3 | matchning | 1.0 | 0.126 | uppmatt |
| S4 | antagande | 1.0 | – | antagen |
| S5 | landmark | 1.0 | – | antagen |
| S6 | matchning | 1.0 | 0.228 | uppmatt |
| S7 | landmark | 1.0 | – | antagen |

| ankare | typ | position (m) | riktning (grad) | status |
|---|---|---|---|---|
| bordskant_A | bordskant | -0.05, 0.28, 0.85 | -79 | antagen |
| bordskant_B | bordskant | -0.01, 2.52, 0.60 | -80 | antagen |
| stol_A | sate | 0.01, -0.04, 0.00 | 92 | antagen |
| stol_B | sate | 0.00, 2.48, 0.00 | -90 | antagen |
| staplats_C | staplats | -1.97, 1.00, 0.00 | 10 | antagen |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvet ligger 1,45 m under kameran i tagningar utan synliga fötter (ingest-steget golv).
- Dialogaxel, motbildskamera vid motpartens huvud och stolsavstånd är scengrammatik (plats_matt.json d_grammatik), inte mätt.
