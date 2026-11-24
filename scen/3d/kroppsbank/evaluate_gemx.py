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

def foot_diagnostics(entry,pid,camera_m,foot_indices,K):
    """Same existing camera/floor for all methods; visibility is a mask diagnostic.

    Uses vakt's 6 cm height / 1 cm vertical speed contact rule, not a new
    requirement. No foot-contact ground truth or clip-specific constants.
    """
    folder=Path(entry['folder']); n=len(camera_m)
    masks=np.load(folder/'masker.npy',mmap_mode='r'); mh,mw=masks.shape[1:]
    w,h=entry['meta']['bredd'],entry['meta']['hojd']
    boxes=E.read_json(folder/'personer.json').get(pid,{})
    V=dict(np.load(folder/'varld.npz')); up=V['upp']; result={}
    for side,indices in foot_indices.items():
        feet=camera_m[:,indices]; visible=np.zeros(n,bool)
        for f in range(n):
            if str(f) not in boxes or not np.isfinite(feet[f]).all() or (feet[f,:,2]<.05).any(): continue
            uv=feet[f]@K[f].T; uv=uv[:,:2]/uv[:,2:3]
            if not ((uv>=0).all() and (uv<[w,h]).all()): continue
            x0,y0,x1,y1=boxes[str(f)]
            if not ((uv>=[x0,y0]).all() and (uv<=[x1,y1]).all()): continue
            pixels=np.minimum((uv*[mw/w,mh/h]).astype(int),[mw-1,mh-1])
            visible[f]=bool(masks[f,pixels[:,1],pixels[:,0]].all())
        world=V['kam_C'][:,None]+np.einsum('nij,nkj->nki',V['kam_R'],feet)
        height=world@up; horizontal=world-height[...,None]*up
        speed=np.linalg.norm(np.diff(horizontal.mean(1),axis=0),axis=1)*100
        vertical=np.abs(np.diff(height.min(1)))*100
        contact=visible[1:]&visible[:-1]&(vertical<1)
        if 'golv_h' in V: contact &= (height[1:].min(1)-float(V['golv_h']))*100<6
        else: contact[:]=False
        values=speed[contact]
        result[side]={'mask_visible_frames':int(visible.sum()),'contact_pairs':len(values),
            'contact_pair_end_frames':(np.flatnonzero(contact)+1).tolist(),
            'slide_cm_frame_median':float(np.median(values)) if len(values) else None,
            'slide_cm_frame_p90':float(np.percentile(values,90)) if len(values) else None}
    return {'feet':result,'coordinates':'Camera joints transformed by the SAME cached ingest kam_R/kam_C and floor for all methods; not aligned GEM-X native rollout.',
        'visibility':'Both ankle and toe in source raster, tracked box and person mask. Diagnostic only; union masks can include another person/occluder.'}

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
             'foot_sliding':foot_diagnostics(entry,pid,data[pid]['camera_m'],
                 {s:[names.index(prefix+'Foot'),names.index(prefix+'ToeBase')] for s,prefix in [('left','Left'),('right','Right')]},data[pid]['intrinsics']),
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
                row=E.read_json(ROOT/'ut'/method/entry['id']/f'metrics_{pid}.json')
                with np.load(ROOT/'ut'/method/entry['id']/f'joints_{pid}.npz') as z: camera=z['camera_cm']/100
                row['foot_sliding']=foot_diagnostics(entry,pid,camera,
                    {s:[E.IX[prefix+'_foot'],E.IX[prefix+'_ball']] for s,prefix in [('left','l'),('right','r')]},
                    np.broadcast_to(entry['K'],(len(camera),3,3)))
                rows.append(row)
        if not (ROOT/'ut/gemx'/entry['id']/'timing.json').exists(): continue
        for variant in ['raw','contact_ik']:
            cached=[ROOT/'ut/gemx'/entry['id']/pid/f'metrics_{variant}.json' for pid in entry['pids']]
            if all(p.exists() for p in cached): rows.extend(E.read_json(p) for p in cached)
            else: rows.extend(measure(entry,variant))
    manifest={s['id']:s for s in E.read_json(ROOT/'manifest.json')['shots']}
    for row in rows:
        entry=manifest[row['shot']]; pid=row['person']; method=row['method']
        if method.startswith('gemx-'):
            variant=method[5:]; base=ROOT/'ut/gemx'/entry['id']/pid
            names=[n.split('/')[-1] for n in E.read_json(base/'joint_names.json')]
            d=np.load(base/f'{variant}_joints.npz')
            camera=np.full((len(d['camera_m']),127,3),np.nan)
            camera[:,E.BODY]=100*d['camera_m'][:,[names.index(MAP[x]) for x in E.BODY_NAMES]]
            camera[~d['observed'].astype(bool)]=np.nan
        else:
            with np.load(ROOT/'ut'/method/entry['id']/f'joints_{pid}.npz') as d: camera=d['camera_cm']
        present=np.isfinite(camera[:,E.BODY]).all(axis=(1,2))
        row['leg_motion_all_tracked_frames']=E.range_metrics(camera,present)
        row['leg_motion_all_tracked_frames']['note']='All tracked frames, including visible legs; useful on seated shots. Not hidden-joint accuracy.'
    references={(r['shot'],r['person']):r for r in rows if r['method']=='sam-raw'}
    for row in rows:
        entry=manifest[row['shot']]; pid=row['person']; method=row['method']
        native=method.startswith('gemx-')
        if native:
            base=ROOT/'ut/gemx'/entry['id']/pid
            names=[n.split('/')[-1] for n in E.read_json(base/'joint_names.json')]
            with np.load(base/f'{method[5:]}_joints.npz') as d: world=d['world_m']
            up=np.array([0,1,0.])
            indices={s:[names.index(prefix+'Foot'),names.index(prefix+'ToeBase')] for s,prefix in [('left','Left'),('right','Right')]}
        else:
            with np.load(ROOT/'ut'/method/entry['id']/f'joints_{pid}.npz') as d: camera=d['camera_cm']/100
            V=dict(np.load(Path(entry['folder'])/'varld.npz'))
            world=V['kam_C'][:,None]+np.einsum('nij,nkj->nki',V['kam_R'],camera); up=V['upp']
            indices={s:[E.IX[prefix+'_foot'],E.IX[prefix+'_ball']] for s,prefix in [('left','l'),('right','r')]}
        results={}
        for side,joints in indices.items():
            contact=references[(row['shot'],pid)]['foot_sliding']['feet'][side]['contact_pair_end_frames']
            foot=world[:,joints].mean(1); hor=foot-(foot@up)[:,None]*up
            values=np.linalg.norm(hor[np.asarray(contact,int)]-hor[np.asarray(contact,int)-1],axis=1)*100
            values=values[np.isfinite(values)]
            results[side]={'pairs':len(values),'median_cm_frame':float(np.median(values)) if len(values) else None,
                           'p90_cm_frame':float(np.percentile(values,90)) if len(values) else None}
        row['foot_common_reference']={'feet':results,
            'world':'Native GEM-X Y-up world' if native else 'Cached ingest world',
            'reference':'Identical intervals for every method: raw SAM ankle+toe in source mask/box, with vakt height<6cm, vertical step<1cm. Assumed contacts, not ground truth. No global scene alignment needed for translation/yaw-invariant horizontal speed; metric scale remains monocular.'}
    E.save_json(ROOT/'gemx_matningar.json',{'rows':rows,'mapping':MAP,
        'mapping_limit':'Anatomical body15 correspondence only; distinct skeletons/identities. Not a retarget or evidence of conversion accuracy.',
        'jitter':'Mean norm of second difference, cm/frame^2; camera coordinates; root-relative also reported.',
        'mask_limit':'Union of person masks; same box/exclusion/cropping rules as evaluate.py; clothes and occluders differ from body mesh.'})

if __name__=='__main__': main()
