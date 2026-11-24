# Kvalitet

Detta är egna diagnostiska trösklar, valda i förväg och inte justerade så att scener ska passera: avvikelse från estimatorns 2D median 20 px/4 % av personhöjd, p90 40 px/8 %, led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal; kroppsmåtten nedan. Bra betyder att alla kontroller passerar. Granska betyder osäkra antaganden, konflikt, darr, låg täckning eller svag oberoende matchning. Dålig betyder att en oberoende gräns (silhuett, tyngdpunkt, darr) är tydligt passerad; avvikelsen från estimatorns 2D ger bara granska, eftersom den inte är oberoende och domineras av fingerleder (42 av de 48 mätta punkterna). **En scen kan aldrig bli bättre än granska på avvikelsen från estimatorns 2D ensam.** Den siffran är inte oberoende: estimatorn passas mot samma 2D-punkter som mäts, och om bildskyddet (äldre ingest) har blandat tillbaka råposen ligger p90 vid gränsen 6 px av konstruktion. Den oberoende kontrollen är silhuett-IoU mot YOLO-masken.

| Scen | Avvikelse från estimatorns 2D median/p90 px (ej oberoende) | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 15.73/48.50 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | granska: avvikelse från estimatorns 2D över gränsen (ej oberoende; mest fingerleder; räknas som granska), endast överkropp (A): inget golv eller kontakt, golv antaget, A: tyngdpunkt p90 4.3 % av bildhöjden |
| s2 | 7.96/24.36 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | granska: endast överkropp (A): inget golv eller kontakt, golv antaget, A: tyngdpunkt p90 3.5 % av bildhöjden |
| s3 | 7.88/21.10 | antagen, ±12.0 cm; spann 0.0 cm; skala 1,0 antagen | B: 32 i 42 rutor | 0.0 → 0.0 % | granska: golv antaget |
| s4 | 2.67/13.03 | antagen, ±12.0 cm; spann 0.0 cm; skala 1,0 antagen | B: 32 i 70 rutor | 0.0 → 0.0 % | granska: golv antaget |
| s5 | 9.29/30.98 | antagen, ±8.5 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | dålig: endast överkropp (C): inget golv eller kontakt, golv antaget, C: tyngdpunkt p90 9.0 % av bildhöjden, C: darr 2.71 cm/ruta² |
| s6 | 5.71/20.74 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 10.2 → 0.7 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: disk:skiva, monter:tak |
| s7 | 3.06/7.16 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 7.1 → 1.5 % | granska: endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: monter:tak |
| s8 | 11.69/29.61 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.2 → 0.2 % | dålig: endast överkropp (C): inget golv eller kontakt, golv antaget, C: silhuett-IoU 0.64 < 0.65, C: tyngdpunkt p90 7.0 % av bildhöjden |
| s9 | 6.41/18.72 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 0.0 → 0.0 % | dålig: endast överkropp (C): inget golv eller kontakt, golv antaget, C: silhuett-IoU 0.60 < 0.65, C: tyngdpunkt p90 10.4 % av bildhöjden |
| s10 | 11.43/21.90 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 1.1 → 1.1 % | dålig: endast överkropp (C): inget golv eller kontakt, golv antaget, C: silhuett-IoU 0.56 < 0.65, C: tyngdpunkt p90 10.4 % av bildhöjden, C: darr 1.69 cm/ruta² |
| s11 | 12.96/40.68 | antagen, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | 0 | 5.3 → 0.0 % | dålig: avvikelse från estimatorns 2D över gränsen (ej oberoende; mest fingerleder; räknas som granska), endast överkropp (C): inget golv eller kontakt, golv antaget, mall utelämnad: disk:skiva, disk:bakpanel, monter:tak, C: silhuett-IoU 0.63 < 0.65, C: tyngdpunkt p90 7.0 % av bildhöjden |

## Kropp: oberoende mått, darr och täckning

Silhuett: kroppsmodellens hudnät skinnat med de byggda lederna, projicerat i den spårade kameran, mot YOLO11-seg-masken (en annan modell än kroppsestimatorn), inom personens egen spårruta, på ALLA rutor där masken finns (även opålitliga). IoU `synlig` klipper nätet vid maskens nedersta rad (skymmande disk/bord). Tyngdpunktsfel i andel av bildhöjden. **Skevhet:** masken har kläder, hår och hållna föremål som kroppen saknar och kan sakna fingrar; estimatorns egna hörn mot samma mask ger referens-IoU (kolumn ref); IoU under ref är alltså inte automatiskt fel. Hudnätet är lod1 (renderingen använder lod3, samma kropp) utan korrigerande blendshapes (< 2 cm lokalt).
Darr: medel andra differens av ledpositionerna (127 leder, planens värld, cm/ruta²) för byggd pose, stabiliserad pose före golv/kontakt/stöd, och estimatorns råa pose med råa cam_t. Råa är skakigare än filmen får vara; byggd över 1.5 = granska, över 3.0 = dålig (våra val). Andel = hur stor del av den stabiliserade posen som överlevde äldre bildskydd (– = inget bildskydd, ny metod).
Täckning: rutor där avvikelsen från estimatorns 2D kunde bedömas / rutor i scenen. Orsaker till uteblivna rutor: ej i bild (personen ej spårad), opålitlig (under 35 % av kroppspunkterna i bild eller 15 % i masken: estimatorn gissar), rådata saknas. Under 60% = granska.
Gränser (våra, inga ägarkrav): IoU synlig bra ≥ 0.65, dålig < 0.5; tyngdpunkt p90 > 3 % granska, > 6 % dålig.

| Scen | Person | IoU / IoU synlig / ref (median) | Tyngdpunkt median/p90 (% bildhöjd) | Mask-rutor | Darr byggd / stabil / rå | Andel | Täckning (bedömda/rutor) | Utelämnade: ej i bild / opålitliga / rådata saknas |
|---|---|---|---|---|---|---|---|---|
| s1 | A | 0.78 / 0.78 / 0.79 | 1.7 / 4.3 | 50 av 50 | 0.97 / 0.97 / 3.40 | – | 50 av 50 | 0 / 0 / 0 |
| s2 | A | 0.79 / 0.79 / 0.80 | 2.9 / 3.5 | 51 av 51 | 0.82 / 0.82 / 2.14 | – | 51 av 52 | 1 / 0 / 0 |
| s3 | B | 0.80 / 0.80 / 0.80 | 0.5 / 1.3 | 42 av 42 | 1.01 / 0.88 / 2.51 | – | 42 av 42 | 0 / 0 / 0 |
| s4 | B | 0.79 / 0.79 / 0.80 | 1.2 / 1.8 | 70 av 70 | 0.67 / 0.61 / 1.61 | – | 70 av 72 | 2 / 0 / 0 |
| s5 | C | 0.63 / 0.66 / 0.63 | 5.6 / 9.0 | 46 av 46 | 2.71 / 2.71 / 7.00 | – | 46 av 46 | 0 / 0 / 0 |
| s6 | C | 0.78 / 0.82 / 0.76 | 1.9 / 2.0 | 32 av 32 | 0.51 / 0.51 / 2.05 | – | 32 av 32 | 0 / 0 / 0 |
| s7 | C | 0.78 / 0.82 / 0.76 | 1.6 / 1.9 | 26 av 26 | 0.36 / 0.36 / 1.04 | – | 26 av 26 | 0 / 0 / 0 |
| s8 | C | 0.61 / 0.64 / 0.60 | 5.8 / 7.0 | 20 av 20 | 1.16 / 1.16 / 3.53 | – | 20 av 20 | 0 / 0 / 0 |
| s9 | C | 0.58 / 0.60 / 0.58 | 7.6 / 10.4 | 35 av 35 | 0.84 / 0.84 / 1.88 | – | 34 av 35 | 0 / 1 / 0 |
| s10 | C | 0.53 / 0.56 / 0.55 | 7.0 / 10.4 | 46 av 49 | 1.69 / 1.69 / 4.67 | – | 46 av 49 | 0 / 0 / 3 |
| s11 | C | 0.62 / 0.63 / 0.61 | 5.6 / 7.0 | 43 av 43 | 0.90 / 0.90 / 4.29 | – | 43 av 46 | 3 / 0 / 0 |

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
| s8 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s9 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s10 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s11 | 0.00 | 0.00 / 0.00 | ja | uppmatt |

Antaget: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). Dessa möbelpriorer används bara vid vanligt bord, inte bardisk. En stilla handled behöver inte vila på bordet. Passningens rest mot handled och bäcken loggas, även när en höjd begränsas av priorn. Ingen kropp skalas för att passa en prior.

Skymning är provandel av källmask inom personrutan, med närmaste MHR70-punkts djup; ingen exakt hudarea. Var tredje och sista rutan kontrolleras (före 10 nov var sjätte). Varje kroppsdel har egen gräns, 10 % av delens maskprov (minst 8), så att tunna skenor över höften syns även när de är << 2 % av alla prov före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.

## Skärmtext

81 tidsatta 2D-lager i källpixlar. Textinnehåll från sparad semantik; teckenmallar mäter plats och synlighet utan OCR. Fontval är närmaste installerade font. Konfidens avser teckenmatchning, inte sannolikheten att modellens text är rätt.

## Diskpassning

- chark_disk: höjd 1.000 m (mall), rest None m. Mallhöjd 100 cm. Stilla handleder håller kött och verifierar inte kontakt med disken. Kamerans/personens höjd passas gemensamt mot avläst diskkant.
