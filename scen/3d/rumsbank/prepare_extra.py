"""Full-rate controls for temporal sampling and black-frame sensitivity."""
from pathlib import Path
import cv2,json,hashlib,numpy as np
B=Path(__file__).resolve().parent;R=B.parents[2]
jobs=json.loads((B/'manifest.json').read_text(encoding='utf-8'));cv2.setNumThreads(1)
for source,name in [('notan_uncut','notan_fullrate'),('pool','pool_fullrate')]:
    if any(j['id']==name for j in jobs):continue
    job=dict(next(j for j in jobs if j['id']==source));job.update(id=name,frames=list(range(job['source_frames'])),input_dir=f'inputs/{name}')
    d=B/job['input_dir'];d.mkdir(exist_ok=True);cap=cv2.VideoCapture(str(R/job['video']));hashes={}
    for i in job['frames']:
        ok,im=cap.read()
        if not ok:raise RuntimeError(f'{name} {i}')
        h,w=im.shape[:2];im=cv2.resize(im,(round(w*768/h),768),interpolation=cv2.INTER_AREA);p=d/f'{i:05d}.jpg';cv2.imwrite(str(p),im,[cv2.IMWRITE_JPEG_QUALITY,96]);hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    cap.release();job['input_sha256']=hashes;jobs.append(job);print(name,len(job['frames']),flush=True)
if not any(j['id']=='pool_visible' for j in jobs):
    pool=next(j for j in jobs if j['id']=='pool_fullrate');indices=[]
    for i in pool['frames']:
        im=cv2.imread(str(B/pool['input_dir']/f'{i:05d}.jpg'))
        if np.mean(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)>12)>.15:indices.append(i)
    job=dict(pool);job.update(id='pool_visible',frames=indices,overlay_frames=[indices[i] for i in np.rint(np.linspace(0,len(indices)-1,8)).astype(int)],note='Black-frame ablation; only visible source frames sent to model');jobs.append(job)
    print('pool_visible',len(indices),flush=True)
if not any(j['id']=='pool_core' for j in jobs):
    pool=next(j for j in jobs if j['id']=='pool_fullrate');indices=list(range(40,351));job=dict(pool)
    job.update(id='pool_core',frames=indices,overlay_frames=np.rint(np.linspace(40,350,8)).astype(int).tolist(),note='Exposure control: frames 40..350 only, excluding black frames AND both fades, selected from source exposure before inference')
    jobs.append(job);print('pool_core',len(indices),flush=True)
(B/'manifest.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
