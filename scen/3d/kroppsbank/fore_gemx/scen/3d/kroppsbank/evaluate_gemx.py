"""GEM-X measurements on saved arrays only; no torch or local model execution.

Uses the same mask rasterization and metrics as evaluate.py. Baselines are
reused from disk. Anatomical joint correspondence is not a rig conversion.
"""
import json
from pathlib import Path
import cv2
import numpy as np
import evaluate as E

ROOT = Path(__file__).resolve().parent
MAP = {'root':'Hips','l_upleg':'LeftLeg','r_upleg':'RightLeg',
       'l_lowleg':'LeftShin','r_lowleg':'RightShin','l_foot':'LeftFoot','r_foot':'RightFoot',
       'c_neck':'Neck1','c_head':'Head','l_uparm':'LeftArm','r_uparm':'RightArm',
       'l_lowarm':'LeftForeArm','r_lowarm':'RightForeArm','l_wrist':'LeftHand','r_wrist':'RightHand'}
EDGES = [('root','l_upleg'),('root','r_upleg'),('l_upleg','l_lowleg'),('r_upleg','r_lowleg'),
         ('l_lowleg','l_foot'),('r_lowleg','r_foot'),('root','c_neck'),('c_neck','c_head'),
         ('c_neck','l_uparm'),('c_neck','r_uparm'),('l_uparm','l_lowarm'),('r_uparm','r_lowarm'),
         ('l_lowarm','l_wrist'),('r_lowarm','r_wrist')]

def measure(entry, variant):
    shot = ROOT/'ut/gemx'/entry['id']
    folder = Path(entry['folder'])
    n,w,h = (entry['meta'][k] for k in ['N','bredd','hojd'])
    masks=np.load(folder/'masker.npy',mmap_mode='r'); mh,mw=masks.shape[1:]
    boxes=E.read_json(folder/'personer.json')
    data={}; samples={}; xs={}; hidden={}; mapping={}
    for pid in entry['pids']:
        names=[p.split('/')[-1] for p in E.read_json(shot/pid/'joint_names.json')]
        assert len(names)==77
        indices=[names.index(MAP[x]) for x in E.BODY_NAMES]
        mapping={x:{'mhr':E.IX[x],'soma':names.index(y),'soma_name':y} for x,y in MAP.items()}
        d=dict(np.load(shot/pid/f'{variant}_joints.npz'))
        assert d['camera_m'].shape==(n,77,3)
        x=np.full((n,127,3),np.nan)
        x[:,E.BODY]=100*d['camera_m'][:,indices]
        x[~d['observed'].astype(bool)]=np.nan
        data[pid]=d; xs[pid]=x; samples[pid]=[]
        with np.load(folder/f'sekvens_{pid}.npz') as s:
            hidden[pid]=s['inom'].astype(bool)&~s['ben_synliga'].astype(bool)
    selected=set(np.linspace(0,n-1,8).round().astype(int))
    tiles=[]; cap=cv2.VideoCapture(entry['video'])
    for f in range(n):
        silhouettes={}
        for pid,d in data.items():
            if not d['observed'][f]: continue
            mesh=shot/pid/variant/f'{f:04d}.npz'
            if not mesh.exists(): continue
            with np.load(mesh) as z: v=z['vertices_camera_m']
            if (v[:,2]<.05).mean()>.02: continue
            K=d['intrinsics'][f]
            uv=(v@K.T); uv=uv[:,:2]/uv[:,2:3]
            silhouettes[pid]=E.KM.fyll(uv*[mw/w,mh/h],np.load(shot/pid/'faces.npy'),mw,mh)
        for pid,sil in silhouettes.items():
            if str(f) not in boxes.get(pid,{}): continue
            others=[s for p,s in silhouettes.items() if p!=pid]
            other=np.logical_or.reduce(others) if others else None
            box=np.asarray(boxes[pid][str(f)])*[mw/w,mh/h,mw/w,mh/h]
            m=E.KM.jamfor_mask(sil,masks[f].astype(bool),box,mw,mh,andra=other)
            if m: samples[pid].append({'frame':f,**m})
        if f in selected:
            cap.set(cv2.CAP_PROP_POS_FRAMES,f); ok,source=cap.read()
            if not ok: continue
            tile=cv2.resize(source,(288,512),interpolation=cv2.INTER_AREA)
            for pid,d in data.items():
                if not d['observed'][f]: continue
                x=xs[pid][f]; K=d['intrinsics'][f]; uv=x@K.T; uv=uv[:,:2]/uv[:,2:3]*[288/w,512/h]
                col=(20,240,250) if pid==entry['pids'][0] else (250,240,40)
                for a,b in EDGES:
                    points=uv[[E.IX[a],E.IX[b]]]
                    if np.isfinite(points).all() and np.abs(points).max()<20000:
                        cv2.line(tile,tuple(np.round(points[0]).astype(int)),tuple(np.round(points[1]).astype(int)),col,2,cv2.LINE_AA)
                for point in uv[E.BODY]:
                    if np.isfinite(point).all() and (point>=0).all() and (point<[288,512]).all():
                        cv2.circle(tile,tuple(np.round(point).astype(int)),3,col,-1)
            cv2.rectangle(tile,(0,0),(288,36),(15,15,15),-1)
            cv2.putText(tile,f'GEM-X {variant} f{f}',(4,23),cv2.FONT_HERSHEY_SIMPLEX,.43,(255,255,255),1,cv2.LINE_AA)
            tiles.append(tile)
    cap.release()
    if tiles: cv2.imwrite(str(shot/f'overlay_{variant}.jpg'),np.concatenate(tiles,axis=1),[cv2.IMWRITE_JPEG_QUALITY,92])
    rows=[]
    for pid,x in xs.items():
        timing=E.read_json(shot/pid/'timing.json')
        row={'method':'gemx-'+variant,'shot':entry['id'],'person':pid,
             'jitter_body15_cm_frame2':E.KM.jitter(x[:,E.BODY]),
             'jitter_root_relative_body15_cm_frame2':E.KM.jitter(x[:,E.BODY]-x[:,E.IX['root']:E.IX['root']+1]),
             'hidden_legs':E.range_metrics(x,hidden[pid]),
             'silhouette':E.KM.sammanfatta(samples[pid]),
             'timing':timing,'joint_mapping':mapping,
             'foot_sliding':{'value':None,'reason':'No verified source foot-contact intervals. Cropped/occluded feet must not be scored as visible.'},
             'hands':{'available':False,'reason':'Body-only run; gated EgoHand weights not downloaded.'}}
        E.save_json(shot/pid/f'metrics_{variant}.json',row)
        E.save_json(shot/pid/f'silhouette_frames_{variant}.json',samples[pid])
        print(entry['id'],pid,variant,'j15',round(row['jitter_body15_cm_frame2'],4),
              'IoU',round(row['silhouette'].get('iou_median',float('nan')),4),flush=True)
        rows.append(row)
    return rows

def main():
    rows=[]
    for entry in E.read_json(ROOT/'manifest.json')['shots']:
        for method in ['sam-raw','slutsekvens']:
            for pid in entry['pids']:
                rows.append(E.read_json(ROOT/'ut'/method/entry['id']/f'metrics_{pid}.json'))
        if not (ROOT/'ut/gemx'/entry['id']/'timing.json').exists(): continue
        for variant in ['raw','contact_ik']: rows.extend(measure(entry,variant))
    E.save_json(ROOT/'gemx_matningar.json',{'rows':rows,'mapping':MAP,
        'mapping_limit':'Anatomical body15 correspondence only; distinct skeletons/identities. Not a retarget or evidence of conversion accuracy.',
        'jitter':'Mean norm of second difference, cm/frame^2; camera coordinates; root-relative also reported.',
        'mask_limit':'Union of person masks; same box/exclusion/cropping rules as evaluate.py; clothes and occluders differ from body mesh.'})

if __name__=='__main__': main()
