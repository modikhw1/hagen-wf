"""Kör en lokal del i taget; spara loggar och tider utan nätanrop."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from textarbete import backup, jsonfil, spara, UT

HIT=Path(__file__).resolve().parent
ROT=HIT.parents[2]
sys.path[:0]=[str(HIT/'semantik'),str(HIT.parent/'ingest')]
from sem_gemensamt import KLIPP


def forbered(clip):
    from kalla_flera import bygg_flera
    from kalla_bygg import sha
    v=KLIPP[clip];ingest=HIT.parent/'ingest/ut'/v['ingest'];video=ROT/'scen/klipp'/v['video'];folder=HIT/'ut'/clip
    place=folder/'plats_text'
    log=UT/f'plats_{clip}.log'
    backup(log)
    for existing in place.glob('*'):
        if existing.is_file():backup(existing)
    backup(folder/'kalla_text.textmatning.json')
    t=time.perf_counter()
    with log.open('w',encoding='utf-8') as stream:
        subprocess.run([sys.executable,'-B',str(HIT.parent/'ingest/plats.py'),str(ingest),'--ut',str(place),'--video',str(video)],cwd=ROT,env=os.environ,stdout=stream,stderr=subprocess.STDOUT,check=True)
    print('plats',clip,round(time.perf_counter()-t,1),flush=True)
    f=folder/'kalla.json';k=bygg_flera(ingest,f.with_name('kalla_text.json'),video,None,None,sha,place/'plats.json',HIT/'semantik/ut'/clip/'semantik.json')
    if f.exists():k['revision']=json.loads(f.read_text(encoding='utf-8'))['revision']
    jsonfil(f,k)
    print('kalla',clip,len(k['semantik']['skarmtext']),round(time.perf_counter()-t,1),flush=True)


def notan():
    from skarmtext import items
    f=HIT/'exempel/notan/kalla.json';k=json.loads(f.read_text(encoding='utf-8'))
    sem=json.loads((HIT/'semantik/ut/notan/semantik.json').read_text(encoding='utf-8'))
    k['semantik']['skarmtext'],log=items(k,sem,(f.parent/k['klipp']['video']['sokvag']).resolve())
    jsonfil(f,k);jsonfil(HIT/'ut/notan/textmatning.json',log)
    # kor_klipp använder samma kontrakt som exemplens regi; rebasa bara filreferenser.
    import os
    def rebase(o):
        if isinstance(o,dict):
            for key,value in o.items():
                if key=='sokvag':o[key]=os.path.relpath((f.parent/value).resolve(),HIT/'ut/notan').replace('\\','/')
                else:rebase(value)
        elif isinstance(o,list):
            for v in o:rebase(v)
    rebase(k);jsonfil(HIT/'ut/notan/kalla.json',k)
    print('notan',len(k['semantik']['skarmtext']),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('klipp',choices=['b','kenny','a','notan']);a=p.parse_args()
    os.environ['PYTHONIOENCODING']='utf-8'
    notan() if a.klipp=='notan' else forbered(a.klipp)
