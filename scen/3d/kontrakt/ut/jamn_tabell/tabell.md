# Utjämningsmetoder: sju scener, rättat ledurval

Rättat 10 november: den tidigare tabellen räknade bara två axelleder när benen var dolda. Filmens kvalitetssida räknade också alla 42 fingerleder. Nu räknar båda samma 44 par (48 med synliga ben), på samma pålitliga rutor. B s1 blir 15,73/48,50 px, exakt filmens värden. Formparametrar låses till samma median som sekvens_stabil.py; det tidigare påståendet att råformen var konstant var fel.

Alla tabellmetoder mäts före golv/kontakt/stöd i tagningens kamera. Filmens sida gäller kroppen efter dessa steg. Px är avvikelse från estimatorns egna 2D-punkter, inte oberoende kvalitet. IoU är hudnät mot YOLO-mask på alla mätbara maskrutor; synlig klipper vid maskens underkant. Darr: 127 leder, cm/ruta² i kamerarum. Täckning är px / mask. Parametrarna och diagnostiska gränserna har inte ändrats för att få godkända resultat.


## scen/3d/ingest/ut/b-tilltal-ravara-tagningar/S1:1

| Metod | median px | p90 px | IoU | IoU synlig | Darr | Täckning px/mask |
|---|---:|---:|---:|---:|---:|---:|
| raw | 0.00 | 0.00 | 0.792 | 0.792 | 3.40 | 1.00/1.00 |
| gammal | 12.51 | 53.80 | 0.780 | 0.780 | 0.77 | 1.00/1.00 |
| bildskydd | 2.77 | 6.02 | 0.788 | 0.788 | 2.86 | 1.00/1.00 |
| sg9/3 | 16.50 | 45.86 | 0.787 | 0.787 | 0.82 | 1.00/1.00 |
| oneeuro | 14.76 | 38.02 | 0.789 | 0.789 | 1.24 | 1.00/1.00 |
| whitt fc4 k2 d2 T-gammal | 14.05 | 44.78 | 0.780 | 0.780 | 0.55 | 1.00/1.00 |
| ror fc4 k2 d2 T-gammal | 15.63 | 48.83 | 0.780 | 0.780 | 0.84 | 1.00/1.00 |
| ror fc4 k2 d2 T-ny (vald) | 15.73 | 48.50 | 0.780 | 0.782 | 0.97 | 1.00/1.00 |
| ror fc4 k1 d2 T-gammal | 13.32 | 45.70 | 0.781 | 0.781 | 1.48 | 1.00/1.00 |
| ror fc4 k3 d2 T-gammal | 14.16 | 48.01 | 0.780 | 0.780 | 0.64 | 1.00/1.00 |
| ror fc3 k2 d3 T-gammal | 18.50 | 51.92 | 0.783 | 0.783 | 0.88 | 1.00/1.00 |
| ror fc6 k2 d2 T-gammal | 11.99 | 41.65 | 0.781 | 0.781 | 0.95 | 1.00/1.00 |

## scen/3d/ingest/ut/b-tilltal-ravara-tagningar/S5:1

| Metod | median px | p90 px | IoU | IoU synlig | Darr | Täckning px/mask |
|---|---:|---:|---:|---:|---:|---:|
| raw | 0.00 | 0.00 | 0.637 | 0.668 | 6.24 | 1.00/1.00 |
| gammal | 8.38 | 46.14 | 0.642 | 0.666 | 1.14 | 1.00/1.00 |
| bildskydd | 3.65 | 5.99 | 0.640 | 0.666 | 4.55 | 1.00/1.00 |
| sg9/3 | 12.85 | 37.43 | 0.642 | 0.667 | 1.16 | 1.00/1.00 |
| oneeuro | 11.79 | 33.60 | 0.647 | 0.672 | 1.43 | 1.00/1.00 |
| whitt fc4 k2 d2 T-gammal | 9.67 | 40.46 | 0.644 | 0.668 | 0.88 | 1.00/1.00 |
| ror fc4 k2 d2 T-gammal | 12.14 | 39.09 | 0.642 | 0.667 | 1.44 | 1.00/1.00 |
| ror fc4 k2 d2 T-ny (vald) | 9.29 | 30.98 | 0.634 | 0.665 | 1.53 | 1.00/1.00 |
| ror fc4 k1 d2 T-gammal | 8.71 | 35.11 | 0.641 | 0.668 | 2.14 | 1.00/1.00 |
| ror fc4 k3 d2 T-gammal | 11.46 | 38.96 | 0.645 | 0.670 | 1.08 | 1.00/1.00 |
| ror fc3 k2 d3 T-gammal | 13.76 | 43.07 | 0.642 | 0.667 | 1.48 | 1.00/1.00 |
| ror fc6 k2 d2 T-gammal | 8.64 | 36.60 | 0.643 | 0.668 | 1.52 | 1.00/1.00 |

## scen/3d/ingest/ut/b-tilltal-ravara-tagningar/S11:1

| Metod | median px | p90 px | IoU | IoU synlig | Darr | Täckning px/mask |
|---|---:|---:|---:|---:|---:|---:|
| raw | 0.00 | 0.00 | 0.621 | 0.628 | 4.29 | 1.00/1.00 |
| gammal | 12.66 | 44.07 | 0.624 | 0.632 | 0.75 | 1.00/1.00 |
| bildskydd | 2.89 | 6.02 | 0.622 | 0.629 | 2.94 | 1.00/1.00 |
| sg9/3 | 14.46 | 48.13 | 0.623 | 0.633 | 0.78 | 1.00/1.00 |
| oneeuro | 11.32 | 35.37 | 0.628 | 0.630 | 1.13 | 1.00/1.00 |
| whitt fc4 k2 d2 T-gammal | 13.22 | 43.34 | 0.624 | 0.632 | 0.52 | 1.00/1.00 |
| ror fc4 k2 d2 T-gammal | 12.49 | 41.84 | 0.625 | 0.630 | 0.90 | 1.00/1.00 |
| ror fc4 k2 d2 T-ny (vald) | 12.96 | 40.68 | 0.622 | 0.630 | 0.90 | 1.00/1.00 |
| ror fc4 k1 d2 T-gammal | 9.46 | 37.60 | 0.627 | 0.632 | 1.55 | 1.00/1.00 |
| ror fc4 k3 d2 T-gammal | 12.94 | 43.50 | 0.624 | 0.631 | 0.67 | 1.00/1.00 |
| ror fc3 k2 d3 T-gammal | 13.86 | 47.40 | 0.624 | 0.630 | 0.91 | 1.00/1.00 |
| ror fc6 k2 d2 T-gammal | 9.89 | 38.49 | 0.623 | 0.633 | 1.05 | 1.00/1.00 |

## scen/3d/ingest/ut/kand-kennysgelato-tagningar/S1:1

| Metod | median px | p90 px | IoU | IoU synlig | Darr | Täckning px/mask |
|---|---:|---:|---:|---:|---:|---:|
| raw | 0.00 | 0.00 | 0.699 | 0.738 | 7.03 | 0.95/0.99 |
| gammal | 12.85 | 62.34 | 0.696 | 0.737 | 1.28 | 0.95/0.99 |
| bildskydd | 3.03 | 5.95 | 0.698 | 0.736 | 5.99 | 0.95/0.99 |
| sg9/3 | 17.60 | 68.48 | 0.697 | 0.738 | 1.32 | 0.95/0.99 |
| oneeuro | 17.28 | 56.61 | 0.697 | 0.739 | 1.95 | 0.95/0.99 |
| whitt fc4 k2 d2 T-gammal | 14.54 | 62.16 | 0.696 | 0.739 | 1.00 | 0.95/0.99 |
| ror fc4 k2 d2 T-gammal | 13.70 | 52.11 | 0.700 | 0.740 | 3.36 | 0.95/0.99 |
| ror fc4 k2 d2 T-ny (vald) | 14.04 | 50.14 | 0.698 | 0.738 | 3.77 | 0.95/0.99 |
| ror fc4 k1 d2 T-gammal | 12.92 | 45.23 | 0.699 | 0.739 | 4.24 | 0.95/0.99 |
| ror fc4 k3 d2 T-gammal | 14.79 | 57.63 | 0.697 | 0.739 | 2.78 | 0.95/0.99 |
| ror fc3 k2 d3 T-gammal | 16.59 | 57.71 | 0.699 | 0.741 | 3.35 | 0.95/0.99 |
| ror fc6 k2 d2 T-gammal | 11.88 | 47.87 | 0.699 | 0.740 | 3.43 | 0.95/0.99 |

## scen/3d/ingest/ut/a-sketch-servering-tagningar/S1:1

| Metod | median px | p90 px | IoU | IoU synlig | Darr | Täckning px/mask |
|---|---:|---:|---:|---:|---:|---:|
| raw | 0.00 | 0.00 | 0.702 | 0.728 | 9.35 | 0.98/0.98 |
| gammal | 11.99 | 55.78 | 0.701 | 0.730 | 2.16 | 0.98/0.98 |
| bildskydd | 4.28 | 5.99 | 0.699 | 0.731 | 6.40 | 0.98/0.98 |
| sg9/3 | 13.88 | 59.45 | 0.704 | 0.732 | 2.31 | 0.98/0.98 |
| oneeuro | 13.81 | 45.70 | 0.702 | 0.723 | 2.97 | 0.98/0.98 |
| whitt fc4 k2 d2 T-gammal | 14.32 | 51.32 | 0.703 | 0.730 | 2.00 | 0.98/0.98 |
| ror fc4 k2 d2 T-gammal | 16.71 | 52.41 | 0.698 | 0.729 | 4.40 | 0.98/0.98 |
| ror fc4 k2 d2 T-ny (vald) | 15.63 | 44.08 | 0.696 | 0.728 | 4.40 | 0.98/0.98 |
| ror fc4 k1 d2 T-gammal | 13.67 | 45.16 | 0.702 | 0.731 | 5.40 | 0.98/0.98 |
| ror fc4 k3 d2 T-gammal | 18.17 | 60.50 | 0.701 | 0.730 | 3.70 | 0.98/0.98 |
| ror fc3 k2 d3 T-gammal | 20.68 | 67.33 | 0.700 | 0.728 | 4.51 | 0.98/0.98 |
| ror fc6 k2 d2 T-gammal | 13.64 | 46.27 | 0.702 | 0.727 | 4.36 | 0.98/0.98 |

## scen/3d/ingest/ut/a-sketch-servering-tagningar/S4:1

| Metod | median px | p90 px | IoU | IoU synlig | Darr | Täckning px/mask |
|---|---:|---:|---:|---:|---:|---:|
| raw | 0.00 | 0.00 | 0.737 | 0.737 | 3.79 | 0.66/1.00 |
| gammal | 12.72 | 47.03 | 0.735 | 0.735 | 0.93 | 0.66/1.00 |
| bildskydd | 4.02 | 6.00 | 0.735 | 0.735 | 3.08 | 0.66/1.00 |
| sg9/3 | 16.57 | 57.61 | 0.735 | 0.735 | 0.87 | 0.66/1.00 |
| oneeuro | 16.70 | 47.77 | 0.734 | 0.734 | 1.22 | 0.66/1.00 |
| whitt fc4 k2 d2 T-gammal | 14.73 | 53.09 | 0.733 | 0.733 | 0.68 | 0.66/1.00 |
| ror fc4 k2 d2 T-gammal | 14.69 | 37.97 | 0.735 | 0.735 | 1.55 | 0.66/1.00 |
| ror fc4 k2 d2 T-ny (vald) | 15.66 | 37.17 | 0.736 | 0.736 | 1.59 | 0.66/1.00 |
| ror fc4 k1 d2 T-gammal | 11.27 | 27.14 | 0.738 | 0.738 | 2.13 | 0.66/1.00 |
| ror fc4 k3 d2 T-gammal | 15.88 | 46.06 | 0.735 | 0.735 | 1.24 | 0.66/1.00 |
| ror fc3 k2 d3 T-gammal | 18.07 | 42.17 | 0.734 | 0.734 | 1.68 | 0.66/1.00 |
| ror fc6 k2 d2 T-gammal | 11.28 | 32.99 | 0.737 | 0.737 | 1.63 | 0.66/1.00 |

## scen/3d/ingest/ut/notan-tagningar/S6:1

| Metod | median px | p90 px | IoU | IoU synlig | Darr | Täckning px/mask |
|---|---:|---:|---:|---:|---:|---:|
| raw | 0.00 | 0.00 | 0.653 | 0.702 | 3.38 | 1.00/1.00 |
| gammal | 19.89 | 68.40 | 0.656 | 0.703 | 0.53 | 1.00/1.00 |
| bildskydd | 2.73 | 6.06 | 0.655 | 0.703 | 3.34 | 1.00/1.00 |
| sg9/3 | 17.99 | 54.41 | 0.655 | 0.703 | 0.84 | 1.00/1.00 |
| oneeuro | 14.50 | 42.25 | 0.654 | 0.704 | 1.20 | 1.00/1.00 |
| whitt fc4 k2 d2 T-gammal | 19.66 | 61.22 | 0.655 | 0.703 | 0.36 | 1.00/1.00 |
| ror fc4 k2 d2 T-gammal | 20.50 | 62.11 | 0.657 | 0.704 | 0.43 | 1.00/1.00 |
| ror fc4 k2 d2 T-ny (vald) | 20.40 | 62.31 | 0.655 | 0.703 | 0.42 | 1.00/1.00 |
| ror fc4 k1 d2 T-gammal | 21.26 | 61.91 | 0.657 | 0.704 | 0.99 | 1.00/1.00 |
| ror fc4 k3 d2 T-gammal | 19.93 | 60.84 | 0.655 | 0.703 | 0.36 | 1.00/1.00 |
| ror fc3 k2 d3 T-gammal | 24.86 | 66.47 | 0.656 | 0.703 | 0.47 | 1.00/1.00 |
| ror fc6 k2 d2 T-gammal | 19.46 | 60.86 | 0.656 | 0.704 | 0.61 | 1.00/1.00 |

Valet behålls för jämn rörelse utan bildskyddets ruta-för-ruta-blandning. Det ger inte samtidigt bra fingerpassning i alla scener. Kenny s1 och a s1 har fortfarande för mycket darr enligt de oförändrade gränserna. Att byta parameteruppsättning utan en ny oberoende granskning skulle inte lösa det.
