# GEM-X – arbetslogg

## 2026-11-10 – start

Ägarens beslut: endast GEM-X utvärderas. Steg 2 får börja först när steg 1
kör och inte är tydligt sämre än slutsekvensen. Ingen lokal inferens.
Budget: 90 GPU-minuter totalt, högst 30 för att få första körningen att fungera.
Tidigare fast-vith-reservation är inte en körning (events tom, debiterat 0).
Inga GEM-X-GPU-anrop har ännu gjorts. Inga befintliga filer har ändrats.

Läst: ingest/README.md, kontrakt/README.md, modal_sam3db.py, manifest,
budget, evaluate.py och sparade GEM-X-installations-/inferenskällor.
Primärkällorna GitHub NVlabs/GEM-X och HF nvidia/GEM-X öppnade igen.
motion-video saknar boxes-argument och följer bara huvudpersonen. Plan:
använd samma upstream-funktion med en avgränsad adapter för detect_track
som levererar varje befintligt personspår, och spara adapterns proveniens.
Kameraintrinsik hämtas från manifestet, antagen i befintlig kedja.
Ingen handmodell eller gated tillgång hämtas/accepteras.

Nästa: lås kodrevision, CPU-bygg och CPU-hämtning till Modal-volym,
sedan ett sekventiellt GPU-anrop med hård startbudget.

Kommandon körs från projektroten med:
`$env:PYTHONIOENCODING='utf-8'; scen/.venv/Scripts/python.exe ...`

## Genomfört 2026-11-10

Löpande loggtillägg via PowerShells stdin tappade svenska tecken. Texten har
rättats till UTF-8 här. Den fullständiga föregående loggtexten ligger kvar i
GEMX-LOGG-fore_utf8.md, inklusive kommandon och mellanlägen.

Låsta revisioner, verifierade med GitHub/HF API:
- GEM-X: 4aef1452e5df171deff4f293c08e643eb450981e.
- GEM-vikter: b111f2dcf3ebcf57965fd53499cb645dfa5ba25c.
- SOMA v0.3.3: d281db2d01553f7230c56e764cec00fe27ef23f7.
- Båda kroppstillgångarnas API svarade gated=false. Inga tokenvärden skrevs ut.

Nytt: ingest/modal_gemx.py; separat Modal-volym gemx-body-v033.
Bild: Debian/Python 3.12, torch 2.10.0+cu128, GEM [video], py-soma-x 0.3.3,
transformers 5.3.0, onnxruntime 1.31.1. Bildbyggets fyra steg tog 165,49 s.
Första CPU-starten hade ett eget paketeringsfel: parents[3] finns inte när
Modal lägger modulen direkt i /root. Rättat före GPU. Den gamla CPU-appen
ap-ABP9kOzIlYPK51JaQAP55J stoppades; inga containrar körde då.
Andra CPU-appen ap-JhgyfCpoRnvzaqGtoxuXsC hämtade och verifierade alla elva
GEM/SOMA-filer samt YOLOX ONNX. Hämtning/importkontroll 131,21 s, anropets
väggtid 138,50 s. Inga handvikter eller nya gategodkännanden.

Exakta huvudkommandon, från projektroten:

```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe -B scen/3d/kroppsbank/gemx_sources.py
scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode prepare *> scen/3d/kroppsbank/gemx_prepare.log
scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode prepare *> scen/3d/kroppsbank/gemx_prepare2.log
scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode evaluate *> scen/3d/kroppsbank/gemx_evaluate.log
scen/.venv/Scripts/python.exe -B scen/3d/kroppsbank/evaluate_gemx.py
scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode audit *> scen/3d/kroppsbank/gemx_audit.log
scen/.venv/Scripts/python.exe -B scen/3d/kroppsbank/report_gemx.py
```

Lokala mätkörningar finns i gemx_metrics*.log. De använder bara sparade
NumPy-arrayer och OpenCV, ingen modell. evaluate.py är orörd; den nya
evaluate_gemx.py återanvänder dess geometri- och maskmått.

## GPU-resultat och budget

GPU-app ap-CA51Gax0c1pSZ1BhOJs18A är avslutad.
Run-id: 20261110T154539Z. En enda L40S-funktion, alla tagningar och personer
sekventiellt. Reservation före start 1800 s, hård funktionsgräns 1650 s,
scaledown 2 s. Ingen Blender-process startades.

294 observerade personrutor, 324 predikterade (inklusive 30 utfyllda före
S4/person 4). Inferens 45,166 s = 0,154 s per observerad personruta.
Hela GPU-funktionen 206,339 s = 0,702 s per observerad personruta, inklusive
båda varianters FK/mesh, filer och packning. Kallstart till första status
41,484 s, inklusive kö/start/import. VRAM vid 1 Hz max 6570 MiB;
PyTorch max 3737261568 byte allokerat, 6287261696 reserverat.

Budgeten avräknad: 333,875 s = 5,565 av 90 GPU-minuter. Det är anropets
väggtid + 15 s avslutsmarginal. GPU-funktionens klocka visar 3,439 minuter;
exakt fakturerad/allokerad tid är inte hämtad från Modal. Inga reservationer
kvar. Ingen lokal inferens. Startbudgeten 30 minuter hölls.

## Granskning och beslut

Samtliga åtta GEM-remsor har öppnats med view_image och granskats: fyra
tagningar gånger rå/kontakt-IK, åtta källrutor per remsa. Även de fyra
slutsekvensremsorna har granskats. Rå och modellens egen kontakt/IK har
separata nativa .pt, 77 leder i kamera och värld, intrinsics, kontaktlogits
och kameramesh i ut/gemx/<tagning>/<pid>.

Steg 1 kör, men kvalitetsvillkoret för steg 2 bedöms inte vara uppfyllt.
Råvara S5 försämras mot slutsekvensen i silhuett-IoU (0,595/0,634),
kamerarumsdarr (5,646/1,121) och rotrelativt darr (0,832/0,630).
Notan S4/person 4 har darr 3,625/0,194. Samtidigt förbättras notans
silhuetter, och modellens IK ger fotglidning 0,043/0,087 cm/ruta
vänster/höger i GEM:s värld, mot gamla 0,104/0,109 på samma antagna
SAM-referenskontakter. Alla vinster och försämringar finns i README.md.
Detta är en bedömning av provet, ingen ny ägartröskel.

Ingen --kropp gemx-växel, produktionsrigg, retarget, platsjustering/rest,
vakt-ablation eller helfilmsombyggnad har gjorts. Ingen gammal
efterbehandling ändrad. Kompilator, kvalitet, props/ankare och forvarld är
inte GEM-verifierade. Ingest-README och kontraktets kommandolista är orörda,
eftersom steg 2 inte utfördes. MHR-identitetsbackend är ingen bevisad
posekonvertering; konverteringsfel saknas. Ingen ny film har granskats.

## Licenskontroll

CPU-appen ap-ygi9OTQrpEcEpqeTWLm9BM är avslutad. ONNX-arkivet saknar
LICENSE/NOTICE. Detektorns separata vikt-/datavillkor är inte verifierade.
GEM:s HF LICENSE säger Apache 2.0, medan modellkortet anger NVIDIA-avtalet
för vikterna; motsägelsen är dokumenterad. SOMA v0.3.3 är Apache 2.0.
GEM har filspecifika undantag enligt ATTRIBUTIONS.md.

Inga handvikter eller gategodkännanden. Ägaren behöver själv granska
EgoHand-v1:s OpenMDW 1.1 och eventuell HF-gate vid handaktivering.
Sparad API-metadata gated=false avviker från uppgiften om gate; faktisk
checkpointåtkomst är inte testad. Se ut/gemx/asset_audit.json och README.md.

## Slutkontroller och återupptagning

SOMA77-ordningen verifierad exakt mot upstream SOMA77_JOINT_NAMES.
Ledpar är anatomiska jämförelser, ingen konvertering. Dold led-jitter och
spann finns i gemx_matningar.json. S4/person 4 har inga dolda rutor enligt
den äldre benflaggan; separata benmått för alla 55 spårrutor finns också.
Fotmått använder samma synliga SAM-referensintervall och redovisar separat
varje metods egen masktäckning. Kontaktintervallen är antagna, inte facit.

Slutkontroll: 648 kamerameshfiler, tio person/variant-arrayer med ändliga
(N,77,3)-leder, rätt intrinsics och observationsantal, åtta 2304×512-remsor
och 20 måttrader. Se gemx_verifiering.json. Syntax kontrollerad; fyra billiga
gränsfall för GPU-budgeten verifierade utan GPU-anrop.
Budgetskyddet begränsar avbrutna omförsök till återstående starttid; efter
första lyckade körningen gäller återstående totalbudget.

Leverans: README.md, gemx_matningar.json, gemx_verifiering.json, rådata och
remsor i ut/gemx. Fore_gemx innehåller originalbudgeten och första versioner
av egna filer som senare ändrades, med samma projektrelativa sökväg.

Inga automatiska nästa steg kvar. Vid fortsättning: läs kvalitetsbeslutet.
Starta inte en ny GPU enbart för att detta är en ny session. GEM-data får
inte användas som färdiga MHR-planer eller platskoordinater utan verifierad
riggväg och platsjustering.


## Uppföljning 2026-11-10 – omprövning

Ägaren begär rättvis rå/rå- och lika-filterjämförelse. Tidigare stopp omprövas; steg 2 startas inte. Källkoden har 30 Hz-normalisering, explicit static-kamera och avsedda incam-parametrar. CPU-inspektionen hämtar sparade villkor utan inferens. Alla nya filer ligger inom kroppsbank samt modal_gemx.py.

GPU-start 20261110T160530Z, app ap-t74oRKXZ6GrqmuRebSKFlp. Stock CLI på fyra klipp med ärvd/default K, adapter+static på notan, hela notan stock med background/static. Sekventiellt; reservation 1500 s; högst 1500 s extra totalt. Servern sparar varje person före nästa. Stora arkiv överförs långsamt; GPU-funktionen och överföringen har därför olika tidslinjer.

### Billiga kontroller och första resultat

CPU-inspektion från Modal klar. Utan inferens exporterades villkor, modellens egna 2D-observationer och kameradiagnostik. Alla fyra källklipp är 30 fps, 576×1024; normaliserade rutor är exakt 73, 85, 46, 35 och tidssteg 1/30 s. Inget tappat ruta-/storlekssteg i dessa prov. S4/person 4 mäts endast där originalspåret finns (55 rutor), inte på de 30 utfyllda rutorna före spåret.

Tidslinjen matchad med tre avkodade bildpar per tagning: S1=original 0–72, S4=171–255. Se ut/jamforelse/timeline.json. Upstream har max_len=120 och uppmärksamhetsmask för längre sekvenser, inte tyst klippning till 120; källan sparad som kallor/gemx_followup_gem_motion_network_r3_matched.py.

Darret är starkt rot-/djupdominerat. Ursprunglig GEM S4/person 4: djup 3,469, rotrelativt 0,288, egen värld 0,320 cm/ruta². Upstream MotionPipeline bygger incam från pred_cam och bbox/K, medan världens rot integreras från predikterad hastighet. Vår mätning använder avsedda incam-parametrar med translation applicerad en gång av SOMA; ingen egen värld-till-kamera-rekomposition.

Första stock-provet S1: Jkamera 0,722 mot adapter 1,432; Jbild 3,596 mot 5,993. Adaptern påverkar resultatet. Static- och intrinsicsproven är separata för att inte blanda orsakerna.

Lika filter körs lokalt på sparad geometri: EN symmetrisk Gausskärna, sigma 0/0,5/1/2/3 rutor, truncate=3, reflekterade ändar, separat rot och rotrelativa led-/meshpositioner med samma kärna. Detta är ett geometriskt ablationsfilter, inte en kvaternions-/riggimplementation. Benlängdsändring mäts. Inga modeller körs lokalt. Samma observerade rutor, maskreferenser och synliga 2D-punktpar används. Övriga personers maskundantag fixeras till rå SAM för alla metoder.

S1 SAM sigma=1: J 0,187 och IoU 0,621; sparad slutsekvens J 0,196 och IoU 0,399. Rotablation: slutpose + rå SAM-rot ger IoU 0,649, medan rå pose + slutrot ger 0,376. Det lokaliserar ett stort bildpassningsfel till rotbanan i den sparade kedjan. Slutsekvensens aktuella npz-poser matchar de tidigare sparade kameraledernas alla koordinater exakt (maxfel 0 cm på alla fem spår).

Nya verktyg: followup_gemx.py och ut/jamforelse/*.json. Modal-lägen inspect och slim gör endast CPU-läsning/serialisering. Första slim-anropet hade ett lokalt dispatchfel, rättat utan GPU-anrop. Ett första loggtillägg via PowerShell-stdin tappade å/ä/ö och rättades här med apply_patch; tidigare loggtext är bevarad.



## Övertagande 2026-11-10 17:22 (Claude, efter att Codex dog på kvot 17:21)

Läge vid övertagandet: de lokala drivprocesserna var döda. GPU-appen ap-t74oRKXZ6GrqmuRebSKFlp fick avbrottssignal 17:22:47 när den just började `notan-whole__stock_background`; den hade inga containrar kvar. CPU-appen ap-nccC166eNm8nOsdlSBECve (projektion) hade ingen mottagare kvar. Båda stoppades med `python -m modal app stop -y <id>` (17:23:36 och 17:23:40).

GPU-avräkning: reservationen 1500 s ersattes av 1107 s (app-start 17:05:24 till stopp 17:23:36 plus 15 s, konservativt). Totalt GEM-X hittills: 1440,9 s = 24,0 min av 90.

Klart av körningen (alla lokalt i ut/gemx_followup/, med nät per ruta): stock CLI med ärvd och default K på S1, S4, S5, S9; adapter+static på S1 och S4. Saknas: hela notan (background och static).

Nytt verktyg: `followup2_gemx.py` (lägen configs, curves, videos). Läser bara sparad geometri. Kör från projektroten:
`$env:PYTHONIOENCODING='utf-8'; scen/.venv/Scripts/python.exe scen/3d/kroppsbank/followup2_gemx.py configs|curves|videos`
Resultat: ut/jamforelse/configurations.json, best.json, curves.json, *_sida-vid-sida.mp4, rutor/<tagning>/f*.png.

Fynd 17:25–17:40 (mätt):
- personer.json-rutornas centrumdarr: S1 6,2, S4/1 0,18, S5 11,5, S9 16,4 px/ruta². Stock-spårarens rutor: S1 2,8, S9 1,8 px. Adaptern för vidare brusiga rutor till GEM-X.
- Stock (ärvd K) mot adapter, kameradarr: S1 0,722 mot 1,432; S4/1 0,166 mot 0,585; S5 4,91 (default K 2,97) mot 5,69; S9 0,891 mot 1,423. Silhuett-IoU nästan oförändrad.
- Static-kameraläge med adaptern är sämre än background: S1 1,769 mot 1,432; S4/1 0,681 mot 0,585.
- Slutkedjans bildfel i S1 och S4/1 är exakt golvsteget: rotförskjutningen slutkedja minus rå SAM = (golv_skala - 1) · cam_t, restfel 0,00 cm. golv_skala 0,849 (S1), 1,105 (S4/1). Steget skalar bara cam_t, inte kroppen, så kroppen flyttas i bild.

Nästa: ett sista GPU-anrop (högst 600 s, endast hela notan, stock, background) för att besvara frågan om klippta tagningar. Kommando:
`$env:PYTHONIOENCODING='utf-8'; scen/.venv/Scripts/python.exe -m modal run scen/3d/ingest/modal_gemx.py --mode whole`
Reservationen skrivs i budget.json av skriptet före start. Dör klienten: stoppa appen och avräkna från app-start till stopp + 15 s.

## Uppföljning: GPU-start 20261110T163255Z
Stock CLI på fyra klipp med ärvd/default K, adapter+static på notan, hela notan stock med background/static. Sekventiellt; reservation 600.0 s; högst 1500 s extra totalt.

GPU-anrop avslutat: 5.828 min konservativt; error. Se ut/gemx_followup/run_20261110T163255Z.json.

Rättelse till raden ovan: anropet 20261110T163255Z körde endast `notan-whole__stock_background` (läge `--mode whole`, tak 600 s), inte static. Stock-CLI stoppade i kamerarotationen: "Background camera tracking was unavailable for more than one second" (källfilen har klippbyten). Ingen ny körning gjordes efter det. Frågan om oklippt sammanhang är obesvarad. Debiterat 349,7 s. GEM-X totalt: 1790,5 s = 29,8 min av 90.

## Klart 17:45 (Claude)

- configs: ut/jamforelse/configurations.json och best.json (regel: högst IoU bland konfigurationer med darr ≤ 1,25 × lägsta).
- curves: ut/jamforelse/curves.json (SAM, slutkedja, bästa GEM-X; sigma 0/0,5/1/2/3).
- slutsekvens_utan_golv.json: slutkedjan med golv- och kontaktförskjutningen borttagen. S1 IoU 0,650, kp 11,1, darr 0,203 (mot 0,399, 198, 0,196). Bildfelet sitter i golv/kontakt, inte i sekvens_stabil.
- videos: ut/jamforelse/{notan-S1,notan-S4,ravara-S5}_sida-vid-sida.mp4 (H.264, 30 fps), stillbilder i rutor/.
- Dom (bedömd från mätningarna): behåll SAM. Rätta steg_golv och kontaktens synliga förskjutning. GEM-X ska inte bli kroppssteg. Se README.md, översta avsnittet.

Nästa (inte startat): rättelsen av golvsteget i ingest. Det kräver ägarens ja, och ingest/ ägs av en annan agent.
