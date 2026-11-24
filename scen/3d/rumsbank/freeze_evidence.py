"""Hash only the reference evidence actually used; bounded 1 MB reads."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;R=B.parents[2]
jobs=json.loads((B/'manifest.json').read_text(encoding='utf-8'));paths=set()
for j in jobs:
    if j.get('reference'):
        d=R/j['reference'];paths.update(d/name for name in ['meta.json','kamera.json','varld.npz','masker.npy','rum.json'])
    if j.get('video'):paths.add(R/j['video'])
for p in (R/'scen/3d/ingest/ut/notan-tagningar').glob('S*'):
    if p.is_dir():paths.update(p/name for name in ['meta.json','masker.npy'])
for p in B.glob('*_metrics.json'):
    try:rows=json.loads(p.read_text(encoding='utf-8'))
    except ValueError:continue
    for row in rows:
        if row.get('status')!='ran':continue
        j=next(j for j in jobs if j['id']==row['shot']);folder=R/j['reference'] if j.get('reference') else None
        if folder:
            for sample in row.get('scale',{}).get('body_samples',[]):paths.add(folder/'kropp'/sample['person']/f'{sample["frame"]:04d}.npz')
        for item in row.get('timing',{}).get('cache_mapping',[]):paths.add(R/item['cache_path'])
out=[]
for p in sorted(paths):
    if not p.is_file():continue
    h=hashlib.sha256()
    with p.open('rb') as file:
        for chunk in iter(lambda:file.read(1024*1024),b''):h.update(chunk)
    s=p.stat();out.append(dict(path=str(p.relative_to(R)),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=h.hexdigest()))
(B/'evidence_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('hashed reference files:',len(out))
