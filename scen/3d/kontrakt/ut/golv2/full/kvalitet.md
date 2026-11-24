# Kvalitet

Detta är egna diagnostiska trösklar, valda i förväg och inte justerade så att scener ska passera: avvikelse från estimatorns 2D median 20 px/4 % av personhöjd, p90 40 px/8 %, led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal; kroppsmåtten nedan. Bra betyder att alla kontroller passerar. Granska betyder osäkra antaganden, konflikt, darr, låg täckning eller svag oberoende matchning. Dålig betyder att en oberoende gräns (silhuett, tyngdpunkt, darr) är tydligt passerad; avvikelsen från estimatorns 2D ger bara granska, eftersom den inte är oberoende och domineras av fingerleder (42 av de 48 mätta punkterna). **En scen kan aldrig bli bättre än granska på avvikelsen från estimatorns 2D ensam.** Den siffran är inte oberoende: estimatorn passas mot samma 2D-punkter som mäts, och om bildskyddet (äldre ingest) har blandat tillbaka råposen ligger p90 vid gränsen 6 px av konstruktion. Den oberoende kontrollen är silhuett-IoU mot YOLO-masken.

| Scen | Avvikelse från estimatorns 2D median/p90 px (ej oberoende) | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 1.98/6.00 | antagen, ±9.0 cm; spann 48.7 cm; skala 1,0 antagen | A: 32 i 73 rutor | 0.0 → 0.0 % | granska: golv antagen, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., golvcues oense, skalprior oense, A: tyngdpunkt p90 5.7 % av bildhöjden |
| s2 | 3.64/14.54 | antagen, ±9.0 cm; spann 14.7 cm; skala 1,0 antagen | B: 32 i 41 rutor | 0.0 → 0.0 % | dålig: golv antagen, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., golvcues oense, skalprior oense, B: tyngdpunkt p90 6.1 % av bildhöjden |
| s3 | 2.10/22.27 | antagen, ±9.0 cm; spann 27.9 cm; skala 1,0 antagen | A: 32 i 57 rutor | 0.0 → 0.0 % | granska: golv antagen, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., golvcues oense, skalprior oense, A: tyngdpunkt p90 4.7 % av bildhöjden |
| s4 | 1.09/4.55 | modellbedomd, ±3.0 cm; spann 29.1 cm; skala 1,0 antagen | C: 20 i 85 rutor | 4.8 → 0.0 % | granska: golv modellbedomd, golvcues oense, skalprior oense, mall utelämnad: bord_A |
| s5 | 3.69/11.26 | antagen, ±9.0 cm; spann 7.1 cm; skala 1,0 antagen | B: 32 i 25 rutor | 0.0 → 0.0 % | granska: golv antagen, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., skalprior oense, B: tyngdpunkt p90 5.6 % av bildhöjden |
| s6 | 20.40/62.31 | antagen, ±9.0 cm; spann 50.5 cm; skala 1,0 antagen | A: 32 i 56 rutor | 0.0 → 0.0 % | granska: avvikelse från estimatorns 2D över gränsen (ej oberoende; mest fingerleder; räknas som granska), golv antagen, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., golvcues oense, skalprior oense, A: tyngdpunkt p90 5.1 % av bildhöjden |
| s7 | 1.53/3.60 | antagen, ±9.0 cm; spann 12.7 cm; skala 1,0 antagen | B: 32 i 46 rutor | 1.9 → 0.0 % | granska: golv antagen, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., golvcues oense, skalprior oense, mall utelämnad: stol_B, B: silhuett-IoU 0.61 < 0.65 |

## GOLV2: kropp och rum

Kroppens kameraposition bevaras. Synlig fot är modellbedömd kontakt, inte fysisk inmätning. Dolda fötter styr inte golvet.

| Scen/person | Kamera över golv m | Kamera till rumskamera m | Modellfotrest m | Synlig fotrest m | Kontakt |
|---|---:|---:|---:|---:|---|
| s1/1 | 1.605 | 0.000000 | -0.130 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s2/1 | 1.625 | 0.000000 | -0.170 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s3/1 | 1.577 | 0.000000 | -0.114 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s4/1 | 1.600 | 0.000000 | 0.168 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s4/4 | 1.600 | 0.000000 | 0.025 | 0.025 | modellbedomd;  |
| s5/1 | 1.407 | 0.000000 | -0.168 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s6/1 | 1.572 | 0.000000 | -0.108 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s7/1 | 1.605 | 0.000000 | -0.230 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |

## Kropp: oberoende mått, darr och täckning

Silhuett: kroppsmodellens hudnät skinnat med de byggda lederna, projicerat i den spårade kameran, mot YOLO11-seg-masken (en annan modell än kroppsestimatorn), inom personens egen spårruta, på ALLA rutor där masken finns (även opålitliga). IoU `synlig` klipper nätet vid maskens nedersta rad (skymmande disk/bord). Tyngdpunktsfel i andel av bildhöjden. **Skevhet:** masken har kläder, hår och hållna föremål som kroppen saknar och kan sakna fingrar; estimatorns egna hörn mot samma mask ger referens-IoU (kolumn ref); IoU under ref är alltså inte automatiskt fel. Hudnätet är lod1 (renderingen använder lod3, samma kropp) utan korrigerande blendshapes (< 2 cm lokalt).
Darr: medel andra differens av ledpositionerna (127 leder, planens värld, cm/ruta²) för byggd pose, stabiliserad pose före golv/kontakt/stöd, och estimatorns råa pose med råa cam_t. Råa är skakigare än filmen får vara; byggd över 1.5 = granska, över 3.0 = dålig (våra val). Andel = hur stor del av den stabiliserade posen som överlevde äldre bildskydd (– = inget bildskydd, ny metod).
Täckning: rutor där avvikelsen från estimatorns 2D kunde bedömas / rutor i scenen. Orsaker till uteblivna rutor: ej i bild (personen ej spårad), opålitlig (under 35 % av kroppspunkterna i bild eller 15 % i masken: estimatorn gissar), rådata saknas. Under 60% = granska.
Gränser (våra, inga ägarkrav): IoU synlig bra ≥ 0.65, dålig < 0.5; tyngdpunkt p90 > 3 % granska, > 6 % dålig.

| Scen | Person | IoU / IoU synlig / ref (median) | Tyngdpunkt median/p90 (% bildhöjd) | Mask-rutor | Darr byggd / stabil / rå | Andel | Täckning (bedömda/rutor) | Utelämnade: ej i bild / opålitliga / rådata saknas |
|---|---|---|---|---|---|---|---|---|
| s1 | A | 0.65 / 0.68 / 0.62 | 4.5 / 5.7 | 73 av 73 | 0.29 / 0.32 / 0.90 | – | 73 av 73 | 0 / 0 / 0 |
| s2 | B | 0.62 / 0.65 / 0.61 | 5.8 / 6.1 | 41 av 41 | 0.47 / 0.48 / 1.28 | – | 41 av 41 | 0 / 0 / 0 |
| s3 | A | 0.67 / 0.71 / 0.65 | 4.5 / 4.7 | 57 av 57 | 0.44 / 0.46 / 1.07 | – | 57 av 57 | 0 / 0 / 0 |
| s4 | C | 0.74 / 0.74 / 0.75 | 1.3 / 1.5 | 85 av 85 | 0.34 / 0.34 / 0.65 | – | 85 av 85 | 0 / 0 / 0 |
| s5 | B | 0.64 / 0.68 / 0.64 | 5.1 / 5.6 | 25 av 25 | 0.44 / 0.47 / 1.20 | – | 25 av 25 | 0 / 0 / 0 |
| s6 | A | 0.65 / 0.70 / 0.65 | 4.7 / 5.1 | 56 av 56 | 0.40 / 0.42 / 3.38 | – | 56 av 56 | 0 / 0 / 0 |
| s7 | B | 0.60 / 0.61 / 0.59 | 2.0 / 2.7 | 46 av 46 | 0.96 / 1.03 / 2.92 | – | 46 av 46 | 0 / 0 / 0 |

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

7 tidsatta 2D-lager i källpixlar. Textinnehåll från sparad semantik; teckenmallar mäter plats och synlighet utan OCR. Fontval är närmaste installerade font. Konfidens avser teckenmatchning, inte sannolikheten att modellens text är rätt.

## Diskpassning

- notan_tva_bord: höjd 0.760 m (antagen), rest 0.0713770706494895 m. Stilla handled är uppmätt, bordkontakt antagen. Klippt mot bordprior 72–76 cm; rest mot handled loggas. Händer och bäcken flyttas aldrig.
- notan_tva_bord: höjd 0.760 m (antagen), rest 0.1268408542943784 m. Stilla handled är uppmätt, bordkontakt antagen. Klippt mot bordprior 72–76 cm; rest mot handled loggas. Händer och bäcken flyttas aldrig.
