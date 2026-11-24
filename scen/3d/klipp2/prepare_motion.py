"""Benchmark common joints, fit root placement, preserve gesture timing, export rig input.

No learned models or detector outputs are presented as ground truth. All pixels
are at the 540x960 render resolution. Bone fitting uses measured directions;
Blender performs rotation retargeting, with no custom IK solver.
"""
import json,time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.signal import savgol_filter,find_peaks
from scipy.spatial.transform import Rotation
from lift import fill,mp_to_h36
HERE=Path(__file__).resolve().parent
PARENTS=np.array([-1,0,1,2,0,4,5,0,7,8,9,8,11,12,8,14,15])
EDGES=[(int(p),i) for i,p in enumerate(PARENTS) if p>=0]
def write(n,v):(HERE/n).write_text(json.dumps(v,indent=2,allow_nan=False),encoding='utf-8')
def smooth(x,window=5):return savgol_filter(x,window,2,axis=0,mode='interp')
def project(x,K):return x[:,:,:2]/x[:,:,2:]*[K[0,0],K[1,1]]+[K[0,2],K[1,2]]
def lengths(x):return np.stack([np.linalg.norm(x[:,b]-x[:,a],axis=-1) for a,b in EDGES],axis=1)
def place(x,uv,conf,K):
    out=[];prev=np.array([0.,0.,3.])
    for p,u,w in zip(x,uv,conf):
        weights=np.sqrt(np.where(w>.5,w,0));weights[[3,6]]=0 # off-screen feet are not translation anchors
        def fun(t):return (((p[:,:2]+t[:2])/(p[:,2:]+t[2])*[K[0,0],K[1,1]]+[K[0,2],K[1,2]]-u)*weights[:,None]).ravel()
        fit=least_squares(fun,prev,bounds=([-5,-5,1.],[5,5,15.]),loss='soft_l1',f_scale=10,max_nfev=35);prev=fit.x;out.append(p+fit.x)
    return np.array(out)
def timing_peaks(raw,filtered):
    records=[]
    for j in [12,13,15,16]:
        for k in [0,1]:
            x=raw[:,j,k];y=filtered[:,j,k]
            for sign in [1,-1]:
                peaks=find_peaks(sign*x,prominence=12,distance=8)[0]
                for p in peaks:
                    lo=max(0,p-4);hi=min(len(y),p+5);q=int(lo+np.argmax(sign*y[lo:hi]));records.append(dict(joint=j,axis=k,frame=int(p),filtered_frame=q,shift=q-int(p)))
    return records
def main():
    start=time.perf_counter();rows=json.loads((HERE/'mediapipe.json').read_text())['frames'];T=len(rows)
    p=fill([r['pose'] if r['pose'] else np.full((33,3),np.nan) for r in rows]);w=fill([r['world'] if r['world'] else np.full((33,3),np.nan) for r in rows]);vis=fill([r['visibility'] if r['visibility'] else np.full(33,np.nan) for r in rows])
    uv=mp_to_h36(p)[:,:,:2]*[540,960];conf=mp_to_h36(vis[:,:,None])[:,:,0];conf[(uv[:,:,0]<0)|(uv[:,:,0]>540)|(uv[:,:,1]<0)|(uv[:,:,1]>960)]=0;conf[[r['frame'] for r in rows if not r['pose']]]=0
    camfile=HERE/'kamera.json' if (HERE/'kamera.json').exists() else HERE/'kamera-fallback.json';cam=json.loads(camfile.read_text());K=np.array(cam.get('K',[[780,0,270],[0,780,480],[0,0,1.]]))
    matrices=np.array([f.get('matrix_world',f.get('world_matrix')) for f in cam['frames']]);assert matrices.shape==(369,4,4),'Camera schema must provide frame-aligned matrices'
    # Input skeletons are camera-CV relative coordinates. Normalize each once to 1.65m stature.
    a=mp_to_h36(w);a-=a[:,0:1];c=np.load(HERE/'motionbert.npz')['xyz']
    for x in [a,c]:
        stature=np.linalg.norm(x[:,8]-x[:,0],axis=-1)+.24+(np.linalg.norm(x[:,1]-x[:,2],axis=-1)+np.linalg.norm(x[:,2]-x[:,3],axis=-1)+np.linalg.norm(x[:,4]-x[:,5],axis=-1)+np.linalg.norm(x[:,5]-x[:,6],axis=-1))/2
        x*=1.65/np.median(stature)
    ca=place(a,uv,conf,K);cc=place(c,uv,conf,K)
    errors={n:np.linalg.norm(project(v,K)-uv,axis=-1) for n,v in [('a_mediapipe',ca),('c_motionbert',cc)]}
    parts={'torso':[0,7,8,9,10,11,14],'left_arm':[12,13],'right_arm':[15,16],'legs':[1,2,3,4,5,6]};choice={}
    hybrid=ca.copy()
    for name,idx in parts.items():
        scores={n:float(np.mean(e[:,idx][conf[:,idx]>.5])) for n,e in errors.items()};best=min(scores,key=scores.get);choice[name]=dict(source=best,mean_reprojection_px=scores)
        if best=='c_motionbert':
            anchor={'left_arm':11,'right_arm':14,'torso':0,'legs':0}[name]
            hybrid[:,idx]=cc[:,idx]-cc[:,anchor:anchor+1]+ca[:,anchor:anchor+1]
    # Preserve the best image observations, using selected 3D predictions for depth only.
    filtered=smooth(uv);peaks=timing_peaks(uv,filtered)
    # Preserve significant source extrema at their exact frame. Short symmetric filter elsewhere.
    for event in peaks:
        i,j,k=event['frame'],event['joint'],event['axis'];filtered[i,j,k]=uv[i,j,k]
    z=smooth(hybrid[:,:,2]);hybrid[:,:,2]=z;hybrid[:,:,:2]=(filtered-[K[0,2],K[1,2]])/[K[0,0],K[1,1]]*z[:,:,None]
    # Fixed-length skeleton: maintain measured per-frame directions, build parent-first.
    lens=np.median(lengths(hybrid),axis=0);fitted=hybrid.copy()
    for n,(pa,ch) in enumerate(EDGES):
        d=hybrid[:,ch]-hybrid[:,pa];d/=np.linalg.norm(d,axis=-1)[:,None];fitted[:,ch]=fitted[:,pa]+d*lens[n]
    R=matrices[:,:3,:3]@np.diag([1.,-1.,-1.]);origin=matrices[:,:3,3]
    to_world=lambda x:np.einsum('tij,tkj->tki',R,x)+origin[:,None]
    world_a,world_c,world_d=map(to_world,[ca,cc,fitted])
    # Conservative contacts require visible confident heels/ankles, low world velocity AND low height.
    feet=world_d[:,[6,3]];speed=np.linalg.norm(np.gradient(feet,axis=0),axis=-1)*30;floor=float(np.quantile(feet[:,:,2],.05));height=feet[:,:,2]-floor
    contacts=(speed<.18)&(height<.055)&(conf[:,[6,3]]>.6)
    # Runs shorter than three frames are not labelled planted. No fabricated contact for cropped feet.
    runs=[]
    for side in range(2):
        changes=np.diff(np.r_[False,contacts[:,side],False].astype(int));starts=np.flatnonzero(changes==1);ends=np.flatnonzero(changes==-1)
        for st,en in zip(starts,ends):
            if en-st<3:contacts[st:en,side]=False;continue
            anchor=np.median(world_d[st:en,[6,3][side]],axis=0);anchor[2]=floor
            runs.append(dict(side=side,start=int(st),end=int(en),anchor=anchor.tolist()))
    # Root-only translation locks retain all bone lengths and limb rotations.
    for run in runs:
        st,en,s=run['start'],run['end'],run['side'];delta=np.array(run['anchor'])-world_d[st:en,[6,3][s]];world_d[st:en]+=delta[:,None]
    local_after=np.einsum('tji,tkj->tki',R,world_d-origin[:,None]);uvafter=project(local_after,K)
    def metrics(world,local):
        err=np.linalg.norm(project(local,K)-uv,axis=-1);valid=conf>.5;l=lengths(world);vel=np.linalg.norm(np.diff(world[:,[6,3],:2],axis=0),axis=-1)*30;mask=contacts[1:]&contacts[:-1]
        return dict(reprojection_mean_px=float(err[valid].mean()),reprojection_median_px=float(np.median(err[valid])),jitter_mean_m_s2=float(np.linalg.norm(np.diff(world,n=2,axis=0),axis=-1).mean()*900),bone_length_cv_percent=float(np.mean(np.std(l,axis=0)/np.mean(l,axis=0))*100),planted_foot_sliding_m_s=float(vel[mask].mean()) if mask.any() else None,planted_samples=int(mask.sum()),below_assumed_floor_frames=int(np.sum(np.min(world[:,[3,6],2],axis=1)<floor-.03)))
    results={'a_mediapipe':metrics(world_a,ca),'b_rtmw':dict(status='NOT RUN: pretrained whole-body weights not cleared for commercial use; task requires commercial permission.'),'c_motionbert':metrics(world_c,cc),'chosen':metrics(world_d,local_after)}
    # Hands use independent world directions; face channels retain original frame numbers.
    hand_data={};hand_valid={}
    for side in ['Left','Right']:
        values=[];valid=[]
        for row in rows:
            h=next((h for h in row['hands'] if h['side']==side),None);valid.append(h is not None);values.append(h['world'] if h else np.full((21,3),np.nan))
        hand_data[side]=smooth(fill(values));hand_valid[side]=valid
    facenames=sorted(set(k for r in rows for k in r['face']));faces={k:fill([r['face'].get(k,np.nan) for r in rows]).tolist() for k in facenames}
    fm=fill([r['face_matrix'] if r['face_matrix'] is not None else np.full((4,4),np.nan) for r in rows]);head=Rotation.from_matrix(fm[:,:3,:3]).as_quat()
    peak_report=timing_peaks(uv,uvafter)
    write('metrics.json',dict(candidates=results,per_part=choice,reference='MediaPipe image observations; NOT ground truth; no independent 2D detector after RTMW licence exclusion',resolution=[540,960],fps=30,common_joints='H36M 17, confidence > .5, in-image only; world metrics all 17',contacts=runs,contact_caveat='Feet mostly cropped. No valid planted samples means unmeasurable, not zero sliding.',camera=camfile.name,filter='Symmetric Savitzky-Golay 5/2; significant image extrema anchored; fixed-length direction reconstruction',peak_events=peak_report,max_peak_shift_frames=max([abs(e['shift']) for e in peak_report],default=0),seconds=time.perf_counter()-start))
    np.savez_compressed(HERE/'motion.npz',a_world=world_a,c_world=world_c,chosen_world=world_d,uv=uv,conf=conf,camera=matrices,K=K,contacts=contacts,left_hand=hand_data['Left'],right_hand=hand_data['Right'],head_quaternion=head)
    write('animation.json',dict(fps=30,frames=369,height_m=1.65,camera_file=camfile.name,ground_z=floor,world=world_d.tolist(),baseline_world=world_a.tolist(),camera=matrices.tolist(),K=K.tolist(),hand_world={k:v.tolist() for k,v in hand_data.items()},hand_detected=hand_valid,face=faces,face_matrix=fm.tolist(),detected=[bool(r['pose']) for r in rows],contacts=runs))
    print(json.dumps(results,indent=2));print('prepared',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
