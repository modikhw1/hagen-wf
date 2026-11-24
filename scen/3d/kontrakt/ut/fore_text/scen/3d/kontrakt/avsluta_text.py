"""Avslutande 2D-korrigering och seriella kontroller efter alla renderingar."""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from textarbete import backup,jsonfil

HIT=Path(__file__).resolve().parent
ROT=HIT.parents[2]

def radfix():
    from skarmtext import kompositera
    from kor_klipp import blad
    sys.path.insert(0,str(HIT/'semantik'))
    from sem_gemensamt import KLIPP
    d=HIT/'ut/b/tom2';archive=HIT/'ut/fore_text/b_fore_radfix'
    archive.mkdir(exist_ok=False)
    for name in ['komposit','textlager']:
        source=(d/name).resolve();target=(archive/name).resolve()
        assert source.is_relative_to(ROT.resolve()) and target.is_relative_to(ROT.resolve())
        for p in source.rglob('*'):
            if p.is_file():backup(p)
        shutil.move(str(source),str(target))
    for name in ['film.mp4','tider.json']:
        backup(d/name);shutil.copy2(d/name,archive/name)
    for p in (d/'blad').glob('*.png'):backup(p)
    p=json.loads((d/'plan.json').read_text(encoding='utf-8'))
    start=time.perf_counter();images=kompositera(p,d)
    blad(p,ROT/'scen/klipp'/KLIPP['b']['video'],d,images)
    times=json.loads((d/'tider.json').read_text(encoding='utf-8'));times['radfix_2d']=round(time.perf_counter()-start,2)
    jsonfil(d/'tider.json',times);print('radfix',times['radfix_2d'],flush=True)

if __name__=='__main__':
    results=json.loads((HIT/'ut/fore_text/renderingar.json').read_text(encoding='utf-8'))
    assert len(results)==5 and all(x['exit']==0 for x in results)
    radfix()
    for name in ['verifiera_text.py','regression_text.py']:
        print('start',name,flush=True)
        subprocess.run([sys.executable,'-B','-u',str(HIT/name)],cwd=ROT,check=True)
