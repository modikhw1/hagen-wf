"""SAM 3D Body (ViT-H) på Modal-GPU för ett helt klipp.

Kör:  scen/.venv/Scripts/modal.exe run scen/3d/klipp2/sam3db/modal_sam3db.py --klipp <mp4> --masker <masker.npy> --ut <mapp> [--steg 1] [--fokal 2154.07]
Kräver Modal-secret 'huggingface' med HF_TOKEN (gated repo facebook/sam-3d-body-vith).
Utdata: en .npz per bildruta (samma nycklar som lokalt), plus timing.json.
Checkpointen cachas i en Modal-volym, så bara första körningen laddar ner den.
"""
import io, json, os, time
import modal

app = modal.App('sam3db')
vol = modal.Volume.from_name('sam3db-vikter', create_if_missing=True)
bild = (
    modal.Image.debian_slim(python_version='3.11')
    .apt_install('git', 'libgl1', 'libglib2.0-0')
    .pip_install('torch==2.5.1', 'torchvision==0.20.1', index_url='https://download.pytorch.org/whl/cu124')
    .pip_install('pytorch-lightning', 'opencv-python-headless', 'yacs', 'scikit-image', 'einops', 'timm', 'dill', 'pandas', 'rich',
                 'hydra-core', 'pyrootutils', 'roma', 'joblib', 'loguru', 'optree', 'fvcore', 'huggingface_hub', 'jsonlines',
                 'networkx==3.2.1', 'braceexpand', 'webdataset', 'numpy<2.3')
    .run_commands('git clone --depth 1 https://github.com/facebookresearch/sam-3d-body.git /kod')
)


@app.cls(image=bild, gpu=['L4', 'A10G', 'L40S', 'A100', 'T4'], volumes={'/vikter': vol}, secrets=[modal.Secret.from_name('huggingface')], timeout=3600, scaledown_window=120)
class Modell:
    @modal.enter()
    def ladda(self):
        import sys, torch
        sys.path.insert(0, '/kod')
        from huggingface_hub import snapshot_download
        d = snapshot_download('facebook/sam-3d-body-vith', local_dir='/vikter/vith', token=os.environ['HF_TOKEN'])
        vol.commit()
        from sam_3d_body import load_sam_3d_body, SAM3DBodyEstimator
        t = time.time()
        model, cfg = load_sam_3d_body(f'{d}/model.ckpt', device=torch.device('cuda'), mhr_path=f'{d}/assets/mhr_model.pt')
        self.est = SAM3DBodyEstimator(sam_3d_body_model=model, model_cfg=cfg)
        print('laddad', round(time.time() - t, 1), 's')

    @modal.method()
    def kor(self, jobb):
        """jobb: lista av (index, jpg-bytes, ruta[4], K 3x3). Returnerar lista av (index, npz-bytes, sekunder)."""
        import numpy as np, cv2, torch
        ut = []
        for i, jpg, ruta, K in jobb:
            img = cv2.cvtColor(cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            t = time.time()
            with torch.inference_mode():
                o = self.est.process_one_image(img, bboxes=np.array([ruta], np.float32), cam_int=torch.tensor(np.array(K, np.float32))[None])
            b = io.BytesIO()
            if o:
                np.savez(b, **{k: (v.detach().cpu().numpy() if hasattr(v, 'detach') else np.asarray(v)) for k, v in o[0].items() if hasattr(v, 'shape')})
            ut.append((i, b.getvalue() if o else b'', time.time() - t))
        return ut


@app.local_entrypoint()
def main(klipp: str, masker: str, ut: str, steg: int = 1, fokal: float = 2154.07, per_anrop: int = 24):
    import numpy as np, cv2
    os.makedirs(ut, exist_ok=True)
    M = np.load(masker); cap = cv2.VideoCapture(klipp)
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); sx, sy = W / M.shape[2], H / M.shape[1]
    K = [[fokal, 0, W / 2], [0, fokal, H / 2], [0, 0, 1]]
    jobb, i = [], 0
    while True:
        ok, f = cap.read()
        if not ok: break
        if i % steg == 0 and not os.path.exists(f'{ut}/{i:04d}.npz'):
            ys, xs = np.nonzero(M[i])
            if len(xs) >= 50:
                jobb.append((i, cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 95])[1].tobytes(),
                             [float(xs.min() * sx), float(ys.min() * sy), float(xs.max() * sx), float(ys.max() * sy)], K))
        i += 1
    print('bildrutor att köra', len(jobb), flush=True)
    t0 = time.time(); tider = []
    delar = [jobb[k:k + per_anrop] for k in range(0, len(jobb), per_anrop)]
    for svar in Modell().kor.map(delar):
        for idx, data, sek in svar:
            if data: open(f'{ut}/{idx:04d}.npz', 'wb').write(data)
            tider.append(sek)
        print('klara', len(tider), '/', len(jobb), round(time.time() - t0, 1), 's', flush=True)
    json.dump(dict(bildrutor=len(tider), sek_per_ruta_median=float(np.median(tider)) if tider else None, total_s=time.time() - t0), open(f'{ut}/timing.json', 'w'))
