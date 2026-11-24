"""Uppdrag 0006: framåtmatad flervyrekonstruktion (VGGT-1B) på Modal ur nyckelbilder, en bild per tagning och körning.
Kör (från scen/):  .venv/Scripts/modal.exe run 3d/ingest/flervy_prov/modal_vggt.py
Skickar bara nyckelbilder (11 per körning för b-tilltal, 4 för guacamole, tre olika bildurval vardera). Skriver vggt_resultat.pkl.
Licens: VGGT-1B (facebook/VGGT-1B) ligger under Metas VGGT-licens för icke-kommersiell forskning; koden i facebookresearch/vggt likaså. Notera i svaret."""
import io, json, os, pickle, time
import modal

app = modal.App('flervy-vggt')
bild = (
    modal.Image.debian_slim(python_version='3.11')
    .apt_install('git', 'libgl1', 'libglib2.0-0')
    .pip_install('torch==2.6.0', 'torchvision==0.21.0', index_url='https://download.pytorch.org/whl/cu124')
    .pip_install('numpy<2', 'pillow', 'huggingface_hub', 'einops', 'safetensors', 'opencv-python-headless', 'scipy')
    .run_commands('git clone --depth 1 https://github.com/facebookresearch/vggt.git /kod')
)


@app.cls(image=bild, gpu=['L40S', 'A100', 'A10G'], timeout=1800, secrets=[modal.Secret.from_name('huggingface')], scaledown_window=60)
class Vggt:
    @modal.enter()
    def ladda(self):
        import sys, torch
        sys.path.insert(0, '/kod')
        from vggt.models.vggt import VGGT
        self.fel = []
        self.m = VGGT.from_pretrained('facebook/VGGT-1B').to('cuda').eval()
        self.dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16

    @modal.method()
    def kor(self, korningar):
        import sys, numpy as np, torch
        sys.path.insert(0, '/kod')
        from vggt.utils.load_fn import load_and_preprocess_images
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
        ut = []; t0 = time.time()
        for k in korningar:
            sokv = []
            for i, jpg in enumerate(k['jpg']):
                p = f'/tmp/{k["namn"]}_{i}.jpg'; open(p, 'wb').write(jpg); sokv.append(p)
            im = load_and_preprocess_images(sokv, mode='pad').to('cuda')                 # (S,3,518,518), liggande/stående bilder paddas
            with torch.no_grad(), torch.autocast('cuda', dtype=self.dtype):
                pr = self.m(im)
            ex, intr = pose_encoding_to_extri_intri(pr['pose_enc'], im.shape[-2:])
            wp = pr['world_points'][0].float().cpu().numpy(); wc = pr['world_points_conf'][0].float().cpu().numpy()
            dep = pr['depth'][0, ..., 0].float().cpu().numpy(); dc = pr['depth_conf'][0].float().cpu().numpy()
            ut.append(dict(namn=k['namn'], ids=k['ids'], extrinsic=ex[0].float().cpu().numpy(), intrinsic=intr[0].float().cpu().numpy(), bildstorlek=list(im.shape[-2:]),
                           world_points=wp[:, ::3, ::3].astype('float16'), world_conf=wc[:, ::3, ::3].astype('float16'),
                           depth=dep[:, ::3, ::3].astype('float16'), depth_conf=dc[:, ::3, ::3].astype('float16'), orig_storlek=k['orig']))
        return dict(resultat=ut, sekunder=round(time.time() - t0, 1), gpu=torch.cuda.get_device_name(0), fel=self.fel)


@app.local_entrypoint()
def main():
    import cv2
    HERE = os.path.dirname(os.path.abspath(__file__)); ING = os.path.abspath(os.path.join(HERE, '..'))
    korningar = []
    for klipp, sidor in (('b-tilltal-ravara-tagningar', 11), ('e-dialog-guacamole-tagningar', 4)):
        I = f'{ING}/ut/{klipp}'
        for q in (.2, .5, .8):
            jpg, ids, orig = [], [], None
            for i in range(1, sidor + 1):
                cap = cv2.VideoCapture(f'{I}/klipp/S{i}.mp4'); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); f = int(round(q * (n - 1))); cap.set(cv2.CAP_PROP_POS_FRAMES, f)
                ok, img = cap.read(); assert ok; orig = img.shape[:2]
                jpg.append(cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tobytes()); ids.append(f'S{i}_{f}')
            korningar.append(dict(namn=f'{klipp.split("-")[0]}_q{int(q * 100)}', jpg=jpg, ids=ids, orig=list(orig)))
    print(len(korningar), 'körningar,', sum(len(k['jpg']) for k in korningar), 'bilder skickas', flush=True)
    t0 = time.time(); r = Vggt().kor.remote(korningar)
    pickle.dump(r, open(f'{HERE}/vggt_resultat.pkl', 'wb'))
    print('klart', len(r['resultat']), 'körningar, GPU-sekunder', r['sekunder'], r['gpu'], 'väggtid', round(time.time() - t0), 'fel', r['fel'])
