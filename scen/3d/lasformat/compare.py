#!/usr/bin/env python3
"""Jämför omkodad SAM 3D Body-läsning med originalets läsning.

Alla bildpunkter från den breddade 480x832-duken mappas tillbaka till
originalets 576x1024-koordinater. Leder utanför originalbildens yta räknas
inte i driftmåttet.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
ORIG = ROOT.parent / "ingest" / "ut" / "notan-tagningar" / "S4"
SCALE = 0.634765625
X0 = 57.0
W, H = 576.0, 1024.0
FORMATS = {
    "A": {"generated_id": 1, "original_id": 1},
    "B": {"generated_id": 1, "original_id": 1},
    "C": {"generated_id": 1, "original_id": 1},
}
UPPER = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 17, 18, 19, 20])
ARMS = np.array([5, 6, 7, 8, 9, 10])


def pct(values: list[float], q: float) -> float | None:
    return float(np.percentile(values, q)) if values else None


def raw_body(folder: Path, pid: int, frame: int) -> np.ndarray | None:
    p = folder / "kropp" / str(pid) / f"{frame:04d}.npz"
    if not p.exists():
        return None
    with np.load(p) as z:
        a = np.asarray(z["pred_keypoints_2d"], dtype=float)
    return a[0] if a.ndim == 3 else a


def to_original(a: np.ndarray) -> np.ndarray:
    b = a.copy()
    b[:, 0] = (b[:, 0] - X0) / SCALE
    b[:, 1] = b[:, 1] / SCALE
    return b


def inside(a: np.ndarray) -> np.ndarray:
    return (
        np.isfinite(a).all(axis=1)
        & (a[:, 0] >= 0)
        & (a[:, 0] < W)
        & (a[:, 1] >= 0)
        & (a[:, 1] < H)
    )


def corr(a: np.ndarray, b: np.ndarray) -> float | None:
    a = np.asarray(a, float).ravel()
    b = np.asarray(b, float).ravel()
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 4 or np.std(a[ok]) < 1e-9 or np.std(b[ok]) < 1e-9:
        return None
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def sequence_metrics(folder: Path, gid: int, oid: int) -> dict:
    gp = folder / f"sekvens_{gid}.npz"
    op = ORIG / f"sekvens_{oid}.npz"
    with np.load(gp) as g, np.load(op) as o:
        gn = min(len(g["pose"]), len(o["pose"]), 85)
        gp3 = np.asarray(g["pose"][:gn, :, :3], float) / 100.0
        op3 = np.asarray(o["pose"][:gn, :, :3], float) / 100.0
        gct = np.asarray(g["cam_t"][:gn], float)
        oct_ = np.asarray(o["cam_t"][:gn], float)
        gr = gp3[:, 1, :] + gct
        or_ = op3[:, 1, :] + oct_
        gd = gr - gr[0]
        od = or_ - or_[0]
        raw = np.linalg.norm(gd - od, axis=1)
        denom = float(np.sum(gd * gd))
        scale = float(np.sum(gd * od) / denom) if denom > 1e-9 else 1.0
        aligned = np.linalg.norm(gd * scale - od, axis=1)
        gh = np.ptp(gp3[:, :, 1], axis=1)
        oh = np.ptp(op3[:, :, 1], axis=1)
    return {
        "frames": gn,
        "root_3d_displacement_error_m": {
            "median": float(np.median(raw)),
            "p95": float(np.percentile(raw, 95)),
            "max": float(np.max(raw)),
        },
        "root_3d_shape_error_after_scalar_fit_m": {
            "fit_scale": scale,
            "median": float(np.median(aligned)),
            "p95": float(np.percentile(aligned, 95)),
        },
        "raw_body_height_m": {
            "generated_median": float(np.median(gh)),
            "original_median": float(np.median(oh)),
            "difference": float(np.median(gh) - np.median(oh)),
        },
    }


def compare_one(name: str, ids: dict) -> tuple[dict, dict]:
    folder = ROOT / "ut" / name
    per_frame = []
    roots_g, roots_o = [], []
    arms_g, arms_o = [], []
    body_err, upper_err, arm_err = [], [], []
    for frame in range(85):
        o = raw_body(ORIG, ids["original_id"], frame)
        g = raw_body(folder, ids["generated_id"], frame)
        if o is None or g is None:
            continue
        g = to_original(g)
        n = min(len(o), len(g), 21)
        o, g = o[:n], g[:n]
        ok = inside(o) & inside(g)
        err = np.linalg.norm(g - o, axis=1)
        bidx = np.arange(n)[ok]
        uidx = UPPER[(UPPER < n) & ok[UPPER[UPPER < n]]]
        aidx = ARMS[(ARMS < n) & ok[ARMS[ARMS < n]]]
        bm = float(np.median(err[bidx])) if len(bidx) else np.nan
        um = float(np.median(err[uidx])) if len(uidx) else np.nan
        am = float(np.median(err[aidx])) if len(aidx) else np.nan
        body_err.append(bm)
        upper_err.append(um)
        arm_err.append(am)
        # Bildrotsbana: centrum av de giltiga överkroppslederna. Den råa
        # MHR-led 0 kan ligga utanför bild för dolda fötter och är därför
        # olämplig som 2D-ankare.
        if len(uidx):
            roots_g.append(g[uidx].mean(axis=0))
            roots_o.append(o[uidx].mean(axis=0))
        if len(aidx):
            arms_g.append(g[aidx].mean(axis=0))
            arms_o.append(o[aidx].mean(axis=0))
        per_frame.append({
            "frame": frame,
            "body_median_px": bm,
            "upper_median_px": um,
            "arms_median_px": am,
            "joints": int(len(bidx)),
        })

    rg, ro = np.asarray(roots_g), np.asarray(roots_o)
    ag, ao = np.asarray(arms_g), np.asarray(arms_o)
    root_shape = np.linalg.norm((rg - rg[0]) - (ro - ro[0]), axis=1)
    av_g = np.diff(ag, axis=0)
    av_o = np.diff(ao, axis=0)
    result = {
        "format": name,
        "identity": ids,
        "frames_compared": len(per_frame),
        "mapping": {"scale": SCALE, "canvas_x_offset": X0, "original_wh": [W, H]},
        "joint_2d_error_px": {
            "body_median": float(np.nanmedian(body_err)),
            "body_p95": pct([x for x in body_err if np.isfinite(x)], 95),
            "upper_median": float(np.nanmedian(upper_err)),
            "upper_p95": pct([x for x in upper_err if np.isfinite(x)], 95),
            "arms_median": float(np.nanmedian(arm_err)),
            "arms_p95": pct([x for x in arm_err if np.isfinite(x)], 95),
        },
        "root_2d_motion_shape_error_px": {
            "median": float(np.median(root_shape)),
            "p95": float(np.percentile(root_shape, 95)),
            "max": float(np.max(root_shape)),
        },
        "arm_velocity_correlation": corr(av_g, av_o),
        "sequence": sequence_metrics(folder, ids["generated_id"], ids["original_id"]),
    }
    return result, {"per_frame": per_frame, "rg": rg, "ro": ro}


def main() -> None:
    all_results = {}
    plot_data = {}
    for name, ids in FORMATS.items():
        result, data = compare_one(name, ids)
        all_results[name] = result
        plot_data[name] = data

    out = {
        "method": (
            "SAM 3D Body raw 2D keypoints, generated canvas inverted to the "
            "original 576x1024 image; joints outside the original image omitted. "
            "Original SAM reading is the reference, not manual ground truth."
        ),
        "results": all_results,
    }
    (ROOT / "matning.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)
    for name, data in plot_data.items():
        pf = data["per_frame"]
        axes[0].plot([x["frame"] for x in pf], [x["upper_median_px"] for x in pf], label=name)
        rg, ro = data["rg"], data["ro"]
        shape = np.linalg.norm((rg - rg[0]) - (ro - ro[0]), axis=1)
        axes[1].plot(np.arange(len(shape)), shape, label=name)
    axes[0].set(title="Drift mot original SAM-läsning", ylabel="Överkroppsleder, median px")
    axes[1].set(title="Rotbanans form mot original", xlabel="Ruta", ylabel="Fel px")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend()
    fig.savefig(ROOT / "drift.png", dpi=160)
    plt.close(fig)

    for name, result in all_results.items():
        print(name, json.dumps(result["joint_2d_error_px"], ensure_ascii=False),
              json.dumps(result["root_2d_motion_shape_error_px"], ensure_ascii=False),
              "arm_corr", result["arm_velocity_correlation"])


if __name__ == "__main__":
    main()
