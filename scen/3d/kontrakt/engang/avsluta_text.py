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

def radfix(folder):
    from skarmtext import kompositera
    from kor_klipp import blad
    sys.path.insert(0,str(HIT/'semantik'))
    from sem_gemensamt import KLIPP
    d=HIT/f'ut/b/{folder}';archive=HIT/f'ut/fore_text/b_{folder}_fore_radfix'
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
    # Måndiskens synliga hyllor får också mallens fiktiva färg.
    d=(HIT/'ut/b/redigerad2').resolve();target=(HIT/'ut/fore_text/b_redigerad2_fore_farg').resolve()
    assert d.is_relative_to(ROT.resolve()) and target.is_relative_to(ROT.resolve()) and not target.exists()
    for path in d.rglob('*'):
        if path.is_file():backup(path)
    shutil.move(str(d),str(target))
    row=next(x for x in results if x['klipp']=='b' and x['mapp']=='redigerad2')
    start=time.perf_counter();print('start b redigerad2 färg',flush=True)
    with (HIT/'ut/fore_text/render_b_redigerad2_farg.log').open('w',encoding='utf-8') as stream:
        subprocess.run(row['kommando'],cwd=ROT,stdout=stream,stderr=subprocess.STDOUT,check=True)
    row['forsta_render_sekunder']=row['sekunder'];row['sekunder']=round(time.perf_counter()-start,2)
    jsonfil(HIT/'ut/fore_text/renderingar.json',results);print('klart b redigerad2 färg',row['sekunder'],flush=True)
    radfix('tom2')
    for name in ['textgranska.py','verifiera_text.py','regression_text.py']:
        print('start',name,flush=True)
        subprocess.run([sys.executable,'-B','-u',str(HIT/name)],cwd=ROT,check=True)
