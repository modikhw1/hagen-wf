"""Mät slutplanen och skriv golvrapporten utan att röra äldre renderingar."""
import difflib
import json
from pathlib import Path
import numpy as np
from gemensamt import HIT,skriv,ladda
from trohet import gravitation,F
from trostod import begransa,BEN,FORALDER
from trosula import per_fot

ROT=HIT.parents[2];UT=HIT/'ut/notan'


def main():
    p=ladda(UT/'golv_tom/plan.json');old=ladda(UT/'tro_tom/plan.json');body=[]
    for d in p['scener']:
        for pm in d['personer']:
            s=dict(np.load(pm['rorelse']));v=dict(np.load(d['varld']));m=np.array(d['till_plats']);g=m[:3,:3]@gravitation(v)
            lengths=pm['benlangder_m'];feet=[];maxerr=0.;upper=0.;visible=0.
            for f in range(d['lokal_start'],d['lokal_start']+d['ut'][1]-d['ut'][0]):
                q=g@v['kam_R'][f]@F;t=g@(v['kam_C'][f]+v['kam_R'][f]@s['cam_t'][f])+m[:3,3]
                pose,r=begransa(s['pose'][f],q,t,pm['stod'],s['ben_synliga'][f],lengths,skyddade_knan=pm.get('skyddade_knan',{}).get(str(f)))
                upper=max(upper,float(np.max(np.abs(pose[[i for i in range(127) if i not in BEN]]-s['pose'][f,[i for i in range(127) if i not in BEN]]))))
                maxerr=max(maxerr,r.get('benlangd_maxfel_m',0.))
                from trostod import IX
                for side,flag in zip('lr',pm.get('skyddade_knan',{}).get(str(f),[False,False])):
                    if flag:
                        visible=max(visible,float(np.max(np.abs(pose[IX[side+'_lowleg'],:3]-s['pose'][f,IX[side+'_lowleg'],:3])))/100)
                        assert np.array_equal(pose[IX[side+'_upleg']],s['pose'][f,IX[side+'_upleg']])
                feet.append(per_fot(pose,q,t))
            body.append(dict(scen=d['id'],person=pm['id'],max_benfel_m=maxerr,max_skyddad_andring=upper,max_synligt_knalagesfel_m=visible,
                             sulgap_m={side:dict(min=min(v[side] for v in feet),median=float(np.median([v[side] for v in feet])),max=max(v[side] for v in feet)) for side in 'lr'}))
    skriv(UT/'golv_kroppskontroll.json',body)
    comparison=[]
    for a,b in zip(old['kvalitet']['bildtrohet']['personer'],p['kvalitet']['bildtrohet']['personer']):
        comparison.append(dict(scen=b['scen'],person=b['person'],fore=[a['median_px'],a['p90_px']],efter=[b['median_px'],b['p90_px']]))
        assert b['median_px']<=a['median_px']+1e-6 and b['p90_px']<=a['p90_px']+1e-6
    skriv(UT/'golv_framing.json',comparison)
    floor=next(iter(p['kvalitet']['golv_skala'].values()));bar=ladda(UT/'golv_bar/plan.json')['kvalitet']['golv_skala']['ensam']
    report=['# Golv, skala och synlighet', '',
            'Alla värden nedan är lokala beräkningar från befintlig ingest. Inget ingeststeg, nätjobb eller GUI-anrop har körts. Säkerhetskopior: fore_golv/scen/... . Tidigare filmer och blad är orörda.', '',
            '## Golvbeslut', '',
            'Ett golv z=0 används i platsen. Varje tagning har egen kamerahöjd och egen translation till detta plan; samma golvförskjutning för alla kameror skulle återinföra höjdantagandet. Poolen beskriver robust konsensus bland de tidigare registrerade golvoffsetarna, inte en ny global längdskala. Golvhöjder från olika kameraorigo kan inte jämföras direkt utan transformen.', '',
            'Priorer: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm (riggled, inte mätt sittyta); kamerahöjd 1,45 m med reservintervall 1,20–1,70 m. Sittande knä får sjunka 0–12 cm i golvcue, fotled/sula antas 8 cm med posemarginal 3 cm. Dessa är priorer. Modellgolv har antaget felintervall 5 cm RANSAC plus lutning över 0,5 m; ingest sparade inte ett residualstandardfel. Diagnostisk cue-tolerans 10 cm.', '',
            '| Tagning | Cue | Värde ± spridning i tidigare platsram, cm | Använd | Beslut |','|---|---|---|---|---|']
    for shot in floor['per_tagning']:
        for c in shot['beslut']['cues']:
            report.append(f'| {shot["tagning"]} | {c["cue"]} | {c["varde_m"]*100:.2f} ± {c["spridning_m"]*100:.2f} | {c["anvand"]} | {c["beslut"]} |')
    report+=['', 'Den använda handledscuen ovan är rollens lägsta stabila fönster, över alla dess tagningar. Även varje tagnings egna lägsta stabila läge sparas; stillhet bevisar inte kontakt:', '',
             '| Tagning/roll | Lokal handledscue för golv ± spridning, cm |','|---|---|']
    for s in floor['per_tagning']:
        for c in s.get('lokal_handledsevidens',[]):
            value=f'{c["varde_m"]*100:.2f} ± {c["spridning_m"]*100:.2f}' if c['varde_m'] is not None else 'ingen stilla handled'
            report.append(f'| {s["tagning"]}/{c["roll"]} | {value} |')
    report+=['', '| Tagning | Golv i tagningens värld, m | Flytt från tidigare, cm | Spridning ± cm / cuespann cm | Status |','|---|---|---|---|---|']
    for s in floor['per_tagning']:
        r=s['beslut'];report.append(f'| {s["tagning"]} | {s["valt_golv_i_tagningen_m"]:.4f} | {s["flytt_fran_tidigare_m"]*100:+.2f} | {r["spridning_m"]*100:.2f} / {r["spann_m"]*100:.2f} | {r["status"]}; {"konflikt" if r["konflikt"] else "inom tolerans"} |')
    pool=floor['pool'];report+=['',f'Pool: {pool["varde_m"]*100:.2f} cm, spridning ±{pool["spridning_m"]*100:.2f} cm, cuespann {pool["spann_m"]*100:.2f} cm, {pool["status"]}. {pool["orsak"]} Konflikten flaggas, inte dold i ett medelvärde.', '',
        'S1/S3/S6 har djupgolv +33,16/+15,23/+38,27 cm. S4 har djupgolv +27,59 cm men kontrollerad fot från bakgrundspersonen nära −2,48 cm. Foten skyddas mot restaurangpriorer i den lokala konsensusen; djupgolvet avvisas. S2/S5/S7 saknar djupgolv. Kamera-priorn används inte i notans beslut.', '',
        'S7: 0 av 46 rutor har fotstöd i mask + personens egen bbox + knä/vrist/tå/häl. I ruta 0 slutar bbox vid y=497 medan skattade vrister ligger vid y=688–690 och tå/häl vid y=696–724. Synliga mörka byxben/skor i källan bevisar inte att modellens vida fotställning är uppmätt. Ingests synlighet testar index 13–14 (vrister), men kommentaren kallar dem knän. Varken dessa punkter eller de bildmässigt synliga skorna kan ge ett tillförlitligt metriskt fotläge ur sparad data. Inga nya fotmått har hittats på.', '',
        'S4: 55 mask/bbox-kontrollerade fotrutor hör till bakgrundsperson 4, inte servitören C. Personen renderas fortfarande inte eftersom den saknar roll/stödankare. Synliga tillförlitliga ben lämnas oförändrade av stödsolvern.', '',
        '## Skala och möbler', '', 'Skala 1,0 behålls i alla transformerna. Kroppsmodellen ger meter; inga ben skalas. Djupskalan är 1,0 men saknar parallaxverifiering. Möbelpriorerna kan pröva förenlighet, inte legitimera en ny kroppsskala.']
    report+=['', '| Poolad cuefamilj | Median / min–max cm | Använda / tillgängliga cues |','|---|---|---|']
    for family in sorted({c['familj'] for c in pool['cues']}):
        cs=[c for c in pool['cues'] if c['familj']==family];values=[c['varde_m']*100 for c in cs]
        report.append(f'| {family} | {np.median(values):.2f} / {min(values):.2f}–{max(values):.2f} | {sum(c["anvand"] for c in cs)}/{len(cs)} |')
    for c in floor['skala']['kontroller']:
        report.append(f'\n{c["roll"]}: stilla handled minus root {c["handled_minus_backen_m"]*100:.2f} cm; prioravstånd 9–31 cm ger skalförenlighet {c["skala_intervall_fran_prior"][0]:.3f}–{c["skala_intervall_fran_prior"][1]:.3f}. Skala 1,0 inom: {c["skala_1_inom"]}.')
    report+=['', 'Djupets sparade skalkontroll per tagning (10 % är vår diagnostiska tolerans):']
    for c in floor['skala']['djupkontroller']:
        report.append(f'- {c["tagning"]}: djupfaktor {c["djupfaktor"]}, sparse-multiplikator {c["sparse_matching_multiplier"]}, differens {c["skillnad_procent"]}; verifierad {c["verifierad"]}.')
    report+=['', 'B:s handledskontakt, kroppens meter och vanliga bord/sitsar är alltså inte helt förenliga genom enbart golvtranslation. Golvet höjs, men möbelpriorerna märks som antagna och handledsresten behålls synlig. Den tidigare rapportens slutsats att fasta ben i sig måste ge hängande fötter var för stark: ett dolt knä kan sjunka med samma benlängder.', '',
             '| Möbel/person | Höjd före → efter, cm | Kontaktrest |','|---|---|---|']
    for fit in p['kvalitet']['hojdpassning']:
        oldfit=next(v for v in old['kvalitet']['hojdpassning'] if v['typ']==fit['typ'] and v['person']==fit['person'])
        rest=(f'handled {fit["evidens_rest_m"]*100:+.2f} cm' if fit['typ']=='bord' else f'root över sits {fit["backen_over_sits_m"]*100:.2f} cm')
        report.append(f'| {fit["typ"]}/{fit["person"]} | {oldfit["hojd_m"]*100:.2f} → {fit["hojd_m"]*100:.2f} | {rest} |')
    report+=['', '| Scen/person | Vänster sula min–max cm | Höger sula min–max cm | Handled/skiva min / median / p90 cm |','|---|---|---|---|']
    for r in body:
        wrist=next((v for fit in p['kvalitet']['hojdpassning'] for v in fit.get('per_scen',[]) if v['scen']==r['scen']),None)
        gaps='/'.join(f'{wrist[k]*100:.2f}' for k in ('min_m','median_m','p90_m')) if wrist else 'ej bordkontakt'
        report.append(f'| {r["scen"]}/{r["person"]} | {r["sulgap_m"]["l"]["min"]*100:.3f}–{r["sulgap_m"]["l"]["max"]*100:.3f} | {r["sulgap_m"]["r"]["min"]*100:.3f}–{r["sulgap_m"]["r"]["max"]*100:.3f} | {gaps} |')
    report+=['',f'Alla 383 rutor: största längdfel i ändrade bensegment {max(r["max_benfel_m"] for r in body):.3g} m, största ändring i skyddade överkroppsleder {max(r["max_skyddad_andring"] for r in body):.3g}. Synliga knälägen: max {max(r["max_synligt_knalagesfel_m"] for r in body):.3g} m; synlig lårpose exakt bevarad. S4 skyddar båda låren och knälägena i 85 rutor. Deras ursprungliga längdvariation är uppmätta indata, inte nya sträckningar; bara dolda segment normaliseras till fasta personmått.', '',
             '## Bildutsnitt', '', '| Scen/person | Före median/p90 px | Efter median/p90 px |','|---|---|---|']
    for r in comparison:report.append(f'| {r["scen"]}/{r["person"]} | {r["fore"][0]:.2f}/{r["fore"][1]:.2f} | {r["efter"][0]:.2f}/{r["efter"][1]:.2f} |')
    report+=['', '## Skymning', '', p['kvalitet']['skymning']['fore']['metod'], '', '| Scen | Del | Före → efter synliga prov skymda |','|---|---|---|']
    oc=p['kvalitet']['skymning']
    for r in oc['fore']['per_del']:
        after=next((v['andel'] for v in oc['efter']['per_del'] if v['scen']==r['scen'] and v['del_id']==r['del_id']),0.)
        report.append(f'| {r["scen"]} | {r["del_id"]} | {r["andel"]*100:.3f} → {after*100:.3f} % ({r["ockluderade_prov"]}/{r["synliga_maskprov"]}) |')
    for r in oc['atgarder']:report+=['',f'{r["scen"]}/{r["del_id"]}: {r["atgard"]}. {r["orsak"]}']
    report+=['', 'Omvänd kontroll: maskfrånvaro kan vara segmenteringsfel. Bara rapport, ingen ny möbel:']
    for r in oc['efter']['omvand']:report.append(f'- {r["scen"]}: {r["utan_mallstod"]}/{r["mojligt_dolda_punkter"]} möjliga dolda punkter utan framförliggande mall.')
    report+=['', '## Bar, en tagning', '', 'Bardisk ger inga priorer för vanliga restaurangbord/sitsar. Standardplanen är oförändrad. Cuekontrollen körs även utan platsreferens.']
    for c in bar['per_tagning'][0]['beslut']['cues']:report.append(f'- {c["cue"]}: {c["varde_m"]:.4f} ± {c["spridning_m"]:.3f} m, används {c["anvand"]}.')
    br=bar['pool'];report+=['',f'Beslut {br["varde_m"]:.4f} ± {br["spridning_m"]:.3f} m, {br["status"]}; cuespann {br["spann_m"]*100:.2f} cm. Tidigare golv −1,4484 m; skillnad cirka −1,4 cm ger inget tydligt stöd för att ändra det. Endast en fotruta är verifierbar. Djupets sparse-multiplikator är 0,5702 och skalavvikelsen 75,37 %: skala 1,0 är alltså inte verifierad, men enbart dessa motstridiga skattningar motiverar inte ny kroppsskala. --tillampa-golv är ett uttryckligt alternativ i plats.py, inte aktiverat för bar.', '',
             '## Filer och verifiering', '', 'CLI-positioner bevaras. plats.py får valfritt --tillampa-golv för ensam tagning. Inga JSON-scheman ändras. plats/1 får golv.matning; plan/1 kvalitet får golv_skala, skymning och ledersattningar samt personfältet skyddade_knan. Notans källa/regi uppdateras till revision 4 för den nya hashlåsta platsfilen. Bar ändrar endast diagnostikfält.']
    backups=UT/'fore_golv';manifest=ladda(backups/'manifest.json');changes=[]
    candidates=[ROT/rel for rel in manifest]+[ROT/'scen/3d/ingest'/n for n in ['mhr_rig.py','plats_oversikt.py']]+[HIT/n for n in ['golvmatning.py','skymning.py','kvalitet.py','golv_exempel.py','verifiera_golv.py','golv_jamfor.py','golv_sammanfatta.py','golv_metadata.py']]
    for f in candidates:
        if not f.is_file():continue
        rel=f.relative_to(ROT).as_posix();oldfile=backups/rel
        if oldfile.exists() and oldfile.read_bytes()==f.read_bytes():continue
        oldlines=oldfile.read_text(encoding='utf-8').splitlines() if oldfile.exists() else []
        diff=list(difflib.ndiff(oldlines,f.read_text(encoding='utf-8').splitlines()))
        changes.append(dict(fil=rel,plus=sum(v.startswith('+ ') for v in diff),minus=sum(v.startswith('- ') for v in diff)))
    skriv(UT/'filandringar_golv.json',changes)
    report+=['', '| Fil | + / − rader |','|---|---|']+[f'| {c["fil"]} | +{c["plus"]} / −{c["minus"]} |' for c in changes]
    report+=['', 'Fasernas väggtider: tider_golv.json. Film/mappar: golv_tom/, golv_redigerad/, golv_jamforelse/. kvalitet.md ligger bredvid varje plan; alla cuevärden finns även i plats.json och plan.json.']
    if (UT/'golv_slutkontroll.json').exists():
        checks=ladda(UT/'golv_slutkontroll.json');test=checks['unittest']
        report+=['', '## Slutkontroller', '',
                 'Alla Pythonkommandon använder scen/.venv/Scripts/python.exe och PYTHONIOENCODING=utf-8. Kontrollera och filmskripten körs från projektroten; unittest körs i scen/3d/kontrakt.', '',
                 f'`python -m unittest test_flode test_rumsmall`: {test["tester"]} tester, {test["resultat"]}, {test["tid_s"]:.3f} s. Logg unittest_golv_final.log. PowerShell lagrar denna logg som UTF-16; dess NativeCommandError-dekoration kommer av att unittest skriver normal status till stderr, medan processens exitkod är 0.', '']
        for c in checks['kontrollera']:report.append(f'- {c["kontroll"]}: {c["resultat"]} ({c["tid_s"]:.3f} s).')
        report+=['', '| Fas | Väggtid s |','|---|---|']
        for phase,v in checks['rendering'].items():report.append(f'| {phase} | {v["tid_s"]:.3f} |')
        report+=['', 'Båda filmerna är H.264/AAC, 576×1024. Tom: 383 rutor/12,7667 s. Redigerad: 326 rutor/10,8667 s. Hela filmerna avkodades med ffmpeg utan fel (0,71/0,63 s). Ingen ljudlyssning.', '',
                 'De slutliga diagnoserna uppdaterades efter en reservprior-kontroll. Alla planfält som styr renderingen är exakt lika före/efter uppdateringen, verifierat i golv_metadata_verifiering.json; kameror, objekt, stöd och tidskarta motsvarar därför filmerna.', '',
                 'Alla 14 slutliga jämförelseblad och fyra översikter har öppnats. Den konkreta scenbedömningen, även försämringarna i redigerad S1, B:s handkontakt och S7:s skoskymning, finns i [golv_granskning.md](golv_granskning.md). S6 är fortsatt dålig; övriga notanscener kräver granskning på grund av antaget golv/skala.', '',
                 'Blender hittades genom AST-läsning av BLENDER-konstanten i ingest_klipp.py. Endast egna bakgrundsprocesser med --factory-startup användes. Den öppna GUI-sessionen och dess filer har inte anslutits eller ändrats. Inga nätjobb, nedladdningar eller installationer.']
    (UT/'golv_rapport.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('Rapport, kropps- och bildkontroll skrivna.',flush=True)


if __name__=='__main__':main()
