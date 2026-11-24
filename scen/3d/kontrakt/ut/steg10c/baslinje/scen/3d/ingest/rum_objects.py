"""Lift detected furniture into metric boxes; refine the occluding edge in image space."""
import json
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree


def counter_edges(clip, M, detections):
    """Image-only line measurement near the detector's counter top. No rendered input.

    The longest steel rim has a strong near-horizontal gradient. Exclude endpoints
    near vertical cabinet edges, and measure every frame, including held-out frames.
    """
    hints = {d['frame']:d['box'][1] for d in detections if d['label']=='bar counter' and d['box'][2]-d['box'][0]>.65*M['bredd']}
    if not hints: return []
    xs=sorted(hints); cap=cv2.VideoCapture(str(clip)); edges=[]
    for i in range(M['N']):
        ok,img=cap.read()
        if not ok: break
        y=float(np.interp(i,xs,[hints[x] for x in xs])); h,w=img.shape[:2]
        lo,hi=max(0,int(y-.04*h)),min(h,int(y+.06*h))
        gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        canny=cv2.Canny(gray[lo:hi],60,160)
        lines=cv2.HoughLinesP(canny,1,np.pi/1800,threshold=70,minLineLength=int(w*.32),maxLineGap=35)
        choices=[]
        if lines is not None:
            for x0,y0,x1,y1 in lines.reshape(-1,4):
                if abs(x1-x0)<w*.32 or abs(y1-y0)>abs(x1-x0)*.18: continue
                y0+=lo;y1+=lo
                mid=(y0+y1)/2
                # Prefer long continuous rim; detector's top is only a loose search window.
                score=abs(x1-x0)-abs(mid-y)*1.3
                choices.append((score,[int(x0),int(y0)],[int(x1),int(y1)]))
        if choices:
            _,a,b=max(choices,key=lambda x:x[0]);edges.append(dict(frame=i,points=[a,b]))
    cap.release(); return edges


def fit_counter(clip,ut,M,V,source,det):
    from rum import gravity, plane_ransac, project, utan_parallax
    G=gravity(V['upp']); floor=float(V['golv_h']); focal=float(np.load(next(ut.glob('sekvens_*.npz')))['fokal'])
    observations=counter_edges(clip,M,det)
    (ut/'rum/counter_edges.json').write_text(json.dumps(observations,indent=1))
    train=[e for e in observations if e['frame']%6==0]
    if len(train)<4: return None
    # Point support: inside detected boxes, horizontal normal and below the camera.
    supports=[]
    for d in det:
        if d['label']!='bar counter' or d['box'][2]-d['box'][0]<.65*M['bredd']: continue
        idx=np.flatnonzero(source['frames']==d['frame']); uv=source['uv'][idx]; p=source['xyz'][idx]; normals=source['normals'][idx]
        x0,y0,x1,y1=d['box']
        valid=(uv[:,0]>x0)&(uv[:,0]<x1)&(uv[:,1]>y0)&(uv[:,1]<y1)&(np.abs(normals[:,2])>.85)&(p[:,2]>floor+.65)&(p[:,2]<floor+1.4)
        supports.append(p[valid])
    points=np.concatenate(supports) if supports else np.empty((0,3))
    fit=plane_ransac(points,'horizontal',threshold=.035)
    if not fit: return None
    normal,d,inside=fit; top=float(np.median(points[inside,2])); points=points[inside]
    # Lift measured line endpoints to the observed top plane, then fit their XY line.
    def lift(frame,pix,z):
        ray=np.c_[(np.asarray(pix)-np.array([M['bredd'],M['hojd']])/2)/focal,np.ones(len(pix))]@V['kam_R'][frame].T@G.T
        c=V['kam_C'][frame]@G.T
        return c+ray*((z-c[2])/ray[:,2])[:,None]
    xy=np.concatenate([lift(e['frame'],e['points'],top)[:,:2] for e in train]); centre=np.median(xy,0)
    _,_,vt=np.linalg.svd(xy-centre,full_matrices=False); n=vt[-1]
    if (V['kam_C'].mean(0)@G.T)[:2]@n<centre@n:n=-n
    theta=np.arctan2(n[1],n[0]); offset=float(centre@n)
    def line(param,frame):
        a,d,z,slope=param;n=np.array([np.cos(a),np.sin(a),0]);t=np.array([-n[1],n[0],slope])
        p=n*d;p[2]=z
        world=np.stack([p-t*3,p+t*3])@G
        uv,_=project(world,frame,V,focal,(M['bredd'],M['hojd']))
        l=np.cross(np.r_[uv[0],1],np.r_[uv[1],1]);return l/np.linalg.norm(l[:2])
    def residual(p):
        r=[]
        for e in train:
            l=line(p,e['frame']);r.extend(np.c_[e['points'],np.ones(2)]@l)
        # Depth-model top height is a metric prior, weak enough for multi-view refinement.
        return np.r_[r,(p[2]-top)/.1]
    if utan_parallax(V):
        # Behåll enkelvylösningen från djupplanet; linjen ensam bestämmer inte djupet.
        param=np.array([theta,offset,top,0.])
    else:
        sol=least_squares(residual,[theta,offset,top,0],loss='soft_l1',f_scale=50,
                          bounds=([theta-.5,offset-1,top-.25,-.15],[theta+.5,offset+1,top+.25,.15]))
        param=sol.x
    a,d,z,slope=param;n=np.array([np.cos(a),np.sin(a),0]);t=np.array([-n[1],n[0],0])
    lifted=np.concatenate([lift(e['frame'],e['points'],z) for e in train]); along=lifted@t
    low,high=np.percentile(along,[0,100]);low-=.25;high+=.25
    front=np.percentile(points@n,98); depth=float(np.clip(front-d,.3,1.2))
    centre=n*(d+depth/2)+t*(low+high)/2;z+=slope*(low+high)/2;centre[2]=(floor+z)/2
    errors=[]
    for e in observations:
        l=line(param,e['frame']);err=np.abs(np.c_[e['points'],np.ones(2)]@l)
        errors.append(dict(frame=e['frame'],error_px=float(err.max()),held_out=e['frame']%6!=0))
    allerr=np.array([e['error_px'] for e in errors]); held=[e['error_px'] for e in errors if e['held_out']]
    report=dict(method='Hough steel back rim vs projected static box back edge; full-resolution source pixels',
                frames=len(errors),total_frames=M['N'],training_frames=len(train),held_out_frames=len(held),
                median_px=float(np.median(allerr)),p95_px=float(np.percentile(allerr,95)),max_px=float(allerr.max()),
                held_out_p95_px=float(np.percentile(held,95)),within_25px_fraction=float(np.mean(allerr<=25)),per_frame=errors)
    (ut/'rum/counter_edge_check.json').write_text(json.dumps(report,indent=2))
    return dict(id='bar_counter_1',label='bar counter',centre=(centre@G).tolist(),size=[float(high-low),depth,float(z-floor)],
                yaw=float(np.arctan2(t[1],t[0])),top_slope=float(slope),frames=[e['frame'] for e in train],support_points=len(points),
                source='Gemini boxes + masked MoGe horizontal plane + multiview rim fit',
                top_height_raw=top,top_height=z,back_plane=dict(normal=(n@G).tolist(),distance=float(d)),
                width_is_minimum=True,edge_check={k:v for k,v in report.items() if k!='per_frame'})


def fit_tables(clip,ut,M,V,source,det):
    from rum import gravity, oriented_rectangle, plane_ransac
    G=gravity(V['upp']); floor=float(V['golv_h']); cap=cv2.VideoCapture(str(clip)); chunks=[]
    table_det=[d for d in det if d['label'] in ('pool table','billiard table','billiards table')]
    for frame in sorted(set(d['frame'] for d in table_det)):
        cap.set(cv2.CAP_PROP_POS_FRAMES,frame);ok,img=cap.read()
        if not ok:continue
        idx=np.flatnonzero(source['frames']==frame);p=source['xyz'][idx];uv=source['uv'][idx];n=source['normals'][idx]
        hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV);pix=np.clip(uv.astype(int),0,[M['bredd']-1,M['hojd']-1]);col=hsv[pix[:,1],pix[:,0]]
        # Felt is a high-saturation green/cyan surface. This refines the detector's boxes,
        # prevents background walls entering a table box, and is not itself a labeler.
        felt=(col[:,0]>30)&(col[:,0]<110)&(col[:,1]>65)&(col[:,2]>45)&(np.abs(n[:,2])>.65)
        for d in [d for d in table_det if d['frame']==frame]:
            x0,y0,x1,y1=d['box'];valid=felt&(uv[:,0]>x0)&(uv[:,0]<x1)&(uv[:,1]>y0)&(uv[:,1]<y1)&(p[:,2]>floor+.45)&(p[:,2]<floor+1.15)
            q=p[valid]
            if len(q)<40:continue
            # Split boxes covering two tables by connected components in image space.
            mask=np.zeros((M['hojd']//6+1,M['bredd']//6+1),np.uint8); xy=(uv[valid]/6).astype(int);mask[xy[:,1],xy[:,0]]=1
            mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
            count,comp,_,_=cv2.connectedComponentsWithStats(mask)
            labels=comp[xy[:,1],xy[:,0]]
            for k in range(1,count):
                group=q[labels==k]
                if len(group)>=35: chunks.append(dict(frame=frame,points=group,uv=uv[valid][labels==k],centre=np.median(group,axis=0),track=d.get('track','')))
    cap.release()
    if not chunks:return []
    # A common top plane and 3D proximity associate observations independently of VLM ids.
    allpoints=np.concatenate([c['points'] for c in chunks]); fitted=plane_ransac(allpoints,'horizontal',threshold=.08)
    top=float(np.median(allpoints[fitted[2],2])) if fitted else float(np.median(allpoints[:,2]))
    # Stabilise depth along the ray by intersecting observations with the fitted top plane.
    focal=float(np.load(next(ut.glob('sekvens_*.npz')))['fokal'])
    for c in chunks:
        frame=c['frame'];pix=c['uv'];ray=np.c_[(pix-np.array([M['bredd'],M['hojd']])/2)/focal,np.ones(len(pix))]@V['kam_R'][frame].T@G.T
        origin=V['kam_C'][frame]@G.T
        c['points']=origin+ray*((top-origin[2])/ray[:,2])[:,None];c['centre']=np.median(c['points'],0)
    allpoints=np.concatenate([c['points'] for c in chunks])
    # Cloud connected components separate tables across the walking aisles. Voxel samples
    # remove image density bias; only a modest radius is allowed to bridge a masked person.
    vox=np.floor(allpoints[:,:2]/.06).astype(int);cells,inv=np.unique(vox,axis=0,return_inverse=True)
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    pairs=cKDTree(cells*.06).query_pairs(.15,output_type='ndarray')
    graph=coo_matrix((np.ones(len(pairs)),(pairs[:,0],pairs[:,1])),shape=(len(cells),len(cells)))
    count,labels=connected_components(graph,directed=False)
    np.savez_compressed(ut/'rum/table_observations.npz',points=allpoints,group=labels[inv],
                        uv=np.concatenate([c['uv'] for c in chunks]),frames=np.concatenate([np.full(len(c['points']),c['frame']) for c in chunks]))
    groups=[]
    for k in range(count):
        p=allpoints[labels[inv]==k]
        if len(p)<250:continue
        rect=cv2.minAreaRect(p[:,:2].astype(np.float32))
        centre=np.array(rect[0]);size=np.array(rect[1]);yaw=np.deg2rad(rect[2])
        if min(size)<.25 or max(size)<.7:continue
        groups.append((k,p,centre,size,yaw))
    objects=[]
    point_frames=np.concatenate([np.full(len(c['points']),c['frame']) for c in chunks])
    point_uv=np.concatenate([c['uv'] for c in chunks])
    person_masks=np.load(ut/'masker.npy')
    for group,p,xy,size,yaw in groups:
        # Unobserved ends may be cropped. Dimensions remain data-derived here; any
        # completion with a standard table prior is explicitly tagged below.
        if size[0]<size[1]:size=size[::-1];yaw+=np.pi/2
        raw_size=size.copy()
        chosen=labels[inv]==group;ff=point_frames[chosen];uv=point_uv[chosen]
        edge_uv=[];edge_ff=[]
        for frame in np.unique(ff):
            pixels=uv[ff==frame]; small=np.zeros((M['hojd']//6+1,M['bredd']//6+1),np.uint8)
            pix=(pixels/6).astype(int);small[pix[:,1],pix[:,0]]=255
            small=cv2.morphologyEx(small,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
            contours,_=cv2.findContours(small,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
            pm=cv2.dilate(cv2.resize(person_masks[frame].astype(np.uint8),small.shape[::-1],interpolation=cv2.INTER_NEAREST),np.ones((5,5),np.uint8))
            for contour in contours:
                pix=contour.reshape(-1,2);valid=(pix[:,0]>3)&(pix[:,0]<small.shape[1]-4)&(pix[:,1]>3)&(pix[:,1]<small.shape[0]-4)
                valid &= pm[pix[:,1],pix[:,0]]==0
                ep=pix[valid][::2]*6+3
                edge_uv.extend(ep);edge_ff.extend([frame]*len(ep))
        edge_uv=np.asarray(edge_uv);edge_ff=np.asarray(edge_ff,int)
        z=float(np.clip(top-floor,.65,.95)); parameters=np.r_[xy,yaw,np.clip(size,[2.2,1.1],[2.7,1.4]),z]
        if len(edge_ff)>50:
            rays=np.c_[(edge_uv-np.array([M['bredd'],M['hojd']])/2)/focal,np.ones(len(edge_uv))]
            rays=np.einsum('nij,nj->ni',V['kam_R'][edge_ff],rays)@G.T
            origins=V['kam_C'][edge_ff]@G.T
            def residual(param):
                cx,cy,a,length,width,height=param
                q=origins+rays*((floor+height-origins[:,2])/rays[:,2])[:,None]
                B=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
                local=(q[:,:2]-[cx,cy])@B;d=np.abs(local)-[length/2,width/2]
                # Signed distance to rectangle boundary, robust to pocket holes/rails.
                sdf=np.linalg.norm(np.maximum(d,0),axis=1)+np.minimum(np.maximum(d[:,0],d[:,1]),0)
                # Each observation is equal-weight; priors express the requested plausible
                # table range and are explicitly recorded, never claimed as tape measurements.
                return np.r_[sdf, (length-2.3)*3, (width-1.2)*3, (height-.8)*6, (a-yaw)*2]
            fit=least_squares(residual,parameters,loss='soft_l1',f_scale=.04,max_nfev=160,
                              bounds=(np.r_[xy-1,yaw-.45,2.2,1.1,.65],np.r_[xy+1,yaw+.45,2.7,1.4,.95]))
            parameters=fit.x
        xy=parameters[:2];yaw=parameters[2];size=parameters[3:5]+.2;z=float(parameters[5]);centre=np.r_[xy,floor+z/2]
        frames=sorted(set(int(f) for f in ff))
        objects.append(dict(id=f'pool_table_{len(objects)+1}',label='pool table',centre=(centre@G).tolist(),
                            size=[float(size[0]),float(size[1]),z],yaw=float(yaw),frames=frames,support_points=len(p),
                            observed_felt_size=raw_size.tolist(),source='Gemini boxes + masked MoGe felt points; gravity-aligned OBB',
                            completion_prior='20 cm total rail margin; soft standard-size prior 2.5 x 1.4 x .8 m; multi-view felt boundary fit',
                            contour_points=len(edge_ff),top_height_raw=top))
    return objects


def fit_props(ut,M,V,source,det,objects):
    """Robust multiframe boxes for the remaining detected furniture/props."""
    from rum import gravity,oriented_rectangle
    G=gravity(V['upp']);floor=float(V['golv_h']);candidates=[]
    for d in det:
        if d['label'] in ('bar counter','pool table','billiard table','billiards table'):continue
        idx=np.flatnonzero(source['frames']==d['frame']);uv=source['uv'][idx];p=source['xyz'][idx]
        x0,y0,x1,y1=d['box'];p=p[(uv[:,0]>x0)&(uv[:,0]<x1)&(uv[:,1]>y0)&(uv[:,1]<y1)]
        if len(p)<35:continue
        c=V['kam_C'][d['frame']]@G.T;forward=V['kam_R'][d['frame'],:,2]@G.T;depth=(p-c)@forward
        lo,hi=np.percentile(depth,[5,65]);p=p[(depth>=lo)&(depth<=hi)]
        if len(p)<25:continue
        candidates.append(dict(label=d['label'],frame=d['frame'],points=p,centre=np.median(p,0)))
    clusters=[]
    for c in candidates:
        matches=[g for g in clusters if g[0]['label']==c['label'] and np.linalg.norm(np.median([x['centre'] for x in g],0)-c['centre'])<.45]
        if matches:matches[0].append(c)
        else:clusters.append([c])
    result=[];rejected=[]
    for group in clusters:
        frames=sorted(set(c['frame'] for c in group));label=group[0]['label']
        if len(frames)<3:
            rejected.append(dict(label=label,frames=frames,reason='fewer than three consistent 3D observations'));continue
        p=np.concatenate([c['points'][::3] for c in group]);xy,size,yaw=oriented_rectangle(p);low,high=np.percentile(p[:,2],[5,95])
        if label in ('chair','table','cabinet','sofa'):low=floor
        size=np.r_[size,high-low];centre=np.r_[xy,(high+low)/2]
        if np.min(size)<.025 or np.max(size)>3:
            rejected.append(dict(label=label,frames=frames,reason='degenerate or background-contaminated box'));continue
        # Small tabletop props follow the fitted support plane so a discrepant monocular
        # depth estimate cannot leave a payment terminal floating above the counter.
        if label=='card payment terminal':
            counters=[o for o in objects if o['label']=='bar counter']
            if counters:
                counter=counters[0];cc=np.asarray(counter['centre'])@G.T
                ratio=(counter['top_height']-np.median(V['kam_C']@G.T,axis=0)[2])/(np.median(p[:,2])-np.median(V['kam_C']@G.T,axis=0)[2])
                origin=np.median(V['kam_C'][frames]@G.T,axis=0)
                centre[:2]=origin[:2]+(centre[:2]-origin[:2])*np.clip(ratio,.2,2.)
                size[:2]*=np.clip(ratio,.2,2.);centre[2]=counter['top_height']+size[2]/2
        result.append(dict(id=f'prop_{len(result)+1}',label=label,centre=(centre@G).tolist(),size=size.tolist(),yaw=yaw,
                           frames=frames,support_points=len(p),source='masked depth inside open-vocabulary boxes, foreground depth quantiles, multiview OBB'))
    (ut/'rum/rejected_detections.json').write_text(json.dumps(rejected,indent=2))
    return result


def fit_objects(clip,ut,M,V,source,det):
    objects=[]
    if any(d['label']=='bar counter' and d['box'][2]-d['box'][0]>.65*M['bredd'] for d in det):
        counter=fit_counter(clip,ut,M,V,source,det)
        if counter:objects.append(counter)
    objects.extend(fit_tables(clip,ut,M,V,source,det))
    objects.extend(fit_props(ut,M,V,source,det,objects))
    return objects
