# Plats plats_1

Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), origo på golvet under första rollens stol, +Y mot andra rollens stol.

Golv: z = 0.00 m (antagen). Objekt: 0, ankare: 8, avvisade observationer: 12.

| tagning | metod | skala | residual (m) | status |
|---|---|---|---|---|
| S1 | antagande | 1.0 | – | antagen |
| S2 | antagande | 1.0 | – | antagen |
| S3 | antagande | 1.0 | – | antagen |
| S4 | antagande | 1.0 | – | antagen |
| S5 | antagande | 1.0 | – | antagen |
| S6 | antagande | 1.0 | – | antagen |
| S7 | antagande | 1.0 | – | antagen |
| S8 | antagande | 1.0 | – | antagen |
| S9 | antagande | 1.0 | – | antagen |
| S10 | antagande | 1.0 | – | antagen |
| S11 | antagande | 1.0 | – | antagen |

| ankare | typ | position (m) | riktning (grad) | status |
|---|---|---|---|---|
| sta_bakom | sta_bakom | 0.00, -0.19, 0.00 | 90 | antagen |
| kundsida | staplats | 0.00, 0.19, 0.00 | -90 | antagen |
| kamera_kund | annat | 0.00, 1.50, 0.00 | -90 | antagen |
| kamera_personal | annat | 0.00, -1.50, 0.00 | 90 | antagen |
| kamera_kund_K1 | annat | -0.00, 0.95, 1.45 | -90 | antagen |
| kamera_kund_K2 | annat | -0.00, 1.29, 1.46 | -90 | antagen |
| kamera_kund_K3 | annat | 0.00, 1.39, 1.45 | -90 | antagen |
| kamera_kund_K4 | annat | 0.00, 0.94, 1.45 | -90 | antagen |

Antaganden:
- Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.
- Golvets cues och priorer finns i golv.matning. Konflikt över 10 cm flaggas; 1,45 m kamerahöjd är endast reserv. Ensam tagning behåller sitt tidigare golv tills --tillampa-golv väljs.
- Ingen scengrammatik kunde tillämpas: semantiken anger ingen dialogaxel mellan kolleger

## Rumsmall

Mall: chark_disk. Rigid ankarrest RMS: 0.000 m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.

Utelämnade: 
