"""Starta egna bakgrundsprocesser; inga ingest-steg eller externa tjänster anropas."""
import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

HIT=Path(__file__).resolve().parent
UT=HIT/'ut/bar'; INGEST=HIT.parent/'ingest'
# Samma installationssökväg som ingest_klipp.py; importera inte dess beroenden.
BLENDER=re.search(r"BLENDER = r'([^']+)'",(INGEST/'ingest_klipp.py').read_text(encoding='utf-8')).group(1)


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


if __name__=='__main__':
    # Skydda hela befintliga ingestmappen, inklusive tidsstämplar. Detta läser bara.
    fore={str(p.relative_to(INGEST/'ut/bar')):[p.stat().st_size,p.stat().st_mtime_ns] for p in (INGEST/'ut/bar').rglob('*') if p.is_file()}
    (UT/'ingest_fore.json').write_text(json.dumps(fore,indent=2),encoding='utf-8')
    for namn in ('meta.json','varld.npz','rum.json','sekvens_1.npz','sekvens_2.npz'):
        mal=UT/'original'/namn
        if not mal.exists(): shutil.copy2(INGEST/'ut/bar'/namn,mal)
    resultat=[]
    for lage in ('original','utan_plan','plan'):
        if (UT/lage/'rapport.json').exists(): raise SystemExit('Befintligt verifieringsresultat: '+lage)
        cmd=[BLENDER,'-b','--factory-startup','--python-exit-code','1','--python',str(HIT/'verifiera_blender.py'),'--',lage]
        start=time.perf_counter()
        try:
            with (UT/(lage+'.log')).open('w',encoding='utf-8') as log:
                r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            res=dict(kommando=subprocess.list2cmdline(cmd),exit=r.returncode,wall_s=time.perf_counter()-start)
        except OSError as e: res=dict(kommando=subprocess.list2cmdline(cmd),fel=repr(e),wall_s=time.perf_counter()-start)
        resultat.append(res); (UT/'korningar.json').write_text(json.dumps(resultat,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(res,ensure_ascii=False),flush=True)
        if res.get('exit')!=0: break
    efter={str(p.relative_to(INGEST/'ut/bar')):[p.stat().st_size,p.stat().st_mtime_ns] for p in (INGEST/'ut/bar').rglob('*') if p.is_file()}
    assert fore==efter, 'Ingestmappen ändrades under verifieringen'
    print('Ingest: samma filer, storlekar och tidsstämplar.',flush=True)
