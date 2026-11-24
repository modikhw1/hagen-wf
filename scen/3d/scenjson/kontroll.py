"""Komponera kontrollbilder och mät MHR-silhuett mot ingestens personmask."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

HIT = Path(__file__).resolve().parent
ROOT = HIT.parents[2]


def skriv_json(path, data):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def en(key, local):
    src = cv2.imread(str(ROOT / f"scen/3d/lasformat/luma-paket/indata/bild/{key}.png"), cv2.IMREAD_COLOR)
    layer = cv2.imread(str(HIT / f"_tmp/kontroll_lager_{key}.png"), cv2.IMREAD_UNCHANGED)
    if src is None or layer is None or layer.shape[2] != 4:
        raise RuntimeError(f"Saknar kontrollunderlag för {key}")
    a = (layer[:, :, 3:4].astype(np.float32) / 255.0) * 0.62
    comp = src.astype(np.float32) * (1.0 - a) + layer[:, :, :3].astype(np.float32) * a
    cv2.imwrite(str(HIT / f"kontroll_{key}.jpg"), np.clip(comp, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])

    render = cv2.imread(str(HIT / f"_tmp/silhuett_{key}.png"), cv2.IMREAD_GRAYSCALE) > 24
    masks = np.load(ROOT / f"scen/3d/ingest/ut/notan-tagningar/{key}/masker.npy")
    source = cv2.resize(masks[local].astype(np.uint8), (576, 1024), interpolation=cv2.INTER_NEAREST) > 0
    personer = json.loads((ROOT / f"scen/3d/ingest/ut/notan-tagningar/{key}/personer.json").read_text(encoding="utf-8"))
    x0, y0, x1, y1 = personer["1"][str(local)]
    # Maskfilen är en union. Begränsa den till huvudpersonens spårbox; för S4 kan
    # några pixlar från den överlappande vänstergästen ändå finnas kvar.
    roi = np.zeros_like(source)
    roi[max(0, int(y0)):min(1024, int(np.ceil(y1))), max(0, int(x0)):min(576, int(np.ceil(x1)))] = True
    source &= roi
    render &= roi
    inter = int(np.logical_and(source, render).sum())
    union = int(np.logical_or(source, render).sum())
    iou = inter / union if union else 0.0
    recall = inter / int(source.sum()) if source.any() else 0.0
    precision = inter / int(render.sum()) if render.any() else 0.0
    return {
        "keyframe": key,
        "lokal_ruta": local,
        "silhuett_iou": round(iou, 4),
        "masktackning_recall": round(recall, 4),
        "render_precision": round(precision, 4),
        "maskkommentar": "Ingestens boolska mask är en personunion; mätningen begränsas till ingest-ID 1:s bbox.",
    }


if __name__ == "__main__":
    out = [en("S1", 36), en("S4", 42)]
    skriv_json(HIT / "kontroll_matt.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=2))
