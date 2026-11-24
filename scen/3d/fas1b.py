"""Phase 1b only: python -B scen/3d/fas1b.py measure|solve|verify|all.

Reuses 30 fps motion; never edits Phase 1 measurements or verification images.
All output, caches, model files and logs stay below scen/3d.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, time
import numpy as np
import cv2
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from fas1 import ROOT, REPO, SHOTS, W, H, get_frame, read_json, write_json, log
from fas1_geometry import points, project, intrinsics, errors, Q, HIP, EDGES, project_world, unproject_plane

GROUPS={'A':['S1','S3','S6'],'B':['S2','S5'],'C':['S4'],'wide':['S7']}
SELECTED_FOV=68


def dump(name,value):
    write_json(ROOT/'data'/name,value)


def ordered(line):
    a=np.array(line,dtype=float).reshape(2,2)
    return a[np.argsort(a[:,0])]


def line_equation(segment):
    a,b=np.c_[segment,np.ones(2)]
    l=np.cross(a,b)
    return l/np.linalg.norm(l[:2])


def measure():
    start=time.perf_counter()
    yolo=read_json(REPO/'scen/data/d-dialog-notan/spar.json')['bilder']
    raw=read_json(REPO/'data/ra/hampuslundgren_-1779375226505.json')['sett']['ramar']
    records=[];selected={k:[] for k in ['B_front','B_left','B_right','A_far']};props=[]
    for shot in SHOTS:
        sid=shot['id'];a,b=shot['start_frame'],shot['end_frame_exclusive']
        samples=sorted(set([a,(a+b-1)//2,b-1]+(np.linspace(a,b-1,15).astype(int).tolist() if sid=='S7' else [])))
        for n in samples:
            image=get_frame(n);gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
            found=cv2.createLineSegmentDetector().detect(gray)[0]
            lines=found.reshape(-1,4) if found is not None else []
            yf=min(yolo,key=lambda f:abs(f['t']-n/30));rf=min(raw,key=lambda f:abs(f['t']-n/30))
            tables=[dict(box=o['box'],confidence=o['c'],source='YOLO-World') for o in yf['f'] if o['k']=='table']
            tables += [dict(box=o['b'],confidence=o['s'],source='EfficientDet') for o in rf.get('saker',[]) if o['k']=='dining table']
            candidates=[];chosen={}
            for l in lines:
                seg=ordered(l);(x0,y0),(x1,y1)=seg;length=float(np.linalg.norm(seg[1]-seg[0]))
                if length<45 or min(y0,y1)<430:continue
                candidates.append(dict(segment_px=seg.tolist(),length_px=length))
                if sid!='S7':continue
                key=None
                if 140<x0<180 and 470<x1<510 and 545<y0<563 and 545<y1<563 and abs(y1-y0)<6:key='B_front'
                if 145<x0<175 and 230<x1<275 and 540<y0<565 and 465<y1<505:key='B_left'
                if 435<x0<470 and 480<x1<510 and 480<y0<530 and 540<y1<565:key='B_right'
                if 275<x0<330 and 390<x1<430 and 695<y0<720 and 700<y1<725 and abs(y1-y0)<15:key='A_far'
                if key and (key not in chosen or length>chosen[key]['length_px']):
                    chosen[key]=dict(frame=n,segment_px=seg.tolist(),length_px=length)
            for k,v in chosen.items():selected[k].append(v)
            for table in tables:
                box=np.array(table['box'])*[W,H,W,H]
                table['clipped']=bool(box[0]<5 or box[2]>W-5 or box[3]>H-5)
                cv2.rectangle(image,tuple(box[:2].astype(int)),tuple(box[2:].astype(int)),(80,210,80),2)
            for k,v in chosen.items():
                seg=np.rint(v['segment_px']).astype(int)
                cv2.line(image,tuple(seg[0]),tuple(seg[1]),(255,255,0),3)
                cv2.putText(image,k,tuple(seg.mean(0).astype(int)),0,.55,(0,0,255),2)
            cv2.putText(image,f'{sid} frame {n} / source edge audit',(10,28),0,.65,(0,220,255),2)
            if sid!='S7':cv2.putText(image,'Box is clipped; food-box lines rejected',(10,55),0,.53,(0,220,255),2)
            if n==(a+b-1)//2:cv2.imwrite(str(ROOT/'verifiering'/f'{sid}-edges-1b.jpg'),image)
            records.append(dict(shot=sid,frame=n,tables=tables,table_region_line_candidates=candidates,selected=chosen))
        for yf in yolo:
            if not a/30<=yf['t']<b/30:continue
            typ='can' if shot['actor']=='A' else 'cup'
            objs=[o for o in yf['f'] if o['k']==('bottle' if typ=='can' else 'cup')]
            if sid=='S4':continue
            if sid=='S7':
                for typ2,test in [('cup',lambda o:o['k']=='cup' and o['box'][3]<.6),('can',lambda o:o['k'] in ['cup','bottle'] and o['box'][0]>.65)]:
                    choices=[o for o in yf['f'] if test(o)]
                    if choices:
                        o=max(choices,key=lambda o:o['c']);props.append(dict(shot=sid,type=typ2,t=yf['t'],box=o['box'],confidence=o['c']))
            elif objs:
                o=max(objs,key=lambda o:o['c']);props.append(dict(shot=sid,type=typ,t=yf['t'],box=o['box'],confidence=o['c']))
    edges={k:dict(segment_px=np.median([s['segment_px'] for s in v],axis=0).tolist(),samples=len(v),
                 endpoint_std_px=np.std([s['segment_px'] for s in v],axis=0).tolist()) for k,v in selected.items() if v}
    assert len(edges)==4,'Missing required source edge; inspect detection audit'
    summary={}
    for group,shots in GROUPS.items():
        for typ in ['can','cup']:
            obs=[p for p in props if p['shot'] in shots and p['type']==typ]
            if not obs:continue
            boxes=np.array([o['box'] for o in obs]);uv=np.c_[(boxes[:,0]+boxes[:,2])*W/2,boxes[:,3]*H,
                (boxes[:,0]+boxes[:,2])*W/2,boxes[:,1]*H].reshape(-1,2,2)
            summary[f'{group}:{typ}']=dict(uv_px=np.median(uv,axis=0).tolist(),std_px=uv.std(axis=0).tolist(),n=len(obs))
    result=dict(records=records,edges=edges,prop_observations=props,prop_summary=summary,runtime_s=time.perf_counter()-start,
        interpretation='Close-shot and foreground table front/side bounds are clipped. Do not use food packaging or dining-table box bottom as a table corner. S7 side endpoints are partly occluded, so table depth is a lower bound plus an explicit seat-clearance prior.')
    dump('measurements-1b.json',result)
    log('## Phase 1b — source measurements\nPreserving Phase 1 images and measurements. Reusing all 383 motion frames. '
        'LSD runs on the source table regions; YOLO/EfficientDet clipped table boxes provide lower bounds, not exact edges. '
        'S7 B front/side lines and A foreground far-edge segment are retained with detection spread. '
        f'Runtime {result["runtime_s"]:.2f} s.\n\n'+json.dumps(edges,ensure_ascii=False))
    print(json.dumps(dict(edges=edges,props=summary),indent=2))


def data_points(frames):
    p=[points(f) for f in frames]
    return np.concatenate([v[0] for v in p]),np.concatenate([v[1] for v in p])


def robust(r,scale=20.):
    return np.sign(r)*np.sqrt(2*scale**2*(np.sqrt(1+(r/scale)**2)-1))


def camera_seed(frames,K):
    rs=[];ts=[]
    for f in frames:
        xyz,uv,_=points(f)
        if len(xyz)<6:continue
        ok,r,t=cv2.solvePnP(xyz,uv,K,None,flags=cv2.SOLVEPNP_SQPNP)
        if ok and t[2,0]>.1:rs.append(r.ravel());ts.append(t.ravel())
    r=np.median(rs,axis=0);t=np.median(ts,axis=0);center=-cv2.Rodrigues(r)[0].T@t
    return np.r_[r,center]


def rt(p):
    return p[:3],-cv2.Rodrigues(p[:3])[0]@p[3:6]


def cam_bounds(actor):
    return [-.8,-.8,-.5,-4.,HIP[actor]-1.7,-8.],[.8,.8,.5,4.,HIP[actor]-.9,-.25]


def camera_stats(p,frames,fov,actor):
    r,t=rt(p);K=intrinsics(fov);R=cv2.Rodrigues(r)[0]
    horizon=np.linalg.inv(K).T@R@np.array([0.,-1.,0.])
    return dict(parameters=p.tolist(),rvec=r.tolist(),tvec=t.tolist(),fov_deg=fov,
        height_m=float(HIP[actor]-p[4]),hip_distance_m=float(np.linalg.norm(p[3:6])),
        horizon_y_px=float(-(horizon[0]*W/2+horizon[2])/horizon[1]),
        **{k:v for k,v in errors(frames,r,t,K).items() if k!='frames'})


def unproject_local(p,uv,plane_y,K):
    r,t=rt(p);R=cv2.Rodrigues(r)[0];c=Q@p[3:6]
    rays=np.c_[np.asarray(uv),np.ones(len(uv))]@np.linalg.inv(K).T@R@Q
    return c+rays*((plane_y-c[1])/rays[:,1])[:,None]


def solve_one(fov,motion,measurements):
    K=intrinsics(fov);groupframes={g:[f for f in motion['frames'] if f['shot'] in shots] for g,shots in GROUPS.items()}
    arr={g:data_points(f) for g,f in groupframes.items()};cams={}
    prop=measurements['prop_summary'];edges=measurements['edges']
    # A: one joint camera plus a can measured on the table. Its local x/z are free.
    for group in ['A','C']:
        actor=group;seed=camera_seed(groupframes[group],K);low,high=cam_bounds(actor)
        if group=='A':seed=np.r_[seed,-.25,.85];low += [-1.,.15];high += [.5,1.8]
        seed=np.clip(seed,np.array(low)+1e-6,np.array(high)-1e-6)
        xyz,uv=arr[group]
        def residual(p):
            r,t=rt(p);res=list(robust((project(xyz,r,t,K)-uv).ravel())/np.sqrt(len(xyz)))
            # Weak camera-height regularizer, explicitly a prior, not a fitted observation.
            res.append((HIP[actor]-p[4]-1.20)/.30*4)
            if group=='A':
                base=[p[6],.75-HIP['A'],p[7]];ob=np.array([base,np.array(base)+[0,.168,0]])@Q
                res.extend(((project(ob,r,t,K)-np.array(prop['A:can']['uv_px']))*1.4).ravel())
            return res
        fitted=least_squares(residual,seed,bounds=(low,high),max_nfev=180)
        cams[group]=camera_stats(fitted.x[:6],groupframes[group],fov,actor)
        if group=='A':cams[group]['can_base_local']=[float(fitted.x[6]),.15,float(fitted.x[7])]
    # B close and wide jointly share the paper cup and one physical table.
    sb=camera_seed(groupframes['B'],K);sw=camera_seed(groupframes['wide'],K)
    lo,hi=cam_bounds('B');lower=lo+lo+[-.8,.1,-2.,.4,.40,.40,-.2,-.4,-.20]
    upper=hi+hi+[.4,1.5,2.,7.,1.8,1.8,.6,.4,.20]
    # [B camera6, wide camera6, B cup xz, A can xz, table width/depth/back-z/center-x/yaw]
    seed=np.r_[sb,sw,-.18,.6,.2,max(.8,-sw[5]-.6),1.05,.85,.20,0.,0.]
    seed=np.clip(seed,np.array(lower)+1e-5,np.array(upper)-1e-5)
    front=np.array(edges['B_front']['segment_px']);leftline=line_equation(edges['B_left']['segment_px']);rightline=line_equation(edges['B_right']['segment_px'])
    targetcup=np.array(prop['wide:cup']['uv_px']);targetcan=np.array(prop['wide:can']['uv_px']);targetclose=np.array(prop['B:cup']['uv_px'])
    def table_points(p):
        w,d,back,cx,angle=p[16:21]
        R=Rotation.from_euler('y',angle).as_matrix()
        local=np.array([[-w/2,0,d/2],[w/2,0,d/2],[-w/2,0,-d/2],[w/2,0,-d/2]])@R.T+[cx,.15,back+d/2]
        return local@Q
    def residual(p):
        rb,tb=rt(p[:6]);rw,tw=rt(p[6:12]);res=[]
        for key,r,t in [('B',rb,tb),('wide',rw,tw)]:
            xyz,uv=arr[key];res.extend(robust((project(xyz,r,t,K)-uv).ravel())/np.sqrt(len(xyz)))
        cup=np.array([[p[12],.15,p[13]],[p[12],.33,p[13]]])@Q
        can=np.array([[p[14],.15,p[15]],[p[14],.318,p[15]]])@Q
        res.extend(((project(cup,rb,tb,K)-targetclose)*1.2).ravel())
        res.extend(((project(cup,rw,tw,K)-targetcup)*1.2).ravel())
        res.extend(((project(can,rw,tw,K)-targetcan)*1.2).ravel())
        corners=project(table_points(p),rw,tw,K)
        res.extend(((corners[:2]-front)*1.8).ravel())
        res.extend([np.r_[corners[2],1]@leftline*.7,np.r_[corners[3],1]@rightline*.7])
        # Back edge must reach at least the visible side endpoints; exact depth is occluded.
        res.extend([max(0.,corners[2,1]-min(np.array(edges['B_left']['segment_px'])[:,1]))*.6,
                    max(0.,corners[3,1]-min(np.array(edges['B_right']['segment_px'])[:,1]))*.6])
        res.extend([(p[18]-.20)/.18*3,(p[17]-.85)/.45*2])
        # Metric camera-height prior is weak; shared visible objects and pose dominate.
        res.extend([(HIP['B']-p[4]-1.2)/.30*3,(HIP['B']-p[10]-1.2)/.30*3])
        # Cup must remain on the measured tabletop, including footprint margin.
        w,d,back,cx,angle=p[16:21];cup_local=Rotation.from_euler('y',-angle).apply([p[12]-cx,0,p[13]-(back+d/2)])
        res.extend([max(0.,abs(cup_local[0])-(w/2-.05))*100,max(0.,abs(cup_local[2])-(d/2-.05))*100])
        return res
    fitted=least_squares(residual,seed,bounds=(lower,upper),max_nfev=350,x_scale='jac')
    p=fitted.x
    for g,sl in [('B',slice(0,6)),('wide',slice(6,12))]:cams[g]=camera_stats(p[sl],groupframes[g],fov,'B')
    corners=table_points(p)@Q
    result=dict(fov_deg=fov,cameras=cams,B_cup_local=[float(p[12]),.15,float(p[13])],
        A_can_B_local=[float(p[14]),.15,float(p[15])],B_table=dict(width_m=float(p[16]),depth_m=float(p[17]),
        back_z_m=float(p[18]),center_x_m=float(p[19]),yaw_rad=float(p[20]),corners_local=corners.tolist()),
        solver_success=bool(fitted.success),solver_evaluations=fitted.nfev,
        edge_error_px=np.linalg.norm(project(table_points(p),*rt(p[6:12]),K)[:2]-front,axis=1).tolist(),
        can_error_px=np.linalg.norm(project(np.array([[p[14],.15,p[15]],[p[14],.318,p[15]]])@Q,*rt(p[6:12]),K)-targetcan,axis=1).tolist())
    # A global translation is fixed by the same physical can in its close and wide views.
    a_can_world=np.array(result['A_can_B_local'])+[0,HIP['B'],0]
    ayaw=Rotation.from_euler('y',180,degrees=True).as_matrix()
    a_origin=a_can_world-ayaw@np.array(cams['A']['can_base_local'])
    result['A_position_m']=a_origin.tolist();result['A_B_distance_m']=float(np.linalg.norm(a_origin[[0,2]]))
    result['shot_errors']={s:errors([f for f in motion['frames'] if f['shot']==s],np.array(cams[g]['rvec']),np.array(cams[g]['tvec']),K)['median_px'] for g,shots in GROUPS.items() for s in shots}
    return result


def solve():
    start=time.perf_counter();motion=read_json(ROOT/'data/sparning.json');m=read_json(ROOT/'data/measurements-1b.json')
    results=[]
    for fov in [58,62,65,68,70,75]:
        r=solve_one(fov,motion,m);results.append(r)
        print('FOV',fov,'AB',round(r['A_B_distance_m'],3),'height',{g:round(c['height_m'],3) for g,c in r['cameras'].items()},
            'Btable',round(r['B_table']['width_m'],3),round(r['B_table']['depth_m'],3),
            'edge',np.round(r['edge_error_px'],2).tolist(),'joints',{s:round(v,2) for s,v in r['shot_errors'].items()},flush=True)
    dump('solve-1b.json',dict(selected_fov_deg=SELECTED_FOV,sensitivity=results,runtime_s=time.perf_counter()-start,
        selection='68 degrees fixed inside requested 65–70 degree phone-main prior. No selection by pose-error minimum. Sensitivity refits all cameras and scene constraints at each shared FOV.'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['measure','solve','refine','verify','all']);args=parser.parse_args()
    from fas1b_finish import refine, verify
    for stage in (['measure','solve','refine','verify'] if args.stage=='all' else [args.stage]):globals()[stage]()
