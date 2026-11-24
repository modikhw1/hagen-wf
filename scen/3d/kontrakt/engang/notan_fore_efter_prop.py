"""Ommät notans sju gamla scener mot orörda fore_jamn-kopior."""
import copy
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch
import numpy as np

H=Path(__file__).resolve().parents[1];sys.path.insert(0,str(H))
from kroppmatt import matt_plan
from trohet import mat
old=json.loads((H/'ut/notan/golv_tom/plan.json').read_text(encoding='utf-8'))
new=json.loads((H/'ut/notan/jamn_tom/plan.json').read_text(encoding='utf-8'))
mapping={};paths=[]
for sc in old['scener']:
    paths+=[sc['varld']]+[pm['rorelse'] for pm in sc['personer']]
for f in paths:
    p=Path(f);backup=p.parent/'fore_jamn'/p.name
    if not backup.exists():raise FileNotFoundError(backup)
    mapping[str(p.resolve())]=backup
original=np.load
def load(f,*args,**kwargs):return original(mapping.get(str(Path(f).resolve()),f),*args,**kwargs)
t=time.perf_counter()
with patch('numpy.load',side_effect=load):
    before_px=mat(old);before_body=matt_plan(old)
out=dict(sek=round(time.perf_counter()-t,2),kalla='golv_tom/plan.json med sekvens/varld från fore_jamn; kamera, möbler och stöd från den gamla planen. Samma oförändrade rådata och masker.',
         fore=dict(bildtrohet=before_px,kropp=before_body),efter=dict(bildtrohet=new['kvalitet']['bildtrohet'],kropp=new['kvalitet']['kropp']['rader']))
path=H/'ut/prop_granskning/notan_fore_efter.json'
if path.exists():raise FileExistsError(path)
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('klart',out['sek'],'s')
