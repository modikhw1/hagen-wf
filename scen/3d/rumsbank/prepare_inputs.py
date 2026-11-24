"""Decode only; no model, no existing files changed. All inference is remote."""
import hashlib, json
from pathlib import Path
import cv2
import numpy as np

BANK=Path(__file__).resolve().parent
ROOT=BANK.parents[2]
BASE=ROOT/'scen/3d/ingest/ut'

def main():
    cv2.setNumThreads(1)
    specs=[('notan_S1','notan-tagningar','S1'),('notan_S4','notan-tagningar','S4'),
           ('b_S5','b-tilltal-ravara-tagningar','S5'),('b_closeup','b-tilltal-ravara-tagningar','S9'),
           ('pool','biljard',None),('kenny_S2','kand-kennysgelato-tagningar','S2')]
    jobs=[]
    for name,group,shot in specs:
        folder=BASE/group/(shot or '')
        video=(BASE/group/'klipp'/f'{shot}.mp4') if shot else ROOT/'scen/klipp/kand-interpooluppsala-7599643065644551446.mp4'
        jobs.append(dict(id=name,video=str(video.relative_to(ROOT)),reference=str(folder.relative_to(ROOT))))
    jobs.append(dict(id='notan_uncut',video='scen/klipp/d-dialog-notan.mp4',reference=None))
    for job in jobs:
        cap=cv2.VideoCapture(str(ROOT/job['video'])); n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        job.update(source_frames=n,fps=cap.get(cv2.CAP_PROP_FPS),width=int(cap.get(3)),height=int(cap.get(4)))
        overlay=np.rint(np.linspace(0,n-1,8)).astype(int).tolist()
        frames=list(range(n)) if job['id'] not in ['pool','notan_uncut'] else sorted(set(np.rint(np.linspace(0,n-1,74 if job['id']=='pool' else 40)).astype(int).tolist()+overlay))
        dest=BANK/'inputs'/job['id'];dest.mkdir(parents=True,exist_ok=True)
        wanted=set(frames)
        for i in range(n):
            ok,frame=cap.read()
            if not ok:raise RuntimeError(f'{job["id"]}: decode {i}')
            if i not in wanted:continue
            h,w=frame.shape[:2];scale=min(1.,768/h);frame=cv2.resize(frame,(round(w*scale),round(h*scale)),interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(dest/f'{i:05d}.jpg'),frame,[cv2.IMWRITE_JPEG_QUALITY,96])
        cap.release()
        job.update(frames=frames,overlay_frames=overlay,input_dir=str(dest.relative_to(BANK)),input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.glob('*.jpg'))})
        print(job['id'],n,'sampled',len(frames),flush=True)
    # Test joint reconstruction of disjoint camera stations without requiring cut tracking.
    joint=dict(id='notan_joint_S1_S4',video=None,reference=None,frames=[],overlay_frames=list(range(16)),fps=None,source_frames=158,inputs=[])
    for name in ['notan_S1','notan_S4']:
        job=next(j for j in jobs if j['id']==name)
        joint['inputs'] += [dict(shot=name,frame=i,path=f'inputs/{name}/{i:05d}.jpg') for i in job['overlay_frames']]
    joint['frames']=list(range(len(joint['inputs'])))
    jobs.append(joint)
    (BANK/'manifest.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
    # Contact sheet used to choose and verify close-up, not a geometry overlay.
    tiles=[]
    for job in jobs[:-1]:
        p=BANK/job['input_dir']/f'{job["frames"][0]:05d}.jpg';im=cv2.imread(str(p));im=cv2.resize(im,(180,320));cv2.putText(im,job['id'],(5,20),cv2.FONT_HERSHEY_SIMPLEX,.45,(0,255,255),1);tiles.append(im)
    cv2.imwrite(str(BANK/'inputs/contact.jpg'),np.concatenate(tiles,axis=1))

if __name__=='__main__':main()
