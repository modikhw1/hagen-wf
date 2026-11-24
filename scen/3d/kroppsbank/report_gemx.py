"""Write the Swedish, reproducible Stage 1 report from saved measurements."""
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parents[2]
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def num(v,d=3): return 'saknas' if v is None else f'{v:.{d}f}'.replace('.',',')

def main():
    measurements=read(ROOT/'gemx_matningar.json'); rows=measurements['rows']
    manifest=read(ROOT/'manifest.json')['shots']; budget=read(ROOT/'budget.json')
    run=read(next((ROOT/'ut/gemx').glob('run_*.json')))
    people=[p for shot in manifest for p in read(ROOT/'ut/gemx'/shot['id']/'timing.json')['people']]
    tracked=sum(len(read(Path(s['folder'])/'personer.json')[pid]) for s in manifest for pid in s['pids'])
    predicted=sum(p['frames'] for p in people)
    forward=sum(p['forward_s'] for p in people); ik=sum(p['contact_ik_s'] for p in people)
    duration=next(e['gpu_function_s'] for e in run if e['kind']=='done')
    cold=run[0]['cold_call_to_first_event_s']
    labels={'sam-raw':'rå SAM','slutsekvens':'nuvarande slutsekvens','gemx-raw':'GEM-X rå','gemx-contact_ik':'GEM-X + modellens kontakt/IK'}
    text=['# GEM-X: genomfört körprov, inget pipelinebyte', '',
        '2026-11-10. Installationen och Body Motion fungerar på Modal. Alla fyra testtagningar är körda, inklusive båda spårade personerna i notan S4. Inga handvikter har hämtats.', '',
        'Beslut: steg 2 startas inte. I råvara S5 är GEM-X sämre än den sparade slutsekvensen i både oberoende silhuett-IoU (0,595 mot 0,634) och kamerarumsdarr (5,65 mot 1,12 cm/ruta² efter modellens kontakt/IK). Rotrelativt darr är också högre (0,832 mot 0,630). Den sittande personen i notan S4 har 3,62 mot 0,19 cm/ruta². Vinsterna i notans silhuetter och fotkontakt väger inte upp detta som generell ersättning för de fyra proven. Detta är en bedömning av provet, ingen ny ägartröskel.', '',
        '## Körning och budget', '',
        f'Bildbygge: 165,49 s, summan av fyra bildsteg i gemx_prepare.log. Första CPU-starten hade ett eget sökvägsfel (parents[3] på Modal), rättat före GPU. CPU-hämtning och importkontroll: 131,21 s; andra CPU-anropets totala väggtid 138,50 s. Kallstart, från GPU-anrop till första status: {num(cold,2)} s (inklusive kö, start och import).', '',
        f'L40S: 46 068 MiB rapporterat minne. Högsta nvidia-smi-prov vid 1 Hz: {max(p["nvidia_smi_peak_used_mib_so_far"] for p in people)} MiB. PyTorch-toppar: {max(p["vram_peak_allocated_bytes"] for p in people)} byte allokerat och {max(p["vram_peak_reserved_bytes"] for p in people)} byte reserverat. 1 Hz kan missa korta VRAM-toppar.', '',
        f'{tracked} observerade personrutor; {predicted} predikterade personrutor inklusive 30 utfyllda rutor före S4:s person 4. Inferens: {num(forward,3)} s / {tracked} = {num(forward/tracked,3)} GPU-funktionssekunder per observerad personruta ({num(forward/predicted,3)} per predikterad). Med modellens IK: {num((forward+ik)/tracked,3)}. Hela GPU-funktionen, inklusive båda FK-/meshvarianterna, filskrivning och packning: {num(duration,3)} s, {num(duration/tracked,3)} s per observerad personruta. Det är väggtid på en GPU-funktion, inte CUDA-kärnprofilering.', '',
        f'Budgeten debiterar konservativt {num(budget["charged_upper_bound_seconds"]/60,3)} av 90 GPU-minuter (anropets väggtid + 15 s avslutsmarginal). GPU-funktionens egen klocka visar {num(duration/60,3)} minuter; exakt fakturerad/allokerad GPU-tid är inte hämtad från Modal. En enda GPU-funktion kördes, sekventiellt. Inga reservationer kvar. Startbudgeten 30 minuter hölls.', '',
        '## Jämförbara mått', '',
        'J15 = medelnormen av ledpositionernas andra differens i cm/ruta², i kamerarum. Jrel = samma mått relativt bäckenet. Lägre är mindre darr, inte automatiskt bättre rörelse. IoU = median mot befintlig personmask. C och H = medianfel för tyngdpunkt respektive absolut höjdskillnad, procent av bildhöjden. IoU synlig klipper nätet vid maskens nedersta rad. Alla maskrutor prövas.', '',
        '| Tagning/person | Backend | J15 | Jrel | IoU | IoU synlig | C % | H % |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        s=r['silhouette']
        text.append(f'| {r["shot"]}/{r["person"]} | {labels[r["method"]]} | {num(r["jitter_body15_cm_frame2"])} | {num(r["jitter_root_relative_body15_cm_frame2"])} | {num(s.get("iou_median"))} | {num(s.get("iou_synlig_median"))} | {num(100*s["tyngdpunkt_median"],2)} | {num(100*s["hojd_median_abs"],2)} |')
    text += ['', 'Baslinjerna kommer från ut/sam-raw och ut/slutsekvens. Slutsekvensen är sekvens_*.npz med sparade golv-/kontaktändringar. Kompilatorns senare kamera-/stödkompensation i plan.json är inte återspelad. S1:s stora bildförskjutning i slutsekvensens överlägg ska därför inte läsas som en granskning av dess senaste film.', '',
        'Masken är en union av personmasker; jämförelsen beskärs till respektive spårruta och andra predikterade kroppars silhuetter undantas. Kläder, bord, grova maskpixlar och naken kroppsgeometri skiljer sig åt. MHR:s sparade silhuetter använder lod1-hud utan alla korrektiver; GEM använder SOMA MID med korrektiver. IoU mäter bildpassning, inte exakt ledposition.', '',
        '## Ledmappning', '',
        'Anatomiska ledpar för samma body15-urval som baslinjerna. MHR-index och SOMA-index är nollbaserade. Detta är en mappning för mätning, ingen rotationstransfer eller bevisad retarget.', '',
        '| MHR | SOMA | MHR-index | SOMA-index |', '|---|---|---:|---:|']
    mapping=next(r['joint_mapping'] for r in rows if r['method']=='gemx-raw')
    for name,v in mapping.items(): text.append(f'| {name} | {v["soma_name"]} | {v["mhr"]} | {v["soma"]} |')
    text += ['', 'Ordningen verifierades exakt mot SOMA77_JOINT_NAMES i den låsta upstream-filen gem/motion/frontend/joint_sets.py. USD-riggens virtuella Root och 32 procedurvridben ingår inte i de 77 offentliga lederna. MHR och SOMA har olika identiteter och leddefinitioner; det finns ingen 3D-sanning i dessa klipp.', '',
        '## Dolda ben och sittande', '',
        'Samma befintliga ben_synliga-flagga används för alla metoder. Det är ett äldre projektions-/maskmått, ingen manuell annotering av varje dold led. Där flaggan saknar dolda rutor visas saknas. Spannet är största diagonal av en benleds rotrelativa xyz-intervall i cm, inte ett anatomiskt rörelseomfång. Alla xyz-intervall och djupspann finns i gemx_matningar.json.', '',
        '| Tagning/person | Backend | Dolda rutor | Dold J | Dold Jrel | Dolt spann cm | Ben-J, alla spårrutor | Benspann, alla cm |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        h=r['hidden_legs']; a=r['leg_motion_all_tracked_frames']
        text.append(f'| {r["shot"]}/{r["person"]} | {labels[r["method"]]} | {h["frames"]} | {num(h.get("jitter_cm_frame2"))} | {num(h.get("root_relative_jitter_cm_frame2"))} | {num(h.get("max_joint_range_diagonal_cm"),2)} | {num(a.get("jitter_cm_frame2"))} | {num(a.get("max_joint_range_diagonal_cm"),2)} |')
    text += ['', '## Fotglidning', '',
        'S4/person 4 ger 50 vänster- och 51 högerintervall med källa i bild/mask enligt rå SAM:s vrist och tå. Samma intervall används för alla fyra metoder. Kontakt antas med vakts befintliga diagnostik: höjd < 6 cm och vertikalt steg < 1 cm. Det är inte oberoende kontaktannotering. För övriga testpersoner finns inga sådana synliga intervall: saknas, inte noll glidning.', '',
        'MHR mäts i sin ingestvärld, GEM i sin egen Y-upp-värld, rå respektive kontakt/IK. Horisontell steglängd påverkas inte av världens translation eller yaw; metriska skalor är fortfarande monokulära antaganden. Ingen platsjustering eller absolut golvrest har verifierats.', '',
        '| Backend, notan S4/person 4 | Vänster median/p90 cm/ruta | Höger median/p90 cm/ruta |', '|---|---:|---:|']
    for r in rows:
        feet=r['foot_common_reference']['feet']
        if not any(f['pairs'] for f in feet.values()): continue
        a,b=feet['left'],feet['right']
        text.append(f'| {labels[r["method"]]} | {num(a["median_cm_frame"])}/{num(a["p90_cm_frame"])} | {num(b["median_cm_frame"])}/{num(b["p90_cm_frame"])} |')
    text += ['', 'Modellens IK förbättrar alltså fotglidningen i dess egen värld. Kamerarumsdarret för samma person är nästan oförändrat. Om varje metod själv måste projicera båda fotpunkterna i masken blir GEM:s kvalificerade kontaktintervall noll; det är en täckningsbrist och redovisas separat i foot_sliding. Det får inte tolkas som perfekt kontakt.', '',
        '## Tidsmått per person', '',
        '| Tagning/person | Predikterade rutor | Inferens s | Kontakt/IK s | Med FK och filer s |', '|---|---:|---:|---:|---:|']
    for shot in manifest:
        for p in read(ROOT/'ut/gemx'/shot['id']/'timing.json')['people']:
            text.append(f'| {shot["id"]}/{p["person"]} | {p["frames"]} | {num(p["forward_s"],2)} | {num(p["contact_ik_s"],2)} | {num(p["total_s"],2)} |')
    text += ['', 'Första IK-körningen inkluderar Warp-kompilering. Tidigare SAM-loggar har medianer 2,134 / 0,586 / 0,541 / 0,530 s per jobb för S1, S4, S5, S9. Dessa är historiska körningar med annan start-/batchningssituation och okänd motsvarande VRAM; de är inte ett nytt kontrollerat hastighetstest på samma GPU.', '',
        '## Bildgranskning', '',
        'Jag har tittat på alla åtta GEM-remsor (fyra tagningar gånger rå/kontakt-IK), åtta källrutor per remsa, samt de fyra sparade slutsekvensremsorna.', '',
        'Notan S1: GEM:s bål och huvud ligger över personen. Slutsekvensens sparade kamerarumsöverlägg är tydligt förskjutet uppåt; planens senare kompensation ingår inte här. GEM fångar upplyfta händer i grova drag, men armbågar/handleder och dold underkropp är osäkra. Rå/IK-remsorna ser mycket lika ut. Bildpassningen blir bättre än denna slutsekvens, men 3D-darr och dold benrörelse blir högre.', '',
        'Notan S4: stående personens huvud, armar och bål följer bilden rimligt; den sittande personen kommer in i granskningen först när den finns i spåret. Sittande knän och fötter är grövre och passar inte lika väl som överkroppen. Ingen stor kroppsvändning syns mellan de åtta provrutorna. Darrmåttet visar ett stort kamerarumsproblem som en gles remsa inte kan visa som en film. IK förbättrar fotbanan i GEM:s värld, men flyttar inte bort problemet i kamerarummet.', '',
        'Råvara S5: GEM följer framåtlutningen mot disken, men handlederna hamnar ofta förskjutna från de synliga händerna och de dolda benen vandrar när personen lutar sig. Kamerarumsspannet för dolda ben är 36,5 cm efter IK, mot 23,9 cm i slutsekvensen. Samtidigt är dess silhuettpassning sämre. IK-remsan visar ingen tydlig förbättring av överkroppens passning.', '',
        'Råvara S9: bröst och huvud följer närbilden ungefär. En handled försvinner bakom vågen i modellen medan händerna börjar lyftas; senare går armar mot ansiktet, med synliga avvikelser. Kroppen fortsätter utanför bild utan verifierbart underlag. Modellens IK återställer inte detaljrörelsen.', '',
        'Ingen ny Blenderfilm eller sida-vid-sida-film har byggts: det tillhör steg 2 och dess kvalitetsvillkor uppfylldes inte. De granskade bilderna är diagnostiska källöverlägg, inte en slutfilm.', '',
        '## Riggrutt och pipeline', '',
        'Ingen riggrutt har satts i produktion. SOMA:s MHR-backend är en identitetsbackend; detta bevisar inte en exakt omvandling av GEM:s 77 rotationer till MHR:s 127 leder/parametrar. Inget konverteringsfel har mätts och ingen handgjord retarget har levererats. En eventuell fortsättning bör först pröva en direkt SOMA-rigg enligt alternativ a för att bevara modellens egen geometri.', '',
        'Nedströmsläsning visar direkta MHR-beroenden i kompilera.py, kalla_bygg.py, mhr_rig.py, trohet/stöd, props/ankare och kvalitet. --kropp gemx finns därför inte i ingest efter detta prov. Kompilering, kvalitetsrapport, props/ankare, platsjustering, Blender --plan, film och webbläsarexport under forvarld är inte verifierade/fungerande med GEM-X. SAM-vägen är orörd. Inga gamla temporal-, golv-, kontakt- eller stödsteg har tagits bort eller mätts med vakt som GEM-ablation. Inga nya ingest-/kontraktkommandon har införts.', '',
        'GEM:s råa värld sparas, men dess koordinater är inte platsens koordinater. Kameraläge är upstream background (approximerad bakgrundsrotation), intrinsics övertagna från manifestet och märkta antagna. Varken ankare, COLMAP-skala, gemensamt golv, världstransform eller rest har verifierats för GEM. Dessa värden får inte användas som färdig platsplacering.', '',
        '## Begränsningar och licenser', '',
        'Dolda kroppar saknar facit. Närbilder ger inte full kroppsinformation. Body Motion har hand-/ansiktsleder, men detta prov har ingen separat handinferens, inga granskade fingermått och ingen ansiktsmimik. Stabilitet innebär inte att osynlig rörelse är rätt.', '',
        'GEM-kod: Apache 2.0 som standard med filspecifika undantag i ATTRIBUTIONS.md (bland annat OpenMDW, MIT, BSD och SAM-villkor). Behåll motsvarande licenser och upphovsrättsnotiser vid distribution. GEM:s modellkort hänvisar vikterna till NVIDIA Open Model License: kommersiell användning tillåts enligt avtalet; villkor/notiser ska följa med vid vidare distribution. NVIDIA gör inte anspråk på utdata. HF-repots LICENSE-fil säger samtidigt Apache 2.0. Denna motsägelse är dokumenterad, inte juridiskt avgjord.', '',
        'SOMA-X-kod och dessa SOMA v0.3.3-tillgångar: Apache 2.0. Andra identitetsbackendars separata modeller får inte automatiskt samma licens. Inga MHR-identitetstillgångar eller handvikter behövdes här.', '',
        'Detektor: OpenMMLab YOLOX-X HumanArt ONNX hämtad från den officiella MMPose-adressen. MMPose-koden är Apache 2.0. Det nedladdade ONNX-arkivet innehåller ingen LICENSE/NOTICE. Separata villkor för just vikterna och HumanArt-underlaget har inte kunnat verifieras; kodlicensen räcker inte som bevis för dem. Med våra spår kringgås själva detektionen, men upstream skapar fortfarande en ONNX-session.', '',
        'Händer: inga EgoHand-/handdetektorvikter hämtade och inga gatevillkor accepterade. Ägaren behöver själv granska EgoHand-v1:s OpenMDW 1.1 och vid begärd HF-gate själv ordna åtkomst/acceptera de visade villkoren. Sparad HF-API-metadata säger gated=false, vilket avviker från uppgiften om gate; faktisk checkpointåtkomst har inte prövats och ska inte antas vara fri.', '',
        'Primärkällor: [GEM-installation](https://github.com/NVlabs/GEM-X/blob/4aef1452e5df171deff4f293c08e643eb450981e/docs/INSTALL.md), [GEM-modellkort](https://huggingface.co/nvidia/GEM-X), [NVIDIA-avtal](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/), [SOMA](https://huggingface.co/nvidia/SOMA-X), [MMPose-licens](https://github.com/open-mmlab/mmpose/blob/main/LICENSE), [EgoHand](https://huggingface.co/nvidia/EgoHand-v1). Verifierade revisioner och nedladdade källor finns i kallor/gemx_verified.json och gemx_live_*; CPU-licensinventering i ut/gemx/asset_audit.json.', '',
        '## Återuppta eller upprepa', '',
        'Kör från projektroten, alltid med scen/.venv/Scripts/python.exe och PYTHONIOENCODING=utf-8. Ingen lokal inferens behövs. Modal-volym: gemx-body-v033. GPU-provet och CPU-licenskontrollen är avslutade.', '',
        '```powershell', "$env:PYTHONIOENCODING='utf-8'",
        'scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode prepare',
        'scen/.venv/Scripts/python.exe -B -m modal run scen/3d/ingest/modal_gemx.py --mode evaluate',
        'scen/.venv/Scripts/python.exe -B scen/3d/kroppsbank/evaluate_gemx.py',
        'scen/.venv/Scripts/python.exe -B scen/3d/kroppsbank/report_gemx.py', '```', '',
        'evaluate-läget återanvänder färdiga tagningar. Gör inte om GPU-provet genom att ta bort filer: kontrollera först budgeten och gör en ny separat körplan. Budgetens reservation skyddar avbrott; den ska avräknas mot Modal innan en ny GPU startas. Den lokala drivaren är byggd för det genomförda första provet, inte för automatiska obegränsade omförsök.', '',
        'Utdata per tagning/person: raw.pt, contact_ik.pt (nativa SOMA-parametrar, villkor, kamera och kontaktlogits), raw_joints.npz/contact_ik_joints.npz (77 leder i kamera och värld, intrinsics och observed), kameramesh per ruta, faces.npy, joint_names.json och timing.json. Per tagning finns overlay_raw.jpg och overlay_contact_ik.jpg. Samlade mått: gemx_matningar.json. Äldre filer som ändrats har originalkopia i fore_gemx med samma projektrelativa sökväg. Arbetsloggen är GEMX-LOGG.md.', '']
    target=ROOT/'README.md'
    if target.exists():
        backup=ROOT/'fore_gemx'/target.relative_to(WORKSPACE)
        backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists(): shutil.copy2(target,backup)
    target.write_text('\n'.join(text),encoding='utf-8')
    print('README.md written; rows',len(rows),'tracked',tracked,'predicted',predicted)

if __name__=='__main__': main()
