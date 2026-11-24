"""Rätta den avlästa enradiga inledningstexten utan ny 3D-rendering."""
import json
import shutil
import sys
import time
from pathlib import Path
from textarbete import backup,jsonfil

HIT=Path(__file__).resolve().parent
ROT=HIT.parents[2]


def kalla():
    from textreferens import las
    f=HIT/'ut/b/kalla.json';k=json.loads(f.read_text(encoding='utf-8'))
    video=(f.parent/k['klipp']['video']['sokvag']).resolve()
    texts,log=las(k,video)
    old=[t for t in k['semantik']['skarmtext'] if t['scen']=='s1']
    assert len(texts)==len(old)==1
    texts[0]['id']=old[0]['id']
    k['semantik']['skarmtext']=texts+[t for t in k['semantik']['skarmtext'] if t['scen']!='s1']
    jsonfil(f,k);jsonfil(HIT/'ut/b/textmatning_forsta.json',log)
    print('källtext',[(t['text'],t['start_s'],t['slut_s']) for t in texts],flush=True)


def planer_och_bilder():
    from kompilera import kompilera
    from trohet import rapport
    from skarmtext import kompositera
    from kor_klipp import blad
    for folder in ['tom2','redigerad2']:
        d=HIT/f'ut/b/{folder}';old=json.loads((d/'plan.json').read_text(encoding='utf-8'))
        regi=d/'regi.json' if folder=='tom2' else HIT/'ut/b/regi_redigerad.json'
        start=time.perf_counter();p=kompilera(HIT/'ut/b/kalla.json',regi)
        for key in ['personer','renderkamera','matkamera','tidskarta','kallrutor']:
            assert old[key]==p[key],key
        jsonfil(d/'plan.json',p)
        for f in [d/'kvalitet.md',d/'plan_trohet.md',d/'plan_trohet.json']:backup(f)
        rapport(p,d/'plan.json')
        archive=(HIT/f'ut/fore_text/b_{folder}_fore_enrad').resolve()
        assert not archive.exists() and archive.is_relative_to(ROT.resolve())
        archive.mkdir()
        for name in ['komposit','textlager']:
            source=(d/name).resolve();assert source.is_relative_to(ROT.resolve())
            for f in source.rglob('*'):
                if f.is_file():backup(f)
            shutil.move(str(source),str(archive/name))
        for name in ['film.mp4','tider.json']:backup(d/name);shutil.copy2(d/name,archive/name)
        for f in (d/'blad').glob('*.png'):backup(f)
        images=kompositera(p,d);k=json.loads((HIT/'ut/b/kalla.json').read_text(encoding='utf-8'))
        blad(p,(HIT/'ut/b'/k['klipp']['video']['sokvag']).resolve(),d,images)
        times=json.loads((d/'tider.json').read_text(encoding='utf-8'));times['avlast_enrad_2d']=round(time.perf_counter()-start,2)
        jsonfil(d/'tider.json',times);print(folder,times['avlast_enrad_2d'],flush=True)


if __name__=='__main__':
    kalla()
    if '--kalla' not in sys.argv:planer_och_bilder()
