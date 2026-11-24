"""Mät kameraavstånd, kroppsvridning och posedrift mot S1/S4-originalet.

En bild:
  scen/.venv/Scripts/python.exe scen/3d/scenjson/matt_andring.py BILD S1

Kalibrering (båda ändrade blockouterna i ett Modal-anrop):
  scen/.venv/Scripts/python.exe scen/3d/scenjson/matt_andring.py --kalibrera

Bild skalas till 576x1024. YOLO väljer största person och SAM 3D Body körs
genom ingest/modal_sam3db.py med fokal 1024 px, precis som poang.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from scipy.spatial.transform import Rotation

HIT = Path(__file__).resolve().parent
REPO = HIT.parents[2]
SCEN = REPO / "scen"
PYTHON = SCEN / ".venv/Scripts/python.exe"
MODAL = SCEN / ".venv/Scripts/modal.exe"
SAM_SCRIPT = SCEN / "3d/ingest/modal_sam3db.py"
YOLO_MODEL = SCEN / "py/modeller/yolo11n-pose.pt"
W, H, FOKAL = 576, 1024, 1024.0
PRIS_USD_PER_GPU_S_KONSERVATIV = 0.00110
MAX_BUDGET_USD = 2.0


def skriv_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def las_budget():
    p = HIT / "budget.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {
        "max_usd": MAX_BUDGET_USD,
        "metod": "Konservativ uppskattning: modal_sam3db timing.total_s × 0,00110 USD/GPU-s; faktisk Modal-faktura kan avvika.",
        "korningar": [],
        "uppskattad_summa_usd": 0.0,
    }


def logga_budget(namn, timing, wall_s, status="klar"):
    b = las_budget()
    gpu_s = float(timing.get("total_s", wall_s))
    cost = gpu_s * PRIS_USD_PER_GPU_S_KONSERVATIV
    b["korningar"].append({
        "namn": namn,
        "status": status,
        "jobb": timing.get("jobb"),
        "sam_total_s": round(gpu_s, 3),
        "vaggtid_s": round(wall_s, 3),
        "uppskattad_usd": round(cost, 4),
        "prisgrund_usd_per_gpu_s": PRIS_USD_PER_GPU_S_KONSERVATIV,
    })
    b["uppskattad_summa_usd"] = round(sum(x.get("uppskattad_usd", 0) for x in b["korningar"]), 4)
    skriv_json(HIT / "budget.json", b)
    return b


def procrustes(A, B, skala=False):
    a, b = A - A.mean(0), B - B.mean(0)
    U, S, Vt = np.linalg.svd(a.T @ b)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1
        R = U @ Vt
    s = S.sum() / (a ** 2).sum() if skala else 1.0
    return float(np.linalg.norm(s * a @ R - b, axis=1).mean())


def original_npz(key):
    return HIT.parent / f"lasformat/luma-paket/poang/kropp/p/{0 if key == 'S1' else 1:04d}.npz"


def mat_rotation(out, orig):
    r0 = Rotation.from_rotvec(np.asarray(orig["global_rot"], float))
    r1 = Rotation.from_rotvec(np.asarray(out["global_rot"], float))
    rel = r1 * r0.inv()
    rv = rel.as_rotvec()
    # SAM:s kamerarum har y NEDÅT (OpenCV). Positiv rotation runt +y ned är moturs sett
    # ovanifrån = mot personens egen vänstra sida, därav minustecknet. Kontrollerat 11 nov
    # mot axeldjupen i S4-guiden: vänster axel kom ~13 cm närmare = ~20° åt egen höger.
    return float(-math.degrees(rv[1])), float(math.degrees(np.linalg.norm(rv)))


def analysera(npz_path: Path, key: str, bild: str, kalla="SAM 3D Body"):
    scene = json.loads((HIT / f"{key}_andrad.json").read_text(encoding="utf-8"))
    target_dist = float(scene["andring"]["avstandsmal"]["forandring_m"])
    target_turn = float(scene["andring"]["huvudperson"]["rotation_grader"])
    orig = np.load(original_npz(key))
    if not npz_path.exists():
        return {"keyframe": key, "bild": bild, "fel": "SAM gav ingen kropp", "dom": "följde inte"}
    out = np.load(npz_path)
    d0 = float(np.linalg.norm(orig["pred_cam_t"]))
    d1 = float(np.linalg.norm(out["pred_cam_t"]))
    dd = d1 - d0
    turn, rel_total = mat_rotation(out, orig)
    drift_cm = 100.0 * procrustes(out["pred_keypoints_3d"][:21], orig["pred_keypoints_3d"][:21], False)
    dist_err = abs(dd - target_dist)
    turn_err = abs(turn - target_turn)
    if dist_err <= 0.25 and turn_err <= 8 and drift_cm <= 5:
        verdict = "följde"
    elif dist_err <= 0.50 and turn_err <= 15 and drift_cm <= 10:
        verdict = "delvis"
    else:
        verdict = "följde inte"
    return {
        "keyframe": key,
        "bild": bild,
        "kalla": kalla,
        "sam_avstand_original_m": round(d0, 4),
        "sam_avstand_utfall_m": round(d1, 4),
        "uppmatt_avstandsforandring_m": round(dd, 4),
        "beordrad_geometrisk_avstandsforandring_m": round(target_dist, 4),
        "avstandsfel_m": round(dist_err, 4),
        "uppmatt_vridning_egen_hogra_grader": round(turn, 3),
        "relativ_rotation_total_grader": round(rel_total, 3),
        "beordrad_vridning_grader": target_turn,
        "vridfel_grader": round(turn_err, 3),
        "posedrift_procrustes_cm": round(drift_cm, 3),
        "dom": verdict,
    }


def forbered_bilder(items, work: Path):
    from ultralytics import YOLO

    pose = YOLO(str(YOLO_MODEL))
    video = work / "bilder.mp4"
    vw = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 30, (W, H))
    jobs, index = [], []
    for i, (path, key) in enumerate(items):
        im0 = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if im0 is None:
            raise FileNotFoundError(path)
        ratio = im0.shape[1] / im0.shape[0]
        if abs(ratio - W / H) > 0.04:
            raise ValueError(f"{path}: bildförhållandet {ratio:.3f} är inte nära 9:16")
        im = cv2.resize(im0, (W, H), interpolation=cv2.INTER_AREA if im0.shape[0] > H else cv2.INTER_CUBIC)
        vw.write(im)
        cv2.imwrite(str(work / f"{i:04d}.png"), im)
        r = pose(im, verbose=False)[0]
        if not len(r.boxes):
            index.append({"ruta": i, "keyframe": key, "bild": str(path), "yolo": "ingen person"})
            continue
        xy = r.boxes.xyxy.cpu().numpy()
        j = int(((xy[:, 2] - xy[:, 0]) * (xy[:, 3] - xy[:, 1])).argmax())
        box = [float(x) for x in xy[j]]
        jobs.append([i, key, box])
        index.append({"ruta": i, "keyframe": key, "bild": str(path), "bbox": box, "yolo_personer": int(len(r.boxes)), "yolo_konf": float(r.boxes.conf[j])})
    vw.release()
    skriv_json(work / "jobb.json", jobs)
    skriv_json(work / "index.json", index)
    return video, jobs, index


def kor_modal(video, work, namn):
    budget = las_budget()
    if float(budget.get("uppskattad_summa_usd", 0)) >= MAX_BUDGET_USD:
        raise RuntimeError("Modal-budgeten 2 USD är redan förbrukad enligt budget.json")
    out = work / "sam"
    cmd = [str(MODAL), "run", str(SAM_SCRIPT), "--klipp", str(video), "--jobb", str(work / "jobb.json"), "--ut", str(out), "--fokal", str(FOKAL)]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    t0 = time.time()
    p = subprocess.run(cmd, cwd=REPO, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True)
    wall = time.time() - t0
    (work / "modal_stdout.txt").write_text(p.stdout, encoding="utf-8", newline="\n")
    (work / "modal_stderr.txt").write_text(p.stderr, encoding="utf-8", newline="\n")
    if p.returncode:
        logga_budget(namn, {"total_s": wall, "jobb": 0}, wall, status="fel")
        raise RuntimeError(f"Modal misslyckades ({p.returncode}); se {work / 'modal_stderr.txt'}")
    timing_path = out / "timing.json"
    timing = json.loads(timing_path.read_text(encoding="utf-8")) if timing_path.exists() else {"total_s": wall}
    logga_budget(namn, timing, wall)
    return out


def originalkontroll(key):
    # Samma analysväg men samma NPZ på båda sidor: avstånd, rotation och drift
    # måste bli exakt noll innan någon bildmodell provas.
    return analysera(original_npz(key), key, f"original/{key}.png", kalla="befintlig exakt original-SAM")


def kalibrera():
    work = HIT / "matning/kalibrering"
    work.mkdir(parents=True, exist_ok=True)
    items = [(HIT / "guide/S1_blockout.png", "S1"), (HIT / "guide/S4_blockout.png", "S4")]
    video, jobs, index = forbered_bilder(items, work)
    if not jobs:
        results = [originalkontroll("S1"), originalkontroll("S4")] + [
            {"keyframe": x[1], "bild": str(x[0]), "fel": "YOLO hittade ingen person", "dom": "följde inte"} for x in items
        ]
    else:
        out = kor_modal(video, work, "guide-blockout-kalibrering-S1-S4")
        results = [originalkontroll("S1"), originalkontroll("S4")]
        for row in index:
            p = out / row["keyframe"] / f"{row['ruta']:04d}.npz"
            results.append(analysera(p, row["keyframe"], row["bild"]))
    skriv_json(HIT / "kalibrering.json", {"resultat": results, "diagnosgranser": {"foljde": {"avstand_m": 0.25, "vridning_grader": 8, "pose_cm": 5}, "delvis": {"avstand_m": 0.50, "vridning_grader": 15, "pose_cm": 10}}})
    print(json.dumps(results, ensure_ascii=False, indent=2))


def en_bild(path: Path, key: str):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    work = HIT / f"matning/{key}_{path.stem}_{digest}"
    work.mkdir(parents=True, exist_ok=True)
    video, jobs, index = forbered_bilder([(path, key)], work)
    if not jobs:
        result = {"keyframe": key, "bild": str(path), "fel": "YOLO hittade ingen person", "dom": "följde inte"}
    else:
        out = kor_modal(video, work, f"enskild-{key}-{path.name}")
        result = analysera(out / key / "0000.npz", key, str(path))
    skriv_json(work / "resultat.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bild", nargs="?", type=Path)
    ap.add_argument("keyframe", nargs="?", choices=["S1", "S4"])
    ap.add_argument("--kalibrera", action="store_true")
    a = ap.parse_args()
    if a.kalibrera:
        kalibrera()
    elif a.bild and a.keyframe:
        en_bild(a.bild.resolve(), a.keyframe)
    else:
        ap.error("ange BILD S1|S4 eller --kalibrera")


if __name__ == "__main__":
    main()
