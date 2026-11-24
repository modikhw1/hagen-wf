"""Verifiera riktiga dataplaner och regressioner, helt utan rendering."""
import copy
import json
import sys
import time
from collections import Counter
from pathlib import Path

H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H))
from gemensamt import ladda, skriv, kontrollera
from kompilera import kompilera
from kvalitet import skriv as kvalitet

O = H/'ut/aterupptagning'
GEOMETRI = ['personer','renderkamera','kallrutor','tidskarta','scener']
rows, checks = [], []


def bygg(clip, kallfil, regi, folder):
    out = H/'ut'/clip/folder
    if (out/'plan.json').exists(): raise FileExistsError(out/'plan.json')
    out.mkdir(exist_ok=True)
    skriv(out/'regi.json',regi)
    t = time.perf_counter()
    plan = kompilera(kallfil,out/'regi.json')
    skriv(out/'plan.json',plan); kvalitet(plan,out/'plan.json')
    elapsed = round(time.perf_counter()-t,2)
    row = dict(klipp=clip,mapp=folder,sek=elapsed,props=len(plan.get('props',[])),
               upplosta=sum(p['byggd'] for p in plan.get('props',[])),ej_tillampat=plan['ej_tillampat'])
    rows.append(row); print(row,flush=True)
    return plan


def jamfor(name, before, after, required=True):
    result = {key:before.get(key)==after.get(key) for key in GEOMETRI}
    row = dict(prov=name,kontroller=result,gron=all(result.values()),krav=required)
    checks.append(row); print(row,flush=True)
    if required: assert row['gron'],row


for clip, base, kname, reference in [
    ('bar',H/'exempel/bar/kalla.json','kalla.json','plan_efter_baromkorning.json'),
    ('notan',H/'exempel/notan/kalla.json','kalla_handelser.json','jamn_tom_rattad/plan.json'),
    ('b',H/'ut/b/kalla_jamn.json','kalla_handelser.json','tom3/plan.json'),
    ('kenny',H/'ut/kenny/kalla_jamn.json','kalla_prop.json','tom3/plan.json'),
    ('a',H/'ut/a/kalla_jamn.json','kalla_prop.json','tom3/plan.json'),
]:
    kallfil = base if clip=='bar' else H/'ut'/clip/kname
    k = ladda(kallfil)
    original_regi = H/'exempel/bar/regi.json' if clip=='bar' else H/'ut'/clip/('jamn_tom_rattad/regi.json' if clip=='notan' else 'tom3/regi.json')
    r = ladda(original_regi)
    if clip!='bar': r['edits']=[]
    r['kalla']['revision']=k['revision']
    current = bygg(clip,kallfil,r,'data_prop')
    old = ladda(H/'ut'/clip/reference)
    jamfor(clip+'_sparad_film',old,current,required=clip!='notan')
    if clip!='bar':
        baseline_regi=copy.deepcopy(r);baseline_regi['kalla']['revision']=ladda(base)['revision']
        baseline=bygg(clip,base,baseline_regi,'data_baslinje')
        jamfor(clip+'_prop_och_event_paverkar_inte_kropp_kamera_tid',baseline,current)
    if clip=='notan':
        jamfor('notan_ursprunglig_jamn_tom_mot_nu',ladda(H/'ut/notan/jamn_tom/plan.json'),current,required=False)
    if clip in ('notan','b'):
        counts=Counter(e['typ'] for e in k['semantik']['handelser'])
        assert counts['scen_handling'] and counts['replik_start'] and counts['prop_synlig'] and counts['person_synlig']
        assert not counts['handmote']
        rb=copy.deepcopy(r)
        if clip=='b':
            rb['edits']=[dict(id='produktbyte_fiktivt',op='byt_prop',ursprung=dict(typ='cm'),prop='prop_o1',ny_typ='fiktiv_molnfrukt',
                kommentar='PÅHITTAD produkt ur produkter_fiktiva.json; inget riktigt kundsortiment.')]
            swapped=bygg(clip,kallfil,rb,'data_prop_byte')
            assert not swapped['ej_tillampat'] and any(p['prop_typ']=='fiktiv_molnfrukt' for p in swapped['props'])
            jamfor('b_produktbyte',current,swapped)
            target='prop_o1';fran='s6_prop_o1_synlig';till='s8_semantisk_handling';typ='fiktiv_molnfrukt'
        else:
            target='prop_burk_kallbild';fran='s1_prop_burk_kallbild_synlig';till='s2_semantisk_handling';typ='food_box'
        rb['edits']=[dict(id='byte_fran_handelse',op='byt_prop',ursprung=dict(typ='cm'),prop=target,ny_typ=typ,
            tid=dict(fran=dict(handelse=fran),till=dict(handelse=till,kant='start')),
            kommentar='Lokalt dataprov från avläst förekomst; inget påstående om säker mottagning.')]
        timed=bygg(clip,kallfil,rb,'data_eventbyte')
        assert not timed['ej_tillampat'],timed['ej_tillampat']
        timing=timed['tillampat'][0]['andring']['tid']
        assert timing['forekomster']
        assert any(p['prop_typ']==typ for p in timed['props'])
        assert any(p['id']==target and p['prop_typ']!=typ for p in timed['props'])
        jamfor(clip+'_eventbyte',current,timed)
        skriv(O/(clip+'_handelser.json'),dict(antal=dict(counts),handelser=timed['handelser'],ankare=timing))
    skriv(O/'data_resultat.json',dict(korningar=rows,regressioner=checks))

assert all(r['gron'] for r in checks if r['krav'])
print('Dataprov färdiga',flush=True)
