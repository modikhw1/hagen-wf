"""föremål/2: SAM 3.1 (öppen vokabulär, text -> instansmasker) på Modal, samma utdataformat som modal_foremal.py.

Ägaren 21 nov: "kör sam 3.1". Vikterna är gated (manuellt godkännande hos Meta, SAM License). Kodväg: transformers
Sam3Model/Sam3Processor; försöker facebook/sam3.1 först, sedan facebook/sam3 (och skriver vilken som användes).
Utdata: ut/<k>/foremal_sam3/<sid>.npz (masker i halv upplösning, etiketter, poäng, boxar) + foremal.json.
usage: modal run modal_sam3.py::main --klipp nyckel1,nyckel2     |  modal run modal_sam3.py::atkomst
"""
from __future__ import annotations
import io, json, os, time
from pathlib import Path
import modal

app = modal.App("hagen-lokalitet-sam3")
vol_hf = modal.Volume.from_name("lokalitet-hf", create_if_missing=True)
img = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11")
    .apt_install("libgl1", "libglib2.0-0")
    .pip_install("torch==2.8.0", "torchvision==0.23.0", index_url="https://download.pytorch.org/whl/cu128")
    .pip_install("numpy<2.3", "opencv-python-headless", "pillow", "huggingface_hub>=0.30", "transformers==5.24.0", "accelerate")
    .env({"HF_HOME": "/hf"})
)
BEGREPP = ["plate", "bowl", "cup", "drinking glass", "bottle", "can", "pan", "pot", "tray", "food", "burger", "french fries", "pizza",
           "pasta", "sandwich", "box", "sauce", "basket", "menu", "chair", "table", "counter", "stool", "bench"]
REPON = ("facebook/sam3.1", "facebook/sam3")


def _token():
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")


@app.function(image=modal.Image.debian_slim(python_version="3.11").pip_install("huggingface_hub>=0.30"),
              secrets=[modal.Secret.from_name("huggingface")], timeout=120)
def har_atkomst() -> dict:
    from huggingface_hub import HfApi
    api = HfApi(token=_token()); ut = {}
    for rid in REPON:
        try:
            api.hf_hub_download(rid, "config.json", cache_dir="/tmp/hfprov"); ut[rid] = True
        except Exception as e:  # noqa: BLE001
            ut[rid] = str(e)[:80]
    return ut


@app.cls(gpu=["L40S", "A100-40GB", "A10G", "L4"], image=img, volumes={"/hf": vol_hf}, secrets=[modal.Secret.from_name("huggingface")],
         timeout=1200, scaledown_window=60, max_containers=4)
class Sam3:
    @modal.enter()
    def ladda(self):
        import torch
        from transformers import Sam3Model, Sam3Processor
        t0 = time.perf_counter(); self.repo = None; fel = {}
        for rid in REPON:
            try:
                self.proc = Sam3Processor.from_pretrained(rid, token=_token())
                self.model = Sam3Model.from_pretrained(rid, token=_token(), torch_dtype=torch.bfloat16).cuda().eval()
                self.repo = rid; break
            except Exception as e:  # noqa: BLE001
                fel[rid] = str(e)[:300]
        self.fel = fel; self.ladd_s = round(time.perf_counter() - t0, 1); vol_hf.commit()

    @modal.method()
    def bilder(self, poster: list) -> dict:
        import cv2, numpy as np, torch
        from PIL import Image
        if self.repo is None:
            return {"fel": self.fel}
        ut = {}
        for namn, data, (w2, h2) in poster:
            bgr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR); H, W = bgr.shape[:2]
            pil = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)); masker, boxar, poang, etik = [], [], [], []
            for i in range(0, len(BEGREPP), 6):
                del_ = BEGREPP[i:i + 6]
                with torch.inference_mode():
                    inp = self.proc(images=[pil] * len(del_), text=del_, return_tensors="pt").to("cuda")
                    inp = {k: (v.to(torch.bfloat16) if hasattr(v, "dtype") and v.dtype == torch.float32 else v) for k, v in inp.items()}
                    o = self.model(**inp)
                    res = self.proc.post_process_instance_segmentation(o, threshold=0.4, mask_threshold=0.5, target_sizes=[(H, W)] * len(del_))
                for begrepp, r in zip(del_, res):
                    for m, b, s in zip(r["masks"], r["boxes"], r["scores"]):
                        m = m.float().cpu().numpy() > 0.5
                        if m.mean() > 0.6:  # hela scenen, inte ett föremål
                            continue
                        masker.append(cv2.resize(m.astype(np.uint8), (w2, h2), interpolation=cv2.INTER_NEAREST).astype(bool))
                        boxar.append(b.float().cpu().numpy()); poang.append(float(s)); etik.append(begrepp)
            M = np.stack(masker) if masker else np.zeros((0, h2, w2), bool); buf = io.BytesIO()
            np.savez_compressed(buf, masker=np.packbits(M, axis=-1), form=np.array(M.shape), boxar=np.array(boxar, np.float32).reshape(-1, 4),
                                poang=np.array(poang, np.float32), etiketter=json.dumps(etik))
            ut[namn] = buf.getvalue()
        return {"bilder": ut, "ladd_s": self.ladd_s, "modeller": {"mask": self.repo, "begrepp": BEGREPP, "trosklar": {"objekt": 0.4, "mask": 0.5}}}


@app.local_entrypoint()
def atkomst():
    print(json.dumps(har_atkomst.remote(), ensure_ascii=False))


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
        cap.release(); jobb.append((k, Sam3().bilder.spawn(poster)))
    for k, fc in jobb:
        r = fc.get(timeout=1200)
        if "fel" in r:
            raise SystemExit(f"SAM 3 kunde inte laddas: {r['fel']}")
        d = here / "ut" / k / "foremal_sam3"; d.mkdir(parents=True, exist_ok=True)
        for sid, b in r["bilder"].items():
            tmp = d / f"{sid}.tmp"; tmp.write_bytes(b); tmp.replace(d / f"{sid}.npz")
        (d / "foremal.json").write_text(json.dumps({"modeller": r["modeller"], "ladd_s": r["ladd_s"]}, ensure_ascii=False), encoding="utf-8")
        print(f"klar {k}: {len(r['bilder'])} tagningar, modell {r['modeller']['mask']}", flush=True)
    print(f"totalt {round(time.perf_counter() - t0, 1)} s", flush=True)
