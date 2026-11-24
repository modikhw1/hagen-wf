# Kvalitet

Detta är egna diagnostiska trösklar, valda i förväg och inte justerade så att scener ska passera: avvikelse från estimatorns 2D median 20 px/4 % av personhöjd, p90 40 px/8 %, led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal; kroppsmåtten nedan. Bra betyder att alla kontroller passerar. Granska betyder osäkra antaganden, konflikt, darr, låg täckning eller svag oberoende matchning. Dålig betyder att en oberoende gräns (silhuett, tyngdpunkt, darr) är tydligt passerad; avvikelsen från estimatorns 2D ger bara granska, eftersom den inte är oberoende och domineras av fingerleder (42 av de 48 mätta punkterna). **En scen kan aldrig bli bättre än granska på avvikelsen från estimatorns 2D ensam.** Den siffran är inte oberoende: estimatorn passas mot samma 2D-punkter som mäts, och om bildskyddet (äldre ingest) har blandat tillbaka råposen ligger p90 vid gränsen 6 px av konstruktion. Den oberoende kontrollen är silhuett-IoU mot YOLO-masken.

| Scen | Avvikelse från estimatorns 2D median/p90 px (ej oberoende) | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 15.63/44.08 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | dålig: avvikelse från estimatorns 2D över gränsen (ej oberoende; mest fingerleder; räknas som granska), endast överkropp (A): inget golv eller kontakt, golv antaget, A: tyngdpunkt p90 4.1 % av bildhöjden, A: darr 4.41 cm/ruta² |
| s2 | 4.45/11.89 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.1 → 0.1 % | granska: endast överkropp (B): inget golv eller kontakt, golv antaget |
| s3 | 10.50/31.79 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 28.2 → 0.1 % | granska: endast överkropp (B): inget golv eller kontakt, golv antaget, mall utelämnad: disk:bakpanel, disk:skiva, B: tyngdpunkt p90 3.9 % av bildhöjden, B: passningen bedömd på 19 av 152 rutor |
| s4 | 15.66/37.17 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | granska: endast överkropp (B): inget golv eller kontakt, golv antaget, B: tyngdpunkt p90 4.8 % av bildhöjden, B: darr 1.59 cm/ruta² |
| s5 | 13.83/29.28 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 17.9 → 0.0 % | dålig: endast överkropp (B): inget golv eller kontakt, golv antaget, mall utelämnad: disk:skiva, disk:bakpanel, B: silhuett-IoU 0.62 < 0.65, B: tyngdpunkt p90 6.3 % av bildhöjden, B: darr 1.66 cm/ruta² |
| s7 | 13.88/34.41 | antagen, ±7.3 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 12.4 → 0.0 % | dålig: endast överkropp (A): inget golv eller kontakt, golv antaget, mall utelämnad: disk:skiva, disk:framkant, disk:bakpanel, A: silhuett-IoU 0.60 < 0.65, A: tyngdpunkt p90 7.3 % av bildhöjden, A: darr 1.87 cm/ruta² |
| s6 | – | – | – | – | ej bedömd: scen utan person (bara kamera och rum, inga kroppar att mäta) |

## Kropp: oberoende mått, darr och täckning

Silhuett: kroppsmodellens hudnät skinnat med de byggda lederna, projicerat i den spårade kameran, mot YOLO11-seg-masken (en annan modell än kroppsestimatorn), inom personens egen spårruta, på ALLA rutor där masken finns (även opålitliga). IoU `synlig` klipper nätet vid maskens nedersta rad (skymmande disk/bord). Tyngdpunktsfel i andel av bildhöjden. **Skevhet:** masken har kläder, hår och hållna föremål som kroppen saknar och kan sakna fingrar; estimatorns egna hörn mot samma mask ger referens-IoU (kolumn ref); IoU under ref är alltså inte automatiskt fel. Hudnätet är lod1 (renderingen använder lod3, samma kropp) utan korrigerande blendshapes (< 2 cm lokalt).
Darr: medel andra differens av ledpositionerna (127 leder, planens värld, cm/ruta²) för byggd pose, stabiliserad pose före golv/kontakt/stöd, och estimatorns råa pose med råa cam_t. Råa är skakigare än filmen får vara; byggd över 1.5 = granska, över 3.0 = dålig (våra val). Andel = hur stor del av den stabiliserade posen som överlevde äldre bildskydd (– = inget bildskydd, ny metod).
Täckning: rutor där avvikelsen från estimatorns 2D kunde bedömas / rutor i scenen. Orsaker till uteblivna rutor: ej i bild (personen ej spårad), opålitlig (under 35 % av kroppspunkterna i bild eller 15 % i masken: estimatorn gissar), rådata saknas. Under 60% = granska.
Gränser (våra, inga ägarkrav): IoU synlig bra ≥ 0.65, dålig < 0.5; tyngdpunkt p90 > 3 % granska, > 6 % dålig.

| Scen | Person | IoU / IoU synlig / ref (median) | Tyngdpunkt median/p90 (% bildhöjd) | Mask-rutor | Darr byggd / stabil / rå | Andel | Täckning (bedömda/rutor) | Utelämnade: ej i bild / opålitliga / rådata saknas |
|---|---|---|---|---|---|---|---|---|
| s1 | A | 0.70 / 0.73 / 0.68 | 2.9 / 4.1 | 59 av 60 | 4.41 / 4.41 / 9.36 | – | 59 av 60 | 0 / 0 / 1 |
| s2 | B | 0.76 / 0.81 / 0.75 | 2.3 / 2.9 | 78 av 78 | 0.92 / 0.92 / 1.87 | – | 78 av 79 | 1 / 0 / 0 |
| s3 | B | 0.72 / 0.72 / 0.71 | 3.2 / 3.9 | 34 av 34 | 0.78 / 0.78 / 3.23 | – | 19 av 152 | 118 / 15 / 0 |
| s4 | B | 0.74 / 0.74 / 0.72 | 2.3 / 4.8 | 216 av 216 | 1.59 / 1.59 / 3.79 | – | 143 av 216 | 0 / 73 / 0 |
| s5 | B | 0.60 / 0.62 / 0.57 | 4.6 / 6.3 | 83 av 83 | 1.66 / 1.66 / 4.37 | – | 54 av 83 | 0 / 29 / 0 |
| s7 | A | 0.58 / 0.60 / 0.57 | 5.5 / 7.3 | 62 av 64 | 1.87 / 1.87 / 5.92 | – | 62 av 64 | 0 / 0 / 2 |

## Kamerabana

Den metriska kamerabanan som bärs in i bygget (`varld.npz`) kontrolleras mot vad en handhållen mobil kan göra inomhus: p90-fart ≤ 5.0 m/s, maxfart ≤ 15.0 m/s, sträcka ≤ 5.0 m/s × scenens längd (våra gränser). En orimlig bana betyder nästan alltid att COLMAP-skalan inte är bestämd (kenny S2 hade 11,7 km). Avvisad skala = translationen är nollad och bara rotationen används.

| Scen | Bana (m) | p90 / max fart (m/s) | Rimlig | Skalbeslut vid ingest |
|---|---|---|---|---|
| s1 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s2 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s3 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s4 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s5 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s6 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s7 | 0.00 | 0.00 / 0.00 | ja | uppmatt |

Antaget: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). Dessa möbelpriorer används bara vid vanligt bord, inte bardisk. En stilla handled behöver inte vila på bordet. Passningens rest mot handled och bäcken loggas, även när en höjd begränsas av priorn. Ingen kropp skalas för att passa en prior.

Skymning är provandel av källmask inom personrutan, med närmaste MHR70-punkts djup; ingen exakt hudarea. Var tredje och sista rutan kontrolleras (före 10 nov var sjätte). Varje kroppsdel har egen gräns, 10 % av delens maskprov (minst 8), så att tunna skenor över höften syns även när de är << 2 % av alla prov före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.

## Skärmtext

9 tidsatta 2D-lager i källpixlar. Textinnehåll från sparad semantik; teckenmallar mäter plats och synlighet utan OCR. Fontval är närmaste installerade font. Konfidens avser teckenmatchning, inte sannolikheten att modellens text är rätt.

## Diskpassning

- servering_disk: höjd 0.850 m (antagen), rest -0.0931689984751991 m. Stilla handled är uppmätt; att handen vilar på disken är antaget. Prior 85–120 cm. Utan sådan cue behålls mallens 100 cm.
