"""Reproducerbart lokalt GOLV2-prov. Inga nätanrop eller inferens."""
import sys, json, shutil, hashlib, copy, datetime, argparse
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
P=ROOT/'scen/3d'; OUT=Path(__file__).resolve().parent
COPY=P/'kontrakt/ut/golv2_ingestprov'
LOG=P/'kontrakt/GOLV2-BLENDER-LOGG.md'
sys.dont_write_bytecode=True
sys.path[:0]=[str(P/'ingest'),str(P/'kontrakt')]
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def log(s,nxt):
    if LOG.exists() and not (P/'kontrakt/ut/fore_golv2_blender/scen/3d/kontrakt/GOLV2-BLENDER-LOGG.md').exists():
        b=P/'kontrakt/ut/fore_golv2_blender/scen/3d/kontrakt/GOLV2-BLENDER-LOGG.md';b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(LOG,b)
    with LOG.open('a',encoding='utf-8',newline='\n') as f:
        f.write(f'\n## {datetime.datetime.now().isoformat(timespec="seconds")}\n{s}\n\nNästa kommando (projektroten):\n```powershell\n$env:PYTHONIOENCODING=\'utf-8\'\n{nxt}\n```\n')
CMD='scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py '
SOURCES={'notan':P/'kontrakt/ut/notan/kalla_handelser.json','bar':P/'kontrakt/ut/bar/kalla.json'}
def refs(o):
    if isinstance(o,dict):
        if isinstance(o.get('sokvag'),str):yield o
        for v in o.values():yield from refs(v)
    elif isinstance(o,list):
        for v in o:yield from refs(v)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name, copied=False):
    src=SOURCES[name];k=json.loads(src.read_text(encoding='utf-8'))
    for r in refs(k):
        path=(src.parent/r['sokvag']).resolve()
        if copied and path.is_relative_to(P/'ingest/ut'):
            dest=COPY/'data'/path.relative_to(P/'ingest/ut')
            if dest.exists():path=dest
        r['sokvag']=str(path)
        if 'sha256' in r and path.is_file():r['sha256']=sha(path)
    dest=COPY/f'{name}_{"ny" if copied else "dagens"}_kalla.json';save(dest,k)
    return dest,k
def inventory():
    for name,src in SOURCES.items():
        k=json.loads(src.read_text(encoding='utf-8'))
        print(name,'revision',k['revision'],'paths',len(list(refs(k))))
        folders=sorted({(src.parent/r['spar_metrisk']['sokvag']).resolve().parent for r in k['matning']['kameror']})
        for d in folders:
            files=list(d.glob('*.*'))+list((d/'kropp').glob('*/*.npz'))
            print(d,len(files),round(sum(f.stat().st_size for f in files if f.is_file())/1e6,1),'MB')
    for phase in ['mat_fore','mat_efter','fore']:
        d=P/'kontrakt/ut/golv2'/phase
        print('plans',phase,[f.name for f in d.glob('*plan.json')])
    log('Underlag och ordinarie plan → ingest/mhr_rig.py lästa. Blender 5.2 finns enligt ingest_klipp.py. Första filsökningen gick av misstag rekursivt in i ut/; ingen fortsatt sådan sökning. Inga original ändrade.',CMD+'ingest')
def ingest():
    from ingest_klipp import steg_golv
    from kontakt import steg_kontakt
    from metrisk import las
    rows=[];hashes={}
    for name,src in SOURCES.items():
        k=json.loads(src.read_text(encoding='utf-8'))
        folders=sorted({(src.parent/r['spar_metrisk']['sokvag']).resolve().parent for r in k['matning']['kameror']})
        for d in folders:
            dest=COPY/'data'/d.relative_to(P/'ingest/ut');dest.mkdir(parents=True,exist_ok=True)
            files=[f for f in d.iterdir() if f.is_file() and f.suffix in ('.json','.npz','.npy')]
            files+=list((d/'kropp').glob('*/*.npz'))
            for f in files:
                target=dest/f.relative_to(d);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
                hashes[str(f)]=sha(f)
            before={f.name:dict(np.load(f)) for f in d.glob('sekvens_*.npz')}
            expected={f.name:las(f) for f in d.glob('sekvens_*.npz')}
            m=json.loads((dest/'meta.json').read_text(encoding='utf-8'))
            g=steg_golv(dest,m);save(dest/'golv_prov.json',g)
            after_g={f.name:dict(np.load(f)) for f in dest.glob('sekvens_*.npz')}
            c=steg_kontakt(dest,m)
            r=dict(klipp=name,tagning=d.name,golv_h=g['golv_h'],status=g['status'],sekvenser=[])
            for f in dest.glob('sekvens_*.npz'):
                got=dict(np.load(f));a=before[f.name];e=expected[f.name]
                item=dict(fil=f.name,golv_version=int(got['golv_version']))
                for key in ('cam_t','pose'):
                    item[key]=dict(max_mot_ra=float(np.max(np.abs(got[key]-a[key]))),
                        max_mot_metrisk=float(np.max(np.abs(got[key]-e[key]))),
                        exakt_mot_metrisk=bool(np.array_equal(got[key],e[key])),
                        kontakt_exakt_orord=bool(np.array_equal(got[key],after_g[f.name][key])))
                r['sekvenser'].append(item)
            r['varld_version']=int(np.load(dest/'varld.npz')['golv_version']);rows.append(r)
            save(OUT/'ingest_matning.json',rows);save(OUT/'original_hashar.json',hashes)
            print(name,d.name,'OK',flush=True)
            log(f'Golv och kontakt färdiga på kopia: {name}/{d.name}. Mätvärden sparade i blender/gen/golv2/ingest_matning.json. Original kopierade, ej skrivna.',CMD+'ingest' if len(rows)<8 else CMD+'compile')
    # Alla manifestpekare till filer som inte behövts av stegen får kopieras separat.
    for name in SOURCES:
        src=SOURCES[name];k=json.loads(src.read_text(encoding='utf-8'))
        for r in refs(k):
            f=(src.parent/r['sokvag']).resolve()
            if f.is_relative_to(P/'ingest/ut') and f.is_file():
                dst=COPY/'data'/f.relative_to(P/'ingest/ut')
                if not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst)
        manifest(name);manifest(name,True)
    assert all(sha(Path(f))==h for f,h in hashes.items())
    log('Del 1 steg körda på sju notantagningar samt bar. SHA256 för samtliga kopierade original oförändrade. Inga bankfiler skrivna.',CMD+'compile')
def differences(a,b,path=''):
    if type(a)!=type(b):return [(path,a,b)]
    if isinstance(a,dict):
        r=[]
        for k in sorted(a.keys()|b.keys()):r+=differences(a.get(k),b.get(k),path+'/'+k)
        return r
    if isinstance(a,list):
        if len(a)!=len(b):return [(path+'/length',len(a),len(b))]
        return [r for i,(x,y) in enumerate(zip(a,b)) for r in differences(x,y,path+'/'+str(i))]
    return [] if a==b else [(path,a,b)]
def normalize(o):
    if isinstance(o,dict):return {k:normalize(v) for k,v in o.items()}
    if isinstance(o,list):return [normalize(x) for x in o]
    if isinstance(o,str):
        o=o.replace(str(COPY/'data'),str(P/'ingest/ut'))
        for name in SOURCES:
            for phase in ['ny','dagens']:o=o.replace(str(COPY/f'{name}_{phase}_kalla.json'),str(SOURCES[name]))
    return o
def compile_():
    import kompilera
    result={}
    base=json.loads((ROOT/'forvarld/varld/pipeline/base-regi.json').read_text(encoding='utf-8'))
    for name in SOURCES:
        plans=[]
        for copied in (False,True):
            f,k=manifest(name,copied);r=copy.deepcopy(base);r['edits']=[]
            r['kalla']=dict(klipp_id=k['klipp']['id'],sha256=k['klipp']['sha256'],revision=k['revision']);r['ramar']['bevara_beats']=[]
            rf=COPY/f'{name}_regi.json';save(rf,r)
            plan=kompilera.kompilera(f,rf,snabb=True)
            save(OUT/f'{name}_{"ny" if copied else "dagens"}_plan.json',plan);plans.append(plan)
        diff=differences(normalize(plans[0]),normalize(plans[1]));save(OUT/f'{name}_plandiff.json',diff)
        numeric=[abs(a-b) for _,a,b in diff if isinstance(a,(int,float)) and isinstance(b,(int,float))]
        result[name]=dict(skillnader=len(diff),max_numerisk=max(numeric,default=0),exempel=diff[:20])
        print(name,result[name],flush=True)
    save(OUT/'planjamforelse.json',result)
    log('Båda kompileringsvägarna körda. Fulla normaliserade plandiffar finns i blender/gen/golv2/*_plandiff.json. Absoluta kopiesökvägar normaliserade; inga numeriska fält undantagna.',CMD+'hashcheck')
def hashcheck():
    hashes=json.loads((OUT/'original_hashar.json').read_text(encoding='utf-8'))
    changed=[f for f,h in hashes.items() if sha(Path(f))!=h]
    save(OUT/'original_kontroll.json',dict(antal=len(hashes),andrade=changed));print('original',len(hashes),'changed',changed)
    assert not changed
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('steg',choices=['inventory','ingest','compile','hashcheck']);x=a.parse_args()
    {'inventory':inventory,'ingest':ingest,'compile':compile_,'hashcheck':hashcheck}[x.steg]()
