# Kvalitet

Detta är egna diagnostiska trösklar, valda i förväg och inte justerade så att scener ska passera: slutkamerans medeloffset 3 % av bildhöjden, skalfaktor 0,85–1,15 och led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal; kroppsmåtten nedan. Slutbildsmåttet projicerar samma leder genom kameran som Blender renderar med. Det är inte oberoende av kroppsestimatorn, men till skillnad från ingestkameramåttet ser det ändrad inramning. Den oberoende kontrollen är silhuett-IoU mot YOLO-masken.

| Scen | Slutkamera: medel px / % höjd / skala / IoU | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 2.56 / 0.25 % / 1.002 / 0.974 | deklarerad, ±9.0 cm; spann 8.2 cm; skala 1,0 antagen | A: 32 i 88 rutor | 0.0 → 0.0 % | granska: endast överkropp (A): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt. |
| s2 | 3.98 / 0.39 % / 0.999 / 0.984 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | B: 32 i 51 rutor | 0.0 → 0.0 % | granska: endast överkropp (B): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., B: tyngdpunkt p90 4.5 % av bildhöjden, B: passningen bedömd på 0 av 51 rutor |
| s3 | 4.84 / 0.47 % / 0.998 / 0.939 | deklarerad, ±9.0 cm; spann 8.2 cm; skala 1,0 antagen | A: 32 i 51 rutor | 0.0 → 0.0 % | granska: endast överkropp (A): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt. |
| s4 | 3.52 / 0.34 % / 1.000 / 0.965 | deklarerad, ±9.0 cm; spann 10.8 cm; skala 1,0 antagen | B: 32 i 109 rutor; A: 32 i 109 rutor | 0.0 → 0.0 % | granska: endast överkropp (B): inget golv eller kontakt, endast överkropp (A): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., golvcues oense, B: darr 1.56 cm/ruta², A: silhuett-IoU 0.55 < 0.65 |

## GOLV2: kropp och rum

Kroppens kameraposition bevaras. Synlig fot är modellbedömd kontakt, inte fysisk inmätning. Dolda fötter styr inte golvet.

| Scen/person | Kamera över golv m | Kamera till rumskamera m | Modellfotrest m | Synlig fotrest m | Kontakt |
|---|---:|---:|---:|---:|---|
| s1/1 | 1.400 | 0.000000 | 0.106 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s2/1 | 1.400 | 0.000000 | 0.064 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s3/1 | 1.400 | 0.000000 | 0.097 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s4/1 | 1.400 | 0.000000 | 0.050 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s4/2 | 1.400 | 0.000000 | 0.067 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |

## Kropp: oberoende mått, darr och täckning

Silhuett: kroppsmodellens hudnät skinnat med de byggda lederna, projicerat i den spårade kameran, mot YOLO11-seg-masken (en annan modell än kroppsestimatorn), inom personens egen spårruta, på ALLA rutor där masken finns (även opålitliga). IoU `synlig` klipper nätet vid maskens nedersta rad (skymmande disk/bord). Tyngdpunktsfel i andel av bildhöjden. **Skevhet:** masken har kläder, hår och hållna föremål som kroppen saknar och kan sakna fingrar; estimatorns egna hörn mot samma mask ger referens-IoU (kolumn ref); IoU under ref är alltså inte automatiskt fel. Hudnätet är lod1 (renderingen använder lod3, samma kropp) utan korrigerande blendshapes (< 2 cm lokalt).
Darr: medel andra differens av ledpositionerna (127 leder, planens värld, cm/ruta²) för byggd pose, stabiliserad pose före golv/kontakt/stöd, och estimatorns råa pose med råa cam_t. Råa är skakigare än filmen får vara; byggd över 1.5 = granska, över 3.0 = dålig (våra val). Andel = hur stor del av den stabiliserade posen som överlevde äldre bildskydd (– = inget bildskydd, ny metod).
Täckning: rutor där avvikelsen från estimatorns 2D kunde bedömas / rutor i scenen. Orsaker till uteblivna rutor: ej i bild (personen ej spårad), opålitlig (under 35 % av kroppspunkterna i bild eller 15 % i masken: estimatorn gissar), rådata saknas. Under 60% = granska.
Gränser (våra, inga ägarkrav): IoU synlig bra ≥ 0.65, dålig < 0.5; tyngdpunkt p90 > 3 % granska, > 6 % dålig.

| Scen | Person | IoU / IoU synlig / ref (median) | Tyngdpunkt median/p90 (% bildhöjd) | Mask-rutor | Darr byggd / stabil / rå | Andel | Täckning (bedömda/rutor) | Utelämnade: ej i bild / opålitliga / rådata saknas |
|---|---|---|---|---|---|---|---|---|
| s1 | A | 0.68 / 0.68 / 0.68 | 2.5 / 2.6 | 88 av 88 | 1.15 / 0.93 / 2.03 | – | 88 av 88 | 0 / 0 / 0 |
| s2 | B | 0.66 / 0.69 / – | 4.0 / 4.5 | 51 av 51 | – / – / – | – | 0 av 51 | 0 / 51 / 0 |
| s3 | A | 0.68 / 0.68 / 0.67 | 1.8 / 2.0 | 51 av 51 | 1.12 / 1.14 / 3.68 | – | 51 av 51 | 0 / 0 / 0 |
| s4 | B | 0.74 / 0.76 / 0.74 | 1.7 / 2.2 | 109 av 109 | 1.56 / 1.54 / 3.88 | – | 109 av 109 | 0 / 0 / 0 |
| s4 | A | 0.55 / 0.55 / 0.54 | 1.9 / 2.1 | 109 av 109 | 0.52 / 0.50 / 1.63 | – | 109 av 109 | 0 / 0 / 0 |

## Kamerabana

Den metriska kamerabanan som bärs in i bygget (`varld.npz`) kontrolleras mot vad en handhållen mobil kan göra inomhus: p90-fart ≤ 5.0 m/s, maxfart ≤ 15.0 m/s, sträcka ≤ 5.0 m/s × scenens längd (våra gränser). En orimlig bana betyder nästan alltid att COLMAP-skalan inte är bestämd (kenny S2 hade 11,7 km). Avvisad skala = translationen är nollad och bara rotationen används.

| Scen | Bana (m) | p90 / max fart (m/s) | Rimlig | Skalbeslut vid ingest |
|---|---|---|---|---|
| s1 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s2 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s3 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s4 | 0.00 | 0.00 / 0.00 | ja | uppmatt |

Antaget: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). Dessa möbelpriorer används bara vid vanligt bord, inte bardisk. En stilla handled behöver inte vila på bordet. Passningens rest mot handled och bäcken loggas, även när en höjd begränsas av priorn. Ingen kropp skalas för att passa en prior.

Skymning är provandel av källmask inom personrutan, med närmaste MHR70-punkts djup; ingen exakt hudarea. Var tredje och sista rutan kontrolleras (före 10 nov var sjätte). Varje kroppsdel har egen gräns, 10 % av delens maskprov (minst 8), så att tunna skenor över höften syns även när de är << 2 % av alla prov före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.

## Skärmtext

8 tidsatta 2D-lager i källpixlar. Textinnehåll från sparad semantik; teckenmallar mäter plats och synlighet utan OCR. Fontval är närmaste installerade font. Konfidens avser teckenmatchning, inte sannolikheten att modellens text är rätt.
- st6 (s4): antagen placering/tid; Inledande utrop före den lokaliserade delsträngens första källruta.
- st7 (s4): antagen placering/tid; Reservplacering: känd sträng kunde inte lokaliseras säkert.
- st8 (s4): antagen placering/tid; Samtidiga textfragment med samma källintervall och skärmyta har samlats till ett block.

## Diskpassning

