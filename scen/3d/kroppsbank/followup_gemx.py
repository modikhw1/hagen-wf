"""Saved geometry only. No torch, local inference or Blender. Run from project root."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d
import evaluate as E
from evaluate_gemx import MAP, EDGES

B=Path(__file__).resolve().parent
OUT=B/'ut/jamforelse'
OUT.mkdir(exist_ok=True,parents=True)
SHOTS=E.read_json(B/'manifest.json')['shots']
SOMA=[0,67,72,68,73,69,74,4,6,12,40,13,41,14,42]
EDGE=[(E.BODY_NAMES.index(a),E.BODY_NAMES.index(b)) for a,b in EDGES]

def project(x,K):
    p=np.einsum('nij,nkj->nki',K,x)
    return p[...,:2]/p[...,2:3]

def jitter(x):
    d=np.diff(x.astype(float),n=2,axis=0)
    good=np.isfinite(d).all(axis=tuple(range(1,d.ndim)))
    return float(np.linalg.norm(d[good],axis=-1).mean()) if good.any() else None

def decompose(x,K,world=None):
    result=dict(camera_cm=jitter(x*100),image_px=jitter(project(x,K)),
                depth_cm=jitter(x[...,2:3]*100),pose_cm=jitter((x-x[:,:1])*100),
                root_cm=jitter(x[:,:1]*100),root_depth_cm=jitter(x[:,:1,2:3]*100))
    if world is not None:
        result.update(world_cm=jitter(world*100),world_pose_cm=jitter((world-world[:,:1])*100),
                      world_root_cm=jitter(world[:,:1]*100))
    return result

def offsets():
    """Match decoded clip frames to original; no assumption about cut start times."""
    p=OUT/'timeline.json'
    if p.exists(): return E.read_json(p)
    c=cv2.VideoCapture('scen/klipp/d-dialog-notan.mp4'); frames=[]
    while True:
        ok,f=c.read()
        if not ok:break
        frames.append(cv2.resize(f,(72,128)).astype(float))
    c.release();rows={}
    for s in SHOTS[:2]:
        cap=cv2.VideoCapture(s['video']); probes=[]
        for f in [0,s['meta']['N']//2,s['meta']['N']-1]:
            cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,a=cap.read();assert ok
            small=cv2.resize(a,(72,128)).astype(float)
            errors=np.array([np.mean(np.abs(a-small)) for a in frames])
            probes.append(dict(clip_frame=f,source_frame=int(errors.argmin()),mae=float(errors.min())))
        cap.release();off=probes[0]['source_frame']
        assert all(r['source_frame']-r['clip_frame']==off for r in probes),probes
        rows[s['id']]=dict(offset=off,probes=probes)
    E.save_json(p,rows);return rows

def load(s,pid,method,mesh=False,sigma=0):
    n=s['meta']['N'];K=np.broadcast_to(s['K'],(n,3,3)).copy();world=None;vertices=None
    if method in ['sam-raw','slutsekvens','fore-golv-kontakt']:
        d=np.load(B/'ut'/method/s['id']/f'joints_{pid}.npz')
        x=d['camera_cm'][:,E.BODY]/100;valid=np.isfinite(x).all(axis=(1,2))
        faces=E.KM.hud()['faces']
        if mesh:
            cache=OUT/'cache'/s['id']/pid
            cache.mkdir(parents=True,exist_ok=True)
            vp=cache/(method+'_mesh.npy')
            if not vp.exists():
                v=np.zeros((n,18439,3),np.float32)
                if method=='sam-raw':
                    for f in np.flatnonzero(valid):
                        with np.load(Path(s['folder'])/'kropp'/pid/f'{f:04d}.npz') as z:
                            v[f]=z['pred_vertices']+z['pred_cam_t']
                else:
                    z=dict(np.load(Path(s['folder'])/f'sekvens_{pid}.npz'))
                    # Preserve the input snapshot used for this diagnostic.
                    np.savez_compressed(cache/(method+'_input.npz'),**z)
                    for f in np.flatnonzero(valid):
                        pose=z['pose'][f].copy();t=z['cam_t'][f]
                        if method=='fore-golv-kontakt':
                            pose=z.get('pose_fore_kontakt',z['pose'])[f].copy()
                            pose[:,:3]/=z.get('golv_skala',np.ones(n))[f]
                            t=z.get('cam_t_fore_golv',z['cam_t'])[f]
                        v[f]=E.KM.hudhorn(pose)/100@E.F+t
                np.save(vp,v)
            vertices=np.load(vp,mmap_mode='r')
    else:
        projected=OUT.parent/'gemx_projected'/s['id']/method/pid/f'{sigma}.npz'
        start=0
        if method in ['gemx-raw','gemx-contact_ik']:
            p=B/'ut/gemx'/s['id']/pid;variant=method[5:]
        else:
            p=B/'ut/gemx_followup'/method/pid;variant='raw'
            if (not mesh or projected.exists()) and not (p/'raw_joints.npz').exists():p=B/'ut/gemx_slim'/method/pid
            if method.startswith('notan-whole'):start=offsets()[s['id']]['offset']
        z=np.load(p/f'{variant}_joints.npz')
        sl=slice(start,start+n)
        x=z['camera_m'][sl][:,SOMA].astype(float);world=z['world_m'][sl][:,SOMA].astype(float)
        K=z['intrinsics'][sl].copy()
        # Every configuration is scored on the SAME original observed frames.
        base=np.load(B/'ut/gemx'/s['id']/pid/'raw_joints.npz')
        valid=base['observed'].astype(bool)
        x[~valid]=np.nan;world[~valid]=np.nan
        faces=np.load(p/'faces.npy')
        if mesh and projected.exists():
            pd=dict(np.load(projected))
            return dict(x=pd['x'],K=pd['K'],valid=pd['valid'],pre_sil=pd['sil'],v=None,faces=faces,
                world=world if not sigma else None,bone_length_delta_p95_pct=float(pd['bone_length_delta_p95_pct']))
        if mesh:
            vertices=np.array([np.load(p/variant/f'{f:04d}.npz')['vertices_camera_m'] for f in range(start,start+n)])
    return dict(x=x,K=K,world=world,valid=valid,v=vertices,faces=faces)

def reference(s,pid):
    z=np.load(B/'ut/gemx'/s['id']/pid/'conditions.npz')
    kp=z['kp2d'][:,SOMA]
    masks=np.load(Path(s['folder'])/'masker.npy',mmap_mode='r');mh,mw=masks.shape[1:]
    w,h=s['meta']['bredd'],s['meta']['hojd'];uv=kp[...,:2]
    good=(kp[...,2]>.5)&(uv>=0).all(-1)&(uv<[w,h]).all(-1)
    ij=np.clip((uv*[mw/w,mh/h]).astype(int),[0,0],[mw-1,mh-1])
    good &= masks[np.arange(len(kp))[:,None],ij[...,1],ij[...,0]].astype(bool)
    boxes=E.read_json(Path(s['folder'])/'personer.json')[pid]
    for f in range(len(kp)):
        if str(f) not in boxes:good[f]=False;continue
        b=boxes[str(f)];good[f]&=(uv[f]>=[b[0],b[1]]).all(-1)&(uv[f]<=[b[2],b[3]]).all(-1)
    return uv,good

def kp_measure(s,pid,d):
    ref,good=reference(s,pid);err=np.linalg.norm(project(d['x'],d['K'])-ref,axis=-1)
    good &= np.isfinite(err)
    return dict(kp_px=float(np.median(err[good])),kp_pairs=int(good.sum()),
                kp_p90_px=float(np.percentile(err[good],90))) if good.any() else dict(kp_px=None,kp_pairs=0)

def filter_data(d,sigma):
    if not sigma:return d
    r=dict(d);good=d['valid'];indices=np.arange(len(good));x=d['x'].copy()
    # Interpolate absent input frames solely for convolution; never score them.
    for j in range(x.shape[1]):
        for k in range(3):x[:,j,k]=np.interp(indices,indices[good],x[good,j,k])
    root=x[:,:1].copy();rel=x-root
    root_f=gaussian_filter1d(root,sigma,axis=0,mode='reflect',truncate=3.)
    r['x']=root_f+gaussian_filter1d(rel,sigma,axis=0,mode='reflect',truncate=3.)
    if d['v'] is not None:
        v=np.asarray(d['v']).copy()
        # Fill unobserved meshes by nearest observed frame (same rule both methods).
        for f in np.flatnonzero(~good):v[f]=v[np.flatnonzero(good)[np.abs(np.flatnonzero(good)-f).argmin()]]
        r['v']=root_f+gaussian_filter1d(v-root,sigma,axis=0,mode='reflect',truncate=3.)
    r['x'][~good]=np.nan
    before=np.array([np.linalg.norm(x[:,a]-x[:,b],axis=-1) for a,b in EDGE])
    after=np.array([np.linalg.norm(r['x'][:,a]-r['x'][:,b],axis=-1) for a,b in EDGE])
    r['bone_length_delta_p95_pct']=float(np.nanpercentile(np.abs(after-before)/np.maximum(before,.01)*100,95))
    return r

def silhouette_frames(s,people):
    masks=np.load(Path(s['folder'])/'masker.npy',mmap_mode='r');mh,mw=masks.shape[1:]
    boxes=E.read_json(Path(s['folder'])/'personer.json');w,h=s['meta']['bredd'],s['meta']['hojd']
    samples={pid:[] for pid in people};sils={pid:[] for pid in people}
    for f in range(s['meta']['N']):
        silhouettes={}
        for pid,d in people.items():
            if not d['valid'][f]:continue
            if 'pre_sil' in d:
                silhouettes[pid]=d['pre_sil'][f]
                continue
            v=d['v'][f];uv=v@d['K'][f].T;uv=uv[:,:2]/uv[:,2:3]
            if (v[:,2]<.05).mean()>.02:continue
            silhouettes[pid]=E.KM.fyll(uv*[mw/w,mh/h],d['faces'],mw,mh)
        for pid in people:
            sils[pid].append(silhouettes.get(pid,np.zeros((mh,mw),bool)))
        for pid,sil in silhouettes.items():
            if str(f) not in boxes[pid]:continue
            # Fixed other-person exclusion from raw SAM for all methods/configurations.
            other=None
            other_path=OUT/'cache'/s['id']/('other_'+pid+'.npy')
            if other_path.exists():other=np.load(other_path,mmap_mode='r')[f]
            b=np.asarray(boxes[pid][str(f)])*[mw/w,mh/h,mw/w,mh/h]
            m=E.KM.jamfor_mask(sil,masks[f].astype(bool),b,mw,mh,andra=other)
            if m:samples[pid].append(dict(frame=f,**m))
    return {pid:E.KM.sammanfatta(v) for pid,v in samples.items()},sils

def audit():
    rows=[];meta=[]
    for s in SHOTS:
        cap=cv2.VideoCapture(s['video']);times=[]
        while True:
            ok,_=cap.read()
            if not ok:break
            times.append(cap.get(cv2.CAP_PROP_POS_MSEC)/1000)
        meta.append(dict(shot=s['id'],fps=cap.get(cv2.CAP_PROP_FPS),frames=len(times),
            width=cap.get(cv2.CAP_PROP_FRAME_WIDTH),height=cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
            timestamp_step_min=float(np.diff(times).min()),timestamp_step_max=float(np.diff(times).max())))
        cap.release()
        for pid in s['pids']:
            for method in ['sam-raw','slutsekvens','gemx-raw','gemx-contact_ik']:
                d=load(s,pid,method)
                rows.append(dict(shot=s['id'],person=pid,method=method,**decompose(d['x'],d['K'],d['world']),**kp_measure(s,pid,d)))
            c=np.load(B/'ut/gemx'/s['id']/pid/'conditions.npz')
            from scipy.spatial.transform import Rotation
            angles=Rotation.from_matrix(c['R_w2c']@c['R_w2c'][0].T).magnitude()*180/np.pi
            meta.append(dict(shot=s['id'],person=pid,model_frames=len(c['frame_times']),
                model_time_step=float(np.diff(c['frame_times']).mean()),
                invented_camera_rotation_max_deg=float(angles.max()),
                transl_jitter_cm=jitter(c['param_transl'][0,:,None]*100)))
    E.save_json(OUT/'decomposition.json',rows);E.save_json(OUT/'input_audit.json',meta)
    offsets()
    for r in rows:print(r['shot'],r['person'],r['method'],*[round(r[k],3) if r.get(k) is not None else '-' for k in ['image_px','depth_cm','pose_cm','root_cm','world_cm']],flush=True)

def configs():
    rows=[]
    for s in SHOTS:
        candidates=['gemx-raw','gemx-contact_ik']
        for p in (B/'ut/gemx_slim').glob(s['id']+'__*'):
            if (B/'ut/gemx_projected'/s['id']/p.name/'1/0.npz').exists():candidates.append(p.name)
        if s['id'].startswith('notan'):
            candidates += [p.name for p in (B/'ut/gemx_slim').glob('notan-whole__*') if (B/'ut/gemx_projected'/s['id']/p.name/'1/0.npz').exists()]
        for method in candidates:
            pids=s['pids'] if method.startswith('gemx-') or 'adapter' in method else ['1']
            people={pid:load(s,pid,method,mesh=True) for pid in pids}
            sm,sils=silhouette_frames(s,people)
            for pid,d in people.items():
                r=dict(shot=s['id'],person=pid,method=method,**decompose(d['x'],d['K'],d['world']),**kp_measure(s,pid,d),silhouette=sm[pid])
                if not method.startswith('gemx-'):
                    c=np.load(B/'ut/gemx_slim'/method/pid/'conditions.npz')
                    start=offsets()[s['id']]['offset'] if method.startswith('notan-whole') else 0
                    boxes=E.read_json(Path(s['folder'])/'personer.json')[pid];ious=[]
                    for f in range(len(d['x'])):
                        if str(f) not in boxes:continue
                        a=np.asarray(boxes[str(f)]);b=c['boxes'][start+f]
                        inter=np.maximum(0,np.minimum(a[2:],b[2:])-np.maximum(a[:2],b[:2])).prod()
                        ious.append(inter/((a[2:]-a[:2]).prod()+(b[2:]-b[:2]).prod()-inter))
                    r['stock_box_iou_median']=float(np.median(ious))
                rows.append(r)
                print(s['id'],pid,method,round(r['camera_cm'],3),round(sm[pid]['iou_median'],3),round(r['kp_px'],2),flush=True)
            E.save_json(OUT/'configurations.json',rows)
    return rows

def quick_configs():
    rows=[]
    for s in SHOTS:
        candidates=[p.name for p in (B/'ut/gemx_slim').glob(s['id']+'__*')]
        if s['id'].startswith('notan'):candidates += [p.name for p in (B/'ut/gemx_slim').glob('notan-whole__*')]
        for method in candidates:
            for pid in (s['pids'] if 'adapter' in method else ['1']):
                d=load(s,pid,method)
                r=dict(shot=s['id'],person=pid,method=method,**decompose(d['x'],d['K'],d['world']),**kp_measure(s,pid,d))
                rows.append(r)
                print(s['id'],pid,method,'J',round(r['camera_cm'],3),'px',round(r['image_px'],3),'pose',round(r['pose_cm'],3),'Kp',round(r['kp_px'],2),flush=True)
    E.save_json(OUT/'quick_configurations.json',rows)

def fixed_exclusions():
    for s in SHOTS:
        if len(s['pids'])<2:continue
        people={pid:load(s,pid,'sam-raw',mesh=True) for pid in s['pids']}
        _,sils=silhouette_frames(s,people)
        for pid in s['pids']:
            arr=np.logical_or.reduce([v for k,v in sils.items() if k!=pid])
            p=OUT/'cache'/s['id']/('other_'+pid+'.npy');p.parent.mkdir(exist_ok=True,parents=True);np.save(p,arr)

def curves(baseline=False):
    best={} if baseline else E.read_json(OUT/'best.json')
    cached_baselines=not baseline and (OUT/'curves_baseline.json').exists()
    rows=E.read_json(OUT/'curves_baseline.json') if cached_baselines else []
    for s in SHOTS:
        for method in (['best-gemx'] if cached_baselines else ['sam-raw','slutsekvens'] if baseline else ['sam-raw','slutsekvens','best-gemx']):
            data={pid:load(s,pid,best[s['id']][pid] if method=='best-gemx' else method,mesh=True) for pid in s['pids']}
            for sigma in ([0] if method=='slutsekvens' else [0,.5,1,2,3]):
                people={pid:(load(s,pid,best[s['id']][pid],mesh=True,sigma=sigma) if method=='best-gemx' and 'pre_sil' in d else filter_data(d,sigma)) for pid,d in data.items()}
                sm,sils=silhouette_frames(s,people)
                for pid,d in people.items():
                    r=dict(shot=s['id'],person=pid,method=method,sigma_frames=sigma,
                        **decompose(d['x'],d['K']),**kp_measure(s,pid,d),silhouette=sm[pid],
                        bone_length_delta_p95_pct=d.get('bone_length_delta_p95_pct',0))
                    rows.append(r)
                    print('curve',s['id'],pid,method,sigma,round(r['camera_cm'],3),round(sm[pid]['iou_median'],3),flush=True)
                if sigma in [0,1,2]:
                    p=OUT/'cache'/s['id'];p.mkdir(exist_ok=True,parents=True)
                    for pid,d in people.items():
                        np.savez_compressed(p/f'{pid}_{method}_{sigma}_display.npz',x=d['x'],K=d['K'],sil=np.array(sils[pid]),valid=d['valid'])
                E.save_json(OUT/('curves_baseline.json' if baseline else 'curves.json'),rows)

def videos():
    for s in SHOTS[:3]:
        n=s['meta']['N'];w,h=s['meta']['bredd'],s['meta']['hojd'];fps=s['meta']['fps']
        for sigma in [0,1,2]:
            methods=['slutsekvens','sam-raw','best-gemx']
            data={method:{pid:dict(np.load(OUT/'cache'/s['id']/f'{pid}_{method}_{0 if method=="slutsekvens" else sigma}_display.npz')) for pid in s['pids']} for method in methods}
            path=OUT/f'{s["id"]}_sigma{sigma}.mp4'
            writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),fps,(1152,512));assert writer.isOpened()
            cap=cv2.VideoCapture(s['video']);samples=[]
            for f in range(n):
                ok,src=cap.read();assert ok
                source=cv2.resize(src,(288,512));tiles=[source.copy()]
                cv2.putText(tiles[0],f'SOURCE f{f} / {fps:g} fps',(5,23),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,255,255),1,cv2.LINE_AA)
                for method in methods:
                    tile=source.copy()
                    for pid,d in data[method].items():
                        if not d['valid'][f]:continue
                        col=(20,240,250) if pid=='1' else (250,210,40)
                        mask=cv2.resize(d['sil'][f].astype(np.uint8),(288,512),interpolation=cv2.INTER_NEAREST)
                        contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(tile,contours,-1,col,1)
                        uv=project(d['x'][f:f+1],d['K'][f:f+1])[0]*[288/w,512/h]
                        for a,b in EDGE:
                            pts=uv[[a,b]]
                            if np.isfinite(pts).all() and np.abs(pts).max()<20000:cv2.line(tile,tuple(pts[0].round().astype(int)),tuple(pts[1].round().astype(int)),col,2,cv2.LINE_AA)
                    cv2.rectangle(tile,(0,0),(288,36),(15,15,15),-1)
                    label={'slutsekvens':'FINAL','sam-raw':'SAM','best-gemx':'GEM-X'}[method]
                    cv2.putText(tile,f'{label} sigma={0 if method=="slutsekvens" else sigma} f{f}',(4,23),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,255,255),1,cv2.LINE_AA);tiles.append(tile)
                frame=np.concatenate(tiles,axis=1);writer.write(frame)
                if f in np.linspace(0,n-1,6).round().astype(int):samples.append(frame)
            cap.release();writer.release()
            cv2.imwrite(str(OUT/f'{s["id"]}_sigma{sigma}_frames.jpg'),np.concatenate(samples,axis=0))
            check=cv2.VideoCapture(str(path));assert int(check.get(cv2.CAP_PROP_FRAME_COUNT))==n;assert abs(check.get(cv2.CAP_PROP_FPS)-fps)<1e-6;check.release()
            print('video',path,flush=True)

def post_ablation(root_filters=False):
    rows=[]
    for s in SHOTS:
        raw={pid:load(s,pid,'sam-raw',mesh=True) for pid in s['pids']}
        final={pid:load(s,pid,'slutsekvens',mesh=True) for pid in s['pids']}
        for name in (['final_pose_sam_root_sigma1','final_pose_sam_root_sigma2'] if root_filters else ['final_pose_sam_root','sam_pose_final_root','before_floor_contact']):
            people={}
            for pid in s['pids']:
                if name=='before_floor_contact':
                    # Reconstruct saved pre-floor/contact state using geometry only.
                    d=dict(final[pid]);z=dict(np.load(Path(s['folder'])/f'sekvens_{pid}.npz'))
                    v=[];x=[]
                    for f in range(s['meta']['N']):
                        pose=z.get('pose_fore_kontakt',z['pose'])[f].copy()
                        pose[:,:3]/=z.get('golv_skala',np.ones(len(z['pose'])))[f]
                        t=z.get('cam_t_fore_golv',z['cam_t'])[f]
                        x.append(pose[E.BODY,:3]/100@E.F+t)
                        v.append(E.KM.hudhorn(pose)/100@E.F+t)
                    d['x']=np.array(x);d['v']=np.array(v);d['x'][~d['valid']]=np.nan
                else:
                    a=final[pid] if name.startswith('final_pose_sam_root') else raw[pid]
                    b=raw[pid] if name.startswith('final_pose_sam_root') else final[pid]
                    if root_filters:
                        b=filter_data(dict(b,v=None),int(name[-1]))
                    d=dict(a);delta=b['x'][:,:1]-a['x'][:,:1]
                    d['x']=a['x']+delta;d['v']=a['v']+delta
                people[pid]=d
            sm,_=silhouette_frames(s,people)
            for pid,d in people.items():
                r=dict(shot=s['id'],person=pid,method=name,**decompose(d['x'],d['K']),**kp_measure(s,pid,d),silhouette=sm[pid]);rows.append(r)
                print(s['id'],pid,name,round(r['camera_cm'],3),round(sm[pid]['iou_median'],3),round(r['kp_px'],2),flush=True)
            E.save_json(OUT/('root_filter_ablation.json' if root_filters else 'post_ablation.json'),rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['audit','configs','quick-configs','curves','baseline','videos','exclusions','post-ablation','root-filters']);a=parser.parse_args()
    {'audit':audit,'configs':configs,'quick-configs':quick_configs,'curves':curves,'baseline':lambda:curves(True),'videos':videos,'exclusions':fixed_exclusions,'post-ablation':post_ablation,'root-filters':lambda:post_ablation(True)}[a.mode]()
