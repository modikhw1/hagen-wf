"""Exact baked-skeleton FK, CPU autograd. Launched by headless optimera.py.

No time resampling; no camera, shape, finger or facial-expression parameters.
Silhouette surrogate uses skinned mesh samples and source-mask distance/coverage.
Native Blender masks are measured independently by verifiera_opt.py.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from common import *
import copy, time, argparse
import cv2
import torch
import torch.nn.functional as F
torch.set_num_threads(4)
cv2.setNumThreads(2)
DT=torch.float64
def ten(a):return torch.as_tensor(np.asarray(a),dtype=DT)
def rot(v):
    # Euler XYZ increments, exact identity and well-behaved derivatives at zero.
    x,y,z=v.unbind(-1);cx,cy,cz=x.cos(),y.cos(),z.cos();sx,sy,sz=x.sin(),y.sin(),z.sin()
    return torch.stack([cy*cz,cz*sx*sy-cx*sz,sx*sz+cx*cz*sy,cy*sz,cx*cz+sx*sy*sz,cx*sy*sz-cz*sx,-sy,cy*sx,cx*cy],-1).reshape(*v.shape[:-1],3,3)
def rot4(v):
    r=rot(v);zero=torch.zeros((*v.shape[:-1],3,1),dtype=DT);last=torch.zeros((*v.shape[:-1],1,4),dtype=DT);last[...,0,3]=1
    return torch.cat([torch.cat([r,zero],-1),last],-2)

class Shot:
    def __init__(self,bake,asset,shot,targets):
        self.fs=main_frames(bake,shot['id']);self.asset=asset;self.shot=shot;self.T=len(self.fs);aid=self.fs[0]['mainActor'];self.aid=aid
        self.names=list(asset['bones']);self.parents=[self.names.index(asset['bones'][n]['parent']) if asset['bones'][n]['parent'] else -1 for n in self.names]
        self.vi={self.names.index(n):i for i,n in enumerate(VARIABLE_BONES)}
        self.roots=ten([mat(f['actors'][aid]['root']['matrix']) for f in self.fs])
        worlds=np.array([[mat(f['actors'][aid]['bones'][n]['world']) for n in self.names] for f in self.fs]);self.oldworld=worlds
        rel=[]
        for j,p in enumerate(self.parents):
            parent=worlds[:,p] if p>=0 else self.roots.numpy()
            rel.append(np.linalg.inv(parent)@worlds[:,j])
        self.rel=ten(np.stack(rel,axis=1));self.oldroot=self.roots.clone()
        self.nose=ten([(trs(f['actors'][aid]['face'])@np.r_[asset['faceLandmarks']['nose'],1]) for f in self.fs])
        self.jids=[self.names.index('Head' if n=='nose' else n) for n in FEATURES]
        pos,R,ff=camera(shot['source']['camera']);self.cpos=ten(pos);self.cR=ten(R);self.focal=ff
        self.target=ten([targets[f['i']]['xy'] for f in self.fs]);self.weights=ten([targets[f['i']]['confidence'] for f in self.fs])
        self.weights[:,7:]*=.15 # 40 finger joints must not overwhelm seven core landmarks
        self.baseuv=self.project(ten([features(f['actors'][aid],asset) for f in self.fs]))
        self.baseacc=torch.linalg.vector_norm(torch.diff(self.baseuv[:,:7],n=2,dim=0),dim=-1).mean().detach()
        self.basespeed=torch.linalg.vector_norm(torch.diff(self.baseuv[:,[0,5,6]],dim=0),dim=-1)
        self.speed_sign=torch.sign(torch.diff(self.basespeed,dim=0))
        self.mesh_samples()
        masks=[];sdfs=[];foreground=[]
        rng=np.random.default_rng(20261109)
        for f in self.fs:
            m=cv2.imread(str(HERE/'gt/masks'/f'{f["i"]:04d}.png'),0)>127
            masks.append(m)
            dist=cv2.distanceTransform((~m).astype(np.uint8),cv2.DIST_L2,5)
            sdfs.append(cv2.resize(dist,(144,256),interpolation=cv2.INTER_AREA))
            ys,xs=np.where(m);pick=rng.choice(len(xs),96,replace=False);foreground.append(np.stack([xs[pick],ys[pick]],-1))
        self.sdf=ten(np.array(sdfs))[:,None];self.foreground=ten(foreground)
        with torch.no_grad():
            vertices=self.skin(ten(worlds));vuv=self.project(vertices)
            # Only near-visible surface samples. Hidden legs below tables must not
            # be pulled into the mask; final rendered IoU still includes occlusion.
            d=self.sample_distance(vuv)
            self.visible=((d<55)&(vuv[...,0]>=0)&(vuv[...,0]<576)&(vuv[...,1]>=0)&(vuv[...,1]<1024)).to(DT)

    def mesh_samples(self):
        m=next(m for m in self.asset['meshes'] if m['name']=='Beta_Surface')
        ids=np.unique(np.array(m['indices']));rng=np.random.default_rng(124)
        ids=rng.choice(ids,min(700,len(ids)),replace=False)
        v=np.c_[np.array(m['positions']).reshape(-1,3)[ids],np.ones(len(ids))]
        bind=mat(m['bindMatrix']);iv=np.array([mat(x) for x in m['boneInverses']]);si=np.array(m['skinIndices']).reshape(-1,4)[ids].astype(int)
        self.skinids=torch.tensor([[self.names.index(m['boneNames'][k]) for k in row] for row in si],dtype=torch.long)
        self.skinweights=ten(np.array(m['skinWeights']).reshape(-1,4)[ids])
        self.localverts=ten(np.einsum('vkij,vj->vki',iv[si]@bind,v))
    def skin(self,w):
        return (torch.einsum('tvkij,vkj->tvki',w[:,self.skinids],self.localverts)*self.skinweights[None,:,:,None]).sum(2)[...,:3]
    def project(self,p):
        q=(p-self.cpos)@self.cR;z=(-q[...,2]).clamp(min=.1)
        return torch.stack([288+self.focal*q[...,0]/z,512-self.focal*q[...,1]/z],-1)
    def sample_distance(self,uv):
        grid=uv/ten([575,1023])*2-1
        return F.grid_sample(self.sdf,grid[:,:,None,:],mode='bilinear',padding_mode='border',align_corners=True)[:,0,:,0]
    def fk(self,x):
        root=self.roots.clone();root[:,:3,:3]=rot(x[:,3:6])@self.roots[:,:3,:3];root[:,:3,3]=self.roots[:,:3,3]+x[:,:3]
        rs=rot4(x[:,6:].reshape(self.T,-1,3));w=[]
        for j,p in enumerate(self.parents):
            local=self.rel[:,j]
            if j in self.vi: local=local@rs[:,self.vi[j]]
            w.append((root if p<0 else w[p])@local)
        w=torch.stack(w,1);joints=w[:,self.jids,:3,3].clone()
        joints[:,0]=(w[:,self.names.index('Head')]@self.nose[:,:,None])[:,:3,0]
        return root,w,joints,self.project(joints)
    def objective(self,x,temporal=1):
        root,w,joints,uv=self.fk(x)
        residual=torch.linalg.vector_norm(uv-self.target,dim=-1)
        reproj=((torch.sqrt(1+(residual/12)**2)-1)*self.weights).sum()/self.weights.sum()
        vuv=self.project(self.skin(w));distance=self.sample_distance(vuv)
        outside=(distance.square()*self.visible).sum()/(self.visible.sum()+1)/400
        # Source coverage approximated by closest visible skinned surface samples.
        d=torch.cdist(self.foreground,vuv)+(1-self.visible[:,None])*1000
        cover=d.min(-1).values.clamp(max=80).square().mean()/1600
        delta=uv-self.baseuv
        dv=torch.diff(delta,dim=0);da=torch.diff(delta,n=2,dim=0)
        acc=torch.linalg.vector_norm(torch.diff(uv[:,:7],n=2,dim=0),dim=-1).mean()
        speed=torch.linalg.vector_norm(torch.diff(uv[:,[0,5,6]],dim=0),dim=-1)
        ds=torch.diff(speed,dim=0)
        ordering=F.relu(-self.speed_sign*ds+.002).square().mean()
        acceleration=F.relu(acc-self.baseacc*.997).square()
        # Physical supports as soft constraints; dimensions fixed, camera fixed.
        hips=w[:,self.names.index('Hips'),:3,3]
        if self.aid in ['A','B']:
            support=((hips[:,1]-.5975)/.02).square().mean()
            # Seat rectangle in scene coordinates, pelvis centre offset 12 cm.
            origin=self.oldworld[:,0,:3,3]
            support+=F.relu(torch.linalg.vector_norm(hips[:,[0,2]]-ten(origin[:,[0,2]]),dim=-1)-.17).square().mean()*200
        else:
            toes=w[:,[self.names.index('LeftToeBase'),self.names.index('RightToeBase')],1,3]
            support=((toes-.03)/.025).square().mean()
        reg=(x[:,:3]/.18).square().mean()+(x[:,3:6]/.15).square().mean()+(x[:,6:]/.6).square().mean()
        temporal_loss=.003*dv[:,:7].square().mean()+.025*da[:,:7].square().mean()+20*acceleration+4*ordering
        loss=reproj+.1*outside+.08*cover+.04*reg+.04*support+temporal*temporal_loss
        return loss,dict(reproj=float(reproj.detach()),silhouette=float((outside+cover).detach()),acc=float(acc.detach()),ordering=float(ordering.detach())),uv

def update_bake(out,shot,x):
    with torch.no_grad():r,w,j,uv=shot.fk(ten(x))
    r,w,j,uv=[t.numpy() for t in [r,w,j,uv]]
    for k,old in enumerate(shot.fs):
        f=out['frames'][old['i']];a=f['actors'][shot.aid]
        a['root'].update(decompose(r[k]));a['root']['matrix']=flat(r[k])
        for bi,n in enumerate(shot.names):
            a['bones'][n]['world']=flat(w[k,bi])
            if n in VARIABLE_BONES:
                vi=VARIABLE_BONES.index(n);q=Rotation.from_quat(old['actors'][shot.aid]['bones'][n]['quaternion'])*Rotation.from_matrix(rot(ten(x[k,6+vi*3:9+vi*3])).numpy())
                a['bones'][n]['quaternion']=q.as_quat().tolist()
        for n,idx in BODY.items():
            ji=FEATURES.index(n);a['jointsWorld'][idx]=j[k,ji].tolist();f['joints'][idx]=[*uv[k,ji].tolist(),f['joints'][idx][2]] if len(f['joints'][idx])>2 else uv[k,ji].tolist()
        for side,indices in [('Left',[17,19,21]),('Right',[18,20,22])]:
            for finger,idx in zip(['Pinky','Index','Thumb'],indices):a['jointsWorld'][idx]=j[k,FEATURES.index(f'{side}Hand{finger}4')].tolist()
        # Remaining body landmarks follow their owning anatomical transform.
        for n,idx in [('LeftUpLeg',23),('RightUpLeg',24),('LeftLeg',25),('RightLeg',26),('LeftFoot',27),('RightFoot',28),('LeftToeBase',31),('RightToeBase',32)]:a['jointsWorld'][idx]=w[k,shot.names.index(n),:3,3].tolist()
        for idx,landmark in [(0,'nose'),(7,'earL'),(8,'earR')]:
            a['jointsWorld'][idx]=(w[k,shot.names.index('Head')]@trs(a['face'])@np.r_[shot.asset['faceLandmarks'][landmark],1])[:3].tolist()
        for idx,p in enumerate(a['jointsWorld']):
            if p is not None and f['joints'][idx] is not None:f['joints'][idx][:2]=project(np.array(p),shot.shot['source']['camera']).tolist()

def attach_props(out,before,spec):
    events=read(HERE/'gt/events-checked.json')['events'];byprop={p['id']:p for p in spec['props']};log=[]
    for f,old in zip(out['frames'],before['frames']):
        shot=next(s for s in spec['shots'] if s['id']==f['shot']);moves={}
        for p in spec['props']:
            attach=shot.get('propOverrides',{}).get(p['id'],{}).get('attach',p.get('attach'))
            if not attach:continue
            aid=attach['actor']
            if not f['actors'][aid]['visible']:continue
            hand=attach.get('hand','Left' if attach.get('joint',15)==15 else 'Right')+'Hand'
            a=f['actors'][aid];b=old['actors'][aid];newhand=mat(a['bones'][hand]['world']);oldhand=mat(b['bones'][hand]['world'])
            prop=newhand@np.linalg.inv(oldhand)@mat(old['props'][p['id']]['matrix'])
            active=any(e['type']=='hold' and e['object']==p['id'] and e['shot']==f['shot'] and e['startSec']<=f['sourceT']<e['endSec'] for e in events)
            delta=np.zeros(3)
            if active:
                # Palm contact against actual prop's oriented box surface, not its
                # centre (a burger's centre is necessarily inside the solid).
                grip=np.mean([mat(a['bones'][hand+n]['world'])[:3,3] for n in ['Index1','Middle1','Ring1']],axis=0)
                local=(np.linalg.inv(prop)@np.r_[grip,1])[:3];nearest=np.clip(local,-np.array(p['dims'])/2,np.array(p['dims'])/2)
                nearworld=(prop@np.r_[nearest,1])[:3];v=grip-nearworld;dist=np.linalg.norm(v)
                if dist>.02:delta=v*(dist-.02)/dist;prop[:3,3]+=delta
                moves[p['id']]=delta
                log.append(dict(i=f['i'],prop=p['id'],offset_m=float(np.linalg.norm(delta))))
            if p['id']=='B:burger_wrap' and 'B:burger' in moves:prop[:3,3]+=moves['B:burger']
            f['props'][p['id']].update(decompose(prop));f['props'][p['id']]['matrix']=flat(prop)
    return log

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--iterations',type=int,default=360);ap.add_argument('--shots',nargs='*');args=ap.parse_args()
    bake=read(HERE.parent/'bake.json');assets=read(HERE.parent/bake['assets']);spec=read(ROOT/'scen3d.json');targets=read(HERE/'gt/targets.json')['frames']
    out=copy.deepcopy(bake);out['assets']='../'+bake['assets'];report=[];start=time.perf_counter()
    for shot in spec['shots']:
        sid=shot['id'];aid=main_frames(bake,sid)[0]['mainActor'];prob=Shot(bake,assets['actors'][aid],shot,targets)
        cache=HERE/f'parameters-{sid}.npy'
        if args.shots and sid not in args.shots and cache.exists():xnp=np.load(cache)
        else:
            # Smooth *corrections*, never low-pass the existing performance.
            # Cubic-in-time parameter increments prevent alternating-frame
            # optimizer noise while retaining every original frame and peak.
            tt=torch.linspace(-1,1,prob.T,dtype=DT)
            basis=torch.stack([torch.ones_like(tt),tt,tt**2,tt**3],1)
            coeff=torch.zeros((4,6+len(VARIABLE_BONES)*3),dtype=DT,requires_grad=True)
            opt=torch.optim.LBFGS([coeff],lr=.8,max_iter=args.iterations,history_size=20,line_search_fn='strong_wolfe',tolerance_grad=1e-7,tolerance_change=1e-9)
            counter=[0]
            def closure():
                opt.zero_grad();loss,details,uv=prob.objective(basis@coeff,temporal=2)
                loss.backward();counter[0]+=1
                if counter[0]%50==0 or counter[0]==1:print(sid,counter[0],round(float(loss.detach()),4),details,flush=True)
                return loss
            opt.step(closure)
            xnp=(basis@coeff).detach().numpy();np.save(cache,xnp)
        update_bake(out,prob,xnp)
        before=prob.baseuv.numpy();after=np.stack([project(features(out['frames'][f['i']]['actors'][aid],assets['actors'][aid]),shot['source']['camera']) for f in prob.fs])
        weight=np.array([targets[f['i']]['confidence'] for f in prob.fs])>0
        e0=np.linalg.norm(before-prob.target.numpy(),axis=-1);e1=np.linalg.norm(after-prob.target.numpy(),axis=-1)
        row=dict(shot=sid,median_before=float(np.median(e0[weight])),median_after=float(np.median(e1[weight])),jitter_before=motion_metrics(before),jitter_after=motion_metrics(after),peak_shift=peak_shift(before,after)[0]);report.append(row);print(row,flush=True)
    props=attach_props(out,bake,spec)
    out['optimization']=dict(method='CPU exact skeleton FK; immutable source cameras; native Blender verification separately',source_bake_sha256=sha(HERE.parent/'bake.json'),targets_sha256=sha(HERE/'gt/targets.json'),seconds=time.perf_counter()-start)
    (HERE/'bake-opt.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
    write(HERE/'fit-report.json',dict(shots=report,prop_offsets=props,seconds=time.perf_counter()-start))

if __name__=='__main__':main()
