# -*- coding: utf-8 -*-
"""Hjälpverktyg för facitmärkning: tar ut en ruta ur originalvideon och ritar ett koordinatrutnät.

Märkningen görs i ORIGINALVIDEONS pixlar (540x960 för hold-out). Rutnätet har en tunn linje var
`--steg` px och en etikett var 100 px, så att en människa kan läsa av koordinater. Ingen modell körs.

  python ruta_rutnat.py <video.mp4> <ruta> <ut.png> [--crop x0 y0 x1 y1] [--skala 2] [--steg 20]
"""
import argparse

import cv2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("ruta", type=int); ap.add_argument("ut")
    ap.add_argument("--crop", nargs=4, type=int)
    ap.add_argument("--skala", type=float, default=1.0)
    ap.add_argument("--steg", type=int, default=20)
    ap.add_argument("--ren", action="store_true", help="spara också rutan utan rutnät")
    a = ap.parse_args()
    cap = cv2.VideoCapture(a.video)
    cap.set(cv2.CAP_PROP_POS_FRAMES, a.ruta)
    ok, fr = cap.read()
    cap.release()
    if not ok:
        raise SystemExit("kunde inte läsa rutan")
    if a.ren:
        cv2.imwrite(a.ut.replace(".png", "_ren.png"), fr)
    x0, y0, x1, y1 = a.crop if a.crop else (0, 0, fr.shape[1], fr.shape[0])
    im = fr[y0:y1, x0:x1].copy()
    k = a.skala
    im = cv2.resize(im, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC if k > 1 else cv2.INTER_AREA)
    g = (x0 // a.steg) * a.steg
    while g <= x1:
        if g >= x0:
            X = int(round((g - x0) * k))
            stark = g % 100 == 0
            cv2.line(im, (X, 0), (X, im.shape[0]), (0, 255, 255) if stark else (0, 160, 160), 1)
            if stark:
                cv2.putText(im, str(g), (X + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        g += a.steg
    g = (y0 // a.steg) * a.steg
    while g <= y1:
        if g >= y0:
            Y = int(round((g - y0) * k))
            stark = g % 100 == 0
            cv2.line(im, (0, Y), (im.shape[1], Y), (255, 0, 255) if stark else (160, 0, 160), 1)
            if stark:
                cv2.putText(im, str(g), (2, Y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
        g += a.steg
    cv2.imwrite(a.ut, im)


if __name__ == "__main__":
    main()
