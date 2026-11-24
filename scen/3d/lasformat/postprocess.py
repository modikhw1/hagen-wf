"""Mappa 16-fps-generering exakt till S4:s 30-fps-tidsbas och återlägg källpixlar."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2] / "scen/3d/ingest/ut/notan-tagningar/klipp/S4.mp4"


def read_video(path: Path) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        raise RuntimeError(f"Tom video: {path}")
    return frames


def write_video(path: Path, frames: list[np.ndarray], fps: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"Kunde inte skriva {path}")
    for frame in frames:
        writer.write(frame)
    writer.release()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", nargs="+")
    parser.add_argument("--in-dir", default=str(HERE / "in"))
    parser.add_argument("--ut", default=str(HERE / "genererat"))
    args = parser.parse_args()
    in_dir, out_dir = Path(args.in_dir), Path(args.ut)
    source = read_video(SOURCE)
    masks = np.load(in_dir / "preserve_all_30fps.npz")["mask"]
    timing = json.loads((in_dir / "timing.json").read_text(encoding="utf-8"))
    tr = timing["transform"]
    scale, x0, y0 = tr["scale"], tr["x0"], tr["y0"]
    placed_w, placed_h = tr["placed_width"], tr["placed_height"]

    source_canvas = []
    alpha = []
    for frame, mask in zip(source, masks):
        canvas = np.zeros((832, 480, 3), np.uint8)
        canvas[y0:y0 + placed_h, x0:x0 + placed_w] = cv2.resize(frame, (placed_w, placed_h), interpolation=cv2.INTER_AREA)
        source_canvas.append(canvas)
        # Exakt kärna, mjuk 3-pixelskant för att undvika en synlig klippkant.
        a = cv2.GaussianBlur(mask, (7, 7), 0).astype(np.float32) / 255.0
        alpha.append(a[..., None])

    manifest = []
    for raw_name in args.raw:
        raw = Path(raw_name)
        generated = read_video(raw)
        if len(generated) < 45:
            raise RuntimeError(f"För få rutor i {raw}: {len(generated)}")
        out_frames = []
        for i in range(len(source)):
            pos = (i / 30.0) * 16.0
            lo = min(int(np.floor(pos)), len(generated) - 1)
            hi = min(lo + 1, len(generated) - 1)
            f = pos - lo
            background = cv2.addWeighted(generated[lo], 1.0 - f, generated[hi], f, 0)
            a = alpha[i]
            composite = np.clip(source_canvas[i].astype(np.float32) * a + background.astype(np.float32) * (1.0 - a), 0, 255).astype(np.uint8)
            out_frames.append(composite)
        name = raw.stem.replace("_raw_16fps", "")
        out = out_dir / name / "video_30fps.mp4"
        write_video(out, out_frames, 30.0)
        still_dir = out.parent / "stillbilder"
        still_dir.mkdir(parents=True, exist_ok=True)
        for idx in (0, 30, 45, 60, 84):
            cv2.imwrite(str(still_dir / f"ruta_{idx:04d}.jpg"), out_frames[idx])
        manifest.append({"id": name, "video": str(out), "frames": len(out_frames), "fps": 30.0, "transform": tr})
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()

