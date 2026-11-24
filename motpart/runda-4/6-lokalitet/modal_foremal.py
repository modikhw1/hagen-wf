"""föremål/1: öppen vokabulär för mat och kärl (Grounding DINO base + SAM 2.1 hiera-large, båda Apache-2.0) på Modal.

Varför: blinda prov 1–3 (21 nov) visar att struktur vinner rummet men föremålen är kvar; OneFormer ADE20K slår ihop
mat/kärl med bord/vägg/person. Här: textprompter -> boxar -> masker, i mittrutan per tagning (samma ruta som struktur_in).
Utdata: ut/<k>/foremal/<sid>.npz (masker i halv upplösning, etiketter, poäng, boxar) + foremal.json.
usage: modal run modal_foremal.py::main --klipp nyckel1,nyckel2
"""
from __future__ import annotations
import io, json, sys, time
from pathlib import Path
import modal

app = modal.App("hagen-lokalitet-foremal")
vol_hf = modal.Volume.from_name("lokalitet-hf", create_if_missing=True)
img = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11")
    .apt_install("libgl1", "libglib2.0-0")
    .pip_install("torch==2.8.0", "torchvision==0.23.0", index_url="https://download.pytorch.org/whl/cu128")
    .pip_install("numpy<2.3", "opencv-python-headless", "pillow", "huggingface_hub>=0.25", "transformers==4.57.1", "accelerate")
    .env({"HF_HOME": "/hf"})
)
PROMPT = "plate. bowl. cup. glass. bottle. can. pan. pot. tray. food. burger. fries. pizza. pasta. sandwich. box. sauce. basket. menu."
DINO, SAM = "IDEA-Research/grounding-dino-base", "facebook/sam2.1-hiera-large"


@app.cls(gpu=["L4", "A10G", "L40S", "A100-40GB"], image=img, volumes={"/hf": vol_hf}, timeout=900, scaledown_window=60, max_containers=6)
class Foremal:
    @modal.enter()
    def ladda(self):
        import torch
        from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection, Sam2Processor, Sam2Model
        t0 = time.perf_counter()
        self.dp = AutoProcessor.from_pretrained(DINO); self.dm = AutoModelForZeroShotObjectDetection.from_pretrained(DINO).cuda().eval()
        self.sp = Sam2Processor.from_pretrained(SAM); self.sm = Sam2Model.from_pretrained(SAM).cuda().eval()
        self.ladd_s = round(time.perf_counter() - t0, 1); vol_hf.commit()

    @modal.method()
    def bilder(self, poster: list) -> dict:
        import cv2, numpy as np, torch
        from PIL import Image
        ut = {}
        for namn, data, (w2, h2) in poster:
            bgr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR); H, W = bgr.shape[:2]
            pil = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            with torch.inference_mode():
                inp = self.dp(images=pil, text=PROMPT, return_tensors="pt").to("cuda")
                o = self.dm(**inp)
                try:
                    r = self.dp.post_process_grounded_object_detection(o, inp.input_ids, threshold=0.30, text_threshold=0.25, target_sizes=[(H, W)])[0]
                except TypeError:
                    r = self.dp.post_process_grounded_object_detection(o, inp.input_ids, box_threshold=0.30, text_threshold=0.25, target_sizes=[(H, W)])[0]
                boxar = r["boxes"].cpu().numpy(); poang = r["scores"].cpu().numpy()
                etik = r.get("text_labels", r.get("labels"))
                etik = [str(e) for e in etik]
                # bort med boxar som täcker nästan hela bilden (scenen, inte ett föremål)
                hall = [i for i, b in enumerate(boxar) if (b[2] - b[0]) * (b[3] - b[1]) < 0.6 * W * H]
                boxar, poang, etik = boxar[hall], poang[hall], [etik[i] for i in hall]
                masker = np.zeros((0, h2, w2), bool)
                if len(boxar):
                    si = self.sp(images=pil, input_boxes=[[b.tolist() for b in boxar]], return_tensors="pt").to("cuda")
                    so = self.sm(**si, multimask_output=False)
                    mm = self.sp.post_process_masks(so.pred_masks.cpu(), si["original_sizes"])[0][:, 0].numpy() > 0.5
                    masker = np.stack([cv2.resize(m.astype(np.uint8), (w2, h2), interpolation=cv2.INTER_NEAREST).astype(bool) for m in mm])
            buf = io.BytesIO()
            np.savez_compressed(buf, masker=np.packbits(masker, axis=-1), form=np.array(masker.shape), boxar=boxar.astype(np.float32),
                                poang=poang.astype(np.float32), etiketter=json.dumps(etik))
            ut[namn] = buf.getvalue()
        return {"bilder": ut, "ladd_s": self.ladd_s, "modeller": {"detektor": DINO, "mask": SAM, "prompt": PROMPT}}


@app.local_entrypoint()
def main(klipp: str):
    import cv2, numpy as np
    here = Path(__file__).resolve().parent; root = here.parents[2]; jobb = []; t0 = time.perf_counter()
    for k in klipp.split(","):
        meta = json.loads((here / "ut" / k / "obs_gpu.json").read_text(encoding="utf-8")); W0, H0 = meta["bild_px"]
        cap = cv2.VideoCapture(str(root / "data/format/kontroll/klipp" / (meta["klipp"] + ".mp4"))); poster = []
        for t in meta["tagningar"]:
            u = t["nyckelrutor"][len(t["nyckelrutor"]) // 2]; cap.set(cv2.CAP_PROP_POS_FRAMES, u); ok, fr = cap.read()
            if ok:
                poster.append((t["id"], cv2.imencode(".png", fr)[1].tobytes(), (W0 // 2, H0 // 2)))
        cap.release(); jobb.append((k, Foremal().bilder.spawn(poster)))
    for k, fc in jobb:
        r = fc.get(timeout=900); d = here / "ut" / k / "foremal"; d.mkdir(parents=True, exist_ok=True); n = 0
        for sid, b in r["bilder"].items():
            tmp = d / f"{sid}.tmp"; tmp.write_bytes(b); tmp.replace(d / f"{sid}.npz"); n += 1
        (d / "foremal.json").write_text(json.dumps({"modeller": r["modeller"], "ladd_s": r["ladd_s"]}, ensure_ascii=False), encoding="utf-8")
        print(f"klar {k}: {n} tagningar", flush=True)
    print(f"totalt {round(time.perf_counter() - t0, 1)} s", flush=True)
