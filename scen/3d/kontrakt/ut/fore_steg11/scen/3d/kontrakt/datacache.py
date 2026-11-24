"""Beständig lokal cache för härledda data. Ingen cache ändrar planens beslut.

Mätfiler identifieras med absolut sökväg, storlek och nanosekundstämplar.
Kod och riggdata innehållshashas. Saknad/trasig cache ger omberäkning.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile

HIT=Path(__file__).resolve().parent
CACHE=HIT/'ut/cache'

def signatur(filer):
    out=[]
    for p in sorted({Path(os.path.abspath(p)) for p in filer},key=str):
        try:
            st=p.stat();out.append([str(p),st.st_size,st.st_mtime_ns,st.st_ctime_ns])
        except FileNotFoundError:out.append([str(p),None])
    return out

def kodnyckel(filer):
    h=hashlib.sha256()
    for p in sorted({Path(p).resolve() for p in filer},key=str):
        h.update(str(p).encode('utf-8'));h.update(p.read_bytes())
    return h.hexdigest()

def nyckel(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,allow_nan=True,separators=(',',':')).encode('utf-8')).hexdigest()

def hamta(grupp,key):
    try:
        d=json.loads((CACHE/grupp/(key+'.json')).read_text(encoding='utf-8'))
        if d['nyckel']==key and nyckel(d['data'])==d['sha256']:return d['data']
    except (OSError,ValueError,KeyError,TypeError):pass
    return None

def spara(grupp,key,data):
    folder=CACHE/grupp;tmp=None
    try:
        folder.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=folder,suffix='.tmp',delete=False) as f:
            tmp=Path(f.name);json.dump(dict(nyckel=key,sha256=nyckel(data),data=data),f,ensure_ascii=False,allow_nan=True,separators=(',',':'))
        os.replace(tmp,folder/(key+'.json'))
    except OSError:pass
    finally:
        if tmp is not None and tmp.exists():tmp.unlink()

def matfiler(plan,alla=False):
    files=set()
    for sc in plan.get('scener') or plan.get('matkamera',{}).get('scener') or []:
        files.add(Path(sc['varld']))
        for pm in sc['personer']:
            f=Path(pm['rorelse']);folder=f.parent;pid=str(pm.get('ingest_id') or f.stem[8:]);files.add(f)
            files.update(folder/n for n in ('masker.npy','personer.json','personer_matning.json',f'palitlig_{pid}.json',f'bildskydd_{pid}.json',f'utsnitt_{pid}.json'))
            files.update((folder/'kropp'/pid).glob('*.npz'))
            if alla:files.update(p for p in folder.iterdir() if p.suffix in ('.json','.npz','.npy'))
    return files
