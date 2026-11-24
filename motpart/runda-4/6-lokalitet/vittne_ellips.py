"""Oberoende lutningsvittne för bilder ovanifrån: vilande runda kärl (tallrik, skål) som ellipser.

En vågrät cirkel sedd med elevationsvinkeln e mot sitt plan syns som en ellips med axelkvot b/a = sin(e).
Kamerans nedåtlutning p = e - atan((y_c - c_y)/f) (kärlets läge i bild korrigeras). Använder bara bildens
segmentmask (OneFormer) och kamerans fokal; varken MoGe-normaler, GeoCalib eller kroppar.
Avstår: kärl som rör en person (kan hållas, inte vågrätt), kärl vid bildkanten, dåligt ellipspassade masker,
brickor (rektangulära). Kräver minst två samstämmiga mätningar (inom 6 grader) per tagning.
"""
from __future__ import annotations
import math
import cv2, numpy as np

RUNDA = ('plate', 'bowl')


def matning(o, etiketter, gk, f_px, W0, H0):
    if 'I' not in o:
        return []
    h, w = o['I'].shape; sx, sy = W0 / w, H0 / h
    pers = np.isin(o['I'], [i_ for i_, l_ in o['segs'].items() if gk.get(l_) == 'person'])
    pers = cv2.dilate(pers.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    ut = []
    for i_, lab in o['segs'].items():
        namn = etiketter.get(lab, '').split(',')[0].strip()
        if namn not in RUNDA or i_ in o.get('osakra', []):
            continue
        m = (o['I'] == i_)
        if m.sum() < 0.004 * h * w or (m & pers).any():
            continue
        ys, xs = np.nonzero(m)
        if xs.min() <= 1 or ys.min() <= 1 or xs.max() >= w - 2 or ys.max() >= h - 2:
            continue  # kärlet skärs av bildkanten
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        hull = cv2.convexHull(max(cs, key=cv2.contourArea)).reshape(-1, 2).astype(np.float32)
        if len(hull) < 5:
            continue
        hull[:, 0] *= sx; hull[:, 1] *= sy
        (cx, cy), (d1, d2), _ = cv2.fitEllipse(hull)
        a, b = max(d1, d2) / 2, min(d1, d2) / 2
        if a < 0.06 * W0:
            continue
        # passform: skrovets yta mot ellipsens
        yta_h = cv2.contourArea(hull); yta_e = math.pi * a * b
        if yta_e <= 0 or not 0.88 <= yta_h / yta_e <= 1.05:
            continue
        e = math.degrees(math.asin(max(0.0, min(1.0, b / a))))
        p = e - math.degrees(math.atan((cy - H0 / 2) / f_px))
        ut.append({'ruta': int(o['u']), 'karl': namn, 'elevation_grader': round(e, 1), 'lutning_grader': round(-p, 1), 'axelkvot': round(b / a, 3)})
    return ut


def vittne(obs, etiketter, gk, f_px, W0, H0):
    alla = [m for o in obs for m in matning(o, etiketter, gk, f_px, W0, H0)]
    if len(alla) < 2:
        return {'lutning_grader': None, 'skal': f'vittne saknas: {len(alla)} godkända vilande runda kärl', 'matningar': alla}
    v = np.array([m['lutning_grader'] for m in alla]); med = float(np.median(v))
    nara = v[np.abs(v - med) <= 6]
    if len(nara) < 2:
        return {'lutning_grader': None, 'skal': 'vittne saknas: mätningarna går isär', 'matningar': alla}
    return {'lutning_grader': round(float(np.median(nara)), 1), 'n': int(len(nara)), 'matningar': alla}


def selftest():
    """Syntetisk cirkel sedd från känd vinkel -> rätt elevation; mätvärdet ska larma vid 15 graders ingestfel."""
    f, W0, H0 = 800.0, 540, 960
    for e_sann in (30, 50, 70):
        img = np.zeros((H0, W0), np.uint8)
        a = 150; b = a * math.sin(math.radians(e_sann))
        cv2.ellipse(img, ((W0 / 2, H0 / 2), (2 * a, 2 * b), 0), 255, -1)
        cs, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        (_, _), (d1, d2), _ = cv2.fitEllipse(cv2.convexHull(cs[0]).reshape(-1, 2).astype(np.float32))
        e = math.degrees(math.asin(min(d1, d2) / max(d1, d2)))
        assert abs(e - e_sann) < 1.0, (e, e_sann)
    return True


if __name__ == '__main__':
    print('självtest', selftest())
