"""SAM 3D Body (ViT-H) på Modal-GPU. Generell: tar en jobbfil med (bildruta, person, ruta) i stället för att läsa klippet självt.

Kör:  scen/.venv/Scripts/modal.exe run scen/3d/ingest/modal_sam3db.py --klipp <mp4> --jobb <jobb.json> --ut <mapp> --fokal <px> [--masker <personmasker-mapp>]
jobb.json: [[bildruta, person_id, [x0,y0,x1,y1]], ...]   Ut: <ut>/<person>/<bildruta:04d>.npz
Checkpointen cachas i volymen 'sam3db-vikter'. HF-token kommer från secreten 'huggingface'.
"""
import io, json, os, time
import modal

app = modal.App('sam3db-ingest')
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


@app.cls(image=bild, gpu=['L4', 'A10G', 'L40S', 'A100', 'T4'], volumes={'/vikter': vol}, secrets=[modal.Secret.from_name('huggingface')],
         timeout=3600, scaledown_window=120)
class Modell:
    @modal.enter()
    def ladda(self):
        import sys, torch
        sys.path.insert(0, '/kod')
        from huggingface_hub import snapshot_download
        d = snapshot_download('facebook/sam-3d-body-vith', local_dir='/vikter/vith', token=os.environ['HF_TOKEN'])
        vol.commit()
        from sam_3d_body import load_sam_3d_body, SAM3DBodyEstimator
        model, cfg = load_sam_3d_body(f'{d}/model.ckpt', device=torch.device('cuda'), mhr_path=f'{d}/assets/mhr_model.pt')
        self.est = SAM3DBodyEstimator(sam_3d_body_model=model, model_cfg=cfg)

    @modal.method()
    def kor(self, jobb):
        import numpy as np, cv2, torch
        ut = []
        for i, pid, jpg, ruta, K, mpng in jobb:
            img = cv2.cvtColor(cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            mask = None
            if mpng:      # personens egen mask som prompt (halv upplösning -> full)
                mk = cv2.imdecode(np.frombuffer(mpng, np.uint8), cv2.IMREAD_GRAYSCALE)
                mask = (cv2.resize(mk, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST) > 127).astype(np.uint8)[None] * 255
            t = time.time()
            with torch.inference_mode():
                o = self.est.process_one_image(img, bboxes=np.array([ruta], np.float32), masks=mask, cam_int=torch.tensor(np.array(K, np.float32))[None])
            b = io.BytesIO()
            if o:
                np.savez(b, **{k: (v.detach().cpu().numpy() if hasattr(v, 'detach') else np.asarray(v)) for k, v in o[0].items() if hasattr(v, 'shape')})
            ut.append((i, pid, b.getvalue() if o else b'', time.time() - t))
        return ut


@app.local_entrypoint()
def main(klipp: str, jobb: str, ut: str, fokal: float, per_anrop: int = 40, masker: str = ''):
    import numpy as np, cv2
    J = json.load(open(jobb)); per_ruta = {}
    for i, pid, ruta in J:
        if not os.path.exists(f'{ut}/{pid}/{i:04d}.npz'): per_ruta.setdefault(i, []).append((pid, ruta))
    cap = cv2.VideoCapture(klipp); W, H = int(cap.get(3)), int(cap.get(4)); K = [[fokal, 0, W / 2], [0, fokal, H / 2], [0, 0, 1]]
    arbete, i = [], 0
    while per_ruta:
        ok, f = cap.read()
        if not ok: break
        if i in per_ruta:
            jpg = cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 95])[1].tobytes()
            for pid, ruta in per_ruta.pop(i):
                mf = f'{masker}/{pid}/{i:04d}.png' if masker else ''
                arbete.append((i, pid, jpg, ruta, K, open(mf, 'rb').read() if mf and os.path.exists(mf) else b''))
        i += 1
    print('jobb', len(arbete), flush=True)
    t0 = time.time(); tider = []
    for svar in Modell().kor.map([arbete[k:k + per_anrop] for k in range(0, len(arbete), per_anrop)]):
        for idx, pid, data, sek in svar:
            os.makedirs(f'{ut}/{pid}', exist_ok=True)
            if data: open(f'{ut}/{pid}/{idx:04d}.npz', 'wb').write(data)
            tider.append(sek)
        print('klara', len(tider), '/', len(arbete), round(time.time() - t0, 1), 's', flush=True)
    json.dump(dict(jobb=len(tider), sek_per_jobb_median=float(np.median(tider)) if tider else None, total_s=time.time() - t0), open(f'{ut}/timing.json', 'w'))
