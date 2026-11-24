"""Write a clean UTF-8 progress log from durable evidence. No inference."""
from pathlib import Path
import json,datetime
B=Path(__file__).resolve().parent
budget=json.loads((B/'budget.json').read_text(encoding='utf-8'))
lines=['# RUM-LOGG','',f'Uppdaterad {datetime.datetime.now(datetime.timezone.utc).isoformat()}. Alla nya filer ligger i rumsbank. Inga befintliga filer utanför denna mapp ändras. Ingen lokal inferens, Blender eller testsvit. Ingen gated hämtning, ansökan eller klickgodkännande. Villkor för offentlig NVIDIA CUDA-basimage redovisas separat i licenser.json.',
'','## Gjort','',
'- Läste ingest README, kontraktets början, ingest_klipp.py, rum.py, plats.py, kamera_vertikal.py och de tre anvisade Modal-apparna. Inga AGENTS.md hittades på sökvägen.',
'- Inventerade befintliga tagningar och källor. S1/S4 notan saknar accepterad COLMAP. B S5 och Kenny S2 har numeriskt accepterade kameror men avvisad metrisk translation i varld.npz. Biljards gamla accepterade hela bana är cirka 1,60 m.',
'- Sparade primärkällor, licenser, modellkort och SHA under sources/. Licensbeslut i licenser.json. NC-kandidater blockerades före inferens.',
'- Förberedde offentliga vikter med CPU-funktioner på Modal; inga vikter hämtades lokalt.',
'- Körde MapAnything Apache och DA3 BASE + METRIC-LARGE. Initiala åtta fall plus fullrutekontroller notan 383/383 och biljard 369/369. Individuella utfall och eventuella pågående kontroller står nedan.',
'- ViPE CPU-försök 1 misslyckades: No matching distribution found for gtsam-develop==4.3a2.dev202609030306. Försök 2 bytte denna pin i Modal-imagen till tillgänglig 4.3.2.dev202611100512, men länkaren saknade clang++: [Errno 2] No such file or directory: clang++. Försök 3 lade till clang och lyckades. Originalfelen finns i vipe_prepare.log, vipe_prepare_2.log och vipe_prepare_3.log. CPU-försöken använde noll GPU-minuter.',
'- ViPE-konfigurationen använder DROID, GeoCalib, MoGe2 och befintliga personmasker; inte standardkedjans UniDepth/VDA eller MetricTrail. MoGe2-viktens revision är låst i appen. Rättigheter för DROID-checkpointen är ännu inte uttryckligen klarlagda för kommersiell drift.',
'- Mätning: rå kamerasamstämmighet, stativdrift, faktisk tidsbas, kroppens råa synliga ytdjup, manuellt utvalda synliga golvplan, återprojektion av SIFT-matchad statisk bakgrund och åtta-rutors överlägg. Baslinjen läser bara befintlig MoGe-cache. Planorigo normaliseras till första giltiga kameran.',
'- Överläggens lådor är observerade ytfläckar med antagen tunn tjocklek, inte kompletta möbler. Ingen skymning: en linje ovanpå personen bevisar inte fel djupordning. Ett gemensamt koordinatsystem bevisar inte ett gemensamt rum. En enda golvruta kan inte verifiera tidsstabilitet.',
'- Alla mätningar är referensjämförelser: kroppsmodell, normala dörr-/bordhöjder och tidigare rumsestimat är inget oberoende inmätt facit. Absolut skalfel är därför null, separat från procentuell kroppsdjupskillnad.',
'','## GPU-anrop och budget','']
for e in budget['events']:
    lines.append(f'- {e["utc"]}: {e["candidate"]}, reserverat {e["reserved_seconds"]} s, debiterad övre gräns {e["charged_upper_bound_seconds"]:.1f} s, success={e["success"]}, fall={e["shots"]}.')
    lines.append(f'  Exakt kommando: `scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py {e["candidate"]} evaluate --shots {",".join(e["shots"])}`.')
lines+=['',f'Aktiv reservation: {budget["active_reservation"] or "ingen"}. Övre gräns {budget["charged_upper_bound_seconds"]/60:.2f}/75 min. Mätt GPU-funktionstid {budget["measured_gpu_function_seconds"]/60:.2f} min. En GPU-funktion åt gången; reservera alltid före start och nollställ aldrig budgeten.',
'','## Sparade fall','']
for candidate in ['baseline','mapanything','da3','vipe']:
    d=B/'ut'/candidate
    for p in sorted(d.glob('*/timing.json')) if d.exists() else []:
        info=json.loads(p.read_text(encoding='utf-8'));lines.append(f'- {candidate}/{p.parent.name}: {info.get("status","ran")}, {info.get("frames")} rutor. Mätfil={str((p.parent/"metrics.json").exists())}.')
lines+=['','## Nästa vid återupptagning','',
'1. Läs budget.json och sista relevanta *_evaluate.log / *_fullrate.log. Om en reservation är aktiv, kontrollera det gamla Modal-anropet och avräkna det innan ny GPU-start. Starta inga parallella GPU-anrop.',
'2. Slutför ViPE:s sekventiella fall och pool_visible-kontrollen om de saknas och budgeten räcker. Ett slutligt misslyckande skall stå med exakt fel, inte som ett nollmått. Ingen kandidat får överstiga 1 200 GPU-sekunder före första riktiga lyckade fall.',
'3. Kör evaluate.py för de färdiga kandidaterna, öppna samtliga nya overlay*.jpg med bildverktyget, uppdatera overlay_review.json. Kör size_checks.py, report.py och resume_log.py. README/resultat skall vara självbärande och skilja verifierat från antaget.',
'4. Leverera högst 45 rader med licenser, tabell, visuell granskning, rekommendation, skalstrategi och exakt budgetintervall.',
'','## Kommandon (projektrot)','',
'```powershell',"$env:PYTHONIOENCODING='utf-8'","$env:OPENBLAS_NUM_THREADS='1'","$env:OMP_NUM_THREADS='1'",
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/research.py',
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/prepare_inputs.py',
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/prepare_extra.py',
'scen/.venv/Scripts/python.exe -B -u scen/3d/rumsbank/run_bank.py vipe prepare',
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/baseline.py',
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py baseline',
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py mapanything',
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py da3',
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/evaluate.py vipe',
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/size_checks.py',
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/report.py',
'scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/resume_log.py','```']
result=json.loads((B/'resultat.json').read_text(encoding='utf-8')) if (B/'resultat.json').exists() else {}
if result.get('status')=='completed' and not budget['active_reservation']:
    marker=lines.index('## Nästa vid återupptagning');end=lines.index('## Kommandon (projektrot)')
    lines[marker:end]=['## Slutfört','',
      'Inga återstående GPU-körningar. Tre konfigurationer kördes; den officiella ViPE-djupfusionen och övriga NC/gated-kandidater blockerades före hämtning. 38 mätrader, 41 visuellt öppnade strips, 4 144 råa NPZ-filer. qa.json visar inga artefaktavvikelser.',
      'MapAnything förbättras kraftigt när även fades tas bort (pool_core, source 40–350), men fokal och djupskala är fortfarande motstridiga. ViPE-kameran är bäst på biljard, men fallerar i B S5. Rekommendation: behåll COLMAP + MoGe med osäkerhet och hårda mätspärrar; ändra inte kroppens cam_t för att nå golvet.',
      'README.md, resultat.json, licenser.json och PLATS-INMATNING.md är slutleveransen. Inga produktionsfiler har ändrats. Vid nytt försök: behåll budget och gamla resultat, använd nytt fallnamn och gör ny visuell granskning; återanvänd inte granskningsgodkännande för ändrade bildhashar.','']
(B/'RUM-LOGG.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('RUM-LOGG.md updated')
