# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (antagen). Objekt: 6, ankare: 2, avvisade observationer: 7.

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
| stol_A | sate | -0.02, 2.06, 0.00 | -108 | uppmatt |
| stol_B | sate | 0.20, 1.12, 0.00 | -120 | uppmatt |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvet ligger 1,45 m under kameran i tagningar utan synliga fötter (ingest-steget golv).
- Ingen scengrammatik kunde tillämpas: rörlig kamera

## Rumsmall

Mall: restaurang_tva. Rigid ankarrest RMS: 0.146 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: okand_s5_2: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd., okand_s9_2: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd., okand_s10_1: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd., okand_s10_2: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd.
