"""MotionBERT Apache-2.0 pose checkpoint; overlapping temporal windows on CPU."""
from pathlib import Path
import os,sys,json,time
os.environ['CUDA_VISIBLE_DEVICES']=''
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'deps/MotionBERT'))
import numpy as np
import torch
from lib.model.DSTformer import DSTformer

def fill(a):
    a=np.array(a,float);flat=a.reshape(len(a),-1)
    for k in range(flat.shape[1]):
        good=np.isfinite(flat[:,k]);flat[:,k]=np.interp(np.arange(len(a)),np.flatnonzero(good),flat[good,k])
    return flat.reshape(a.shape)

def mp_to_h36(p):
    a=np.zeros((len(p),17,p.shape[-1]));a[:,0]=(p[:,23]+p[:,24])/2
    for dst,src in {1:24,2:26,3:28,4:23,5:25,6:27,9:0,11:11,12:13,13:15,14:12,15:14,16:16}.items():a[:,dst]=p[:,src]
    a[:,8]=(p[:,11]+p[:,12])/2;a[:,7]=(a[:,0]+a[:,8])/2
    a[:,10]=(p[:,7]+p[:,8])/2
    return a

def main():
    start=time.perf_counter();torch.set_num_threads(4)
    rows=json.loads((HERE/'mediapipe.json').read_text())['frames']
    p=fill([r['pose'] if r['pose'] else np.full((33,3),np.nan) for r in rows]);a=mp_to_h36(p);a[:,:,:2]=(a[:,:,:2]*[540,960]-[270,480])/270
    conf=fill([r['visibility'] if r['visibility'] else np.full(33,np.nan) for r in rows]);a[:,:,2]=mp_to_h36(conf[:,:,None])[:,:,0]
    source='MediaPipe 2D (RTMW excluded pending commercial-use clarification)'
    if (HERE/'rtmw.npz').exists():
        r=np.load(HERE/'rtmw.npz');q=r['uv'];c=r['scores'];a=np.zeros((len(p),17,3));idx={1:12,2:14,3:16,4:11,5:13,6:15,9:0,11:5,12:7,13:9,14:6,15:8,16:10}
        for d,s in idx.items():a[:,d,:2]=q[:,s];a[:,d,2]=c[:,s]
        a[:,0]=(a[:,1]+a[:,4])/2;a[:,8]=(a[:,11]+a[:,14])/2;a[:,7]=(a[:,0]+a[:,8])/2
        a[:,10,:2]=(q[:,3]+q[:,4])/2;a[:,10,2]=(c[:,3]+c[:,4])/2;a[:,:,:2]=(a[:,:,:2]-[270,480])/270;source='RTMW 2D'
    model=DSTformer(dim_in=3,dim_out=3,dim_feat=512,dim_rep=512,depth=5,num_heads=8,mlp_ratio=2,norm_layer=torch.nn.LayerNorm,maxlen=243,num_joints=17)
    ck=torch.load(HERE/'deps/MotionBERT/checkpoint/pose3d/FT_MB_release_MB_ft_h36m/best_epoch.bin',map_location='cpu',weights_only=False)
    model.load_state_dict({k.replace('module.',''):v for k,v in ck['model_pos'].items()});model.eval()
    result=np.zeros((len(a),17,3));weight=np.zeros((len(a),1,1));flip=[0,4,5,6,1,2,3,7,8,9,10,14,15,16,11,12,13]
    with torch.inference_mode():
        for st in [0,126]:
            x=torch.tensor(a[st:st+243],dtype=torch.float32)[None];y=model(x).numpy()[0]
            xx=x.clone();xx[:,:,:,0]*=-1;xx=xx[:,:,flip];yy=model(xx).numpy()[0];yy[:,:,0]*=-1;yy=yy[:,flip];y=(y+yy)/2;y-=y[:,0:1]
            w=np.minimum(np.arange(243)+1,np.arange(243)[::-1]+1).clip(1,60)[:,None,None];result[st:st+243]+=y*w;weight[st:st+243]+=w
            print('MotionBERT window',st,round(time.perf_counter()-start,1),flush=True)
    result/=weight
    np.savez_compressed(HERE/'motionbert.npz',xyz=result,input=a)
    (HERE/'motionbert-timing.json').write_text(json.dumps(dict(seconds=time.perf_counter()-start,input=source,frames=len(a),window=243,overlap=117,flip_augmentation=True,device='cpu'),indent=2))

if __name__=='__main__':main()
