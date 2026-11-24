# Kvalitet

Detta är egna diagnostiska trösklar, valda i förväg och inte justerade så att scener ska passera: slutkamerans medeloffset 3 % av bildhöjden, skalfaktor 0,85–1,15 och led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal; kroppsmåtten nedan. Slutbildsmåttet projicerar samma leder genom kameran som Blender renderar med. Det är inte oberoende av kroppsestimatorn, men till skillnad från ingestkameramåttet ser det ändrad inramning. Den oberoende kontrollen är silhuett-IoU mot YOLO-masken.

| Scen | Slutkamera: medel px / % höjd / skala / IoU | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 22.77 / 2.22 % / 1.008 / 0.908 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | A: 32 i 50 rutor | 0.0 → 0.0 % | granska: endast överkropp (A): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., A: tyngdpunkt p90 4.3 % av bildhöjden |
| s2 | 12.01 / 1.17 % / 0.999 / 0.952 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | A: 32 i 51 rutor | 0.7 → 0.7 % | granska: endast överkropp (A): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., A: tyngdpunkt p90 3.4 % av bildhöjden |
| s3 | 10.74 / 1.05 % / 1.006 / 0.951 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | B: 32 i 42 rutor | 0.0 → 0.0 % | granska: golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt. |
| s4 | 5.12 / 0.50 % / 1.000 / 0.979 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | B: 32 i 70 rutor | 0.0 → 0.0 % | granska: golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt. |
| s5 | 13.43 / 1.31 % / 1.011 / 0.921 | deklarerad, ±8.5 cm; spann 0.0 cm; skala 1,0 antagen | C: 32 i 46 rutor | 36.3 → 36.3 % | dålig: endast överkropp (C): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., mall utelämnad: disk_C, skymningsrest, C: tyngdpunkt p90 9.1 % av bildhöjden, C: darr 3.08 cm/ruta² |
| s6 | 8.40 / 0.82 % / 0.998 / 0.966 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | C: 32 i 32 rutor | 85.2 → 85.2 % | granska: endast överkropp (C): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., mall utelämnad: disk_C, skymningsrest |
| s7 | 4.30 / 0.42 % / 1.000 / 0.983 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | C: 32 i 26 rutor | 86.9 → 86.9 % | granska: endast överkropp (C): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., mall utelämnad: disk_C, skymningsrest |
| s8 | 15.21 / 1.49 % / 1.003 / 0.944 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | C: 32 i 20 rutor | 51.5 → 51.5 % | dålig: endast överkropp (C): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., mall utelämnad: disk_C, skymningsrest, C: silhuett-IoU 0.64 < 0.65, C: tyngdpunkt p90 7.1 % av bildhöjden |
| s9 | 10.48 / 1.02 % / 1.000 / 0.966 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | C: 32 i 35 rutor | 69.3 → 69.3 % | dålig: endast överkropp (C): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., mall utelämnad: disk_C, skymningsrest, C: silhuett-IoU 0.60 < 0.65, C: tyngdpunkt p90 10.5 % av bildhöjden |
| s10 | 12.60 / 1.23 % / 1.002 / 0.876 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | C: 32 i 49 rutor | 32.7 → 32.7 % | dålig: endast överkropp (C): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., mall utelämnad: disk_C, skymningsrest, C: silhuett-IoU 0.56 < 0.65, C: tyngdpunkt p90 10.4 % av bildhöjden |
| s11 | 18.99 / 1.85 % / 1.002 / 0.945 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | C: 32 i 43 rutor | 72.5 → 72.5 % | dålig: endast överkropp (C): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., mall utelämnad: disk_C, skymningsrest, C: silhuett-IoU 0.63 < 0.65, C: tyngdpunkt p90 6.9 % av bildhöjden |

## GOLV2: kropp och rum

Kroppens kameraposition bevaras. Synlig fot är modellbedömd kontakt, inte fysisk inmätning. Dolda fötter styr inte golvet.

| Scen/person | Kamera över golv m | Kamera till rumskamera m | Modellfotrest m | Synlig fotrest m | Kontakt |
|---|---:|---:|---:|---:|---|
| s1/1 | 1.400 | 0.000000 | 0.068 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s2/1 | 1.400 | 0.000000 | 0.073 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s3/1 | 1.400 | 0.000000 | 0.068 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s4/1 | 1.400 | 0.000000 | 0.092 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s5/1 | 1.400 | 0.000000 | 0.102 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s6/1 | 1.400 | 0.000000 | 0.087 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s7/1 | 1.400 | 0.000000 | 0.087 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s8/1 | 1.400 | 0.000000 | 0.036 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s9/1 | 1.400 | 0.000000 | 0.062 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s10/1 | 1.400 | 0.000000 | 0.156 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s11/1 | 1.400 | 0.000000 | 0.107 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |

## Kropp: oberoende mått, darr och täckning

Silhuett: kroppsmodellens hudnät skinnat med de byggda lederna, projicerat i den spårade kameran, mot YOLO11-seg-masken (en annan modell än kroppsestimatorn), inom personens egen spårruta, på ALLA rutor där masken finns (även opålitliga). IoU `synlig` klipper nätet vid maskens nedersta rad (skymmande disk/bord). Tyngdpunktsfel i andel av bildhöjden. **Skevhet:** masken har kläder, hår och hållna föremål som kroppen saknar och kan sakna fingrar; estimatorns egna hörn mot samma mask ger referens-IoU (kolumn ref); IoU under ref är alltså inte automatiskt fel. Hudnätet är lod1 (renderingen använder lod3, samma kropp) utan korrigerande blendshapes (< 2 cm lokalt).
Darr: medel andra differens av ledpositionerna (127 leder, planens värld, cm/ruta²) för byggd pose, stabiliserad pose före golv/kontakt/stöd, och estimatorns råa pose med råa cam_t. Råa är skakigare än filmen får vara; byggd över 1.5 = granska, över 3.0 = dålig (våra val). Andel = hur stor del av den stabiliserade posen som överlevde äldre bildskydd (– = inget bildskydd, ny metod).
Täckning: rutor där avvikelsen från estimatorns 2D kunde bedömas / rutor i scenen. Orsaker till uteblivna rutor: ej i bild (personen ej spårad), opålitlig (under 35 % av kroppspunkterna i bild eller 15 % i masken: estimatorn gissar), rådata saknas. Under 60% = granska.
Gränser (våra, inga ägarkrav): IoU synlig bra ≥ 0.65, dålig < 0.5; tyngdpunkt p90 > 3 % granska, > 6 % dålig.

| Scen | Person | IoU / IoU synlig / ref (median) | Tyngdpunkt median/p90 (% bildhöjd) | Mask-rutor | Darr byggd / stabil / rå | Andel | Täckning (bedömda/rutor) | Utelämnade: ej i bild / opålitliga / rådata saknas |
|---|---|---|---|---|---|---|---|---|
| s1 | A | 0.78 / 0.78 / 0.79 | 1.7 / 4.3 | 50 av 50 | 1.22 / 0.97 / 3.40 | – | 50 av 50 | 0 / 0 / 0 |
| s2 | A | 0.79 / 0.79 / 0.80 | 2.8 / 3.4 | 51 av 51 | 0.87 / 0.82 / 2.14 | – | 51 av 52 | 1 / 0 / 0 |
| s3 | B | 0.79 / 0.79 / 0.80 | 0.6 / 1.4 | 42 av 42 | 0.99 / 0.88 / 2.51 | – | 42 av 42 | 0 / 0 / 0 |
| s4 | B | 0.79 / 0.79 / 0.80 | 1.3 / 1.9 | 70 av 70 | 0.61 / 0.61 / 1.61 | – | 70 av 72 | 2 / 0 / 0 |
| s5 | C | 0.63 / 0.66 / 0.63 | 5.7 / 9.1 | 46 av 46 | 3.08 / 2.71 / 7.00 | – | 46 av 46 | 0 / 0 / 0 |
| s6 | C | 0.78 / 0.82 / 0.76 | 1.9 / 2.0 | 32 av 32 | 0.51 / 0.51 / 2.05 | – | 32 av 32 | 0 / 0 / 0 |
| s7 | C | 0.78 / 0.82 / 0.76 | 1.6 / 1.8 | 26 av 26 | 0.37 / 0.36 / 1.04 | – | 26 av 26 | 0 / 0 / 0 |
| s8 | C | 0.61 / 0.64 / 0.60 | 5.8 / 7.1 | 20 av 20 | 1.20 / 1.16 / 3.53 | – | 20 av 20 | 0 / 0 / 0 |
| s9 | C | 0.58 / 0.60 / 0.58 | 7.6 / 10.5 | 35 av 35 | 1.04 / 0.84 / 1.88 | – | 34 av 35 | 0 / 1 / 0 |
| s10 | C | 0.53 / 0.56 / 0.55 | 7.0 / 10.4 | 46 av 49 | 1.44 / 1.69 / 4.67 | – | 46 av 49 | 0 / 0 / 3 |
| s11 | C | 0.62 / 0.63 / 0.61 | 5.6 / 6.9 | 43 av 43 | 0.88 / 0.90 / 4.29 | – | 43 av 46 | 3 / 0 / 0 |

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

Skymning är provandel av källmask inom personrutan: segmentet från mätkameran till närmaste synliga MHR70-punkts riktiga 3D-position provas mot möbellådorna; ingen exakt hudarea. Var tredje och sista rutan kontrolleras (före 10 nov var sjätte). Varje kroppsdel har egen gräns, 10 % av delens maskprov (minst 8), så att tunna skenor över höften syns även när de är << 2 % av alla prov före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.

## Skärmtext

81 tidsatta 2D-lager i källpixlar. Textinnehåll från sparad semantik; teckenmallar mäter plats och synlighet utan OCR. Fontval är närmaste installerade font. Konfidens avser teckenmatchning, inte sannolikheten att modellens text är rätt.

## Diskpassning

