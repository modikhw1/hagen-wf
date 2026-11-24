"""Lager 1 på GPU (Modal): MoGe-2 ViT-L (full nivå) + OneFormer ADE20K Swin-L (panoptisk: etikett + instans).

Kör:  PYTHONUTF8=1 scen/.venv/Scripts/modal.exe run motpart/runda-4/6-lokalitet/modal_obs.py --klipp "duepiani-7650849186912406806:duepiani,..."
Ett klipp per container (parallellt, max 6), tidstak per anrop, inga nyckelfiler laddas upp (bara videobytes).
Skriver ut/<nyckel>/obs_gpu/<ruta>.npz atomiskt + ut/<nyckel>/obs_gpu.json. Lagras i halv upplösning:
djup (f16), normal (int8), mask, etikett (uint8, ADE-150), instans (int16) + segmentlista.
"""
from __future__ import annotations
import io, json, sys, time
from pathlib import Path
import modal

REV_MOGE = "74fbce054ebed49800de42d0ad0e83495065719a"
WEIGHTS_MOGE = "cb0e8bbd6b1e243589717c78e750b1ba4c093acf"
MODEL_MOGE = "Ruicheng/moge-2-vitl-normal"
SEG = "shi-labs/oneformer_ade20k_swin_large"
OBSV = "obs_gpu/2:moge2-vitl-niva9-fp16,oneformer-ade-swinL-panoptisk,geocalib-pinhole,halv"

app = modal.App("hagen-lokalitet-obs")
vol_moge = modal.Volume.from_name("rum-moge2-vikter", create_if_missing=False)
vol_hf = modal.Volume.from_name("lokalitet-hf", create_if_missing=True)
img = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11")
    .apt_install("git", "libgl1", "libglib2.0-0")
    .pip_install("torch==2.5.1", "torchvision==0.20.1", index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("numpy<2.3", "scipy", "opencv-python-headless", "pillow", "huggingface_hub>=0.25", "transformers==4.46.3", "timm", "einops")
    .run_commands(
        f"git clone https://github.com/microsoft/MoGe.git /moge && cd /moge && git checkout {REV_MOGE}",
        "pip install git+https://github.com/EasternJournalist/utils3d-moge.git@62f09d58509485564e24d5d9f6aac9ee9ebc0c37",
        "pip install 'git+https://github.com/cvg/GeoCalib#egg=geocalib'",
    )
    .env({"HF_HOME": "/hf", "TORCH_HOME": "/hf/torch", "PYTHONUNBUFFERED": "1"})
)


@app.cls(gpu=["L4", "A10G", "L40S", "A100-40GB"], image=img, volumes={"/vikter_moge": vol_moge, "/hf": vol_hf}, timeout=900, scaledown_window=60, max_containers=6)
class Obs:
    @modal.enter()
    def ladda(self):
        import torch
        sys.path.insert(0, "/moge")
        from moge.model.v2 import MoGeModel
        from transformers import OneFormerForUniversalSegmentation, OneFormerProcessor
        t = time.perf_counter()
        self.moge = MoGeModel.from_pretrained(MODEL_MOGE, revision=WEIGHTS_MOGE, cache_dir="/vikter_moge").cuda().eval()
        self.proc = OneFormerProcessor.from_pretrained(SEG)
        self.seg = OneFormerForUniversalSegmentation.from_pretrained(SEG).cuda().eval()
        from geocalib import GeoCalib
        self.geo = GeoCalib(weights="pinhole").cuda().eval()  # andra lodlinjevittne: tyngdkraft + fokal ur en bild
        vol_hf.commit()
        self.labels = {int(k): v for k, v in self.seg.config.id2label.items()}
        self.ladd_s = round(time.perf_counter() - t, 1)

    @modal.method()
    def rutor(self, video: bytes, rutor: list[int]) -> dict:
        import cv2, numpy as np, torch, tempfile
        t0 = time.perf_counter()
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(video); vp = f.name
        cap = cv2.VideoCapture(vp); want = set(rutor); frames = {}; i = 0
        while want - set(frames):
            ok, fr = cap.read()
            if not ok:
                break
            if i in want:
                frames[i] = fr
            i += 1
        out = {}; tider = []
        for u in rutor:
            t1 = time.perf_counter(); out[u] = self._obs(frames[u]); tider.append(round(time.perf_counter() - t1, 2))
        return {"rutor": out, "etiketter": self.labels, "tider": tider, "ladd_s": self.ladd_s, "sek": round(time.perf_counter() - t0, 1)}

    @modal.method()
    def bilder(self, poster: list) -> dict:
        """rumshjärna: samma observation på godtyckliga bilder (t.ex. genererade varianter), [(namn, png-bytes, (W, H))].
        Bilden skalas till (W, H) (originalets upplösning) innan läsning så att rutnätet linjerar med originalet."""
        import cv2, numpy as np
        out = {}
        for namn, data, wh in poster:
            bgr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if wh:
                bgr = cv2.resize(bgr, tuple(wh), interpolation=cv2.INTER_AREA)
            out[namn] = self._obs(bgr)
        return {"bilder": out, "etiketter": self.labels}

    def _obs(self, bgr):
        import cv2, numpy as np, torch
        if True:
            H, W = bgr.shape[:2]; rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            with torch.inference_mode():
                mo = self.moge.infer(torch.from_numpy(rgb).permute(2, 0, 1).float().cuda() / 255.0, resolution_level=9, use_fp16=True)
                inp = self.proc(images=rgb, task_inputs=["panoptic"], return_tensors="pt")
                inp = {k: (v.cuda() if hasattr(v, "cuda") else v) for k, v in inp.items()}
                so = self.seg(**inp)
                pan = self.proc.post_process_panoptic_segmentation(so, threshold=0.5, overlap_mask_area_threshold=0.8, target_sizes=[(H, W)])[0]
            h2, w2 = H // 2, W // 2
            dep = mo["depth"].float().cpu().numpy(); nor = mo["normal"].float().cpu().numpy(); msk = mo["mask"].cpu().numpy()
            dep = cv2.resize(np.nan_to_num(dep, nan=0, posinf=0), (w2, h2), interpolation=cv2.INTER_NEAREST)
            nor = cv2.resize(np.nan_to_num(nor), (w2, h2), interpolation=cv2.INTER_NEAREST)
            msk = cv2.resize(msk.astype(np.uint8), (w2, h2), interpolation=cv2.INTER_NEAREST).astype(bool) & (dep > 0)
            inst = pan["segmentation"].cpu().numpy().astype(np.int16)
            seginfo = [{"id": int(s["id"]), "etikett": int(s["label_id"]), "score": round(float(s["score"]), 3)} for s in pan["segments_info"]]
            lab = np.full(inst.shape, 255, np.uint8)
            for s in seginfo:
                lab[inst == s["id"]] = s["etikett"]
            inst2 = cv2.resize(inst, (w2, h2), interpolation=cv2.INTER_NEAREST); lab2 = cv2.resize(lab, (w2, h2), interpolation=cv2.INTER_NEAREST)
            geo = {}
            try:
                with torch.inference_mode():
                    g = self.geo.calibrate(torch.from_numpy(rgb).permute(2, 0, 1).float().cuda() / 255.0)
                vec = g["gravity"].vec3d.reshape(-1)[:3].float().cpu().numpy().tolist()
                geo = {"gravity_vec3d": vec, "roll_pitch_rad": g["gravity"].rp.reshape(-1)[:2].float().cpu().numpy().tolist(),
                       "f_px": float(g["camera"].f.reshape(-1)[0]), "bild_px": [W, H]}
                for k_, v_ in g.items():
                    if "uncertainty" in k_ and hasattr(v_, "reshape"):
                        geo[k_] = float(v_.reshape(-1)[0])
            except Exception as e:
                geo = {"fel": repr(e)[:300]}
            buf = io.BytesIO()
            np.savez_compressed(buf, depth=dep.astype(np.float16), normal=np.clip(nor * 127, -127, 127).astype(np.int8), mask=msk,
                                intrinsics=mo["intrinsics"].float().cpu().numpy(), labels=lab2, instans=inst2,
                                segment=np.frombuffer(json.dumps(seginfo).encode(), np.uint8), geocalib=np.frombuffer(json.dumps(geo).encode(), np.uint8), nyckel=np.array(OBSV))
            return buf.getvalue()


@app.local_entrypoint()
def main(klipp: str):
    import hashlib
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from observera import las_rutor, tagningar_for, KLIPP  # samma tagningsregel som CPU-vägen
    here = Path(__file__).resolve().parent; jobb = []; t0 = time.perf_counter()
    for spec in klipp.split(","):
        namn, nyckel = spec.split(":")
        video = KLIPP / (namn + ".mp4"); frames, fps = las_rutor(video); H, W = frames[0].shape[:2]
        shots, kalla = tagningar_for(nyckel, frames)
        for s in shots:  # tre nyckelrutor per tagning för alla klipp (kvalitet)
            a0, b0 = s["ut"]; n = b0 - a0
            s["nyckelrutor"] = sorted({a0 + min(2, n - 1), a0 + n // 2, b0 - 1 - min(2, n - 1)})
        rutor = sorted({u for s in shots for u in s["nyckelrutor"]})
        data = video.read_bytes()
        jobb.append((namn, nyckel, shots, kalla, rutor, fps, W, H, hashlib.sha256(data).hexdigest(), Obs().rutor.spawn(data, rutor)))
        print(f"skickat {nyckel}: {len(rutor)} rutor", flush=True)
    for namn, nyckel, shots, kalla, rutor, fps, W, H, src, fc in jobb:
        r = fc.get(timeout=900)
        out = here / "ut" / nyckel / "obs_gpu"; out.mkdir(parents=True, exist_ok=True)
        for u, b in r["rutor"].items():
            tmp = out / f"{int(u):04d}.tmp"; tmp.write_bytes(b); tmp.replace(out / f"{int(u):04d}.npz")
        meta = {"klipp": namn, "nyckel": nyckel, "kalla_sha256": src, "fps": fps, "bild_px": [W, H], "lagrad_px": [W // 2, H // 2],
                "antal_rutor": None, "tagningar": shots, "tagningskalla": kalla, "modeller": {"djup": MODEL_MOGE, "etiketter": SEG}, "obsv": OBSV,
                "etiketter": r["etiketter"], "sek_per_ruta": r["tider"], "ladd_s": r["ladd_s"], "sek_gpu_anrop": r["sek"]}
        cap_n = len(las_rutor(KLIPP / (namn + ".mp4"))[0]); meta["antal_rutor"] = cap_n
        tmp = here / "ut" / nyckel / "obs_gpu.json.tmp"; tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(here / "ut" / nyckel / "obs_gpu.json")
        print(f"klar {nyckel}: {len(r['rutor'])} rutor, laddning {r['ladd_s']} s, anrop {r['sek']} s, median {sorted(r['tider'])[len(r['tider'])//2]} s/ruta", flush=True)
    print(f"totalt {round(time.perf_counter() - t0, 1)} s väggtid", flush=True)


@app.local_entrypoint()
def bildobs(katalog: str, bredd: int = 540, hojd: int = 960):
    """Kör observationen på alla *_v*.png i katalogen (utom .codex.json), skriver <namn>.obs.npz bredvid."""
    d = Path(katalog); poster = [(p.stem, p.read_bytes(), (bredd, hojd)) for p in sorted(d.glob('*_v*.png'))]
    r = Obs().bilder.remote(poster)
    for namn, b in r["bilder"].items():
        tmp = d / f"{namn}.obs.tmp"; tmp.write_bytes(b); tmp.replace(d / f"{namn}.obs.npz")
    (d / "etiketter.json").write_text(json.dumps(r["etiketter"], ensure_ascii=False), encoding="utf-8")
    print(f"klar {len(r['bilder'])} bilder", flush=True)
