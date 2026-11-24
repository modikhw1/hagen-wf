"""0025 del B: segmenterarens masker för färgkodningens rutor. Samma modeller och trösklar som ingest/modal_segmentera.py
(Grounding DINO base, textprompt -> ruta, SAM 2.1 hiera-large, ruta -> mask, L4, deterministiskt, en prompt per pass), men masken
sparas som PNG i stället för bara rutans mått. Kedjans fil ändras inte.

  (från scen/) .venv/Scripts/modal.exe run 3d/gennedbrytning/fargkod/modal_seg_mask.py --ut 3d/gennedbrytning/fargkod/seg
Bilder: fargkod/rutor/<klipp>_<ruta>.png. Prompter per id i PROMPTER. Ut per bild och id: seg/<bild>__<id>.png (bästa fyndets mask,
eller unionen av fynd med poäng >= 0,35) och seg/seg.json (poäng, rutor, GPU-sekunder).
"""
import io, json, os, time
from pathlib import Path
import modal

app = modal.App('fargkod-seg-mask')
bild = (modal.Image.debian_slim(python_version='3.11').apt_install('libgl1', 'libglib2.0-0')
        .pip_install('torch==2.6.0', 'torchvision==0.21.0', index_url='https://download.pytorch.org/whl/cu124')
        .pip_install('transformers>=4.56', 'pillow', 'numpy<2.3', 'accelerate', 'scipy', 'huggingface_hub'))
PROMPTER = {'gelato': {'disk_A': 'ice cream display counter', 'bakgrund': 'back wall', 'A:hand:provsked': 'small spoon', 'person': 'woman'},
            'guac': {'bardisk': 'bar counter', 'stol_A': 'bar stool', 'vagg_bak': 'wall mural', 'foremal_i_hand_A': 'phone', 'person': 'man'}}


@app.cls(image=bild, gpu='L4', max_containers=4, timeout=1800, secrets=[modal.Secret.from_name('huggingface')], scaledown_window=60)
class Seg:
    @modal.enter()
    def ladda(self):
        import torch
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor, Sam2Model, Sam2Processor
        torch.manual_seed(0); torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False
        torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
        self.dp = AutoProcessor.from_pretrained('IDEA-Research/grounding-dino-base')
        self.dm = AutoModelForZeroShotObjectDetection.from_pretrained('IDEA-Research/grounding-dino-base').to('cuda').eval()
        self.sp = Sam2Processor.from_pretrained('facebook/sam2.1-hiera-large'); self.sm = Sam2Model.from_pretrained('facebook/sam2.1-hiera-large').to('cuda').eval()

    @modal.method()
    def kor(self, jobb):
        import numpy as np, torch
        from PIL import Image
        t0 = time.time(); img = Image.open(io.BytesIO(jobb['png'])).convert('RGB'); w, h = img.size; ut = {}
        for id_, pr in jobb['prompter'].items():
            with torch.inference_mode():
                inp = self.dp(images=img, text=pr + '.', return_tensors='pt').to('cuda'); o = self.dm(**inp)
            res = self.dp.post_process_grounded_object_detection(o, inp.input_ids, threshold=.25, text_threshold=.2, target_sizes=[(h, w)])[0]
            fynd = sorted([(float(s), [float(v) for v in b.tolist()]) for b, s in zip(res['boxes'], res['scores'])], key=lambda f: (-f[0], f[1]))
            if not fynd: ut[id_] = dict(prompt=pr, fynd=0); continue
            val = [f for f in fynd if f[0] >= .35] or fynd[:1]
            si = self.sp(images=img, input_boxes=[[b for _, b in val]], return_tensors='pt').to('cuda')
            with torch.inference_mode(): so = self.sm(**si, multimask_output=False)
            mk = self.sp.post_process_masks(so.pred_masks.cpu(), si['original_sizes'])[0]
            m = np.zeros((h, w), bool)
            for x in mk: m |= (x[0] > 0).numpy()
            b = io.BytesIO(); Image.fromarray((m * 255).astype('uint8')).save(b, 'PNG')
            ut[id_] = dict(prompt=pr, fynd=len(fynd), anvanda=len(val), poang=[round(s, 3) for s, _ in val], rutor=[[round(v, 1) for v in bx] for _, bx in val], png=b.getvalue())
        return dict(bild=jobb['bild'], ut=ut, sekunder=round(time.time() - t0, 1))


@app.local_entrypoint()
def main(ut: str):
    R = Path(__file__).resolve().parent / 'rutor'; U = Path(ut); U.mkdir(parents=True, exist_ok=True)
    jobb = [dict(bild=p.stem, png=p.read_bytes(), prompter=PROMPTER[p.stem.split('_')[0]]) for p in sorted(R.glob('*.png')) if p.stem.count('_') == 1]
    svar = list(Seg().kor.map(jobb)); sam = {}
    for s in svar:
        for id_, r in s['ut'].items():
            if 'png' in r: (U / f"{s['bild']}__{id_.replace(':', '-')}.png").write_bytes(r.pop('png'))
        sam[s['bild']] = dict(ut=s['ut'], sekunder=s['sekunder'])
    sam['gpu_sekunder'] = round(sum(s['sekunder'] for s in svar), 1)
    (U / 'seg.json').write_text(json.dumps(sam, ensure_ascii=False, indent=1), encoding='utf-8'); print('klart', len(svar), 'bilder, GPU-sekunder', sam['gpu_sekunder'])
