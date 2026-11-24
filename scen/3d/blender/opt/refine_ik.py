"""Per-frame damped least-squares IK with exact analytic projection Jacobian.
Refines saved timing parameters; solves hand orientation without moving wrists.
"""
from fit_cpu import *
from scipy.optimize import least_squares

def rotation(v):
    x,y,z=v;cx,cy,cz=np.cos(v);sx,sy,sz=np.sin(v)
    rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    dx=np.array([[0,0,0],[0,-sx,-cx],[0,cx,-sx]]);dy=np.array([[-sy,0,cy],[0,0,0],[-cy,0,-sy]]);dz=np.array([[-sz,-cz,0],[cz,-sz,0],[0,0,0]])
    return rz@ry@rx,[rz@ry@dx,rz@dy@rx,dz@ry@rx]

class FrameIK:
    def __init__(self,prob,k,prior):
        self.prob=prob;self.k=k;self.prior=prior;self.oldroot=prob.oldroot[k].numpy();self.rel=prob.rel[k].numpy();self.cpos=prob.cpos.numpy();self.cR=prob.cR.numpy();self.ff=prob.focal
        self.ancestors=[]
        self.extra=[prob.names.index(n) for n in ['LeftUpLeg','RightUpLeg','LeftToeBase','RightToeBase']]
        for j in prob.jids+self.extra:
            aa=[]
            while j>=0:aa.append(j);j=prob.parents[j]
            self.ancestors.append(aa)
        self.last=None
    def calc(self,x):
        if self.last is not None and np.array_equal(x,self.last[0]):return self.last[1:]
        p=self.prob;root=self.oldroot.copy();R,rd=rotation(x[3:6]);root[:3,:3]=R@self.oldroot[:3,:3];root[:3,3]+=x[:3]
        w=[];derivatives={}
        for j,parent in enumerate(p.parents):
            parentm=root if parent<0 else w[parent];base=parentm@self.rel[j];m=base.copy()
            if j in p.vi:
                v=p.vi[j];r,dr=rotation(x[6+v*3:9+v*3]);m[:3,:3]=base[:3,:3]@r
                derivatives[j]=[base[:3,:3]@d for d in dr]
            if p.names[j]=='Head':
                # Original MediaPipe head/gaze orientation is already valuable.
                # A nose-only objective otherwise exploits head rotation to move
                # the nose while making the rendered face look away.
                m[:3,:3]=p.oldworld[self.k,j,:3,:3]
                derivatives[j]=[np.zeros((3,3)) for _ in range(3)]
            w.append(m)
        w=np.array(w);pts=w[p.jids+self.extra,:3,3].copy();pts[0]=(w[p.names.index('Head')]@p.nose[self.k].numpy())[:3]
        q=(pts-self.cpos)@self.cR;z=-q[:,2];uv=np.stack([288+self.ff*q[:,0]/z,512-self.ff*q[:,1]/q[:,2]*-1],-1)
        # y = 512 + f*q_y/q_z.
        uv[:,1]=512+self.ff*q[:,1]/q[:,2]
        dp=np.zeros((len(pts),3,len(x)));dp[:,:,:3]=np.eye(3)
        anchors=pts.copy();anchors[0]=w[p.names.index('Head'),:3,3]
        invroot=np.linalg.inv(root);local=(np.c_[anchors,np.ones(len(pts))]@invroot.T)[:,:3]
        for k,d in enumerate(rd):dp[:,:,3+k]=local@(d@self.oldroot[:3,:3]).T
        for j,ds in derivatives.items():
            mask=np.array([j in a for a in self.ancestors]);local=(np.c_[anchors[mask],np.ones(mask.sum())]@np.linalg.inv(w[j]).T)[:,:3]
            for k,d in enumerate(ds):dp[mask,:,6+p.vi[j]*3+k]=local@d.T
        dc=np.einsum('kav,ab->kbv',dp,self.cR)
        jac=np.empty((len(pts),2,len(x)))
        jac[:,0]=self.ff*(-dc[:,0]/q[:,2,None]+q[:,0,None]*dc[:,2]/q[:,2,None]**2)
        jac[:,1]=self.ff*(dc[:,1]/q[:,2,None]-q[:,1,None]*dc[:,2]/q[:,2,None]**2)
        self.last=(x.copy(),uv[:len(FEATURES)],jac[:len(FEATURES)],w,root,pts[-4:],dp[-4:],pts[:len(FEATURES)],dp[:len(FEATURES)])
        return self.last[1:]
    def solve_core(self,desired):
        # Tiny nullspace prior removes singularity without compromising pixel fit.
        regularization=1e-5
        def support(x):
            result=self.calc(x);points,derivative=result[4:6]
            if self.prob.aid=='C':return (points[2:,1]-.03)*1000,derivative[2:,1,:]*1000
            pelvis=points[:2].mean(0);d=derivative[:2].mean(0)
            centre=self.prob.oldworld[self.k,self.extra[:2],:3,3].mean(0)
            horizontal=pelvis[[0,2]]-centre[[0,2]]
            residual=np.r_[(pelvis[1]-.5975)*1000,np.maximum(abs(horizontal)-.22,0)*1000]
            jacobian=np.vstack([d[1]*1000,d[[0,2]]*(np.sign(horizontal)*(abs(horizontal)>.22))[:,None]*1000])
            return residual,jacobian
        # Keep nose/wrist trajectories exact; the silhouette/head-size ambiguity
        # is controlled by a source-pose depth prior, not by changing the camera.
        coreweights=np.array([50,1,1,1,1,50,50])[:,None]
        original=features(self.prob.fs[self.k]['actors'][self.prob.aid],self.prob.asset)
        di=np.array([0,5,6]);zaxis=self.cR[:,2]
        def depth(x):
            result=self.calc(x);pts,dp=result[6:8]
            return ((pts[di]-original[di])@zaxis)*200,np.einsum('kav,a->kv',dp[di],zaxis)*200
        root_scale=np.array([.10,.10,.10,.25,.25,.25])
        root_jac=np.zeros((6,len(self.prior)));root_jac[:,:6]=np.diag(1/root_scale)
        def fun(x):return np.r_[((self.calc(x)[0][:7]-desired)*coreweights).ravel(),support(x)[0],depth(x)[0],x[:6]/root_scale,(x-self.prior)*regularization]
        def jac(x):return np.vstack([(self.calc(x)[1][:7]*coreweights[:,:,None]).reshape(14,-1),support(x)[1],depth(x)[1],root_jac,np.eye(len(x))*regularization])
        result=least_squares(fun,self.prior,jac=jac,max_nfev=80,xtol=1e-7,ftol=1e-7,gtol=1e-7,method='trf')
        x=result.x.copy();w=self.calc(x)[2];bi=self.prob.names.index('Head');parent=self.prob.parents[bi]
        base=w[parent]@self.rel[bi];delta=np.linalg.inv(base[:3,:3])@self.prob.oldworld[self.k,bi,:3,:3]
        vi=VARIABLE_BONES.index('Head');x[6+vi*3:9+vi*3]=Rotation.from_matrix(delta).as_euler('xyz')
        return x,float(abs(self.calc(x)[0][:7]-desired).max()),result.nfev
    def solve_hands(self,x,truth,weight):
        x=x.copy()
        for side in ['Left','Right']:
            v=VARIABLE_BONES.index(side+'Hand');columns=np.arange(6+v*3,9+v*3);ids=np.array([i for i,n in enumerate(FEATURES) if n.startswith(side+'Hand') and i>=7]);valid=weight[ids]>.01;ids=ids[valid]
            if len(ids)<3:continue
            initial=x[columns].copy();ww=np.sqrt(weight[ids,None]);prior=x.copy()
            def fun(r):
                xx=prior.copy();xx[columns]=r;return np.r_[((self.calc(xx)[0][ids]-truth[ids])*ww).ravel(),(r-initial)*.5]
            def jac(r):
                xx=prior.copy();xx[columns]=r;return np.vstack([(self.calc(xx)[1][ids][:,:,columns]*ww[:,:,None]).reshape(-1,3),np.eye(3)*.5])
            result=least_squares(fun,initial,jac=jac,max_nfev=60,loss='soft_l1',f_scale=10,bounds=(initial-1.5,initial+1.5))
            x[columns]=result.x
        return x

def main():
    (HERE/'refine.pid').write_text(str(os.getpid()))
    ap=argparse.ArgumentParser();ap.add_argument('--shots',nargs='*');ap.add_argument('--strength',type=float,default=1);args=ap.parse_args()
    bake=read(HERE.parent/'bake.json');assets=read(HERE.parent/bake['assets']);spec=read(ROOT/'scen3d.json');targets=read(HERE/'gt/targets.json')['frames']
    out=copy.deepcopy(bake);out['assets']='../'+bake['assets'];report=[];start=time.perf_counter()
    for shot in spec['shots']:
        sid=shot['id'];aid=main_frames(bake,sid)[0]['mainActor'];prob=Shot(bake,assets['actors'][aid],shot,targets);cache=HERE/f'ik-{sid}.npy'
        if args.shots and sid not in args.shots and cache.exists():xnp=np.load(cache)
        else:
            prior=np.load(cache) if cache.exists() else (np.load(HERE/f'timing-{sid}.npy') if (HERE/f'timing-{sid}.npy').exists() else np.load(HERE/f'parameters-{sid}.npy'))
            base=prob.baseuv.numpy();truth=prob.target.numpy();weight=prob.weights.numpy()
            offsets=np.stack([np.median((truth-base)[weight[:,j]>0,j],axis=0) if (weight[:,j]>0).any() else np.zeros(2) for j in range(7)])
            desired=base[:,:7]*.995+base[:,:7].mean(0)*.005+offsets[None]*args.strength
            xs=[];worst=0
            for k in range(prob.T):
                solver=FrameIK(prob,k,prior[k]);x,error,n=solver.solve_core(desired[k]);x=solver.solve_hands(x,truth[k],weight[k]);xs.append(x);worst=max(worst,error)
                if k%25==0:print(sid,k,'IK max residual px',error,'evaluations',n,flush=True)
            xnp=np.array(xs);np.save(cache,xnp);print(sid,'worst core residual',worst,flush=True)
        update_bake(out,prob,xnp)
        b=prob.baseuv.numpy();a=np.stack([project(features(out['frames'][f['i']]['actors'][aid],assets['actors'][aid]),shot['source']['camera']) for f in prob.fs]);w=np.array([targets[f['i']]['confidence'] for f in prob.fs])>0
        es=[np.linalg.norm(q-prob.target.numpy(),axis=-1) for q in [b,a]]
        row=dict(shot=sid,body_median_before=float(np.median(es[0][:,:7][w[:,:7]])),body_median_after=float(np.median(es[1][:,:7][w[:,:7]])),median_before=float(np.median(es[0][w])),median_after=float(np.median(es[1][w])),jitter_before=motion_metrics(b),jitter_after=motion_metrics(a),peak_shift=peak_shift(b,a)[0]);report.append(row);print(row,flush=True)
    props=attach_props(out,bake,spec);out['optimization']=dict(method='CPU exact FK with source-mask objective, confidence keypoints, support priors; per-frame analytic-Jacobian constrained IK preserving original core image-space trajectories up to 0.995 amplitude and constant offsets; palm contact props.',source_bake_sha256=sha(HERE.parent/'bake.json'),targets_sha256=sha(HERE/'gt/targets.json'),seconds=time.perf_counter()-start,strength=args.strength)
    (HERE/'bake-opt.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8');write(HERE/'ik-fit-report.json',dict(shots=report,prop_offsets=props,seconds=time.perf_counter()-start))

if __name__=='__main__':main()
