# -*- coding: utf-8 -*-
"""Förslag på flyktpunktsfamiljer för facitmärkning (klassisk LSD + RANSAC, ingen inlärd modell).

Skriptet FÖRESLÅR linjefamiljer. Märkaren granskar ritningen och väljer bara familjer vars linjer
syns ligga på verkligt vågräta (eller lodräta) kanter i rummet: hyllor, bänkskivor, golvfogar, tak.
Valda linjer skrivs in i ankarfilen för hand. Inget i facit beror på en djupmodell.

  python facit_vp.py <video> <ruta> <ut.png> [--min-langd 35] [--familjer 3] [--mask x0 y0 x1 y1 ...]
Utdata: ritning (en färg per familj, lodräta i vitt) och JSON på stdout med flyktpunkter och linjer.
"""
import argparse
import json

import cv2
import numpy as np

FARG = [(0, 0, 255), (0, 200, 0), (255, 0, 0), (0, 200, 255), (255, 0, 255)]


def hom(l):
    x1, y1, x2, y2 = l
    v = np.cross([x1, y1, 1.0], [x2, y2, 1.0])
    return v / np.linalg.norm(v[:2])


def vp_lsq(L):
    _, _, vt = np.linalg.svd(np.array([hom(l) for l in L]))
    return vt[-1]


def vinkelfel(l, vp):
    """Vinkel (grader) mellan segmentet och linjen från dess mitt till flyktpunkten."""
    x1, y1, x2, y2 = l
    m = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
    d = np.array([x2 - x1, y2 - y1]); d /= np.linalg.norm(d)
    if abs(vp[2]) < 1e-9:
        r = vp[:2] / np.linalg.norm(vp[:2])
    else:
        r = vp[:2] / vp[2] - m
        n = np.linalg.norm(r)
        if n < 1e-6:
            return 0.0
        r /= n
    return float(np.degrees(np.arccos(min(1.0, abs(d @ r)))))


def ransac(L, rng, tol=1.5, iters=3000):
    best = []
    for _ in range(iters):
        i, j = rng.choice(len(L), 2, replace=False)
        vp = np.cross(hom(L[i]), hom(L[j]))
        if np.linalg.norm(vp) < 1e-12:
            continue
        inl = [k for k in range(len(L)) if vinkelfel(L[k], vp) < tol]
        if len(inl) > len(best):
            best = inl
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("ruta", type=int); ap.add_argument("ut")
    ap.add_argument("--min-langd", type=float, default=35)
    ap.add_argument("--familjer", type=int, default=3)
    ap.add_argument("--mask", nargs="*", type=int, default=[], help="rektanglar att utesluta (t.ex. textskyltar)")
    a = ap.parse_args()
    cap = cv2.VideoCapture(a.video); cap.set(cv2.CAP_PROP_POS_FRAMES, a.ruta)
    ok, fr = cap.read(); cap.release()
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    segs = lsd.detect(g)[0].reshape(-1, 4)
    L = [s for s in segs if np.hypot(s[2] - s[0], s[3] - s[1]) >= a.min_langd]
    rect = [a.mask[i:i + 4] for i in range(0, len(a.mask), 4)]
    L = [s for s in L if not any(r[0] <= (s[0] + s[2]) / 2 <= r[2] and r[1] <= (s[1] + s[3]) / 2 <= r[3] for r in rect)]
    ang = [abs(np.degrees(np.arctan2(s[3] - s[1], s[2] - s[0]))) for s in L]
    lod = [s for s, v in zip(L, ang) if 75 <= v <= 105]
    rest = [s for s, v in zip(L, ang) if not (75 <= v <= 105)]
    rng = np.random.default_rng(0)
    fam = []
    for _ in range(a.familjer):
        if len(rest) < 3:
            break
        inl = ransac(rest, rng)
        if len(inl) < 3:
            break
        F = [rest[k] for k in inl]
        fam.append(F)
        rest = [rest[k] for k in range(len(rest)) if k not in set(inl)]
    im = fr.copy()
    ut = {"ruta": a.ruta, "familjer": [], "lodrata": [[round(float(x), 1) for x in s] for s in lod]}
    for s in lod:
        cv2.line(im, (int(s[0]), int(s[1])), (int(s[2]), int(s[3])), (255, 255, 255), 2)
    for i, F in enumerate(fam):
        vp = vp_lsq(F)
        p = None if abs(vp[2]) < 1e-9 else [round(float(vp[0] / vp[2]), 1), round(float(vp[1] / vp[2]), 1)]
        ut["familjer"].append({"farg_bgr": FARG[i % 5], "vp": p, "n": len(F),
                               "linjer": [[round(float(x), 1) for x in s] for s in F]})
        for s in F:
            cv2.line(im, (int(s[0]), int(s[1])), (int(s[2]), int(s[3])), FARG[i % 5], 2)
            cv2.putText(im, str(i), (int((s[0] + s[2]) / 2), int((s[1] + s[3]) / 2)), cv2.FONT_HERSHEY_SIMPLEX,
                        0.4, FARG[i % 5], 1)
    if len(lod) >= 2:
        v = vp_lsq(lod)
        ut["lodrat_vp"] = None if abs(v[2]) < 1e-9 else [round(float(v[0] / v[2]), 1), round(float(v[1] / v[2]), 1)]
    cv2.imwrite(a.ut, im)
    print(json.dumps(ut))


if __name__ == "__main__":
    main()
