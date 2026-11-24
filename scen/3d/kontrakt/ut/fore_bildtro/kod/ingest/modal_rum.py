"""MoGe-2 metric depth on Modal; resumable per-frame cache, no person geometry.

Licences and pinned revisions: RUM-LICENSES.md. Camera FOV is supplied, never re-estimated.
The model sees the RGB context; its output is masked BEFORE any geometry is returned.
"""
import io
import json
import time
from pathlib import Path

import modal

REV = '74fbce054ebed49800de42d0ad0e83495065719a'
WEIGHTS_REV = 'cb0e8bbd6b1e243589717c78e750b1ba4c093acf'
MODEL = 'Ruicheng/moge-2-vitl-normal'
app = modal.App('ingest-rum-moge2')
vol = modal.Volume.from_name('rum-moge2-vikter', create_if_missing=True)
bild = (modal.Image.debian_slim(python_version='3.11')
        .apt_install('git', 'libgl1', 'libglib2.0-0')
        .pip_install('torch==2.5.1', 'torchvision==0.20.1', index_url='https://download.pytorch.org/whl/cu124')
        .pip_install('numpy<2.3', 'scipy', 'opencv-python-headless', 'huggingface_hub', 'pillow', 'einops', 'timm')
        .run_commands(f'git clone https://github.com/microsoft/MoGe.git /moge && cd /moge && git checkout {REV}')
        .pip_install('git+https://github.com/EasternJournalist/utils3d-moge.git@62f09d58509485564e24d5d9f6aac9ee9ebc0c37'))


@app.cls(image=bild, gpu=['L4', 'A10G', 'L40S', 'A100', 'T4'], volumes={'/vikter': vol},
         timeout=1200, scaledown_window=60, max_containers=2)
class Djup:
    @modal.enter()
    def ladda(self):
        import sys
        sys.path.insert(0, '/moge')
        from moge.model.v2 import MoGeModel
        self.model = MoGeModel.from_pretrained(MODEL, revision=WEIGHTS_REV, cache_dir='/vikter').cuda().eval()
        vol.commit()

    @modal.method()
    def kor(self, jobb, fov):
        import cv2
        import numpy as np
        import torch
        results = []
        for idx, jpg, png in jobb:
            t = time.perf_counter()
            rgb = cv2.cvtColor(cv2.imdecode(np.frombuffer(jpg, np.uint8), 1), cv2.COLOR_BGR2RGB)
            person = cv2.imdecode(np.frombuffer(png, np.uint8), 0) > 0
            with torch.inference_mode():
                o = self.model.infer(torch.from_numpy(rgb.copy()).permute(2, 0, 1).cuda().float() / 255,
                                     fov_x=fov, resolution_level=7)
            depth = o['depth'].cpu().numpy().astype(np.float32)
            valid = o['mask'].cpu().numpy() & ~person & np.isfinite(depth) & (depth > .1) & (depth < 80)
            depth[~valid] = np.nan
            normal = o['normal'].cpu().numpy().astype(np.float16)
            normal[~valid] = 0
            b = io.BytesIO()
            np.savez_compressed(b, depth=depth, normal=normal, intrinsics=o['intrinsics'].cpu().numpy())
            results.append((idx, b.getvalue(), time.perf_counter() - t))
        return results


@app.local_entrypoint()
def main(klipp: str, ut: str, fokal: float, steg: int = 6):
    import cv2
    import numpy as np
    dest = Path(ut); dest.mkdir(parents=True, exist_ok=True)
    masks = np.load(dest.parent.parent / 'masker.npy', mmap_mode='r')
    cap = cv2.VideoCapture(klipp)
    width, height = int(cap.get(3)), int(cap.get(4))
    # Half-HD portrait retains sharp counter edges without returning multi-GB point maps.
    scale = min(1., 960 / height)
    w, h = round(width * scale), round(height * scale)
    fov = float(np.degrees(2 * np.arctan(width / (2 * fokal))))
    jobs = []
    for i in range(int(cap.get(7))):
        ok, frame = cap.read()
        if not ok: raise RuntimeError(f'Could not decode frame {i}')
        if i % steg or (dest / f'{i:04d}.npz').exists(): continue
        frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)
        mask = cv2.resize(masks[i].astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) * 255
        jobs.append((i, cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 96])[1].tobytes(),
                     cv2.imencode('.png', mask)[1].tobytes()))
    cap.release()
    t = time.perf_counter(); times = []
    print(f'MoGe-2: {len(jobs)} uncached frames, FOV {fov:.2f}', flush=True)
    if jobs:
        for result in Djup().kor.map([jobs[i:i + 12] for i in range(0, len(jobs), 12)], kwargs={'fov': fov}):
            for idx, data, sec in result:
                tmp = dest / f'{idx:04d}.tmp'; tmp.write_bytes(data); tmp.replace(dest / f'{idx:04d}.npz')
                times.append(sec)
            print(f'Depth {len(times)}/{len(jobs)} {time.perf_counter() - t:.1f}s', flush=True)
    (dest / 'modell.json').write_text(json.dumps(dict(model=MODEL, revision=WEIGHTS_REV, code_revision=REV,
        license='MIT; DINOv2 Apache-2.0', step=steg, width=w, height=h, fov_x=fov,
        frames=len(list(dest.glob('*.npz'))), seconds=time.perf_counter()-t), indent=2))
