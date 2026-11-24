# Kvalitet

Detta är egna diagnostiska trösklar: bildfel median 20 px/4 % av personhöjd, p90 40 px/8 %, led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal. Bra betyder att dessa kontroller passerar. Granska betyder osäkra antaganden eller konflikt. Dålig betyder att bildfelet passerar gränsen.

| Scen | Bildfel median/p90 px | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 12.51/53.80 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 17.7 → 0.0 % | dålig: bildfel, endast överkropp (A): inget golv eller kontakt, golv antaget, mall utelämnad: disk |
| s2 | 5.95/24.84 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 21.0 → 0.0 % | granska: endast överkropp (A): inget golv eller kontakt, golv antaget, mall utelämnad: disk |
| s3 | 7.61/33.70 | antagen, ±12.0 cm; spann 0.0 cm; skala 1,0 antagen | B: 32 i 42 rutor | 41.4 → 0.0 % | granska: golv antaget, mall utelämnad: disk |
| s4 | 2.59/19.45 | antagen, ±12.0 cm; spann 0.0 cm; skala 1,0 antagen | B: 32 i 70 rutor | 37.3 → 0.0 % | granska: golv antaget, mall utelämnad: disk |
| s5 | 8.38/46.14 | antagen, ±8.5 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | dålig: bildfel, endast överkropp (C): inget golv eller kontakt, golv antaget |
| s6 | 4.07/19.90 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 17.2 → 0.0 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: disk |
| s7 | 1.91/6.71 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 14.3 → 0.0 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: disk |
| s8 | 8.88/35.76 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 23.3 → 0.0 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: disk |
| s9 | 5.69/25.06 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 7.4 → 0.0 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: disk |
| s10 | 8.84/30.96 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 8.9 → 0.0 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: disk |
| s11 | 12.66/44.07 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 22.9 → 0.0 % | dålig: bildfel, endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: disk |

Antaget: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). Dessa möbelpriorer används bara vid vanligt bord, inte bardisk. En stilla handled behöver inte vila på bordet. Passningens rest mot handled och bäcken loggas, även när en höjd begränsas av priorn. Ingen kropp skalas för att passa en prior.

Skymning är provandel av källmask inom personrutan, med närmaste MHR70-punkts djup; ingen exakt hudarea. Var sjätte och sista rutan kontrolleras före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.
