# RUM-LOGG

Uppdaterad 2026-11-10T17:35:33.076047+00:00. Alla nya filer ligger i rumsbank. Inga befintliga filer utanför denna mapp ändras. Ingen lokal inferens, Blender eller testsvit. Ingen gated hämtning, ansökan eller klickgodkännande. Villkor för offentlig NVIDIA CUDA-basimage redovisas separat i licenser.json.

## Gjort

- Läste ingest README, kontraktets början, ingest_klipp.py, rum.py, plats.py, kamera_vertikal.py och de tre anvisade Modal-apparna. Inga AGENTS.md hittades på sökvägen.
- Inventerade befintliga tagningar och källor. S1/S4 notan saknar accepterad COLMAP. B S5 och Kenny S2 har numeriskt accepterade kameror men avvisad metrisk translation i varld.npz. Biljards gamla accepterade hela bana är cirka 1,60 m.
- Sparade primärkällor, licenser, modellkort och SHA under sources/. Licensbeslut i licenser.json. NC-kandidater blockerades före inferens.
- Förberedde offentliga vikter med CPU-funktioner på Modal; inga vikter hämtades lokalt.
- Körde MapAnything Apache och DA3 BASE + METRIC-LARGE. Initiala åtta fall plus fullrutekontroller notan 383/383 och biljard 369/369. Individuella utfall och eventuella pågående kontroller står nedan.
- ViPE CPU-försök 1 misslyckades: No matching distribution found for gtsam-develop==4.3a2.dev202609030306. Försök 2 bytte denna pin i Modal-imagen till tillgänglig 4.3.2.dev202611100512, men länkaren saknade clang++: [Errno 2] No such file or directory: clang++. Försök 3 lade till clang och lyckades. Originalfelen finns i vipe_prepare.log, vipe_prepare_2.log och vipe_prepare_3.log. CPU-försöken använde noll GPU-minuter.
- ViPE-konfigurationen använder DROID, GeoCalib, MoGe2 och befintliga personmasker; inte standardkedjans UniDepth/VDA eller MetricTrail. MoGe2-viktens revision är låst i appen. Rättigheter för DROID-checkpointen är ännu inte uttryckligen klarlagda för kommersiell drift.
- Mätning: rå kamerasamstämmighet, stativdrift, faktisk tidsbas, kroppens råa synliga ytdjup, manuellt utvalda synliga golvplan, återprojektion av SIFT-matchad statisk bakgrund och åtta-rutors överlägg. Baslinjen läser bara befintlig MoGe-cache. Planorigo normaliseras till första giltiga kameran.
- Överläggens lådor är observerade ytfläckar med antagen tunn tjocklek, inte kompletta möbler. Ingen skymning: en linje ovanpå personen bevisar inte fel djupordning. Ett gemensamt koordinatsystem bevisar inte ett gemensamt rum. En enda golvruta kan inte verifiera tidsstabilitet.
- Alla mätningar är referensjämförelser: kroppsmodell, normala dörr-/bordhöjder och tidigare rumsestimat är inget oberoende inmätt facit. Absolut skalfel är därför null, separat från procentuell kroppsdjupskillnad.

## GPU-anrop och budget

- 2026-11-10T16:35:26.112708+00:00: mapanything, reserverat 900 s, debiterad övre gräns 309.9 s, success=True, fall=['notan_S1', 'notan_S4', 'b_S5', 'b_closeup', 'pool', 'kenny_S2', 'notan_uncut', 'notan_joint_S1_S4'].
  Exakt kommando: `scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py mapanything evaluate --shots notan_S1,notan_S4,b_S5,b_closeup,pool,kenny_S2,notan_uncut,notan_joint_S1_S4`.
- 2026-11-10T16:39:57.457965+00:00: da3, reserverat 900 s, debiterad övre gräns 223.0 s, success=True, fall=['notan_S1', 'notan_S4', 'b_S5', 'b_closeup', 'pool', 'kenny_S2', 'notan_uncut', 'notan_joint_S1_S4'].
  Exakt kommando: `scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py da3 evaluate --shots notan_S1,notan_S4,b_S5,b_closeup,pool,kenny_S2,notan_uncut,notan_joint_S1_S4`.
- 2026-11-10T16:49:09.852924+00:00: mapanything, reserverat 900 s, debiterad övre gräns 324.2 s, success=True, fall=['notan_fullrate', 'pool_fullrate'].
  Exakt kommando: `scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py mapanything evaluate --shots notan_fullrate,pool_fullrate`.
- 2026-11-10T16:53:59.386085+00:00: da3, reserverat 900 s, debiterad övre gräns 579.1 s, success=True, fall=['notan_fullrate', 'pool_fullrate'].
  Exakt kommando: `scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py da3 evaluate --shots notan_fullrate,pool_fullrate`.
- 2026-11-10T17:05:11.903553+00:00: vipe, reserverat 900 s, debiterad övre gräns 240.4 s, success=True, fall=['notan_S1', 'notan_S4', 'b_S5', 'b_closeup', 'pool', 'kenny_S2', 'notan_uncut', 'notan_joint_S1_S4'].
  Exakt kommando: `scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py vipe evaluate --shots notan_S1,notan_S4,b_S5,b_closeup,pool,kenny_S2,notan_uncut,notan_joint_S1_S4`.
- 2026-11-10T17:08:38.856523+00:00: mapanything, reserverat 900 s, debiterad övre gräns 223.7 s, success=True, fall=['pool_visible'].
  Exakt kommando: `scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py mapanything evaluate --shots pool_visible`.
- 2026-11-10T17:12:08.222417+00:00: vipe, reserverat 900 s, debiterad övre gräns 331.6 s, success=True, fall=['notan_fullrate', 'pool_fullrate'].
  Exakt kommando: `scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py vipe evaluate --shots notan_fullrate,pool_fullrate`.
- 2026-11-10T17:17:11.592767+00:00: mapanything, reserverat 900 s, debiterad övre gräns 237.0 s, success=True, fall=['pool_core'].
  Exakt kommando: `scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py mapanything evaluate --shots pool_core`.

Aktiv reservation: ingen. Övre gräns 41.15/75 min. Mätt GPU-funktionstid 14.48 min. En GPU-funktion åt gången; reservera alltid före start och nollställ aldrig budgeten.

## Sparade fall

- baseline/b_closeup: ran, 8 rutor. Mätfil=True.
- baseline/b_S5: ran, 8 rutor. Mätfil=True.
- baseline/kenny_S2: ran, 8 rutor. Mätfil=True.
- baseline/notan_S1: ran, 8 rutor. Mätfil=True.
- baseline/notan_S4: ran, 8 rutor. Mätfil=True.
- baseline/pool: ran, 8 rutor. Mätfil=True.
- mapanything/b_closeup: ran, 35 rutor. Mätfil=True.
- mapanything/b_S5: ran, 46 rutor. Mätfil=True.
- mapanything/kenny_S2: ran, 96 rutor. Mätfil=True.
- mapanything/notan_fullrate: ran, 383 rutor. Mätfil=True.
- mapanything/notan_joint_S1_S4: ran, 16 rutor. Mätfil=True.
- mapanything/notan_S1: ran, 73 rutor. Mätfil=True.
- mapanything/notan_S4: ran, 85 rutor. Mätfil=True.
- mapanything/notan_uncut: ran, 46 rutor. Mätfil=True.
- mapanything/pool: ran, 80 rutor. Mätfil=True.
- mapanything/pool_core: ran, 311 rutor. Mätfil=True.
- mapanything/pool_fullrate: ran, 369 rutor. Mätfil=True.
- mapanything/pool_visible: ran, 363 rutor. Mätfil=True.
- da3/b_closeup: ran, 26 rutor. Mätfil=True.
- da3/b_S5: ran, 28 rutor. Mätfil=True.
- da3/kenny_S2: ran, 28 rutor. Mätfil=True.
- da3/notan_fullrate: ran, 383 rutor. Mätfil=True.
- da3/notan_joint_S1_S4: ran, 16 rutor. Mätfil=True.
- da3/notan_S1: ran, 28 rutor. Mätfil=True.
- da3/notan_S4: ran, 30 rutor. Mätfil=True.
- da3/notan_uncut: ran, 28 rutor. Mätfil=True.
- da3/pool: ran, 28 rutor. Mätfil=True.
- da3/pool_fullrate: ran, 369 rutor. Mätfil=True.
- vipe/b_closeup: ran, 35 rutor. Mätfil=True.
- vipe/b_S5: ran, 46 rutor. Mätfil=True.
- vipe/kenny_S2: ran, 96 rutor. Mätfil=True.
- vipe/notan_fullrate: ran, 383 rutor. Mätfil=True.
- vipe/notan_joint_S1_S4: ran, 16 rutor. Mätfil=True.
- vipe/notan_S1: ran, 73 rutor. Mätfil=True.
- vipe/notan_S4: ran, 85 rutor. Mätfil=True.
- vipe/notan_uncut: ran, 46 rutor. Mätfil=True.
- vipe/pool: ran, 80 rutor. Mätfil=True.
- vipe/pool_fullrate: ran, 369 rutor. Mätfil=True.

## Slutfört

Inga återstående GPU-körningar. Tre konfigurationer kördes; den officiella ViPE-djupfusionen och övriga NC/gated-kandidater blockerades före hämtning. 38 mätrader, 41 visuellt öppnade strips, 4 144 råa NPZ-filer. qa.json visar inga artefaktavvikelser.
MapAnything förbättras kraftigt när även fades tas bort (pool_core, source 40–350), men fokal och djupskala är fortfarande motstridiga. ViPE-kameran är bäst på biljard, men fallerar i B S5. Rekommendation: behåll COLMAP + MoGe med osäkerhet och hårda mätspärrar; ändra inte kroppens cam_t för att nå golvet.
README.md, resultat.json, licenser.json och PLATS-INMATNING.md är slutleveransen. Inga produktionsfiler har ändrats. Vid nytt försök: behåll budget och gamla resultat, använd nytt fallnamn och gör ny visuell granskning; återanvänd inte granskningsgodkännande för ändrade bildhashar.

## Kommandon (projektrot)

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/research.py
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/prepare_inputs.py
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/prepare_extra.py
scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py vipe prepare
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/baseline.py
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py baseline
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py mapanything
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py da3
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py vipe
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/size_checks.py
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/report.py
scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/resume_log.py
```
