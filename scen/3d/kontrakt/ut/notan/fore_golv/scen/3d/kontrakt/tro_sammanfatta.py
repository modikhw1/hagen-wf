"""Samla lokala mätningar, filskillnader och den visuella granskningen."""
import difflib
import json
from pathlib import Path
import shutil
import numpy as np
from gemensamt import HIT,skriv,ladda
from trohet import gravitation,F
from trostod import BEN,FORALDER,IX,begransa
from trosula import per_fot

ROT=HIT.parents[2];UT=HIT/'ut/notan'


def main():
    p=ladda(UT/'tro_tom/plan.json');fore=ladda(UT/'tro_fore_notan_matning.json')
    kontroll=ladda(UT/'tro_tom/byggkontroll.json');tider=ladda(UT/'tider_tro.json')
    nya=['trohet.py','trostod.py','tropassning.py','trosula.py','tro_export_rigg.py',
         'tro_granska_blender.py','tro_jamfor.py','tro_bar_blender.py','verifiera_tro.py','tro_sammanfatta.py','tro_rigg.json']
    andrade=['scen/3d/kontrakt/'+n for n in ('kompilera.py','test_flode.py','test_rumsmall.py','README.md')]
    andrade+=['scen/3d/ingest/mhr_rig.py','scen/3d/ingest/README.md']
    files=[]
    for rel in andrade+['scen/3d/kontrakt/'+n for n in nya]:
        f=ROT/rel;b=UT/'fore_tro'/rel
        old=b.read_text(encoding='utf-8').splitlines() if b.exists() else []
        new=f.read_text(encoding='utf-8').splitlines();d=list(difflib.ndiff(old,new))
        files.append(dict(fil=rel,plus=sum(x.startswith('+ ') for x in d),minus=sum(x.startswith('- ') for x in d)))
    files.append(dict(fil='scen/3d/kontrakt/tro_fothud.npz',ny_binar_bytes=(HIT/'tro_fothud.npz').stat().st_size,status='uppmatt ur lokal lod3.fbx'))
    skriv(UT/'filandringar_tro.json',files)
    # Alla rutor: fasta personmått, exakt skyddad överkropp, och sulmått per fot.
    body=[]
    for d in p['scener']:
        for pm in d['personer']:
            s=dict(np.load(pm['rorelse']));v=dict(np.load(d['varld']));m=np.array(d['till_plats']);g=m[:3,:3]@gravitation(v)
            err=[];upper=[];feet=[];choices=set()
            for f in range(d['lokal_start'],d['lokal_start']+d['ut'][1]-d['ut'][0]):
                q=g@v['kam_R'][f]@F;t=g@(v['kam_C'][f]+v['kam_R'][f]@s['cam_t'][f])+m[:3,3]
                pose,r=begransa(s['pose'][f],q,t,pm['stod'],s['ben_synliga'][f],pm['benlangder_m'])
                err.append(r['benlangd_maxfel_m']);upper.append(float(np.max(np.abs(pose[34:]-s['pose'][f,34:]))))
                feet.append(per_fot(pose,q,t));choices.update(b['val'] for b in r['ben'])
            body.append(dict(scen=d['id'],person=pm['id'],rutor=len(err),max_benfel_m=max(err),max_overkroppsandring=max(upper),
                             sulor={side:dict(min_m=min(x[side] for x in feet),max_m=max(x[side] for x in feet)) for side in 'lr'},val=sorted(choices)))
    skriv(UT/'tro_kroppskontroll.json',body)
    oldbar=ladda(UT/'tro_fore_bar.json');bar=ladda(UT/'tro_barplan.json')
    byggregression=all(bar[k]==v for k,v in oldbar.items())
    assert byggregression
    rows=['# Bildtrohet, kroppsstöd och bord: notan', '',
          'Alla arbeten är lokala. Ingen ingest har körts om, inget nätjobb har startats och den öppna Blender-sessionen har inte använts. Ursprungliga ändrade filer finns under `fore_tro/scen/...`. Det egna första renderprovet finns under `fore_tro/eget_forsta_prov/`. Tidigare mall- och platsfilmer är orörda.', '',
          '## Framing: mätt orsak och rättning', '',
          'Orsaken är `ingest/ingest_klipp.py:227`: golvsteget multiplicerar bara `cam_t` med sin skala, medan kroppens ledavstånd behålls. Kommentarens påstående vid rad 197 om oförändrad bildprojektion är fel för en kropp med ändlig utsträckning. Planen kompenserar nu med en motsvarande kameratranslation (`kompilera.py:150–164`). Personen står kvar i platsen, brännvidd och rotation ändras inte. Detta är en lokal återställning av den tidigare sparade projektionen, inte en ny kameramätning från videon.', '',
          'Fokal i varje sekvens är exakt samma som i respektive kroppsestimat (max differens 0 px). Estimatorns 3D/translation/fokal återger dess sparade 2D-punkter inom 0,00019 px i full 576×1024-bild. Gemensam rigid platstransform ger samma projektion. Sensorpassningen är horisontell, 36 mm; Blenderkontrollen bekräftar aspekt och tecken. Inget cropfel hittades. Se `tro_diagnos.json`.', '',
          'Primärmåtten jämför exakta riggleder med motsvarande MHR70-punkter. Ansiktets hudpunkter är inte huvudbenets ledcentrum och räknas inte som samma punkt. Osynliga ben redovisas separat i planens JSON. IoU avser samma synliga/tillförlitliga leders omslutningar, inte detektionsrutans hudutsträckning. Bboxhöjden i normaliseringen kommer däremot från sparad `bbox`.', '',
          '| Scen/person | före median/p90 px | efter median/p90 px | före median/p90 bboxandel | efter median/p90 bboxandel | IoU före → efter |',
          '|---|---|---|---|---|---|']
    for old,new in zip(fore['personer'],p['kvalitet']['bildtrohet']['personer']):
        rows.append(f"| {new['scen']}/{new['person']} | {old['median_px']:.2f}/{old['p90_px']:.2f} | {new['median_px']:.2f}/{new['p90_px']:.2f} | {old['median_bboxandel']:.4f}/{old['p90_bboxandel']:.4f} | {new['median_bboxandel']:.4f}/{new['p90_bboxandel']:.4f} | {old['bbox_iou']:.3f} → {new['bbox_iou']:.3f} |")
    rows+=['', 'Egna diagnostiska gränser, inte ägarkrav: median 20 px/4 %, p90 40 px/8 %, IoU minst 0,65. De har marginal över notans goda scener och den redigerade bars befintliga rest. En enda överskriden gräns flaggar personen/scenen; rendering kräver då uttryckligt granskningsläge `--tillat-flaggad`.', '',
           'S6 flaggas fortfarande: poseutjämningen ensam ger p90 68,405 px, translationsutjämningen ensam 4,540 px. Resterande fel kräver en lokal omprövning av tidigare poseutjämning eller byte till sparade råposer. Det kräver inte ett nytt betalt kroppssteg, men skulle flytta de handleder som uppgiften skyddar och går utanför förbudet mot omkörning av sekvens. Ingen betald omkörning behövdes för projektionsrättningen.', '',
           f"Numpy mot faktisk Blenderkamera, två rutor per scen: max {kontroll['max_numpy_blender_px']:.6f} px. Även den faktiska CM-redigerade renderkameran kontrollerades. Bar: max 0,000866 px på tre rutor per synlig person.", '',
           'Bars äldre planfält är alla exakt oförändrade (regression med samma regi). Endast `kallbild_hojd`, `matkamera` och `kvalitet` har lagts till. Den tomma bars hela 202-rutorsklipp flaggar person 2:s befintliga p90-rest 9,02 %; den redigerade bars 156 rutor klarar gränserna. Inget döljande tröskelbyte har gjorts för att få hela bar grönt.', '',
           '## Kroppsstöd', '',
           'Personens dolda ben använder konstanta medianmått över alla dess befintliga poser och scener; alla 32 led–förälder-avstånd i benkedjorna kontrolleras. `rest` i NPZ är samma generiska FBX-vilopose för alla personer, inte en personmätning. MHR:s uppmätta överkroppsavstånd varierar redan med pose. Därför kan inte samtidigt generisk rest, konstanta överkroppsavstånd och exakt skyddad överkropp krävas. Överkroppen skyddas; denna kvarvarande konflikt är inte löst genom att kalla generisk rest för personmått.', '',
           f"Samtliga 383 numpy-rutor: längdfel högst {max(r['max_benfel_m'] for r in body):.2g} m, överkroppsändring exakt noll. Blenderprov: längdfel högst {kontroll['max_benlangdsfel_m']*1000:.6f} mm, skyddad överkropps lägesfel högst {max(r['overkropp_max_m'] for r in kontroll['rutor'])*1000:.6f} mm (flyttal).", '',
           'Sitsintervall 0,35–0,65 m är ett antaget mallintervall. Uppmätt medianbäcken minus mallens 0,11 m mjukdel ger A 0,54479 m och B 0,60286 m. Båda ryms. Bäckenet flyttas aldrig för att passa sitsen. Vid otillåten önskad höjd klipps stolen till intervallet och avvikelsen redovisas; inga ben sträcks.', '',
           'A:s sulor hänger ungefär 0,20–0,24 m, B:s ungefär 0,24–0,33 m över golvet. Det är sämre golvkontakt än den tidigare utsträckta gissningen, men förenligt med fasta benmått och skyddat bäcken. Källans osynliga ben ger inte bevis för den valda horisontella lårposen.', '',
           'Servitör C väljer knäböjning och närmaste nåbara golvpunkt med bäckenet oförändrat, eftersom det ändrar minst uppmätt data. NumPy-skinning av uppmätt FBX-fothud ger vänster sula 0,100 mm och höger 0,135–0,546 mm över golvet. Den faktiska hudens globala minimum kontrollerades på alla 383+326 renderade rutor: 0,09959 mm över golvet. Ingen sula går igenom golvet.', '',
           '## Bordhöjd och händer', '',
           'Bordintervallet 0,65–1,05 m är antaget. Evidens är lägsta 12-rutorsfönster med högst 3 cm Z-variation och 8 cm XY-spann (antagna stabilitetsgränser). Stillhet är mätt; att det betyder fysisk bordkontakt är osäkert, särskilt A som också gestikulerar. Handledscentrum är inte handflatans kontaktyta. Handleder flyttas aldrig.', '',
           'A: S6 höger handled, lokala rutor [0,12), 0,91730 m → bord 0,91730 m (tidigare 0,88). B: S2 höger handled [26,38), 1,05568 m → bord klippt till 1,05 m (tidigare 0,94). Ursprung och per-scen-gap finns i kvalitet.hojdpassning.', '',
           '| Scen/person | min/median/p90 handled–skiva, cm |','|---|---|']
    for fit in p['kvalitet']['hojdpassning']:
        for x in fit.get('per_scen',[]):rows.append(f"| {x['scen']}/{x['person']} | {x['min_m']*100:.2f}/{x['median_m']*100:.2f}/{x['p90_m']*100:.2f} |")
    rows+=['', 'Små negativa handledsgap kvarstår: A −5,8 mm och B −2,2 mm. Fingrar kan skära skivan mer, särskilt i S6. Detta är redovisat och inte dolt genom att flytta uppmätta händer.', '',
           '## Filer, kontrakt och kontroller', '',
           'Inga kalla-/regi-/rumsmall-scheman ändras, ingen revision av exemplen behövs och hashlåsta ingestdata lämnas orörda. `plan/1` får valfria fält för mätkamera, bildhöjd, kvalitet, höjdpassning och personliga benmått. Befintliga CLI-positioner och flaggor behålls. `--tillat-flaggad` är ett nytt valfritt granskningsläge.', '',
           '| Fil | +/− rader |','|---|---|']
    rows += [f"| {x['fil']} | +{x['plus']}/−{x['minus']} |" for x in files if 'plus' in x]
    rows += ['',f"`tro_fothud.npz`: ny uppmätt riggdata, {(HIT/'tro_fothud.npz').stat().st_size} byte. Detaljer: filandringar_tro.json.", '',
             'Kommandon från projektroten, PYTHONIOENCODING=utf-8 och scen/.venv/Scripts/python.exe:', '',
             '```text', 'scen/.venv/Scripts/python.exe scen/3d/kontrakt/kontrollera.py exempel/bar',
             'scen/.venv/Scripts/python.exe scen/3d/kontrakt/kontrollera.py exempel/notan',
             '# Med arbetsmapp scen/3d/kontrakt:', 'C:/Users/praiseworthy/Desktop/hagen-wf/scen/.venv/Scripts/python.exe -m unittest test_flode test_rumsmall',
             '# Filmer, första körningen (vägrar befintlig film):', 'scen/.venv/Scripts/python.exe scen/3d/kontrakt/verifiera_tro.py',
             'scen/.venv/Scripts/python.exe scen/3d/kontrakt/tro_jamfor.py', '```', '',
             'Kontrollera: bar 0 fel/0 varningar/15 hashar, notan 0 fel/0 varningar/64 hashar. Unittest: 57 tester OK, 218,868 s testtid/219,484 s väggtid. Logg unittest_tro_slut.log. Det omfattar känd syntetisk kamera med nollfel, fel fokal som flaggas, alla notans rutor med fasta benmått/skyddad överkropp/hudgolv, sitsintervall och äldre flödesregressioner.', '',
             'Båda filmerna avkodas helt med ffmpeg utan fel; H.264/AAC, 576×1024: tom 383 rutor/12,7667 s, redigerad 326 rutor/10,8667 s. Ingen ljudlyssning. Se tro_filmkontroll.json.', '',
             '## Filmer, blad och väggtider', '',
             '`tro_tom/film.mp4`, `tro_redigerad/film.mp4`, `tro_jamforelse/s1.png`–`s7.png`, `tro_tom/oversikt_ovan.png`, `tro_tom/oversikt_sned.png`. Bar har tre granskade stillbilder i `tro_bar/` samt `tro_bar/jamforelse.png`.', '',
             '| Fas | Sekunder |','|---|---|']
    rows += [f"| {k} | {v['tid_s']:.3f} |" for k,v in tider.items()]
    rows += ['', 'Blender hittas genom att läsa BLENDER-konstanten i ingest_klipp.py med AST. Alla processer är egna bakgrundsprocesser. Samtliga slutliga Blenderprocesser avslutas med kod 0; Intel-kraschen återkom inte. Alternativ mjukvarubakände har därför inte provats. Inget befintligt blend-dokument från GUI-sessionen har öppnats eller ändrats.', '',
             '## Visuell granskning, samma två rutor per scen', '',
             'S1: huvud och axlar har nu ungefär källans storlek och position, luft ovanför huvudet återställd. Gesten är bevarad. Handled/hand ligger högt över bordet också i källan. Bordet saknar rekvisita och personens hudform är generisk.', '',
             'S2: huvudet ryms nu; storlek och placering följer källan mycket bättre. Bordet ligger närmare stödhandens höjd. Handens/fingrarnas pose och kroppens lutning skiljer sig fortfarande från den klädda personen.', '',
             'S3: motsvarande huvudläge och skala; armgesten är i stort densamma. Fingerdetaljer och hudform är fortfarande grova. Ingen ny beskärning.', '',
             'S4: servitören får källans större skala/högre läge, snarare än den tidigare för lilla figuren. Golvkontakten finns i översikten. En mallskiva skymmer mer av den nedre kroppen än källans gång; placeringen av möbler och C är fortsatt antagen.', '',
             'S5: huvudet och överkroppen krymper till ett utsnitt närmare källan. Den utsträckta handen har rimligare bildläge. Händer kan tangera skivan och de stora släta ytorna gör bedömningen av kontakt svår.', '',
             'S6: tydligt bättre huvudskala/läge, men handgesten är fortfarande för låg/fel mot källan på vissa rutor. Den högre skivan gör vissa fingerpenetrationer tydligare: det blev visuellt sämre där. Scenen är flaggad.', '',
             'S7: B är nu liten och långt bort, nära källans huvudläge och skala. Hela bortre bordet och mer rum syns. De kortare fasta benen hänger och ser mindre naturligt golvförankrade ut än källans mörka byxben; den förra anatomiska sträckningen är borta. Bordens relativa avstånd och fotavtryck är fortfarande mall/antagande.', '',
             'Bar: de tre tomma-regi-proven behåller personernas bildstorlek och läge; huvuden/hår och den klädda konturen är inte identiska. Diskens stora terminalbox och grova rum är tidigare brister, inga nya måttändringar. Hela klippets redan befintliga person-2-rest flaggas nu.', '',
             '## Kvar, högst sex', '',
             '1. S6:s tidigare poseutjämning avviker från sparade estimatorpunkter; en rättning skulle ändra skyddade handleder. Ingen betald körning krävs, men lokal omprövning av sekvens behövs.',
             '2. Överkroppens befintliga poseberoende ledavstånd kan inte både låsas till generisk rest och lämnas exakt oförändrade. Fasta mått har därför genomförts för dolda ben, inte genom ommodellering av uppmätt överkropp.',
             '3. Sittfötter hänger 20–33 cm. Dolda lårposer, golvhöjd och anatomisk skala är inte verkligt inmätta; sänkning av stolen ensam kan inte flytta skyddat bäcken.',
             '4. Stilla handleder bevisar inte fysisk bordkontakt. Finger/skivpenetration och negativa millimetergap kvarstår, särskilt S6.',
             '5. Layout, möbelmått och C:s plats är delvis antagna; IoU mellan leder bevisar inte hudsilhuett eller korrekt rum. Full bar flaggar en befintlig rest.',
             '6. Ingen ny betald ingest, fotorealistisk yta, ljudlyssning eller alternativ renderbakände har verifierats. Intel-felet återkom inte i detta arbete.', '']
    (UT/'tro_rapport.md').write_text('\n'.join(rows),encoding='utf-8')
    # Testet skriver ett granskningsplan-exempel. Återställ dess tidigare innehåll.
    rel='scen/3d/kontrakt/ut/bar/plan_props_test.json';b=UT/'fore_tro'/rel
    if b.exists():
        current=ROT/rel;snapshot=UT/'fore_tro/testgenererat_plan_props_test.json'
        if not snapshot.exists():shutil.copy2(current,snapshot)
        shutil.copy2(b,current)
    print('Rapport:',UT/'tro_rapport.md')
    print('Ändrade befintliga filer:',[(x['fil'],x['plus'],x['minus']) for x in files[:6]])


if __name__=='__main__':main()
