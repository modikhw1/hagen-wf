"""GEM-X Body Motion on Modal. No local torch imports/inference.

From project root, PYTHONIOENCODING=utf-8:
  scen/.venv/Scripts/python.exe -m modal run scen/3d/ingest/modal_gemx.py --mode prepare
  scen/.venv/Scripts/python.exe -m modal run scen/3d/ingest/modal_gemx.py --mode evaluate
Downloads only public body assets; never requests gated hand weights.
"""
import io
import json
import time
import zipfile
from pathlib import Path
import modal

ROOT = Path(__file__).resolve().parents[3] if modal.is_local() else Path('/tmp/hagen')
BANK = ROOT / 'scen/3d/kroppsbank'
SHA = '4aef1452e5df171deff4f293c08e643eb450981e'
WEIGHTS_SHA = 'b111f2dcf3ebcf57965fd53499cb645dfa5ba25c'
SOMA_SHA = 'd281db2d01553f7230c56e764cec00fe27ef23f7'

def gpu_reservation(budget):
    """A retry may consume only the unspent startup allowance; never reset it."""
    startup=[e for e in budget.get('events',[]) if e.get('candidate')=='gemx-startup']
    first_success=any(e.get('success') for e in startup)
    total_left=max(0,5400-budget.get('charged_upper_bound_seconds',0))
    startup_left=max(0,1800-sum(e.get('charged_upper_bound_seconds',0) for e in startup))
    return min(1800,total_left if first_success else min(total_left,startup_left)), ('gemx-evaluation' if first_success else 'gemx-startup')

GPU_RESERVATION_S, BUDGET_CANDIDATE = gpu_reservation(
    json.loads((BANK/'budget.json').read_text(encoding='utf-8'))
    if modal.is_local() and (BANK/'budget.json').exists() else {})
GPU_TIMEOUT_S = max(1,min(1350,int(GPU_RESERVATION_S-150)))
app = modal.App('hagen-gemx-body')
vol = modal.Volume.from_name('gemx-body-v033', create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version='3.12')
    .apt_install('git', 'ffmpeg', 'libgl1', 'libglib2.0-0', 'build-essential')
    .pip_install('torch==2.10.0', index_url='https://download.pytorch.org/whl/cu128')
    .run_commands('git clone https://github.com/NVlabs/GEM-X.git /opt/gemx',
                  f'cd /opt/gemx && git checkout {SHA}',
                  "python -m pip install '/opt/gemx[video]' huggingface_hub")
    .env({'TORCH_ALLOW_TF32_CUBLAS_OVERRIDE': '0', 'OMP_NUM_THREADS': '4',
          'HF_HUB_DISABLE_IMPLICIT_TOKEN': '1'})
)


@app.function(image=image, volumes={'/data': vol}, timeout=3600, memory=16384)
def prepare():
    import hashlib
    import importlib.metadata
    import shutil
    import urllib.request
    from huggingface_hub import hf_hub_download
    started = time.monotonic()
    folders = {'nvidia/GEM-X': ('weights', WEIGHTS_SHA, [
        'body_s240000.ckpt', 'body_config.json', 'vitpose.pth',
        'body_video_native77.yaml', 'motion_native77_e774_s292175.ckpt',
        'motion_stats_raw.npz', 'motion_native77.yaml']),
        'nvidia/SOMA-X': ('soma', SOMA_SHA, ['SOMA_neutral.npz',
        'SOMA_template_rig.usda', 'SOMA_procedural_transforms.json', 'correctives_model.pt'])}
    inventory = []
    for repo, (folder, revision, names) in folders.items():
        for name in names:
            path = Path(hf_hub_download(repo, name, revision=revision,
                                      local_dir=f'/data/{folder}', token=False))
            inventory.append({'repo': repo, 'revision': revision, 'file': name,
                              'bytes': path.stat().st_size})
            print('cached', repo, name, path.stat().st_size, flush=True)
            vol.commit()
    detector = Path('/data/weights/yolox_humanart.onnx')
    url = 'https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/onnx_sdk/yolox_x_8xb8-300e_humanart-a39d44ed.zip'
    if not detector.exists():
        archive = Path('/data/weights/yolox_humanart.zip')
        urllib.request.urlretrieve(url, archive)
        with zipfile.ZipFile(archive) as z:
            name = next(n for n in z.namelist() if n.endswith('/end2end.onnx'))
            with z.open(name) as source, detector.open('wb') as dest:
                shutil.copyfileobj(source, dest)
    inventory.append({'file': detector.name, 'source': url, 'bytes': detector.stat().st_size,
                      'sha256': hashlib.sha256(detector.read_bytes()).hexdigest()})
    # Import-only preflight on CPU; catches missing runtime dependencies before a GPU is reserved.
    from gem.inference.body_video import run_body_video
    from gem.inference.postprocess import postprocess_motion_result
    from gem.motion.geometry import MotionGeometry
    versions = {n: importlib.metadata.version(n) for n in ['torch', 'gem', 'py-soma-x', 'transformers', 'onnxruntime']}
    result = {'files': inventory, 'versions': versions, 'git_sha': SHA,
              'cpu_prepare_s': time.monotonic() - started}
    Path('/data/prepared.json').write_text(json.dumps(result, indent=2))
    vol.commit()
    return result


@app.function(image=image, volumes={'/data':vol}, timeout=120, memory=2048)
def audit_assets():
    """CPU-only licence/archive inventory; never a gated request."""
    from huggingface_hub import hf_hub_download
    result={}
    with zipfile.ZipFile('/data/weights/yolox_humanart.zip') as z:
        result['detector_archive_members']=z.namelist()
        result['detector_licence_files']={n:z.read(n).decode('utf-8',errors='replace')[:20000]
            for n in z.namelist() if any(s in n.lower() for s in ['license','licence','notice'])}
    for repo,revision,folder in [('nvidia/GEM-X',WEIGHTS_SHA,'weights'),('nvidia/SOMA-X',SOMA_SHA,'soma')]:
        file=hf_hub_download(repo,'LICENSE',revision=revision,local_dir=f'/data/{folder}',token=False)
        result[repo+'_LICENSE']=Path(file).read_text()
    vol.commit()
    return result


@app.function(image=image, volumes={'/data':vol}, timeout=240, memory=4096)
def inspect_saved():
    """CPU serialization/source inspection only; no model execution."""
    import torch
    import numpy as np
    result = {}
    for p in Path('/data/runs/20261110T154539Z').glob('*/*/raw.pt'):
        r = torch.load(p, map_location='cpu', weights_only=False)
        key = p.parent.parent.name + '/' + p.parent.name
        buf = io.BytesIO()
        np.savez_compressed(buf, kp2d=r['conditions']['kp2d_native77'][0].numpy(),
            frame_times=r['conditions']['frame_times'][0].numpy(),
            R_w2c=r['camera']['R_w2c'].numpy(), boxes=r['tracking']['boxes_xyxy'],
            **{'param_'+k:v.numpy() for k,v in r['pred_soma_params_incam'].items()})
        result[key]={'arrays':buf.getvalue(),'video':r['video'],'release':r['release'],
                     'coordinates':r['coordinates'],'camera_diagnostics':r['camera']['diagnostics']}
    sources={}
    for rel in ['gem/motion/api.py','gem/motion/pipeline.py','gem/motion/frontend/time.py']:
        sources[rel]=Path('/opt/gemx',rel).read_text()
    return result,sources


@app.function(image=image, volumes={'/data':vol}, timeout=240, memory=4096)
def pull_slim(run_id):
    """Read already committed arrays, without meshes or any inference."""
    buf=io.BytesIO()
    base=Path('/data/runs')/run_id
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for shot in base.iterdir():
            if not shot.is_dir() or not (shot/'timing.json').exists():continue
            for p in shot.rglob('*'):
                if p.is_file() and (p.name in ['raw_joints.npz','contact_ik_joints.npz','conditions.npz','metadata.json','faces.npy','timing.json','joint_names.json']):
                    z.write(p,p.relative_to(base))
    return buf.getvalue()


@app.function(image=image, volumes={'/data':vol}, timeout=1800, memory=8192, cpu=4)
def project_saved(run_id,jobs):
    """CPU-only filtering/rasterization of saved geometry, no model calls."""
    import cv2
    import numpy as np
    from scipy.ndimage import gaussian_filter1d
    cv2.setNumThreads(1)
    result={};indices=[0,67,72,68,73,69,74,4,6,12,40,13,41,14,42]
    edges=[(0,1),(0,2),(1,3),(2,4),(3,5),(4,6),(0,7),(7,8),
           (7,9),(7,10),(9,11),(10,12),(11,13),(12,14)]
    for job in jobs:
        p=Path('/data/runs')/run_id/job['config']/job['person']
        start,n=job['start'],job['n'];sl=slice(start,start+n)
        z=np.load(p/'raw_joints.npz');x=z['camera_m'][sl][:,indices].astype(float)
        K=z['intrinsics'][sl];valid=np.asarray(job['valid'],bool)
        v=np.array([np.load(p/'raw'/f'{f:04d}.npz')['vertices_camera_m'] for f in range(start,start+n)])
        faces=np.load(p/'faces.npy');mw,mh=job['mask_size'];w,h=job['image_size']
        good=np.flatnonzero(valid)
        for f in np.flatnonzero(~valid):
            v[f]=v[good[np.abs(good-f).argmin()]]
        for j in range(15):
            for k in range(3):x[:,j,k]=np.interp(np.arange(n),good,x[good,j,k])
        root=x[:,:1].copy();rel=x-root
        for sigma in job['sigmas']:
            cache=Path('/data/projected')/run_id/job['key']/f'{sigma}.npz'
            cache.parent.mkdir(exist_ok=True,parents=True)
            if not cache.exists():
                if sigma:
                    rf=gaussian_filter1d(root,sigma,axis=0,mode='reflect',truncate=3.)
                    xf=rf+gaussian_filter1d(rel,sigma,axis=0,mode='reflect',truncate=3.)
                    vf=rf+gaussian_filter1d(v-root,sigma,axis=0,mode='reflect',truncate=3.)
                else:xf=x.copy();vf=v
                sil=[]
                for f in range(n):
                    mask=np.zeros((mh,mw),np.uint8)
                    if valid[f] and (vf[f,:,2]<.05).mean()<=.02:
                        uv=vf[f]@K[f].T;uv=uv[:,:2]/uv[:,2:3]*[mw/w,mh/h]
                        pts=np.round(uv[faces]*8).astype(np.int32)
                        pts=pts[(np.abs(pts)<8*20000).all(axis=(1,2))]
                        cv2.fillPoly(mask,list(pts),1,lineType=cv2.LINE_8,shift=3)
                    sil.append(mask.astype(bool))
                before=np.array([np.linalg.norm(x[:,a]-x[:,b],axis=-1) for a,b in edges])
                after=np.array([np.linalg.norm(xf[:,a]-xf[:,b],axis=-1) for a,b in edges])
                bone=float(np.percentile(np.abs(after-before)/np.maximum(before,.01)*100,95))
                xf[~valid]=np.nan
                np.savez_compressed(cache,x=xf,K=K,valid=valid,sil=np.array(sil),bone_length_delta_p95_pct=bone)
                vol.commit()
            result[job['key']+f'/{sigma}.npz']=cache.read_bytes()
        print('PROJECTED',job['key'],job['sigmas'],flush=True)
    return result


@app.function(image=image, gpu='L40S', volumes={'/data': vol}, timeout=GPU_TIMEOUT_S,
              memory=32768, cpu=4, max_containers=1, scaledown_window=2)
def predict(shots, run_id, timeout_s=1650):
    """Sequential shots and people; retain native predictions and both FK variants."""
    started = time.monotonic()
    import traceback
    import subprocess
    import dataclasses
    import gc
    import threading
    import numpy as np
    import torch
    memory_samples = []
    monitor_stop = threading.Event()
    def monitor_memory():
        while not monitor_stop.is_set():
            try:
                value = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used',
                    '--format=csv,noheader,nounits'], timeout=5).decode().strip()
                memory_samples.append(int(value))
            except Exception:
                pass
            monitor_stop.wait(1)
    threading.Thread(target=monitor_memory, daemon=True).start()
    try:
        import gem.inference.body_video as bv
        from gem.common.detectors.tracks import TrackResult, square_crops, smooth_boxes
        from gem.inference.postprocess import postprocess_motion_result
        from gem.inference.serialization import save_predictions
        from gem.motion.geometry import MotionGeometry
        assert Path('/data/prepared.json').exists(), 'Run CPU prepare first'
        torch.set_num_threads(4)
        import_s = time.monotonic() - started
        gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader']).decode().strip()
        yield {'kind': 'loaded', 'import_s': import_s, 'gpu': gpu}
        for shot in shots:
            shot_start = time.monotonic()
            folder = Path('/data/runs') / run_id / shot['id']
            folder.mkdir(parents=True, exist_ok=True)
            video = folder / 'input.mp4'
            video.write_bytes(shot['video'])
            records = []
            for pid in shot['pids']:
                if time.monotonic() - started > max(0,timeout_s-200):
                    raise TimeoutError('Stop before the 30 GPU-minute startup allowance is exhausted')
                person_start = time.monotonic()
                torch.cuda.reset_peak_memory_stats()
                out = folder / pid
                out.mkdir(exist_ok=True)
                config = bv.load_body_video_config('/data/weights/body_video_native77.yaml')
                if shot.get('default_intrinsics'):
                    config['camera'].pop('intrinsics',None)
                else:
                    config['camera']['intrinsics'] = shot['K']
                config['camera']['mode'] = shot.get('camera_mode','background')
                config['pose']['batch_size'] = 4
                config['observations']['batch_size'] = 4
                tracks_source = shot.get('tracks',{})
                # Upstream CLI supports no supplied motion boxes. Only replace tracking,
                # keeping upstream smoothing/crop convention, models and camera estimation.
                def supplied_tracks(frames, detector, **options):
                    n = len(frames)
                    assert n == shot['meta']['N'], (n, shot['meta']['N'])
                    observed_ids = sorted(int(f) for f in tracks_source[pid])
                    assert observed_ids
                    values = np.asarray([tracks_source[pid][str(f)] for f in observed_ids], np.float32)
                    boxes = np.column_stack([np.interp(np.arange(n), observed_ids, values[:, j]) for j in range(4)]).astype(np.float32)
                    seen = np.isin(np.arange(n), observed_ids)
                    all_boxes = [np.asarray([v[str(f)] for v in tracks_source.values() if str(f) in v], np.float32).reshape(-1, 4) for f in range(n)]
                    others = [np.asarray([v[str(f)] for p,v in tracks_source.items() if p != pid and str(f) in v], np.float32).reshape(-1,4) for f in range(n)]
                    return TrackResult(np.arange(n), boxes,
                        square_crops(smooth_boxes(boxes), options.get('bbox_enlarge',1.2)),
                        np.full(n, int(pid), np.int32), seen, (observed_ids[0], observed_ids[-1]),
                        all_boxes, others, all_boxes, [np.ones(len(b),np.float32) for b in all_boxes],
                        ['supplied_observed' if s else 'supplied_interpolated_assumed' for s in seen])
                original = bv.detect_track
                bv.detect_track = original if shot.get('stock') else supplied_tracks
                try:
                    if shot.get('stock'):
                        config_path=folder/'release.json'
                        config_path.write_text(json.dumps(config))
                        command=['gem-infer','motion-video','--task','body','--input',str(video),
                            '--config',str(config_path),'--device','cuda','--output',str(out/'raw.pt')]
                        subprocess.run(command,check=True,timeout=max(30,int(timeout_s-(time.monotonic()-started)-120)))
                        raw=torch.load(out/'raw.pt',map_location='cpu',weights_only=False)
                    else:
                        raw = bv.run_body_video(str(video), config, device='cuda',
                            progress=lambda s: print(shot['id'],pid,s,flush=True))
                finally:
                    bv.detect_track = original
                forward_s = time.monotonic() - person_start
                save_predictions(raw, out / 'raw.pt')
                (out/'metadata.json').write_text(json.dumps({'video':raw['video'],
                    'release':raw['release'],'coordinates':raw['coordinates'],
                    'camera_diagnostics':raw['camera']['diagnostics']}))
                np.savez_compressed(out/'conditions.npz',
                    kp2d=raw['conditions']['kp2d_native77'][0].numpy(),
                    frame_times=raw['conditions']['frame_times'][0].numpy(),
                    R_w2c=raw['camera']['R_w2c'].numpy(),boxes=raw['tracking']['boxes_xyxy'],
                    **{'param_'+k:v.numpy() for k,v in raw['pred_soma_params_incam'].items()})
                # Commit raw result before optional IK/geometry, so a failure is recoverable.
                vol.commit()
                ik_start = time.monotonic()
                processed = postprocess_motion_result(raw, soma_assets='/data/soma', device='cuda')
                save_predictions(processed, out / 'contact_ik.pt')
                ik_s = time.monotonic() - ik_start
                geometry = MotionGeometry('/data/soma', device='cuda', chunk_size=8)
                faces = geometry.faces.numpy()
                np.save(out / 'faces.npy', faces)
                for variant, result in [('raw',raw), ('contact_ik',processed)]:
                    camera_joints, world_joints = [], []
                    for coordinate, collected in [('incam',camera_joints), ('global',world_joints)]:
                        for start, chunk in geometry.iter_chunks(result[f'pred_soma_params_{coordinate}']):
                            collected.append(chunk['joints'][0].numpy())
                            if coordinate == 'incam':
                                dest = out / variant
                                dest.mkdir(exist_ok=True)
                                for offset, vertices in enumerate(chunk['vertices'][0].numpy()):
                                    np.savez_compressed(dest / f'{start+offset:04d}.npz', vertices_camera_m=vertices)
                    np.savez_compressed(out / f'{variant}_joints.npz',
                        camera_m=np.concatenate(camera_joints), world_m=np.concatenate(world_joints),
                        intrinsics=raw['conditions']['K_fullimg'][0].numpy(),
                        contact_logits=raw['static_conf_logits'].numpy(),
                        observed=raw['tracking']['observed_primary'])
                # Native joint names from SOMA rig (no guessed numeric map).
                from pxr import Usd, UsdSkel
                stage = Usd.Stage.Open('/data/soma/SOMA_template_rig.usda')
                skeletons = [UsdSkel.Skeleton(p) for p in stage.Traverse() if p.IsA(UsdSkel.Skeleton)]
                import re
                joint_paths = [str(n) for n in skeletons[0].GetJointsAttr().Get()
                               if str(n) != 'Root' and not re.search(r'Twist[1-4]$',str(n))]
                assert len(joint_paths) == 77, len(joint_paths)
                (out / 'joint_names.json').write_text(json.dumps(joint_paths))
                record = {'person':pid, 'frames':int(raw['length'][0]), 'forward_s':forward_s,
                    'contact_ik_s':ik_s, 'total_s':time.monotonic()-person_start,
                    'vram_peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                    'vram_peak_reserved_bytes':torch.cuda.max_memory_reserved(),
                    'nvidia_smi_peak_used_mib_so_far':max(memory_samples,default=None),
                    'git_sha':SHA, 'tracking':'stock gem-infer motion-video' if shot.get('stock') else 'personer.json; upstream smooth_boxes and square_crops; linear gap fill assumed',
                    'intrinsics_origin':'upstream diagonal default' if shot.get('default_intrinsics') else 'manifest; inherited estimate, not measured calibration'}
                (out / 'timing.json').write_text(json.dumps(record,indent=2))
                records.append(record)
                del geometry, raw, processed
                gc.collect()
                torch.cuda.empty_cache()
                vol.commit()
                print('PERSON_DONE', shot['id'], json.dumps(record),flush=True)
            timing = {'people':records,'shot_s':time.monotonic()-shot_start,'gpu':gpu,'import_s':import_s}
            (folder / 'timing.json').write_text(json.dumps(timing,indent=2))
            archive = folder.with_suffix('.zip')
            with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
                for p in folder.rglob('*'):
                    if p.is_file() and p.name != 'input.mp4': z.write(p,p.relative_to(folder))
            vol.commit()
            yield {'kind':'shot','id':shot['id'],'timing':timing,'archive':archive.read_bytes()}
        yield {'kind':'done','gpu_function_s':time.monotonic()-started}
    except Exception:
        yield {'kind':'error','gpu_function_s':time.monotonic()-started,'traceback':traceback.format_exc()}
    finally:
        monitor_stop.set()


def backup(relative):
    import shutil
    source = ROOT / relative
    target = BANK / 'fore_gemx' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists() and not target.exists(): shutil.copy2(source,target)


def run_followup():
    from datetime import datetime, timezone
    import copy
    manifest=json.loads((BANK/'manifest.json').read_text(encoding='utf-8'))
    out=BANK/'ut/gemx_followup'
    out.mkdir(parents=True,exist_ok=True)
    plan=[]
    for s in manifest['shots']:
        for variant in ['stock_inherited','stock_default']:
            r=copy.deepcopy(s)
            r.update(id=s['id']+'__'+variant,pids=['1'],stock=True,
                     default_intrinsics=variant=='stock_default',base_shot=s['id'])
            plan.append(r)
        if s['id'].startswith('notan'):
            r=copy.deepcopy(s)
            r.update(id=s['id']+'__adapter_static',camera_mode='static',base_shot=s['id'])
            r['tracks']=json.loads((ROOT/s['folder']/'personer.json').read_text(encoding='utf-8'))
            plan.append(r)
    for camera in ['background','static']:
        plan.append(dict(id='notan-whole__stock_'+camera,video='scen/klipp/d-dialog-notan.mp4',
                         pids=['1'],stock=True,camera_mode=camera,K=manifest['shots'][0]['K']))
    (out/'plan.json').write_text(json.dumps([{k:v for k,v in s.items() if k not in ('source_sha256','tracks')} for s in plan],indent=2),encoding='utf-8')
    shots=[]
    for s in plan:
        if (out/s['id']/'timing.json').exists(): continue
        r={k:v for k,v in s.items() if k!='source_sha256'}
        r['video']=(ROOT/s['video']).read_bytes()
        shots.append(r)
    if not shots: return
    bp=BANK/'budget.json'
    b=json.loads(bp.read_text(encoding='utf-8'))
    if b.get('reservations'): raise RuntimeError('Unsettled GPU reservation')
    used=b['charged_upper_bound_seconds']
    task_used=sum(e['charged_upper_bound_seconds'] for e in b['events'] if e.get('candidate')=='gemx-followup')
    reservation=min(1500-task_used,5400-used)
    if reservation<200: raise RuntimeError('Follow-up GPU budget exhausted')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    b['gemx_followup_cap_seconds']=1500
    b['reservations']=[dict(candidate='gemx-followup',seconds=reservation,run_id=run_id)]
    b['charged_upper_bound_seconds']=used+reservation
    bp.write_text(json.dumps(b,indent=2),encoding='utf-8')
    with (BANK/'GEMX-LOGG.md').open('a',encoding='utf-8') as f:
        f.write(f'\n## Uppföljning: GPU-start {run_id}\nStock CLI på fyra klipp med ärvd/default K, adapter+static på notan, hela notan stock med background/static. Sekventiellt; reservation {reservation:.1f} s; högst 1500 s extra totalt.\n')
    start=time.monotonic();events=[]
    for r in predict.remote_gen(shots,run_id,min(GPU_TIMEOUT_S,reservation-150)):
        if r['kind']=='shot':
            target=out/r['id'];target.mkdir(exist_ok=True)
            data=r.pop('archive')
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist():
                    if not (target/name).resolve().is_relative_to(target.resolve()): raise ValueError(name)
                z.extractall(target)
        events.append(r)
        (out/f'run_{run_id}.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
        print(json.dumps(r),flush=True)
    elapsed=time.monotonic()-start
    charge=min(reservation,elapsed+15)
    b['events'].append(dict(candidate='gemx-followup',run_id=run_id,remote_call_wall_s=elapsed,
        gpu_function_s=max((r.get('gpu_function_s',0) for r in events),default=0),
        charged_upper_bound_seconds=charge,success=events[-1]['kind']=='done'))
    b['reservations']=[];b['charged_upper_bound_seconds']=used+charge
    bp.write_text(json.dumps(b,indent=2),encoding='utf-8')
    with (BANK/'GEMX-LOGG.md').open('a',encoding='utf-8') as f:
        f.write(f'\nGPU-anrop avslutat: {charge/60:.3f} min konservativt; {events[-1]["kind"]}. Se ut/gemx_followup/run_{run_id}.json.\n')
    if events[-1]['kind']!='done': raise RuntimeError(events[-1])


@app.local_entrypoint()
def main(mode: str = 'prepare'):
    from datetime import datetime, timezone
    start = time.monotonic()
    out = BANK / 'ut/gemx'
    out.mkdir(parents=True,exist_ok=True)
    if mode == 'slim':
        b=json.loads((BANK/'budget.json').read_text(encoding='utf-8'))
        run_id=next((r['run_id'] for r in b.get('reservations',[]) if r['candidate']=='gemx-followup'),None)
        if run_id is None:run_id=next(e['run_id'] for e in reversed(b['events']) if e['candidate']=='gemx-followup')
        data=pull_slim.remote(run_id)
        target=BANK/'ut/gemx_slim';target.mkdir(exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(data)) as z:z.extractall(target)
        print('Committed slim arrays saved',run_id,len(data))
        return
    if mode in ['project','project-best']:
        import numpy as np
        import sys
        sys.path.insert(0,str(BANK))
        import followup_gemx as F
        b=json.loads((BANK/'budget.json').read_text(encoding='utf-8'))
        run_id=next((r['run_id'] for r in b.get('reservations',[]) if r['candidate']=='gemx-followup'),None)
        if run_id is None:run_id=next(e['run_id'] for e in reversed(b['events']) if e['candidate']=='gemx-followup')
        jobs=[]
        best=F.E.read_json(F.OUT/'best.json') if mode=='project-best' else {}
        for s in F.SHOTS:
            masks=np.load(ROOT/s['folder']/'masker.npy',mmap_mode='r')
            configs=[p.name for p in (BANK/'ut/gemx_slim').glob(s['id']+'__*')]
            if s['id'].startswith('notan'):configs += [p.name for p in (BANK/'ut/gemx_slim').glob('notan-whole__*')]
            if best:configs=list(set(best[s['id']].values())-{'gemx-raw','gemx-contact_ik'})
            for config in configs:
                for pid in (s['pids'] if 'adapter' in config else ['1']):
                    if best and best[s['id']][pid]!=config:continue
                    valid=np.load(BANK/'ut/gemx'/s['id']/pid/'raw_joints.npz')['observed'].tolist()
                    key=s['id']+'/'+config+'/'+pid
                    sigmas=[0,.5,1,2,3] if best else [0]
                    if all((BANK/'ut/gemx_projected'/key/f'{sig}.npz').exists() for sig in sigmas):continue
                    jobs.append(dict(key=key,config=config,person=pid,start=F.offsets()[s['id']]['offset'] if config.startswith('notan-whole') else 0,
                        n=s['meta']['N'],valid=valid,mask_size=[masks.shape[2],masks.shape[1]],
                        image_size=[s['meta']['bredd'],s['meta']['hojd']],sigmas=sigmas))
        if jobs:
            result=project_saved.remote(run_id,jobs)
            for name,data in result.items():
                p=BANK/'ut/gemx_projected'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            print('CPU projected jobs saved',len(jobs))
        return
    if mode == 'inspect':
        results,sources=inspect_saved.remote()
        for key,r in results.items():
            target=out/key
            (target/'conditions.npz').write_bytes(r.pop('arrays'))
            (target/'metadata.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
        for name,source in sources.items():
            (BANK/'kallor'/('gemx_followup_'+name.replace('/','_'))).write_text(source,encoding='utf-8')
        print('CPU inspection saved',list(results))
        return
    if mode == 'followup':
        run_followup()
        return
    if mode == 'audit':
        result=audit_assets.remote()
        (out/'asset_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('CPU asset audit saved; detector licence files:',list(result['detector_licence_files']))
        return
    if mode == 'prepare':
        result = prepare.remote()
        result['build_and_prepare_wall_s'] = time.monotonic()-start
        (out/'prepare.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
        return
    if mode != 'evaluate': raise ValueError('mode must be prepare or evaluate')
    # Local work is input serialization, budgets and output writes only.
    manifest = json.loads((BANK/'manifest.json').read_text(encoding='utf-8'))
    shots=[]
    for s in manifest['shots']:
        if (out/s['id']/'timing.json').exists(): continue
        s = {k:v for k,v in s.items() if k != 'source_sha256'}
        s['tracks'] = json.loads((ROOT/s['folder']/'personer.json').read_text(encoding='utf-8'))
        s['video'] = (ROOT/s['video']).read_bytes()
        shots.append(s)
    if not shots: return
    budget_path = BANK/'budget.json'
    budget = json.loads(budget_path.read_text(encoding='utf-8'))
    backup(Path('scen/3d/kroppsbank/budget.json'))
    used = budget['charged_upper_bound_seconds']
    active = [r for r in budget.get('reservations',[]) if r.get('candidate','').startswith('gemx')]
    if active: raise RuntimeError('Unsettled GEM-X reservation: check Modal app before resuming')
    reservation,candidate=gpu_reservation(budget)
    if reservation != GPU_RESERVATION_S: raise RuntimeError('Budget changed during app startup; restart before reserving a GPU')
    if reservation <= 150: raise RuntimeError('Insufficient remaining startup/total GPU allowance')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    budget['reservations']=[{'candidate':candidate,'seconds':reservation,'run_id':run_id}]
    budget['gemx_startup_cap_seconds']=1800
    budget['single_candidate_cap_seconds']=1800
    budget['charged_upper_bound_seconds']=used+reservation
    budget_path.write_text(json.dumps(budget,indent=2),encoding='utf-8')
    # Never settle on a local disconnect: reservation remains for manual reconciliation.
    gpu_start=time.monotonic()
    events=[]
    for result in predict.remote_gen(shots,run_id,GPU_TIMEOUT_S):
        if not events:
            result['cold_call_to_first_event_s']=time.monotonic()-gpu_start
        if result['kind']=='shot':
            target=out/result['id']; target.mkdir(parents=True,exist_ok=True)
            data=result.pop('archive')
            (target/'predictions.zip').write_bytes(data)
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist():
                    resolved=(target/name).resolve()
                    if not resolved.is_relative_to(target.resolve()): raise ValueError(name)
                z.extractall(target)
        events.append(result)
        (out/f'run_{run_id}.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
        print(json.dumps(result),flush=True)
    elapsed=time.monotonic()-gpu_start
    remote_s=max((e.get('gpu_function_s',0) for e in events),default=0)
    charge=min(reservation,elapsed+15)
    budget['events'].append({'candidate':candidate,'run_id':run_id,
        'remote_call_wall_s':elapsed,'gpu_function_s':remote_s,
        'charged_upper_bound_seconds':charge,'success':events[-1]['kind']=='done'})
    budget['reservations']=[]
    budget['charged_upper_bound_seconds']=used+charge
    budget_path.write_text(json.dumps(budget,indent=2),encoding='utf-8')
    if events[-1]['kind']!='done': raise RuntimeError('Stage 1 failed; see run JSON. Stop before pipeline integration.')
