"""Feed-forward-rekonstruktion över alla tagningar i ett pass med VGGT (facebookresearch/vggt), för att pröva "gemensamt rum över tagningar" (PIPE.md Öppet 3/6).
Kör (från scen/):  .venv/Scripts/modal.exe run 3d/ingest/modal_ffrek_vggt.py --ingest 3d/ingest/ut/b-tilltal-ravara-tagningar --antal 5
Installation exakt enligt README (git clone + pip install -r requirements.txt). Checkpoint: facebook/VGGT-1B-Commercial om den går att ladda, annars facebook/VGGT-1B.
Personer maskeras med ingestens YOLO-rutor (<S>/jobb.json) genom att pixlarna sätts svarta (README: maskera med 0). En container, ett pass (alla bilder samtidigt).
Skriver <ingest>/ffrek/vggt/vggt_ra.npz + korning.json + in_*.jpg. Analys: ffrek_analys.py."""
import io, json, os, time
import modal

app = modal.App('ffrek-vggt')
bild = (
    modal.Image.debian_slim(python_version='3.11')
    .apt_install('git', 'libgl1', 'libglib2.0-0')
    .run_commands('git clone https://github.com/facebookresearch/vggt.git /vggt', 'cd /vggt && pip install -r requirements.txt')
    .env({'PYTHONPATH': '/vggt'})
)


@app.function(image=bild, gpu='H100', timeout=1800, secrets=[modal.Secret.from_name('huggingface')])
def kor(jpgs):
    import numpy as np, torch, tempfile
    from vggt.models.vggt import VGGT
    from vggt.utils.load_fn import load_and_preprocess_images
    from vggt.utils.pose_enc import pose_encoding_to_extri_intri
    t0 = time.time(); logg = []
    model = None
    for repo in ['facebook/VGGT-1B-Commercial', 'facebook/VGGT-1B']:
        try:
            model = VGGT.from_pretrained(repo); logg.append(f'laddad via from_pretrained: {repo}'); break
        except Exception as ex:
            logg.append(f'from_pretrained {repo}: {repr(ex)[:400]}')
            try:
                from huggingface_hub import hf_hub_download
                p = hf_hub_download(repo, 'model.pt'); model = VGGT(); model.load_state_dict(torch.load(p, map_location='cpu')); logg.append(f'laddad via model.pt: {repo}'); break
            except Exception as ex2:
                logg.append(f'model.pt {repo}: {repr(ex2)[:400]}')
    model = model.to('cuda').eval()
    t_ladd = time.time() - t0
    d = tempfile.mkdtemp(); namn = []
    for i, b in enumerate(jpgs):
        p = f'{d}/{i:03d}.jpg'; open(p, 'wb').write(b); namn.append(p)
    images = load_and_preprocess_images(namn, mode='pad').to('cuda')
    dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    t1 = time.time()
    with torch.no_grad():
        with torch.cuda.amp.autocast(dtype=dtype):
            pred = model(images)
        extr, intr = pose_encoding_to_extri_intri(pred['pose_enc'], images.shape[-2:])
    torch.cuda.synchronize(); t_inf = time.time() - t1
    f = lambda x: x.float().cpu().numpy()
    buf = io.BytesIO()
    np.savez_compressed(buf, extrinsic=f(extr[0]), intrinsic=f(intr[0]), depth=f(pred['depth'][0]).astype(np.float16), depth_conf=f(pred['depth_conf'][0]).astype(np.float16),
                        world_points=f(pred['world_points'][0]).astype(np.float16), world_points_conf=f(pred['world_points_conf'][0]).astype(np.float16),
                        images=(f(images) * 255).astype(np.uint8))
    return dict(npz=buf.getvalue(), logg=logg, gpu=torch.cuda.get_device_name(0), t_ladd=round(t_ladd, 1), t_inf=round(t_inf, 2),
                mem_gb=round(torch.cuda.max_memory_allocated() / 1e9, 1), form=list(images.shape))


@app.local_entrypoint()
def main(ingest: str, antal: int = 5):
    import cv2
    I = os.path.abspath(ingest); ut = f'{I}/ffrek/vggt'; os.makedirs(ut, exist_ok=True)
    jpgs, meta = [], []
    for sid in sorted([d for d in os.listdir(I) if d.startswith('S') and d[1:].isdigit() and os.path.exists(f'{I}/klipp/{d}.mp4')], key=lambda x: int(x[1:])):
        rutor = {}
        for fr, pid, box in json.load(open(f'{I}/{sid}/jobb.json')): rutor.setdefault(fr, []).append(box)
        cap = cv2.VideoCapture(f'{I}/klipp/{sid}.mp4'); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for q in [.1 + .8 * i / max(antal - 1, 1) for i in range(antal)]:
            fr = int(round(q * (n - 1)))
            if fr not in rutor and rutor: fr = min(rutor, key=lambda k: abs(k - fr))
            cap.set(cv2.CAP_PROP_POS_FRAMES, fr); ok, img = cap.read()
            if not ok: continue
            for x0, y0, x1, y1 in rutor.get(fr, []):
                pad = 0.06 * (x1 - x0)
                img[max(0, int(y0 - pad)):int(y1 + pad), max(0, int(x0 - pad)):int(x1 + pad)] = 0
            jpgs.append(cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tobytes())
            meta.append(dict(i=len(meta), tagning=sid, ruta=fr, bredd=img.shape[1], hojd=img.shape[0], personrutor=len(rutor.get(fr, []))))
            cv2.imwrite(f'{ut}/in_{len(meta)-1:03d}_{sid}_{fr}.jpg', img)
    print(len(jpgs), 'bilder i ett pass', flush=True)
    t0 = time.time(); r = kor.remote(jpgs); vagg = round(time.time() - t0, 1)
    open(f'{ut}/vggt_ra.npz', 'wb').write(r.pop('npz'))
    r.update(vagg_s=vagg, bilder=meta)
    json.dump(r, open(f'{ut}/korning.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('klart', {k: v for k, v in r.items() if k != 'bilder'})
