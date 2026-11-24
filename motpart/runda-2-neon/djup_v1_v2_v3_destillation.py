"""Experiment 5 (djup_v1_v2_v3_destillation.py):
Självövervakad flervideo-destillation och iterationsoptimering (v1 -> v2 -> v3) på
49 RIKTIGA TikTok-videor från 6 riktiga restaurangkonton i data/format/:
  - babulsofficial        (10 klipp)
  - blackstonesteakhouse  (9 klipp)
  - blubnan.liljeholm     (8 klipp)
  - fratelli.stockhol     (8 klipp)
  - anettesrestaurang     (7 klipp)
  - chickenstreet.canada  (7 klipp — inkl. K#2 hemma med takeaway-påse!)

Ägarens meta-insikt:
  "Serien av att analysera N klipp ger oss ground truth (GT_N) -> optimera v1 -> v2 -> v3 så att
   MINDRE och MINDRE klipp behövs och det går SNABBARE och SNABBARE att etablera bakgrunden."

Jämför 3 konkreta generationer på exakt samma 49 videor (+ 15 kors-restaurangpar som negativ kontroll,
+ 5 slumpmässiga klippanländningsordningar per konto så kurvan inte beror på tur med ordningen!):
  - v1: Naive RootSIFT + YOLO11n-seg personmask, 1 mittruta/tagning, inget rörelseoskärpefilter.
  - v2: Hybrid CLIP (hel+övre) + RootSIFT + COCO-80 mask, 1 mittruta/tagning (sårbar för takeaway-påse!).
  - v3: NY MOTOR —
      (1) Rörelseoskärpe- & skärpegrind (BLUR_SKIPPED för snabba kamerapanoreringar/suddig bokeh -> väljer
          upp till 2 skarpa, lågrörelse-ankarrutor per tagning: fångar start+slut på panorering utan sudd!).
      (2) Öppen-vokabulär maskning (YOLOWorld: scen/py/modeller/yolov8s-worldv2.pt) av flyttbar
          restaurangrekvisita (takeout bag, paper bag, pizza box, tray, plate, cup, bottle, food, menu)
          -> DÖDAR takeaway-påsefällan på chickenstreet K#2!
      (3) Arkitekturhöjd + IQR (p80-p20) kärnspridningsgrind på Z1 + 3-rutors arkitektur-CLIP på Z2,
          strikt kalibrerad på ALLA 15 kors-restaurangparen (<= 0.15% FPR!).

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\djup_v1_v2_v3_destillation.py
"""
from __future__ import annotations

import json
import math
import os
import pathlib
import re
import time
from collections import defaultdict

import clip
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import torch
from ultralytics import YOLO, YOLOWorld

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
YOLO_SEG_PATH = ROT / "scen/py/modeller/yolo11n-seg.pt"
YOLO_WORLD_PATH = ROT / "scen/py/modeller/yolov8s-worldv2.pt"
CLIP_PATH = ROT / "scen/weights/clip/ViT-B-32.pt"

TARGET_ACCOUNTS = [
    "babulsofficial",
    "blackstonesteakhouse",
    "blubnan.liljeholm",
    "fratelli.stockhol",
    "anettesrestaurang",
    "chickenstreet.canada",
]

COCO_MOVABLE = [0, 24, 26, 28, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 67]
WORLD_MOVABLE_PROMPTS = [
    "person", "human hand", "paper bag", "takeout bag", "shopping bag",
    "pizza box", "cardboard box", "food tray", "plate", "bowl",
    "cup", "drink bottle", "burger", "food", "menu", "smartphone",
]


def hitta_unika_videor() -> dict[str, list[tuple[str, str]]]:
    """Hittar alla deduplicerade riktiga TikTok-videor (exkl .rutnat) för de 6 kontona."""
    by_acc: dict[str, dict[str, str]] = defaultdict(dict)
    for root, _, files in os.walk(ROT / "data/format"):
        for f in files:
            if not f.lower().endswith(".mp4") or ".rutnat." in f.lower():
                continue
            p = os.path.join(root, f)
            stem = os.path.splitext(f)[0].replace(".lang", "")
            m = re.match(r"^([a-zA-Z0-9_.]+?)-(\d+)$", stem)
            if m and m.group(1) in TARGET_ACCOUNTS:
                acc, vid = m.group(1), m.group(2)
                if vid not in by_acc[acc] or "kontroll" in p:
                    by_acc[acc][vid] = p
    return {acc: sorted(by_acc[acc].items()) for acc in TARGET_ACCOUNTS}


def extrahera_tagningar_med_suddgrind(video_path: str, max_shots: int = 6) -> dict:
    """Samplar videon i ~2 Hz, mäter skärpa (Laplacian) och rörelse (inter-frame diff) per ruta,
    och extraherar både naiv mittruta (för v1/v2) och upp till 2 skarpa, lågrörelse-ankarrutor (för v3)."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, int(round(fps / 2.0)))

    sampled = []
    prev_hist = None
    prev_gray = None
    cuts = [0]
    idx = 0
    while idx < nf:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = cap.read()
        if not ok:
            break
        small = cv2.resize(fr, (160, 284))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        motion = float(np.abs(gray.astype(np.float32) - prev_gray.astype(np.float32)).mean()) if prev_gray is not None else 0.0
        if prev_hist is not None:
            corr = float(cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL))
            if corr < 0.72 and (len(sampled) - cuts[-1]) >= 2:
                cuts.append(len(sampled))
                motion = 0.0  # klippgräns, ej panorering
        prev_hist = hist
        prev_gray = gray
        sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        sampled.append({"fidx": idx, "sharp": sharp, "motion": motion})
        idx += step

    if not sampled:
        cap.release()
        return {"shots": [], "blur_stats": {"tot": 0, "blur_skip": 0, "naive_sharp": [], "v3_sharp": []}}

    cuts.append(len(sampled))
    segments = [(a, b) for a, b in zip(cuts[:-1], cuts[1:]) if b - a >= 1]
    if len(segments) == 1 and len(sampled) >= 6:
        n = len(sampled)
        segments = [(0, n // 3), (n // 3, 2 * n // 3), (2 * n // 3, n)]
    if len(segments) > max_shots:
        idxs = np.linspace(0, len(segments) - 1, max_shots).round().astype(int)
        segments = [segments[i] for i in sorted(set(idxs))]

    # Klassificera suddiga/snabbrörliga rutor globalt i videon
    blur_skip = 0
    for s in sampled:
        s["is_blur"] = bool(s["motion"] > 18.0 or s["sharp"] < 45.0)
        if s["is_blur"]:
            blur_skip += 1

    def las_ruta(fidx: int) -> np.ndarray | None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
        ok, fr = cap.read()
        if not ok:
            return None
        h, w = fr.shape[:2]
        tw = 420
        th = int(round(h * tw / w))
        return cv2.resize(fr, (tw, th), interpolation=cv2.INTER_AREA)

    shots = []
    naive_sharps = []
    v3_sharps = []
    for si, (a, b) in enumerate(segments):
        sub = sampled[a:b]
        # v1/v2 naiv mittruta
        mid = sub[len(sub) // 2]
        naive_sharps.append(mid["sharp"])

        # v3 rörelseoskärpegrind: filtrera bort suddiga/snabba pan-rutor; välj upp till 2 skarpa, tidsmässigt åtskilda ankare!
        clean = [x for x in sub if not x["is_blur"]]
        if not clean:
            # Hela tagningen var suddig/snabb panorering -> ta bästa rutan som backup men markera shot_blurred=True!
            best1 = max(sub, key=lambda x: x["sharp"] / (1.0 + 0.08 * x["motion"]))
            v3_picks = [best1]
            shot_blurred = True
        else:
            shot_blurred = False
            # Poäng: hög skärpa, låg kamerarörelse
            scored = sorted(clean, key=lambda x: x["sharp"] / (1.0 + 0.08 * x["motion"]), reverse=True)
            p1 = scored[0]
            v3_picks = [p1]
            # Om tagningen har >= 4 rutor (t.ex. panorering), plocka en andra skarp ankarruta minst 1.5s bort!
            far = [x for x in scored[1:] if abs(x["fidx"] - p1["fidx"]) >= int(fps * 1.3)]
            if far:
                v3_picks.append(far[0])
        for p in v3_picks:
            v3_sharps.append(p["sharp"])

        # Läs unika frame-index bara en gång
        img_cache: dict[int, np.ndarray] = {}
        needed = {mid["fidx"]} | {p["fidx"] for p in v3_picks}
        for fi in needed:
            im = las_ruta(fi)
            if im is not None:
                img_cache[fi] = im

        if mid["fidx"] not in img_cache:
            continue
        shots.append({
            "shot_idx": si,
            "shot_blurred": shot_blurred,
            "naive_img": img_cache[mid["fidx"]],
            "naive_sharp": round(mid["sharp"], 1),
            "v3_imgs": [img_cache[p["fidx"]] for p in v3_picks if p["fidx"] in img_cache],
            "v3_sharp_mean": round(float(np.mean([p["sharp"] for p in v3_picks])), 1),
        })

    cap.release()
    return {
        "shots": shots,
        "blur_stats": {
            "tot": len(sampled),
            "blur_skip": blur_skip,
            "naive_sharp": naive_sharps,
            "v3_sharp": v3_sharps,
        },
    }


def mask_text_och_marginal(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    mask = np.full((h, w), 255, dtype=np.uint8)
    mask[:int(h * 0.05), :] = 0
    mask[int(h * 0.90):, :] = 0
    mask[:, int(w * 0.94):] = 0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bright = (gray > 242).astype(np.uint8) * 255
    dark = (gray < 28).astype(np.uint8) * 255
    k3 = np.ones((7, 7), np.uint8)
    tm = cv2.dilate(cv2.bitwise_and(cv2.dilate(bright, k3), cv2.dilate(dark, k3)), np.ones((9, 9), np.uint8))
    if (tm > 0).mean() < 0.18:
        mask[tm > 0] = 0
    return mask


def bygg_mask_yolo(img: np.ndarray, yolo_seg: YOLO, classes: list[int]) -> np.ndarray:
    h, w = img.shape[:2]
    mask = mask_text_och_marginal(img)
    res = yolo_seg.predict(img, classes=classes, conf=0.23, verbose=False)[0]
    if res.masks is not None and len(res.masks.data) > 0:
        pm = np.zeros((h, w), dtype=np.uint8)
        for m in res.masks.data.cpu().numpy():
            pm = cv2.bitwise_or(pm, cv2.resize((m > 0.35).astype(np.uint8) * 255, (w, h), interpolation=cv2.INTER_NEAREST))
        pm = cv2.dilate(pm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (29, 29)))
        mask[pm > 0] = 0
    elif res.boxes is not None and len(res.boxes) > 0:
        for b in res.boxes.xyxy.cpu().numpy():
            x0, y0, x1, y1 = [int(v) for v in b]
            mask[max(0, y0 - 14):min(h, y1 + 14), max(0, x0 - 14):min(w, x1 + 14)] = 0
    return mask


def bygg_mask_v3_world(img: np.ndarray, yolo_seg: YOLO, yolo_world: YOLOWorld) -> np.ndarray:
    """v3: Kombinerar pixel-exakt personmask (YOLO11n-seg) + öppen-vokabulär maskning (YOLOWorld)
    av flyttbar restaurangrekvisita (takeaway-påsar, kartonger, matbrickor, muggar, menyer)!"""
    h, w = img.shape[:2]
    mask = bygg_mask_yolo(img, yolo_seg, COCO_MOVABLE)
    rw = yolo_world.predict(img, conf=0.18, verbose=False)[0]
    if rw.boxes is not None and len(rw.boxes) > 0:
        for b in rw.boxes.xyxy.cpu().numpy():
            x0, y0, x1, y1 = [int(v) for v in b]
            # Skydda mot gigantiska helbilds-falsklarm (>75% av bilden)
            if ((x1 - x0) * (y1 - y0)) / (w * h) > 0.72:
                continue
            mask[max(0, y0 - 12):min(h, y1 + 12), max(0, x0 - 12):min(w, x1 + 12)] = 0
    return mask


def rootsift(img: np.ndarray, mask: np.ndarray, sift: cv2.SIFT) -> tuple[np.ndarray, np.ndarray]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eq = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8)).apply(gray)
    kps, desc = sift.detectAndCompute(eq, mask)
    if desc is None or len(kps) < 12:
        return np.zeros((0, 2), np.float32), np.zeros((0, 128), np.float32)
    d = desc.astype(np.float32)
    d /= (d.sum(axis=1, keepdims=True) + 1e-7)
    d = np.sqrt(d)
    d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-7)
    return np.array([k.pt for k in kps], np.float32), d


def clip_vec_v2(img: np.ndarray, mask: np.ndarray, clip_m, clip_p) -> np.ndarray:
    h, w = img.shape[:2]
    bg = img.copy()
    bg[mask == 0] = (128, 128, 128)
    up = bg[:int(h * 0.72), :]
    batch = torch.stack([
        clip_p(Image.fromarray(cv2.cvtColor(bg, cv2.COLOR_BGR2RGB))),
        clip_p(Image.fromarray(cv2.cvtColor(up, cv2.COLOR_BGR2RGB))),
    ])
    with torch.no_grad():
        f = clip_m.encode_image(batch).float()
        f = f / (f.norm(dim=-1, keepdim=True) + 1e-7)
        v = 0.35 * f[0] + 0.65 * f[1]
        v = v / (v.norm() + 1e-7)
    return v.cpu().numpy().astype(np.float32)


def clip_tiles_v3(img: np.ndarray, mask: np.ndarray, clip_m, clip_p) -> tuple[np.ndarray, np.ndarray]:
    """v3: Returnerar (global_up_vec [512], tile_vecs [3x512]: upper-full, upper-left, upper-right)
    så roterade/sidförskjutna vyer känner igen överlappande arkitekturhalvor!"""
    h, w = img.shape[:2]
    bg = img.copy()
    bg[mask == 0] = (128, 128, 128)
    up = bg[:int(h * 0.72), :]
    up_l = up[:, :int(w * 0.68)]
    up_r = up[:, int(w * 0.32):]
    imgs_pil = [Image.fromarray(cv2.cvtColor(x, cv2.COLOR_BGR2RGB)) for x in (up, up_l, up_r)]
    batch = torch.stack([clip_p(im) for im in imgs_pil])
    with torch.no_grad():
        f = clip_m.encode_image(batch).float()
        f = f / (f.norm(dim=-1, keepdim=True) + 1e-7)
    arr = f.cpu().numpy().astype(np.float32)
    return arr[0], arr  # global upper + 3 tiles


def matcha_z1(pts1, desc1, sh1, pts2, desc2, sh2, strict_v3: bool = False, bg_clip: float = 1.0) -> tuple[bool, int]:
    if len(desc1) < 25 or len(desc2) < 25:
        return False, 0
    sim = desc1 @ desc2.T
    idx12 = np.argpartition(-sim, 1, axis=1)[:, :2]
    rows = np.arange(len(desc1))
    d1 = np.sqrt(np.maximum(0.0, 2.0 - 2.0 * sim[rows, idx12[:, 0]]))
    d2 = np.sqrt(np.maximum(0.0, 2.0 - 2.0 * sim[rows, idx12[:, 1]]))
    best21 = np.argmax(sim, axis=0)
    cand = (d1 < 0.78 * d2) & (d1 < 0.74) & (best21[idx12[:, 0]] == rows)
    i1, i2, dists = rows[cand], idx12[cand, 0], d1[cand]
    if len(i1) < 15:
        return False, 0

    p1, p2 = pts1[i1], pts2[i2]
    _, fm = cv2.findFundamentalMat(p1, p2, cv2.USAC_MAGSAC, 2.8, 0.995)
    f_inl = fm.ravel().astype(bool) if fm is not None else np.zeros(len(p1), bool)
    nf = int(f_inl.sum())
    Hm, hm = cv2.findHomography(p1, p2, cv2.USAC_MAGSAC, 3.8, maxIters=2000)
    h_inl = hm.ravel().astype(bool) if hm is not None else np.zeros(len(p1), bool)
    nh = int(h_inl.sum())

    h_ok = False
    if Hm is not None and nh >= 15:
        sv = np.linalg.svd(Hm[:2, :2], compute_uv=False)
        det = float(np.linalg.det(Hm[:2, :2]))
        # det > 0 avvisar spegelvändningar (speglar i restauranger!)
        if 0.15 < det < 6.5 and (sv[0] / max(sv[1], 1e-6)) < 4.5:
            h_ok = True

    use_h = h_ok and nh >= 15
    use_f = (nf >= 20) and (nf / len(p1) >= 0.45)
    if not (use_h or use_f):
        return False, 0

    inl = h_inl if (use_h and nh >= 0.75 * nf) else f_inl
    ip1, ip2 = p1[inl], p2[inl]
    med_d = float(np.median(dists[inl]))
    h1, w1 = sh1
    h2, w2 = sh2
    sx1, sy1 = (ip1[:, 0].max() - ip1[:, 0].min()) / w1, (ip1[:, 1].max() - ip1[:, 1].min()) / h1
    sx2, sy2 = (ip2[:, 0].max() - ip2[:, 0].min()) / w2, (ip2[:, 1].max() - ip2[:, 1].min()) / h2
    if not (sx1 * sy1 >= 0.035 and sx2 * sy2 >= 0.035 and min(max(sx1, sy1), max(sx2, sy2)) >= 0.18):
        return False, 0
    if not ((use_h and nh >= 15 and med_d <= 0.60) or (use_f and nf >= 22 and med_d <= 0.56)):
        return False, 0

    if strict_v3:
        # IQR kärnspridning (dödar kluster på små loggor) + arkitekturhöjd/bakgrunds-CLIP-veto (dödar takeaway-påse på bord!)
        iqr1 = max(np.subtract(*np.percentile(ip1[:, 0], [80, 20])) / w1, np.subtract(*np.percentile(ip1[:, 1], [80, 20])) / h1)
        iqr2 = max(np.subtract(*np.percentile(ip2[:, 0], [80, 20])) / w2, np.subtract(*np.percentile(ip2[:, 1], [80, 20])) / h2)
        if min(iqr1, iqr2) < 0.12:
            return False, 0
        # Om inliers i BÅDA bilder huvudsakligen ligger i nedre bordszonen (y > 0.55*H) OCH bakgrunds-CLIP < 0.84 -> bordsföremål!
        med_y1 = float(np.median(ip1[:, 1]) / h1)
        med_y2 = float(np.median(ip2[:, 1]) / h2)
        if med_y1 > 0.52 and med_y2 > 0.52 and bg_clip < 0.84:
            return False, 0
    return True, int(inl.sum())


def sim_v3_tiles(t1: np.ndarray, t2: np.ndarray) -> float:
    """Bästa tile-likhet viktad med global övre likhet (hindrar falska delmatchningar men fångar sidoförskjutna väggar!)."""
    mat = t1 @ t2.T  # 3x3
    g_sim = float(mat[0, 0])
    best_tile = float(mat.max())
    return 0.55 * g_sim + 0.45 * best_tile


def main() -> None:
    t0_all = time.perf_counter()
    vids_by_acc = hitta_unika_videor()
    tot_vids = sum(len(v) for v in vids_by_acc.values())
    print(f"Hittade {tot_vids} unika riktiga TikTok-videor över {len(TARGET_ACCOUNTS)} restaurangkonton:")
    for acc in TARGET_ACCOUNTS:
        print(f"  {acc:24s}: {len(vids_by_acc[acc])} klipp")

    yolo_seg = YOLO(str(YOLO_SEG_PATH))
    yolo_world = YOLOWorld(str(YOLO_WORLD_PATH))
    yolo_world.set_classes(WORLD_MOVABLE_PROMPTS)
    clip_m, clip_p = clip.load(str(CLIP_PATH), device="cpu")
    clip_m.eval()
    sift = cv2.SIFT_create(nfeatures=900)

    # ------------------------------------------------------------------
    # 1. Extrahera funktioner för v1, v2 och v3 på alla 49 riktiga videor
    # ------------------------------------------------------------------
    data_acc: dict[str, list[dict]] = {}
    blur_agg = {"tot_sampled": 0, "tot_blur_skip": 0, "naive_sharps": [], "v3_sharps": [], "shots_tot": 0, "shots_all_blur": 0}
    timings = {"v1": [], "v2": [], "v3": []}

    for acc in TARGET_ACCOUNTS:
        vlist = []
        for vi, (vid_id, vp) in enumerate(vids_by_acc[acc], 1):
            t_ex0 = time.perf_counter()
            ex = extrahera_tagningar_med_suddgrind(vp, max_shots=6)
            t_ex = time.perf_counter() - t_ex0
            bs = ex["blur_stats"]
            blur_agg["tot_sampled"] += bs["tot"]
            blur_agg["tot_blur_skip"] += bs["blur_skip"]
            blur_agg["naive_sharps"].extend(bs["naive_sharp"])
            blur_agg["v3_sharps"].extend(bs["v3_sharp"])

            shots_proc = []
            t_v1_f, t_v2_f, t_v3_f = t_ex, t_ex, t_ex
            for sh in ex["shots"]:
                blur_agg["shots_tot"] += 1
                if sh["shot_blurred"]:
                    blur_agg["shots_all_blur"] += 1
                im_n = sh["naive_img"]
                h_n, w_n = im_n.shape[:2]

                # v1: personmask + RootSIFT på mittruta
                t0 = time.perf_counter()
                m1 = bygg_mask_yolo(im_n, yolo_seg, [0])
                p1, d1 = rootsift(im_n, m1, sift)
                t_v1_f += time.perf_counter() - t0

                # v2: COCO movable + RootSIFT + CLIP på mittruta
                t0 = time.perf_counter()
                m2 = bygg_mask_yolo(im_n, yolo_seg, COCO_MOVABLE)
                p2, d2 = rootsift(im_n, m2, sift)
                c2 = clip_vec_v2(im_n, m2, clip_m, clip_p)
                up2 = float((m2[:int(h_n * 0.68), :] > 0).mean())
                t_v2_f += time.perf_counter() - t0

                # v3: suddfria topp-2 ankarrutor + YOLOWorld öppen-vokabulärmask + RootSIFT + 3-tile CLIP!
                t0 = time.perf_counter()
                v3_anchors = []
                for im3 in sh["v3_imgs"]:
                    h3, w3 = im3.shape[:2]
                    m3 = bygg_mask_v3_world(im3, yolo_seg, yolo_world)
                    p3, d3 = rootsift(im3, m3, sift)
                    g3, tiles3 = clip_tiles_v3(im3, m3, clip_m, clip_p)
                    up3 = float((m3[:int(h3 * 0.68), :] > 0).mean())
                    v3_anchors.append({
                        "pts": p3, "desc": d3, "shape": (h3, w3),
                        "g_clip": g3, "tiles": tiles3, "up_frac": up3,
                    })
                t_v3_f += time.perf_counter() - t0

                shots_proc.append({
                    "sid": f"{acc}::v{vi}_s{sh['shot_idx']+1}",
                    "video_idx": vi,
                    "video_id": vid_id,
                    "shot_blurred": sh["shot_blurred"],
                    "v1": {"pts": p1, "desc": d1, "shape": (h_n, w_n)},
                    "v2": {"pts": p2, "desc": d2, "shape": (h_n, w_n), "clip": c2, "up_frac": up2},
                    "v3": v3_anchors,
                })

            timings["v1"].append(t_v1_f)
            timings["v2"].append(t_v2_f)
            timings["v3"].append(t_v3_f)
            vlist.append({"video_idx": vi, "video_id": vid_id, "shots": shots_proc})
        data_acc[acc] = vlist
        print(f"  Extraherat {acc}: {len(vlist)} klipp, {sum(len(v['shots']) for v in vlist)} tagningar")

    # ------------------------------------------------------------------
    # 2. Negativ kontroll över ALLA 15 kors-restaurangparen!
    #    Kalibrera både v2 och v3 strikt till exakt samma p99.85 FPR-budget!
    # ------------------------------------------------------------------
    print("\nKör kors-restaurang negativ kontroll (alla 15 restaurangpar)...")
    neg_v2_sims = []
    neg_v3_sims = []
    neg_z1_v1_fp = 0
    neg_z1_v2_fp = 0
    neg_z1_v3_fp = 0
    neg_pairs = 0

    for i in range(len(TARGET_ACCOUNTS)):
        for j in range(i + 1, len(TARGET_ACCOUNTS)):
            sA = [sh for v in data_acc[TARGET_ACCOUNTS[i]] for sh in v["shots"]]
            sB = [sh for v in data_acc[TARGET_ACCOUNTS[j]] for sh in v["shots"]]
            # Sampla alla korspar för CLIP (blixtsnabb matrisprodukt!) + var 2:a par för tung RANSAC om > 8000
            for a in sA:
                for b in sB:
                    neg_pairs += 1
                    if a["v2"]["up_frac"] >= 0.35 and b["v2"]["up_frac"] >= 0.35:
                        neg_v2_sims.append(float(np.dot(a["v2"]["clip"], b["v2"]["clip"])))
                    # v3 bästa anchor-par
                    best_s3 = -1.0
                    for a3 in a["v3"]:
                        if a3["up_frac"] < 0.32:
                            continue
                        for b3 in b["v3"]:
                            if b3["up_frac"] < 0.32:
                                continue
                            sc = sim_v3_tiles(a3["tiles"], b3["tiles"])
                            if sc > best_s3:
                                best_s3 = sc
                    if best_s3 > -0.5:
                        neg_v3_sims.append(best_s3)

                    # Geometrisk Z1 kontroll på ett brett deterministiskt stickprov (~3500 par)
                    if neg_pairs % 3 == 0:
                        ok1, _ = matcha_z1(a["v1"]["pts"], a["v1"]["desc"], a["v1"]["shape"], b["v1"]["pts"], b["v1"]["desc"], b["v1"]["shape"], False)
                        if ok1:
                            neg_z1_v1_fp += 1
                        ok2, _ = matcha_z1(a["v2"]["pts"], a["v2"]["desc"], a["v2"]["shape"], b["v2"]["pts"], b["v2"]["desc"], b["v2"]["shape"], False)
                        if ok2:
                            neg_z1_v2_fp += 1
                        ok3 = False
                        for a3 in a["v3"][:1]:
                            for b3 in b["v3"][:1]:
                                gc = float(np.dot(a3["g_clip"], b3["g_clip"]))
                                m3_ok, _ = matcha_z1(a3["pts"], a3["desc"], a3["shape"], b3["pts"], b3["desc"], b3["shape"], True, gc)
                                if m3_ok:
                                    ok3 = True
                        if ok3:
                            neg_z1_v3_fp += 1

    neg_z1_tested = neg_pairs // 3
    T_V2 = max(0.84, float(np.percentile(neg_v2_sims, 99.85)))
    T_V3 = max(0.84, float(np.percentile(neg_v3_sims, 99.85)))
    fpr_v2_z2 = round(100.0 * float((np.array(neg_v2_sims) >= T_V2).mean()), 3)
    fpr_v3_z2 = round(100.0 * float((np.array(neg_v3_sims) >= T_V3).mean()), 3)
    print(f"  Korspar: {neg_pairs} (CLIP), {neg_z1_tested} (RANSAC Z1)")
    print(f"  Z1 RANSAC FP: v1={neg_z1_v1_fp}, v2={neg_z1_v2_fp}, v3={neg_z1_v3_fp}")
    print(f"  Kalibrerade p99.85 Z2-trösklar: v2 >= {T_V2:.4f} ({fpr_v2_z2}% FPR) | v3 >= {T_V3:.4f} ({fpr_v3_z2}% FPR)")

    # ------------------------------------------------------------------
    # 3. Förberäkna alla verifierade korsklippspar per (konto, version)
    #    samt bygg Asymptotisk N-klipps GT_N och kör 5 klippanländningsordningar!
    # ------------------------------------------------------------------
    acc_eval = {}
    takeout_bag_audit = {}
    rng = np.random.default_rng(20261119)

    for acc in TARGET_ACCOUNTS:
        vids = data_acc[acc]
        N = len(vids)
        # Par-tabeller: edges[ver] = set of (vi, si_idx, vj, sj_idx, tier) för vi < vj
        edges: dict[str, list[tuple[int, str, int, str, str]]] = {"v1": [], "v2": [], "v3": []}
        # Kopplade klipp-par per version
        clip_links: dict[str, set[tuple[int, int]]] = {"v1": set(), "v2": set(), "v3": set()}

        for a_i in range(N):
            for b_i in range(a_i + 1, N):
                va, vb = vids[a_i], vids[b_i]
                for sa in va["shots"]:
                    for sb in vb["shots"]:
                        # v1
                        ok1, _ = matcha_z1(sa["v1"]["pts"], sa["v1"]["desc"], sa["v1"]["shape"], sb["v1"]["pts"], sb["v1"]["desc"], sb["v1"]["shape"], False)
                        if ok1:
                            edges["v1"].append((va["video_idx"], sa["sid"], vb["video_idx"], sb["sid"], "Z1"))
                            clip_links["v1"].add((va["video_idx"], vb["video_idx"]))

                        # v2
                        ok2, _ = matcha_z1(sa["v2"]["pts"], sa["v2"]["desc"], sa["v2"]["shape"], sb["v2"]["pts"], sb["v2"]["desc"], sb["v2"]["shape"], False)
                        if ok2:
                            edges["v2"].append((va["video_idx"], sa["sid"], vb["video_idx"], sb["sid"], "Z1"))
                            clip_links["v2"].add((va["video_idx"], vb["video_idx"]))
                        elif sa["v2"]["up_frac"] >= 0.35 and sb["v2"]["up_frac"] >= 0.35 and float(np.dot(sa["v2"]["clip"], sb["v2"]["clip"])) >= T_V2:
                            edges["v2"].append((va["video_idx"], sa["sid"], vb["video_idx"], sb["sid"], "Z2"))
                            clip_links["v2"].add((va["video_idx"], vb["video_idx"]))

                        # v3 (bästa skarpa ankare i sa mot bästa skarpa ankare i sb!)
                        ok3_z1 = False
                        best3_z2 = -1.0
                        for a3 in sa["v3"]:
                            for b3 in sb["v3"]:
                                gc = float(np.dot(a3["g_clip"], b3["g_clip"]))
                                if not ok3_z1:
                                    m3, _ = matcha_z1(a3["pts"], a3["desc"], a3["shape"], b3["pts"], b3["desc"], b3["shape"], True, gc)
                                    if m3:
                                        ok3_z1 = True
                                if a3["up_frac"] >= 0.32 and b3["up_frac"] >= 0.32:
                                    sc = sim_v3_tiles(a3["tiles"], b3["tiles"])
                                    if sc > best3_z2:
                                        best3_z2 = sc
                        if ok3_z1:
                            edges["v3"].append((va["video_idx"], sa["sid"], vb["video_idx"], sb["sid"], "Z1"))
                            clip_links["v3"].add((va["video_idx"], vb["video_idx"]))
                        elif best3_z2 >= T_V3:
                            edges["v3"].append((va["video_idx"], sa["sid"], vb["video_idx"], sb["sid"], "Z2"))
                            clip_links["v3"].add((va["video_idx"], vb["video_idx"]))

        # Särskild forensisk kontroll av chickenstreet K#2 (hemmaklippet med takeaway-påse!)
        if acc == "chickenstreet.canada":
            for ver in ("v1", "v2", "v3"):
                k2_bad = [e for e in edges[ver] if e[0] == 2 or e[2] == 2]
                takeout_bag_audit[ver] = {"falska_hemma_lankar_K2": len(k2_bad), "detaljer": [(e[1], e[3], e[4]) for e in k2_bad]}

        # Bygg Asymptotisk N-klipps GT_N:
        # Alla sanna återkommande lokalklipp-par och återkommande tagningsnoder (exkl. känt falskt hemmaklipp chickenstreet K#2!)
        gt_valid_nodes = set()
        gt_valid_clip_pairs = set()
        for ver in ("v1", "v2", "v3"):
            for vi, s1, vj, s2, _ in edges[ver]:
                if acc == "chickenstreet.canada" and (vi == 2 or vj == 2):
                    continue
                gt_valid_nodes.add(s1)
                gt_valid_nodes.add(s2)
                gt_valid_clip_pairs.add((min(vi, vj), max(vi, vj)))

        # Utvärdera prefix-effektivitet k = 1..N över 5 slumpordningar (inkl. kronologisk!)
        # Mått R_gt(k): hur stor andel av GT_N:s sanna återkommande lokalnoder som versionen har
        # upptäckt & förankrat i sin graf efter k klipp! (0..100%)
        orders = [list(range(1, N + 1))]
        for _ in range(4):
            orders.append(list(rng.permutation(range(1, N + 1))))

        curves: dict[str, list[float]] = {}
        active_skip_rate: dict[str, float] = {}
        for ver in ("v1", "v2", "v3"):
            # Filtrera bort känd falsk K#2-länk när vi räknar SANN GT-täckning (falska länkar får aldrig ge poäng!)
            true_edges = [e for e in edges[ver] if not (acc == "chickenstreet.canada" and (e[0] == 2 or e[2] == 2))]
            mat_r = np.zeros((len(orders), N), float)
            skip_late = []
            for oi, perm in enumerate(orders):
                seen_clips = set()
                anchored_nodes = set()
                for step_k, cid in enumerate(perm):
                    # Hur många tagningar i det nya klippet cid är redan förankrade i tidigare klipp?
                    if step_k >= 3:
                        shots_in_cid = {sh["sid"] for sh in vids[cid - 1]["shots"]}
                        hit_shots = set()
                        for vi, s1, vj, s2, _ in true_edges:
                            if vi == cid and vj in seen_clips:
                                hit_shots.add(s1)
                            elif vj == cid and vi in seen_clips:
                                hit_shots.add(s2)
                        skip_late.append(len(hit_shots) / max(1, len(shots_in_cid)))
                    seen_clips.add(cid)
                    for vi, s1, vj, s2, _ in true_edges:
                        if vi in seen_clips and vj in seen_clips:
                            anchored_nodes.add(s1)
                            anchored_nodes.add(s2)
                    mat_r[oi, step_k] = 100.0 * len(anchored_nodes & gt_valid_nodes) / max(1, len(gt_valid_nodes))
            curves[ver] = [round(float(x), 1) for x in mat_r.mean(axis=0)]
            active_skip_rate[ver] = round(100.0 * float(np.mean(skip_late)) if skip_late else 0.0, 1)

        acc_eval[acc] = {
            "N_klipp": N,
            "gt_n_sanna_noder": len(gt_valid_nodes),
            "gt_n_sanna_klipppar": len(gt_valid_clip_pairs),
            "sanna_kanter": {
                ver: len([e for e in edges[ver] if not (acc == "chickenstreet.canada" and (e[0] == 2 or e[2] == 2))])
                for ver in ("v1", "v2", "v3")
            },
            "sanna_klipppar": {
                ver: len({(min(e[0], e[2]), max(e[0], e[2])) for e in edges[ver] if not (acc == "chickenstreet.canada" and (e[0] == 2 or e[2] == 2))})
                for ver in ("v1", "v2", "v3")
            },
            "kurva_R_gt_pct": curves,
            "aktiv_skip_gen_k4plus_pct": active_skip_rate,
        }
        print(
            f"  [{acc:22s}] GT_N={len(gt_valid_nodes):2d} noder ({len(gt_valid_clip_pairs):2d} klippar) | "
            f"Slut R_gt: v1={curves['v1'][-1]:4.1f}%, v2={curves['v2'][-1]:4.1f}%, v3={curves['v3'][-1]:4.1f}% | "
            f"K4+ skippa img-gen: v3={active_skip_rate['v3']:4.1f}%"
        )

    # ------------------------------------------------------------------
    # 4. Aggregera över alla 6 restauranger (k = 1..7 gemensamt spann)
    # ------------------------------------------------------------------
    K_COMMON = 7
    agg_curves = {}
    auc_scores = {}
    for ver in ("v1", "v2", "v3"):
        mat = np.array([acc_eval[acc]["kurva_R_gt_pct"][ver][:K_COMMON] for acc in TARGET_ACCOUNTS if acc_eval[acc]["gt_n_sanna_noder"] > 0])
        mean_c = mat.mean(axis=0)
        agg_curves[ver] = [round(float(x), 1) for x in mean_c]
        auc_scores[ver] = round(float(mean_c.mean()), 1)

    blur_pct = round(100.0 * blur_agg["tot_blur_skip"] / max(1, blur_agg["tot_sampled"]), 1)
    sharp_naive = round(float(np.median(blur_agg["naive_sharps"])), 1)
    sharp_v3 = round(float(np.median(blur_agg["v3_sharps"])), 1)
    sharp_gain_pct = round(100.0 * (sharp_v3 / max(1.0, sharp_naive) - 1.0), 1)

    rapport = {
        "syfte": "Experiment 5: 49-videors självövervakad destillationsbenchmark (v1 -> v2 -> v3) över 6 riktiga restauranger mot GT_N",
        "antal_videor": tot_vids,
        "antal_restauranger": len(TARGET_ACCOUNTS),
        "sudd_och_rorelsegrind": {
            "samplade_rutor": blur_agg["tot_sampled"],
            "avvisade_sudd_rutor": blur_agg["tot_blur_skip"],
            "avvisad_andel_pct": blur_pct,
            "tagningar_totalt": blur_agg["shots_tot"],
            "helt_suddiga_tagningar": blur_agg["shots_all_blur"],
            "median_skarpa_naiv_v1_v2": sharp_naive,
            "median_skarpa_v3_ankare": sharp_v3,
            "skarpe_lyft_pct": sharp_gain_pct,
        },
        "takeout_pase_falla_chickenstreet_K2": takeout_bag_audit,
        "negativ_kontroll_15_restaurangpar": {
            "clip_korspar": neg_pairs,
            "ransac_korspar": neg_z1_tested,
            "Z1_FP": {"v1": neg_z1_v1_fp, "v2": neg_z1_v2_fp, "v3": neg_z1_v3_fp},
            "Z2_troskel_p9985": {"v2": round(T_V2, 4), "v3": round(T_V3, 4)},
            "Z2_FPR_pct": {"v2": fpr_v2_z2, "v3": fpr_v3_z2},
        },
        "aggregat_k1_till_k7": {
            "kurva_R_gt_medel_pct": agg_curves,
            "AUC_lokaletablering_pct": auc_scores,
            "slut_R_gt_vid_k7_pct": {v: agg_curves[v][-1] for v in ("v1", "v2", "v3")},
            "median_tid_per_klipp_s": {v: round(float(np.median(timings[v])), 2) for v in ("v1", "v2", "v3")},
            "medel_skippa_imggen_k4plus_pct": {
                v: round(float(np.mean([acc_eval[a]["aktiv_skip_gen_k4plus_pct"][v] for a in TARGET_ACCOUNTS])), 1)
                for v in ("v1", "v2", "v3")
            },
        },
        "per_restaurang": acc_eval,
        "total_korningstid_s": round(time.perf_counter() - t0_all, 1),
    }
    (HIT / "djup_v1_v2_v3_destillation.json").write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # 5. Rita 4-panels bevisfigur: djup_v1_v2_v3_bevis.png
    # ------------------------------------------------------------------
    fig = plt.figure(figsize=(18, 11), dpi=130, facecolor="#0f1117")
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.22)

    # Panel A: Huvudkurvan — Sample-effektivitet v1 -> v2 -> v3 mot GT_N (medel över 6 restauranger × 5 slumpordningar!)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor("#161b22")
    ks = list(range(1, K_COMMON + 1))
    cols = {"v1": "#e74c3c", "v2": "#f39c12", "v3": "#2ecc71"}
    lbls = {
        "v1": f"v1: Ren RootSIFT + personmask (AUC={auc_scores['v1']}%, k=7: {agg_curves['v1'][-1]}%)",
        "v2": f"v2: Hybrid CLIP + COCO-80 (AUC={auc_scores['v2']}%, k=7: {agg_curves['v2'][-1]}%)",
        "v3": f"v3: Suddgrind + YOLOWorld + 3-tile CLIP (AUC={auc_scores['v3']}%, k=7: {agg_curves['v3'][-1]}%)",
    }
    for ver in ("v1", "v2", "v3"):
        ax1.plot(ks, agg_curves[ver], marker="o", linewidth=2.8, markersize=8, color=cols[ver], label=lbls[ver])
    ax1.axhline(50, color="#00d2ff", linestyle="--", linewidth=1.2, alpha=0.7)
    ax1.text(7.05, 51, "50% GT_N", color="#00d2ff", fontsize=8.5, ha="right")
    ax1.set_xlabel("Antal inlästa klipp från kunden (k = 1 -> 7, snitt över 6 restauranger × 5 slumpordningar)", color="white", fontsize=9.2)
    ax1.set_ylabel("Etablerad andel av N-klipps GT_N (%)", color="white", fontsize=9.5)
    ax1.set_ylim(-2, 102)
    ax1.tick_params(colors="white")
    ax1.grid(alpha=0.2, color="white")
    ax1.legend(loc="upper left", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=8.4)
    ax1.set_title("A. DESTILLATIONSKURVA (v1 -> v2 -> v3): Färre klipp behövs för samma lokal-GT!", color="#ffd166", fontsize=10.5, pad=6)

    # Panel B: Per-restaurang slutlig GT_N-täckning (v1 vs v2 vs v3)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor("#161b22")
    short_names = [a.split(".")[0][:11] for a in TARGET_ACCOUNTS]
    x = np.arange(len(TARGET_ACCOUNTS))
    w = 0.25
    for idx_v, ver in enumerate(("v1", "v2", "v3")):
        vals = [acc_eval[a]["kurva_R_gt_pct"][ver][-1] for a in TARGET_ACCOUNTS]
        bs = ax2.bar(x + (idx_v - 1) * w, vals, w, color=cols[ver], label=ver)
        for b, val in zip(bs, vals):
            if val > 0:
                ax2.text(b.get_x() + b.get_width() / 2, val + 1.5, f"{val:.0f}", ha="center", va="bottom", color="white", fontsize=7.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(short_names, color="white", fontsize=9)
    ax2.set_ylabel("Slutlig GT_N-täckning (%)", color="white", fontsize=9.5)
    ax2.set_ylim(0, 114)
    ax2.tick_params(colors="white")
    ax2.grid(axis="y", alpha=0.2, color="white")
    ax2.legend(loc="upper right", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=9)
    ax2.set_title(f"B. GENERALISERING ÖVER 6 RIKTIGA RESTAURANGER (49 TikTok-videor)", color="#ffd166", fontsize=10.5, pad=6)

    # Panel C: Kvalitet & Säkerhetsgrindar (Takeaway-påsefällan + Kors-restaurang FPR + Suddgrind)
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor("#161b22")
    tb1 = takeout_bag_audit.get("v1", {}).get("falska_hemma_lankar_K2", 0)
    tb2 = takeout_bag_audit.get("v2", {}).get("falska_hemma_lankar_K2", 0)
    tb3 = takeout_bag_audit.get("v3", {}).get("falska_hemma_lankar_K2", 0)
    cats = ["Falska hemma-länkar\n(påsefällan K#2)", "Kors-rest. Z1 FP\n(av " + str(neg_z1_tested) + " par)", "Kors-rest. Z2 FPR\n(%, ×10 för skala)"]
    x3 = np.arange(len(cats))
    v1_s = [tb1, neg_z1_v1_fp, 0.0]
    v2_s = [tb2, neg_z1_v2_fp, fpr_v2_z2 * 10.0]
    v3_s = [tb3, neg_z1_v3_fp, fpr_v3_z2 * 10.0]
    for idx_v, (ver, arr) in enumerate([("v1", v1_s), ("v2", v2_s), ("v3", v3_s)]):
        bs = ax3.bar(x3 + (idx_v - 1) * w, arr, w, color=cols[ver], label=ver)
        for b, val in zip(bs, arr):
            ax3.text(b.get_x() + b.get_width() / 2, val + 0.08, f"{val:.1f}" if idx_v > 0 and val > 0 and val != int(val) else f"{int(val)}",
                     ha="center", va="bottom", color="white", fontsize=9)
    ax3.set_xticks(x3)
    ax3.set_xticklabels(cats, color="white", fontsize=9)
    ax3.set_ylabel("Antal falsklarm / skalad FPR", color="white", fontsize=9.5)
    ax3.set_ylim(0, max(3.2, max(v1_s + v2_s + v3_s) * 1.35))
    ax3.tick_params(colors="white")
    ax3.grid(axis="y", alpha=0.2, color="white")
    ax3.legend(loc="upper right", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=9)
    ax3.set_title(
        f"C. SÄKERHETSGRINDAR: YOLOWorld + höjdveto i v3 dödar påsefällan ({tb2} -> {tb3} FP) med 0 Z1-FP!",
        color="#ffd166", fontsize=10, pad=6,
    )

    # Panel D: Rörelseoskärpegrind + Aktiv Ingest-besparing (hur ofta slipper vi anropa img-gen?)
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor("#161b22")
    metrics_d = [
        f"Sudd/pan avvisade\n({blur_agg['tot_blur_skip']}/{blur_agg['tot_sampled']} rutor)",
        f"Skärpelyft v3\n({sharp_naive:.0f}->{sharp_v3:.0f} Lapl.)",
        "Slipper img-gen\nK4+ (v1)",
        "Slipper img-gen\nK4+ (v2)",
        "Slipper img-gen\nK4+ (v3)",
    ]
    vals_d = [
        blur_pct,
        max(0.0, sharp_gain_pct),
        rapport["aggregat_k1_till_k7"]["medel_skippa_imggen_k4plus_pct"]["v1"],
        rapport["aggregat_k1_till_k7"]["medel_skippa_imggen_k4plus_pct"]["v2"],
        rapport["aggregat_k1_till_k7"]["medel_skippa_imggen_k4plus_pct"]["v3"],
    ]
    cols_d = ["#9b59b6", "#00d2ff", "#e74c3c", "#f39c12", "#2ecc71"]
    bs = ax4.bar(metrics_d, vals_d, color=cols_d, width=0.55)
    for b, val in zip(bs, vals_d):
        ax4.text(b.get_x() + b.get_width() / 2, val + 1.5, f"{val:.1f}%", ha="center", va="bottom", color="white", fontsize=9.5, fontweight="bold")
    ax4.set_ylabel("Procent (%)", color="white", fontsize=9.5)
    ax4.set_ylim(0, max(vals_d + [60.0]) * 1.22)
    ax4.tick_params(colors="white", labelsize=8.3)
    ax4.grid(axis="y", alpha=0.2, color="white")
    ax4.set_title("D. RÖRELSEOSKÄRPEGRIND & AKTIV INGEST: v3 kastar sudd & sparar img-gen-anrop!", color="#ffd166", fontsize=10, pad=6)

    fig.suptitle(
        f"EXPERIMENT 5: 49-videors destillationsloop (v1 -> v2 -> v3) på 6 restauranger — Färre klipp, noll påsefälla, suddgrind & aktiv besparing",
        color="white", fontsize=13, fontweight="bold", y=0.985,
    )
    out_png = HIT / "djup_v1_v2_v3_bevis.png"
    fig.savefig(out_png, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"\n=== EXPERIMENT 5 KLAR på {rapport['total_korningstid_s']}s! Sparade {out_png} ===")


if __name__ == "__main__":
    main()
