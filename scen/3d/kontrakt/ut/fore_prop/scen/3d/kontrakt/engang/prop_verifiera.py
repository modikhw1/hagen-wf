"""Alla begärda lokala prov, sekventiellt. Ingen ingest eller rendering."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

H=Path(__file__).resolve().parents[1];ROOT=H.parents[2];out=H/'ut/prop_granskning'
stages=[('kontrollera',[str(H/'kontrollera.py')],ROOT),
        ('unittest',['-m','unittest','test_flode','test_rumsmall','test_regler','test_text_disk','test_kroppmatt','test_props'],H),
        ('semantik',[str(H/'semantik/test_semantik.py')],ROOT),
        ('bro',[str(H/'bro/test_bro.py')],ROOT),
        ('rum',[str(H.parent/'ingest/test_rum.py')],ROOT)]
log=out/'prov.log';result=out/'prov.json'
if log.exists() or result.exists():raise FileExistsError(log)
os.environ['PYTHONIOENCODING']='utf-8';os.environ['OMP_NUM_THREADS']='4';records=[]
with log.open('w',encoding='utf-8') as f:
    for name,args,cwd in stages:
        start=time.perf_counter();print(name,'start',flush=True);f.write('\n== '+name+'\n');f.flush()
        r=subprocess.run([sys.executable,'-B',*args],cwd=cwd,env=os.environ,stdout=f,stderr=subprocess.STDOUT)
        row=dict(prov=name,exit=r.returncode,sek=round(time.perf_counter()-start,2));records.append(row)
        result.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(row,flush=True)
        if r.returncode:sys.exit(r.returncode)
