"""Kör slutkontroller sekventiellt från projektroten, utan Blender."""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

H = Path(__file__).resolve().parents[1]
ROOT = H.parents[2]
OUT = H / 'ut/aterupptagning'
stages = [
    ('kontroll_bar', [str(H/'kontrollera.py')]),
    ('kontroll_notan', [str(H/'kontrollera.py'), 'exempel/notan']),
    ('unittest', ['-m','unittest','test_flode','test_rumsmall','test_regler','test_text_disk','test_kroppmatt','test_props','test_handelser']),
    ('semantik', [str(H/'semantik/test_semantik.py')]),
    ('bro', [str(H/'bro/test_bro.py')]),
    ('rum', [str(H.parent/'ingest/test_rum.py')]),
]
tag = sys.argv[1] if len(sys.argv)>1 else 'prov'
log = OUT/(tag+'.log'); summary = OUT/(tag+'.json')
if log.exists() or summary.exists(): raise FileExistsError(log)
env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONPATH=str(H), OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4', MKL_NUM_THREADS='4')
results = []
for name, args in stages:
    start = time.perf_counter()
    print(name, 'start', flush=True)
    result = subprocess.run([sys.executable,'-B',*args],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output = result.stdout.decode('utf-8',errors='replace')
    with log.open('a',encoding='utf-8') as f:
        f.write('\n== '+name+'\n'+output)
    counts = re.findall(r'Ran (\d+) tests? in', output)
    row = dict(prov=name,kommando=[str(Path(sys.executable).relative_to(ROOT)),*args],exit=result.returncode,
               antal=int(counts[-1]) if counts else None,sek=round(time.perf_counter()-start,2))
    results.append(row)
    summary.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(row,flush=True)
    if result.returncode:
        print(output[-9000:],flush=True)
        sys.exit(result.returncode)
