# Återskapning 1:1 vid ingest (0035)

Generativ video används bara för att återskapa originalet så likt som möjligt (ägarens besked 13 nov). Den här filen säger vad "likt" betyder, vilka vägar som finns och vad som är prövat.

## Vad 1:1 betyder (kedjans kontroll, `h_kontroll.py`, `h2_extra.py`, `t_tid.py`)
1. **Synliga leder mot originalet:** överkroppens leder projicerade i originalets rutor, i promille av bildhöjden (median och p90).
2. **Hela kroppen i bild:** andelen rutor där hela kroppen syns, och rutorna där huvudet är avskuret.
3. **Tid:** vändpunkterna (handen lägst, armen längst fram) mot källan, efter tidspassningen, i rutor; samt rotens hopp.
4. **Kameran står still** där källan är kamerafri: fotlinjens glidning i px.
5. **Inga påhittade föremål eller personer:** kontrolleras för ögat i remsan (inget mått än).

## Vägarna

| Väg | Video som rörelsereferens | Nyckelbilder på tid | Mask | Exakt längd | Åtkomst | Pris per 5 s | Licens för resultatet |
|---|---|---|---|---|---|---|---|
| **Dreamina / Seedance 2.0** | ja ("Universell referens", upp till 12 referenser) | bara som referenser | nej | nej (5, 8, 10 s) | webbapp för hand; API via BytePlus ModelArk ([guide](https://www.nxcode.io/resources/news/seedance-2-0-api-guide-pricing-setup-2026)) | återförsäljare cirka 0,02–0,25 USD/s | kommersiellt enligt plan |
| **Luma Ray 3.2** (fal) | ja, video-till-video | ja, upp till 64 på tid | nej | ja | API (fal) | cirka 0,15 USD (540p) | kommersiellt |
| **Kling 3.0 Motion Control** ([priser](https://dev.to/evan-dong/kling-ai-video-generation-pricing-complete-cost-breakdown-for-developers-2026-3fnp)) | ja (rörelse ur video på en karaktärsbild) | startbild | nej | ja (upp till 10–30 s) | API | cirka 0,13–0,17 USD/s | kommersiellt enligt plan |
| **Runway Act-Two** ([spec](https://www.cometapi.com/models/runway/act-two/)) och **Aleph** | ja: framförande + karaktärsreferens; Aleph = video till video | karaktärsbild | nej | ja (3–30 s) | API (via återförsäljare) | cirka 0,30 USD (v2v) | kommersiellt |
| **Wan 2.2 Animate / VACE** | ja (Animate: rörelse + karaktär; Replace behåller scen och kamera) | ja (VACE) | ja (VACE) | ja | öppen modell, Apache-2.0; måste hostas (ägaren har sagt nej till egen hosting på Modal) eller nås via en tjänst | tjänstens pris | Apache-2.0 |

**Bedömning:** för 1:1 är det avgörande att längden och tiden blir exakta och att skymda delar inte hittas på. Ray 3.2 och Kling har exakt längd, och Ray har nyckelbilder på tid, alltså bäst styrning; Dreamina ger bäst helkropp och lutning (0026), men drar ut tiden och skär huvudet. Wan VACE med mask är det mest kontrollerbara, men faller på kravet att inte hosta själv, om inte en tjänst erbjuder VACE med mask.

## Prövat (gelato S1; omgång 2 och guacamole S1 väntar på ägaren)

| Generering | Hela kroppen | Överkropp median / p90 (promille) | Rotens största hopp | Huvud avskuret | Tid |
|---|---|---|---|---|---|
| a (Ray, startbild) | 48/148 | 15,8 / 61,6 | 4 cm | – | exakt |
| k (Ray, kamerafri) | 148/148 | 14,8 / 79,7 | 2 cm | – | exakt |
| k2 (Ray, originalets pixlar) | 124/148 | 15,9 / 57,0 | 4 cm | – | exakt |
| Dreamina (tidspassad) | 148/148 | 22,0 / 63,9 | 13 cm | källrutorna 22–69 (43) | 193 → 148 rutor (DTW) |
| Dreamina genom kedjan (0030) | 148/148 | 22,1 / 63,9 | 13 cm | samma | samma |

**Huvudet:** den kamerafria källan har alltid huvudet inne i bilden (minst 330 px från kanten, `kamerafri/huvudmarginal.json`). I k2-källan, där originalets pixlar följer med, skär originalets överkant huvudet i källrutorna 58–77 (`kamerafri/kanten_skar_huvudet.json`). Dreamina skar 22–69. Generatorn ärver alltså kanten, och skär dessutom själv när hon lutar sig mot kameran. Ett paket med huvudrum finns i `d_video/dreamina-paket/omgang3_huvudrum/`: källan skalad till 82 % med fötterna fasta, och en rad i prompten.
