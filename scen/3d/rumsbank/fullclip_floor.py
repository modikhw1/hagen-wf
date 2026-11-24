"""Within-shot floor stability inside uncut notan; read at most 16 depths per case."""
import os,json
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import numpy as np
import evaluate as e
B=Path(__file__).resolve().parent;R=B.parents[2]
manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8'))
masks=np.load(R/'scen/3d/ingest/ut/notan-tagningar/S4/masker.npy',mmap_mode='r')
for candidate in ['mapanything','da3','vipe']:
    path=B/f'{candidate}_metrics.json';rows=json.loads(path.read_text(encoding='utf-8'))
    for row in rows:
        if row['shot'] not in ['notan_uncut','notan_fullrate'] or row['status']!='ran':continue
        job=next(j for j in manifest if j['id']==row['shot']);indices=row['timing'].get('indices',list(range(len(job['frames']))))
        chosen=[(i,job['frames'][ind]) for i,ind in enumerate(indices) if 171<=job['frames'][ind]<=255]
        if len(chosen)>16:chosen=[chosen[i] for i in np.rint(np.linspace(0,len(chosen)-1,16)).astype(int)]
        found=[]
        for index,frame in chosen:
            d=e.load(B/'ut'/candidate/row['shot']/f'{index:05d}.npz');d['camera_poses'][:3,3]-=np.array(row['evaluation_origin'])
            mk=e.crop_mask(masks[frame-171]>0,d['depth_z'].shape);p=e.surface(d,e.ROIS['notan_S4']['floor'],mk)
            if p:found.append((frame,p))
        if len(found)<2:continue
        ns=np.array([p['normal'] for _,p in found]);off=np.array([p['offset'] for _,p in found]);sign=np.where(ns@ns[0]>=0,1.,-1.);ns*=sign[:,None];off*=sign
        n=np.median(ns,0);n/=np.linalg.norm(n);angles=np.degrees(np.arccos(np.clip(ns@n,-1,1)))
        row['floor']=dict(frames=len(found),temporal_stability_verified=True,normal_variation_deg=e.stats(angles),offset_range_cm=float(np.ptp(off)*100),offset_mad_cm=float(np.median(np.abs(off-np.median(off)))*100),surface_rms_cm=e.stats([p['rms_m']*100 for _,p in found]),per_frame=[dict(frame=f,normal=p['normal'].tolist(),offset=p['offset'],rms_m=p['rms_m'],support_fraction=p['support_fraction']) for f,p in found],note='Within-shot S4 floor segment (source 171..255) inside uncut clip, at most 16 equally spaced available predictions. This does NOT establish consistency across camera stations; S1 floor is invisible.')
        e.write(B/'ut'/candidate/row['shot']/'metrics.json',row);print(candidate,row['shot'],'floor cm',round(row['floor']['offset_range_cm'],2),flush=True)
    e.write(path,rows)
