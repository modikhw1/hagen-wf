"""Uppdrag 0011: Depth Anything 3 (Apache-2.0-varianterna DA3-BASE + DA3METRIC-LARGE) på Modal ur samma nyckelbilder som VGGT-provet (0006).
Kör (från scen/):  .venv/Scripts/modal.exe run 3d/ingest/flervy_prov/modal_da3.py
Återanvänder bild och vikter ur 3d/rumsbank/modal_da3.py (volymen `hagen-rumsbank-da3-apache`, vikterna ligger redan i den).
Körs både med personerna kvar och med personerna maskade (ingestens masker.npy, gråfyllda). Skriver da3_resultat.pkl.
Licens: DA3-BASE och DA3METRIC-LARGE är Apache-2.0 (det är inte NC-varianten `Nested`/`Giant`); bekräftas mot modellkorten i svaret."""
import io, json, os, pickle, time
import modal

app = modal.App('flervy-da3')
vol = modal.Volume.from_name('hagen-rumsbank-da3-apache', create_if_missing=False)
SHA = '3d835ec1a5802d64a8b8b15f817a1ab54809bfe4'
image = (modal.Image.debian_slim(python_version='3.11')
         .apt_install('git', 'libgl1', 'libglib2.0-0')
         .pip_install('torch==2.7.1', 'torchvision==0.22.1', index_url='https://download.pytorch.org/whl/cu128')
         .pip_install('xformers==0.0.31.post1', 'addict')
         .run_commands('git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git /opt/da3', f'cd /opt/da3 && git checkout {SHA}', 'pip install -e /opt/da3')
         .env({'HF_HUB_DISABLE_IMPLICIT_TOKEN': '1', 'OMP_NUM_THREADS': '4'}))


@app.function(image=image, gpu='A100-80GB', volumes={'/weights': vol}, timeout=1500, memory=32768, scaledown_window=2, max_containers=1)
def kor(jobb):
    import numpy as np, torch, cv2
    from pathlib import Path
    from depth_anything_3.api import DepthAnything3
    torch.set_num_threads(4); cv2.setNumThreads(2); t0 = time.monotonic()
    base = DepthAnything3.from_pretrained('/weights/base', local_files_only=True).cuda().eval()
    metric = DepthAnything3.from_pretrained('/weights/metric', local_files_only=True).cuda().eval()
    ut = []
    for j in jobb:
        d = Path('/tmp/da3') / j['namn']; d.mkdir(parents=True, exist_ok=True); paths = []
        for i, data in enumerate(j['jpg']):
            p = d / f'{i:05d}.jpg'; p.write_bytes(data); paths.append(str(p))
        pred = base.inference(paths, process_res=504)
        md = np.stack([metric.inference([p], process_res=504).depth[0].copy() for p in paths])
        f = (pred.intrinsics[:, 0, 0] + pred.intrinsics[:, 1, 1]) / 2; metric_m = md * f[:, None, None] / 300.
        good = np.isfinite(pred.depth) & (pred.depth > .001) & np.isfinite(metric_m) & (metric_m > .05) & (metric_m < 50)
        if pred.conf is not None: good &= pred.conf > np.median(pred.conf)
        scale = float(np.median(metric_m[good] / pred.depth[good]))
        E = np.tile(np.eye(4), (len(paths), 1, 1)); E[:, :3, :] = pred.extrinsics[:, :3, :]; E[:, :3, 3] *= scale
        ut.append(dict(namn=j['namn'], ids=j['ids'], skala=scale, intrinsic=np.asarray(pred.intrinsics), extrinsic_cw=E, depth_z=(pred.depth * scale).astype('float16'),
                       metric_m=metric_m.astype('float16'), conf=None if pred.conf is None else np.asarray(pred.conf).astype('float16'), proc_storlek=list(pred.depth.shape[1:]),
                       orig_storlek=j['orig'], maskerad=j['maskerad']))
    return dict(resultat=ut, sekunder=round(time.monotonic() - t0, 1), gpu=torch.cuda.get_device_name(0))


@app.local_entrypoint()
def main():
    import cv2, numpy as np
    HERE = os.path.dirname(os.path.abspath(__file__)); ING = os.path.abspath(os.path.join(HERE, '..'))
    jobb = []
    for klipp, sidor in (('b-tilltal-ravara-tagningar', 11), ('e-dialog-guacamole-tagningar', 4)):
        I = f'{ING}/ut/{klipp}'
        for q in (.2, .5, .8):
            for mask in (False, True):
                jpg, ids, orig = [], [], None
                for i in range(1, sidor + 1):
                    cap = cv2.VideoCapture(f'{I}/klipp/S{i}.mp4'); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); f = int(round(q * (n - 1))); cap.set(cv2.CAP_PROP_POS_FRAMES, f)
                    ok, img = cap.read(); assert ok; orig = img.shape[:2]
                    if mask:
                        M = np.load(f'{I}/S{i}/masker.npy', allow_pickle=True)
                        pm = cv2.dilate(cv2.resize(M[min(f, len(M) - 1)].astype(np.uint8) * 255, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST), np.ones((15, 15), np.uint8)) > 0
                        img = img.copy(); img[pm] = (127, 127, 127)
                    jpg.append(cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tobytes()); ids.append(f'S{i}_{f}')
                jobb.append(dict(namn=f'{klipp.split("-")[0]}_q{int(q * 100)}_{"mask" if mask else "med"}', jpg=jpg, ids=ids, orig=list(orig), maskerad=mask))
    print(len(jobb), 'körningar,', sum(len(j['jpg']) for j in jobb), 'bilder skickas', flush=True)
    t0 = time.time(); r = kor.remote(jobb)
    pickle.dump(r, open(f'{HERE}/da3_resultat.pkl', 'wb'))
    print('klart', len(r['resultat']), 'körningar, GPU-sekunder', r['sekunder'], r['gpu'], 'väggtid', round(time.time() - t0))
