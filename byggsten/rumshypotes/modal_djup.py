"""MoGe-2 med personerna kvar: en nyckelruta per tagning, för skalan per tagning.

Kedjans scen/3d/ingest/modal_rum.py maskar bort personerna. Här behövs djupet på kroppen för att
jämföra med SAM 3D Body, där kroppens storlek är skalankaret. Varje ruta körs två gånger:
- med klippets fokal (samma som observationerna)
- utan fokal, så att MoGe:s egen FOV syns som kontroll av fokalen

Samma modell, vikter och kodrevision som kedjan. Rutan är samma nyckelruta som obs_ingest.py väljer.

    scen/.venv/Scripts/modal.exe run byggsten/rumshypotes/modal_djup.py \
        --ingest scen/3d/ingest/ut/notan-tagningar --ut byggsten/rumshypotes/ut/notan/djup --fokal 983.7
"""
import io
import json
import time
from pathlib import Path

import modal

REV = '74fbce054ebed49800de42d0ad0e83495065719a'
WEIGHTS_REV = 'cb0e8bbd6b1e243589717c78e750b1ba4c093acf'
MODEL = 'Ruicheng/moge-2-vitl-normal'
app = modal.App('rumshypotes-djup')
vol = modal.Volume.from_name('rum-moge2-vikter', create_if_missing=True)
bild = (modal.Image.debian_slim(python_version='3.11')
        .apt_install('git', 'libgl1', 'libglib2.0-0')
        .pip_install('torch==2.5.1', 'torchvision==0.20.1', index_url='https://download.pytorch.org/whl/cu124')
        .pip_install('numpy<2.3', 'scipy', 'opencv-python-headless', 'huggingface_hub', 'pillow', 'einops', 'timm')
        .run_commands(f'git clone https://github.com/microsoft/MoGe.git /moge && cd /moge && git checkout {REV}')
        .pip_install('git+https://github.com/EasternJournalist/utils3d-moge.git@62f09d58509485564e24d5d9f6aac9ee9ebc0c37'))


@app.cls(image=bild, gpu=['L4', 'A10G', 'L40S', 'A100', 'T4'], volumes={'/vikter': vol},
         timeout=900, scaledown_window=30, max_containers=1)
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
        ut = []
        for S, idx, jpg in jobb:
            t0 = time.perf_counter()
            rgb = cv2.cvtColor(cv2.imdecode(np.frombuffer(jpg, np.uint8), 1), cv2.COLOR_BGR2RGB)
            x = torch.from_numpy(rgb.copy()).permute(2, 0, 1).cuda().float() / 255
            with torch.inference_mode():
                o = self.model.infer(x, fov_x=fov, resolution_level=7)
                e = self.model.infer(x, resolution_level=7)
            delar = {}
            for namn, r in (('', o), ('_egen', e)):
                d = r['depth'].cpu().numpy().astype(np.float32)
                ok = r['mask'].cpu().numpy() & np.isfinite(d) & (d > .1) & (d < 80)
                d[~ok] = np.nan
                delar['depth' + namn] = d
                delar['intrinsics' + namn] = r['intrinsics'].cpu().numpy()
            n = o['normal'].cpu().numpy().astype(np.float16)
            n[~np.isfinite(delar['depth'])] = 0
            delar['normal'] = n
            Ke = delar['intrinsics_egen']
            fov_egen = float(np.degrees(2 * np.arctan(0.5 / Ke[0, 0])))
            b = io.BytesIO()
            np.savez_compressed(b, **delar)
            ut.append((S, idx, b.getvalue(), fov_egen, time.perf_counter() - t0))
        return ut


@app.local_entrypoint()
def main(ingest: str, ut: str, fokal: float):
    import cv2
    import numpy as np
    ing, dest = Path(ingest), Path(ut)
    dest.mkdir(parents=True, exist_ok=True)
    info = json.loads((dest / 'modell.json').read_text()) if (dest / 'modell.json').exists() else {}
    jobb, fov = [], None
    tagn = sorted((p.name for p in ing.iterdir() if p.is_dir() and p.name[:1] == 'S' and p.name[1:].isdigit()),
                  key=lambda s: int(s[1:]))
    for S in tagn:
        if (dest / f'{S}.npz').exists():
            continue
        N = json.loads((ing / S / 'meta.json').read_text())['N']
        idx = min((int(f.stem) for f in (ing / S / 'rum' / 'depth').glob('*.npz')), key=lambda i: abs(i - N // 2))
        cap = cv2.VideoCapture(str(ing / 'klipp' / f'{S}.mp4'))
        for _ in range(idx + 1):
            ok, frame = cap.read()
        cap.release()
        if not ok:
            raise RuntimeError(f'{S}: kunde inte läsa ruta {idx}')
        bredd, hojd = frame.shape[1], frame.shape[0]
        skala = min(1., 960 / hojd)
        frame = cv2.resize(frame, (round(bredd * skala), round(hojd * skala)), interpolation=cv2.INTER_AREA)
        fov = float(np.degrees(2 * np.arctan(bredd / (2 * fokal))))
        jobb.append((S, idx, cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 96])[1].tobytes()))
    t = time.perf_counter()
    print(f'MoGe-2 utan personmask: {len(jobb)} rutor, FOV {fov}', flush=True)
    if jobb:
        for res in Djup().kor.map([jobb], kwargs={'fov': fov}):
            for S, idx, data, fov_egen, sek in res:
                tmp = dest / f'{S}.tmp'
                tmp.write_bytes(data)
                tmp.replace(dest / f'{S}.npz')
                info[S] = dict(ruta=idx, fov_given=fov, fov_egen=round(fov_egen, 2), sekunder=round(sek, 2))
                print(S, info[S], flush=True)
    info['_modell'] = dict(model=MODEL, revision=WEIGHTS_REV, code_revision=REV, license='MIT; DINOv2 Apache-2.0',
                           sekunder=round(time.perf_counter() - t, 1))
    (dest / 'modell.json').write_text(json.dumps(info, indent=2))
