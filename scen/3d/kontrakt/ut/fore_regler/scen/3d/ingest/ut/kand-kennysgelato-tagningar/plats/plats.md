# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (antagen). Objekt: 1, ankare: 0, avvisade observationer: 3.

| tagning | metod | skala | residual (m) | status |
|---|---|---|---|---|
| S1 | identitet | 1.0 | – | uppmatt |
| S2 | identitet | 1.0 | – | uppmatt |

| ankare | typ | position (m) | riktning (grad) | status |
|---|---|---|---|---|

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvet ligger 1,45 m under kameran i tagningar utan synliga fötter (ingest-steget golv).
- Ingen scengrammatik kunde tillämpas: rörlig kamera

## Rumsmall

Mall: bar_disk. Rigid ankarrest RMS: 1.494 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: okand_s1_1: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd., okand_s1_7: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd., okand_s2_1: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd., okand_s2_5: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd.
