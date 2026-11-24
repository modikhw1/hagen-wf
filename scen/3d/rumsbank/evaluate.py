"""Bounded numpy/OpenCV measurements only. No model or ingest imports."""
import argparse,json,math,os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
from pathlib import Path
import cv2,numpy as np
from scipy.spatial.transform import Rotation,Slerp

BANK=Path(__file__).resolve().parent
ROOT=BANK.parents[2]
cv2.setNumThreads(1)

def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def angle(a,b):return np.degrees(np.arccos(np.clip((np.einsum('...ij,...ij->...',a,b)-1)/2,-1,1)))
def stats(a):
    a=np.asarray(a);a=a[np.isfinite(a)]
    return dict(n=len(a),median=float(np.median(a)),p90=float(np.percentile(a,90)),min=float(a.min()),max=float(a.max())) if len(a) else None
def load(p):
    with np.load(p) as d:return {k:d[k].squeeze() for k in d.files}
def pc(d,K,uv):
    uv=np.asarray(uv);z=d[np.clip(uv[:,1].astype(int),0,d.shape[0]-1),np.clip(uv[:,0].astype(int),0,d.shape[1]-1)]
    return np.c_[(uv[:,0]-K[0,2])/K[0,0]*z,(uv[:,1]-K[1,2])/K[1,1]*z,z]
def world(d,uv):return pc(d['depth_z'],d['intrinsics'],uv)@d['camera_poses'][:3,:3].T+d['camera_poses'][:3,3]
def project(x,d):
    x=(np.asarray(x)-d['camera_poses'][:3,3])@d['camera_poses'][:3,:3];uv=x[:,:2]/np.maximum(x[:,2:],1e-8);uv=uv*np.diag(d['intrinsics'])[:2]+d['intrinsics'][:2,2];return uv,x[:,2]

# Normalized polygons chosen after visually inspecting eight ORIGINAL frames, before model overlays.
# They describe visible surface patches, not complete objects. Person pixels are removed separately.
ROIS={
 'notan_S1':dict(table=[(.08,.88),(.92,.88),(.92,.99),(.08,.99)],wall=[(.025,.27),(.14,.27),(.14,.43),(.025,.43)]),
 'notan_S4':dict(floor=[(.64,.68),(.78,.68),(.77,.96),(.60,.96)],wall=[(.79,.34),(.98,.34),(.98,.59),(.79,.59)]),
 'pool':dict(floor=[(.02,.78),(.20,.78),(.24,.98),(.02,.98)],table=[(.75,.535),(.98,.535),(.98,.57),(.75,.57)]),
 'b_S5':dict(wall=[(.025,.07),(.29,.07),(.29,.28),(.025,.28)]),
 'b_closeup':dict(wall=[(.015,.04),(.20,.04),(.20,.26),(.015,.26)]),
 'kenny_S2':dict(table=[(.04,.70),(.35,.70),(.35,.85),(.04,.85)]),
}

def plane(points):
    p=points[np.isfinite(points).all(1)]
    if len(p)<40:return None
    rng=np.random.default_rng(13);p=p[rng.choice(len(p),min(600,len(p)),replace=False)]
    best=None
    for _ in range(96):
        a,b,c=p[rng.choice(len(p),3,replace=False)];n=np.cross(b-a,c-a);length=np.linalg.norm(n)
        if length<1e-8:continue
        n/=length;off=-n@a;inlier=np.abs(p@n+off)<.035
        if best is None or inlier.sum()>best.sum():best=inlier
    if best is None or best.sum()<30:return None
    pts=p[best];mean=pts.mean(0);_,_,vt=np.linalg.svd(pts-mean,full_matrices=False);n=vt[-1];off=-n@mean
    return dict(normal=n,offset=off,center=mean,points=pts,rms_m=float(np.sqrt(np.mean((pts@n+off)**2))),support_fraction=float(best.mean()))

def surface(d,poly,mask):
    h,w=d['depth_z'].shape;roi=np.zeros((h,w),np.uint8);cv2.fillPoly(roi,[np.rint(np.array(poly)*[w,h]).astype(np.int32)],1)
    valid=(roi>0)&~mask&np.isfinite(d['depth_z'])&(d['depth_z']>.05)&(d['depth_z']<40)
    yy,xx=np.where(valid);uv=np.c_[xx[::4],yy[::4]]
    return plane(world(d,uv)) if len(uv)>=40 else None

def box_edges(p):
    pts=p['points'];n=p['normal'];a=np.array([1.,0,0]);a-=n*(a@n)
    if np.linalg.norm(a)<.1:a=np.cross(n,[0.,1.,0.])
    a/=np.linalg.norm(a);b=np.cross(n,a);B=np.stack([a,b,n]);q=(pts-p['center'])@B.T;lo,hi=np.percentile(q,[5,95],axis=0);lo[2]=-.025;hi[2]=.025
    v=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])@B+p['center']
    return [(v[i],v[j]) for i in range(8) for j in range(i+1,8) if bin(i^j).count('1')==1]
def grid_edges(p):
    n=p['normal'];a=np.array([1.,0,0]);a-=n*(a@n);a/=np.linalg.norm(a);b=np.cross(n,a);o=p['center']
    return [(o+a*x-b*2,o+a*x+b*2) for x in np.arange(-2,2.01,.5)]+[(o+b*y-a*2,o+b*y+a*2) for y in np.arange(-2,2.01,.5)]
def draw_edges(im,edges,d,color):
    h,w=im.shape[:2]
    for a,b in edges:
        uv,z=project(np.array([a,b]),d)
        if np.min(z)<.05 or not np.isfinite(uv).all() or np.max(np.abs(uv))>1e6:continue
        ok,p,q=cv2.clipLine((0,0,w,h),tuple(np.rint(uv[0]).astype(int)),tuple(np.rint(uv[1]).astype(int)))
        if ok:cv2.line(im,p,q,color,1,cv2.LINE_AA)

def crop_mask(mask,hw):
    # Match upstream center-crop aspect mapping; at portrait ratios this removes <= 1%.
    h,w=hw;mh,mw=mask.shape;s=max(w/mw,h/mh);rw,rh=round(mw*s),round(mh*s)
    a=cv2.resize(mask.astype(np.uint8),(rw,rh),interpolation=cv2.INTER_NEAREST);top=(rh-h)//2;left=(rw-w)//2
    return a[top:top+h,left:left+w]>0

def frame_context(job,index):
    frame=job['frames'][index]
    if 'inputs' in job:
        item=job['inputs'][index];shot=item['shot'];frame=item['frame'];folder=ROOT/'scen/3d/ingest/ut/notan-tagningar'/('S1' if shot=='notan_S1' else 'S4')
    elif job['id'] in ['notan_uncut','notan_fullrate']:
        start=0;shot=None;folder=None
        for sid,count in [(1,73),(2,41),(3,57),(4,85),(5,25),(6,56),(7,46)]:
            if start<=frame<start+count:
                frame-=start;folder=ROOT/'scen/3d/ingest/ut/notan-tagningar'/f'S{sid}';shot='notan_S1' if sid in [1,3,6] else 'notan_S4' if sid==4 else 'notan_other';break
            start+=count
    else:shot='pool' if job['id'] in ['pool_fullrate','pool_visible','pool_core'] else job['id'];folder=ROOT/job['reference'] if job.get('reference') else None
    return shot,folder,frame

def background_reprojection(ds,images,indices,chosen,job,valid):
    sift=cv2.SIFT_create(nfeatures=700);features={};cache={}
    for i in chosen:
        if not valid[i]:continue
        _,folder,frame=frame_context(job,indices[i]);h,w=images[i].shape[:2]
        mp=folder/'masker.npy' if folder else None
        if mp and mp.exists():
            key=str(mp)
            if key not in cache:cache[key]=np.load(mp,mmap_mode='r')
            mk=crop_mask(cache[key][frame]>0,(h,w))
        else:mk=np.zeros((h,w),bool)
        bg=(~cv2.dilate(mk.astype(np.uint8),np.ones((9,9),np.uint8)).astype(bool)).astype(np.uint8)*255
        # Burned-in TikTok captions are not fixed points in the physical room.
        # These source-inspected bands are evaluation masks, not a new model.
        band=(.46,.66) if job['id'].startswith('b_') else (.61,.68) if job['id'].startswith('pool') else (.49,.66) if job['id'].startswith('kenny') else (.50,.64)
        bg[round(h*band[0]):round(h*band[1])]=0
        k,d=sift.detectAndCompute(cv2.cvtColor(images[i],cv2.COLOR_BGR2GRAY),bg);features[i]=(k,d)
    pairs=[];failed_pairs=[]
    for a,b in zip(chosen[:-1],chosen[1:]):
        if a not in features or b not in features:continue
        ka,da=features[a];kb,db=features[b]
        if da is None or db is None or len(da)<8 or len(db)<8:continue
        matches=[m for m,n in cv2.BFMatcher().knnMatch(da,db,k=2) if m.distance<.72*n.distance]
        if len(matches)<8:continue
        ua=np.array([ka[m.queryIdx].pt for m in matches]);ub=np.array([kb[m.trainIdx].pt for m in matches])
        try:_,inl=cv2.findFundamentalMat(ua,ub,cv2.USAC_MAGSAC,1.0,.999)
        except cv2.error as error:
            failed_pairs.append(dict(first=job['frames'][indices[a]],second=job['frames'][indices[b]],error=str(error)))
            continue
        if inl is None:continue
        keep=inl.ravel()>0;ua=ua[keep];ub=ub[keep]
        if len(ua)<8:continue
        uv,z=project(world(ds[a],ua),ds[b]);error=np.linalg.norm(uv-ub,axis=1);error=error[(z>.05)&np.isfinite(error)]
        pairs.append(dict(first=job['frames'][indices[a]],second=job['frames'][indices[b]],matches=len(ua),error_px=stats(error)))
    allmed=[p['error_px']['median'] for p in pairs if p['error_px']]
    return dict(pair_median_px=stats(allmed),pairs=pairs,failed_pairs=failed_pairs,note='SIFT ratio test + MAGSAC epipolar inliers outside person masks and manually identified caption bands; moving props are not explicitly segmented. Candidate depth + cameras reproject frame a points into b. Units are model-input pixels; cut pairs may have no shared features. Degenerate OpenCV epipolar fits are reported in failed_pairs, never treated as zero error.')

def camera_metrics(ds,indices,job,valid):
    P=np.stack([d['camera_poses'] for d in ds]);K=np.stack([d['intrinsics'] for d in ds]);C=P[:,:3,3];R=P[:,:3,:3]
    fov=np.degrees(2*np.arctan(ds[0]['depth_z'].shape[1]/(2*K[:,0,0])))
    good=np.flatnonzero(valid);Cg=C[good];Rg=R[good];ts=np.array([job['frames'][i] for i in indices],float)/(job.get('fps') or 30)
    span=float(np.max(np.linalg.norm(Cg[:,None]-Cg[None,:],axis=2))) if len(good) else None
    step=np.linalg.norm(np.diff(Cg,axis=0),axis=1);dt=np.diff(ts[good]);speeds=step/np.maximum(dt,1e-6)
    vel=np.diff(Cg,axis=0)/np.maximum(dt[:,None],1e-6);acc=np.linalg.norm(np.diff(vel,axis=0),axis=1)/np.maximum((dt[:-1]+dt[1:])/2,1e-6)
    result=dict(path_m=float(step.sum()),diameter_m=span,rotation_from_first_deg=stats(angle(np.broadcast_to(Rg[0],Rg.shape),Rg)) if len(good) else None,speed_m_s=stats(speeds),acceleration_m_s2=stats(acc),horizontal_fov_deg=stats(fov[valid]),focal_relative_range_pct=float(100*np.ptp(K[valid,0,0])/np.median(K[valid,0,0])),reference=None)
    if not job.get('reference'):return result
    folder=ROOT/job['reference'];cp=folder/'kamera.json'
    if not cp.exists():result['reference']='Ingen kamera.json; statisk reservkamera är ingen COLMAP-mätning';return result
    col=json.loads(cp.read_text());accepted=col.get('registrerade',0)>=8 and col.get('registrerade',0)/max(1,col.get('av',1))>=.5 and col.get('fel_px',100)<=1
    pose=col.get('pose',{});observed=sorted((int(k),v) for k,v in pose.items());result['reference']=dict(accepted_numeric_camera_criteria=accepted,registered=col.get('registrerade'),total=col.get('av'),reprojection_px=col.get('fel_px'),translation_metric_ground_truth=False)
    if not accepted or len(observed)<2:return result
    # Compare only within registered temporal support. No endpoint-hold extrapolation.
    sf=np.array([x[0] for x in observed]);rf=np.array([job['frames'][i] for i in indices]);sel=valid&(rf>=sf[0])&(rf<=sf[-1]);which=np.flatnonzero(sel)
    if len(which)<2:return result
    cr=np.array([v[0] for _,v in observed]);cc=np.array([v[1] for _,v in observed]);rr=Slerp(sf,Rotation.from_matrix(cr))(rf[sel]).as_matrix();ct=np.stack([np.interp(rf[sel],sf,cc[:,k]) for k in range(3)],1)
    pp=R[sel];Q=rr[0]@pp[0].T;aligned=np.einsum('ij,njk->nik',Q,pp);err=angle(aligned,rr)
    dc=ct[-1]-ct[0];dp=Q@(C[which[-1]]-C[which[0]]);den=np.linalg.norm(dc)*np.linalg.norm(dp)
    direction=float(np.degrees(np.arccos(np.clip(dp@dc/den,-1,1)))) if den>1e-8 else None
    fokal=col['fokal_px']*ds[0]['depth_z'].shape[0]/job['height']
    result['reference'].update(comparison_frames=len(which),rotation_deg=stats(err),translation_endpoint_direction_deg=direction,focal_difference_pct=float(100*(np.median(K[sel,1,1])/fokal-1)),translation_note='COLMAP up-to-scale; translation direction uses first-pose rotation alignment, no fitted similarity rotation')
    return result

def body_depth(folder,frame,d,mask,meta):
    ratios=[];records=[];h,w=d['depth_z'].shape
    for person in (folder/'kropp').iterdir() if (folder/'kropp').exists() else []:
        p=person/f'{frame:04d}.npz'
        if not p.exists():continue
        raw=load(p);verts=raw.get('pred_vertices');ct=raw.get('pred_cam_t')
        if verts is None or ct is None:continue
        # Independent surface depths, projected with the body model's own focal.
        v=verts[::3]+ct;f=float(raw['focal_length']);uv=v[:,:2]/v[:,2:]*f+[meta['bredd']/2,meta['hojd']/2]
        # Same center crop as RGB preprocessing.
        s=max(w/meta['bredd'],h/meta['hojd']);uv=uv*s-[(meta['bredd']*s-w)/2,(meta['hojd']*s-h)/2]
        xx,yy=np.rint(uv).astype(int).T;inside=(xx>=0)&(xx<w)&(yy>=0)&(yy<h)&(v[:,2]>.05)
        xx,yy,zz=xx[inside],yy[inside],v[inside,2]
        if len(xx)<30:continue
        # Z-buffer suppresses back-side mesh depths, no local model operations.
        depth=np.full((h,w),np.inf);np.minimum.at(depth,(yy,xx),zz)
        keep=np.isfinite(depth)&mask&np.isfinite(d['depth_z'])&(d['depth_z']>.05)
        if keep.sum()<30:continue
        r=d['depth_z'][keep]/depth[keep];median=float(np.median(r));ratios.append(median)
        records.append(dict(frame=frame,person=person.name,pixels=int(keep.sum()),model_to_body_depth_ratio=median,body_depth_m=float(np.median(depth[keep])),candidate_depth_m=float(np.median(d['depth_z'][keep])),body_height_m=float(np.ptp(verts[:,1])),raw_focal_px=f))
    return ratios,records

def run(candidate):
    manifest=json.loads((BANK/('baseline_manifest.json' if candidate=='baseline' else 'manifest.json')).read_text(encoding='utf-8'));results=[]
    for job in manifest:
        dest=BANK/'ut'/candidate/job['id']
        if not (dest/'timing.json').exists():continue
        timing=json.loads((dest/'timing.json').read_text(encoding='utf-8'))
        if timing.get('status')=='did_not_run':results.append(dict(shot=job['id'],status='did_not_run',error=timing.get('error')));continue
        indices=timing.get('indices',list(range(len(job['frames']))));paths=[dest/f'{i:05d}.npz' for i in range(len(indices))]
        ds=[]
        for p in paths:
            with np.load(p) as raw:ds.append({k:raw[k].squeeze() for k in ['depth_z','intrinsics','camera_poses','conf'] if k in raw})
        valid=[];images=[]
        for i in range(len(ds)):
            im=cv2.imread(str(dest/f'{i:05d}.jpg'));images.append(im);valid.append(np.mean(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)>12)>.15)
        valid=np.array(valid)
        evaluation_origin=ds[int(np.flatnonzero(valid)[0])]['camera_poses'][:3,3].copy()
        for d in ds:d['camera_poses'][:3,3]-=evaluation_origin
        camera=camera_metrics(ds,indices,job,valid)
        folder=ROOT/job['reference'] if job.get('reference') else None
        masks=np.load(folder/'masker.npy',mmap_mode='r') if folder and (folder/'masker.npy').exists() else None
        meta=json.loads((folder/'meta.json').read_text()) if folder else None
        surfaces={};ratios=[];body=[];floor_per_frame=[];notes=[];tiles=[]
        chosen=[i for i,ind in enumerate(indices) if job['frames'][ind] in job['overlay_frames']]
        if not chosen:chosen=np.rint(np.linspace(0,len(ds)-1,8)).astype(int).tolist()
        for i in chosen:
            d=ds[i];frame=job['frames'][indices[i]];h,w=d['depth_z'].shape
            mk=crop_mask(masks[frame]>0,(h,w)) if masks is not None else np.zeros((h,w),bool)
            shot,local_folder,local_frame=frame_context(job,indices[i])
            if local_folder and (not folder or local_folder!=folder):
                mp=local_folder/'masker.npy'
                if mp.exists():mk=crop_mask(np.load(mp,mmap_mode='r')[local_frame]>0,(h,w))
            rois=ROIS.get(shot,{})
            if valid[i]:
                for kind,poly in rois.items():
                    fitted=surface(d,poly,mk)
                    if fitted:
                        if kind not in surfaces:surfaces[kind]=fitted
                        if kind=='floor':floor_per_frame.append((frame,fitted))
                if folder:
                    r,records=body_depth(folder,frame,d,mk,meta);ratios.extend(r);body.extend(records)
        if not floor_per_frame:notes.append('Golv saknar synligt, mätbart stöd i valda rutor; ingen kamerahöjd antas.')
        stability=None
        if floor_per_frame:
            ns=np.array([p['normal'] for _,p in floor_per_frame]);offs=np.array([p['offset'] for _,p in floor_per_frame]);ref=ns[0];signs=np.sign(ns@ref);ns*=signs[:,None];offs*=signs
            mean=np.median(ns,axis=0);mean/=np.linalg.norm(mean);angles=np.degrees(np.arccos(np.clip(ns@mean,-1,1)))
            stability=dict(frames=len(ns),temporal_stability_verified=len(ns)>=2,normal_variation_deg=stats(angles),offset_range_cm=float(np.ptp(offs)*100) if len(ns)>=2 else None,offset_mad_cm=float(np.median(np.abs(offs-np.median(offs)))*100) if len(ns)>=2 else None,surface_rms_cm=stats([p['rms_m']*100 for _,p in floor_per_frame]),per_frame=[dict(frame=f,normal=p['normal'].tolist(),offset=p['offset'],rms_m=p['rms_m'],support_fraction=p['support_fraction']) for f,p in floor_per_frame],note='World-plane stability on manually selected visible floor patches, people masked; origin is first valid camera. No gravity or camera-height prior. One frame cannot establish temporal stability.')
        # A joint-room sanity check: floor from S4, table patch from S1.
        joint_height=None
        if 'inputs' in job and 'table' in surfaces and 'floor' in surfaces:
            fl=surfaces['floor'];tb=surfaces['table'];height=abs(fl['normal']@tb['center']+fl['offset']);joint_height=dict(table_height_m=float(height),prior_range_m=[.72,.76],deviation_from_074_pct=float(100*(height/.74-1)),note='Furniture prior, not surveyed ground truth')
        for i in chosen:
            d=ds[i];im=images[i].copy();frame=job['frames'][indices[i]]
            if valid[i]:
                if 'floor' in surfaces:draw_edges(im,grid_edges(surfaces['floor']),d,(255,255,0))
                for kind,p in surfaces.items():
                    if kind!='floor':draw_edges(im,box_edges(p),d,(0,255,0) if kind=='table' else (0,150,255))
            title=f'{candidate} {job["id"]} f{frame}'
            cv2.putText(im,title,(4,18),0,.42,(0,255,255),1,cv2.LINE_AA)
            if 'floor' not in surfaces:cv2.putText(im,'FLOOR: NO VISIBLE SUPPORT',(4,h-12),0,.38,(0,255,255),1,cv2.LINE_AA)
            if not valid[i]:cv2.putText(im,'BLACK FRAME: INVALID',(4,h//2),0,.5,(0,0,255),1)
            tiles.append(cv2.resize(im,(240,424)))
        # Eight per strip; joint has 16 and therefore two strips.
        stripnames=[]
        for start in range(0,len(tiles),8):
            tile=tiles[start:start+8]
            while len(tile)<8:tile.append(np.zeros_like(tile[0]))
            strip=np.concatenate([np.concatenate(tile[:4],1),np.concatenate(tile[4:],1)],0);name='overlay.jpg' if start==0 else f'overlay_{start//8+1}.jpg';cv2.imwrite(str(dest/name),strip,[cv2.IMWRITE_JPEG_QUALITY,94]);stripnames.append(name)
        if job['id'] in ['notan_uncut','notan_fullrate','notan_joint_S1_S4']:notes.append('Path includes cuts or station changes and is not a physical continuous camera trajectory. Cross-shot shared room is only a hypothesis.')
        reprojection=background_reprojection(ds,images,indices,chosen,job,valid)
        result=dict(candidate=candidate,shot=job['id'],status='ran',source_frames=job['source_frames'],inference_frames=len(ds),camera=camera,background_reprojection=reprojection,evaluation_origin=evaluation_origin.tolist(),scale=dict(metric_claim=True,error_against_surveyed_ground_truth_pct=None,body_depth_disagreement_pct=float(100*(np.median(ratios)-1)) if ratios else None,body_depth_ratios=stats(ratios),body_samples=body,note='Body model is an independent estimate, NOT measured ground truth. Raw body surface projected with its own focal; inconsistent focal also affects depth disagreement. No body root was rescaled.',joint_room_table_check=joint_height),floor=stability,timing=timing,overlays=stripnames,notes=notes)
        write(dest/'metrics.json',result);results.append(result)
        print(candidate,job['id'],'camera',round(camera['path_m'],3),'diam',round(camera['diameter_m'],3),'body%',result['scale']['body_depth_disagreement_pct'],'floor_cm',stability['offset_range_cm'] if stability else None,flush=True)
    write(BANK/f'{candidate}_metrics.json',results)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate');run(p.parse_args().candidate)
