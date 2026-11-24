# Motprov 1: kod och antaganden

Kört: `.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py basic` från `6-lokalitet/`. Testet söker klippnamn, tagnings-id och långa numeriska id:n och inventerar alla numeriska AST-litteraler. Fullständig råinventering: [code-scan.json](code-scan.json). De tre filerna lästes även i sin helhet, inklusive villkor på `nyckel`, tagning och sökvägar.

Enda namnträffen: `modal_obs.py:3`, körningsexemplet `duepiani-7650849186912406806:duepiani` i docstringen. Inga exekverbara klippnamn, tagnings-id eller klippvisa värdetabeller hittades. `observera.py:55`, `lokalitet.py:619` väljer delat ingest före lokalt ingest; klippnyckeln används till sökvägen, inte ett särskilt geometrirecept. Detta är en granskning av dessa tre filer, inte av de modeller, kroppspaket och importerade hjälpfunktioner som försörjer dem.

Alla identifierade numeriska modellantaganden och urvalsregler nedan är gemensamma för klippen. Det finns inget belägg här för att en viss konstant endast passar ett klipp. Däremot säger koden uttryckligen att 20°-priorn gäller matklipp i 9:16 och att GeoCalib nedviktas för beteendet i detta material. Det begränsar hur starkt ordet ”allmän” kan läsas. ”Nej” i sista kolumnen betyder att värdet inte anges i `RAPPORT.md`; märkning i kod/utdata räknas separat.

| Källa | Antagen konstant eller regel | Uttalad i RAPPORT.md? |
|---|---|---|
| lokalitet:74 | OneFormer-segment med poäng <0,75 får inte rösta om lod, höjd eller lådobjekt | Ja, steg 3 |
| lokalitet:94–110 | Dominant normal: fönster 12°, minst 30 normaler, högst 60 kandidater, seed 0, sex förfiningar, minst fem stödnormaler; annan axel ska ligga inom 20° från ortogonal | Nej |
| lokalitet:124–134 | Högst 20 000 normaler, seed 1; tre Manhattan-axlar; stöd minst max(40, 4 %); tredje axeln kan bli kryssprodukten | Nej för talen; Manhattan-principen finns i docstring, inte rapportens numeriska redovisning |
| lokalitet:143–153 | Normalröster: 20° för golv/tak/topp, kärl vikt 0,5; vägg 15°, felgränser absolut skalärprodukt 0,5/0,6; vikter golv 3, tak 2, topp 1,5, vägg 1, felvägg −2, felgolv −2 | Nej |
| lokalitet:154–166 | Uppåtvektorns bild-y >0,25 förbjuds med −10^9; inget val om poäng <−10^8 | Nej |
| lokalitet:156–157 | Kamera tittar högst 20° uppåt, annars −10^9 | Ja, fysisk prior |
| lokalitet:158–159 | Stor rullningskomponent: abs(u_x)>sin(35°) ger straff 0,5 × antal normaler | Nej; detta är en komponentgräns, inte exakt en Euler-rollgräns |
| lokalitet:160–172 | Bålbonus 0,15 × antal normaler inom 20°; bålklassning vid skalärprodukt >0,9; förfining av stödnormaler inom 15°, >30 pixlar | Nej; bålbonusen används inte av huvudflödets `lodlinje(..., None)` |
| lokalitet:200–211 | Färg: reserv #888888 vid <10 pixlar; palett först >50, högst cirka 4 000 prov, tre kluster, 20 iterationer, epsilon 1,0, två k-means-försök | Nej |
| lokalitet:221–242,264–266 | 2D-registrering: varannan kroppsbild, ledpoäng >0,5, minst tre leder, medianfel högst 350 px, minst tolv observationer; soft-L1 15 px; translationsgränser ±1,5/±2,0/±1,5 m | Nej |
| lokalitet:257,274–299 | Minst fem projicerbara leder; dubletter vid median-IoU >0,4 och minst tre gemensamma rutor, eller 3D-bålavstånd <0,6 m | Endast 0,6 m nämns i steg 2 som begränsning; övriga värden nej |
| lokalitet:317–321 | Golv: >max(40 pixlar, 0,5 % giltiga pixlar), percentiler 2/98, marginal 0,6 m, tjocklek 0,04 m, centrum z=−0,02 m | Endast 0,5 % anges, steg 3 |
| lokalitet:328–344 | Vägg minst 40 pixlar, övrig möbel 25; väggnormalens horisontalkomponent minst 0,3, percentiler 3/97, vägg minst 0,15 m bred/hög; underkant klipps vid golv, tjocklek 0,04 m | Nej |
| lokalitet:346–361 | Möbeltopp inom 25° från lod och minst tolv punkter; annars 95:e percentilen; planutbredning percentiler 4/96; djup <0,25 m ersätts av 0,40 m; bredd minst 0,1 m, topp inom 0,15–2,6 m | Nej; det ersatta djupet märks i objektets `antaganden` |
| lokalitet:364–368 | Om möbelns femte höjdpercentil >0,6 m antas väggmontering; annars botten=0 och golvstående | Nej; märks i objektets `antaganden` |
| lokalitet:381–401 | Mat minst 15 pixlar; mat/kärl kopplas med 5×5-dilatation; radie 95:e percentilen, måste ligga 0,03–0,40 m; skål/bricka om >40 % av etiketterna | Nej |
| lokalitet:407–432 | Fusion 1/σ²; MoGe σ=max(3°, median av rutornas avvikelse); GeoCalib σ≥1,5°, saknad osäkerhet=10°; GeoCalib σ×4 vid >20°; bål σ=6°; strykning >2,5σ i en omgång, återanvänd alla om ingen överlever | Ja för 1/σ², 3°, ×4, 20°, 6° och 2,5σ; nej för 1,5°, reserv 10° och återtagning av alla |
| lokalitet:441–478 | SIFT högst 4 000 punkter, översta 6 % maskas, minst 50 punkter/bild, kvottest 0,75; minst 40 matchningar/2D-inliers; MAGSAC 1,5 px, 0,999, 10 000 iterationer; 3D-RANSAC 400 försök, seed 0 | Rapporten nämner textmask, SIFT och MAGSAC, men inte talen; 40 är en tidigare grind än de slutliga 20 |
| lokalitet:475–498 | 3D-par minst 20; baslinje minst 0,10 m; resttröskel 0,10 m; slutkant minst 20 och 25 % inliers | Ja för 0,10 m rest, 20 slut-inliers och 25 %; nej för minsta baslinje |
| lokalitet:523–578 | Nätrutsteg 3; relativt djupsprång högst 6 %; personmask dilateras 3×3, andra rutors personmask 5×5; fyllnads-Gauss σ=4/12/36, viktstöd >0,001; minst åtta trianglar/bit | Steg 3 i halvupplösning och djupsprång nämns; övriga tal nej |
| lokalitet:626,639,669–675 | Virtuell sensor 36 mm, kvadratiska pixlar, huvudpunkt (0,5,0,5); MoGe-djup ändras med fokalkvoten så kropp och rum delar strålar | Samma fokal beskrivs; 36 mm/huvudpunkt nej. 36 mm är en enhetskonvention, inte belägg för telefonens fysiska sensor |
| lokalitet:643 | Kroppsregistrering startar vid kamera (0,0,1,38 m) | Nej |
| lokalitet:654–659 | Spår utan 2D-stöd: fel >max(3 × bästa felet, 120 px); bästa spår behålls även om alla annars faller | Nej |
| lokalitet:689–701 | Personytans skalprov: fönster 5×5, minst tre personpixlar/led och tre giltiga ledprov; kroppens bål-z minus 0,08 m jämförs med ytans z | Nej; 0,08 m här är ett antaget avstånd från led till framyta, skilt från fotledens 0,08 m |
| lokalitet:703 | Utan kroppsskala: MoGe-skala=1 | Rapporten nämner metrisk skattning generellt; reservvärdet anges inte. Utdata märker den antagen |
| lokalitet:709–719 | Stående bål antas peka uppåt; reserv A-rotation, annars bildens uppåt [0,−1,0] | Bål som vittne ja; reservreglerna nej |
| lokalitet:735–749 | Stående person antas ha kontakt; golv kräver >max(40, 0,5 %); median golvavstånd >0,2 m; minsta fotledens höjd får +0,08 m suloffset; skala=fothöjd/golvavstånd | Kontakt nämns som resultat; ekvationen, 0,2 m och 0,08 m redovisas inte |
| lokalitet:750–776 | Kamerahöjd från golv, annars fötter +0,08 m; ingen kontroll av stående pose i reservgrenen | Rapporten nämner golv/fötter; suloffset och reservgrenens poseoberoende nej |
| lokalitet:768–774 | Reservhöjd: stödnormal inom 25°, >20 pixlar; bänk/bord/spis antas 0,90 m hög; annars kamerahöjd 1,40 m | 1,40 m ja, steg 3; 0,90 m, 25° och 20 pixlar nej. Båda höjdantagandena märks i utdata |
| lokalitet:824–838 | Mat följer hand om avstånd till centrum minus halva diametern <0,15 m; annars statisk. Fast tjocklek 0,07 m, skål 0,10 m | Nej i RAPPORT.md; 0,15 m står i lokalitet-docstringen |
| lokalitet:7,538–547,802–805,845 | Statisk kamera per tagning; samma pixelstråle används för bakgrund från andra nyckelrutor, statiska objekt från mittrutan | Ja, steg 1; nyckelrutorna visar undantag i bl.a. 08burgerkebab S8 och kennysgelato S1 |
| observera:39–49 | Hårt klipp vid histogramavstånd >0,45, minst åtta rutor mellan klipp; förminskning 135×240, HSV-histogram 32×32 | Nej |
| observera:85–100 | Tre nyckelrutor vid ingest, annars bara mitt; början/slut ligger två rutor från gränsen. MoGe upplösningsnivå 3, fp32, SegFormer argmax/nearest | Nivåer och exakta urval nej; rapportens tre rutor gäller GPU-vägen |
| observera:16–18,97–104 | MoGe ViT-S, SegFormer B2; lagring punkter/normaler fp16, etiketter uint8 | CPU-modeller anges i README, inte här med alla numeriska lagringsval |
| modal_obs:13–17,45–49 | MoGe kod/vikter pinnade till SHA; OneFormer och GeoCalib inte revisionspinnade; GeoCalib pinhole | Modeller och pinhole ja, revisionsförhållandet nej; det är inte ett klippberoende |
| modal_obs:72–103 | MoGe nivå 9/fp16; OneFormer tröskel 0,5, masköverlapp 0,8; halvupplösning/nearest; djup fp16, normaler gånger 127 till int8, okänd etikett 255 | Halvupplösning nämns; trösklar/nivå/kvantisering nej |
| modal_obs:118–120 | Alltid tre nyckelrutor, två rutor in från början/slut, samt heltalsmitt | Tre nyckelrutor ja indirekt; två rutor från gräns nej |
| modal_obs:23–36,126 | CUDA 12.4.1, Python 3.11, torch 2.5.1, torchvision 0.20.1, transformers 4.46.3, numpy<2.3, HF≥0.25; GPU-reservlista; 900 s timeout, 60 s scaledown, max sex containrar | Reservlistan ja; övrigt nej. Infrastrukturkonfiguration, inga antaganden om rummet. Inget kördes här |
| lokalitet:27,84,809,864 | CPU-pixelsteg 3; millimeterrundning av leder; mått avrundas till 2–4 decimaler, diagnostiska grader till 0,1° | Nej för precisionerna; generisk kvantisering, inga uppmätta fysiska storheter |

Nollor, ettor, koordinatindex, COCO-ledindex, id-sentineler, percentilskalans 100, byteskift och flyttals-epsilon är inte ytterligare fysiska antaganden. De finns ändå i råinventeringen så att urvalet ovan går att kontrollera. T.ex. `1e-6`/`1e-8` skyddar normaliseringar, `1e9` används även för saknat 2D-fel och färgerna är visningsval.
