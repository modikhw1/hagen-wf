"""Suppress uncertain hand-orientation jitter, leaving wrist/head paths exact."""
from fit_cpu import *
from scipy.signal import savgol_filter

def main():
    bake=read(HERE.parent/'bake.json');assets=read(HERE.parent/bake['assets']);spec=read(ROOT/'scen3d.json');targets=read(HERE/'gt/targets.json')['frames'];out=copy.deepcopy(bake);out['assets']='../'+bake['assets'];report=[]
    for shot in spec['shots']:
        sid=shot['id'];aid=main_frames(bake,sid)[0]['mainActor'];p=Shot(bake,assets['actors'][aid],shot,targets);x=np.load(HERE/f'ik-{sid}.npy')
        with torch.no_grad():_,world,_,uv=p.fk(ten(x))
        world=world.numpy();uv=uv.numpy();original=p.baseuv.numpy()
        jitter=lambda q:float(np.linalg.norm(np.diff(q,n=2,axis=0),axis=-1).mean())
        base_jit=jitter(original);start_jit=jitter(uv);candidates=[]
        def score(xx,label):
            with torch.no_grad():qq=p.fk(ten(xx))[3].numpy()
            jj=jitter(qq);err=np.linalg.norm(qq-p.target.numpy(),axis=-1);valid=p.weights.numpy()>0
            return dict(label=label,jitter=jj,median=float(np.median(err[valid])),x=xx)
        candidates.append(score(x,'unchanged'))
        if start_jit>base_jit:
            for window in [5,7,11,15,21,31,51,99]:
                xx=x.copy()
                for side in ['Left','Right']:
                    name=side+'Hand';bi=p.names.index(name);vi=VARIABLE_BONES.index(name);parent=p.parents[bi]
                    current=world[:,bi,:3,:3];current=current/np.linalg.norm(current,axis=1)[:,None,:]
                    ref=current[0];rv=Rotation.from_matrix(current@ref.T).as_rotvec()
                    ww=min(window,p.T if p.T%2 else p.T-1)
                    smooth=savgol_filter(rv,ww,2,axis=0) if window<99 else np.tile(np.median(rv,axis=0),(p.T,1))
                    target=Rotation.from_rotvec(smooth).as_matrix()@ref
                    base=world[:,parent]@p.rel[:,bi].numpy();r=np.linalg.inv(base[:,:3,:3])@target
                    rr=Rotation.from_matrix(r).as_euler('xyz');xx[:,6+vi*3:9+vi*3]=rr
                candidates.append(score(xx,f'zero-phase hand orientation window {window}'))
            good=[c for c in candidates if c['jitter']<=base_jit*.999]
            chosen=min(good,key=lambda c:c['median']) if good else min(candidates,key=lambda c:c['jitter'])
        else:chosen=candidates[0]
        x=chosen['x'];np.save(HERE/f'final-{sid}.npy',x);update_bake(out,p,x)
        report.append(dict(shot=sid,baseline_jitter_all=base_jit,before_jitter_all=start_jit,chosen={k:v for k,v in chosen.items() if k!='x'},candidates=[{k:v for k,v in c.items() if k!='x'} for c in candidates]));print(report[-1],flush=True)
    attach_props(out,bake,spec)
    out['optimization']=dict(method='Exact FK source fit + per-frame constrained IK and hard supports; original core projected trajectories preserved up to .995 amplitude/constant offsets where feasible. Hand orientation regularization only where all-joint jitter otherwise increases; wrists/head unchanged.',source_bake_sha256=sha(HERE.parent/'bake.json'),targets_sha256=sha(HERE/'gt/targets.json'))
    (HERE/'bake-opt.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8');write(HERE/'hand-stability-report.json',report)

if __name__=='__main__':main()
