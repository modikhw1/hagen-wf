"""Beständig lokal cache för härledda data. Ingen cache ändrar planens beslut.

Mätfiler identifieras med absolut sökväg, storlek och nanosekundstämplar.
Kod och riggdata innehållshashas. Saknad/trasig cache ger omberäkning.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile
import numpy as np

HIT=Path(__file__).resolve().parent
CACHE=HIT/'ut/cache'

def signatur(filer):
    out=[]
    for p in sorted({Path(os.path.abspath(p)) for p in filer},key=str):
        try:
            st=p.stat();out.append([str(p),st.st_size,st.st_mtime_ns,st.st_ctime_ns])
        except FileNotFoundError:out.append([str(p),None])
    return out

_KOD_MINNE={}   # processminne: (sökväg, storlek, ändring, skapad) -> sha256 av innehållet

def _innehallshash(p):
    """sha256 av en fil. I samma process räknas den om först när filstämpel eller storlek ändrats."""
    try:
        st=p.stat();k=(str(p),st.st_size,st.st_mtime_ns,st.st_ctime_ns)
    except OSError:return hashlib.sha256(p.read_bytes()).hexdigest()
    h=_KOD_MINNE.get(k)
    if h is None:
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        for old in [x for x in _KOD_MINNE if x[0]==k[0]]:del _KOD_MINNE[old]
        _KOD_MINNE[k]=h
    return h

def kodnyckel(filer):
    h=hashlib.sha256()
    for p in sorted({Path(os.path.abspath(p)) for p in filer},key=str):
        h.update(str(p).encode('utf-8'));h.update(_innehallshash(p).encode('ascii'))
    return h.hexdigest()

def lokala_moduler(start, mappar):
    """Startfilerna och alla lokala .py i `mappar` som de importerar, transitivt. Läses statiskt (ast),
    så importer inne i funktioner räknas också. Används för att nyckla cachen på all kod som kan påverka ett beslut;
    en fast fillista missade 12 nov 17 moduler (t.ex. dolda_fotter.py, rumsmall.py)."""
    import ast
    mappar = [Path(m).resolve() for m in mappar]
    def hitta(namn):
        for m in mappar:
            f = m / (namn.split('.')[0] + '.py')
            if f.exists(): return f
    sedda, ko = set(), [Path(s).resolve() for s in start]
    while ko:
        f = ko.pop()
        if f in sedda: continue
        sedda.add(f)
        try: trad = ast.parse(f.read_text(encoding='utf-8-sig'))
        except (OSError, SyntaxError, ValueError): continue
        for nod in ast.walk(trad):
            namn = [a.name for a in nod.names] if isinstance(nod, ast.Import) else [nod.module] if isinstance(nod, ast.ImportFrom) and nod.module and nod.level == 0 else []
            for n in namn:
                g = hitta(n)
                if g and g not in sedda: ko.append(g)
    return sorted(sedda, key=str)

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


def hamta_npz(grupp,key):
    """Läser en npz-post; ger dict av arrayer eller None. Nyckeln lagras i filen och prövas."""
    try:
        with np.load(CACHE/grupp/(key+'.npz'),allow_pickle=False) as d:
            if str(d['_nyckel'])!=key:return None
            return {n:d[n] for n in d.files if n!='_nyckel'}
    except (OSError,ValueError,KeyError,EOFError,zipfile.BadZipFile):return None

def spara_npz(grupp,key,data):
    folder=CACHE/grupp;tmp=None
    try:
        folder.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=folder,suffix='.tmp',delete=False) as f:
            tmp=Path(f.name);np.savez(f,_nyckel=np.array(key),**data)
        os.replace(tmp,folder/(key+'.npz'))
    except OSError:pass
    finally:
        if tmp is not None and tmp.exists():tmp.unlink()
