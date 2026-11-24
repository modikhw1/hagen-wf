# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (antagen). Objekt: 5, ankare: 5, avvisade observationer: 11.

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
| bordskant_A | bordskant | 0.07, 0.26, 0.95 | -102 | antagen |
| bordskant_B | bordskant | 0.04, 2.24, 0.66 | 100 | antagen |
| stol_A | sate | 0.01, -0.04, 0.00 | 92 | antagen |
| stol_B | sate | 0.00, 2.48, 0.00 | -90 | antagen |
| staplats_C | staplats | 1.84, 1.09, 0.00 | -170 | antagen |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvets cues och priorer finns i golv.matning. Konflikt över 10 cm flaggas; 1,45 m kamerahöjd är endast reserv. Ensam tagning behåller sitt tidigare golv tills --tillampa-golv väljs.
- Dialogaxel, motbildskamera vid motpartens huvud och stolsavstånd är scengrammatik (plats_matt.json d_grammatik), inte mätt.
- Modellens bedömning (gemini-3.5-flash): plats restaurang_matsal; Två separata bord placerade tvärs över rummet från varandra. Paret: separata_bord. Inga avstånd i meter anges: modellen kan inte mäta.

## Rumsmall

Mall: notan_tva_bord. Rigid ankarrest RMS: 1.265 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: okand_s4_4: Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd.
