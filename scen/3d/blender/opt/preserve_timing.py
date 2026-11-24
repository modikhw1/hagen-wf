"""Constrained IK projection onto timing-preserving image trajectories.

Each core joint's screen trajectory = .995 * original + one constant per-shot
offset. Thus accelerations decrease .5% and velocity extrema retain exact frames.
FK solves these targets without camera changes, bone scaling or time resampling.
"""
from fit_cpu import *

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--iterations',type=int,default=350);ap.add_argument('--strength',type=float,default=1);ap.add_argument('--shots',nargs='*');args=ap.parse_args()
    bake=read(HERE.parent/'bake.json');assets=read(HERE.parent/bake['assets']);spec=read(ROOT/'scen3d.json');targets=read(HERE/'gt/targets.json')['frames']
    out=copy.deepcopy(bake);out['assets']='../'+bake['assets'];report=[];start=time.perf_counter()
    for shot in spec['shots']:
        sid=shot['id'];aid=main_frames(bake,sid)[0]['mainActor'];prob=Shot(bake,assets['actors'][aid],shot,targets)
        cache=HERE/f'timing-{sid}.npy'
        if args.shots and sid not in args.shots and cache.exists():xnp=np.load(cache)
        else:
            prior=np.load(HERE/f'parameters-{sid}.npy')
            base=prob.baseuv.numpy();truth=prob.target.numpy();weight=prob.weights.numpy()
            offsets=np.stack([np.median((truth-base)[weight[:,j]>0,j],axis=0) if (weight[:,j]>0).any() else np.zeros(2) for j in range(7)])
            desired=ten(base[:,:7]*.995+base[:,:7].mean(0)*.005+offsets[None]*args.strength)
            x=ten(prior).clone().requires_grad_(True)
            opt=torch.optim.LBFGS([x],lr=.8,max_iter=args.iterations,history_size=30,line_search_fn='strong_wolfe',tolerance_grad=1e-9,tolerance_change=1e-12)
            counter=[0]
            def closure():
                opt.zero_grad();root,w,joints,uv=prob.fk(x)
                residual=(uv[:,:7]-desired)
                support=(root[:,1,3]-prob.oldroot[:,1,3]).square().mean()
                # Feet and pelvis retain original support height. Null-space prior
                # chooses the source-fitted pose when multiple IK solutions exist.
                loss=residual.square().mean()+support*.1+(x-ten(prior)).square().mean()*.0001
                loss.backward();counter[0]+=1
                if counter[0]%75==0 or counter[0]==1:print(sid,'timing IK',counter[0],float(residual.detach().abs().max()),flush=True)
                return loss
            opt.step(closure);xnp=x.detach().numpy();np.save(cache,xnp)
        update_bake(out,prob,xnp)
        before=prob.baseuv.numpy();after=np.stack([project(features(out['frames'][f['i']]['actors'][aid],assets['actors'][aid]),shot['source']['camera']) for f in prob.fs])
        weight=np.array([targets[f['i']]['confidence'] for f in prob.fs])>0
        e0=np.linalg.norm(before-prob.target.numpy(),axis=-1);e1=np.linalg.norm(after-prob.target.numpy(),axis=-1)
        row=dict(shot=sid,body_median_before=float(np.median(e0[:,:7][weight[:,:7]])),body_median_after=float(np.median(e1[:,:7][weight[:,:7]])),median_before=float(np.median(e0[weight])),median_after=float(np.median(e1[weight])),jitter_before=motion_metrics(before),jitter_after=motion_metrics(after),peak_shift=peak_shift(before,after)[0]);report.append(row);print(row,flush=True)
    props=attach_props(out,bake,spec)
    out['optimization']=dict(method='Exact skeletal FK + constrained IK; .995 original screen-space core trajectory plus constant per-joint shot offsets. Original velocity-extrema frames retained, no camera/shape/face/time edits.',source_bake_sha256=sha(HERE.parent/'bake.json'),targets_sha256=sha(HERE/'gt/targets.json'),seconds=time.perf_counter()-start,strength=args.strength)
    (HERE/'bake-opt.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
    write(HERE/'timing-fit-report.json',dict(shots=report,prop_offsets=props,seconds=time.perf_counter()-start))

if __name__=='__main__':main()
