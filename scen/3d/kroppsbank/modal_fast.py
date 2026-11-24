"""Fast SAM code with already cached ViT-H weights, supplied tracks and camera.

No downloads of weights; no SMPL, YOLO, MoGe, TensorRT, or local inference.
This is explicitly an eager ViT-H variant, not the published DINOv3/TRT setup.
"""
import io
import json
import os
import time
import zipfile
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent
SHA = 'd72aa36913a1673ace029d345f437561a85ec9e2'
app = modal.App('kroppsbank-fast-vith')
vol = modal.Volume.from_name('sam3db-vikter', create_if_missing=False)
image = (
    modal.Image.debian_slim(python_version='3.11')
    .apt_install('git', 'libgl1', 'libglib2.0-0')
    .pip_install('torch==2.5.1', 'torchvision==0.20.1',
                 index_url='https://download.pytorch.org/whl/cu124')
    .pip_install('pytorch-lightning', 'opencv-python-headless', 'yacs', 'scikit-image',
                 'einops', 'timm', 'dill', 'pandas', 'rich', 'hydra-core', 'pyrootutils',
                 'roma', 'joblib', 'loguru', 'optree', 'fvcore', 'huggingface_hub',
                 'jsonlines', 'networkx==3.2.1', 'braceexpand', 'webdataset', 'numpy<2.3')
    .run_commands('git clone https://github.com/yangtiming/Fast-SAM-3D-Body.git /kod',
                  f'cd /kod && git checkout {SHA}')
    .env({'GPU_HAND_PREP': '1', 'LAYER_DTYPE': 'fp32', 'SKIP_KEYPOINT_PROMPT': '1',
          'USE_COMPILE': '0', 'USE_COMPILE_BACKBONE': '0', 'DECODER_COMPILE': '0',
          'MHR_USE_CUDA_GRAPH': '0', 'KEYPOINT_PROMPT_INTERM_INTERVAL': '999',
          'BODY_INTERM_PRED_LAYERS': '0,1,2', 'HAND_INTERM_PRED_LAYERS': '0,1',
          'MHR_NO_CORRECTIVES': '1', 'OMP_NUM_THREADS': '2'})
)


@app.function(image=image, gpu='L4', volumes={'/vikter': vol}, timeout=1350,
              memory=32768, max_containers=1, scaledown_window=2)
def run(shots):
    import contextlib
    import sys
    import traceback
    import subprocess
    started = time.monotonic()
    import cv2
    import numpy as np
    import torch
    sys.path.insert(0, '/kod')
    try:
        from sam_3d_body import load_sam_3d_body, SAM3DBodyEstimator
        ckpt = '/vikter/vith/model.ckpt'
        assert Path(ckpt).is_file(), 'Previously downloaded ViT-H checkpoint missing'
        model, cfg = load_sam_3d_body(ckpt, device=torch.device('cuda'),
                                    mhr_path='/vikter/vith/assets/mhr_model.pt')
        est = SAM3DBodyEstimator(sam_3d_body_model=model, model_cfg=cfg)
        load_s = time.monotonic() - started
        gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total',
                                       '--format=csv,noheader']).decode().strip()
        yield {'kind': 'loaded', 'load_s': load_s, 'gpu': gpu, 'git_sha': SHA}
        for shot in shots:
            t0 = time.monotonic()
            folder = Path('/tmp') / shot['id']
            folder.mkdir(exist_ok=True)
            video = folder / 'input.mp4'
            video.write_bytes(shot['video'])
            cap = cv2.VideoCapture(str(video))
            by_frame = {}
            for frame, pid, box in shot['jobs']:
                by_frame.setdefault(frame, []).append((pid, box))
            archive = io.BytesIO()
            records = []
            torch.cuda.reset_peak_memory_stats()
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
                f = 0
                while True:
                    ok, bgr = cap.read()
                    if not ok:
                        break
                    for pid, box in by_frame.get(f, []):
                        torch.cuda.synchronize()
                        tick = time.monotonic()
                        with contextlib.redirect_stdout(io.StringIO()), torch.inference_mode():
                            result = est.process_one_image(
                                cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB),
                                bboxes=np.asarray([box], dtype=np.float32),
                                cam_int=torch.tensor(shot['K'], dtype=torch.float32)[None])
                        torch.cuda.synchronize()
                        elapsed = time.monotonic() - tick
                        records.append({'frame': f, 'person': str(pid), 'inference_s': elapsed,
                                        'success': bool(result)})
                        if result:
                            b = io.BytesIO()
                            np.savez_compressed(b, **{k: np.asarray(v) for k, v in result[0].items()
                                                      if v is not None and hasattr(v, 'shape')})
                            z.writestr(f'{pid}/{f:04d}.npz', b.getvalue())
                    f += 1
                cap.release()
                stats = {'shot': shot['id'], 'records': records,
                         'wall_s': time.monotonic() - t0, 'model_load_s': load_s,
                         'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
                         'peak_reserved_bytes': torch.cuda.max_memory_reserved(), 'gpu': gpu}
                z.writestr('timing.json', json.dumps(stats, indent=2))
            yield {'kind': 'shot', 'id': shot['id'], 'zip': archive.getvalue(), 'timing': stats}
        yield {'kind': 'finished', 'remote_elapsed_s': time.monotonic() - started}
    except Exception:
        yield {'kind': 'error', 'error': traceback.format_exc(),
               'remote_elapsed_s': time.monotonic() - started}


@app.local_entrypoint()
def main():
    import numpy as np
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    budget_path = ROOT / 'budget.json'
    budget = json.loads(budget_path.read_text(encoding='utf-8'))
    reserve = 1500
    assert budget['charged_upper_bound_seconds'] + sum(r['seconds'] for r in budget['reservations']) + reserve <= budget['gpu_cap_seconds'], 'GPU budget exhausted'
    assert not budget['reservations'], 'Unresolved earlier GPU reservation; reconcile before running'
    budget['reservations'] = [{'candidate': 'fast-vith', 'seconds': reserve}]
    budget_path.write_text(json.dumps(budget, indent=2), encoding='utf-8')
    shots = []
    for entry in manifest['shots']:
        folder = Path(entry['folder'])
        jobs = json.loads((folder / 'jobb.json').read_text(encoding='utf-8'))
        allowed = set(entry['pids'])
        jobs = [j for j in jobs if str(j[1]) in allowed]
        shots.append({'id': entry['id'], 'video': Path(entry['video']).read_bytes(),
                      'jobs': jobs, 'K': entry['K']})
    tick = time.monotonic()
    events = []
    try:
        for item in run.remote_gen(shots):
            if item['kind'] == 'shot':
                out = ROOT / 'ut' / 'fast-vith' / item['id']
                out.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(io.BytesIO(item.pop('zip'))) as z:
                    for name in z.namelist():
                        target = (out / name).resolve()
                        assert target.is_relative_to(out.resolve())
                    z.extractall(out)
                print('Saved', item['id'], item['timing']['wall_s'], flush=True)
            else:
                print(json.dumps(item), flush=True)
            events.append(item)
            (ROOT / 'fast_events.json').write_text(json.dumps(events, indent=2), encoding='utf-8')
    finally:
        elapsed = time.monotonic() - tick
        # Includes container provisioning and all RPC overhead; conservative GPU upper bound.
        charged = min(reserve, elapsed + 10)
        budget['reservations'] = []
        budget['charged_upper_bound_seconds'] += charged
        budget['events'].append({'candidate': 'fast-vith', 'remote_call_wall_s': elapsed,
                                 'shutdown_allowance_s': 10, 'gpu_seconds_upper_bound': charged,
                                 'cpu_image_build_gpu_seconds': 0, 'status': events[-1]['kind'] if events else 'RPC failed'})
        budget_path.write_text(json.dumps(budget, indent=2), encoding='utf-8')
