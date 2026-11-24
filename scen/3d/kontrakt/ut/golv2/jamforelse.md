# GOLV2 före → efter

Före: `mat_fore` (backupträdets kod). Efter: `mat_efter`. Samma rutor, masker, rigg och estimatorpunkter.

**Läs så här.** Oförändrat rot-/bildfel och IoU är till stor del en matematisk följd av att kroppens gamla cam_t-skala och kamerans kompensation försvinner tillsammans. Det visar att projektionen i originalkameran är hel, inte att golvet är rätt. Det som prövar golvet är sulornas höjd över golvet per person (tabellen nedan) och personernas inbördes placering från flyttad kamera (bilderna).

## Lägsta sula över golvet (riggens fothud, median över rutor), m

| Klipp | Scen/person | i plan | Modellpose före → efter | Byggd pose (efter stöd) före → efter | Synliga fotrutor |
|---|---|---|---|---|---|
| notan | s1/1 (A) | ja | -0.268 → -0.223 | 0.000 → 0.000 | 0 |
| notan | s2/1 (B) | ja | -0.293 → -0.261 | 0.000 → 0.000 | 0 |
| notan | s3/1 (A) | ja | -0.253 → -0.207 | 0.000 → 0.000 | 0 |
| notan | s4/1 (C) | ja | -0.036 → 0.118 | 0.000 → 0.112 | 0 |
| notan | s4/4 (utelämnad) | nej | -0.026 → -0.014 | – → – | 55 |
| notan | s5/1 (B) | ja | -0.292 → -0.259 | 0.000 → 0.000 | 0 |
| notan | s6/1 (A) | ja | -0.258 → -0.201 | 0.000 → 0.000 | 0 |
| notan | s7/1 (B) | ja | -0.323 → -0.320 | 0.000 → 0.000 | 0 |
| b | s1/1 (A) | ja | 0.000 → 0.000 | 0.000 → 0.000 | 0 |
| b | s2/1 (A) | ja | -0.002 → -0.002 | -0.002 → -0.002 | 0 |
| b | s3/1 (B) | ja | -0.046 → -0.096 | 0.000 → 0.000 | 0 |
| b | s4/1 (B) | ja | -0.053 → -0.039 | 0.000 → 0.000 | 0 |
| b | s5/1 (C) | ja | 0.514 → 0.514 | 0.514 → 0.514 | 0 |
| b | s6/1 (C) | ja | 0.134 → -0.014 | 0.134 → -0.014 | 0 |
| b | s7/1 (C) | ja | 0.100 → -0.095 | 0.100 → -0.095 | 0 |
| b | s8/1 (C) | ja | 0.112 → 0.112 | 0.112 → 0.112 | 0 |
| b | s9/1 (C) | ja | 0.004 → 0.004 | 0.004 → 0.004 | 0 |
| b | s10/1 (C) | ja | 0.216 → 0.216 | 0.216 → 0.216 | 0 |
| b | s11/1 (C) | ja | 0.120 → 0.055 | 0.120 → 0.055 | 0 |

## Alla mått

| Klipp | Scen/person | i plan | Rot px | Median px | p90 px | IoU | Kamera→rumskamera m | Kamerahöjd m | Modellfotrest m | Synlig fotrest m (rutor) | Byggd fotrest m | Höft m | Huvud m |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| notan | s1/1 (A) | ja | 0.0 → 0.0 | 1.98 → 1.98 | 6.00 → 6.00 | 0.651 → 0.651 | 0.303 → 0.000 | 1.56 → 1.61 | -0.175 → -0.130 | – → – (0) | 0.092 → 0.092 | 0.49 → 0.54 | 1.09 → 1.13 |
| notan | s2/1 (B) | ja | 0.0 → 0.0 | 3.64 → 3.64 | 14.54 → 14.54 | 0.624 → 0.623 | 0.426 → 0.000 | 1.59 → 1.63 | -0.202 → -0.170 | – → – (0) | 0.088 → 0.088 | 0.51 → 0.54 | 1.14 → 1.17 |
| notan | s3/1 (A) | ja | 0.0 → 0.0 | 2.10 → 2.10 | 22.27 → 22.27 | 0.674 → 0.673 | 0.263 → 0.000 | 1.53 → 1.58 | -0.160 → -0.114 | – → – (0) | 0.092 → 0.092 | 0.49 → 0.54 | 1.07 → 1.12 |
| notan | s4/1 (C) | ja | 0.0 → 0.0 | 1.09 → 1.09 | 4.55 → 4.55 | 0.721 → 0.735 | 0.231 → 0.000 | 1.45 → 1.60 | 0.014 → 0.168 | – → – (0) | 0.081 → 0.193 | 0.89 → 1.04 | 1.54 → 1.70 |
| notan | s4/4 (utelämnad) | nej | – → – | – → – | – → – | – → – | 0.230 → 0.000 | 1.45 → 1.60 | 0.014 → 0.025 | 0.014 → 0.025 (55) | – → – | 0.42 → 0.44 | 1.01 → 1.02 |
| notan | s5/1 (B) | ja | 0.0 → 0.0 | 3.69 → 3.69 | 11.26 → 11.26 | 0.645 → 0.645 | 0.147 → 0.000 | 1.37 → 1.41 | -0.201 → -0.168 | – → – (0) | 0.088 → 0.088 | 0.51 → 0.54 | 1.14 → 1.17 |
| notan | s6/1 (A) | ja | 0.0 → 0.0 | 20.40 → 20.40 | 62.31 → 62.31 | 0.654 → 0.654 | 0.246 → 0.000 | 1.51 → 1.57 | -0.165 → -0.108 | – → – (0) | 0.092 → 0.092 | 0.48 → 0.54 | 1.07 → 1.13 |
| notan | s7/1 (B) | ja | 0.0 → 0.0 | 1.53 → 1.53 | 3.60 → 3.60 | 0.599 → 0.599 | 0.706 → 0.000 | 1.60 → 1.61 | -0.234 → -0.230 | – → – (0) | 0.088 → 0.088 | 0.54 → 0.54 | 1.14 → 1.15 |
| b | s1/1 (A) | ja | 0.0 → 0.0 | 15.73 → 15.73 | 48.50 → 48.50 | 0.780 → 0.780 | 0.000 → 0.000 | 1.45 → 1.45 | 0.072 → 0.072 | – → – (0) | 0.072 → 0.072 | 0.89 → 0.89 | 1.53 → 1.53 |
| b | s2/1 (A) | ja | 0.0 → 0.0 | 7.96 → 7.96 | 24.36 → 24.36 | 0.793 → 0.793 | 0.000 → 0.000 | 1.45 → 1.45 | 0.068 → 0.068 | – → – (0) | 0.068 → 0.068 | 0.90 → 0.90 | 1.55 → 1.55 |
| b | s3/1 (B) | ja | 0.0 → 0.0 | 7.88 → 7.88 | 21.10 → 21.10 | 0.795 → 0.773 | 0.082 → 0.000 | 1.50 → 1.45 | 0.026 → -0.024 | – → – (0) | 0.086 → 0.086 | 0.82 → 0.77 | 1.46 → 1.41 |
| b | s4/1 (B) | ja | 0.0 → 0.0 | 2.67 → 2.67 | 13.03 → 13.03 | 0.790 → 0.790 | 0.181 → 0.000 | 1.44 → 1.45 | 0.011 → 0.024 | – → – (0) | 0.086 → 0.086 | 0.81 → 0.82 | 1.45 → 1.47 |
| b | s5/1 (C) | ja | 0.0 → 0.0 | 9.29 → 9.29 | 30.98 → 30.98 | 0.634 → 0.634 | 0.000 → 0.000 | 1.89 → 1.89 | 0.564 → 0.564 | – → – (0) | 0.564 → 0.564 | 1.30 → 1.30 | 1.82 → 1.82 |
| b | s6/1 (C) | ja | 0.0 → 0.0 | 5.71 → 5.71 | 20.74 → 20.74 | 0.785 → 0.785 | 0.000 → 0.000 | 1.60 → 1.45 | 0.208 → 0.060 | – → – (0) | 0.208 → 0.060 | 0.94 → 0.79 | 1.53 → 1.38 |
| b | s7/1 (C) | ja | 0.0 → 0.0 | 3.06 → 3.06 | 7.16 → 7.16 | 0.782 → 0.782 | 0.000 → 0.000 | 1.65 → 1.45 | 0.192 → -0.004 | – → – (0) | 0.192 → -0.004 | 0.91 → 0.71 | 1.51 → 1.31 |
| b | s8/1 (C) | ja | 0.0 → 0.0 | 11.69 → 11.69 | 29.61 → 29.61 | 0.606 → 0.606 | 0.000 → 0.000 | 1.45 → 1.45 | 0.171 → 0.171 | – → – (0) | 0.171 → 0.171 | 0.98 → 0.98 | 1.57 → 1.57 |
| b | s9/1 (C) | ja | 0.0 → 0.0 | 6.41 → 6.41 | 18.72 → 18.72 | 0.580 → 0.580 | 0.000 → 0.000 | 1.45 → 1.45 | 0.092 → 0.092 | – → – (0) | 0.092 → 0.092 | 0.86 → 0.86 | 1.47 → 1.47 |
| b | s10/1 (C) | ja | 0.0 → 0.0 | 11.43 → 11.43 | 21.90 → 21.90 | 0.534 → 0.534 | 0.000 → 0.000 | 1.45 → 1.45 | 0.249 → 0.249 | – → – (0) | 0.249 → 0.249 | 1.07 → 1.07 | 1.69 → 1.69 |
| b | s11/1 (C) | ja | 0.0 → 0.0 | 12.96 → 12.96 | 40.68 → 40.68 | 0.622 → 0.622 | 0.000 → 0.000 | 1.51 → 1.45 | 0.208 → 0.143 | – → – (0) | 0.208 → 0.143 | 0.94 → 0.87 | 1.54 → 1.48 |

## Försämringar (rot/bild > 0,5 px, IoU > 0,005)

- b s3/1: iou 0.795 → 0.773

## Förklaringar (mätta 10 nov kväll)

- **b s3/B, IoU 0,795 → 0,773.** Samma plan mätt utan stöd (kroppmatt stod=False) ger 0,795 efter GOLV2. Fallet kommer alltså från det längdbevarande stödet för dolda ben: golvet i b S3 väljs nu av antagen kamerahöjd (förr −1,568 m ur den gamla medianen över cue-familjer, där kroppsräckvidd fick rösta), 5 cm högre relativt kroppen, och stödet böjer de dolda benen mer för att nå golvet. Silhuettkostnad för dold benpose redovisas separat enligt GOLV2.md.
- **notan S4/C svävar (lägsta sula 0,112 m byggd, 0,118 m modell).** C:s fötter är utanför bilden: 0 fotpunkter i egen ruta, 0 användbara rutor. Golvet i S4 väljs av den utelämnade person 4:s synliga fötter (55 rutor, modellbedömd kontakt). Resten är en konflikt mellan två personers skattade djup, inte en uppmätt kontakt för C. Förr skalade golvsteget C:s cam_t tills foten nådde golvet och kompilatorn flyttade kameran 0,23 m för att dölja det. GOLV2 flyttar inte kroppen; stödet når inte golvet med bevarad benlängd.
- **Sittande A/B i notan.** Modellens sulor ligger 0,20–0,32 m under golvet (dolda ben); efter stöd 0,000 m både före och efter. Golvet väljs av sits mot identifierad stol (antagen prior) i alla tagningar utom S4.
- **b S5/C 0,514 m över golvet** både före och efter: golvet väljs av djupgolvet (MoGe, modellbedömt) och C:s ben är dolda. Oförändrat av GOLV2, men en kvarstående brist.

## Objekt notan

| Objekt | Topp m före → efter | XY före → efter |
|---|---|---|
| stol_A | 0.43 → 0.43 | [0.01, -0.04] → [0.03, -0.1] |
| stol_B | 0.43 → 0.43 | [0.0, 2.48] → [-0.01, 2.73] |
| bord_A | 0.76 → 0.76 | [-0.01, 0.6] → [0.01, 0.54] |
| bord_A | 0.76 → 0.76 | [-0.01, 0.6] → [0.01, 0.54] |
| bord_B | 0.76 → 0.76 | [0.0, 1.77] → [-0.01, 2.02] |

## Objekt b

| Objekt | Topp m före → efter | XY före → efter |
|---|---|---|
