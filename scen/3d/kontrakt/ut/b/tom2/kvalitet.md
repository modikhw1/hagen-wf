# Kvalitet

Detta är egna diagnostiska trösklar: bildfel median 20 px/4 % av personhöjd, p90 40 px/8 %, led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal. Bra betyder att dessa kontroller passerar. Granska betyder osäkra antaganden eller konflikt. Dålig betyder att bildfelet passerar gränsen.

| Scen | Bildfel median/p90 px | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 2.77/6.02 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | granska: endast överkropp (A): inget golv eller kontakt, golv antaget |
| s2 | 2.74/5.91 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | granska: endast överkropp (A): inget golv eller kontakt, golv antaget |
| s3 | 3.31/6.00 | antagen, ±12.0 cm; spann 0.0 cm; skala 1,0 antagen | B: 32 i 42 rutor | 0.0 → 0.0 % | granska: golv antaget |
| s4 | 1.93/5.24 | antagen, ±12.0 cm; spann 0.0 cm; skala 1,0 antagen | B: 32 i 70 rutor | 0.0 → 0.0 % | granska: golv antaget |
| s5 | 3.65/5.99 | antagen, ±8.5 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget |
| s6 | 2.29/5.90 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 5.6 → 0.0 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: disk:ram:1.0:-0.2424847417686884, monter:ram:0.42:-0.21823626759181955 |
| s7 | 1.70/4.69 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 6.1 → 0.0 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: disk:ram:1.0:-0.2424847417686884, monter:ram:0.42:-0.21823626759181955 |
| s8 | 3.34/5.96 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 1.0 → 1.0 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget |
| s9 | 3.19/5.89 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget |
| s10 | 4.34/6.00 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 1.8 → 1.8 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget |
| s11 | 2.89/6.02 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 4.7 → 1.9 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: monter:ram:0.42:-0.21823626759181955 |

Antaget: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). Dessa möbelpriorer används bara vid vanligt bord, inte bardisk. En stilla handled behöver inte vila på bordet. Passningens rest mot handled och bäcken loggas, även när en höjd begränsas av priorn. Ingen kropp skalas för att passa en prior.

Skymning är provandel av källmask inom personrutan, med närmaste MHR70-punkts djup; ingen exakt hudarea. Var sjätte och sista rutan kontrolleras före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.

## Skärmtext

81 tidsatta 2D-lager i källpixlar. Textinnehåll från sparad semantik; teckenmallar mäter plats och synlighet utan OCR. Fontval är närmaste installerade font. Konfidens avser teckenmatchning, inte sannolikheten att modellens text är rätt.

## Diskpassning

- chark_disk: höjd 1.000 m (mall), rest None m. Mallhöjd 100 cm. Stilla handleder håller kött och verifierar inte kontakt med disken. Kamerans/personens höjd passas gemensamt mot avläst diskkant.
