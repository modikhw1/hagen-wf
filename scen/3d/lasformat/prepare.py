"""Förbered S4 för VACE utan att skriva utanför lasformat/.

Skapar en 49-rutors 16-fps-condition i 480x832, modellmasker och en exakt
tidskarta. Svart mask = bevara, vit = generera.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "scen/3d/ingest/ut/notan-tagningar/klipp/S4.mp4"
ORIGINAL = ROOT / "scen/3d/ingest/ut/notan-tagningar/S4"
CANVAS_W, CANVAS_H = 480, 832
SOURCE_FPS, MODEL_FPS = 30.0, 16.0
MODEL_FRAMES = 49  # 4n+1; 3,0 s med sista källrutan hållen efter 2,8 s.
PLACED_H = 650


def las_video(path: Path) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        raise RuntimeError(f"Kunde inte läsa {path}")
    return frames


def skriv_video(path: Path, frames: list[np.ndarray], fps: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"Kunde inte öppna videoutdata {path}")
    for frame in frames:
        writer.write(frame)
    writer.release()


def personmasker(frames: list[np.ndarray]) -> np.ndarray:
    """Isolera bara de två valda spåren ur den sparade maskunionen."""
    union = np.load(ORIGINAL / "masker.npy")
    tracks = json.loads((ORIGINAL / "personer.json").read_text(encoding="utf-8"))
    n, h, w = len(frames), frames[0].shape[0], frames[0].shape[1]
    out = np.zeros((n, h, w), np.uint8)
    for i in range(n):
        full = cv2.resize(union[i].astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
        chosen = np.zeros_like(full)
        for pid in ("1", "4"):
            box = tracks.get(pid, {}).get(str(i))
            if box is None:
                continue
            x0, y0, x1, y1 = box
            pad = 5
            xa, ya = max(0, int(x0) - pad), max(0, int(y0) - pad)
            xb, yb = min(w, int(np.ceil(x1)) + pad), min(h, int(np.ceil(y1)) + pad)
            chosen[ya:yb, xa:xb] |= full[ya:yb, xa:xb]
        chosen = cv2.morphologyEx(chosen, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        chosen = cv2.dilate(chosen, np.ones((5, 5), np.uint8))

        # Undertexten är inbränd över kroppen. Bevara hela texten, inte bara de
        # bokstavsdelar som råkar ligga innanför personmasken.
        bgr = frames[i]
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        text = np.zeros_like(chosen)
        band = (slice(round(h * 0.43), round(h * 0.72)), slice(round(w * 0.04), round(w * 0.96)))
        bright = ((hsv[band][..., 1] < 65) & (hsv[band][..., 2] > 205)).astype(np.uint8)
        bright = cv2.dilate(bright, np.ones((9, 9), np.uint8))
        text[band] = bright
        out[i] = np.maximum(chosen, text) * 255
    return out


def placera(frame: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    src_h, src_w = frame.shape[:2]
    scale = PLACED_H / src_h
    placed_w = int(round(src_w * scale))
    x0, y0 = (CANVAS_W - placed_w) // 2, 0
    canvas = np.full((CANVAS_H, CANVAS_W, 3), 127, np.uint8)
    resized = cv2.resize(frame, (placed_w, PLACED_H), interpolation=cv2.INTER_AREA)
    canvas[y0:y0 + PLACED_H, x0:x0 + placed_w] = resized
    preserve = np.zeros((CANVAS_H, CANVAS_W), np.uint8)
    preserve[y0:y0 + PLACED_H, x0:x0 + placed_w] = cv2.resize(
        mask, (placed_w, PLACED_H), interpolation=cv2.INTER_NEAREST
    )
    return canvas, preserve, {
        "scale": scale,
        "x0": x0,
        "y0": y0,
        "placed_width": placed_w,
        "placed_height": PLACED_H,
        "canvas_width": CANVAS_W,
        "canvas_height": CANVAS_H,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ut", default=str(HERE / "in"))
    args = parser.parse_args()
    out = Path(args.ut).resolve()
    out.mkdir(parents=True, exist_ok=True)

    frames = las_video(SOURCE)
    if len(frames) != 85 or frames[0].shape[:2] != (1024, 576):
        raise RuntimeError(f"Oväntad S4-form: {len(frames)} rutor, {frames[0].shape[:2]}")
    masks = personmasker(frames)
    all_canvas, all_preserve = [], []
    transform = None
    for frame, mask in zip(frames, masks):
        canvas, preserve, transform = placera(frame, mask)
        all_canvas.append(canvas)
        all_preserve.append(preserve)

    model_source_indices = [min(round(i * SOURCE_FPS / MODEL_FPS), len(frames) - 1) for i in range(MODEL_FRAMES)]
    condition = [all_canvas[i] for i in model_source_indices]
    preserve = np.stack([all_preserve[i] for i in model_source_indices])
    generation_mask = 255 - preserve
    skriv_video(out / "condition_16fps.mp4", condition, MODEL_FPS)
    np.savez_compressed(out / "generation_mask_16fps.npz", mask=generation_mask)
    np.savez_compressed(out / "preserve_all_30fps.npz", mask=np.stack(all_preserve))

    preview = condition[min(24, len(condition) - 1)].copy()
    overlay = np.zeros_like(preview)
    overlay[..., 2] = generation_mask[min(24, len(condition) - 1)]
    preview = cv2.addWeighted(preview, 0.72, overlay, 0.28, 0)
    cv2.imwrite(str(out / "mask_preview.jpg"), preview)

    timing = {
        "source": str(SOURCE),
        "source_fps": SOURCE_FPS,
        "source_frames": len(frames),
        "model_fps": MODEL_FPS,
        "model_frames": MODEL_FRAMES,
        "model_source_indices": model_source_indices,
        "model_times_s": [i / MODEL_FPS for i in range(MODEL_FRAMES)],
        "source_times_s": [i / SOURCE_FPS for i in model_source_indices],
        "comparison_rule": "För originalruta i används genererad bakgrund vid exakt t=i/30 s, linjärt mellan 16-fps-rutor; originalpersonerna läggs tillbaka från samma originalruta i.",
        "transform": transform,
    }
    (out / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    common = (
        "Photorealistic live-action vertical smartphone video in the same modern casual restaurant, same warm natural light. "
        "Locked stationary camera. Preserve the exact two foreground people, their faces, expressions, hands, clothes, identity, gestures and timing. "
        "Extend the view downward and complete the central young male waiter's trousers, shoes, both legs and both feet naturally planted on the floor. "
        "No additional people, no invented motion, no camera movement, no stylization, no animation, no body deformation."
    )
    jobs = [
        {
            "id": "A_01",
            "format": "A",
            "seed": 1041,
            "prompt": common + " Reconstruct a realistic tidy version of the same restaurant background with the same walls, tables, concrete ceiling and lighting.",
        },
        {
            "id": "B_01",
            "format": "B",
            "seed": 2041,
            "prompt": common + " Use a simplified realistic restaurant background: calm smooth wall and floor surfaces, clearly separated walls, floor and tables, very little clutter.",
        },
        {
            "id": "C_01",
            "format": "C",
            "seed": 3041,
            "prompt": common + " Use a simplified realistic restaurant background with calm smooth walls and tables. The floor has a clear regular square grid tile pattern in correct perspective, useful for reading scale and the floor plane.",
        },
    ]
    negative = (
        "cartoon, illustration, painting, CGI, stylized, beauty filter, face change, identity change, expression change, "
        "different gesture, different pose, duplicated person, extra person, extra limbs, missing limbs, deformed hands, "
        "floating feet, cropped feet, camera shake, camera pan, camera zoom, motion blur, clutter, subtitles, watermark"
    )
    for job in jobs:
        job.update(negative_prompt=negative, num_inference_steps=30, guidance_scale=5.0, conditioning_scale=1.0)
    (out / "jobs.json").write_text(json.dumps(jobs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"ut": str(out), "rutor": MODEL_FRAMES, "transform": transform}, ensure_ascii=False))


if __name__ == "__main__":
    main()

