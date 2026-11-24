# Kvalitet

Detta är egna diagnostiska trösklar: bildfel median 20 px/4 % av personhöjd, p90 40 px/8 %, led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal. Bra betyder att dessa kontroller passerar. Granska betyder osäkra antaganden eller konflikt. Dålig betyder att bildfelet passerar gränsen.

| Scen | Bildfel median/p90 px | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 4.28/5.99 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | granska: endast överkropp (A): inget golv eller kontakt, golv antaget |
| s2 | 2.41/5.83 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | granska: endast överkropp (B): inget golv eller kontakt, golv antaget |
| s3 | 3.47/6.00 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 24.1 → 0.0 % | granska: endast överkropp (B): inget golv eller kontakt, golv antaget, mall utelämnad: disk |
| s4 | 4.00/6.01 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | granska: endast överkropp (B): inget golv eller kontakt, golv antaget |
| s5 | 4.66/5.98 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 16.1 → 0.0 % | granska: endast överkropp (B): inget golv eller kontakt, golv antaget, mall utelämnad: disk |
| s7 | 3.62/5.90 | antagen, ±7.3 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 12.2 → 0.0 % | granska: endast överkropp (A): inget golv eller kontakt, golv antaget, mall utelämnad: disk |
| s6 | – | – | – | – | ej bedömd: scen utan person (bara kamera och rum, inga kroppar att mäta) |

Antaget: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). Dessa möbelpriorer används bara vid vanligt bord, inte bardisk. En stilla handled behöver inte vila på bordet. Passningens rest mot handled och bäcken loggas, även när en höjd begränsas av priorn. Ingen kropp skalas för att passa en prior.

Skymning är provandel av källmask inom personrutan, med närmaste MHR70-punkts djup; ingen exakt hudarea. Var sjätte och sista rutan kontrolleras före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.

## Skärmtext

9 tidsatta 2D-lager i källpixlar. Textinnehåll från sparad semantik; teckenmallar mäter plats och synlighet utan OCR. Fontval är närmaste installerade font. Konfidens avser teckenmatchning, inte sannolikheten att modellens text är rätt.

## Diskpassning

- servering_disk: höjd 0.850 m (antagen), rest -0.0931689984751991 m. Stilla handled är uppmätt; att handen vilar på disken är antaget. Prior 85–120 cm. Utan sådan cue behålls mallens 100 cm.
