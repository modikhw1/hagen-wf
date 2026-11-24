# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (antagen). Objekt: 5, ankare: 3, avvisade observationer: 12.

| tagning | metod | skala | residual (m) | status |
|---|---|---|---|---|
| S1 | landmark | 1.0 | – | antagen |
| S2 | landmark | 1.0 | – | antagen |
| S3 | landmark | 1.0 | – | antagen |
| S4 | landmark | 1.0 | – | antagen |
| S5 | landmark | 1.0 | – | antagen |
| S6 | landmark | 1.0 | – | antagen |
| S7 | landmark | 1.0 | – | antagen |
| S8 | landmark | 1.0 | – | antagen |
| S9 | landmark | 1.0 | – | antagen |
| S10 | landmark | 1.0 | – | antagen |
| S11 | landmark | 1.0 | – | antagen |

| ankare | typ | position (m) | riktning (grad) | status |
|---|---|---|---|---|
| staplats_A | staplats | 0.00, 1.37, 0.00 | -120 | antagen |
| staplats_B | staplats | 0.00, 1.37, 0.00 | -116 | antagen |
| staplats_C | staplats | 2.27, 1.36, 0.00 | -87 | antagen |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvets cues och priorer finns i golv.matning. Konflikt över 10 cm flaggas; 1,45 m kamerahöjd är endast reserv. Ensam tagning behåller sitt tidigare golv tills --tillampa-golv väljs.
- Ingen scengrammatik kunde tillämpas: deklarerat montage utan dialogaxel; person- och kameraplatser används per tagning
- Deklarerat rum (plats/deklaration.json, deklaration/0.8):

## Rumsmall

Mall: dekl_b-tilltal-ravara-tagningar_konsensus_fokus_n6. Rigid ankarrest RMS: 0.057 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: 
