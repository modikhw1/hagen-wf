"""Ramremsor: åtta på varandra följande rutor, källa överst, sedan varje renderad mapp (t.ex. tom2, tom3) under.
    scen/.venv/Scripts/python.exe scen/3d/kontrakt/ut/jamn_tabell/strip.py <klipp> <video> <ut-png> <mapp1> <mapp2> [scen:utruta ...]
Rutorna tas ur <mapp>/komposit/f<utruta>.png (renderingen med textlager). Skriver <ut-png>."""
import json
import sys
from pathlib import Path
import cv2
import numpy as np

klipp, video, utpng, m1, m2 = sys.argv[1:6]; platser = sys.argv[6:]
base = Path(__file__).resolve().parents[1] / klipp
plan = json.loads((base / m2 / 'plan.json').read_text(encoding='utf-8'))
cap = cv2.VideoCapture(str(video)); B = 150; rader = []
for p in platser:
    sid, u0 = p.split(':'); u0 = int(u0)
    rutor = list(range(u0, u0 + 8)); rader_p = []
    for namn in ('kalla', m1, m2):
        celler = []
        for u in rutor:
            if namn == 'kalla':
                cap.set(cv2.CAP_PROP_POS_FRAMES, plan['kallrutor'][u]); ok, im = cap.read()
            else:
                im = cv2.imread(str(base / namn / 'komposit' / f'f{u:04d}.png'))
                if im is None: im = cv2.imread(str(base / namn / 'render' / f'f{u:04d}.png'))
                if im is None: im = cv2.imread(str(base / namn / f'f{u:04d}.png'))
            if im is None: im = np.zeros((1024, 576, 3), np.uint8)
            h = int(B * im.shape[0] / im.shape[1]); celler.append(cv2.resize(im, (B, h)))
        rad = np.hstack(celler)
        cv2.putText(rad, f'{sid} {namn}', (4, 14), cv2.FONT_HERSHEY_SIMPLEX, .45, (0, 255, 255), 1)
        rader_p.append(rad)
    rader.append(np.vstack(rader_p))
cv2.imwrite(utpng, np.hstack(rader) if len(rader) == 1 else np.vstack(rader))
print(utpng)
