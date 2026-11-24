"""Ladda arkiverad kod i en separat process, med samma resursbas och samma indata."""
import sys,types,json,hashlib,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
sys.dont_write_bytecode=True
sys.path[:0]=[str(P/'kontrakt'),str(P/'ingest'),str(HERE)]
from prova import save,log
archive=P/'kontrakt/ut/fore_golv2/scen/3d/kontrakt'
provenance=[]
for name in ['trohet','golvmatning','kroppmatt','tropassning','kvalitet','kompilera']:
    src=archive/(name+'.py');data=src.read_bytes()
    mod=types.ModuleType(name);mod.__file__=str(P/'kontrakt'/(name+'.py'));sys.modules[name]=mod
    exec(compile(data,str(src),'exec'),mod.__dict__)
    provenance.append(dict(modul=name,kod=str(src),sha256=hashlib.sha256(data).hexdigest(),resursbas=mod.__file__))
kalla=P/'kontrakt/ut/golv2_ingestprov/notan_dagens_kalla.json'
regi=P/'kontrakt/ut/golv2_ingestprov/notan_regi.json'
plan=sys.modules['kompilera'].kompilera(kalla,regi,snabb=True)
target=HERE/'fore/plan.json'
backup=P/'kontrakt/ut/fore_golv2_blender'/target.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists():shutil.copy2(target,backup)
save(target,plan);save(HERE/'fore/kodursprung.json',provenance)
print('FOREPLAN OK',len(plan['objekt']),len(plan.get('props',[])),flush=True)
log('Korrigerad föreplan kompilerad med arkiverad GOLV2-förekod i separat process mot exakt samma dagens källmanifest och tomma regi som efterplanen. Moduler laddades från backup, deras resursbas behölls; inga produktionsfiler byttes. Första mask-/sidopassen hade provskriptsfel och ersätts efter rättning.',"scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore")
