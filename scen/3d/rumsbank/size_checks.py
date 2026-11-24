"""Independent object-size priors. No fitted global rescaling, no ground-truth claim."""
from pathlib import Path
import numpy as np,json
B=Path(__file__).resolve().parent
out={}
for candidate in ['baseline','mapanything','da3','vipe']:
    folder=B/'ut'/candidate/'notan_S4';values=[]
    for p in sorted(folder.glob('*.npz')):
        with np.load(p) as d:
            D=d['depth_z'].squeeze();K=d['intrinsics'].squeeze();h,w=D.shape
            uv=np.array([[.805*w,.420*h],[.805*w,.615*h]])
            z=D[uv[:,1].astype(int),uv[:,0].astype(int)]
            xyz=np.c_[(uv[:,0]-K[0,2])/K[0,0]*z,(uv[:,1]-K[1,2])/K[1,1]*z,z]
            height=float(np.linalg.norm(xyz[1]-xyz[0]))
            if np.isfinite(height):values.append(dict(raw_output=p.name,height_m=height))
    if values:
        a=np.array([v['height_m'] for v in values]);out[candidate]=dict(shot='notan_S4',object='black rear door',image_points_normalized=[[.805,.420],[.805,.615]],height_m=float(np.median(a)),height_min_max_m=[float(a.min()),float(a.max())],assumed_height_m=2.0,deviation_from_prior_pct=float(100*(np.median(a)/2-1)),note='2.0 m is a door-height prior, not a surveyed measurement. Endpoint occlusion and pixel choice add uncertainty.',per_frame=values)
(B/'size_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:{a:v for a,v in d.items() if a!='per_frame'} for k,d in out.items()},ensure_ascii=False,indent=2))
