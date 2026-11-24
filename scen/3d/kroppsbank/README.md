# GEM-X: genomfört körprov, inget pipelinebyte

## Omprövning 10 nov kväll: behåll SAM, rätta golvsteget

Ägaren ville ha rå mot rå och lika filter i stället för rå GEM-X mot vår utjämnade slutkedja. Det är gjort. Domen blir: behåll SAM 3D Body. GEM-X är inte bättre när filtret är lika. Slutkedjans förlorade bildpassning kommer från golvsteget (och kontaktsteget), inte från utjämningen.

Mått: darr = medel av andra differensen för 15 leder i kamerarummet (cm/ruta²). IoU = median silhuett-IoU mot personmasken. kp = medianavstånd i px till GEM-X:s egna 2D-punkter. Filtret är en symmetrisk Gausskärna (sigma i rutor) på rotbana och rotrelativa leder och nät, samma för alla metoder.

| spår | rå SAM s0 / s1 / s2 | bästa GEM-X s0 / s1 / s2 | slutkedjan | slutkedjan utan golv/kontakt |
|---|---|---|---|---|
| notan S1 | 0,886/0,621 · 0,187/0,621 · 0,052/0,622 | 0,722/0,611 · 0,226/0,610 · 0,082/0,611 | 0,196/0,399 | 0,203/0,650 |
| notan S4/1 | 0,394/0,781 · 0,092/0,781 · 0,035/0,781 | 0,166/0,736 · 0,044/0,736 · 0,020/0,736 | 0,183/0,623 | 0,175/0,764 |
| notan S4/4 | 1,285/0,507 · 0,309/0,507 · 0,105/0,506 | 3,625/0,526 · 0,687/0,526 · 0,215/0,527 | 0,194/0,516 | 0,243/0,517 |
| råvara S5 | 5,37/0,633 · 1,40/0,625 · 0,525/0,632 | 2,97/0,595 · 0,784/0,598 · 0,287/0,598 | 1,12/0,634 | 1,12/0,634 |
| råvara S9 | 1,84/0,578 · 0,449/0,574 · 0,164/0,575 | 0,891/0,567 · 0,261/0,566 · 0,099/0,565 | 0,612/0,580 | 0,612/0,580 |

Varje cell är darr/IoU. Bästa GEM-X är stock-CLI med ärvd K (S1, S4/1, S9), stock med default K (S5) och vår adapter (S4/4, som stock inte följer). kp: S1 SAM 11, GEM-X 36, slutkedjan 198 (utan golv 11). GEM-X missar armgesterna i S1. I S9 är GEM-X bättre på kp (29 mot 37).

Vid lika darr har SAM högre IoU på alla fem spåren. GEM-X är lugnare vid samma filter på fyra av fem, men det köps med sämre bildpassning, och ett något starkare filter på SAM ger samma lugn utan att IoU sjunker.

Uppsättningsfel som prövats:
- Bildfrekvens, tidsstämplar och storlek: alla klipp är 30 fps, 576×1024 och har steg 1/30 s utan tappade rutor. Detta var inte orsaken.
- Vår spårningsadapter var en orsak. personer.json-rutorna darrar (centrum S1 6,2, S5 11,5, S9 16,4 px/ruta²; stock-spåraren S1 2,8, S9 1,8). Stock gav darr S1 0,722 mot 1,432, S4/1 0,166 mot 0,585 och S9 0,891 mot 1,423. IoU ändrades högst 0,006.
- Intrinsik: ärvd och default K ger samma resultat i notan (S1 0,722 mot 0,786). I S5 ger default K 2,97 mot 4,91, men IoU är densamma.
- Kameraläge: static är sämre än background (S1 1,769 mot 1,432, S4/1 0,681 mot 0,585). Det var inte orsaken.
- Hela oklippta notan: kunde inte prövas. Källfilen har klippbyten, och stock-CLI med background stoppar ("Background camera tracking was unavailable for more than one second"). Tagningarna är 73–85 rutor och modellens fönster är 120, så ingen tyst kapning sker. Frågan är obesvarad.
- Mätt utdata: avsedda incam-parametrar, translation applicerad en gång. Det är ingen egen rekomposition och därmed inte orsaken.

Golvsteget (`steg_golv` i `ingest/ingest_klipp.py`) multiplicerar bara `cam_t` med `golv_skala`, inte kroppen. MHR-origo ligger långt från den synliga kroppen, så kroppen flyttas i bild. Rotförskjutningen slutkedjan minus rå SAM är exakt (golv_skala − 1)·cam_t (restfel 0,00 cm) med golv_skala 0,849 i S1 och 1,105 i S4/1. Kontaktsteget (`kontakt.py`) lägger till en horisontell förskjutning som också syns.

Videor (30 fps, H.264, tre paneler: slutkedjan, rå SAM med sigma 1, bästa GEM-X): `ut/jamforelse/notan-S1_sida-vid-sida.mp4`, `notan-S4_sida-vid-sida.mp4`, `ravara-S5_sida-vid-sida.mp4`. Stillbilder ligger i `ut/jamforelse/rutor/`.

Steg 2 bör vara att rätta golv- och kontaktstegen så att de skalar hela kroppen kring kameran (pose och cam_t tillsammans) eller inte flyttar den i bild alls. GEM-X ska inte integreras som kroppssteg. Dess världsbana och kontaktlogits kan prövas som indata till golv/kontakt, med SAM-posen kvar och utan riggbyte.

GPU: 29,8 min av 90 för hela GEM-X-arbetet (budget.json). Verktyg: `followup2_gemx.py` (configs, whole, curves, videos). Loggen finns i `GEMX-LOGG.md`.

Resten av filen beskriver första körprovet.

## Första körprovet

2026-11-10. Installationen och Body Motion fungerar på Modal. Alla fyra testtagningar är körda, inklusive båda spårade personerna i notan S4. Inga handvikter har hämtats.

Beslut: steg 2 startas inte. I råvara S5 är GEM-X sämre än den sparade slutsekvensen i både oberoende silhuett-IoU (0,595 mot 0,634) och kamerarumsdarr (5,65 mot 1,12 cm/ruta² efter modellens kontakt/IK). Rotrelativt darr är också högre (0,832 mot 0,630). Den sittande personen i notan S4 har 3,62 mot 0,19 cm/ruta². Vinsterna i notans silhuetter och fotkontakt väger inte upp detta som generell ersättning för de fyra proven. Detta är en bedömning av provet, ingen ny ägartröskel.

## Körning och budget

Bildbygge: 165,49 s, summan av fyra bildsteg i gemx_prepare.log. Första CPU-starten hade ett eget sökvägsfel (parents[3] på Modal), rättat före GPU. CPU-hämtning och importkontroll: 131,21 s; andra CPU-anropets totala väggtid 138,50 s. Kallstart, från GPU-anrop till första status: 41,48 s (inklusive kö, start och import).

L40S: 46 068 MiB rapporterat minne. Högsta nvidia-smi-prov vid 1 Hz: 6570 MiB. PyTorch-toppar: 3737261568 byte allokerat och 6287261696 byte reserverat. 1 Hz kan missa korta VRAM-toppar.

294 observerade personrutor; 324 predikterade personrutor inklusive 30 utfyllda rutor före S4:s person 4. Inferens: 45,166 s / 294 = 0,154 GPU-funktionssekunder per observerad personruta (0,139 per predikterad). Med modellens IK: 0,207. Hela GPU-funktionen, inklusive båda FK-/meshvarianterna, filskrivning och packning: 206,339 s, 0,702 s per observerad personruta. Det är väggtid på en GPU-funktion, inte CUDA-kärnprofilering.

Budgeten debiterar konservativt 5,565 av 90 GPU-minuter (anropets väggtid + 15 s avslutsmarginal). GPU-funktionens egen klocka visar 3,439 minuter; exakt fakturerad/allokerad GPU-tid är inte hämtad från Modal. En enda GPU-funktion kördes, sekventiellt. Inga reservationer kvar. Startbudgeten 30 minuter hölls.

## Jämförbara mått

J15 = medelnormen av ledpositionernas andra differens i cm/ruta², i kamerarum. Jrel = samma mått relativt bäckenet. Lägre är mindre darr, inte automatiskt bättre rörelse. IoU = median mot befintlig personmask. C och H = medianfel för tyngdpunkt respektive absolut höjdskillnad, procent av bildhöjden. IoU synlig klipper nätet vid maskens nedersta rad. Alla maskrutor prövas.

| Tagning/person | Backend | J15 | Jrel | IoU | IoU synlig | C % | H % |
|---|---|---:|---:|---:|---:|---:|---:|
| notan-S1/1 | rå SAM | 0,886 | 0,742 | 0,621 | 0,646 | 4,14 | 1,56 |
| notan-S1/1 | nuvarande slutsekvens | 0,196 | 0,178 | 0,399 | 0,410 | 4,88 | 4,30 |
| notan-S1/1 | GEM-X rå | 1,432 | 0,451 | 0,615 | 0,637 | 5,00 | 3,12 |
| notan-S1/1 | GEM-X + modellens kontakt/IK | 1,430 | 0,446 | 0,616 | 0,637 | 4,99 | 3,12 |
| notan-S4/1 | rå SAM | 0,394 | 0,316 | 0,781 | 0,781 | 0,71 | 2,73 |
| notan-S4/4 | rå SAM | 1,285 | 0,598 | 0,507 | 0,507 | 5,32 | 17,97 |
| notan-S4/1 | nuvarande slutsekvens | 0,183 | 0,118 | 0,622 | 0,622 | 5,39 | 13,28 |
| notan-S4/4 | nuvarande slutsekvens | 0,194 | 0,147 | 0,540 | 0,540 | 2,70 | 15,62 |
| notan-S4/1 | GEM-X rå | 0,585 | 0,162 | 0,736 | 0,736 | 1,02 | 2,34 |
| notan-S4/4 | GEM-X rå | 3,625 | 0,288 | 0,507 | 0,507 | 4,42 | 14,45 |
| notan-S4/1 | GEM-X + modellens kontakt/IK | 0,575 | 0,145 | 0,736 | 0,736 | 1,03 | 2,34 |
| notan-S4/4 | GEM-X + modellens kontakt/IK | 3,625 | 0,250 | 0,507 | 0,507 | 4,38 | 14,45 |
| ravara-S5/1 | rå SAM | 5,370 | 2,502 | 0,633 | 0,661 | 5,41 | 1,17 |
| ravara-S5/1 | nuvarande slutsekvens | 1,121 | 0,630 | 0,634 | 0,665 | 5,63 | 1,76 |
| ravara-S5/1 | GEM-X rå | 5,692 | 0,918 | 0,595 | 0,617 | 6,08 | 2,34 |
| ravara-S5/1 | GEM-X + modellens kontakt/IK | 5,646 | 0,832 | 0,595 | 0,618 | 6,07 | 2,34 |
| ravara-S9/1 | rå SAM | 1,843 | 1,378 | 0,578 | 0,596 | 7,43 | 0,39 |
| ravara-S9/1 | nuvarande slutsekvens | 0,612 | 0,520 | 0,580 | 0,604 | 7,64 | 0,39 |
| ravara-S9/1 | GEM-X rå | 1,423 | 0,595 | 0,570 | 0,593 | 6,58 | 0,39 |
| ravara-S9/1 | GEM-X + modellens kontakt/IK | 1,363 | 0,545 | 0,570 | 0,593 | 6,57 | 0,39 |

Baslinjerna kommer från ut/sam-raw och ut/slutsekvens. Slutsekvensen är sekvens_*.npz med sparade golv-/kontaktändringar. Kompilatorns senare kamera-/stödkompensation i plan.json är inte återspelad. S1:s stora bildförskjutning i slutsekvensens överlägg ska därför inte läsas som en granskning av dess senaste film.

Masken är en union av personmasker; jämförelsen beskärs till respektive spårruta och andra predikterade kroppars silhuetter undantas. Kläder, bord, grova maskpixlar och naken kroppsgeometri skiljer sig åt. MHR:s sparade silhuetter använder lod1-hud utan alla korrektiver; GEM använder SOMA MID med korrektiver. IoU mäter bildpassning, inte exakt ledposition.

## Ledmappning

Anatomiska ledpar för samma body15-urval som baslinjerna. MHR-index och SOMA-index är nollbaserade. Detta är en mappning för mätning, ingen rotationstransfer eller bevisad retarget.

| MHR | SOMA | MHR-index | SOMA-index |
|---|---|---:|---:|
| root | Hips | 1 | 0 |
| l_upleg | LeftLeg | 2 | 67 |
| r_upleg | RightLeg | 18 | 72 |
| l_lowleg | LeftShin | 3 | 68 |
| r_lowleg | RightShin | 19 | 73 |
| l_foot | LeftFoot | 4 | 69 |
| r_foot | RightFoot | 20 | 74 |
| c_neck | Neck1 | 110 | 4 |
| c_head | Head | 113 | 6 |
| l_uparm | LeftArm | 75 | 12 |
| r_uparm | RightArm | 39 | 40 |
| l_lowarm | LeftForeArm | 76 | 13 |
| r_lowarm | RightForeArm | 40 | 41 |
| l_wrist | LeftHand | 78 | 14 |
| r_wrist | RightHand | 42 | 42 |

Ordningen verifierades exakt mot SOMA77_JOINT_NAMES i den låsta upstream-filen gem/motion/frontend/joint_sets.py. USD-riggens virtuella Root och 32 procedurvridben ingår inte i de 77 offentliga lederna. MHR och SOMA har olika identiteter och leddefinitioner; det finns ingen 3D-sanning i dessa klipp.

## Dolda ben och sittande

Samma befintliga ben_synliga-flagga används för alla metoder. Det är ett äldre projektions-/maskmått, ingen manuell annotering av varje dold led. Där flaggan saknar dolda rutor visas saknas. Spannet är största diagonal av en benleds rotrelativa xyz-intervall i cm, inte ett anatomiskt rörelseomfång. Alla xyz-intervall och djupspann finns i gemx_matningar.json.

| Tagning/person | Backend | Dolda rutor | Dold J | Dold Jrel | Dolt spann cm | Ben-J, alla spårrutor | Benspann, alla cm |
|---|---|---:|---:|---:|---:|---:|---:|
| notan-S1/1 | rå SAM | 73 | 1,128 | 0,525 | 4,82 | 1,128 | 4,82 |
| notan-S1/1 | nuvarande slutsekvens | 73 | 0,180 | 0,123 | 5,36 | 0,180 | 5,36 |
| notan-S1/1 | GEM-X rå | 73 | 1,621 | 0,486 | 6,26 | 1,621 | 6,26 |
| notan-S1/1 | GEM-X + modellens kontakt/IK | 73 | 1,539 | 0,467 | 6,10 | 1,539 | 6,10 |
| notan-S4/1 | rå SAM | 85 | 0,240 | 0,183 | 2,31 | 0,240 | 2,31 |
| notan-S4/4 | rå SAM | 0 | saknas | saknas | saknas | 1,356 | 7,50 |
| notan-S4/1 | nuvarande slutsekvens | 85 | 0,113 | 0,030 | 2,55 | 0,113 | 2,55 |
| notan-S4/4 | nuvarande slutsekvens | 0 | saknas | saknas | saknas | 0,134 | 7,45 |
| notan-S4/1 | GEM-X rå | 85 | 0,582 | 0,153 | 4,52 | 0,582 | 4,52 |
| notan-S4/4 | GEM-X rå | 0 | saknas | saknas | saknas | 3,693 | 6,91 |
| notan-S4/1 | GEM-X + modellens kontakt/IK | 85 | 0,579 | 0,148 | 3,18 | 0,579 | 3,18 |
| notan-S4/4 | GEM-X + modellens kontakt/IK | 0 | saknas | saknas | saknas | 3,699 | 6,53 |
| ravara-S5/1 | rå SAM | 46 | 5,672 | 2,556 | 58,37 | 5,672 | 58,37 |
| ravara-S5/1 | nuvarande slutsekvens | 46 | 0,998 | 0,347 | 23,93 | 0,998 | 23,93 |
| ravara-S5/1 | GEM-X rå | 46 | 6,078 | 1,131 | 36,50 | 6,078 | 36,50 |
| ravara-S5/1 | GEM-X + modellens kontakt/IK | 46 | 5,959 | 0,941 | 36,53 | 5,959 | 36,53 |
| ravara-S9/1 | rå SAM | 35 | 2,466 | 1,420 | 14,00 | 2,466 | 14,00 |
| ravara-S9/1 | nuvarande slutsekvens | 35 | 0,704 | 0,427 | 10,19 | 0,704 | 10,19 |
| ravara-S9/1 | GEM-X rå | 35 | 1,557 | 0,562 | 15,97 | 1,557 | 15,97 |
| ravara-S9/1 | GEM-X + modellens kontakt/IK | 35 | 1,435 | 0,482 | 13,11 | 1,435 | 13,11 |

## Fotglidning

S4/person 4 ger 50 vänster- och 51 högerintervall med källa i bild/mask enligt rå SAM:s vrist och tå. Samma intervall används för alla fyra metoder. Kontakt antas med vakts befintliga diagnostik: höjd < 6 cm och vertikalt steg < 1 cm. Det är inte oberoende kontaktannotering. För övriga testpersoner finns inga sådana synliga intervall: saknas, inte noll glidning.

MHR mäts i sin ingestvärld, GEM i sin egen Y-upp-värld, rå respektive kontakt/IK. Horisontell steglängd påverkas inte av världens translation eller yaw; metriska skalor är fortfarande monokulära antaganden. Ingen platsjustering eller absolut golvrest har verifierats.

| Backend, notan S4/person 4 | Vänster median/p90 cm/ruta | Höger median/p90 cm/ruta |
|---|---:|---:|
| rå SAM | 0,682/1,405 | 0,769/1,714 |
| nuvarande slutsekvens | 0,104/0,265 | 0,109/0,278 |
| GEM-X rå | 0,370/0,918 | 0,291/0,499 |
| GEM-X + modellens kontakt/IK | 0,043/0,073 | 0,087/0,150 |

Modellens IK förbättrar alltså fotglidningen i dess egen värld. Kamerarumsdarret för samma person är nästan oförändrat. Om varje metod själv måste projicera båda fotpunkterna i masken blir GEM:s kvalificerade kontaktintervall noll; det är en täckningsbrist och redovisas separat i foot_sliding. Det får inte tolkas som perfekt kontakt.

## Tidsmått per person

| Tagning/person | Predikterade rutor | Inferens s | Kontakt/IK s | Med FK och filer s |
|---|---:|---:|---:|---:|
| notan-S1/1 | 73 | 13,36 | 11,95 | 32,73 |
| notan-S4/1 | 85 | 9,89 | 0,94 | 17,91 |
| notan-S4/4 | 85 | 9,67 | 0,91 | 23,33 |
| ravara-S5/1 | 46 | 6,82 | 0,91 | 13,75 |
| ravara-S9/1 | 35 | 5,43 | 0,93 | 13,67 |

Första IK-körningen inkluderar Warp-kompilering. Tidigare SAM-loggar har medianer 2,134 / 0,586 / 0,541 / 0,530 s per jobb för S1, S4, S5, S9. Dessa är historiska körningar med annan start-/batchningssituation och okänd motsvarande VRAM; de är inte ett nytt kontrollerat hastighetstest på samma GPU.

## Bildgranskning

Jag har tittat på alla åtta GEM-remsor (fyra tagningar gånger rå/kontakt-IK), åtta källrutor per remsa, samt de fyra sparade slutsekvensremsorna.

Notan S1: GEM:s bål och huvud ligger över personen. Slutsekvensens sparade kamerarumsöverlägg är tydligt förskjutet uppåt; planens senare kompensation ingår inte här. GEM fångar upplyfta händer i grova drag, men armbågar/handleder och dold underkropp är osäkra. Rå/IK-remsorna ser mycket lika ut. Bildpassningen blir bättre än denna slutsekvens, men 3D-darr och dold benrörelse blir högre.

Notan S4: stående personens huvud, armar och bål följer bilden rimligt; den sittande personen kommer in i granskningen först när den finns i spåret. Sittande knän och fötter är grövre och passar inte lika väl som överkroppen. Ingen stor kroppsvändning syns mellan de åtta provrutorna. Darrmåttet visar ett stort kamerarumsproblem som en gles remsa inte kan visa som en film. IK förbättrar fotbanan i GEM:s värld, men flyttar inte bort problemet i kamerarummet.

Råvara S5: GEM följer framåtlutningen mot disken, men handlederna hamnar ofta förskjutna från de synliga händerna och de dolda benen vandrar när personen lutar sig. Kamerarumsspannet för dolda ben är 36,5 cm efter IK, mot 23,9 cm i slutsekvensen. Samtidigt är dess silhuettpassning sämre. IK-remsan visar ingen tydlig förbättring av överkroppens passning.

Råvara S9: bröst och huvud följer närbilden ungefär. En handled försvinner bakom vågen i modellen medan händerna börjar lyftas; senare går armar mot ansiktet, med synliga avvikelser. Kroppen fortsätter utanför bild utan verifierbart underlag. Modellens IK återställer inte detaljrörelsen.

Ingen ny Blenderfilm eller sida-vid-sida-film har byggts: det tillhör steg 2 och dess kvalitetsvillkor uppfylldes inte. De granskade bilderna är diagnostiska källöverlägg, inte en slutfilm.

## Riggrutt och pipeline

Ingen riggrutt har satts i produktion. SOMA:s MHR-backend är en identitetsbackend; detta bevisar inte en exakt omvandling av GEM:s 77 rotationer till MHR:s 127 leder/parametrar. Inget konverteringsfel har mätts och ingen handgjord retarget har levererats. En eventuell fortsättning bör först pröva en direkt SOMA-rigg enligt alternativ a för att bevara modellens egen geometri.

Nedströmsläsning visar direkta MHR-beroenden i kompilera.py, kalla_bygg.py, mhr_rig.py, trohet/stöd, props/ankare och kvalitet. --kropp gemx finns därför inte i ingest efter detta prov. Kompilering, kvalitetsrapport, props/ankare, platsjustering, Blender --plan, film och webbläsarexport under forvarld är inte verifierade/fungerande med GEM-X. SAM-vägen är orörd. Inga gamla temporal-, golv-, kontakt- eller stödsteg har tagits bort eller mätts med vakt som GEM-ablation. Inga nya ingest-/kontraktkommandon har införts.

GEM:s råa värld sparas, men dess koordinater är inte platsens koordinater. Kameraläge är upstream background (approximerad bakgrundsrotation), intrinsics övertagna från manifestet och märkta antagna. Varken ankare, COLMAP-skala, gemensamt golv, världstransform eller rest har verifierats för GEM. Dessa värden får inte användas som färdig platsplacering.

## Begränsningar och licenser

Dolda kroppar saknar facit. Närbilder ger inte full kroppsinformation. Body Motion har hand-/ansiktsleder, men detta prov har ingen separat handinferens, inga granskade fingermått och ingen ansiktsmimik. Stabilitet innebär inte att osynlig rörelse är rätt.

GEM-kod: Apache 2.0 som standard med filspecifika undantag i ATTRIBUTIONS.md (bland annat OpenMDW, MIT, BSD och SAM-villkor). Behåll motsvarande licenser och upphovsrättsnotiser vid distribution. GEM:s modellkort hänvisar vikterna till NVIDIA Open Model License: kommersiell användning tillåts enligt avtalet; villkor/notiser ska följa med vid vidare distribution. NVIDIA gör inte anspråk på utdata. HF-repots LICENSE-fil säger samtidigt Apache 2.0. Denna motsägelse är dokumenterad, inte juridiskt avgjord.

SOMA-X-kod och dessa SOMA v0.3.3-tillgångar: Apache 2.0. Andra identitetsbackendars separata modeller får inte automatiskt samma licens. Inga MHR-identitetstillgångar eller handvikter behövdes här.

Detektor: OpenMMLab YOLOX-X HumanArt ONNX hämtad från den officiella MMPose-adressen. MMPose-koden är Apache 2.0. Det nedladdade ONNX-arkivet innehåller ingen LICENSE/NOTICE. Separata villkor för just vikterna och HumanArt-underlaget har inte kunnat verifieras; kodlicensen räcker inte som bevis för dem. Med våra spår kringgås själva detektionen, men upstream skapar fortfarande en ONNX-session.

Händer: inga EgoHand-/handdetektorvikter hämtade och inga gatevillkor accepterade. Ägaren behöver själv granska EgoHand-v1:s OpenMDW 1.1 och vid begärd HF-gate själv ordna åtkomst/acceptera de visade villkoren. Sparad HF-API-metadata säger gated=false, vilket avviker från uppgiften om gate; faktisk checkpointåtkomst har inte prövats och ska inte antas vara fri.

Primärkällor: [GEM-installation](https://github.com/NVlabs/GEM-X/blob/4aef1452e5df171deff4f293c08e643eb450981e/docs/INSTALL.md), [GEM-modellkort](https://huggingface.co/nvidia/GEM-X), [NVIDIA-avtal](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/), [SOMA](https://huggingface.co/nvidia/SOMA-X), [MMPose-licens](https://github.com/open-mmlab/mmpose/blob/main/LICENSE), [EgoHand](https://huggingface.co/nvidia/EgoHand-v1). Verifierade revisioner och nedladdade källor finns i kallor/gemx_verified.json och gemx_live_*; CPU-licensinventering i ut/gemx/asset_audit.json.

## Återuppta eller upprepa

Kör från projektroten, alltid med scen/.venv/Scripts/python.exe och PYTHONIOENCODING=utf-8. Ingen lokal inferens behövs. Modal-volym: gemx-body-v033. GPU-provet och CPU-licenskontrollen är avslutade.

```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode prepare
scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode evaluate
scen/.venv/Scripts/python.exe -B scen/3d/kroppsbank/evaluate_gemx.py
scen/.venv/Scripts/python.exe -B scen/3d/kroppsbank/report_gemx.py
```

evaluate-läget återanvänder färdiga tagningar. Gör inte om GPU-provet genom att ta bort filer: kontrollera först budgeten och gör en ny separat körplan. Budgetens reservation skyddar avbrott; den ska avräknas mot Modal innan en ny GPU startas. Den lokala drivaren är byggd för det genomförda första provet, inte för automatiska obegränsade omförsök.

Utdata per tagning/person: raw.pt, contact_ik.pt (nativa SOMA-parametrar, villkor, kamera och kontaktlogits), raw_joints.npz/contact_ik_joints.npz (77 leder i kamera och värld, intrinsics och observed), kameramesh per ruta, faces.npy, joint_names.json och timing.json. Per tagning finns overlay_raw.jpg och overlay_contact_ik.jpg. Samlade mått: gemx_matningar.json. Äldre filer som ändrats har originalkopia i fore_gemx med samma projektrelativa sökväg. Arbetsloggen är GEMX-LOGG.md.
