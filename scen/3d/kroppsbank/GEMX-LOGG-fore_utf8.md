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
använd samma upstream-funktion med en avgränsad adapter för det_track
som levererar varje befintligt personspår, och spara adapterns proveniens.
Kameraintrinsik hämtas från manifestet, antagen i befintlig kedja.
Ingen handmodell eller gated tillgång hämtas/accepteras.

Nästa: lås kodrevision, CPU-bygg och CPU-hämtning till Modal-volym,
sedan ett sekventiellt GPU-anrop med hård startbudget.

Kommandon körs från projektroten med:
`$env:PYTHONIOENCODING='utf-8'; scen/.venv/Scripts/python.exe ...`

## L?sta revisioner och p?g?ende CPU-bygge

GEM-X: 4aef1452e5df171deff4f293c08e643eb450981e.
GEM-vikter: b111f2dcf3ebcf57965fd53499cb645dfa5ba25c.
SOMA v0.3.3: d281db2d01553f7230c56e764cec00fe27ef23f7.
HF API bekr?ftade gated=false f?r b?da. Underlag: kallor/gemx_verified.json.
Nytt: ingest/modal_gemx.py; separat Modal-volym gemx-body-v033.
Bild: Debian/Python 3.12, torch 2.10.0 cu128, GEM [video], py-soma-x 0.3.3.
GPU planerad L40S 48 GB, max_containers=1, timeout 1650 s, scaledown 2 s.
Alla tagningar/personer sekventiellt i ett generatoranrop; r?resultat
sparas till volym f?re IK. Inga handvikter. Sparar r?/IK .pt, kamera/v?rldsleder,
kameran, intrinsics, kontaktlogits och kameramesh f?r maskj?mf?relse.

Exakta kommandon:
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe -B scen/3d/kroppsbank/gemx_sources.py
scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode prepare *> scen/3d/kroppsbank/gemx_prepare.log
```
P?g?r: CPU-bildbygget. Ingen GPU reserverad/k?rd ?nnu.
N?sta efter lyckad CPU-preflight: samma modal-kommando med --mode evaluate,
logg till gemx_evaluate.log. Om k?rningen misslyckas: stoppa och rapportera;
starta inte steg 2. Vid avbrott: l?s budgetreservation och Modal-app innan ny GPU.

CPU-bygget klart. F?rsta CPU-starten hittade ett eget paketeringsfel:
Modal placerar modulfilen direkt i /root, s? parents[3] fanns inte.
R?ttat till lokal/remote-?tskillnad. Ingen GPU anv?ndes. Gamla CPU-appen
ap-ABP9kOzIlYPK51JaQAP55J stoppad med --yes (inga containrar k?rde).
CPU-h?mtning p?g?r nu i ap-JhgyfCpoRnvzaqGtoxuXsC, logg gemx_prepare2.log.
Kommando: python -B -m modal run scen/3d/ingest/modal_gemx.py --mode prepare.
Nytt evaluate_gemx.py anv?nder evaluate.py:s rasterisering/maskm?tt, inga modeller.
SOMA USD har 110 riggleder inkl virtuell Root och 32 procedurvridben;
77 offentliga leder ?terst?r. Ledpar ?r anatomisk j?mf?relse, inte konvertering.
F?rsta backup av ?ndrad modal_gemx.py ligger i fore_gemx med samma relativa s?kv?g.

CPU-preflight lyckad: torch 2.10.0+cu128, GEM 0.1.0, py-soma-x 0.3.3,
transformers 5.3.0, onnxruntime 1.31.1. CPU-h?mtning 131,21 s;
kallbyggets fyra rapporterade bildsteg totalt 165,49 s. Alla elva
GEM/SOMA-filer samt YOLOX ONNX finns i volymen. Lokal prepare.json sparad.
Startar nu f?rsta GPU-anropet (alla fyra tagningar/personer sekventiellt):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode evaluate *> scen/3d/kroppsbank/gemx_evaluate.log
```
Anropet reserverar 1800 s innan GPU-start. H?rd funktionsgr?ns 1650 s,
stoppar f?re n?sta person om ?ver 1450 s. Reservation kvar vid lokal disconnect.

## Slutl?ge ? steg 1 klart, steg 2 stoppat p? kvalitet

GPU-app: ap-CA51Gax0c1pSZ1BhOJs18A (avslutad).
Run-id: 20261110T154539Z. En enda L40S-funktion, inga parallella GPU-anrop.
294 observerade personrutor, 324 predikterade (inkl 30 utfyllda f?re S4/p4).
Inferens 45,166 s = 0,154 s/observerad personruta.
Hela GPU-funktionen 206,339 s = 0,702 s/observerad personruta, med
b?da varianters FK/mesh, filskrivning och packning. Kallstart 41,484 s.
VRAM nvidia-smi 1 Hz max 6570 MiB; torch allokerat max 3737261568 byte.
Konservativ budget 333,875 s = 5,565 av 90 GPU-minuter, inga reservationer.
Exakt debiterad GPU-allokering ej h?mtad fr?n Modal.

Samtliga ?tta GEM-X-remsor har ?PPNATS OCH GRANSKATS med view_image,
samt slutsekvensens remsor f?r de fyra tagningarna.
R? och modellens egen kontakt/IK har separata nativa .pt, 77 leder i kamera
och v?rld, intrinsics, kontaktlogits och kameramesh i ut/gemx/<tagning>/<pid>.

Kvalitetsbeslut: starta inte steg 2. S5 f?rs?mras mot slutsekvensen i
silhuett-IoU (0,595/0,634), kamerarumsdarr (5,646/1,121) och rotrelativt
darr (0,832/0,630). S4/p4 darr 3,625/0,194. Samtidigt f?rb?ttras
notans silhuetter och modellens IK ger fotglidning 0,043/0,087 cm/ruta
v?nster/h?ger i GEM:s v?rld, mot gamla 0,104/0,109 p? samma antagna
SAM-referenskontakter. Vinster och f?rs?mringar redovisas tillsammans.
Detta ?r en provbed?mning, ingen ?gartr?skel. Inget p?st?ende om en ny film.

Ingen --kropp gemx-v?xel, rigg, retarget, platsjustering/rest, vakt-ablation
eller helfilmsombyggnad har gjorts. Ingen gammal efterbehandling ?ndrad.
Kompilator, kvalitet, props/ankare och forvarld ?r inte GEM-verifierade.
Ingest-README och kontraktets kommandolista ?r or?rda (steg 2 utf?rdes inte).
MHR-identitetsbackend ?r inte en bevisad posekonvertering; konverteringsfel saknas.

M?tningarna k?rdes lokalt p? sparade arrayer med NumPy/OpenCV, ingen modell:
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe -B scen/3d/kroppsbank/evaluate_gemx.py
scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode audit *> scen/3d/kroppsbank/gemx_audit.log
scen/.venv/Scripts/python.exe -B scen/3d/kroppsbank/report_gemx.py
```
CPU-licensaudit avslutad: ap-ygi9OTQrpEcEpqeTWLm9BM.
ONNX-arkivet saknar LICENSE/NOTICE. Vikternas egna detektorvillkor ej
verifierade. HF GEM LICENSE ?r Apache, modellkort anger NVIDIA-avtalet;
mots?gelsen dokumenterad. Inga handvikter/gateaccept gjorda. Sparad
EgoHand-API gated=false avviker fr?n gateuppgiften; ?tkomst inte testad.

SOMA77-ordningen ?r exakt verifierad mot upstream SOMA77_JOINT_NAMES,
inte gissad fr?n ledpositionerna. Dold led-jitter och spann finns; S4/p4
har inga dolda rutor med ?ldre benflaggan, s? separata benm?tt f?r alla
55 sp?rrutor finns i gemx_matningar.json. Fotm?tt anv?nder samma synliga
SAM-referensintervall, samt redovisar varje metods egen maskt?ckning.

Slutkontroll: 648 kamerameshfiler, tio person/variant-arrayer med ?ndliga
(N,77,3)-leder, r?tt intrinsics/observationsantal, ?tta 2304x512-remsor
och 20 m?ttrader. Se gemx_verifiering.json. Syntax kontrollerad; fyra
billiga gr?nsfall f?r GPU-budgeten verifierade utan GPU-anrop.
Budgetskyddet begr?nsar ?ven avbrutna omf?rs?k till ?terst?ende starttid;
efter f?rsta lyckade k?rning g?ller ?terst?ende totalbudget.

Leverans: README.md ?r svensk resultatrapport, gemx_matningar.json r?a
samlade m?tt, GEMX-LOGG.md ?terupptagningslogg. evaluate.py ?r or?rd;
evaluate_gemx.py ?teranv?nder dess m?tt. Fore_gemx inneh?ller original
av budgeten och f?rsta versioner av egna filer som sedan ?ndrades.

Inga automatiska n?sta steg kvar. Vid forts?ttning: l?s kvalitetsbeslutet
och stoppa inte in GEM-data i MHR-planer utan verifierad riggv?g och
platsjustering. Starta ingen ny GPU enbart f?r att detta ?r en ny session.
