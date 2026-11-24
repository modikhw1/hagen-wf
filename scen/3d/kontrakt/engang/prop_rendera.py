"""Fem lokala filmer i nya mappar. Aldrig två Blender samtidigt."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

H=Path(__file__).resolve().parents[1];ROOT=H.parents[2];sys.path.insert(0,str(H/'semantik'))
from sem_gemensamt import KLIPP

os.environ['PYTHONIOENCODING']='utf-8';os.environ['OMP_NUM_THREADS']='4'
tasks=[('b','tom4',None),('kenny','tom4',None),('a','tom4',None),('b','prop_byte','regi_prop_byte.json'),('notan','prop_tom',None)]
rows=[];output=H/'ut/prop_granskning/renderingar.json'
if output.exists():raise FileExistsError(output)
for clip,folder,regi in tasks:
    if (H/'ut'/clip/folder).exists():raise FileExistsError(folder)
    spec=KLIPP[clip];start=time.perf_counter();print(clip,folder,'start',flush=True)
    args=[sys.executable,'-B',str(H/'kor_klipp.py'),clip,str(H.parent/'ingest/ut'/spec['ingest']),str(ROOT/'scen/klipp'/spec['video']),
          '--kalla',('kalla_prop_golv.json' if clip=='notan' else 'kalla_prop.json'),'--undermapp',folder,'--tillat-flaggad']
    if regi:args+=['--regi',str(H/'ut'/clip/regi)]
    log=H/f'ut/prop_granskning/render_{clip}_{folder}.log'
    with log.open('w',encoding='utf-8') as f:r=subprocess.run(args,cwd=ROOT,env=os.environ,stdout=f,stderr=subprocess.STDOUT)
    row=dict(klipp=clip,mapp=folder,exit=r.returncode,sek=round(time.perf_counter()-start,2));rows.append(row)
    output.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(row,flush=True)
    if r.returncode:sys.exit(r.returncode)
