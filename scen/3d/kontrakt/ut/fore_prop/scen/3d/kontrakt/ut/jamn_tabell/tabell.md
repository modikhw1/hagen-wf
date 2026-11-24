# Utjämningsmetoder, sju scener (jamn_utvardera.py, rå-estimat ur kropp/, tagningens egen kamera före golv/kontakt)

px = avvikelse mot estimatorns 2D-punkter (EJ oberoende; 42 av 48 punkter är fingerleder). IoU = hudnätets silhuett mot YOLO-masken, alla rutor med mask (oberoende modell; `syn` = klippt vid maskens nedre rad). Darr = medel andra differens, 127 leder, cm/ruta², kamerarum. Täckning px / IoU = bedömda rutor / rutor i tagningen.


### b-tilltal-ravara-tagningar/S1 person 1

| metod | px median | px p90 | IoU | IoU syn | darr | täckn px | täckn IoU |
|---|---|---|---|---|---|---|---|
| raw (estimatorn) | 0.00 | 0.00 | 0.792 | 0.792 | 3.40 | 1.00 | 1.00 |
| gammal stabilisering (Hampel + 6 Hz) | 3.08 | 6.58 | 0.780 | 0.780 | 0.77 | 1.00 | 1.00 |
| bildskydd (som tom2) | 0.40 | 2.69 | 0.788 | 0.788 | 2.86 | 1.00 | 1.00 |
| Savitzky-Golay 9/3 | 3.18 | 7.06 | 0.787 | 0.787 | 0.82 | 1.00 | 1.00 |
| One-Euro (dubbelriktad) | 3.09 | 6.01 | 0.789 | 0.789 | 1.24 | 1.00 | 1.00 |
| Whittaker 4 Hz, utan rör | 3.10 | 6.80 | 0.780 | 0.780 | 0.55 | 1.00 | 1.00 |
| rör 4 Hz k2, gammal cam_t | 3.12 | 6.34 | 0.780 | 0.780 | 0.84 | 1.00 | 1.00 |
| **rör 4 Hz k2 + ny cam_t (vald)** | 2.52 | 5.17 | 0.780 | 0.782 | 0.97 | 1.00 | 1.00 |
| rör k1 | 3.07 | 6.24 | 0.781 | 0.781 | 1.48 | 1.00 | 1.00 |
| rör k3 | 3.12 | 6.89 | 0.780 | 0.780 | 0.64 | 1.00 | 1.00 |
| rör 3 Hz, jerk-straff (d3) | 3.44 | 6.53 | 0.783 | 0.783 | 0.88 | 1.00 | 1.00 |
| rör 6 Hz k2 | 2.92 | 6.45 | 0.781 | 0.781 | 0.95 | 1.00 | 1.00 |

### b-tilltal-ravara-tagningar/S5 person 1

| metod | px median | px p90 | IoU | IoU syn | darr | täckn px | täckn IoU |
|---|---|---|---|---|---|---|---|
| raw (estimatorn) | 0.00 | 0.00 | 0.637 | 0.668 | 6.24 | 1.00 | 1.00 |
| gammal stabilisering (Hampel + 6 Hz) | 3.74 | 18.26 | 0.642 | 0.666 | 1.14 | 1.00 | 1.00 |
| bildskydd (som tom2) | 1.52 | 4.83 | 0.640 | 0.666 | 4.55 | 1.00 | 1.00 |
| Savitzky-Golay 9/3 | 4.15 | 19.47 | 0.642 | 0.667 | 1.16 | 1.00 | 1.00 |
| One-Euro (dubbelriktad) | 4.49 | 18.72 | 0.647 | 0.672 | 1.43 | 1.00 | 1.00 |
| Whittaker 4 Hz, utan rör | 3.96 | 19.66 | 0.644 | 0.668 | 0.88 | 1.00 | 1.00 |
| rör 4 Hz k2, gammal cam_t | 3.91 | 17.29 | 0.642 | 0.667 | 1.44 | 1.00 | 1.00 |
| **rör 4 Hz k2 + ny cam_t (vald)** | 2.48 | 4.24 | 0.634 | 0.665 | 1.53 | 1.00 | 1.00 |
| rör k1 | 3.96 | 16.89 | 0.641 | 0.668 | 2.14 | 1.00 | 1.00 |
| rör k3 | 4.16 | 18.25 | 0.645 | 0.670 | 1.08 | 1.00 | 1.00 |
| rör 3 Hz, jerk-straff (d3) | 4.13 | 17.64 | 0.642 | 0.667 | 1.48 | 1.00 | 1.00 |
| rör 6 Hz k2 | 3.53 | 17.66 | 0.643 | 0.668 | 1.52 | 1.00 | 1.00 |

### b-tilltal-ravara-tagningar/S11 person 1

| metod | px median | px p90 | IoU | IoU syn | darr | täckn px | täckn IoU |
|---|---|---|---|---|---|---|---|
| raw (estimatorn) | 0.00 | 0.00 | 0.621 | 0.628 | 4.29 | 1.00 | 1.00 |
| gammal stabilisering (Hampel + 6 Hz) | 2.99 | 5.89 | 0.624 | 0.632 | 0.75 | 1.00 | 1.00 |
| bildskydd (som tom2) | 0.57 | 1.51 | 0.622 | 0.629 | 2.94 | 1.00 | 1.00 |
| Savitzky-Golay 9/3 | 2.70 | 6.40 | 0.623 | 0.633 | 0.78 | 1.00 | 1.00 |
| One-Euro (dubbelriktad) | 2.98 | 5.78 | 0.628 | 0.630 | 1.13 | 1.00 | 1.00 |
| Whittaker 4 Hz, utan rör | 2.68 | 5.87 | 0.624 | 0.632 | 0.52 | 1.00 | 1.00 |
| rör 4 Hz k2, gammal cam_t | 3.12 | 5.68 | 0.625 | 0.630 | 0.90 | 1.00 | 1.00 |
| **rör 4 Hz k2 + ny cam_t (vald)** | 2.65 | 4.87 | 0.622 | 0.630 | 0.90 | 1.00 | 1.00 |
| rör k1 | 2.96 | 5.37 | 0.627 | 0.632 | 1.55 | 1.00 | 1.00 |
| rör k3 | 2.94 | 5.72 | 0.624 | 0.631 | 0.67 | 1.00 | 1.00 |
| rör 3 Hz, jerk-straff (d3) | 3.05 | 6.33 | 0.624 | 0.630 | 0.91 | 1.00 | 1.00 |
| rör 6 Hz k2 | 2.56 | 5.68 | 0.623 | 0.633 | 1.05 | 1.00 | 1.00 |

### kand-kennysgelato-tagningar/S1 person 1

| metod | px median | px p90 | IoU | IoU syn | darr | täckn px | täckn IoU |
|---|---|---|---|---|---|---|---|
| raw (estimatorn) | 0.00 | 0.00 | 0.699 | 0.738 | 7.03 | 0.95 | 0.99 |
| gammal stabilisering (Hampel + 6 Hz) | 9.15 | 34.74 | 0.696 | 0.737 | 1.28 | 0.95 | 0.99 |
| bildskydd (som tom2) | 1.46 | 4.95 | 0.698 | 0.736 | 5.99 | 0.95 | 0.99 |
| Savitzky-Golay 9/3 | 11.29 | 78.47 | 0.697 | 0.738 | 1.32 | 0.95 | 0.99 |
| One-Euro (dubbelriktad) | 9.23 | 57.15 | 0.697 | 0.739 | 1.95 | 0.95 | 0.99 |
| Whittaker 4 Hz, utan rör | 8.79 | 55.52 | 0.696 | 0.739 | 1.00 | 0.95 | 0.99 |
| rör 4 Hz k2, gammal cam_t | 9.19 | 43.63 | 0.700 | 0.740 | 3.36 | 0.95 | 0.99 |
| **rör 4 Hz k2 + ny cam_t (vald)** | 8.50 | 27.05 | 0.698 | 0.738 | 3.77 | 0.95 | 0.99 |
| rör k1 | 11.39 | 40.56 | 0.699 | 0.739 | 4.24 | 0.95 | 0.99 |
| rör k3 | 8.80 | 47.50 | 0.697 | 0.739 | 2.78 | 0.95 | 0.99 |
| rör 3 Hz, jerk-straff (d3) | 9.42 | 40.66 | 0.699 | 0.741 | 3.35 | 0.95 | 0.99 |
| rör 6 Hz k2 | 8.80 | 43.63 | 0.699 | 0.740 | 3.43 | 0.95 | 0.99 |

### a-sketch-servering-tagningar/S1 person 1

| metod | px median | px p90 | IoU | IoU syn | darr | täckn px | täckn IoU |
|---|---|---|---|---|---|---|---|
| raw (estimatorn) | 0.00 | 0.00 | 0.702 | 0.728 | 9.35 | 0.98 | 0.98 |
| gammal stabilisering (Hampel + 6 Hz) | 15.68 | 49.08 | 0.701 | 0.730 | 2.16 | 0.98 | 0.98 |
| bildskydd (som tom2) | 2.83 | 5.52 | 0.699 | 0.731 | 6.40 | 0.98 | 0.98 |
| Savitzky-Golay 9/3 | 15.57 | 51.36 | 0.704 | 0.732 | 2.31 | 0.98 | 0.98 |
| One-Euro (dubbelriktad) | 12.64 | 33.06 | 0.702 | 0.723 | 2.97 | 0.98 | 0.98 |
| Whittaker 4 Hz, utan rör | 15.42 | 45.20 | 0.703 | 0.730 | 2.00 | 0.98 | 0.98 |
| rör 4 Hz k2, gammal cam_t | 16.42 | 50.64 | 0.698 | 0.729 | 4.40 | 0.98 | 0.98 |
| **rör 4 Hz k2 + ny cam_t (vald)** | 8.27 | 41.34 | 0.696 | 0.728 | 4.40 | 0.98 | 0.98 |
| rör k1 | 10.90 | 46.29 | 0.702 | 0.731 | 5.40 | 0.98 | 0.98 |
| rör k3 | 18.87 | 58.14 | 0.701 | 0.730 | 3.70 | 0.98 | 0.98 |
| rör 3 Hz, jerk-straff (d3) | 18.50 | 65.94 | 0.700 | 0.728 | 4.51 | 0.98 | 0.98 |
| rör 6 Hz k2 | 13.89 | 50.87 | 0.702 | 0.727 | 4.36 | 0.98 | 0.98 |

### a-sketch-servering-tagningar/S4 person 1

| metod | px median | px p90 | IoU | IoU syn | darr | täckn px | täckn IoU |
|---|---|---|---|---|---|---|---|
| raw (estimatorn) | 0.00 | 0.00 | 0.737 | 0.737 | 3.79 | 0.66 | 1.00 |
| gammal stabilisering (Hampel + 6 Hz) | 4.19 | 10.74 | 0.735 | 0.735 | 0.93 | 0.66 | 1.00 |
| bildskydd (som tom2) | 0.96 | 3.18 | 0.735 | 0.735 | 3.08 | 0.66 | 1.00 |
| Savitzky-Golay 9/3 | 4.87 | 12.38 | 0.735 | 0.735 | 0.87 | 0.66 | 1.00 |
| One-Euro (dubbelriktad) | 5.95 | 13.68 | 0.734 | 0.734 | 1.22 | 0.66 | 1.00 |
| Whittaker 4 Hz, utan rör | 4.72 | 11.74 | 0.733 | 0.733 | 0.68 | 0.66 | 1.00 |
| rör 4 Hz k2, gammal cam_t | 4.96 | 11.62 | 0.735 | 0.735 | 1.55 | 0.66 | 1.00 |
| **rör 4 Hz k2 + ny cam_t (vald)** | 4.70 | 10.16 | 0.736 | 0.736 | 1.59 | 0.66 | 1.00 |
| rör k1 | 4.30 | 11.32 | 0.738 | 0.738 | 2.13 | 0.66 | 1.00 |
| rör k3 | 4.92 | 12.17 | 0.735 | 0.735 | 1.24 | 0.66 | 1.00 |
| rör 3 Hz, jerk-straff (d3) | 5.55 | 12.32 | 0.734 | 0.734 | 1.68 | 0.66 | 1.00 |
| rör 6 Hz k2 | 4.11 | 9.93 | 0.737 | 0.737 | 1.63 | 0.66 | 1.00 |

### notan-tagningar/S6 person 1

| metod | px median | px p90 | IoU | IoU syn | darr | täckn px | täckn IoU |
|---|---|---|---|---|---|---|---|
| raw (estimatorn) | 0.00 | 0.00 | 0.653 | 0.702 | 3.38 | 1.00 | 1.00 |
| gammal stabilisering (Hampel + 6 Hz) | 1.37 | 2.99 | 0.656 | 0.703 | 0.53 | 1.00 | 1.00 |
| bildskydd (som tom2) | 0.15 | 0.53 | 0.655 | 0.703 | 3.34 | 1.00 | 1.00 |
| Savitzky-Golay 9/3 | 1.52 | 3.09 | 0.655 | 0.703 | 0.84 | 1.00 | 1.00 |
| One-Euro (dubbelriktad) | 1.44 | 2.92 | 0.654 | 0.704 | 1.20 | 1.00 | 1.00 |
| Whittaker 4 Hz, utan rör | 1.39 | 2.96 | 0.655 | 0.703 | 0.36 | 1.00 | 1.00 |
| rör 4 Hz k2, gammal cam_t | 1.32 | 2.75 | 0.657 | 0.704 | 0.43 | 1.00 | 1.00 |
| **rör 4 Hz k2 + ny cam_t (vald)** | 1.30 | 2.57 | 0.655 | 0.703 | 0.42 | 1.00 | 1.00 |
| rör k1 | 1.38 | 2.89 | 0.657 | 0.704 | 0.99 | 1.00 | 1.00 |
| rör k3 | 1.44 | 2.91 | 0.655 | 0.703 | 0.36 | 1.00 | 1.00 |
| rör 3 Hz, jerk-straff (d3) | 1.54 | 3.14 | 0.656 | 0.703 | 0.47 | 1.00 | 1.00 |
| rör 6 Hz k2 | 1.26 | 2.74 | 0.656 | 0.704 | 0.61 | 1.00 | 1.00 |
