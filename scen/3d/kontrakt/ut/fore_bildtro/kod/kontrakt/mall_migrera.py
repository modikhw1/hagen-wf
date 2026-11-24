"""Engångsmigrering av notan efter säkerhetskopiering i fore_mall.

Skriver endast tillåtna kontraktsfiler. Ingest körs inte om.
"""
import copy
import json
from pathlib import Path
from gemensamt import HIT,ladda,skriv


def main():
    s=ladda(HIT/'kalla.schema.json')
    s['$defs']['plats']['properties']['rumsmall_id']=dict(description='Valfri vald rumsmall. Den passade instansen ligger hashlåst i matning.platser[].fil.',type='string',minLength=1)
    s['$defs']['platsmatning']['properties']['rumsmall']=dict(description='Valfri referens till den passade mallen i plats.json.',type='object',additionalProperties=False,
        required=['id','sha256','rms_m','status'],properties=dict(
            id=dict(description='Mall-id i rumsmall/.',type='string'),sha256=dict(description='Hash för mallen före passning.',type='string',pattern='^[0-9a-f]{64}$'),
            rms_m=dict(description='Viktad ankarrest efter rigid passning, före stödens lokala anpassning.',type='number',minimum=0),
            status=dict(description='Måttens ursprung.',const='mall')))
    skriv(HIT/'kalla.schema.json',s)
    s=ladda(HIT/'regi.schema.json')
    s['$defs']['byt_miljo']['properties']['rum']['properties']['rumsmall_id']=dict(description='Valfritt mall-id i rumsmall/. Har företräde framför tillgang_id.',type='string',minLength=1)
    (HIT/'regi.schema.json').write_text(json.dumps(s,ensure_ascii=False,indent=1)+'\n',encoding='utf-8',newline='\n')
    skriv(HIT/'plats_bank/fiktiv_lokal.json',dict(schema_version='rumsmall-ref/1',rumsmall_ref='../rumsmall/fiktiv_lokal.json',beskrivning='Bakåtpekare. Den enda mallbanken är rumsmall/. FIKTIV kundlokal.'))


def uppdatera_exempel():
    import hashlib,os
    from kalla_plats import plats_delar
    f=HIT/'exempel/notan/kalla.json';k=ladda(f);p=HIT.parent/'ingest/ut/notan-tagningar/plats/plats.json'
    def pek(p,roll):return dict(sokvag=Path(os.path.relpath(p,f.parent)).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),format='json',roll=roll)
    sem,mat,sc,props=plats_delar(p,[(s['id'],s['kamera'],'S'+s['id'][1:]) for s in k['semantik']['scener']],pek,{s['id']:s['personer'] for s in k['semantik']['scener']})
    k['revision']=3;k['semantik']['platser']=[sem];k['matning']['platser']=[mat];k['semantik']['props']=props
    for s in k['semantik']['scener']:s['plats_id'],s['bindningar']=sc[s['id']]
    k['matning']['kvalitet']=[x for x in k['matning']['kvalitet'] if x['post']!='semantik.platser.rumsmall']
    k['matning']['kvalitet'].append(dict(post='semantik.platser.rumsmall',status='antagen',metod='Mallvald tvåbordstopologi efter bildgranskning, se plats/hand.json. Djupfragment endast evidens.',osakerhet='Rummets mått och material kommer från mall. Två bord väl stödda av S7; avstånd och servitörens läge antagna.',saknas_steg=None,kalla_fil=Path(os.path.relpath(p,HIT.parents[2])).as_posix()))
    skriv(f,k)
    for f in (HIT/'exempel/notan').glob('regi*.json'):
        r=ladda(f);r['kalla']['revision']=3
        f.write_text(json.dumps(r,ensure_ascii=False,indent=1 if f.name=='regi.json' else 2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__': main()
