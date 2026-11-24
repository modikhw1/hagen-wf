import json,sys,shutil,hashlib,difflib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
sys.path.insert(0,str(HERE))
from prova import save,log
old=json.loads((P/'kontrakt/ut/golv2/mat_fore/notan_plan.json').read_text(encoding='utf-8'))
new=json.loads((HERE/'notan_dagens_plan.json').read_text(encoding='utf-8'))
print('plan scene/persons',[(s['id'],s['ut'],[(p['id'],p['rorelse']) for p in s['personer']]) for s in new['scener']])
print('old paths',[(s['id'],s['varld'],[p['rorelse'] for p in s['personer']]) for s in old['scener']])
print('utdata',new['utdata'])
print('raw delta',[(r['tagning'],[(s['fil'],s['cam_t']['max_mot_ra'],s['pose']['max_mot_ra']) for s in r['sekvenser']]) for r in json.loads((HERE/'ingest_matning.json').read_text(encoding='utf-8'))])
for label,plan in [('fore',old),('efter',new)]:
    d=HERE/label;d.mkdir(exist_ok=True);save(d/'plan.json',plan)
archive=P/'kontrakt/ut/fore_golv2/scen/3d'
for f in ['ingest/mhr_rig.py','blender/mhr_blender.py']:
    a=(archive/f).read_text(encoding='utf-8').splitlines();b=(P/f).read_text(encoding='utf-8').splitlines()
    print('\n'.join(difflib.unified_diff(a,b,fromfile='fore/'+f,tofile='efter/'+f)))
log('Del 1: nyskriven kopia och dagens metriska läsning har identiska scen-, kropp-, kamera- och objektdata. Full plan skiljer endast filhashar och byggunderlagets filförteckning (extra golv_prov.json); diffarna bevarade. Föreplan vald: ut/golv2/mat_fore/notan_plan.json, framställd med före-GOLV2-kod.',"scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py efter")
