"""Shared coordinate/schema definitions. three.js Y-up; pixel origin top-left."""
import json, hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.signal import find_peaks
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
BODY={'nose':0,'LeftArm':11,'RightArm':12,'LeftForeArm':13,'RightForeArm':14,'LeftHand':15,'RightHand':16}
COCO={'nose':0,'LeftArm':5,'RightArm':6,'LeftForeArm':7,'RightForeArm':8,'LeftHand':9,'RightHand':10}
FEATURES=list(BODY)
HAND_LM={}
for side in ['Left','Right']:
    for finger,first in [('Thumb',1),('Index',5),('Middle',9),('Ring',13),('Pinky',17)]:
        for k in range(4):
            n=f'{side}Hand{finger}{k+1}';FEATURES.append(n);HAND_LM[n]=(side,first+k)
VARIABLE_BONES=['Spine','Spine1','Spine2','Neck','Head','LeftShoulder','LeftArm','LeftForeArm','LeftHand','RightShoulder','RightArm','RightForeArm','RightHand']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mat(x):return np.array(x,dtype=float).reshape(4,4).T
def flat(x):return np.asarray(x).T.reshape(-1).tolist()
def trs(v):
    m=np.eye(4);m[:3,:3]=Rotation.from_quat(v['quaternion']).as_matrix()*np.array(v['scale'])[None,:];m[:3,3]=v['position'];return m
def decompose(m):
    scale=np.linalg.norm(m[:3,:3],axis=0)
    return dict(position=m[:3,3].tolist(),quaternion=Rotation.from_matrix(m[:3,:3]/scale).as_quat().tolist(),scale=scale.tolist())
def camera(c):
    pos=np.array(c['pos']);z=pos-np.array(c['target']);z/=np.linalg.norm(z)
    x=np.cross(c['up'],z);x/=np.linalg.norm(x);y=np.cross(z,x)
    return pos,np.stack([x,y,z],axis=1),1024/(2*np.tan(np.deg2rad(c['fov'])/2))
def project(points,c):
    p,R,f=camera(c);q=(np.asarray(points)-p)@R
    return np.stack([288+f*q[...,0]/(-q[...,2]),512-f*q[...,1]/(-q[...,2])],axis=-1)
def features(actor,asset):
    w={n:mat(v['world']) for n,v in actor['bones'].items()}
    nose=(w['Head']@trs(actor['face'])@np.r_[asset['faceLandmarks']['nose'],1])[:3]
    return np.stack([nose if n=='nose' else w[n][:3,3] for n in FEATURES])
def motion_metrics(uv):
    # Core body only: fingers are separately reported in keypoint errors.
    acc=np.diff(uv[:,:7],n=2,axis=0)
    return float(np.mean(np.linalg.norm(acc,axis=-1)))
def extrema(x):
    prominence=max(.25,float(np.ptp(x))*.1)
    return {kind:find_peaks(sign*x,prominence=prominence,distance=3)[0] for kind,sign in [('max',1),('min',-1)]}
def peak_shift(before,after):
    records=[];maximum=0
    for j,name in [(0,'head/nose'),(5,'LeftHand'),(6,'RightHand')]:
        speeds=[np.linalg.norm(np.diff(q[:,j],axis=0),axis=-1) for q in [before,after]]
        es=[extrema(x) for x in speeds]
        for kind in ['max','min']:
            a,b=es[0][kind],es[1][kind]
            # Bidirectional: missing/new extrema cannot disappear from the score.
            distances=[int(np.min(abs(v-b))) if len(b) else len(before) for v in a]
            distances += [int(np.min(abs(v-a))) if len(a) else len(before) for v in b]
            shift=max(distances,default=0);maximum=max(maximum,shift)
            records.append(dict(joint=name,type=kind,before=a.tolist(),after=b.tolist(),max_shift=shift))
    return maximum,records
def main_frames(bake,sid):return [f for f in bake['frames'] if f['shot']==sid]
