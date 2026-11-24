"""Källvertikaler och granskade disksidor; nya platsfiler, samma text-id."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from textarbete import backup,jsonfil,UT
from kalla_plats import plats_delar

HIT=Path(__file__).resolve().parent;ROOT=HIT.parents[2]
sys.path[:0]=[str(HIT.parent/'ingest'),str(HIT/'semantik')]
from kamera_vertikal import kor
from sem_gemensamt import KLIPP


if __name__=='__main__':
    for clip in ['b','kenny','a']:
        info=KLIPP[clip];ingest=HIT.parent/'ingest/ut'/info['ingest'];f=HIT/f'ut/{clip}/kalla.json';k=json.loads(f.read_text(encoding='utf-8'))
        logs=kor(ingest,HIT/f'semantik/ut/{clip}/semantik.json',backup,jsonfil);jsonfil(UT/f'vertikaler_{clip}_slut.json',logs)
        place=HIT/f'ut/{clip}/plats_text2';log=UT/f'plats_{clip}_ompassning.log'
        with log.open('w',encoding='utf-8') as stream:
            subprocess.run([sys.executable,'-B',str(HIT.parent/'ingest/plats.py'),str(ingest),'--ut',str(place),'--video',str(ROOT/'scen/klipp'/info['video'])],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
        def pek(p,role):
            p=Path(p);return dict(sokvag=os.path.relpath(p,f.parent).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),format='json',roll=role)
        scenes=k['semantik']['scener'];sem,measurement,bindings,props=plats_delar(place/'plats.json',[(s['id'],s['kamera'],s['id'].upper()) for s in scenes],pek,{s['id']:s['personer'] for s in scenes})
        k['semantik']['platser']=[sem];k['matning']['platser']=[measurement];k['semantik']['props']=props
        source=json.loads((place/'plats.json').read_text(encoding='utf-8'))
        for s in scenes:
            s['plats_id'],s['bindningar']=bindings[s['id']];b=next(b for b in source['kamera_bindningar'] if b['tagning']==s['id'].upper());s['kamera_bindning']={key:b[key] for key in ['ankare','status','metod']}
        for camera in k['matning']['kameror']:
            p=(f.parent/camera['spar_metrisk']['sokvag']).resolve();camera['spar_metrisk']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        jsonfil(f,k);print(clip,'klart',flush=True)
