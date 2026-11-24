# -*- coding: utf-8 -*-
"""Rutnät av originalet för min egen granskning: en ruta per sekund, oberoende av mina detektorer.

    scen/.venv/Scripts/python.exe -X utf8 rutnat.py urval|holdout|<video.mp4>
Skriver granskning/rutnat/<klipp>.jpg (10 rutor per rad, 108 px breda, tid i hörnet).
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from medielager.gemensamt import abs_, las_rutor, probe  # noqa: E402


def rutnat(video, ut, per_rad=10, bredd=108):
    L = probe(video)["langd"]
    tider = [t + 0.5 for t in range(int(L))] or [L / 2]
    R = las_rutor(video, tider, bredd=bredd)
    h = next((r.shape[0] for r in R if r is not None), 192)
    rutor = []
    for t, r in zip(tider, R):
        r = r if r is not None else np.zeros((h, bredd, 3), np.uint8)
        r = r[:h].copy()
        cv2.rectangle(r, (0, 0), (34, 14), (0, 0, 0), -1)
        cv2.putText(r, f"{t:.1f}", (2, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)
        rutor.append(r)
    while len(rutor) % per_rad:
        rutor.append(np.zeros_like(rutor[0]))
    rader = [np.hstack(rutor[i:i + per_rad]) for i in range(0, len(rutor), per_rad)]
    ut.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(ut), np.vstack(rader), [cv2.IMWRITE_JPEG_QUALITY, 85])


if __name__ == "__main__":
    a = sys.argv[1]
    if a in ("urval", "holdout"):
        U = json.loads((D / "urval.json").read_text(encoding="utf-8"))
        vids = [abs_(u["video"]) for u in (U["holdout"] if a == "holdout" else U["urval"])]
    else:
        vids = [abs_(a)]
    for v in vids:
        rutnat(v, D / "granskning" / "rutnat" / f"{v.stem}.jpg")
        print(v.stem, flush=True)
