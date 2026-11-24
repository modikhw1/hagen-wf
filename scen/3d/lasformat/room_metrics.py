#!/usr/bin/env python3
"""Robust tidsstabilitet för befintliga MoGe-djupkartor."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent
SETS = {
    "original": ROOT.parent / "ingest" / "ut" / "notan-tagningar" / "S4",
    "A": ROOT / "ut" / "A",
    "B": ROOT / "ut" / "B",
    "C": ROOT / "ut" / "C",
}


def metrics(folder: Path) -> dict:
    files = sorted((folder / "rum" / "depth").glob("[0-9][0-9][0-9][0-9].npz"))
    masks = np.load(folder / "masker.npy")
    ds, excluded = [], []
    for p in files:
        frame = int(p.stem)
        with np.load(p) as z:
            d = np.asarray(z["depth"], float)
        h0, w0 = d.shape
        # 240 px bredd räcker för ett robust stabilitetsmått och håller
        # percentilberäkningen liten även för originalets 960p-kartor.
        w = min(240, w0)
        h = max(1, round(h0 * w / w0))
        d = cv2.resize(d, (w, h), interpolation=cv2.INTER_NEAREST)
        m = cv2.resize(masks[frame].astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
        valid = np.isfinite(d) & (d > 0) & ~m
        med = np.median(d[valid])
        ds.append(d / med)
        excluded.append(m | ~np.isfinite(d) | (d <= 0))
    stack = np.stack(ds)
    bad = np.any(np.stack(excluded), axis=0)
    spread = np.nanpercentile(stack, 90, axis=0) - np.nanpercentile(stack, 10, axis=0)
    ok = ~bad & np.isfinite(spread)
    h = spread.shape[0]
    lower = ok.copy()
    lower[: int(h * 0.60)] = False

    def summary(sel: np.ndarray) -> dict:
        v = spread[sel] * 100.0
        return {
            "pixels": int(len(v)),
            "median_percent_of_frame_median_depth": float(np.median(v)),
            "p90_percent_of_frame_median_depth": float(np.percentile(v, 90)),
            "p95_percent_of_frame_median_depth": float(np.percentile(v, 95)),
        }

    return {
        "frames": len(files),
        "all_background": summary(ok),
        "lower_40_percent_background": summary(lower),
    }


def main() -> None:
    out = {
        "method": (
            "For each of 15 static-camera MoGe depth maps, divide depth by the "
            "background median. Exclude any pixel occupied by a person or invalid "
            "in any sampled frame. Report per-pixel p90-p10 temporal spread."
        ),
        "sets": {name: metrics(folder) for name, folder in SETS.items()},
    }
    (ROOT / "rum_matning.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
