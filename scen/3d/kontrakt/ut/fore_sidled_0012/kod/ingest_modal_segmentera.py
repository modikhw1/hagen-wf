"""Uppdrag 0008 del B / 0010 punkt 3: öppen-vokabulär segmentering på Modal. Grounding DINO (textprompt -> ruta) + SAM 2 (ruta -> mask -> tät ruta).
Kör (från scen/):  .venv/Scripts/modal.exe run 3d/ingest/modal_segmentera.py --ingest <ingestmapp> --prompter <json med element -> engelsk prompt> --ut <fil>
Skickar bara nyckelbilder (4 per tagning ur klippen). Skriver <fil> (rutor per bild, se rum_rutor.py). Licenser: Grounding DINO (Apache-2.0), SAM 2 (Apache-2.0).
Vikterna hämtas från Hugging Face (secreten 'huggingface'). Kostnaden redovisas av körningen (GPU-sekunder)."""
import io, json, os, time
import modal

app = modal.App('rutprov-gdino-sam2')
bild = (
    modal.Image.debian_slim(python_version='3.11')
    .apt_install('libgl1', 'libglib2.0-0')
    .pip_install('torch==2.6.0', 'torchvision==0.21.0', index_url='https://download.pytorch.org/whl/cu124')
    .pip_install('transformers>=4.56', 'pillow', 'numpy<2.3', 'accelerate', 'scipy', 'huggingface_hub')
)


@app.cls(image=bild, gpu=['L4', 'T4', 'A10G'], timeout=1800, secrets=[modal.Secret.from_name('huggingface')], scaledown_window=60)
class Seg:
    @modal.enter()
    def ladda(self):
        import torch
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
        self.dev = 'cuda'; self.fel = []
        self.dp = AutoProcessor.from_pretrained('IDEA-Research/grounding-dino-base')
        self.dm = AutoModelForZeroShotObjectDetection.from_pretrained('IDEA-Research/grounding-dino-base').to(self.dev).eval()
        try:
            from transformers import Sam2Model, Sam2Processor
            self.sp = Sam2Processor.from_pretrained('facebook/sam2.1-hiera-large'); self.sm = Sam2Model.from_pretrained('facebook/sam2.1-hiera-large').to(self.dev).eval()
        except Exception as ex:                                      # SAM 2 i transformers saknas eller kan inte laddas: bara rutor från Grounding DINO
            self.sp = self.sm = None; self.fel.append('sam2: ' + repr(ex)[:300])

    @modal.method()
    def kor(self, jobb):
        import numpy as np, torch
        from PIL import Image
        ut = []; t0 = time.time()
        for j in jobb:
            img = Image.open(io.BytesIO(j['jpg'])).convert('RGB'); w, h = img.size
            text = '. '.join(j['prompter']) + '.'
            with torch.inference_mode():
                inp = self.dp(images=img, text=text, return_tensors='pt').to(self.dev); o = self.dm(**inp)
            res = self.dp.post_process_grounded_object_detection(o, inp.input_ids, threshold=.25, text_threshold=.2, target_sizes=[(h, w)])[0]
            lab = res.get('text_labels', res.get('labels'))
            fynd = [dict(etikett=str(l), poang=round(float(s), 3), dino_box_px=[round(float(v), 1) for v in b.tolist()]) for b, s, l in zip(res['boxes'], res['scores'], lab)]
            if self.sm is not None and fynd:
                try:
                    boxar = [[f['dino_box_px']] for f in fynd][:12]
                    si = self.sp(images=img, input_boxes=[[f['dino_box_px'] for f in fynd[:12]]], return_tensors='pt').to(self.dev)
                    with torch.inference_mode(): so = self.sm(**si, multimask_output=False)
                    masker = self.sp.post_process_masks(so.pred_masks.cpu(), si['original_sizes'])[0]       # (n, 1, h, w)
                    for f, m in zip(fynd, masker):
                        mm = np.asarray(m[0] > 0) if hasattr(m[0], 'numpy') is False else (m[0] > 0).numpy()
                        ys, xs = np.where(mm)
                        if len(xs): f['mask_box_px'] = [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]; f['mask_area_andel'] = round(float(mm.mean()), 4)
                except Exception as ex: self.fel.append(f"sam2 {j['id']}: {repr(ex)[:300]}")
            ut.append(dict(id=j['id'], bredd=w, hojd=h, fynd=fynd))
        return dict(resultat=ut, sekunder=round(time.time() - t0, 1), fel=self.fel[:10])


@app.local_entrypoint()
def main(ingest: str, prompter: str, ut: str, antal: int = 4):
    import cv2
    I = os.path.abspath(ingest); P = json.load(open(prompter, encoding='utf8')); prompt = list(dict.fromkeys(P.values()))
    jobb = []
    for sid in sorted([d for d in os.listdir(I) if d.startswith('S') and d[1:].isdigit() and os.path.exists(f'{I}/klipp/{d}.mp4')], key=lambda x: int(x[1:])):
        cap = cv2.VideoCapture(f'{I}/klipp/{sid}.mp4'); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for q in [.12 + .76 * i / max(antal - 1, 1) for i in range(antal)]:
            f = int(round(q * (n - 1))); cap.set(cv2.CAP_PROP_POS_FRAMES, f); ok, img = cap.read()
            if ok: jobb.append(dict(id=f'{sid}_{f}', jpg=cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes(), prompter=prompt))
    print(len(jobb), 'bilder skickas', flush=True)
    t0 = time.time(); r = Seg().kor.remote(jobb); r['prompter'] = P
    json.dump(r, open(ut, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('klart', len(r['resultat']), 'bilder, GPU-sekunder', r['sekunder'], 'väggtid', round(time.time() - t0), 'fel', r['fel'])
