"""Arbetsbord Ingest v2: Snabb singel-GPU Modal-ingest (L4, 0 Blender, < 5 MB/klipp).

Kör hela ingestkedjan i en varm L4-container per klipp:
  1. ffprobe + scenklippdetektering (tröskel 0.3, samma som hagen-ui) + 576p H.264 webbproxy
  2. CUDA Demucs (htdemucs i minne -> tal.wav + musiknivå) + faster-whisper (ordtider) + OCR (nyckelrutor)
  3. CUDA YOLO11n-seg (10 fps tracking av personer/mat/bord + klipp-ReID + tagningsklassning)
  4. Bakgrundshomografi per tagning (upptäcker rörlig kamera i mat- & detaljtagningar)
  5. CUDA MoGe-2 (1 nyckelruta per tagning -> golvnormal, bordsplan, fokal, R_cam)
  6. CUDA SAM 3D Body (3 fps + kanter + PCHIP-interpolation med benlängdsprojektion -> T1 + tilltro)
  7. Komprimerat paket (< 5 MB/klipp): paket.json (scenpaket/2), tidslinje.json (medielager/1),
     tal.wav, proxy_h264.mp4 och ingest_rapport.json.

Körning (sekventiellt över 2 riktiga mat+tal-klipp för ärlig kall- vs varmtid):
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\modal.exe run arbetsbord/ingest_v2/modal_ingest_v2.py
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from typing import Any

import modal

HIT = pathlib.Path(__file__).resolve().parent
IS_LOCAL = len(HIT.parents) > 1 and (HIT.parents[1] / "forvarld").exists()
ROT = HIT.parents[1] if IS_LOCAL else HIT
UT_BASE = ROT / "arbetsbord" / "data" / "ingest_v2"

REV_MOGE = "74fbce054ebed49800de42d0ad0e83495065719a"
WEIGHTS_MOGE = "cb0e8bbd6b1e243589717c78e750b1ba4c093acf"
MODEL_MOGE = "Ruicheng/moge-2-vitl-normal"

# Modal L4 listpris ($0.80 / h)
L4_USD_PER_S = 0.80 / 3600.0

app = modal.App("hagen-ingest-v2")
vol_moge = modal.Volume.from_name("rum-moge2-vikter", create_if_missing=True)
vol_sam = modal.Volume.from_name("sam3db-vikter", create_if_missing=True)
vol_v2 = modal.Volume.from_name("hagen-ingest-v2-cache", create_if_missing=True)

img = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11")
    .apt_install("git", "ffmpeg", "libgl1", "libglib2.0-0", "libsndfile1")
    .pip_install(
        "torch==2.5.1",
        "torchvision==0.20.1",
        "torchaudio==2.5.1",
        index_url="https://download.pytorch.org/whl/cu124",
    )
    .pip_install(
        "numpy<2.3",
        "scipy",
        "opencv-python-headless",
        "pillow",
        "huggingface_hub>=0.25",
        "einops",
        "timm",
        "pytorch-lightning",
        "yacs",
        "scikit-image",
        "dill",
        "pandas",
        "rich",
        "hydra-core",
        "pyrootutils",
        "roma",
        "joblib",
        "loguru",
        "optree",
        "fvcore",
        "jsonlines",
        "networkx==3.2.1",
        "braceexpand",
        "webdataset",
        "ultralytics",
        "demucs",
        "faster-whisper",
        "rapidocr-onnxruntime",
        "soundfile",
    )
    .run_commands(
        f"git clone https://github.com/microsoft/MoGe.git /moge && cd /moge && git checkout {REV_MOGE}",
        "pip install git+https://github.com/EasternJournalist/utils3d-moge.git@62f09d58509485564e24d5d9f6aac9ee9ebc0c37",
        "git clone --depth 1 https://github.com/facebookresearch/sam-3d-body.git /kod",
    )
    .env(
        {
            "HF_HOME": "/vol_v2/hf",
            "TORCH_HOME": "/vol_v2/torch",
            "YOLO_CONFIG_DIR": "/tmp/ultralytics",
            "PYTHONUNBUFFERED": "1",
        }
    )
)

if IS_LOCAL:
    img = (
        img.add_local_file(str(ROT / "scen" / "py" / "modeller" / "yolo11n-seg.pt"), "/root/yolo11n-seg.pt")
        .add_local_file(str(ROT / "scen" / "3d" / "kontrakt" / "tro_rigg.json"), "/root/tro_rigg.json")
    )

LEDER_T1 = [
    "c_spine0", "c_spine1", "c_spine2", "c_spine3", "c_neck", "c_head", "huvud_upp", "nasa_mal",
    "l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
    "r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1",
    "l_upleg", "l_lowleg", "l_foot", "l_ball", "r_upleg", "r_lowleg", "r_foot", "r_ball",
]
T1_IX = {n: i for i, n in enumerate(LEDER_T1)}
FOTLED_OVER_GOLV = 0.065
ROLL_FARG = {"A": "#4c8bf5", "B": "#e06c75", "C": "#98c379"}
# COCO mat-/bords-klasser
FOOD_COCO_IDS = {39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55}
BOWL_COCO_IDS = {41, 45}
TABLE_COCO_IDS = {60}

# Fasta källträds-kanter för att projicera bort kordaförkortning efter PCHIP
T1_KANTER = [
    ("c_spine0", "c_spine1"), ("c_spine1", "c_spine2"), ("c_spine2", "c_spine3"),
    ("c_spine3", "c_neck"), ("c_neck", "c_head"),
    ("c_spine3", "l_clavicle"), ("l_clavicle", "l_uparm"), ("l_uparm", "l_lowarm"),
    ("l_lowarm", "l_wrist"), ("l_wrist", "l_hand_mitt"), ("l_hand_mitt", "l_index1"),
    ("c_spine3", "r_clavicle"), ("r_clavicle", "r_uparm"), ("r_uparm", "r_lowarm"),
    ("r_lowarm", "r_wrist"), ("r_wrist", "r_hand_mitt"), ("r_hand_mitt", "r_index1"),
    ("c_spine0", "l_upleg"), ("l_upleg", "l_lowleg"), ("l_lowleg", "l_foot"), ("l_foot", "l_ball"),
    ("c_spine0", "r_upleg"), ("r_upleg", "r_lowleg"), ("r_lowleg", "r_foot"), ("r_foot", "r_ball"),
]


@app.cls(
    image=img,
    gpu="L4",
    volumes={"/vikter_moge": vol_moge, "/vikter_sam": vol_sam, "/vol_v2": vol_v2},
    secrets=[modal.Secret.from_name("huggingface")],
    timeout=1800,
    scaledown_window=180,
)
class IngestV2Worker:
    @modal.enter()
    def ladda(self):
        import json as _json
        import os
        import sys
        import torch

        t0 = time.perf_counter()
        self.gpu = torch.cuda.get_device_name(0)

        # 1. MHR ledindex
        rigg = _json.loads(open("/root/tro_rigg.json", encoding="utf-8").read())
        self.mhr_ix = {n: i for i, n in enumerate(rigg["namn"])}

        # 2. YOLO11n-seg
        from ultralytics import YOLO
        self.yolo = YOLO("/root/yolo11n-seg.pt")

        # 3. MoGe-2
        sys.path.insert(0, "/moge")
        from moge.model.v2 import MoGeModel
        self.moge = MoGeModel.from_pretrained(
            MODEL_MOGE, revision=WEIGHTS_MOGE, cache_dir="/vikter_moge"
        ).cuda().eval()

        # 4. SAM 3D Body (ViT-H)
        sys.path.insert(0, "/kod")
        from huggingface_hub import snapshot_download
        sam_dir = snapshot_download(
            "facebook/sam-3d-body-vith", local_dir="/vikter_sam/vith", token=os.environ.get("HF_TOKEN")
        )
        from sam_3d_body import load_sam_3d_body, SAM3DBodyEstimator
        sam_m, sam_cfg = load_sam_3d_body(
            f"{sam_dir}/model.ckpt", device=torch.device("cuda"), mhr_path=f"{sam_dir}/assets/mhr_model.pt"
        )
        self.sam3d = SAM3DBodyEstimator(sam_3d_body_model=sam_m, model_cfg=sam_cfg)

        # 5. Demucs (htdemucs i GPU-minnet)
        from demucs.pretrained import get_model
        self.demucs = get_model("htdemucs").cuda().eval()
        self.vocals_idx = self.demucs.sources.index("vocals")

        # 6. Whisper (faster-whisper small på CUDA -> fallback CPU int8 om lib saknas)
        from faster_whisper import WhisperModel
        try:
            self.whisper = WhisperModel("small", device="cuda", compute_type="float16", download_root="/vol_v2/whisper")
            self.whisper_dev = "cuda"
        except Exception:
            self.whisper = WhisperModel("small", device="cpu", compute_type="int8", download_root="/vol_v2/whisper")
            self.whisper_dev = "cpu"

        # 7. RapidOCR
        from rapidocr_onnxruntime import RapidOCR
        self.ocr = RapidOCR()

        vol_moge.commit()
        vol_sam.commit()
        vol_v2.commit()
        self.load_s = round(time.perf_counter() - t0, 2)

    @modal.method()
    def ingest_klipp(self, video_bytes: bytes, klipp_id: str, nyckel: str) -> dict[str, Any]:
        import concurrent.futures
        import subprocess
        import tempfile
        import wave
        import cv2
        import numpy as np
        import soundfile as sf
        import torch
        import torchaudio
        from scipy.interpolate import PchipInterpolator

        t_tot0 = time.perf_counter()
        tider: dict[str, float] = {}
        F = np.diag([1.0, -1.0, -1.0])

        with tempfile.TemporaryDirectory() as td:
            td_p = pathlib.Path(td)
            src_mp4 = td_p / f"{nyckel}_src.mp4"
            src_mp4.write_bytes(video_bytes)
            proxy_mp4 = td_p / f"{nyckel}_proxy.mp4"
            tal_wav = td_p / f"{nyckel}_tal.wav"
            mix_wav = td_p / f"{nyckel}_mix.wav"

            # --- 1. ffprobe + scenklipp + H.264 proxy + ljudavkodning ---
            t0 = time.perf_counter()
            pr = json.loads(
                subprocess.check_output(
                    [
                        "ffprobe", "-v", "error",
                        "-show_entries", "stream=codec_type,width,height,r_frame_rate,sample_rate:format=duration",
                        "-of", "json", str(src_mp4),
                    ],
                    text=True,
                )
            )
            v_st = next(s for s in pr["streams"] if s.get("codec_type") == "video")
            a_st = next((s for s in pr["streams"] if s.get("codec_type") == "audio"), None)
            num, den = (v_st.get("r_frame_rate") or "30/1").split("/")
            fps_src = float(num) / float(den or 1)
            fps = 30.0 if abs(fps_src - 30.0) < 0.05 else round(fps_src, 3)
            W_orig, H_orig = int(v_st["width"]), int(v_st["height"])
            dur_s = float(pr["format"]["duration"])

            # Kör ffmpeg scenklippdetektering (tröskel 0.3), H.264-proxy och WAV parallellt!
            def _run_cuts():
                cmd = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "info", "-i", str(src_mp4),
                    "-vf", "select='gt(scene,0.3)',showinfo", "-f", "null", "-",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                pts = [0.0]
                for ln in res.stderr.splitlines():
                    if "pts_time:" in ln:
                        try:
                            val = float(ln.split("pts_time:")[1].split()[0])
                            if val - pts[-1] >= 0.38 and dur_s - val >= 0.35:
                                pts.append(val)
                        except Exception:
                            pass
                pts.append(dur_s)
                # Slå ihop korta skarvklipp < 0.35 s
                clean = [pts[0]]
                for p in pts[1:]:
                    if p - clean[-1] >= 0.35 or p == dur_s:
                        clean.append(p)
                if len(clean) < 2:
                    clean = [0.0, dur_s]
                return clean

            def _run_proxy():
                cmd = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src_mp4),
                    "-vf", "scale=576:-2",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "27", "-pix_fmt", "yuv420p", "-g", "15",
                    "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(proxy_mp4),
                ]
                subprocess.run(cmd, check=True)

            def _run_audio_extract():
                if a_st is None:
                    return False
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src_mp4),
                        "-vn", "-ac", "2", "-ar", str(self.demucs.samplerate), "-f", "wav", str(mix_wav),
                    ],
                    check=True,
                )
                return True

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                f_cuts = ex.submit(_run_cuts)
                f_proxy = ex.submit(_run_proxy)
                f_aud = ex.submit(_run_audio_extract)
                cut_times = f_cuts.result()
                f_proxy.result()
                has_audio = f_aud.result()

            # Läs in proxy/originalrutor till minnet i ~576x1024 för snabb GPU-analys
            cap = cv2.VideoCapture(str(proxy_mp4))
            frames_bgr = []
            while True:
                ok, fr = cap.read()
                if not ok:
                    break
                frames_bgr.append(fr)
            cap.release()
            n_frames = max(1, len(frames_bgr))
            Hp, Wp = frames_bgr[0].shape[:2]
            tider["ffmpeg_proxy_och_klipp"] = round(time.perf_counter() - t0, 2)

            # --- 2. CUDA Demucs + Whisper ---
            t0 = time.perf_counter()
            tal_segment = []
            musik_meta = {"finns": False, "borttagen": False, "skal": "saknar ljud"}
            if has_audio and mix_wav.exists():
                from demucs.apply import apply_model
                data_np, sr_dem = sf.read(str(mix_wav), dtype="float32")
                if data_np.ndim == 1:
                    data_np = np.stack([data_np, data_np], axis=1)
                wav_t = torch.from_numpy(data_np.T).cuda()  # (2, L)
                ref = wav_t.mean(0)
                wav_n = (wav_t - ref.mean()) / (ref.std() + 1e-8)
                with torch.inference_mode():
                    stems = apply_model(self.demucs, wav_n[None], shifts=0, split=True, overlap=0.25, progress=False)[0]
                    stems = stems * ref.std() + ref.mean()
                voc_t = stems[self.vocals_idx].mean(dim=0, keepdim=True)  # mono
                mus_t = (stems.sum(dim=0) - stems[self.vocals_idx]).mean(dim=0, keepdim=True)
                # Beräkna enkel 0.5 s musikenergi-andel
                blk = int(0.5 * sr_dem)
                n_blk = max(1, mus_t.shape[1] // blk)
                m_rms = mus_t[0, : n_blk * blk].view(n_blk, blk).pow(2).mean(dim=1).sqrt()
                mix_peak = float(wav_t.abs().max().item()) + 1e-8
                mus_frac = float(((20.0 * torch.log10(m_rms / mix_peak + 1e-8)) > -35.0).float().mean().item())
                musik_meta = {"finns": bool(mus_frac >= 0.2), "borttagen": False, "andel_musik": round(mus_frac, 3)}

                # Sampla ner voc till 16 kHz mono PCM16 -> tal.wav
                voc_16k = torchaudio.functional.resample(voc_t.cpu(), sr_dem, 16000)[0].numpy()
                voc_i16 = np.clip(voc_16k * 32767.0, -32768, 32767).astype(np.int16)
                with wave.open(str(tal_wav), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(voc_i16.tobytes())

                # faster-whisper på talspåret
                segs, _info = self.whisper.transcribe(
                    str(tal_wav), language="sv", word_timestamps=True, vad_filter=True, beam_size=1
                )
                for idx_s, s in enumerate(segs, 1):
                    ord_ut = []
                    for w_item in (s.words or []):
                        ord_ut.append({
                            "o": w_item.word.strip(),
                            "fran_s": round(float(w_item.start), 2),
                            "till_s": round(float(w_item.end), 2),
                        })
                    tal_segment.append({
                        "id": f"tal_{idx_s}",
                        "talare": "A",
                        "text": s.text.strip(),
                        "fran_s": round(float(s.start), 3),
                        "till_s": round(float(s.end), 3),
                        "ord": ord_ut,
                    })
            tider["demucs_och_whisper"] = round(time.perf_counter() - t0, 2)

            # Bygg tagningsgränser i bildrutor
            shot_defs = []
            for s_idx in range(len(cut_times) - 1):
                t_a, t_b = cut_times[s_idx], cut_times[s_idx + 1]
                f_a = max(0, min(n_frames - 1, int(round(t_a * fps))))
                f_b = max(f_a + 1, min(n_frames, int(round(t_b * fps))))
                if s_idx == len(cut_times) - 2:
                    f_b = n_frames
                if f_b > f_a:
                    shot_defs.append({"id": f"s{s_idx + 1}", "tid_id": f"t{s_idx + 1}", "fran_s": round(t_a, 3), "till_s": round(t_b, 3), "ut": [f_a, f_b]})

            # --- 3. OCR (2 nyckelrutor per tagning) & YOLO11-seg (~10 fps) ---
            t0 = time.perf_counter()
            skarmtext = []
            seen_ocr = {}
            step_yolo = max(1, int(round(fps / 10.0)))
            yolo_indices = sorted({min(n_frames - 1, f) for s in shot_defs for f in list(range(s["ut"][0], s["ut"][1], step_yolo)) + [s["ut"][0], (s["ut"][0] + s["ut"][1]) // 2, s["ut"][1] - 1]})

            yolo_per_frame: dict[int, dict[str, Any]] = {}
            for b0 in range(0, len(yolo_indices), 16):
                batch_ix = yolo_indices[b0 : b0 + 16]
                imgs = [frames_bgr[fi] for fi in batch_ix]
                preds = self.yolo.predict(imgs, verbose=False, conf=0.28, imgsz=640)
                for fi, res in zip(batch_ix, preds):
                    p_list = []
                    f_list = []
                    t_list = []
                    has_masks = res.masks is not None and len(res.masks.data) > 0
                    for bi in range(len(res.boxes)):
                        cls_id = int(res.boxes.cls[bi].item())
                        conf = float(res.boxes.conf[bi].item())
                        xyxy = [float(v) for v in res.boxes.xyxy[bi].tolist()]
                        area_fr = ((xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1])) / max(1.0, Wp * Hp)
                        mask_bin = None
                        if has_masks and bi < len(res.masks.data):
                            m_raw = res.masks.data[bi].cpu().numpy()
                            mask_bin = cv2.resize(m_raw.astype(np.float32), (Wp, Hp), interpolation=cv2.INTER_NEAREST) > 0.5
                        if cls_id == 0 and area_fr > 0.018:
                            p_list.append({"box": xyxy, "conf": conf, "area": area_fr, "mask": mask_bin})
                        elif cls_id in FOOD_COCO_IDS:
                            f_list.append({"cls": cls_id, "box": xyxy, "conf": conf, "area": area_fr})
                        elif cls_id in TABLE_COCO_IDS:
                            t_list.append({"box": xyxy, "conf": conf, "area": area_fr})
                    yolo_per_frame[fi] = {"personer": p_list, "mat": f_list, "bord": t_list}

            # OCR på start + mitt av varje tagning
            ocr_idx = 0
            for sh in shot_defs:
                a0, b0 = sh["ut"]
                pts = sorted({a0, (a0 + b0) // 2})
                for fi in pts:
                    res_ocr, _ = self.ocr(frames_bgr[fi])
                    if not res_ocr:
                        continue
                    for box_pts, txt, conf in res_ocr:
                        clean = str(txt or "").strip()
                        if len(clean) < 2 or float(conf) < 0.5:
                            continue
                        xs = [pt[0] / Wp for pt in box_pts]
                        ys = [pt[1] / Hp for pt in box_pts]
                        key_ocr = clean.lower()[:28]
                        if key_ocr in seen_ocr and sh["fran_s"] - seen_ocr[key_ocr]["till_s"] <= 1.2:
                            seen_ocr[key_ocr]["till_s"] = round(sh["till_s"], 3)
                        else:
                            ocr_idx += 1
                            entry = {
                                "id": f"x{ocr_idx}",
                                "text": clean,
                                "fran_s": round(sh["fran_s"], 3),
                                "till_s": round(sh["till_s"], 3),
                                "box": [round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)],
                                "typ": "overlag",
                                "stil": {"glyffarg": "#f6f5f5", "kontur": "#000000", "platta": False, "radhojd": round(max(0.028, max(ys) - min(ys)), 4)},
                            }
                            skarmtext.append(entry)
                            seen_ocr[key_ocr] = entry
            tider["yolo_och_ocr"] = round(time.perf_counter() - t0, 2)

            # --- 4. Spårning, Tagningsklassning, Homografi & MoGe-2 (1 nyckelruta/tagning) ---
            t0 = time.perf_counter()
            person_tracks: dict[str, dict[str, Any]] = {}  # pid -> {hist, tagningar: ...}
            global_tracks: list[dict[str, Any]] = []  # [{'pid': 'A', 'hist': ...}]

            def _torso_hist(img_bgr, box):
                x0, y0, x1, y1 = [int(v) for v in box]
                x0, x1 = max(0, x0), min(Wp, x1)
                y0_t = max(0, int(y0 + 0.15 * (y1 - y0)))
                y1_t = min(Hp, int(y0 + 0.60 * (y1 - y0)))
                crop = img_bgr[y0_t:y1_t, x0:x1]
                if crop.size < 20:
                    return np.ones(16, dtype=np.float32) / 16.0
                hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                hist = cv2.calcHist([hsv], [0, 1], None, [8, 2], [0, 180, 0, 256]).ravel()
                return hist / (np.linalg.norm(hist) + 1e-8)

            shot_info_list = []
            orb = cv2.ORB_create(350)
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

            for sh in shot_defs:
                sid = sh["id"]
                a0, b0 = sh["ut"]
                mid_f = (a0 + b0) // 2
                # Bakgrundshomografi mellan första och sista tredje-delen i tagningen
                f_h0 = a0
                f_h1 = min(b0 - 1, max(a0 + 1, b0 - 2))
                bg_shift_px = 0.0
                pan_flow_xy = [0.0, 0.0]
                if f_h1 > f_h0:
                    g0 = cv2.cvtColor(frames_bgr[f_h0], cv2.COLOR_BGR2GRAY)
                    g1 = cv2.cvtColor(frames_bgr[f_h1], cv2.COLOR_BGR2GRAY)
                    mask0 = np.full((Hp, Wp), 255, dtype=np.uint8)
                    for pd_item in (yolo_per_frame.get(f_h0, {})).get("personer", []):
                        bx = [int(v) for v in pd_item["box"]]
                        mask0[max(0, bx[1]):min(Hp, bx[3]), max(0, bx[0]):min(Wp, bx[2])] = 0
                    kp0, d0 = orb.detectAndCompute(g0, mask0)
                    kp1, d1 = orb.detectAndCompute(g1, mask0)
                    if d0 is not None and d1 is not None and len(kp0) >= 12 and len(kp1) >= 12:
                        ms = bf.match(d0, d1)
                        if len(ms) >= 10:
                            pts0 = np.float32([kp0[m.queryIdx].pt for m in ms[:60]])
                            pts1 = np.float32([kp1[m.trainIdx].pt for m in ms[:60]])
                            diff_pts = pts1 - pts0
                            bg_shift_px = float(np.median(np.linalg.norm(diff_pts, axis=1)))
                            pan_flow_xy = [float(np.median(diff_pts[:, 0])), float(np.median(diff_pts[:, 1]))]

                # MoGe-2 på 1 representativ nyckelruta per tagning
                rgb_mid = cv2.cvtColor(frames_bgr[mid_f], cv2.COLOR_BGR2RGB)
                with torch.inference_mode():
                    mo = self.moge.infer(torch.from_numpy(rgb_mid.copy()).permute(2, 0, 1).cuda().float() / 255.0, resolution_level=7)
                D_map = mo["depth"].cpu().numpy().astype(np.float32)
                Nm_map = mo["normal"].cpu().numpy().astype(np.float32)
                K_moge = mo["intrinsics"].cpu().numpy()
                f_px_p = float(K_moge[0, 0] * Wp)
                f_px_orig = float(K_moge[0, 0] * W_orig)
                lins_mm = round(36.0 * f_px_p / Wp, 2)
                hfov_deg = round(math.degrees(2.0 * math.atan(Wp / (2.0 * f_px_p))), 2)

                # Maskera ut ev. personer från MoGe-golv-/bordsestimering
                giltig = mo["mask"].cpu().numpy() & np.isfinite(D_map) & (D_map > 0.12) & (D_map < 30.0)
                ym = yolo_per_frame.get(mid_f, {"personer": [], "mat": [], "bord": []})
                for pd_item in ym["personer"]:
                    if pd_item["mask"] is not None:
                        giltig &= ~pd_item["mask"]

                # Hitta golvnormal u_cv (samma klampade _lodlinje som obs_motor.py)
                kropp_ref = np.array([0.0, -1.0, 0.0])
                n_g = Nm_map[giltig]
                hor_n = n_g[(n_g @ kropp_ref) > math.cos(math.radians(32.0))] if len(n_g) else np.zeros((0, 3))
                if len(hor_n) > 800:
                    u_raw = np.median(hor_n, axis=0)
                    u_raw /= (np.linalg.norm(u_raw) + 1e-9)
                else:
                    u_raw = kropp_ref
                u_clamp = np.array([
                    np.clip(u_raw[0], -math.sin(math.radians(8)), math.sin(math.radians(8))),
                    min(u_raw[1], -math.cos(math.radians(18))),
                    np.clip(u_raw[2], -math.sin(math.radians(18)), math.sin(math.radians(18))),
                ])
                u_cv = u_clamp / (np.linalg.norm(u_clamp) + 1e-9)
                fh_cv = np.array([0.0, 0.0, 1.0]) - u_cv[2] * u_cv
                fh_cv /= (np.linalg.norm(fh_cv) + 1e-9)
                rh_cv = np.cross(fh_cv, u_cv)
                rh_cv /= (np.linalg.norm(rh_cv) + 1e-9)

                # Mät om det finns mat / personer i tagningen
                y_frames_in_shot = [yolo_per_frame[fi] for fi in yolo_indices if a0 <= fi < b0 and fi in yolo_per_frame]
                n_pers_frames = sum(1 for y in y_frames_in_shot if len(y["personer"]) > 0)
                n_mat_frames = sum(1 for y in y_frames_in_shot if len(y["mat"]) > 0)
                med_pers_area = float(np.median([max((p["area"] for p in y["personer"]), default=0.0) for y in y_frames_in_shot])) if y_frames_in_shot else 0.0

                if n_pers_frames >= max(1, len(y_frames_in_shot) // 2) and med_pers_area > 0.035:
                    klass = "person_med_mat" if n_mat_frames >= 1 else "person"
                elif n_mat_frames >= 1 or (med_pers_area < 0.025 and bg_shift_px >= 2.0):
                    klass = "mat"
                else:
                    klass = "person" if n_pers_frames >= 1 else "miljo"

                # Färgpalett för ev. matshot från center-box eller bildmitt
                palette_hex = ["#d98f4e", "#6b9c4a", "#f2e5d5"]
                all_food_boxes = [m["box"] for y in y_frames_in_shot for m in y["mat"]]
                is_bowl = any(m["cls"] in BOWL_COCO_IDS for y in y_frames_in_shot for m in y["mat"])
                if all_food_boxes:
                    bx_m = np.median(np.array(all_food_boxes), axis=0)
                else:
                    bx_m = np.array([Wp * 0.25, Hp * 0.35, Wp * 0.75, Hp * 0.72])
                cx0, cy0, cx1, cy1 = [int(np.clip(v, 0, b)) for v, b in zip(bx_m, (Wp, Hp, Wp, Hp))]
                crop_f = frames_bgr[mid_f][max(0, cy0):max(cy0 + 10, cy1), max(0, cx0):max(cx0 + 10, cx1)]
                if crop_f.size > 30:
                    pix_rgb = cv2.cvtColor(crop_f, cv2.COLOR_BGR2RGB).reshape(-1, 3)
                    qs = np.percentile(pix_rgb, [20, 50, 80], axis=0).astype(int)
                    palette_hex = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in qs]

                # Matcha/spåra person-ID i denna tagning över YOLO-rutor
                shot_tracks: dict[str, dict[int, dict[str, Any]]] = {}
                if klass in ("person", "person_med_mat"):
                    local_tracks: list[dict[str, Any]] = []
                    for fi in [k for k in yolo_indices if a0 <= k < b0]:
                        for pd_item in yolo_per_frame.get(fi, {}).get("personer", []):
                            bx = pd_item["box"]
                            cx_p = 0.5 * (bx[0] + bx[2])
                            cy_p = 0.5 * (bx[1] + bx[3])
                            hist = _torso_hist(frames_bgr[fi], bx)
                            best_loc = None
                            best_sc = 0.0
                            for lt in local_tracks:
                                prev_f, prev_bx = lt["last_f"], lt["last_box"]
                                px_c = 0.5 * (prev_bx[0] + prev_bx[2])
                                py_c = 0.5 * (prev_bx[1] + prev_bx[3])
                                dist_n = math.hypot(cx_p - px_c, cy_p - py_c) / max(Wp, 1)
                                sim_h = float(np.dot(hist, lt["hist"]))
                                sc = sim_h - 0.8 * dist_n
                                if dist_n < 0.35 and sc > best_sc:
                                    best_sc = sc
                                    best_loc = lt
                            if best_loc is None:
                                # Re-ID mot globala personer
                                best_pid = None
                                best_g = 0.65
                                for gp in global_tracks:
                                    g_sim = float(np.dot(hist, gp["hist"]))
                                    if gp["pid"] not in {x["pid"] for x in local_tracks} and g_sim > best_g:
                                        best_g = g_sim
                                        best_pid = gp["pid"]
                                if best_pid is None:
                                    idx_name = len(global_tracks)
                                    best_pid = chr(65 + idx_name) if idx_name < 26 else f"P{idx_name}"
                                    global_tracks.append({"pid": best_pid, "hist": hist})
                                best_loc = {"pid": best_pid, "hist": hist, "frames": {}, "last_f": fi, "last_box": bx}
                                local_tracks.append(best_loc)
                            best_loc["last_f"] = fi
                            best_loc["last_box"] = bx
                            best_loc["hist"] = 0.7 * best_loc["hist"] + 0.3 * hist
                            best_loc["frames"][fi] = pd_item
                    for lt in local_tracks:
                        if len(lt["frames"]) >= 1:
                            shot_tracks[lt["pid"]] = lt["frames"]

                shot_info_list.append({
                    **sh,
                    "klass": klass,
                    "lins_mm": lins_mm,
                    "hfov_deg": hfov_deg,
                    "f_px_p": f_px_p,
                    "f_px_orig": f_px_orig,
                    "u_cv": u_cv,
                    "fh_cv": fh_cv,
                    "rh_cv": rh_cv,
                    "D_map": D_map,
                    "K_moge": K_moge,
                    "bg_shift_px": bg_shift_px,
                    "pan_flow_xy": pan_flow_xy,
                    "palette_hex": palette_hex,
                    "is_bowl": is_bowl,
                    "shot_tracks": shot_tracks,
                })
            tider["moge_homografi_tracking"] = round(time.perf_counter() - t0, 2)

            # --- 5. SAM 3D Body på 3 fps + PCHIP + benlängdsåterprojicering + ablationsmätning ---
            t0 = time.perf_counter()
            step_sam = max(1, int(round(fps / 3.0)))  # ~3 fps

            # Orienteringsmatris OpenCV -> Blender världsrum [X=rh, Y=fh, Z=u], kameramatris M @ F med det = +1
            rorelse: dict[str, list[dict[str, Any]]] = {}
            personer_meta: dict[str, dict[str, Any]] = {}
            objekt_lista: list[dict[str, Any]] = []
            tagningar_ut: list[dict[str, Any]] = []
            sam_calls = 0
            pchip_ablation: dict[str, Any] | None = None

            # Global rumsgräns i kamerakordinater (enkla rumsobjekt kring 0..4 m framåt)
            min_x, max_x, min_y, max_y = -2.2, 2.2, -1.2, 4.2

            def _map_sam_to_world(o_dict, info, C_w):
                # Koordinatbas i värld (Z-upp)
                rh_v, fh_v, u_v = info["rh_cv"], info["fh_cv"], info["u_cv"]
                # OpenCV coords i meter (X_right, Y_down, Z_fwd) -> värld (p @ rh, p @ fh, p @ u)
                M_cv2w = np.stack([rh_v, fh_v, u_v], axis=0)  # det = +1
                pts_cv = o_dict["pred_joint_coords"].astype(float) + o_dict["pred_cam_t"].astype(float)
                pts_w = (pts_cv @ M_cv2w.T) + C_w

                # Hämta MHR -> LEDER_T1
                m_ix = self.mhr_ix
                hi = m_ix["c_head"]
                R_head_mhr = o_dict["pred_global_rots"][hi].astype(float)
                # Huvudriktningsvektor ur höger/vänster öga mot hjässa
                v_fram_w = pts_w[m_ix.get("r_eye", hi)] * 0.5 + pts_w[m_ix.get("l_eye", hi)] * 0.5 - pts_w[hi]
                nf = float(np.linalg.norm(v_fram_w))
                if nf > 0.01:
                    v_fram_w = (v_fram_w / nf) * 0.12
                else:
                    v_fram_w = np.array([0.0, 0.12, 0.0])

                pts_28 = np.zeros((len(LEDER_T1), 3), dtype=float)
                for ji, jn in enumerate(LEDER_T1):
                    if jn == "huvud_upp":
                        pts_28[ji] = pts_w[hi] + np.array([0.0, 0.0, 0.10])
                    elif jn == "nasa_mal":
                        pts_28[ji] = pts_w[hi] + v_fram_w + np.array([0.0, 0.0, 0.02])
                    elif jn in ("l_hand_mitt", "r_hand_mitt"):
                        sd = jn[0]
                        i1 = m_ix.get(f"{sd}_index1")
                        p1 = m_ix.get(f"{sd}_pinky1")
                        if i1 is not None and p1 is not None:
                            pts_28[ji] = 0.5 * (pts_w[i1] + pts_w[p1])
                        else:
                            pts_28[ji] = pts_w[m_ix[f"{sd}_wrist"]]
                    else:
                        pts_28[ji] = pts_w[m_ix[jn]]
                return pts_28, M_cv2w

            bord_counter_candidates = []
            ablation_done = False

            for sh in shot_info_list:
                sid = sh["id"]
                a0, b0 = sh["ut"]
                sh_dur_frames = b0 - a0
                rh_v, fh_v, u_v = sh["rh_cv"], sh["fh_cv"], sh["u_cv"]
                M_cv2w = np.stack([rh_v, fh_v, u_v], axis=0)
                R_cam = M_cv2w @ F  # det(M_cv2w)=+1, det(F)=+1 -> det(R_cam)=+1
                # Matris -> [qw, qx, qy, qz]
                tr_r = float(np.trace(R_cam))
                if tr_r > 0:
                    s_q = math.sqrt(tr_r + 1.0) * 2.0
                    q_cam = [0.25 * s_q, (R_cam[2, 1] - R_cam[1, 2]) / s_q, (R_cam[0, 2] - R_cam[2, 0]) / s_q, (R_cam[1, 0] - R_cam[0, 1]) / s_q]
                elif R_cam[0, 0] > R_cam[1, 1] and R_cam[0, 0] > R_cam[2, 2]:
                    s_q = math.sqrt(1.0 + R_cam[0, 0] - R_cam[1, 1] - R_cam[2, 2]) * 2.0
                    q_cam = [(R_cam[2, 1] - R_cam[1, 2]) / s_q, 0.25 * s_q, (R_cam[0, 1] + R_cam[1, 0]) / s_q, (R_cam[0, 2] + R_cam[2, 0]) / s_q]
                elif R_cam[1, 1] > R_cam[2, 2]:
                    s_q = math.sqrt(1.0 + R_cam[1, 1] - R_cam[0, 0] - R_cam[2, 2]) * 2.0
                    q_cam = [(R_cam[0, 2] - R_cam[2, 0]) / s_q, (R_cam[0, 1] + R_cam[1, 0]) / s_q, 0.25 * s_q, (R_cam[1, 2] + R_cam[2, 1]) / s_q]
                else:
                    s_q = math.sqrt(1.0 + R_cam[2, 2] - R_cam[0, 0] - R_cam[1, 1]) * 2.0
                    q_cam = [(R_cam[1, 0] - R_cam[0, 1]) / s_q, (R_cam[0, 2] + R_cam[2, 0]) / s_q, (R_cam[1, 2] + R_cam[2, 1]) / s_q, 0.25 * s_q]
                qn = math.sqrt(sum(c * c for c in q_cam)) or 1.0
                q_cam = [round(c / qn, 5) for c in q_cam]

                C_world = np.array([0.0, 0.0, 1.38], dtype=float)
                K_proxy = np.array([[sh["f_px_p"], 0.0, Wp / 2.0], [0.0, sh["f_px_p"], Hp / 2.0], [0.0, 0.0, 1.0]], dtype=np.float32)

                shot_pers_meta = []
                if sh["shot_tracks"]:
                    for pid, tr_frames in sh["shot_tracks"].items():
                        avail_fs = sorted(tr_frames.keys())
                        sample_fs = [avail_fs[0]]
                        for fi in avail_fs:
                            if fi - sample_fs[-1] >= step_sam:
                                sample_fs.append(fi)
                        if avail_fs[-1] not in sample_fs:
                            sample_fs.append(avail_fs[-1])

                        pts_anchors = []
                        t_anchors = []
                        ben_vis_list = []
                        for fi in sample_fs:
                            bx = tr_frames[fi]["box"]
                            img_rgb = cv2.cvtColor(frames_bgr[fi], cv2.COLOR_BGR2RGB)
                            with torch.inference_mode():
                                out_sam = self.sam3d.process_one_image(
                                    img_rgb,
                                    bboxes=np.array([bx], np.float32),
                                    masks=None,
                                    cam_int=torch.tensor(K_proxy)[None],
                                )
                            sam_calls += 1
                            if not out_sam:
                                continue
                            p28, _ = _map_sam_to_world(out_sam[0], sh, C_world)
                            pts_anchors.append(p28)
                            t_anchors.append(fi)
                            ben_vis_list.append(bool(bx[3] > Hp * 0.86))

                        if not pts_anchors:
                            continue
                        t_anc = np.array(t_anchors, dtype=float)
                        p_anc = np.array(pts_anchors, dtype=float)  # (K, 28, 3)

                        # Bestäm stående/sittande + golv/bordsjustering (z_skift) + per-led tilltro
                        med_fot_z = float(np.median(np.minimum(p_anc[:, T1_IX["l_foot"], 2], p_anc[:, T1_IX["r_foot"], 2])))
                        ben_skymda = bool(np.mean(ben_vis_list) < 0.45)
                        is_sitting = bool(np.median(p_anc[:, T1_IX["c_spine0"], 2]) - med_fot_z < 0.62)
                        pose_lbl = "sittande" if is_sitting else "staende"
                        if not is_sitting and abs(med_fot_z - FOTLED_OVER_GOLV) > 0.05:
                            p_anc[:, :, 2] -= (med_fot_z - FOTLED_OVER_GOLV)

                        # Empirisk PCHIP-ablation på första tagningen med >= 4 ankare & fler YOLO-rutor
                        if not ablation_done and not pchip_ablation and len(t_anc) >= 4:
                            mid_cands = [fi for fi in avail_fs if fi not in sample_fs and t_anc[0] < fi < t_anc[-1]][:4]
                            if mid_cands:
                                pchip_ab = PchipInterpolator(t_anc, p_anc, axis=0)
                                errs_mm = []
                                for fi_t in mid_cands:
                                    img_rgb = cv2.cvtColor(frames_bgr[fi_t], cv2.COLOR_BGR2RGB)
                                    with torch.inference_mode():
                                        o_t = self.sam3d.process_one_image(
                                            img_rgb, bboxes=np.array([tr_frames[fi_t]["box"]], np.float32), masks=None, cam_int=torch.tensor(K_proxy)[None]
                                        )
                                    if o_t:
                                        p_gt, _ = _map_sam_to_world(o_t[0], sh, C_world)
                                        if not is_sitting and abs(med_fot_z - FOTLED_OVER_GOLV) > 0.05:
                                            p_gt[:, 2] -= (med_fot_z - FOTLED_OVER_GOLV)
                                        p_hat = pchip_ab(float(fi_t))
                                        # Mät överkropps- + axel-/handledsfel i mm
                                        errs_mm.extend((np.linalg.norm(p_hat - p_gt, axis=-1) * 1000.0).tolist())
                                if errs_mm:
                                    pchip_ablation = {
                                        "klipp": nyckel,
                                        "tagning": sid,
                                        "testade_rutor": len(mid_cands),
                                        "median_fel_mm": round(float(np.median(errs_mm)), 1),
                                        "p90_fel_mm": round(float(np.percentile(errs_mm, 90)), 1),
                                    }
                                    ablation_done = True

                        # PCHIP-interpolation över [a0, b0) + återprojicering av benlängder
                        u_full = np.arange(a0, b0, dtype=float)
                        if len(t_anc) >= 2:
                            u_clamped = np.clip(u_full, t_anc[0], t_anc[-1])
                            X_full = PchipInterpolator(t_anc, p_anc, axis=0)(u_clamped)
                        else:
                            X_full = np.repeat(p_anc[:1], len(u_full), axis=0)

                        # Återprojicera benlängder längs trädet från c_spine0 (förhindrar kordaeffekt!)
                        med_lens = {}
                        for pa, ch in T1_KANTER:
                            d_v = np.linalg.norm(p_anc[:, T1_IX[ch]] - p_anc[:, T1_IX[pa]], axis=-1)
                            med_lens[(pa, ch)] = float(np.median(d_v))
                        sp0_ix = T1_IX["c_spine0"]
                        for ti in range(len(X_full)):
                            for pa, ch in T1_KANTER:
                                ia, ib = T1_IX[pa], T1_IX[ch]
                                vec = X_full[ti, ib] - X_full[ti, ia]
                                ln = float(np.linalg.norm(vec))
                                if ln > 1e-5:
                                    X_full[ti, ib] = X_full[ti, ia] + (vec / ln) * med_lens[(pa, ch)]

                        rutor_int = [[int(u)] + [int(round(c * 1000.0)) for c in X_full[i].reshape(-1)] for i, u in enumerate(range(a0, b0))]
                        rorelse.setdefault(pid, []).append({"tagning": sid, "ut": [a0, b0], "rutor": rutor_int})
                        shot_pers_meta.append({"id": pid, "ankare": f"bord_1" if ben_skymda else None})

                        tilltro_status = {
                            "overkropp": "observerad",
                            "underkropp": "skymd_antagen" if ben_skymda else "observerad",
                        }
                        if pid not in personer_meta:
                            personer_meta[pid] = {
                                "roll": pid,
                                "farg": ROLL_FARG.get(pid, "#98c379"),
                                "hemplats": "stol_" + pid if is_sitting else None,
                                "pose": pose_lbl,
                                "unik": True,
                                "tilltro": tilltro_status,
                                "status": {"identitet": "utseende+proportioner", "hallning": "antagen" if ben_skymda else "observerad"},
                            }
                        if ben_skymda or sh["klass"] == "person_med_mat":
                            arm_z = float(np.median(np.minimum(X_full[:, T1_IX["l_wrist"], 2], X_full[:, T1_IX["r_wrist"], 2])))
                            b_cx = float(np.median(X_full[:, T1_IX["c_spine2"], 0]))
                            b_cy = float(np.median(X_full[:, T1_IX["c_spine2"], 1])) - 0.52
                            bord_counter_candidates.append([b_cx, b_cy, max(0.72, arm_z - 0.06)])

                # Bygg matshot-tallrik/skål för 'mat' / 'person_med_mat' tagningar
                if sh["klass"] in ("mat", "person_med_mat"):
                    mat_typ = "mat_skal" if sh["is_bowl"] else "mat_tallrik"
                    if sh["shot_tracks"] and bord_counter_candidates:
                        m_pos = list(bord_counter_candidates[-1])
                        m_pos[2] += 0.08
                    else:
                        # Placera tallrik mitt i kamerans siktlinje vid median-MoGe-djup ~ 0.95 m
                        dm = sh["D_map"]
                        valid_d = dm[np.isfinite(dm) & (dm > 0.3) & (dm < 3.5)]
                        d_med = float(np.clip(np.median(valid_d) if len(valid_d) else 1.0, 0.55, 1.85))
                        p_cv_m = np.array([0.0, 0.05 * d_med, d_med])
                        p_w_m = (p_cv_m @ M_cv2w.T) + C_world
                        m_pos = [round(float(v), 3) for v in p_w_m]
                        # Om ingen bord finns under, skapa observerat bordsunderlag under tallriken
                        objekt_lista.append({
                            "id": f"bord_{sid}", "bas": "bord", "typ": "bord",
                            "pos": [m_pos[0], m_pos[1], round(m_pos[2] - 0.05, 3)],
                            "rot": [0.0, 0.0, 0.0],
                            "matt": [1.1, 0.75, 0.06],
                            "farg": "#78624d",
                            "tilltro": "observerad",
                            "rum": "gemensamt",
                            "synlig_ut": [[a0, b0]],
                        })

                    objekt_lista.append({
                        "id": f"mat_{sid}", "bas": "mat", "typ": mat_typ,
                        "mat_stil": "skal" if mat_typ == "mat_skal" else "tallrik",
                        "etikett": f"Maträtt ({sid})",
                        "farg": sh["palette_hex"][0],
                        "farg_palett": sh["palette_hex"],
                        "pos": [round(float(v), 3) for v in m_pos],
                        "rot": [0.0, 0.0, 0.0],
                        "matt": [0.34, 0.34, 0.07 if mat_typ == "mat_tallrik" else 0.11],
                        "tilltro": "observerad",
                        "rum": "gemensamt",
                        "synlig_ut": [[a0, b0]],
                    })

                # Kamera per tagning (rörlig om homografin visade kamerarörelse!)
                is_moving = sh["bg_shift_px"] > 7.5
                if is_moving:
                    # Mjuk kamerainåkning / panorering ur uppmätt homografi
                    dx_m = np.clip(-sh["pan_flow_xy"][0] / max(sh["f_px_p"], 100.0) * 1.1, -0.35, 0.35)
                    dy_m = 0.22 if sh["klass"] == "mat" else 0.14
                    nyck_list = []
                    for k_i in range(min(8, max(3, sh_dur_frames // 5)) + 1):
                        alpha_k = k_i / float(min(8, max(3, sh_dur_frames // 5)))
                        u_k = min(b0 - 1, a0 + int(round(alpha_k * (sh_dur_frames - 1))))
                        c_k = [
                            round(float(C_world[0] + dx_m * (alpha_k - 0.5)), 4),
                            round(float(C_world[1] + dy_m * alpha_k), 4),
                            round(float(C_world[2] - (0.04 * alpha_k if sh["klass"] == "mat" else 0.0)), 4),
                        ]
                        nyck_list.append([u_k] + c_k + q_cam + [sh["lins_mm"]])
                    kam_obj = {"typ": "rorlig", "statisk": False, "nycklar": nyck_list}
                else:
                    kam_obj = {"typ": "statisk", "statisk": True, "nycklar": [[a0, round(float(C_world[0]), 4), round(float(C_world[1]), 4), round(float(C_world[2]), 4), *q_cam, sh["lins_mm"]]]}

                tagningar_ut.append({
                    "id": sid,
                    "ut": [a0, b0],
                    "personer": shot_pers_meta,
                    "kamera": kam_obj,
                    "klass": sh["klass"],
                })

            # Gemensamt golv & huvudbord om det behövs
            objekt_lista.insert(0, {
                "id": "golv", "bas": "golv", "typ": "golv",
                "pos": [0.0, 1.5, -0.02], "rot": [0.0, 0.0, 0.0], "matt": [4.4, 5.4, 0.04],
                "farg": "#3d3832", "tilltro": "observerad", "rum": "gemensamt", "synlig_ut": [[0, n_frames]],
            })
            if bord_counter_candidates:
                med_b = np.median(np.array(bord_counter_candidates), axis=0)
                objekt_lista.append({
                    "id": "bord_1", "bas": "bord_1", "typ": "bord",
                    "pos": [round(float(med_b[0]), 3), round(float(med_b[1]), 3), round(float(med_b[2]), 3)],
                    "rot": [0.0, 0.0, 0.0], "matt": [1.5, 0.52, 0.14],
                    "farg": "#8c6239", "tilltro": "observerad", "rum": "gemensamt", "synlig_ut": [[0, n_frames]],
                })

            tider["sam3d_och_pchip"] = round(time.perf_counter() - t0, 2)
            tot_gpu_s = round(time.perf_counter() - t_tot0, 2)

            # Bygg scenpaket/2 & medielager/1
            paket = {
                "schema": "scenpaket/2",
                "klipp": {"id": klipp_id, "nyckel": nyckel, "ingest_v": "ingest_v2_gpu"},
                "tidsbas": {"fps": round(fps, 3), "antal_rutor": n_frames, "regel": "ingest_v2 3fps+PCHIP"},
                "bild": {"bredd": Wp, "hojd": Hp, "sensor_mm": 36.0},
                "koordinater": "Blender: Z upp, meter; kvaternion (w,x,y,z); leder i hel-mm.",
                "golv_z": 0.0,
                "objekt": objekt_lista,
                "tagningar": tagningar_ut,
                "personer": personer_meta,
                "leder": LEDER_T1,
                "rorelse": rorelse,
            }
            tagningar_ml = [
                {
                    "id": sh["tid_id"], "fran": sh["fran_s"], "till": sh["till_s"],
                    "langd": round(sh["till_s"] - sh["fran_s"], 3),
                    "klass": sh["klass"],
                    "tal": [i for i, ts in enumerate(tal_segment) if min(sh["till_s"], ts["till_s"]) > max(sh["fran_s"], ts["fran_s"])],
                    "skarmtext": [x["id"] for x in skarmtext if min(sh["till_s"], x["till_s"]) > max(sh["fran_s"], x["fran_s"])],
                }
                for sh in shot_info_list
            ]
            tidslinje = {
                "schema": "medielager/1",
                "klipp": klipp_id,
                "kalla": {"bredd": Wp, "hojd": Hp, "fps": round(fps, 3), "langd": round(dur_s, 3), "ljud": has_audio},
                "tagningar": tagningar_ml,
                "skarmtext": skarmtext,
                "tal": {"segment": tal_segment, "sekunder": round(sum(s["till_s"] - s["fran_s"] for s in tal_segment), 2)},
                "musik": {**musik_meta, "stammar": {"tal": "tal.wav"} if has_audio else {}},
                "mat": {
                    "tagningar_mat": [t["id"] for t in tagningar_ml if t["klass"] == "mat"],
                    "tagningar_person_med_mat": [t["id"] for t in tagningar_ml if t["klass"] == "person_med_mat"],
                },
                "tider_s": tider,
            }

            proxy_bytes = proxy_mp4.read_bytes()
            tal_bytes = tal_wav.read_bytes() if tal_wav.exists() else b""
            paket_bytes = json.dumps(paket, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            tl_bytes = json.dumps(tidslinje, ensure_ascii=False, indent=1).encode("utf-8")

            total_bytes = len(proxy_bytes) + len(tal_bytes) + len(paket_bytes) + len(tl_bytes)
            rapport = {
                "klipp": klipp_id,
                "nyckel": nyckel,
                "gpu": self.gpu,
                "container_load_s": self.load_s,
                "whisper_device": self.whisper_dev,
                "langd_video_s": round(dur_s, 2),
                "n_frames": n_frames,
                "antal_tagningar": len(tagningar_ut),
                "antal_sam3db_anrop": sam_calls,
                "pchip_ablation": pchip_ablation,
                "tider_s": {**tider, "total_ingest_s": tot_gpu_s},
                "est_marginal_usd": round(tot_gpu_s * L4_USD_PER_S, 4),
                "storlekar_bytes": {
                    "paket_json": len(paket_bytes),
                    "tidslinje_json": len(tl_bytes),
                    "proxy_h264_mp4": len(proxy_bytes),
                    "tal_wav": len(tal_bytes),
                    "totalt_bytes": total_bytes,
                    "totalt_mb": round(total_bytes / (1024.0 * 1024.0), 3),
                },
            }
            return {
                "paket_bytes": paket_bytes,
                "tidslinje_bytes": tl_bytes,
                "proxy_bytes": proxy_bytes,
                "tal_bytes": tal_bytes,
                "rapport": rapport,
            }


@app.local_entrypoint()
def main() -> None:
    jobs = [
        ("spanjorskan", "spanjorskansthlm-7474263274415082774", ROT / "data" / "format" / "kontroll" / "klipp" / "spanjorskansthlm-7474263274415082774.mp4"),
        ("duepiani", "duepiani-7650849186912406806", ROT / "data" / "format" / "kontroll" / "klipp" / "duepiani-7650849186912406806.mp4"),
    ]
    worker = IngestV2Worker()
    rapporter = []
    for i, (nyckel, klipp_id, vid_path) in enumerate(jobs):
        t0 = time.perf_counter()
        print(f"Startar ingest_v2 #{i + 1} ({nyckel}: {vid_path.name})...", flush=True)
        res = worker.ingest_klipp.remote(vid_path.read_bytes(), klipp_id, nyckel)
        wall_s = round(time.perf_counter() - t0, 2)

        ut_dir = UT_BASE / nyckel
        ut_dir.mkdir(parents=True, exist_ok=True)
        (ut_dir / "paket.json").write_bytes(res["paket_bytes"])
        (ut_dir / "tidslinje.json").write_bytes(res["tidslinje_bytes"])
        (ut_dir / "proxy_h264.mp4").write_bytes(res["proxy_bytes"])
        if res["tal_bytes"]:
            (ut_dir / "tal.wav").write_bytes(res["tal_bytes"])
        rap = dict(res["rapport"], wall_inkl_natverk_s=wall_s, var_varm=(i > 0))
        (ut_dir / "ingest_rapport.json").write_text(json.dumps(rap, ensure_ascii=False, indent=2), encoding="utf-8")
        rapporter.append(rap)
        print(
            f"KLAR {nyckel}: wall={wall_s}s, gpu_ingest={rap['tider_s']['total_ingest_s']}s, "
            f"storlek={rap['storlekar_bytes']['totalt_mb']} MB, sam3db={rap['antal_sam3db_anrop']} anrop",
            flush=True,
        )
    (UT_BASE / "ingest_v2_benchmark.json").write_text(json.dumps(rapporter, ensure_ascii=False, indent=2), encoding="utf-8")
    print("INGEST_V2_BENCHMARK_OK", flush=True)
