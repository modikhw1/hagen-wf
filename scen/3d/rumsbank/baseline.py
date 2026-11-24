"""Copy eight read-only cached MoGe measurements to the same evaluation format."""
import json,cv2,numpy as np
from pathlib import Path
B=Path(__file__).resolve().parent;R=B.parents[2];cv2.setNumThreads(1)
manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8'));jobs=[]
for job in manifest:
    if not job.get('reference') or job['id'].endswith('_fullrate'):continue
    folder=R/job['reference'];files=sorted((folder/'rum/depth').glob('*.npz'))
    if not files:continue
    frames=[int(p.stem) for p in files];dest=B/'ut/baseline'/job['id'];dest.mkdir(parents=True,exist_ok=True)
    v=np.load(folder/'varld.npz');cap=cv2.VideoCapture(str(R/job['video']));pairs=[]
    for ix,frame in enumerate(job['overlay_frames']):
        nearest=min(range(len(frames)),key=lambda i:abs(frames[i]-frame));p=files[nearest]
        with np.load(p) as d:
            depth=d['depth'];h,w=depth.shape;K=d['intrinsics'].copy();K[0]*=w;K[1]*=h
        nh,nw=518,292;depth=cv2.resize(depth,(nw,nh),interpolation=cv2.INTER_NEAREST);K[0]*=nw/w;K[1]*=nh/h
        pose=np.eye(4);pose[:3,:3]=v['kam_R'][frame];pose[:3,3]=v['kam_C'][frame]
        np.savez_compressed(dest/f'{ix:05d}.npz',depth_z=depth,intrinsics=K,camera_poses=pose,conf=np.isfinite(depth).astype(np.float32))
        cap.set(cv2.CAP_PROP_POS_FRAMES,frame);ok,im=cap.read()
        if not ok:raise RuntimeError(f'{job["id"]} {frame}')
        cv2.imwrite(str(dest/f'{ix:05d}.jpg'),cv2.resize(im,(nw,nh)),[cv2.IMWRITE_JPEG_QUALITY,95])
        pairs.append(dict(source_frame=frame,cached_depth_frame=frames[nearest],cache_path=str(p.relative_to(R))))
    cap.release();j=dict(job);j['frames']=job['overlay_frames'];jobs.append(j)
    (dest/'timing.json').write_text(json.dumps(dict(candidate='baseline',metric=True,frames=len(pairs),gpu_s_per_frame=None,source='Existing MoGe2 cache + varld.npz; NO inference or ingestion performed',cache_mapping=pairs),ensure_ascii=False,indent=2),encoding='utf-8');print(job['id'],flush=True)
(B/'baseline_manifest.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
