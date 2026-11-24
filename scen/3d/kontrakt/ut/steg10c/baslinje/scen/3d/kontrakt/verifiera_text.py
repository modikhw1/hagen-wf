"""Kör de beställda kontrollerna seriellt och logga väggtid."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from textarbete import backup,jsonfil

HIT=Path(__file__).resolve().parent;ROT=HIT.parents[2];UT=HIT/'ut/fore_text'
PY=ROT/'scen/.venv/Scripts/python.exe'
COMMANDS=[
    ('exempel',ROT,[str(PY),'-B',str(HIT/'kontrollera.py')]),
    ('unittest',HIT,[str(PY),'-B','-m','unittest','test_flode','test_rumsmall','test_regler','test_text_disk']),
    ('semantik',ROT,[str(PY),'-B',str(HIT/'semantik/test_semantik.py')]),
    ('bro',ROT,[str(PY),'-B',str(HIT/'bro/test_bro.py')])]


if __name__=='__main__':
    results=[];os.environ['PYTHONIOENCODING']='utf-8'
    for name,cwd,cmd in COMMANDS:
        log=UT/f'kontroll_{name}.log';backup(log);start=time.perf_counter()
        with log.open('w',encoding='utf-8') as stream:result=subprocess.run(cmd,cwd=cwd,env=os.environ,stdout=stream,stderr=subprocess.STDOUT)
        results.append(dict(namn=name,kommando=cmd,cwd=str(cwd),exit=result.returncode,sekunder=round(time.perf_counter()-start,2)))
        print(name,result.returncode,results[-1]['sekunder'],flush=True)
        jsonfil(UT/'kontroller.json',results)
