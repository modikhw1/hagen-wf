import os,sys,json,hashlib,shutil
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path.cwd();OUT=ROOT/'forvarld/varld';KON=ROOT/'scen/3d/kontrakt'
sys.path.insert(0,str(KON))
from kalla_omhasha import omhasha
original=KON/'exempel/notan/kalla_jamn.json'
k=json.loads(original.read_text(encoding='utf8'))
out=OUT/'pipeline';out.mkdir(exist_ok=True)
snapshot=out/'snapshot';folders=set();copied={}
def copyfile(p):
    p=p.resolve()
    if p in copied:return copied[p]
    dest=snapshot/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,dest);copied[p]=dest
    return dest
def absolute(o):
    if isinstance(o,dict):
        for key,v in o.items():
            if key=='sokvag' and isinstance(v,str):
                p=(original.parent/v).resolve()
                if p.name=='varld.npz' or p.name.startswith('sekvens_'):folders.add(p.parent)
                o[key]=str(copyfile(p))
            else:absolute(v)
    elif isinstance(o,list):
        for v in o:absolute(v)
absolute(k);changed=[];missing=[];omhasha(k,OUT,changed,missing)
for folder in folders:
    for pattern in ['*.json','masker.npy','kropp/*/*.npz']:
        for file in folder.glob(pattern):copyfile(file)
(out/'kalla.json').write_text(json.dumps(k,ensure_ascii=False),encoding='utf8')
r=json.loads((ROOT/'scen/3d/kontrakt/ut/notan/jamn_tom/regi.json').read_text(encoding='utf8'))
r['kalla'].update(revision=k['revision'],sha256=k['klipp']['sha256'])
(out/'base-regi.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf8')
(out/'copy-report.json').write_text(json.dumps(dict(original=str(original),refreshed=changed,missing=missing,snapshotFiles=len(copied),snapshotBytes=sum(p.stat().st_size for p in copied.values()),method='Private frozen measurement files and absolute pointers, then kalla_omhasha.omhasha; originals untouched'),ensure_ascii=False,indent=2),encoding='utf8')
print(len(changed),'hashes refreshed;',len(missing),'missing')
