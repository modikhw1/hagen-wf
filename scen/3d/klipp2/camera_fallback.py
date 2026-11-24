"""Masked SIFT two-view reconstruction + per-frame PnP. Monocular scale is inferred.

Never overwrites the parallel libmv kamera.json. Writes kamera-fallback.json.
"""
from pathlib import Path
import json,time
import numpy as np
import cv2
from scipy.spatial.transform import Rotation,Slerp
from scipy.signal import savgol_filter
HERE=Path(__file__).resolve().parent
def main():
    start=time.perf_counter();cv2.setNumThreads(4);masks=np.load(HERE/'masker.npy');sift=cv2.SIFT_create(nfeatures=3000,contrastThreshold=.025)
    frames=[]
    for i in range(369):
        im=cv2.imread(str(HERE/'source'/f'{i:04d}.jpg'),0);mask=255-cv2.resize(masks[i].astype('uint8')*255,(540,960),interpolation=cv2.INTER_NEAREST);mask[600:680]=0 # source watermark
        k,d=sift.detectAndCompute(im,mask);frames.append((np.float32([v.pt for v in k]),d))
    K=np.array([[780,0,270],[0,780,480],[0,0,1.]],float);match=cv2.BFMatcher()
    def pairs(i,j):
        a,b=frames[i],frames[j]
        if a[1] is None or b[1] is None or len(b[1])<2:return np.array([],int),np.array([],int)
        ms=match.knnMatch(a[1],b[1],k=2);ms=[pair[0] for pair in ms if len(pair)==2 and pair[0].distance<.7*pair[1].distance]
        return np.array([m.queryIdx for m in ms]),np.array([m.trainIdx for m in ms])
    best=None
    for base in [15,60]:
        for end in [120,180,240,330]:
            ii,jj=pairs(base,end)
            if len(ii)<30:continue
            a,b=frames[base][0][ii],frames[end][0][jj];E,mask=cv2.findEssentialMat(a,b,K,method=cv2.RANSAC,prob=.999,threshold=1.0)
            n,R,t,mask=cv2.recoverPose(E,a,b,K,mask=mask)
            if best is None or n>best[0]:best=(n,base,end,ii,jj,R,t,mask)
    n,base,end,ii,jj,R,t,mask=best;good=mask.ravel()>0;ii=ii[good];jj=jj[good]
    P0=K@np.c_[np.eye(3),np.zeros(3)];P1=K@np.c_[R,t];X=cv2.triangulatePoints(P0,P1,frames[base][0][ii].T,frames[end][0][jj].T);X=(X[:3]/X[3]).T
    # Initial camera-to-background distance is assumed 7m. Metric scale cannot be recovered from one video.
    scale=7/np.median(X[:,2]);X*=scale
    lookup={int(k):v for k,v in zip(ii,X)};cams=[];errors=[];counts=[];valid=[];observations=[]
    for i in range(369):
        aa,bb=pairs(base,i);keep=np.array([k in lookup for k in aa],dtype=bool);aa,bb=aa[keep],bb[keep]
        if len(aa)<10: cams.append(None);continue
        obj=np.float64([lookup[int(k)] for k in aa]);uv=frames[i][0][bb]
        ok,rv,tv,inliers=cv2.solvePnPRansac(obj,uv,K,None,iterationsCount=150,reprojectionError=2.0,confidence=.999,flags=cv2.SOLVEPNP_EPNP)
        if not ok or len(inliers)<10:cams.append(None);continue
        ix=inliers.ravel();rv,tv=cv2.solvePnPRefineLM(obj[ix],uv[ix],K,None,rv,tv)
        rr=cv2.Rodrigues(rv)[0];C=-rr.T@tv[:,0];proj=cv2.projectPoints(obj[ix],rv,tv,K,None)[0][:,0];err=np.linalg.norm(proj-uv[ix],axis=1)
        cams.append((rr.T,C));valid.append(i);errors.extend(err.tolist());counts.append(len(ix));observations.append((i,obj[ix],uv[ix]))
    if len(valid)<100:raise RuntimeError(f'Only {len(valid)} PnP frames; camera not usable')
    rotations=Rotation.from_matrix([cams[i][0] for i in valid]);tt=np.clip(np.arange(369),valid[0],valid[-1]);rot=Slerp(valid,rotations)(tt).as_matrix();centers=np.array([cams[i][1] for i in valid]);cs=np.stack([np.interp(np.arange(369),valid,centers[:,k]) for k in range(3)],axis=1)
    # Symmetric filter suppresses independent PnP depth noise; report the resulting reprojection error too.
    cs=savgol_filter(cs,9,2,axis=0);rot=Rotation.from_rotvec(savgol_filter(Rotation.from_matrix(rot).as_rotvec(),9,2,axis=0)).as_matrix();clean_errors=[]
    for i,obj,uv in observations:
        x=(rot[i].T@(obj-cs[i]).T).T;q=x[:,:2]/x[:,2:]*780+[270,480];clean_errors.extend(np.linalg.norm(q-uv,axis=-1).tolist())
    # Camera-CV to Blender world: x right, y forward, z up; approximate 5deg downward view and 1.5m initial height.
    B=np.array([[1,0,0],[0,0,1],[0,-1,0.]])@Rotation.from_euler('x',-5,degrees=True).as_matrix();cv_to_bl=np.diag([1,-1,-1.]);mat=np.tile(np.eye(4),(369,1,1));mat[:,:3,:3]=B@rot@cv_to_bl;mat[:,:3,3]=(B@cs.T).T+[0,0,1.5]
    result=dict(schema='klipp2-camera/1',method='OpenCV masked SIFT essential + PnP; fallback, not libmv',fps=30,width=540,height=960,focal_length_mm=52.,sensor_width_mm=36.,sensor_fit='HORIZONTAL',K=K.tolist(),solve_error_px=float(np.mean(errors)),registered_frames=len(valid),interpolated_frames=[i for i in range(369) if i not in valid],points_world=((B@X.T).T+[0,0,1.5]).tolist(),metric_scale='Assumed background depth 7m, camera height 1.5m and initial tilt 5deg. Not calibrated to floor.',base_frame=base,end_frame=end,frames=[dict(frame=i,matrix_world=m.tolist(),lens_mm=52.,sensor_width_mm=36.) for i,m in enumerate(mat)],seconds=time.perf_counter()-start)
    result['raw_solve_error_px']=result['solve_error_px'];result['solve_error_px']=float(np.mean(clean_errors));result['filter']='Symmetric Savitzky-Golay 9/2 on translation and rotation vector'
    (HERE/'kamera-fallback.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k not in ['frames','points_world','interpolated_frames']},flush=True)
if __name__=='__main__':main()
