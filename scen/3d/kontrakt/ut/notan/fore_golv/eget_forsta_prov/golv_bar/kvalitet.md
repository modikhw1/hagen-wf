# Kvalitet

Detta är egna diagnostiska trösklar: bildfel median 20 px/4 % av personhöjd, p90 40 px/8 %, led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal. Bra betyder att dessa kontroller passerar. Granska betyder osäkra antaganden eller konflikt. Dålig betyder att bildfelet passerar gränsen.

| Scen | Bildfel median/p90 px | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 15.11/26.82 | antagen, ±14.7 cm; spann 28.9 cm; skala 1,0 antagen; golv endast granskat | 0 | 0.0 → 0.0 % | granska: golv antaget, golvcues oense |

Antaget: bord 72–76 cm, sits 43–48 cm, bäcken över sits 7–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). En stilla handled behöver inte vila på bordet. Möbelpassningen får avvika från vanliga intervall när fasta uppmätta kroppar kräver det; avvikelsen loggas i planens höjdpassning. Ingen kropp skalas för att passa en prior.

Skymning är provandel av källmask inom personrutan, med närmaste MHR70-punkts djup; ingen exakt hudarea. Var sjätte och sista rutan kontrolleras före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.
