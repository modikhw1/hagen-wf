"""Camera comparison, shared layout and independent read-back verification for Phase 1."""
import time
import math
import json
import numpy as np
import cv2
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
from fas1 import ROOT, REPO, W, H, SHOTS, read_json, write_json, get_frame, log

# Keep distinct anatomical joints, not five nearly coincident eye landmarks.
UPPER = [0, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
Q = np.diag([1., -1., -1.])  # right-handed MediaPipe -> local y-up, +z toward viewer
HIP = {'A': .60, 'B': .60, 'C': .98}
EDGES = [(0,7),(0,8),(11,12),(11,13),(13,15),(12,14),(14,16),(15,17),(15,19),(15,21),
         (16,18),(16,20),(16,22),(11,23),(12,24),(23,24),(23,25),(24,26),(25,27),(26,28),(27,31),(28,32)]


def intrinsics(fov):
    f=H/(2*np.tan(np.deg2rad(fov)/2))
    return np.array([[f,0,W/2],[0,f,H/2],[0,0,1.]],np.float64)


def points(frame):
    pose=frame['pose']
    if pose is None: return None
    lm=np.array(pose['image']); xyz=np.array(pose['world'])[:,:3]
    ids=np.array(UPPER+([23,24,25,26,27,28,29,30,31,32] if frame['actor']=='C' else []))
    if frame['actor']!='C':
        visible_sides={h['side'] for h in frame['hands']}
        # Pose confidence is not an occlusion detector: e.g. S6 hallucinates hands
        # through burgers/table. Require independent hand evidence for seated
        # wrist/tip points; retain raw measurements in the motion file.
        hidden=set()
        if 'Left' not in visible_sides:hidden.update([15,17,19,21])
        if 'Right' not in visible_sides:hidden.update([16,18,20,22])
        ids=np.array([i for i in ids if i not in hidden])
    mask=(lm[ids,3]>=.65)&(lm[ids,4]>=.65)&(lm[ids,0]>=0)&(lm[ids,0]<=1)&(lm[ids,1]>=0)&(lm[ids,1]<=1)
    ids=ids[mask]
    return xyz[ids].astype(np.float64), (lm[ids,:2]*[W,H]).astype(np.float64), ids


def project(xyz, rvec, tvec, K):
    return cv2.projectPoints(np.asarray(xyz,np.float64),np.asarray(rvec,np.float64),np.asarray(tvec,np.float64),K,None)[0].reshape(-1,2)


def errors(frames, rvec, tvec, K):
    each=[]; all_errors=[]
    for f in frames:
        p=points(f)
        if p is None or len(p[0])<4: continue
        e=np.linalg.norm(project(p[0],rvec,tvec,K)-p[1],axis=1)
        all_errors.extend(e.tolist());each.append(dict(frame=f['frame'],median_px=float(np.median(e)),joints=len(e)))
    return dict(median_px=float(np.median(all_errors)),median_height=float(np.median(all_errors)/H),
                p90_px=float(np.percentile(all_errors,90)),frames=each,joints=len(all_errors))


def camera_info(rvec,tvec,K,actor):
    R=cv2.Rodrigues(np.array(rvec))[0];c=-R.T@np.array(tvec).reshape(3)
    # Horizon is line K^-T R n for n = metric local up, represented in raw pose coordinates.
    line=np.linalg.inv(K).T@R@np.array([0.,-1.,0.])
    horizon=-(line[0]*W/2+line[2])/line[1] if abs(line[1])>1e-8 else None
    return dict(camera_actor_local_m=(Q@c).tolist(),height_m=float(HIP[actor]-c[1]),
        hip_distance_m=float(np.linalg.norm(c)),horizon_center_y_px=float(horizon) if horizon is not None else None,
        rvec=np.array(rvec).reshape(3).tolist(),tvec=np.array(tvec).reshape(3).tolist())


def pnp_candidates(frames,actor):
    out=[]
    for fov in range(40,86):
        K=intrinsics(fov);rotations=[];translations=[];perframe=[]
        for frame in frames:
            p=points(frame)
            if p is None or len(p[0])<6: continue
            ok,r,t=cv2.solvePnP(p[0],p[1],K,None,flags=cv2.SOLVEPNP_SQPNP)
            if not ok: continue
            ok,r,t=cv2.solvePnP(p[0],p[1],K,None,r,t,True,flags=cv2.SOLVEPNP_ITERATIVE)
            if t[2,0]<.1: continue
            rotations.append(r.ravel());translations.append(t.ravel())
            perframe.append(float(np.median(np.linalg.norm(project(p[0],r,t,K)-p[1],axis=1))))
        # Rotations are small around identity in the source pose frame; robust component median.
        r=np.median(rotations,axis=0);t=np.median(translations,axis=0)
        m=errors(frames,r,t,K)
        out.append(dict(fov_deg=fov,**camera_info(r,t,K,actor),**m,
                        per_frame_fit_median_px=float(np.median(perframe)),valid_pnp_frames=len(rotations)))
    return out


def depth_candidate(shot,frames):
    """Independent depth placement: body-size scaled unprojection + rigid 3D alignment.

    Relative inverse depth has an unknown affine offset. We report zero-offset and
    10%-of-median offsets rather than claiming this is calibrated metric depth.
    Scale is set by the median model shoulder width over the shot (body-size prior).
    Rigid alignment to 3D points uses no 2D PnP optimization.
    """
    n=(shot['start_frame']+shot['end_frame_exclusive']-1)//2
    fr=next(f for f in frames if f['frame']==n)
    xyz,uv,ids=points(fr)
    d=np.load(ROOT/'data'/f'{shot["id"]}-relative-depth.npy')
    widths=[np.linalg.norm(np.array(f['pose']['world'])[11,:3]-np.array(f['pose']['world'])[12,:3]) for f in frames if f['pose']]
    width=float(np.median(widths))
    variants=[]
    for fov in [40,55,70,85]:
        K=intrinsics(fov); rays=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T
        rel=np.array([np.median(d[max(0,int(v)-2):min(H,int(v)+3),max(0,int(u)-2):min(W,int(u)+3)]) for u,v in uv])
        for shift_fraction in [0.,.1]:
            z=1/np.maximum(rel+shift_fraction*np.median(rel),1e-6)
            cloud=rays*z[:,None]
            a,b=list(ids).index(11),list(ids).index(12)
            scale=width/np.linalg.norm(cloud[a]-cloud[b]);cloud*=scale
            # Kabsch (proper rotation) rigid fit; absolutely no nonrigid pose deformation.
            xc=xyz-xyz.mean(0);yc=cloud-cloud.mean(0)
            u,_,vt=np.linalg.svd(xc.T@yc);R=vt.T@np.diag([1,1,np.linalg.det(vt.T@u.T)])@u.T
            t=cloud.mean(0)-R@xyz.mean(0);r=cv2.Rodrigues(R)[0].ravel()
            variants.append(dict(fov_deg=fov,shift_fraction=shift_fraction,scale=scale,
                shoulder_width_m=width,**camera_info(r,t,K,shot['actor']),**errors(frames,r,t,K),
                keyframe_median_px=errors([fr],r,t,K)['median_px'],rigid_cloud_rmse_m=float(np.sqrt(np.mean((xyz@R.T+t-cloud)**2)))))
    return variants


def constrained_candidates(frames,actor,unconstrained):
    """Static robust refinement with an explicit floor/hip-height prior.

    Raw per-frame PnP medians initialize every candidate. Only one rigid camera
    is optimized per shot; raw 3D joints and actor placement never deform.
    """
    xyz=np.concatenate([points(f)[0] for f in frames if points(f) is not None])
    uv=np.concatenate([points(f)[1] for f in frames if points(f) is not None])
    out=[]
    for old in unconstrained:
        K=intrinsics(old['fov_deg']);r=np.array(old['rvec']);R=cv2.Rodrigues(r)[0]
        center=-R.T@np.array(old['tvec'])
        lower=np.array([-1.,-1.,-1.,-10.,HIP[actor]-1.7,-15.])
        upper=np.array([1.,1.,1.,10.,HIP[actor]-.9,-.2])
        initial=np.clip(np.r_[r,center],lower+1e-7,upper-1e-7)
        def residual(p):
            rot=cv2.Rodrigues(p[:3])[0];t=-rot@p[3:]
            return (project(xyz,p[:3],t,K)-uv).ravel()
        result=least_squares(residual,initial,bounds=(lower,upper),loss='soft_l1',f_scale=15,max_nfev=120)
        r=result.x[:3];t=-cv2.Rodrigues(r)[0]@result.x[3:]
        out.append(dict(fov_deg=old['fov_deg'],**camera_info(r,t,K,actor),**errors(frames,r,t,K),
                        optimizer_success=bool(result.success),evaluations=result.nfev,
                        height_prior_active=bool(abs((HIP[actor]-result.x[4])-.9)<.001 or abs((HIP[actor]-result.x[4])-1.7)<.001)))
    return out


def solve():
    start=time.perf_counter();data=read_json(ROOT/'data/sparning.json');allresults={}
    for shot in SHOTS:
        frames=[f for f in data['frames'] if f['shot']==shot['id']]
        candidates=pnp_candidates(frames,shot['actor'])
        best=min(candidates,key=lambda c:c['median_px'])
        depth=depth_candidate(shot,frames)
        constrained=constrained_candidates(frames,shot['actor'],candidates)
        allresults[shot['id']]=dict(pnp_candidates=candidates,pnp_best=best,depth_candidates=depth,
            depth_best=min(depth,key=lambda c:c['median_px']),constrained_candidates=constrained,
            selected=min(constrained,key=lambda c:c['median_px']))
        print(shot['id'],'PnP', {k:round(best[k],3) for k in ['fov_deg','median_px','height_m','hip_distance_m','horizon_center_y_px']},
              'Depth',{k:round(allresults[shot['id']]['depth_best'][k],3) for k in ['fov_deg','median_px','height_m','hip_distance_m']},flush=True)
        print('Selected',{k:round(allresults[shot['id']]['selected'][k],3) for k in ['fov_deg','median_px','height_m','hip_distance_m','horizon_center_y_px']},flush=True)
    write_json(ROOT/'data/camera-comparison.json',dict(shots=allresults,runtime_s=time.perf_counter()-start))


def fit_shared_prop(frames,actor,seeds,anchors,free=False):
    xyz=np.concatenate([points(f)[0] for f in frames if points(f) is not None])
    uv=np.concatenate([points(f)[1] for f in frames if points(f) is not None])
    # Each anchor contains bbox-derived bottom/top centers. Heights are declared
    # packaging priors, not measured product dimensions or exact silhouette points.
    target=np.array([p for a in anchors for p in [a['base_uv'],a['top_uv']]])
    weight=4*np.sqrt(len(xyz)/len(target))
    out=[]
    for old in seeds:
        K=intrinsics(old['fov_deg']);r=np.array(old['rvec']);R=cv2.Rodrigues(r)[0]
        center=-R.T@np.array(old['tvec'])
        lower=[-1.,-1.,-1.,-10.,HIP[actor]-1.7,-15.]
        upper=[1.,1.,1.,10.,HIP[actor]-.9,-.2]
        initial=list(np.r_[r,center])
        if free:
            for a in anchors:
                ray=Q@R.T@np.linalg.inv(K)@np.r_[a['base_uv'],1.]
                cam=Q@center
                base=cam+ray*(a['base_local'][1]-cam[1])/ray[1]
                initial.extend([base[0],base[2]])
                lower.extend(a['lower_xz']);upper.extend(a['upper_xz'])
        initial=np.clip(initial,np.array(lower)+1e-6,np.array(upper)-1e-6)
        def object_points(p):
            pts=[]
            for i,a in enumerate(anchors):
                base=np.array(a['base_local'],float)
                if free: base[[0,2]]=p[6+2*i:8+2*i]
                pts.extend([Q@base,Q@(base+np.array([0,a['height_m'],0]))])
            return np.array(pts)
        def residual(p):
            rot=cv2.Rodrigues(p[:3])[0];t=-rot@p[3:6]
            joint=(project(xyz,p[:3],t,K)-uv).ravel()
            joint=np.sign(joint)*np.sqrt(2*15**2*(np.sqrt(1+(joint/15)**2)-1))
            prop=(project(object_points(p),p[:3],t,K)-target).ravel()*weight
            return np.r_[joint,prop]
        result=least_squares(residual,initial,bounds=(lower,upper),loss='linear',max_nfev=150)
        r=result.x[:3];t=-cv2.Rodrigues(r)[0]@result.x[3:6]
        ae=np.linalg.norm(project(object_points(result.x),r,t,K)-target,axis=1)
        out.append(dict(fov_deg=old['fov_deg'],**camera_info(r,t,K,actor),**errors(frames,r,t,K),
            anchor_error_px=ae.tolist(),anchor_max_px=float(max(ae)),optimizer_success=bool(result.success),
            anchor_bases_local_m=[(Q@p).tolist() for p in object_points(result.x)[::2]],
            height_prior_active=bool(abs(HIP[actor]-result.x[4]-.9)<.001 or abs(HIP[actor]-result.x[4]-1.7)<.001)))
    feasible=[c for c in out if c['anchor_max_px']<=12 and c['optimizer_success']]
    chosen=min(feasible or out,key=lambda c:c['median_px'] if feasible else c['anchor_max_px'])
    return chosen,out


def layout():
    start=time.perf_counter();data=read_json(ROOT/'data/sparning.json')
    comparison=read_json(ROOT/'data/camera-comparison.json')['shots']
    anchors7=[dict(id='B:cup',base_uv=[.4875*W,.485*H],top_uv=[.4875*W,.423*H],height_m=.18,
                  base_local=[-.17,.75-HIP['B'],.80],lower_xz=[-.30,.79999],upper_xz=[-.05,.80001]),
              dict(id='A:can',base_uv=[.844*W,.965*H],top_uv=[.844*W,.634*H],height_m=.168,
                  base_local=[.13,.75-HIP['B'],4.05],lower_xz=[-1.5,.3],upper_xz=[1.5,8.])]
    frames7=[f for f in data['frames'] if f['shot']=='S7']
    best,candidates=fit_shared_prop(frames7,'B',comparison['S7']['constrained_candidates'],anchors7,True)
    comparison['S7']['height_only_selected']=comparison['S7']['selected']
    comparison['S7']['selected']=best;comparison['S7']['shared_prop_candidates']=candidates
    comparison['S7']['anchors']=anchors7
    print('Shared S7',{k:round(best[k],3) for k in ['fov_deg','median_px','height_m','anchor_max_px']},best['anchor_bases_local_m'],flush=True)
    yolo=read_json(REPO/'scen/data/d-dialog-notan/spar.json')['bilder']
    for shot in SHOTS[:-1]:
        sid=shot['id'];actor=shot['actor']
        if actor=='C':continue
        mid=(shot['start_frame']+shot['end_frame_exclusive']-1)/60
        detections=min(yolo,key=lambda f:abs(f['t']-mid))
        options=[o for o in detections['f'] if o['k']==('bottle' if actor=='A' else 'cup')]
        obj=max(options,key=lambda o:o['c']);x0,y0,x1,y1=obj['box']
        base=[-.22,.75-HIP[actor],.90] if actor=='A' else best['anchor_bases_local_m'][0]
        anchor=dict(id=f'{actor}:'+('can' if actor=='A' else 'cup'),base_uv=[(x0+x1)*W/2,y1*H],
            top_uv=[(x0+x1)*W/2,y0*H],height_m=.168 if actor=='A' else .18,base_local=base,
            source='YOLO-World source frame',source_t=detections['t'],source_box=obj['box'])
        frames=[f for f in data['frames'] if f['shot']==sid]
        chosen,candidates=fit_shared_prop(frames,actor,comparison[sid]['constrained_candidates'],[anchor])
        comparison[sid]['height_only_selected']=comparison[sid]['selected']
        comparison[sid]['selected']=chosen;comparison[sid]['shared_prop_candidates']=candidates
        comparison[sid]['anchors']=[anchor]
        print('Shared',sid,{k:round(chosen[k],3) for k in ['fov_deg','median_px','height_m','anchor_max_px']},flush=True)
    write_json(ROOT/'data/layout-comparison.json',dict(shots=comparison,runtime_s=time.perf_counter()-start,
        anchor_priors='can height .168 m; paper cup .18 m; y=.75 m bases; A can x=-.22,z=.90 relative to hip; B cup z=.80. Both on 0.7 m tables centered .60 m ahead of seats. Anthropometric/package and placement assumptions, not surveyed dimensions.'))
    build_layout(data,comparison)


def build_layout(data,comparison):
    started=time.perf_counter()
    def yaw(degrees): return Rotation.from_euler('y',degrees,degrees=True).as_matrix()
    bpos=np.array([0.,HIP['B'],0.]);bcan=np.array(comparison['S7']['selected']['anchor_bases_local_m'][1])+bpos
    apos=bcan-yaw(180)@np.array([-.22,.75-HIP['A'],.90])
    placements={'A':(apos,180),'B':(bpos,0),'C':(np.array([1.55,HIP['C'],2.4]),90)}
    actors={}
    for actor,(position,angle) in placements.items():
        transform=np.eye(4);transform[:3,:3]=yaw(angle)@Q;transform[:3,3]=position
        actors[actor]=dict(id=actor,position_m=position.tolist(),yaw_deg=angle,
            hip_height_m=HIP[actor],posture='standing' if actor=='C' else 'seated',
            raw_pose_to_world=transform.tolist(),motion_track='sparning.json',
            assumption='Fixed hip origin, source-view pose axes rotated into shared room; no per-frame camera or pose warping.')
    cameras={}
    for shot in SHOTS:
        sid=shot['id'];selected=comparison[sid]['selected'];actor=actors[shot['actor']]
        transform=np.array(actor['raw_pose_to_world']);r=cv2.Rodrigues(np.array(selected['rvec']))[0]
        rw=r@transform[:3,:3].T;tw=np.array(selected['tvec'])-rw@transform[:3,3]
        extrinsic=np.eye(4);extrinsic[:3,:3]=rw;extrinsic[:3,3]=tw
        center=-rw.T@tw;direction=rw.T@np.array([0.,0.,1.])
        cameras[sid]=dict(id=sid,actor=shot['actor'],start_frame=shot['start_frame'],end_frame_exclusive=shot['end_frame_exclusive'],
            time_in=shot['start_frame']/30,time_out=shot['end_frame_exclusive']/30,
            position_m=center.tolist(),target_m=(center+direction).tolist(),up=(rw.T@np.array([0.,-1.,0.])).tolist(),
            vertical_fov_deg=selected['fov_deg'],intrinsics_px=intrinsics(selected['fov_deg']).tolist(),
            world_to_camera_cv=extrinsic.tolist(),camera_to_world_cv=np.linalg.inv(extrinsic).tolist(),
            distortion=[0,0,0,0,0],static=True,
            method='Median PnP initialization + static robust joints + shared table prop constraints' if sid!='S4' else 'Median PnP initialization + static robust joints + camera height bounds',
            height_prior_active=selected['height_prior_active'],horizon_center_y_px=selected['horizon_center_y_px'],
            hip_distance_m=selected['hip_distance_m'],fit_median_px=selected['median_px'],fit_median_height=selected['median_height'])
    def table(id,center,source):
        return dict(id=id,type='table',position_m=[center[0],.375,center[2]],top_center_m=[center[0],.75,center[2]],
                    dims_m=[.7,.75,.7],surface_y_m=.75,yaw_deg=0,provenance=source)
    acenter=apos+yaw(180)@np.array([0.,.75-HIP['A'],.60])
    tables=[table('table:A',acenter,'Seat/table geometry prior, tied to S7 foreground can'),
            table('table:B',[0,.75,.60],'Seat/table geometry prior; shared cup on table in S2/S5/S7'),
            table('table:empty:1',[-.80,.75,1.80],'Qualitative empty-table prior; not metrically recovered from a visible tabletop'),
            table('table:empty:2',[.85,.75,3.00],'Qualitative empty-table prior; not metrically recovered from a visible tabletop')]
    furniture=tables.copy()
    for a in ['A','B']:
        pos=actors[a]['position_m']
        furniture.append(dict(id=f'seat:{a}',type='chair',position_m=[pos[0],.225,pos[2]],
            seat_y_m=.45,dims_m=[.45,.45,.45],yaw_deg=actors[a]['yaw_deg'],provenance='seated actor support prior'))
    # These two empty seats are source-box unprojections, kept separate from the inferred empty tables.
    observations=[]
    yolo=read_json(REPO/'scen/data/d-dialog-notan/spar.json')['bilder']
    ra=read_json(REPO/'data/ra/hampuslundgren_-1779375226505.json')['sett']['ramar']
    for shot in SHOTS:
        sid=shot['id'];mid=(shot['start_frame']+shot['end_frame_exclusive']-1)/60
        yf=min((f for f in yolo if shot['start_frame']/30<=f['t']<shot['end_frame_exclusive']/30),key=lambda f:abs(f['t']-mid))
        rf=min((f for f in ra if shot['start_frame']/30<=f['t']<shot['end_frame_exclusive']/30),key=lambda f:abs(f['t']-mid))
        entries=[dict(label=o['k'],box=o['box'],confidence=o['c'],source='YOLO-World source',t=yf['t']) for o in yf['f']]
        entries += [dict(label=o['k'],box=o['b'],confidence=o['s'],source='RA EfficientDet source',t=rf['t']) for o in rf.get('saker',[]) if o['k']!='person']
        if sid in ['S1','S4','S7']:
            gd=read_json(REPO/f'scen/luma/d-dialog-notan/gemini_skikt/{sid}.json')
            for o in gd['saker']:
                if o['kategori'] in ['person','rum'] or o['etikett']=='lampa':continue
                y0,x0,y1,x1=np.array(o['box_2d'])/1000
                entries.append(dict(label=o['etikett'],box=[x0,y0,x1,y1],confidence=None,
                    source='Gemini source S7' if sid=='S7' else 'Gemini altered line-art (approximate only)',t=12. if sid=='S7' else mid))
        for ei,o in enumerate(entries):
            label=o['label'];plane=0. if label in ['chair','stol'] else .75
            if label in ['telefon','laptop','cell phone']:
                o.update(shot=sid,status='handheld: do not unproject onto floor/table');observations.append(o);continue
            x0,y0,x1,y1=o['box']
            # A table detector box includes legs/occlusion: its center is only a rough tabletop sample.
            uv=[(x0+x1)*W/2,((y0+y1)/2 if label in ['table','dining table','bord'] else y1)*H]
            world=unproject_plane(cameras[sid],uv,plane)
            owner=shot['actor'] if shot['actor'] in ['A','B'] else None
            if sid=='S7': owner='A' if label in ['burk','bottle'] or y1>.8 else 'B'
            support=next((t for t in tables if t['id']==f'table:{owner}'),None)
            inside=False
            if world is not None and support:
                inside=bool(np.all(np.abs(np.array(world)[[0,2]]-np.array(support['top_center_m'])[[0,2]])<=.35))
            o.update(id=f'{sid}:obs:{ei}',shot=sid,actor=owner,plane_y_m=plane,ray_uv_px=uv,
                world_position_m=world,on_assigned_table=inside,
                status='valid ray-plane intersection' if world is not None else 'rejected: plane behind camera or near horizon')
            observations.append(o)
            if sid=='S7' and label=='stol' and world is not None:
                furniture.append(dict(id=f'seat:empty:{ei}',type='chair',position_m=[world[0],.225,world[2]],seat_y_m=.45,
                    dims_m=[.45,.45,.45],yaw_deg=90 if world[0]<0 else -90,
                    provenance=o['id']+'; bbox bottom center projected onto floor, approximate'))
    props=[dict(id='A:can',type='drink_can',position_m=(bcan+[0,.168/2,0]).tolist(),base_position_m=bcan.tolist(),
                dims_m=[.066,.168,.066],support='table:A',provenance='shared S7/S1/S3/S6 can anchor; assumed dimensions'),
           dict(id='B:cup',type='paper_cup',base_position_m=(np.array(comparison['S7']['selected']['anchor_bases_local_m'][0])+bpos).tolist(),
                position_m=(np.array(comparison['S7']['selected']['anchor_bases_local_m'][0])+bpos+[0,.09,0]).tolist(),
                dims_m=[.10,.18,.10],support='table:B',provenance='shared S7/S2/S5 cup anchor; assumed dimensions')]
    mapping={'cup':('cup','paper_cup',[.10,.18,.10]),'sandwich':('burger','burger',[.18,.10,.18]),
             'bowl':('sauce','sauce_cup',[.07,.04,.07]),'pommes':('fries','fries_box',[.12,.10,.12]),
             'pommes i förpackning':('fries','fries_box',[.12,.10,.12]),'bricka':('tray','tray',[.45,.025,.30])}
    for actor in ['A','B']:
        for label,(short,typ,dims) in mapping.items():
            if any(p['id']==f'{actor}:{short}' for p in props):continue
            obs=[o for o in observations if o.get('actor')==actor and o['label']==label and o.get('world_position_m') and o.get('on_assigned_table')]
            if actor=='A' and label=='cup':obs=[o for o in obs if o['box'][0]>.20]
            if not obs:continue
            obs.sort(key=lambda o:('altered' in o['source'],-(o['confidence'] or 0)))
            selected=obs[0];base=np.array(selected['world_position_m'])
            props.append(dict(id=f'{actor}:{short}',type=typ,base_position_m=base.tolist(),position_m=(base+[0,dims[1]/2,0]).tolist(),
                dims_m=dims,support=f'table:{actor}',provenance=selected['id'],uncertainty='approximate silhouette-base ray on table plane; dimensions prior'))
    # Missing/occluded small props get explicit layout priors, never a false observation label.
    for actor,short,typ,offset,dims in [
        ('A','tray','tray',[0,0,0],[.45,.025,.30]),('A','fries','fries_box',[.02,0,-.10],[.12,.10,.12]),
        ('A','sauce','sauce_cup',[.23,0,.05],[.07,.04,.07]),
        ('B','fries','fries_box',[.20,0,.05],[.15,.12,.15]),('B','burger','burger',[.02,0,.04],[.18,.10,.18]),
        ('B','sauce','sauce_cup',[-.05,0,.22],[.07,.04,.07])]:
        if any(p['id']==f'{actor}:{short}' for p in props):continue
        tb=next(t for t in tables if t['id']==f'table:{actor}')
        base=np.array(tb['top_center_m'])+yaw(actors[actor]['yaw_deg'])@np.array(offset)
        props.append(dict(id=f'{actor}:{short}',type=typ,base_position_m=base.tolist(),position_m=(base+[0,dims[1]/2,0]).tolist(),
            dims_m=dims,support=f'table:{actor}',provenance='semantic presence from source; placement prior because source detection/ray was absent or inconsistent',uncertainty='high'))
    f4=data['frames'][(171+256-1)//2];wrist=np.array(f4['pose']['world'])[15,:3]
    m=np.array(actors['C']['raw_pose_to_world']);terminal=m[:3,:3]@wrist+m[:3,3]
    props.append(dict(id='C:terminal',type='card_terminal',position_m=terminal.tolist(),dims_m=[.09,.025,.16],
        attach=dict(actor='C',pose_joint=15),provenance='semantic terminal + measured wrist; approximate attachment, not floor unprojection'))
    room=dict(units='meters',up='y',floor_y=0,bounds_m=dict(x=[-2.,4.5],z=[-.7,float(apos[2]+.75)]),height_m=2.8,
              walls=[dict(id='wall:B:white',axis='z',coordinate=-.7),dict(id='wall:A:window',axis='z',coordinate=float(apos[2]+.75))],
              provenance='minimal consistent room hypothesis; outer walls, empty tables and waiter yaw are not surveyed')
    result=dict(schema='scen3d.layout.phase1.v1',units='meters',coordinates='right-handed y up; OpenCV camera x right y down z forward',
        source=dict(video='scen/klipp/d-dialog-notan.mp4',width=W,height=H,fps=30),room=room,actors=actors,
        furniture=furniture,props=props,cameras=cameras,observations=observations,
        assumptions=['Hip heights A/B .60 m, C .98 m; inferred metric skeleton scale is approximate.',
            'Square .70 m tables, .75 m top, centered .60 m in front of each seated actor.',
            'Can .168 m high, cup .18 m high; package measurements are priors.',
            'Can near front-left of A table (x=-.22,z=.90); B cup z=.80. Selected among table-compatible alternatives.',
            'C spot/yaw, walls and empty tables have no cross-shot metric registration; qualitative room hypothesis.',
            'The lens has no calibration: centered principal point, square pixels, zero distortion.'],
        limitations=['Skeleton fitting is not independent 3D ground truth.',
            'FOV at 40-degree bound in some shots remains weakly identified.',
            'Many furniture/prop boxes are clipped, include legs, or come from altered art; retain rejected observations.',
            'S7 tabletop width/edges are not fitted; table shape in source may differ from mandated .7 m square.',
            'Seated legs are intentionally excluded from calibration; S6 hands are occluded; no motion is synthesized.'],
        runtime_s=time.perf_counter()-started)
    write_json(ROOT/'data/layout.json',result)
    print('Layout',len(cameras),'cameras',len(furniture),'furniture',len(props),'props',len(observations),'ray observations',flush=True)


def unproject_plane(camera,uv,height):
    c=np.array(camera['position_m']);r=np.array(camera['world_to_camera_cv'])[:3,:3]
    direction=r.T@np.linalg.inv(np.array(camera['intrinsics_px']))@np.r_[uv,1.]
    if abs(direction[1])<1e-7:return None
    distance=(height-c[1])/direction[1]
    if distance<=0 or distance>50:return None
    return (c+distance*direction).tolist()


def project_world(camera,world):
    m=np.array(camera['world_to_camera_cv']);p=np.asarray(world)@m[:3,:3].T+m[:3,3]
    image=p@np.array(camera['intrinsics_px']).T
    return image[:,:2]/image[:,2:3],p[:,2]


def plan_image(layout):
    from PIL import Image, ImageDraw, ImageFont
    canvas=Image.new('RGB',(1500,1250),'#f7f6f2');draw=ImageDraw.Draw(canvas)
    fontpath='C:/Windows/Fonts/arial.ttf'
    font=ImageFont.truetype(fontpath,20);small=ImageFont.truetype(fontpath,16);large=ImageFont.truetype(fontpath,29)
    xmin,xmax=layout['room']['bounds_m']['x'];zmin,zmax=layout['room']['bounds_m']['z'];scale=min(1000/(xmax-xmin),1040/(zmax-zmin))
    def xy(x,z):return (55+(x-xmin)*scale,105+(z-zmin)*scale)
    draw.text((55,25),'PHASE 1 / shared restaurant plan (meters)',font=large,fill='#172432')
    draw.text((55,65),'B at far white wall; A / foreground can at bottom. Empty-table positions are priors.',font=font,fill='#465460')
    for x in np.arange(math.ceil(xmin),xmax+.1,1):
        draw.line([xy(x,zmin),xy(x,zmax)],fill='#d8d9d3');draw.text((xy(x,zmax)[0]-12,xy(x,zmax)[1]+12),str(int(x)),font=small,fill='#667078')
    for z in np.arange(math.ceil(zmin),zmax+.1,1):
        draw.line([xy(xmin,z),xy(xmax,z)],fill='#d8d9d3');draw.text((15,xy(xmin,z)[1]-8),str(int(z)),font=small,fill='#667078')
    draw.rectangle([xy(xmin,zmin),xy(xmax,zmax)],outline='#465460',width=3)
    colors=['#d25226','#00798c','#df9b17','#6d4ea2','#28a06e','#a93276','#2455c4']
    for (sid,camera),color in zip(layout['cameras'].items(),colors):
        c=np.array(camera['position_m']);r=np.array(camera['world_to_camera_cv'])[:3,:3]
        aspect=W/H;half=math.tan(math.radians(camera['vertical_fov_deg']/2))*aspect
        length=min(camera['hip_distance_m']+.2,5.5)
        points2=[]
        for sign in [-1,1]:
            direction=r.T@np.array([sign*half,0.,1.]);direction/=np.linalg.norm(direction[[0,2]])
            end=c+length*direction;points2.append(xy(end[0],end[2]))
        p=xy(c[0],c[2]);draw.line([p,points2[0]],fill=color,width=2);draw.line([p,points2[1]],fill=color,width=2)
        draw.line(points2,fill=color,width=1)
    for item in layout['furniture']:
        x,_,z=item['position_m'];dx,_,dz=item['dims_m'];p0=xy(x-dx/2,z-dz/2);p1=xy(x+dx/2,z+dz/2)
        is_table=item['type']=='table';fill='#b4c9cc' if is_table else '#d6c6ad'
        if 'empty' in item['id'] and is_table:fill='#e1e6e3'
        draw.rectangle([p0,p1],fill=fill,outline='#344b53',width=2)
        label=item['id'].replace('table:','T ').replace('seat:','seat ').replace('empty:','E')
        draw.text((p0[0]+3,p0[1]+3),label,font=small,fill='#18343c')
    for prop in layout['props']:
        if prop['id'] not in ['A:can','B:cup']:continue
        x,_,z=prop['position_m'];px,pz=xy(x,z);draw.ellipse((px-6,pz-6,px+6,pz+6),fill='#d44942',outline='white',width=1)
        draw.text((px+9,pz-5),prop['id'],font=small,fill='#9d2923')
    for actor,a in layout['actors'].items():
        x,_,z=a['position_m'];px,pz=xy(x,z)
        draw.ellipse((px-15,pz-15,px+15,pz+15),fill='#273540',outline='white',width=2)
        draw.text((px-7,pz-11),actor,font=font,fill='white')
        direction=Rotation.from_euler('y',a['yaw_deg'],degrees=True).apply([0,0,.35]);end=xy(x+direction[0],z+direction[2])
        draw.line([(px,pz),end],fill='#273540',width=3)
    for i,((sid,camera),color) in enumerate(zip(layout['cameras'].items(),colors)):
        x,y,z=camera['position_m'];px,pz=xy(x,z)
        draw.ellipse((px-7,pz-7,px+7,pz+7),fill=color,outline='white',width=2)
        offset=[(9,-28),(-54,-24),(10,10),(10,-25),(10,9),(-54,9),(10,-25)][i]
        draw.text((px+offset[0],pz+offset[1]),sid,font=font,fill=color)
        ly=140+i*106;draw.rectangle((1100,ly+4,1118,ly+22),fill=color)
        draw.text((1130,ly),f'{sid} / {camera["actor"]}',font=font,fill=color)
        draw.text((1130,ly+27),f'FOV {camera["vertical_fov_deg"]} deg | h {y:.3f} m',font=small,fill='#354651')
        draw.text((1130,ly+49),f'x {x:.2f}, z {z:.2f}',font=small,fill='#354651')
        draw.text((1130,ly+70),f'hip distance {camera["hip_distance_m"]:.2f} m',font=small,fill='#354651')
    draw.text((1100,945),'Tables: 0.70 x 0.70 m',font=font,fill='#354651')
    draw.text((1100,978),'Table tops: y = 0.75 m',font=font,fill='#354651')
    draw.text((1100,1011),'Floor: y = 0.00 m',font=font,fill='#354651')
    draw.text((1100,1060),'Frusta show horizontal FOV.',font=small,fill='#354651')
    draw.text((1100,1087),'Walls / C yaw / empty tables',font=small,fill='#354651')
    draw.text((1100,1111),'are layout assumptions.',font=small,fill='#354651')
    draw.text((55,1203),'Diagnostic plan only. No Phase 2 characters or player built.',font=font,fill='#465460')
    canvas.save(ROOT/'verifiering/plan.png')


def furniture_projection(layout):
    camera=layout['cameras']['S7'];im=get_frame(359)
    for table in [f for f in layout['furniture'] if f['type']=='table']:
        x,y,z=table['top_center_m'];corners=np.array([[x-.35,y,z-.35],[x+.35,y,z-.35],[x+.35,y,z+.35],[x-.35,y,z+.35]])
        uv,depths=project_world(camera,corners)
        if np.all(depths>.05):
            color=(0,180,255) if table['id'] in ['table:A','table:B'] else (170,170,170)
            cv2.polylines(im,[np.rint(np.clip(uv,-5000,5000)).astype(np.int32)],True,color,2,cv2.LINE_AA)
            center=uv.mean(0)
            if 0<center[0]<W and 0<center[1]<H:cv2.putText(im,table['id'],tuple(np.rint(center).astype(int)),0,.5,color,2)
    for prop in layout['props']:
        if prop['id'] not in ['A:can','B:cup']:continue
        base=np.array(prop['base_position_m']);uv,_=project_world(camera,[base,base+[0,prop['dims_m'][1],0]])
        cv2.line(im,tuple(np.rint(uv[0]).astype(int)),tuple(np.rint(uv[1]).astype(int)),(255,255,0),3)
    cv2.putText(im,'S7 table wireframes / prop anchors',(12,27),0,.62,(0,180,255),2)
    cv2.putText(im,'Grey tables are hypotheses, not detections',(12,51),0,.53,(0,180,255),2)
    # Independent manual reading of source frame 359 (roughly +/-4 px).
    # Diagnostic only: never supplied to any camera fit.
    cv2.line(im,(154,553),(497,553),(255,255,0),2,cv2.LINE_AA)
    cv2.imwrite(str(ROOT/'verifiering/S7-layout-overlay.jpg'),im)


def append_report(data,comparison,layout,result):
    lines=['## Final Phase 1 verification (serialized layout read-back)',
        'All 383 frames are extracted at 30 fps. Pose and required face channels: 383/383. '
        '103 face frames use a head ROI (57 in S4, 46 in S7); matrices retain that ROI camera convention. '
        'S6 hands are hidden behind the table and have no detections; S2 has 2 frames and S7 has 25 frames without detected hands. '
        'This is missing data, not neutral hand motion.',
        '### Camera methods and selection',
        '1. **Unconstrained PnP:** SQPnP + iterative solvePnP for each frame/FOV, then component medians '
        'of small rotation vectors and translations per static shot. FOV candidates: every degree from 40 to 85. '
        'Unconstrained heights outside the required range under the stated hip/floor prior: '+
        ', '.join(s for s,c in comparison.items() if not .9<=c['pnp_best']['height_m']<=1.7)+'.',
        '2. **Depth Anything V2:** seven measured relative inverse-depth keyframes; backproject with 40/55/70/85-degree '
        'FOV and zero / 10%-median inverse-depth offsets; scale by shot-median MediaPipe shoulder width, rigid Kabsch fit '
        'to pose (no nonrigid warp or PnP in this branch). The absolute body size is NOT known from a tape measure. '
        'Offsets, scale and gravity remain assumptions. Depth generally has higher joint error and implausible heights.',
        '3. **Height-only PnP refinement:** a single rigid static camera per shot initialized by the median; '
        'soft-L1 joint residual and camera height bounds [0.9,1.7] m. This passes the numerical tests but '
        'places all seven cameras at the lower bound and does not reconcile shared table props.',
        '4. **Selected:** static PnP refinement plus shared can/cup bottom/top anchors on y=.75 m, '
        'with declared .168 m can / .18 m cup height priors, for S1/S2/S3/S5/S6/S7. '
        'For S4 retain height-only PnP because no shared stationary prop is reliable. '
        'Choose lowest visible-joint median among FOV candidates with <=12 px maximum anchor error and successful optimizer convergence. '
        'Per-frame pose landmarks, hip positions and world cameras are never adjusted during verification.',
        'Placement alternatives were inspected before selection. A-can local z=.55 caused 58.3/91.4/128.7 px '
        'in S1/S3/S6 when anchors were enforced. At z=.75, coarse-FOV trials gave 33.2/46.9/53.8 px; '
        'z=.95 gave 25.9/31.4/33.8 px but leaves no can-radius margin at the table edge; z=1.15 lies outside the .70 m table. '
        'Selected z=.90 leaves a .05 m center-to-edge margin. B-cup z=.477 from an unconstrained S7 prop fit '
        'gave 42.7 px in S2; z=.55/.65/.80/.90 were compared (coarse best S2 errors 31.6/25.2/25.1/19.9 px). '
        'Selected z=.80 leaves room for the cup footprint; S7 was refitted with that shared location. '
        'These are explicit geometric priors selected for a consistent editable hypothesis, not independently recovered coordinates.',
        'A first shared-prop trial applied robust loss to the already weighted anchor residuals, allowing 25–148 px anchor misses. '
        'Rejected. The final implementation robustifies joints only and keeps anchor residuals quadratic; '
        'failed prior trials are reported here, not silently promoted to success.',
        '| Shot | FOV | median px | median / H | P90 px | camera y m | hip distance m | horizon y px | YOLO crosscheck px |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for sid,r in result['shots'].items():
        lines.append(f"| {sid} | {r['fov_deg']} | {r['median_px']:.3f} | {r['median_height']:.5f} | {r['p90_px']:.2f} | {r['height_m']:.3f} | {r['distance_m']:.3f} | {r['horizon_center_y_px']:.1f} | {r['yolo_crosscheck_median_px']:.2f} |")
    lines += ['', '| Shot | raw PnP FOV / px / height m | depth FOV / px / height m / distance m / horizon px | selected anchor max px |',
              '|---|---|---|---:|']
    for sid,c in comparison.items():
        p=c['pnp_best'];d=c['depth_best'];s=c['selected'];ae=s.get('anchor_max_px')
        lines.append(f"| {sid} | {p['fov_deg']} / {p['median_px']:.2f} / {p['height_m']:.3f} | {d['fov_deg']} / {d['median_px']:.2f} / {d['height_m']:.3f} / {d['hip_distance_m']:.3f} / {d['horizon_center_y_px']:.1f} | {ae:.3f} |" if ae is not None else
            f"| {sid} | {p['fov_deg']} / {p['median_px']:.2f} / {p['height_m']:.3f} | {d['fov_deg']} / {d['median_px']:.2f} / {d['height_m']:.3f} / {d['hip_distance_m']:.3f} / {d['horizon_center_y_px']:.1f} | n/a |")
    lines += ['', '### Acceptance and practical limits',
        f"Computed acceptance: `{result['acceptance']}`. Distances: `{result['distances']}`.",
        'The error is the median Euclidean pixel distance over all evaluated joints/frames, divided by 1024. '
        'Visible anatomical joints only: nose, ears, shoulders/elbows/wrists/hand pose tips; standing hips/legs when visibility and presence >=.65 and within frame. '
        'Seated hips and legs behind tables, seated wrists/tips without independently detected matching hands, redundant eye/mouth points, low-confidence and out-of-frame landmarks are excluded. '
        'This is an in-sample 2D consistency check of MediaPipe 3D against MediaPipe 2D. '
        'The YOLO column is a separate-detector crosscheck at original 10 fps timestamps; it is not manual ground truth.',
        'The floor plan has separate A/B tables, A/B seats, waiter spot, two empty tables between, '
        'and every camera frustum. S7 starts at A’s table with the can in front and B farther away. '
        'Empty table coordinates, room walls and C’s cross-shot yaw/position are qualitative priors. '
        'Inspect S7-layout-overlay.jpg: the mandatory .70 m square tables do not fully reproduce source tabletop boundaries. '
        'Thus qualitative S7 plan ordering passes; precise furniture reconstruction is unresolved.',
        'S4 camera height is constraint-limited at .900 m. Search-bound FOVs: '+
        ', '.join(s for s,c in layout['cameras'].items() if c['vertical_fov_deg'] in [40,85])+'. '
        'focal length, hip/floor scale and depth are not uniquely calibrated. No camera sensor data or measured actor heights are available. '
        'Depth cannot resolve scale/shift by itself. A can/cup height or seat placement error changes the metric result.',
        'All ray-plane observations, including rejected and off-table positions, remain in layout.json with provenance. '
        'Source YOLO/RA detections are preferred. S1/S4 Gemini art boxes are approximate only; S7 boxes are source-based. '
        'Prop priors are explicit where detections do not support a location; handheld terminal uses a measured wrist attachment. '
        'No false claim of recovered occluded geometry, hands, or metric room truth.',
        '### Reproduction, runtimes and artifacts',
        '```powershell\nscen/.venv/Scripts/python.exe -B scen/3d/fas1.py extract\nscen/.venv/Scripts/python.exe -B scen/3d/fas1.py depth\nscen/.venv/Scripts/python.exe -B scen/3d/fas1.py solve\nscen/.venv/Scripts/python.exe -B scen/3d/fas1.py layout\nscen/.venv/Scripts/python.exe -B scen/3d/fas1.py verify\n```',
        'For image/layout iteration without refitting: `... fas1.py layout --reuse`, then `... fas1.py verify`.',
        f"Latest runtimes (CPU): extraction {data['runtime_s']:.2f} s; depth {read_json(ROOT/'data/depth-metadata.json')['runtime_s']:.2f} s; "
        f"PnP/depth comparison {read_json(ROOT/'data/camera-comparison.json')['runtime_s']:.2f} s; shared-prop refinement {read_json(ROOT/'data/layout-comparison.json')['runtime_s']:.2f} s; "
        f"assembly {layout['runtime_s']:.2f} s; verification/images {result['runtime_s']:.2f} s. Runtimes exclude exploratory retries.",
        '- `data/sparning.json`: complete per-frame motion, face and hand measurements, shot assignment, coverage and model hashes.',
        '- `data/layout.json`: room, actors, furniture, semantic props, static cameras and all placement observations.',
        '- `data/camera-comparison.json`, `data/layout-comparison.json`: full FOV grids, alternate methods, per-frame errors and priors.',
        '- `data/verification.json`: read-back projection metrics, per-joint errors, acceptance checks and plan distances.',
        '- `verifiering/fas1.jpg`: 21 overlays (start / middle / final source frame of each shot).',
        '- `verifiering/plan.png`: all cameras/frusta, tables, seats and actors in one room.',
        '- `verifiering/S1-overlay.jpg` … `S7-overlay.jpg`: full-resolution shot sheets; `S*-frame-*.jpg`: individual frames.',
        '- `verifiering/extraction.jpg`: actor/hand/face extraction audit; `S*-depth.jpg`: source versus relative depth.',
        '- `verifiering/S7-layout-overlay.jpg`: table-wireframe diagnostic exposing unresolved furniture edges.',
        'Only Phase 1 implemented. No Three.js, character renderer, player, semantic edit operations, or Phase 2/3 artifacts.']
    log('\n\n'.join(lines[:3])+'\n\n'+'\n'.join(lines[3:]))


def verify():
    started=time.perf_counter();layout=read_json(ROOT/'data/layout.json');data=read_json(ROOT/'data/sparning.json')
    assert len(data['frames'])==383 and data['fps']==30
    required={'jawOpen','mouthSmileLeft','mouthSmileRight','browDownLeft','browDownRight','browInnerUp','eyeBlinkLeft','eyeBlinkRight'}
    for n,f in enumerate(data['frames']):
        assert f['frame']==n and abs(f['t']-n/30)<1e-8
        assert len(f['pose']['image'])==len(f['pose']['world'])==33
        assert required<=set(f['face']['blendshapes'])
        for hand in f['hands']:assert len(hand['image'])==len(hand['world'])==21
        rot=np.array(f['face']['head_rotation_matrix'])
        assert np.allclose(rot.T@rot,np.eye(3),atol=1e-5)
    for camera in layout['cameras'].values():
        mat=np.array(camera['world_to_camera_cv']);inverse=np.array(camera['camera_to_world_cv'])
        assert np.allclose(mat@inverse,np.eye(4),atol=1e-8)
        assert np.allclose(mat[:3,:3].T@mat[:3,:3],np.eye(3),atol=1e-8)
        assert np.linalg.det(mat[:3,:3])>.99999
        uv=[W*.42,H*.88];world=unproject_plane(camera,uv,0.)
        if world is not None:
            reproj,_=project_world(camera,[world]);assert np.allclose(reproj[0],uv,atol=1e-7)
    comparison=read_json(ROOT/'data/layout-comparison.json')['shots'];yolo=read_json(REPO/'scen/data/d-dialog-notan/spar.json')['bilder']
    report={};rows=[];extraction=[]
    mapping=[(0,0),(11,5),(12,6),(13,7),(14,8),(15,9),(16,10)]
    for shot in SHOTS:
        sid=shot['id'];camera=layout['cameras'][sid];actor=layout['actors'][shot['actor']]
        transform=np.array(actor['raw_pose_to_world']);frames=[f for f in data['frames'] if f['shot']==sid]
        all_error=[];per_frame=[];independent=[];core_errors=[]
        for f in frames:
            p=points(f)
            if p is None:continue
            world=p[0]@transform[:3,:3].T+transform[:3,3]
            projected,z=project_world(camera,world)
            assert np.all(z>0),f'{sid}: joint behind camera'
            e=np.linalg.norm(projected-p[1],axis=1);all_error.extend(e.tolist())
            core_errors.extend([float(error) for index,error in zip(p[2],e) if index in [0,11,12,13,14,15,16]])
            per_frame.append(dict(frame=f['frame'],joints=p[2].tolist(),error_px=e.tolist(),median_px=float(np.median(e))))
            yf=min(yolo,key=lambda yf:abs(yf['t']-f['t']))
            if abs(yf['t']-f['t'])<.017 and yf['p']:
                person=max(yf['p'],key=lambda p:(p['box'][2]-p['box'][0])*(p['box'][3]-p['box'][1]))
                kp=np.array(person['kp']);allworld=np.array(f['pose']['world'])[:,:3]@transform[:3,:3].T+transform[:3,3]
                projectedall,_=project_world(camera,allworld)
                for mi,yi in mapping:
                    if mi in p[2] and kp[yi,2]>=.65:
                        independent.append(float(np.linalg.norm(projectedall[mi]-kp[yi,:2]*[W,H])))
        med=float(np.median(all_error));samples=[shot['start_frame'],(shot['start_frame']+shot['end_frame_exclusive']-1)//2,shot['end_frame_exclusive']-1]
        assert abs(med-camera['fit_median_px'])<1e-6,'Serialized projection disagrees with camera solve'
        report[sid]=dict(actor=shot['actor'],frames=len(frames),evaluated_joints=len(all_error),median_px=med,median_height=med/H,
            p90_px=float(np.percentile(all_error,90)),fov_deg=camera['vertical_fov_deg'],height_m=camera['position_m'][1],
            distance_m=camera['hip_distance_m'],horizon_center_y_px=camera['horizon_center_y_px'],
            yolo_crosscheck_median_px=float(np.median(independent)) if independent else None,yolo_joint_count=len(independent),
            sample_frames=samples,frame_results=per_frame,pass_error=med/H<=.04,pass_height=.9-1e-6<=camera['position_m'][1]<=1.7+1e-6)
        report[sid]['core_joint_median_px']=float(np.median(core_errors))
        report[sid]['max_frame_median_px']=max(f['median_px'] for f in per_frame)
        tiles=[];full=[]
        for n in samples:
            f=data['frames'][n];im=get_frame(n);p=points(f)
            allworld=np.array(f['pose']['world'])[:,:3]@transform[:3,:3].T+transform[:3,3]
            projected,_=project_world(camera,allworld);observed=np.array(f['pose']['image'])[:,:2]*[W,H];valid=set(p[2])
            for a,b in EDGES:
                if a in valid and b in valid:
                    cv2.line(im,tuple(np.rint(projected[a]).astype(int)),tuple(np.rint(projected[b]).astype(int)),(0,150,255),3,cv2.LINE_AA)
            for i in valid:
                cv2.line(im,tuple(np.rint(projected[i]).astype(int)),tuple(np.rint(observed[i]).astype(int)),(220,220,220),1,cv2.LINE_AA)
                cv2.circle(im,tuple(np.rint(observed[i]).astype(int)),5,(255,255,0),1,cv2.LINE_AA)
                cv2.circle(im,tuple(np.rint(projected[i]).astype(int)),3,(0,150,255),-1,cv2.LINE_AA)
            e=next(x['median_px'] for x in per_frame if x['frame']==n)
            header=np.full((86,W,3),25,np.uint8)
            cv2.putText(header,f'{sid} {shot["actor"]}  frame {n}  {n/30:.3f}s',(12,25),0,.65,(255,255,255),1,cv2.LINE_AA)
            cv2.putText(header,f'{e:.2f}px / {e/H:.4f}H   FOV {camera["vertical_fov_deg"]}  h={camera["position_m"][1]:.3f}m',(12,49),0,.55,(255,255,255),1,cv2.LINE_AA)
            cv2.putText(header,'orange: projected 3D   cyan: observed 2D',(12,73),0,.55,(255,255,255),1,cv2.LINE_AA)
            annotated=np.vstack([header,im]);cv2.imwrite(str(ROOT/'verifiering'/f'{sid}-frame-{n:03d}.jpg'),annotated)
            full.append(annotated);tiles.append(cv2.resize(annotated,(W//2,(H+86)//2)))
        cv2.imwrite(str(ROOT/'verifiering'/f'{sid}-overlay.jpg'),np.hstack(full))
        rows.append(np.hstack(tiles))
        n=samples[1];im=get_frame(n);f=data['frames'][n]
        for p in f['pose']['image']:
            if p[3]>=.65:cv2.circle(im,(int(p[0]*W),int(p[1]*H)),4,(0,255,0),-1)
        for hand in f['hands']:
            for p in hand['image']:cv2.circle(im,(int(p[0]*W),int(p[1]*H)),3,(255,255,0),-1)
        fp=f['face']['nose_image'];cv2.circle(im,(int(fp[0]*W),int(fp[1]*H)),9,(0,0,255),2)
        cv2.putText(im,f'{sid} / {shot["actor"]} / pose, hand, face',(10,27),0,.65,(0,255,255),2)
        extraction.append(cv2.resize(im,(288,512)))
    cv2.imwrite(str(ROOT/'verifiering/fas1.jpg'),np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,92])
    cv2.imwrite(str(ROOT/'verifiering/extraction.jpg'),np.hstack(extraction))
    plan_image(layout)
    furniture_projection(layout)
    a=np.array(layout['actors']['A']['position_m']);b=np.array(layout['actors']['B']['position_m']);c7=np.array(layout['cameras']['S7']['position_m'])
    ta=np.array(next(t['top_center_m'] for t in layout['furniture'] if t['id']=='table:A'))
    distances=dict(actor_A_B_m=float(np.linalg.norm((a-b)[[0,2]])),S7_to_A_table_m=float(np.linalg.norm((c7-ta)[[0,2]])),
        S7_to_B_hip_m=float(np.linalg.norm(c7-b)),empty_tables_between=int(sum(t['id'].startswith('table:empty') and b[2]<t['top_center_m'][2]<a[2] for t in layout['furniture'])))
    acceptance=dict(joint_errors_S1_S6=all(report[f'S{i}']['pass_error'] for i in range(1,7)),
        heights_all_shots=all(r['pass_height'] for r in report.values()),
        S7_plan_ordering=distances['actor_A_B_m']>2.5 and distances['S7_to_A_table_m']<1. and distances['empty_tables_between']>=2)
    result=dict(shots=report,acceptance=acceptance,distances=distances,
        criteria='Median over visible anatomical joints and all source frames; 0.04H = 40.96 px. Height [0.9,1.7] m. Plan ordering qualitative.',
        evaluation='Projection of unchanged metric landmarks through serialized actor/world/camera transforms. In-sample model consistency, not independent metric ground truth.',
        excluded='Seated hips/legs occluded by table; seated wrists/tips without independently detected matching hand; visibility/presence <.65; out-of-frame points; redundant eye/mouth pose markers.',
        runtime_s=time.perf_counter()-started)
    edge=np.array([[-.35,.75,.95],[.35,.75,.95]])
    edge_uv,_=project_world(layout['cameras']['S7'],edge)
    source_edge=np.array([[154.,553.],[497.,553.]])
    result['furniture_diagnostic']=dict(shot='S7',frame=359,source_edge_px=source_edge.tolist(),
        projected_edge_px=edge_uv.tolist(),corner_errors_px=np.linalg.norm(edge_uv-source_edge,axis=1).tolist(),
        provenance='Manual approximate source front table corners, +/-4 px; held out of all fits.',
        status='Unresolved tabletop mismatch. Qualitative plan ordering passes; metric furniture is not verified.')
    import hashlib
    import importlib.metadata
    sources=['scen/klipp/d-dialog-notan.mp4','data/ra/hampuslundgren_-1779375226505.json',
        'scen/data/d-dialog-notan/spar.json','scen/luma/d-dialog-notan/gemini_skikt/S7.json',
        'scen/luma/d-dialog-notan/gemini_skikt/S1.json','scen/luma/d-dialog-notan/gemini_skikt/S4.json']
    versions={name:importlib.metadata.version(name) for name in ['numpy','scipy','torch','transformers','mediapipe','pillow']}
    write_json(ROOT/'data/provenance.json',dict(versions=versions,opencv=cv2.__version__,
        sources={s:dict(sha256=hashlib.sha256((REPO/s).read_bytes()).hexdigest(),bytes=(REPO/s).stat().st_size) for s in sources},
        official_references=['https://github.com/DepthAnything/Depth-Anything-V2',
          'https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker',
          'https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python']))
    write_json(ROOT/'data/verification.json',result)
    append_report(data,comparison,layout,result)
    print(json.dumps(dict(acceptance=acceptance,distances=distances,shots={s:{k:r[k] for k in ['median_px','median_height','height_m','fov_deg','yolo_crosscheck_median_px']} for s,r in report.items()}),indent=2),flush=True)
