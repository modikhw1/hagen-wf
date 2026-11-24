"""Recompute only eight-frame background comparisons; avoids full depth loading."""
import json,os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import numpy as np,cv2
import evaluate as e
B=Path(__file__).resolve().parent
for candidate in ['baseline','mapanything','da3','vipe']:
    mp=B/f'{candidate}_metrics.json'
    if not mp.exists():continue
    rows=json.loads(mp.read_text(encoding='utf-8'));manifest=json.loads((B/('baseline_manifest.json' if candidate=='baseline' else 'manifest.json')).read_text(encoding='utf-8'))
    for row in rows:
        if row.get('status')!='ran':continue
        job=next(j for j in manifest if j['id']==row['shot']);dest=B/'ut'/candidate/row['shot'];indices=row['timing'].get('indices',list(range(len(job['frames']))))
        chosen=[i for i,ind in enumerate(indices) if job['frames'][ind] in job['overlay_frames']]
        ds=[None]*len(indices);images=[None]*len(indices);valid=np.zeros(len(indices),bool)
        for i in chosen:
            ds[i]=e.load(dest/f'{i:05d}.npz');images[i]=cv2.imread(str(dest/f'{i:05d}.jpg'));valid[i]=np.mean(cv2.cvtColor(images[i],cv2.COLOR_BGR2GRAY)>12)>.15
        row['background_reprojection']=e.background_reprojection(ds,images,indices,chosen,job,valid)
        e.write(dest/'metrics.json',row)
    e.write(mp,rows)
    print(candidate,'background comparisons refreshed',flush=True)
