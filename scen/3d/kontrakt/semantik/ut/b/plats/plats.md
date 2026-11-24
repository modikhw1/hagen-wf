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
| stol_C | sate | 0.14, 1.83, 0.00 | -91 | uppmatt |
| staplats_A | staplats | 0.02, 1.30, 0.00 | -117 | uppmatt |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvet ligger 1,45 m under kameran i tagningar utan synliga fötter (ingest-steget golv).
- Ingen scengrammatik kunde tillämpas: rörlig kamera
- Modellens bedömning (gemini-3.5-flash): plats butik_eller_disk; Personalen står bakom betjäningsdisk/charkdisk med våg. Paret: disk_mellan. Inga avstånd i meter anges: modellen kan inte mäta.

## Rumsmall

Mall: bar_disk. Rigid ankarrest RMS: 1.649 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: okand_s5_2: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd., okand_s9_2: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd., okand_s10_2: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd.
