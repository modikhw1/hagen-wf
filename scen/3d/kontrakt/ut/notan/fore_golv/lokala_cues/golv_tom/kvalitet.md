# Kvalitet

Detta är egna diagnostiska trösklar: bildfel median 20 px/4 % av personhöjd, p90 40 px/8 %, led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal. Bra betyder att dessa kontroller passerar. Granska betyder osäkra antaganden eller konflikt. Dålig betyder att bildfelet passerar gränsen.

| Scen | Bildfel median/p90 px | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 1.40/4.11 | antagen, ±27.4 cm; spann 20.2 cm; skala 1,0 antagen | A: 32 i 73 rutor | 0.3 → 0.3 % | granska: golv antaget, golvcues oense, skalprior oense |
| s2 | 2.09/13.98 | antagen, ±16.4 cm; spann 14.6 cm; skala 1,0 antagen | B: 32 i 41 rutor | 0.0 → 0.0 % | granska: golv antaget, golvcues oense, skalprior oense |
| s3 | 1.69/19.12 | antagen, ±13.7 cm; spann 6.4 cm; skala 1,0 antagen | A: 32 i 57 rutor | 0.0 → 0.0 % | granska: golv antaget, skalprior oense |
| s4 | 0.87/4.18 | antagen, ±12.8 cm; spann 30.1 cm; skala 1,0 antagen | C: 20 i 85 rutor | 9.2 → 0.0 % | granska: golv antaget, golvcues oense, skalprior oense, mall utelämnad: bord_A |
| s5 | 2.92/9.92 | antagen, ±16.4 cm; spann 14.8 cm; skala 1,0 antagen | B: 32 i 25 rutor | 0.0 → 0.0 % | granska: golv antaget, golvcues oense, skalprior oense |
| s6 | 19.89/68.40 | antagen, ±14.9 cm; spann 27.7 cm; skala 1,0 antagen | A: 32 i 56 rutor | 0.0 → 0.0 % | dålig: bildfel, golv antaget, golvcues oense, skalprior oense |
| s7 | 2.00/4.88 | antagen, ±13.2 cm; spann 8.5 cm; skala 1,0 antagen | B: 32 i 46 rutor | 0.0 → 0.0 % | granska: golv antaget, skalprior oense |

Antaget: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). Dessa möbelpriorer används bara vid vanligt bord, inte bardisk. En stilla handled behöver inte vila på bordet. Passningens rest mot handled och bäcken loggas, även när en höjd begränsas av priorn. Ingen kropp skalas för att passa en prior.

Skymning är provandel av källmask inom personrutan, med närmaste MHR70-punkts djup; ingen exakt hudarea. Var sjätte och sista rutan kontrolleras före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.
