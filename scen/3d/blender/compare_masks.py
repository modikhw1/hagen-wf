"""Image comparison worker using the existing scen Python environment (OpenCV)."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

here = Path(__file__).resolve().parent
out = here / 'verifiering'
bake = json.loads((here / 'bake.json').read_text(encoding='utf-8'))
rows, results = {}, []
for sample in bake['samples']:
    i, shot = sample['i'], sample['shot']
    stem = f'{shot}-{i:03d}'
    paths = [out / f'{stem}-player-mask.png', out / f'{stem}-blender-mask.png']
    images = [cv2.imread(str(p)) for p in paths]
    if any(x is None for x in images):
        raise RuntimeError(f'Missing mask: {paths}')
    a, b = [cv2.cvtColor(x, cv2.COLOR_BGR2GRAY) > 127 for x in images]
    if a.shape != b.shape or not a.any() or not b.any():
        raise RuntimeError(f'Invalid or empty masks: {stem}')
    intersection, union = int((a & b).sum()), int((a | b).sum())
    iou = intersection / union
    results.append(dict(i=i, shot=shot, iou=iou, intersection_px=intersection, union_px=union))
    overlay = np.zeros_like(images[0])
    overlay[a & b] = (220, 220, 220)
    overlay[a & ~b] = (40, 180, 255)   # orange: player only
    overlay[b & ~a] = (255, 160, 40)   # blue: Blender only
    panels = []
    for img, label in zip([*images, overlay], ['three.js mask', 'Blender Workbench', f'Overlap {iou:.5f}']):
        img = cv2.resize(img, (288, 512), interpolation=cv2.INTER_AREA)
        title = np.full((36, 288, 3), 32, dtype=np.uint8)
        cv2.putText(title, label, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, .55, (245, 245, 245), 1, cv2.LINE_AA)
        panels.append(np.vstack((title, img)))
    row = np.hstack(panels)
    cv2.putText(row, f'{shot} frame {i} / {i / 30:.4f}s', (10, row.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX, .5, (130, 255, 130), 1, cv2.LINE_AA)
    rows.setdefault(shot, []).append(row)
for shot, shot_rows in rows.items():
    cv2.imwrite(str(out / f'{shot}-comparison.png'), np.vstack(shot_rows))
(out / 'mask-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps({s: min(x['iou'] for x in results if x['shot'] == s) for s in rows}))
