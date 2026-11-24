"""Fem nya resultatmappar, alltid en Blender i taget."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from textarbete import jsonfil,backup

HIT=Path(__file__).resolve().parent;ROT=HIT.parents[2]
sys.path.insert(0,str(HIT/'semantik'))
from sem_gemensamt import KLIPP


if __name__=='__main__':
    results=[];os.environ['PYTHONIOENCODING']='utf-8'
    jobs=[('b','tom2',None),('kenny','tom2',None),('a','tom2',None),('b','redigerad2',HIT/'ut/b/regi_redigerad.json'),('notan','text_redigerad',HIT/'exempel/notan/regi.json')]
    for clip,folder,regi in jobs:
        v=KLIPP[clip];log=HIT/f'ut/fore_text/render_{clip}_{folder}.log';backup(log)
        cmd=[sys.executable,'-u','-B',str(HIT/'kor_klipp.py'),clip,str(HIT.parent/'ingest/ut'/v['ingest']),str(ROT/'scen/klipp'/v['video']),'--undermapp',folder,'--tillat-flaggad']
        if regi:cmd+=['--regi',str(regi)]
        start=time.perf_counter();print('start',clip,folder,flush=True)
        with log.open('w',encoding='utf-8') as stream:result=subprocess.run(cmd,cwd=ROT,env=os.environ,stdout=stream,stderr=subprocess.STDOUT)
        results.append(dict(klipp=clip,mapp=folder,exit=result.returncode,sekunder=round(time.perf_counter()-start,2),kommando=cmd));jsonfil(HIT/'ut/fore_text/renderingar.json',results)
        print('klart',clip,folder,result.returncode,results[-1]['sekunder'],flush=True)
        if result.returncode:raise SystemExit(result.returncode)
