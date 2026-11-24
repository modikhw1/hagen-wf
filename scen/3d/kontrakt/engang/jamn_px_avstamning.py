"""Stäm av vald metod mot de redan byggda filmernas lagrade kvalitetsvärden."""
import json
from pathlib import Path
H=Path(__file__).resolve().parents[1]
table=json.loads((H/'ut/prop_granskning/metoder_korrigerade.json').read_text(encoding='utf-8'))
rows=[]
for key,data in table.items():
    folder,person=key.rsplit(':',1);parts=folder.replace('\\','/').split('/');shot=parts[-1].lower();ingest=parts[-2]
    clip='b' if ingest.startswith('b-') else 'a' if ingest.startswith('a-') else 'kenny' if ingest.startswith('kand-') else 'notan'
    run='jamn_tom' if clip=='notan' else 'tom3';p=json.loads((H/'ut'/clip/run/'plan.json').read_text(encoding='utf-8'))
    scene=next(x for x in p['scener'] if x['id']==shot);pm=next(x for x in scene['personer'] if x.get('ingest_id')==person)
    movie=next(x for x in p['kvalitet']['bildtrohet']['personer'] if x['scen']==shot and x['person']==pm['id'])
    method=next(x for x in data['rader'] if x['metod']=='ror fc4 k2 d2 T-ny')
    rows.append(dict(klipp=clip,scen=shot,person=pm['id'],tabell=[method['px_median'],method['px_p90']],film=[movie['median_px'],movie['p90_px']],delta=[movie['median_px']-method['px_median'],movie['p90_px']-method['px_p90']]))
path=H/'ut/prop_granskning/px_avstamning.json'
if path.exists():raise FileExistsError(path)
path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(rows,ensure_ascii=False,indent=2))
