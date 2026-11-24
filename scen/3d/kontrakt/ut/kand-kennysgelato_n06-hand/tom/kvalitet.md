# Kvalitet

Detta är egna diagnostiska trösklar, valda i förväg och inte justerade så att scener ska passera: slutkamerans medeloffset 3 % av bildhöjden, skalfaktor 0,85–1,15 och led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal; kroppsmåtten nedan. Slutbildsmåttet projicerar samma leder genom kameran som Blender renderar med. Det är inte oberoende av kroppsestimatorn, men till skillnad från ingestkameramåttet ser det ändrad inramning. Den oberoende kontrollen är silhuett-IoU mot YOLO-masken.

| Scen | Slutkamera: medel px / % höjd / skala / IoU | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |
|---|---|---|---|---|---|
| s1 | 24.09 / 1.25 % / 1.013 / 0.926 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | A: 32 i 153 rutor | 9.5 → 0.0 % | dålig: endast överkropp (A): inget golv eller kontakt, golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., mall utelämnad: disk_A, A: tyngdpunkt p90 3.8 % av bildhöjden, A: darr 3.85 cm/ruta² |
| s2 | 338.46 / 17.63 % / 1.034 / 0.714 | deklarerad, ±25.0 cm; spann 0.0 cm; skala 1,0 antagen | A: 32 i 36 rutor | 0.0 → 0.0 % | dålig: slutkamerans inramning avviker från originalets 2D-läsning, endast överkropp (A): inget golv eller kontakt, kamerans translation okänd (avvisad skala), golv deklarerad, Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt., A: silhuett-IoU 0.56 < 0.65, A: tyngdpunkt p90 12.3 % av bildhöjden, A: passningen bedömd på 12 av 96 rutor |

## GOLV2: kropp och rum

Kroppens kameraposition bevaras. Synlig fot är modellbedömd kontakt, inte fysisk inmätning. Dolda fötter styr inte golvet.

| Scen/person | Kamera över golv m | Kamera till rumskamera m | Modellfotrest m | Synlig fotrest m | Kontakt |
|---|---:|---:|---:|---:|---|
| s1/1 | 1.300 | 0.000000 | -0.080 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |
| s2/5 | 1.300 | 0.000000 | 0.223 | saknas | saknas; Dolda fötter: kontakt okänd; modellresten styr inte golvet. |

## Kropp: oberoende mått, darr och täckning

Silhuett: kroppsmodellens hudnät skinnat med de byggda lederna, projicerat i den spårade kameran, mot YOLO11-seg-masken (en annan modell än kroppsestimatorn), inom personens egen spårruta, på ALLA rutor där masken finns (även opålitliga). IoU `synlig` klipper nätet vid maskens nedersta rad (skymmande disk/bord). Tyngdpunktsfel i andel av bildhöjden. **Skevhet:** masken har kläder, hår och hållna föremål som kroppen saknar och kan sakna fingrar; estimatorns egna hörn mot samma mask ger referens-IoU (kolumn ref); IoU under ref är alltså inte automatiskt fel. Hudnätet är lod1 (renderingen använder lod3, samma kropp) utan korrigerande blendshapes (< 2 cm lokalt).
Darr: medel andra differens av ledpositionerna (127 leder, planens värld, cm/ruta²) för byggd pose, stabiliserad pose före golv/kontakt/stöd, och estimatorns råa pose med råa cam_t. Råa är skakigare än filmen får vara; byggd över 1.5 = granska, över 3.0 = dålig (våra val). Andel = hur stor del av den stabiliserade posen som överlevde äldre bildskydd (– = inget bildskydd, ny metod).
Täckning: rutor där avvikelsen från estimatorns 2D kunde bedömas / rutor i scenen. Orsaker till uteblivna rutor: ej i bild (personen ej spårad), opålitlig (under 35 % av kroppspunkterna i bild eller 15 % i masken: estimatorn gissar), rådata saknas. Under 60% = granska.
Gränser (våra, inga ägarkrav): IoU synlig bra ≥ 0.65, dålig < 0.5; tyngdpunkt p90 > 3 % granska, > 6 % dålig.

| Scen | Person | IoU / IoU synlig / ref (median) | Tyngdpunkt median/p90 (% bildhöjd) | Mask-rutor | Darr byggd / stabil / rå | Andel | Täckning (bedömda/rutor) | Utelämnade: ej i bild / opålitliga / rådata saknas |
|---|---|---|---|---|---|---|---|---|
| s1 | A | 0.70 / 0.74 / 0.71 | 1.7 / 3.8 | 154 av 156 | 3.85 / 3.77 / 7.03 | – | 148 av 156 | 0 / 6 / 2 |
| s2 | A | 0.56 / 0.56 / 0.59 | 2.2 / 12.3 | 36 av 36 | 0.59 / 0.67 / 1.93 | – | 12 av 96 | 60 / 24 / 0 |

## Kamerabana

Den metriska kamerabanan som bärs in i bygget (`varld.npz`) kontrolleras mot vad en handhållen mobil kan göra inomhus: p90-fart ≤ 5.0 m/s, maxfart ≤ 15.0 m/s, sträcka ≤ 5.0 m/s × scenens längd (våra gränser). En orimlig bana betyder nästan alltid att COLMAP-skalan inte är bestämd (kenny S2 hade 11,7 km). Avvisad skala = translationen är nollad och bara rotationen används.

| Scen | Bana (m) | p90 / max fart (m/s) | Rimlig | Skalbeslut vid ingest |
|---|---|---|---|---|
| s1 | 0.00 | 0.00 / 0.00 | ja | uppmatt |
| s2 | 0.00 | 0.00 / 0.00 | ja | antagen: Skalan oidentifierbar: rotbanans ojämnhet är platt över k (kameran stod still medan personen syntes). Translation avvisad, rotation behålls. (translation avvisad; p90 före avvisning 1.29e+04 m/s, 1.431e+04 m) |

Antaget: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). Dessa möbelpriorer används bara vid vanligt bord, inte bardisk. En stilla handled behöver inte vila på bordet. Passningens rest mot handled och bäcken loggas, även när en höjd begränsas av priorn. Ingen kropp skalas för att passa en prior.

Skymning är provandel av källmask inom personrutan: segmentet från mätkameran till närmaste synliga MHR70-punkts riktiga 3D-position provas mot möbellådorna; ingen exakt hudarea. Var tredje och sista rutan kontrolleras (före 10 nov var sjätte). Varje kroppsdel har egen gräns, 10 % av delens maskprov (minst 8), så att tunna skenor över höften syns även när de är << 2 % av alla prov före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.

## Skärmtext

3 tidsatta 2D-lager i källpixlar. Textinnehåll från sparad semantik; teckenmallar mäter plats och synlighet utan OCR. Fontval är närmaste installerade font. Konfidens avser teckenmatchning, inte sannolikheten att modellens text är rätt.

## Diskpassning

