# Rumsbank: kamera, rum och meterskala

## Bedömning

Behåll tills vidare COLMAP + MoGe med tydligt redovisad osäkerhet. Ingen av de prövade offentligt tillgängliga kedjorna är här verifierad som en säkrare automatisk grund för ett bildtroget 1:1-rum. ViPE:s kamera är tekniskt bäst på den rörliga biljardtagningen men fallerar kraftigt i B S5 och har olösta vikträttigheter. DA3:s Apache-kombination är en möjlig reservkandidat för relativ kamera; meterskala och gemensamt rum räcker inte för ett byte.

Detta är en separat utvärdering. Alla nya filer finns i denna mapp. Inga befintliga projektfiler har ändrats, inga ingeststeg har körts om, ingen lokal modellinferens, Blender eller testsvit har körts. Alla modellkörningar gjordes på Modal med en GPU-funktion åt gången.

## Material och vad som faktiskt kördes

Notan: S1 (73 rutor), S4 (85 rutor), hela originalet (383 rutor), samt ett gemensamt S1/S4-fall med åtta jämnt fördelade bilder från vardera kamerastationen. B: S5 (46 rutor) och närbilden S9 (35 rutor). Biljard: originalet med 369 rutor. Kenny: S2 (96 rutor), där den tidigare oidentifierbara COLMAP-skalan gav en avvisad kilometerbana. Fullständiga källsökvägar, tidsindex och JPEG-hashar finns i manifest.json.

MapAnything använder den uttryckliga Apache-vikten, inte standardvikten. DA3 här är vår redovisade kombination av DA3-BASE för relativ kamera/djup och DA3METRIC-LARGE för en gemensam skala. Konverteringen är den officiella `focal * canonical_depth / 300`; samma skalär multiplicerar djup och kameratranslation. Det är inte den officiella NC-licensierade Nested-Giant-modellen. Ingen kroppstranslation ändras.

Första jämförelsen använder alla rutor i de korta tagningarna för MapAnything, upp till 24 jämnt fördelade plus de åtta granskningsrutorna för DA3, samt 80 provrutor i biljard och 46 i hela notan för MapAnything. Tabellen anger faktiskt antal. Separata fullrutekontroller för alla tre omfattar 383/383 notanrutor och 369/369 biljardrutor. MapAnything har också pool_visible (363 rutor utan helt svarta ändrutor, men med fades) och pool_core (311 rutor, source 40–350, utan fades). Råfilerna bevarar utvalda ofiltrerade djup-, kamera- och konfidenstensorer, inte alla latenta egenskaper eller fria punkt-/strålkartor. Geometrin prövas som K + Z-djup, den pinhålskamerarepresentation som platskedjan behöver.

ViPE-koden finns i modal_vipe.py. Den särskilda konfigurationen använder DROID, GeoCalib, MoGe2 och de befintliga personmaskerna. Kamerans SLAM är ViPE; sparat tätt djup är separat MoGe2 vid den skattade K. Den officiella adaptiva djupfusionen har INTE körts: AdaptiveDepthProcessor skapar PriorDA som i sin tur använder DAV2-Base-backbones med NC-vikter. Detta gäller även när det metriska försteget byts till MoGe2. Standardkedjans UniDepth/VDA och MetricTrail är också blockerade. Resultatet kan därför bedöma en ViPE-kamerakonfiguration men inte avfärda den kommersiellt blockerade fulla djupmetodens tekniska kvalitet. CPU-bygget behövde en tillgänglig gtsam-develop-version samt clang; ursprungsfel och ändringar finns i RUM-LOGG.md och vipe_prepare*.log.

## Mätdefinitioner och begränsningar

Kamerajämförelsen använder rå kamera.json endast när de numeriska acceptanskraven uppfylls, och endast inom de registrerade rutornas tidsintervall. En enda rotation anpassar första giltiga kameran; ingen bäst anpassad likformighetstransform får dölja fel. R är median rotationsskillnad i grader, T är skillnaden i ändpunkternas translationsriktning i grader, f är brännviddsskillnaden i procent. COLMAP är en referens, inte ett facit. S1/S4 saknar accepterad COLMAP. B S5:s och Kennys metriska translation har avvisats i varld.npz trots godkända numeriska kamera-/fokalkrav.

Stativkolumnen anger kamerabanans diameter i cm, inte summan av alla små steg. Rå banlängd, rotation, hastighet och acceleration finns också i resultat.json. Olika tidsurval ger olika känslighet för darr. FOV är horisontell och bygger på varje modells faktiska processbild. En avvikelse från uppdragsbeskrivningen: regler.py och de sparade kropparna använder här bildens längsta sida som reservfokal, inte en gemensam 68°-kalibrering. Vi jämför med de faktiska sparade värdena och ändrar dem inte.

Δ kropp är median procentuell djupskillnad mot den råa kroppsmodellens synliga yta, projicerad med kroppens egen fokal och z-buffrad. Positivt värde betyder djupare rum/personyta. Detta är INTE uppmätt absolut skalfel: kroppen och dess fokal är också skattningar. Frånvarande eller redan personmaskat djup ger inget sådant mått. Absolut skalfel mot oberoende mätning är null i JSON för samtliga tagningar. En god överläggsbild kan inte verifiera meterskalan.

Golv mäts i manuellt valda synliga golvytor med personerna bortmaskade. Tabellen visar planoffsetens variationsvidd i cm och normalens p90-variation i grader, med världsorigo vid första giltiga kameran. Minst två stödrutor krävs. Hela notan-klippets golvkontroll kompletteras med högst 16 tillgängliga rutor inom S4-delen (source 171–255); detta mäter tidsstabilitet i den kameravyn, inte samstämmighet mellan motbilder. S1, B-närbilderna och Kenny saknar tillräckligt synligt golv; där redovisas inget påhittat golvmått eller antagen kamerahöjd. Golv över flera motbilder är inte verifierat bara för att nätet producerar gemensamma koordinater.

BG är medianen av parvisa medianfel för SIFT-matchningar utanför personmasker och manuellt maskade textband, efter ratio-test och epipolär MAGSAC. Rörligt rekvisitainnehåll är inte separat segmenterat. Kandidatens djup och kameror projicerar punkterna mellan bilder. Enheten är modellbildens pixlar (Map 518 × 294, DA3 504 × 280, baslinje 518 × 292, ViPE 768 × 432); jämför upplösningarna innan en bildmetod rangordnas. Gränsen 1 px här är inte identisk med COLMAP:s ursprungliga pixelgräns. Misslyckade klippövergångar kan ge få eller inga matchningar. Ett degenererat OpenCV-fel sparas i failed_pairs och behandlas aldrig som nollfel.

Baslinjen läser åtta av de befintliga MoGe-cachemätningarna och varld.npz. Närmaste cachade djup till granskningsrutan används; avvikelsen står i cache_mapping. Det är en begränsad referens, inte en ny MoGe-körning. Den fulla accepterade äldre biljardbanan är cirka 1,60 m; tabellens glesa baslinje summerar bara granskningsrutornas delbana.

## Resultattabell

| Metod / tagning | R / T / f | Stativdiameter cm | Δ kropp % | Golv cm / ° | BG px | GPU s/ruta | Rutor |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / notan_S1 | — / — / — | 0.00 | — | ej mätbart | 0.7 | — | 8 |
| baseline / notan_S4 | — / — / — | 0.00 | — | 5.6 / 0.5 | 0.5 | — | 8 |
| baseline / b_S5 | 0.0 / — / 0.0 | — | 13.0 | ej mätbart | 45.7 | — | 8 |
| baseline / b_closeup | — / — / — | — | — | ej mätbart | 16.5 | — | 8 |
| baseline / pool | 0.0 / 0.0 / 0.0 | — | 106.4 | 23.0 / 2.2 | 6.7 | — | 8 |
| baseline / kenny_S2 | 0.8 / — / 0.0 | — | 47.6 | ej mätbart | 19.6 | — | 8 |
| mapanything / notan_S1 | — / — / — | 1.06 | -5.1 | ej mätbart | 0.5 | 0.068 | 73 |
| mapanything / notan_S4 | — / — / — | 1.81 | -32.5 | 1.0 / 0.7 | 0.4 | 0.036 | 85 |
| mapanything / b_S5 | 6.6 / 94.9 / -50.0 | — | -32.3 | ej mätbart | 12.0 | 0.030 | 46 |
| mapanything / b_closeup | — / — / — | — | 112.1 | ej mätbart | 2.3 | 0.028 | 35 |
| mapanything / pool | 9.8 / 67.9 / -36.2 | — | -25.3 | 10.5 / 4.3 | 18.0 | 0.035 | 80 |
| mapanything / kenny_S2 | 1.0 / 10.4 / 36.9 | — | 106.4 | ej mätbart | 3.8 | 0.038 | 96 |
| mapanything / notan_uncut | — / — / — | — | — | 4.2 / 0.5 | 1.6 | 0.030 | 46 |
| mapanything / notan_joint_S1_S4 | — / — / — | — | — | 3.3 / 0.4 | 2.1 | 0.026 | 16 |
| mapanything / notan_fullrate | — / — / — | — | — | 6.6 / 0.7 | 3.5 | 0.087 | 383 |
| mapanything / pool_fullrate | 39.7 / 77.6 / -36.3 | — | -28.8 | 8.8 / 4.7 | 37.2 | 0.082 | 369 |
| mapanything / pool_visible | 43.9 / 125.6 / -37.1 | — | -32.6 | 84.0 / 5.6 | 49.0 | 0.085 | 363 |
| mapanything / pool_core | 1.0 / 2.7 / -35.6 | — | -24.8 | 7.0 / 2.0 | 2.0 | 0.079 | 311 |
| da3 / notan_S1 | — / — / — | 0.43 | -33.6 | ej mätbart | 0.7 | 0.096 | 28 |
| da3 / notan_S4 | — / — / — | 0.96 | 4.7 | 2.6 / 0.2 | 0.6 | 0.065 | 30 |
| da3 / b_S5 | 3.7 / 17.8 / -53.4 | — | -54.1 | ej mätbart | 6.4 | 0.064 | 28 |
| da3 / b_closeup | — / — / — | — | -4.9 | ej mätbart | 1.3 | 0.059 | 26 |
| da3 / pool | 0.8 / 0.3 / 11.5 | — | 21.4 | 19.6 / 2.5 | 6.2 | 0.055 | 28 |
| da3 / kenny_S2 | 0.5 / 1.0 / 17.8 | — | 14.0 | ej mätbart | 5.9 | 0.055 | 28 |
| da3 / notan_uncut | — / — / — | — | — | 5.0 / 0.6 | 309.4 | 0.052 | 28 |
| da3 / notan_joint_S1_S4 | — / — / — | — | — | 2.3 / 0.5 | 3.6 | 0.066 | 16 |
| da3 / notan_fullrate | — / — / — | — | — | 4.1 / 0.7 | 112.6 | 0.087 | 383 |
| da3 / pool_fullrate | 1.4 / 1.1 / 13.8 | — | 38.6 | 19.2 / 2.8 | 3.7 | 0.072 | 369 |
| vipe / notan_S1 | — / — / — | 0.75 | 19.5 | ej mätbart | 0.2 | 0.265 | 73 |
| vipe / notan_S4 | — / — / — | 0.63 | -24.6 | 6.7 / 0.3 | 0.2 | 0.159 | 85 |
| vipe / b_S5 | 7.6 / 59.7 / 165.9 | — | 288.0 | ej mätbart | 106.9 | 0.249 | 46 |
| vipe / b_closeup | — / — / — | — | 128.2 | ej mätbart | 0.3 | 0.187 | 35 |
| vipe / pool | 0.6 / 1.3 / -2.0 | — | -3.8 | 22.9 / 2.2 | 1.4 | 0.229 | 80 |
| vipe / kenny_S2 | 0.5 / 11.6 / -0.5 | — | -4.8 | ej mätbart | 19.6 | 0.294 | 96 |
| vipe / notan_uncut | — / — / — | — | — | 4.7 / 0.3 | 4.7 | 0.206 | 46 |
| vipe / notan_joint_S1_S4 | — / — / — | — | — | 7.0 / 0.3 | 0.2 | 0.245 | 16 |
| vipe / notan_fullrate | — / — / — | — | — | 5.7 / 0.3 | 8.2 | 0.164 | 383 |
| vipe / pool_fullrate | 0.2 / 0.4 / -0.7 | — | -1.5 | 23.3 / 2.1 | 1.4 | 0.162 | 369 |

## FOV och kostnad per fall

| Metod / tagning | Horisontell FOV min / median / max ° | Fokalspann % | Fjärrtid per fall s | Allokerat VRAM GB |
|---|---:|---:|---:|---:|
| baseline / notan_S1 | 31.4 / 31.4 / 31.4 | 0.0 | — | — |
| baseline / notan_S4 | 31.4 / 31.4 / 31.4 | 0.0 | — | — |
| baseline / b_S5 | 14.1 / 14.1 / 14.1 | 0.0 | — | — |
| baseline / b_closeup | 31.4 / 31.4 / 31.4 | 0.0 | — | — |
| baseline / pool | 36.1 / 36.1 / 36.1 | 0.0 | — | — |
| baseline / kenny_S2 | 39.5 / 39.5 / 39.5 | 0.0 | — | — |
| mapanything / notan_S1 | 52.9 / 53.0 / 53.2 | 0.7 | 9.7 | 10.1 |
| mapanything / notan_S4 | 53.4 / 53.6 / 53.8 | 1.0 | 8.5 | 11.2 |
| mapanything / b_S5 | 27.8 / 28.0 / 28.3 | 1.9 | 4.7 | 8.5 |
| mapanything / b_closeup | 23.5 / 23.6 / 23.7 | 0.8 | 3.4 | 7.6 |
| mapanything / pool | 52.9 / 54.1 / 54.7 | 3.8 | 6.3 | 10.7 |
| mapanything / kenny_S2 | 29.4 / 30.0 / 35.2 | 17.7 | 11.0 | 12.0 |
| mapanything / notan_uncut | 53.1 / 53.9 / 55.7 | 5.5 | 5.1 | 8.6 |
| mapanything / notan_joint_S1_S4 | 53.2 / 53.8 / 54.2 | 2.1 | 1.7 | 6.4 |
| mapanything / notan_fullrate | 52.7 / 54.2 / 55.8 | 6.6 | 61.0 | 31.9 |
| mapanything / pool_fullrate | 52.6 / 54.1 / 54.9 | 4.9 | 48.0 | 32.4 |
| mapanything / pool_visible | 53.5 / 55.0 / 56.0 | 5.3 | 50.3 | 30.5 |
| mapanything / pool_core | 53.6 / 54.2 / 54.8 | 2.6 | 47.8 | 26.9 |
| da3 / notan_S1 | 37.4 / 38.1 / 38.2 | 2.2 | 6.4 | 4.1 |
| da3 / notan_S4 | 33.2 / 33.2 / 33.3 | 0.5 | 5.5 | 4.2 |
| da3 / b_S5 | 32.6 / 34.5 / 35.4 | 9.0 | 5.1 | 4.1 |
| da3 / b_closeup | 25.7 / 25.9 / 26.2 | 1.8 | 5.3 | 4.1 |
| da3 / pool | 36.4 / 38.4 / 41.0 | 12.8 | 5.4 | 4.1 |
| da3 / kenny_S2 | 38.1 / 39.5 / 40.0 | 5.3 | 5.4 | 4.1 |
| da3 / notan_uncut | 34.9 / 36.2 / 37.2 | 6.9 | 4.7 | 4.1 |
| da3 / notan_joint_S1_S4 | 32.7 / 34.0 / 35.0 | 7.3 | 2.9 | 3.7 |
| da3 / notan_fullrate | 35.3 / 36.3 / 37.1 | 5.1 | 80.3 | 18.3 |
| da3 / pool_fullrate | 35.0 / 37.6 / 39.5 | 13.1 | 72.6 | 17.7 |
| vipe / notan_S1 | 34.4 / 34.4 / 34.4 | 0.0 | 28.1 | 6.8 |
| vipe / notan_S4 | 37.6 / 37.6 / 37.6 | 0.0 | 13.5 | 6.8 |
| vipe / b_S5 | 5.3 / 5.3 / 5.3 | 0.0 | 11.6 | 8.1 |
| vipe / b_closeup | 14.6 / 14.6 / 14.6 | 0.0 | 6.6 | 7.3 |
| vipe / pool | 36.8 / 36.8 / 36.8 | 0.0 | 18.4 | 7.7 |
| vipe / kenny_S2 | 39.7 / 39.7 / 39.7 | 0.0 | 28.3 | 8.0 |
| vipe / notan_uncut | 34.7 / 34.7 / 34.7 | 0.0 | 9.7 | 7.0 |
| vipe / notan_joint_S1_S4 | 40.9 / 40.9 / 40.9 | 0.0 | 4.0 | 6.8 |
| vipe / notan_fullrate | 34.3 / 34.3 / 34.3 | 0.0 | 73.5 | 7.0 |
| vipe / pool_fullrate | 36.3 / 36.3 / 36.3 | 0.0 | 60.0 | 7.8 |

Fjärrtiden är ökningen i funktionens klocka mellan fall, efter separat redovisad modellstart i första fallet. Den omfattar förberedelse, beräkning, komprimering och ibland överföringsarbete efter föregående svar. Den är inte en isolerad kärntid. Lokal väggtid för hela anropet finns i budgethändelsen och separat i varje kostnadspost i resultat.json. Faktisk kallstart och fakturerad tid kunde inte separeras från uppladdning/hämtning.

## Skala och föremål

Gemensamt S1/S4 gav en bordsskivehöjd omkring 0,86 m med MapAnything, 0,72 m med DA3 och 0,82 m med ViPE-kamera + rå MoGe2 i den första gemensamma körningen. Mot priorn 0,74 m är det cirka +16, −3 respektive +11 procent; det är inte fysiskt uppmätt skalfel. Samtidigt ger en separat dörrlinje andra mått, exempelvis cirka 2,22 m med MapAnything och 1,58 m med DA3 mot en 2,0 m-prior. Det visar varför en enda skalfaktor eller enbart bordshöjd inte räcker som godkännande. Exakta tal och bildpunkter finns i size_checks.json och respektive metrics.json.

Biljardbordets tidigare 2,4 × 1,3 m kan inte verifieras på en hel, identifierad rektangel i de åtta valda bilderna: människor skymmer och närborden beskärs. Vi tvingar därför inte en godtycklig grön yta till det måttet. Dörrens 2,0 m och bordets 0,72–0,76 m redovisas som priorer. Ingen oberoende inmätning av rummet eller kamerorna fanns i materialet.

## Granskade överlägg och dynamik

Strips ligger bredvid råutdata under ut/<metod>/<tagning>/overlay*.jpg. Åtta jämnt placerade källrutor används per fall; S1/S4 har två strips med totalt 16. Cyan är ett 0,5 m-golvgrid. Gröna och orange lådor är tunna passningar till observerade bord-/väggfläckar, inte automatisk möbeldetektering eller kompletta rum. De saknar skymning och ritas även över personer; detta är ingen djupordningskontroll. Granskningens observationer och vilka filer som faktiskt har öppnats finns i overlay_review.json.

Stativfallen ser stabila ut i originalvyn trots olika metriska djup. MapAnything tappar stabilitet i biljardsekvensen med svart/fade-intro: rå banlängd 94,7 m med alla rutor och 144,0 m efter borttagning av bara svarta rutor. När även fades tas bort blir banan 5,20 m, rotationsskillnaden cirka 0,99° och griden betydligt lugnare. Detta är en viktig förbättring, inte ett generellt misslyckande på all rörlig video. Ändå är fokalen cirka −36 procent mot COLMAP och ytdjupet cirka −25 procent mot kroppen. ViPE på hela biljardklippet når cirka 0,23° rotationsskillnad och −0,7 procent i fokal, men dess separata MoGe2-golv varierar cirka 23 cm. B S5 är ett motexempel: ViPE skattar cirka 5,3° horisontell FOV, +166 procent fokalavvikelse och stort bakgrundsfel. Kenny saknar synligt golv och byter bildinnehåll kraftigt från disk till ansikte.

Rådjupen från MapAnything/DA3 innehåller människor. De måste maskas före fusion; nätens generella konfidens är ingen personmask. Förgrundens kausala bidrag till kamerafelet har inte isolerats med en kontrollerad maskablation. ViPE återanvänder däremot explicit befintliga masker. En enda kedja genom ett klipp med motbilder är fortfarande ingen bekräftad gemensam plats.

## Kostnad

Mätt ackumulerad GPU-funktionstid hittills: 14.48 min. Konservativ debiterad övre gräns, inklusive pågående reservationer: 41.15 av 75 min. En pågående reservation är ingen. Se budget.json för varje start och avslut.

GPU s/ruta i tabellen avser det tidsintervall som står i kandidatens timing.json. För Map/DA3 är det modellkörning, för ViPE omfattar det även dess dokumenterade kamerakedja och djupberäkning. Modellstart, JPEG-arbete och överföring ingår inte på samma sätt. PyTorch-toppen är allokerat tensor-VRAM, inte hela enhetens minnesförbrukning. Total lokal väggtid inkluderar hämtning av råutdata och är mycket längre än inferensen. Separat fysisk kallstart hos Modal kunde inte isoleras.

MapAnything laddade modellen på cirka 35–38 s; DA3 på cirka 16–18 s. Fullrutekörningarna på A100-80GB använde cirka 32,4 respektive 18,3 GB allokerat VRAM som mest. CPU-byggen och CPU-hämtning av vikter är separata och kostar inga GPU-minuter här. Kostnad i kronor/dollar har inte mätts.

## Licenser och blockerade kandidater

Primärkällor hämtades under utvärderingen. Fulla texter, modellkort, API-metadata, felaktiga 404-länkar och kodrevisioner finns i sources/. Licensbesluten och exakta ägaråtgärder finns i licenser.json. Inga gated vikter hämtades och inga ansökningar, registreringar eller klickgodkännanden gjordes. ViPE-imagen bygger på offentlig nvidia/cuda:12.8.1-devel-ubuntu22.04, vars startmeddelande anger NVIDIA Deep Learning Container License och att användning innebär acceptans. Ägaren har inte lämnat något separat godkännande här; dessa basimagevillkor måste också granskas inför drift, se licenser.json.

| Kandidat | Kod | Vikter / beroenden | Kommersiellt | Källor |
|---|---|---|---|---|
| MapAnything Apache | Apache-2.0 | Apache-2.0 (facebook/map-anything-apache ONLY) | yes | [kod](https://github.com/facebookresearch/map-anything/blob/3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9/LICENSE), [vikter](https://huggingface.co/facebook/map-anything-apache/blob/00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a/README.md) |
| DA3 Apache combination: BASE + METRIC-LARGE | Apache-2.0 | Apache-2.0 for both selected checkpoints | yes | [kod](https://github.com/ByteDance-Seed/Depth-Anything-3/blob/3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/LICENSE), [vikter](https://huggingface.co/depth-anything/DA3-BASE/blob/f4a6c9b3c95e41c82048423d3493a81ec3fa810e/README.md) |
| ViPE (tested configuration: DROID + GeoCalib + MoGe2, existing person masks) | NVIDIA-authored Apache-2.0; selected DROID/LieTorch BSD-3-Clause; GeoCalib Apache-2.0; MoGe2 MIT | MoGe2 MIT; GeoCalib CC-BY-4.0; DROID repository BSD-3-Clause but a separate explicit grant for the externally hosted checkpoint was not located | unclear | [kod](https://github.com/nv-tlabs/vipe/blob/ead2e008bc055310121736a49ff306bba50d10dc/LICENSE), [vikter](https://github.com/cvg/GeoCalib/blob/main/LICENSE-WEIGHTS) |
| MegaSaM | Apache-2.0 (own code) | Own other materials CC-BY-4.0; required UniDepth code/weights CC-BY-NC-4.0 | no (published complete pipeline) | [kod](https://github.com/mega-sam/mega-sam/blob/main/LICENSE), [vikter](https://github.com/mega-sam/mega-sam/blob/main/README.md#copyright) |
| VGGT / VGGT-1B-Commercial | Custom VGGT licence with acceptable-use policy (military use restricted) | Original VGGT-1B CC-BY-NC-4.0; commercial checkpoint custom VGGT-AUP, manually gated | yes conditional on owner's acceptance and granted access; blocked in this evaluation | [kod](https://github.com/facebookresearch/vggt/blob/main/LICENSE.txt), [vikter](https://huggingface.co/facebook/VGGT-1B-Commercial) |
| VGGT-Omega | FAIR Noncommercial Research License | FAIR Noncommercial Research License | no | [kod](https://github.com/facebookresearch/vggt-omega/blob/main/LICENSE), [vikter](https://github.com/facebookresearch/vggt-omega/blob/main/LICENSE) |
| Pi3 / Pi3X | BSD-3-Clause | CC-BY-NC-4.0, explicitly stated by upstream repository | no | [kod](https://github.com/yyfz/Pi3/blob/main/LICENSE), [vikter](https://github.com/yyfz/Pi3#-license) |
| DUSt3R / MASt3R / MASt3R-SLAM | CC-BY-NC-SA-4.0 | Non-commercial; MASt3R CHECKPOINTS_NOTICE retains training-dataset restrictions | no | [kod](https://github.com/naver/dust3r/blob/main/LICENSE), [vikter](https://github.com/naver/mast3r/blob/main/CHECKPOINTS_NOTICE) |
| HSfM | MIT (own code) | Pipeline uses NC DUSt3R and separately licensed SMPL/MANO/SMPL-X body assets | no for published complete pipeline | [kod](https://github.com/hongsukchoi/HSfM_RELEASE/blob/main/LICENSE), [vikter](https://github.com/hongsukchoi/HSfM_RELEASE/blob/main/README.md) |
| StudioRecon (SIGGRAPH 2026) | Custom non-commercial research/evaluation only | Separate dependencies; Pi3, SAM3, GEN3C, SMPL etc retain their restrictions | no | [kod](https://github.com/sisyphm/StudioRecon/blob/master/LICENSE.md), [vikter](https://github.com/sisyphm/StudioRecon/blob/master/docs/THIRD_PARTY.md) |
| OVOW / RHINO / TRAM | MIT / Apache-2.0 / MIT for own code | Complete dependency rights not cleared; OVOW explicitly includes NC components, RHINO requires separate body-model licences, TRAM requires registered SMPL/SMPLify assets | no for OVOW default; unclear/blocked for RHINO and TRAM full pipelines | [kod](https://github.com/yisuanwang/OVOW/blob/main/README.md), [vikter](https://github.com/lxxue/RHINO/blob/main/README.md) |
| DVLT (new video geometry lead) | Apache-2.0 for majority, VGGT-derived files retain VGGT terms | NVIDIA OneWay Noncommercial License | no | [kod](https://github.com/nv-tlabs/dvlt/blob/main/README.md), [vikter](https://github.com/nv-tlabs/dvlt/blob/main/LICENSES/NVIDIA-LICENSE.txt) |

VGGT Commercial är manuellt gated: ägaren måste själv ansöka, lämna namn, födelsedatum, land, organisation och roll, godta VGGT/AUP och Meta:s integritetsbehandling samt få åtkomst beviljad. Originalvikterna är NC. För övriga NC-kandidater krävs ett separat kommersiellt tillstånd; att bara acceptera en NC-licens ger inte produktionsrätt. Pi3:s BSD-etikett på HF motsäger det uttryckliga NC-viktvillkoret i upstream README; vi valde det restriktiva, tydliga villkoret.

## Rekommenderad inmatning och kvarstående arbete

Läs PLATS-INMATNING.md. Behåll accepterade kameror och låt en ny kamera vara en avvisningsbar hypotes. Kontrollera bakgrundspixlar och stativdrift före användning. Ge plats.py observerade kameror, djup, statiska masker, mätstödda plan och per-tagningsförbindelser, därefter möbelmallar och ankare. Håll observation och antagande åtskilda.

Lås en gemensam skala från identifierade fysiska mått; skala bakgrund och kameratranslation tillsammans. Bygg kroppens världsläge med den oförändrade kamerarumspositionen: `X_world = R @ x_body_cam + C`. Skala aldrig bara kroppens cam_t för att nå golvet. Ett K-byte kräver ny kroppsestimering eller en bildbunden ompassning med fasta kroppslängder. En rigid transform av kamera, kroppar och rum kan därefter sätta golvet till z=0.

Detta löser inte osynlig geometri, oöverlappande motbilder, okänd verklig personlängd, speglar/glas, verklig zoom, rullande slutare eller kroppens egna posefel. Ingen rendering har godkänts som 1:1 här.

## Köra om från projektroten

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/prepare_inputs.py
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/prepare_extra.py
# En kandidat i taget; offentlig CPU-förberedelse före GPU:
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/run_bank.py mapanything prepare
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/run_bank.py mapanything evaluate
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/run_bank.py da3 prepare
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/run_bank.py da3 evaluate
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/run_bank.py vipe prepare
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/run_bank.py vipe evaluate
# Lokala, begränsade mätningar utan modell:
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/baseline.py
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py baseline
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py mapanything
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py da3
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py vipe
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/refresh_background.py
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/fullclip_floor.py
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/size_checks.py
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/report.py
```

Runnern hoppar över färdiga timing.json och nollställer aldrig budgeten. Den reserverar högst 900 s per GPU-anrop, högst återstående uppstartsbudget innan första lyckade körning, och högst 4 500 s totalt. Serverns tidsgräns är reservationen minus 60 s. Oreglerad aktiv reservation stoppar nya starter. Efter kvotavbrott: läs RUM-LOGG.md och budget.json, kontrollera det gamla Modal-anropet innan eventuell avräkning. Behåll gamla resultat och använd ett nytt fallnamn för ett nytt försök.
