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
| staplats_A | staplats | 0.00, 1.16, 0.00 | -119 | antagen |
| staplats_B | staplats | 0.00, 1.16, 0.00 | -116 | antagen |
| staplats_C | staplats | 3.11, 1.54, 0.00 | -78 | antagen |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvets cues och priorer finns i golv.matning. Konflikt över 10 cm flaggas; 1,45 m kamerahöjd är endast reserv. Ensam tagning behåller sitt tidigare golv tills --tillampa-golv väljs.
- Ingen scengrammatik kunde tillämpas: deklarerat montage utan dialogaxel; person- och kameraplatser används per tagning
- Deklarerat rum (plats/deklaration.json, deklaration/0.8): En slaktarbutik, ett rum. Tre gissar vad en köttbit väger (Mads 2,400, Morten 2,348, Lærke 3,005); sist vägs den (2,056).

## Rumsmall

Mall: dekl_b-tilltal-ravara-tagningar. Rigid ankarrest RMS: 0.054 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: 
