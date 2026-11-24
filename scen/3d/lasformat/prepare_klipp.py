"""Generell förberedelse för format A (maskad VACE, breddad bild) på valfri ingest-tagning.
Kör: python prepare_klipp.py --tagning <ingest/ut/.../S2> --namn <id>   -> lasformat/in_klipp/<id>/
Bygger på prepare.py (S4) men tar alla spårade personer och sätter rutantal efter tagningens längd."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import cv2, numpy as np
import prepare as P

ap = argparse.ArgumentParser(); ap.add_argument('--tagning', required=True); ap.add_argument('--namn', required=True)
a = ap.parse_args()
T = Path(a.tagning).resolve(); M = json.loads((T / 'meta.json').read_text(encoding='utf-8'))
src = Path(M['kallvideo']) if 'kallvideo' in M else T.parent / 'klipp' / f'{T.name}.mp4'; fps = float(M['fps'])
ut = P.HERE / 'in_klipp' / a.namn; ut.mkdir(parents=True, exist_ok=True)
frames = P.las_video(src); frames = [cv2.resize(f, (576, 1024)) if f.shape[:2] != (1024, 576) else f for f in frames]
union = np.load(T / 'masker.npy'); tracks = json.loads((T / 'personer.json').read_text(encoding='utf-8'))
n = len(frames); h, w = 1024, 576
skala_spar = 576 / M['bredd']
masks = np.zeros((n, h, w), np.uint8)
for i in range(n):
    full = cv2.resize(union[min(i, len(union) - 1)].astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
    chosen = np.zeros_like(full)
    for pid, d in tracks.items():
        box = d.get(str(i))
        if box is None: continue
        x0, y0, x1, y1 = [v * skala_spar for v in box]
        chosen[max(0, int(y0) - 5):min(h, int(math.ceil(y1)) + 5), max(0, int(x0) - 5):min(w, int(math.ceil(x1)) + 5)] |= \
            full[max(0, int(y0) - 5):min(h, int(math.ceil(y1)) + 5), max(0, int(x0) - 5):min(w, int(math.ceil(x1)) + 5)]
    chosen = cv2.dilate(cv2.morphologyEx(chosen, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)), np.ones((5, 5), np.uint8))
    hsv = cv2.cvtColor(frames[i], cv2.COLOR_BGR2HSV); text = np.zeros_like(chosen)
    band = (slice(round(h * 0.43), round(h * 0.72)), slice(round(w * 0.04), round(w * 0.96)))
    text[band] = cv2.dilate(((hsv[band][..., 1] < 65) & (hsv[band][..., 2] > 205)).astype(np.uint8), np.ones((9, 9), np.uint8))
    masks[i] = np.maximum(chosen, text) * 255
canv, pres = [], []
for f, m in zip(frames, masks):
    c, p, tr = P.placera(f, m); canv.append(c); pres.append(p)
behov = math.ceil(n / fps * P.MODEL_FPS); mf = min(81, 4 * math.ceil((behov - 1) / 4) + 1)
idx = [min(round(i * fps / P.MODEL_FPS), n - 1) for i in range(mf)]
P.skriv_video(ut / 'condition_16fps.mp4', [canv[i] for i in idx], P.MODEL_FPS)
np.savez_compressed(ut / 'generation_mask_16fps.npz', mask=255 - np.stack([pres[i] for i in idx]))
np.savez_compressed(ut / 'preserve_all_30fps.npz', mask=np.stack(pres))
(ut / 'timing.json').write_text(json.dumps(dict(source=str(src), source_fps=fps, source_frames=n, model_fps=P.MODEL_FPS, model_frames=mf,
                                                model_source_indices=idx, transform=tr), indent=1), encoding='utf-8', newline='\n')
prompt = ("Photorealistic live-action vertical smartphone video in the same place, same natural light. Locked stationary camera. "
          "Preserve the exact people, their faces, expressions, hands, clothes, identity, gestures and timing. "
          "Extend the view downward and complete the people's legs and feet, chairs, table legs and floor naturally. "
          "Reconstruct a realistic tidy version of the same background with the same walls, furniture and lighting. "
          "No additional people, no invented motion, no camera movement, no stylization.")
neg = ("cartoon, illustration, painting, CGI, stylized, face change, identity change, different gesture, different pose, duplicated person, "
       "extra person, extra limbs, missing limbs, deformed hands, floating feet, cropped feet, camera shake, camera pan, camera zoom, motion blur, subtitles, watermark")
(ut / 'jobs.json').write_text(json.dumps([dict(id=f'{a.namn}_A', format='A', seed=1041, prompt=prompt, negative_prompt=neg, num_inference_steps=30,
                                               guidance_scale=5.0, conditioning_scale=1.0)], indent=1), encoding='utf-8', newline='\n')
print(a.namn, 'rutor', n, 'modellrutor', mf, 'personer', list(tracks))
