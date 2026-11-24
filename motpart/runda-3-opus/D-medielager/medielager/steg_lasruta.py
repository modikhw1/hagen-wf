# -*- coding: utf-8 -*-
"""Läs text i givna lådor vid givna tider (för mätningen). Körs i D-medielager/_cache/venv.

Indata (json): [{"video": ..., "t": sek, "box": [x0,y0,x1,y1] normerat}, ...]
Utdata (json): samma lista med "text" och "p". Läser med detektion inom utsnittet (flera rader slås ihop).
"""
import json
import logging
import sys

import cv2


def main(inn, ut):
    from rapidocr import RapidOCR
    logging.getLogger("RapidOCR").setLevel(logging.ERROR)
    motor = RapidOCR()
    fr = json.load(open(inn, encoding="utf-8"))
    cache = {}
    for f in fr:
        cap = cache.get(f["video"]) or cv2.VideoCapture(f["video"])
        cache[f["video"]] = cap
        cap.set(cv2.CAP_PROP_POS_MSEC, f["t"] * 1000)
        ok, img = cap.read()
        f["text"], f["p"] = "", 0.0
        if not ok:
            continue
        H, W = img.shape[:2]
        x0, y0, x1, y1 = f["box"]
        p = 0.4 * (y1 - y0)
        c = img[int(max(0, (y0 - p) * H)):int(min(1, (y1 + p)) * H), int(max(0, (x0 - 0.05) * W)):int(min(1, x1 + 0.05) * W)]
        if c.size == 0:
            continue
        r = motor(c)
        if r.txts:
            f["text"] = " ".join(r.txts)
            f["p"] = round(float(sum(r.scores) / len(r.scores)), 3)
    json.dump(fr, open(ut, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
