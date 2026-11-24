"""Mäter bildrörelse per tagning i originalet (ingen modell, bara OpenCV).

Kedjar likformighetstransformer (skala, rotation, translation) mellan på varandra
följande rutor med RANSAC över hela bilden. Rapporterar kumulativ skala/förflyttning
första->sista ruta och andelen inliers. Detta är bildrörelse, inte metrisk kamerabana.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import cv2, numpy as np

ROOT = Path(__file__).resolve().parents[3]
VIDEO = ROOT / 'data/format/kontroll/klipp/duepiani-7650849186912406806.mp4'
PAKET = ROOT / 'arbetsbord/data/ingest_v2/duepiani/paket.json'
OUT = Path(__file__).resolve().parent / 'ut'

def frames():
    cap = cv2.VideoCapture(str(VIDEO)); out = []
    while True:
        ok, f = cap.read()
        if not ok: break
        out.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    return out

def step(g0, g1):
    p0 = cv2.goodFeaturesToTrack(g0, 600, 0.01, 7)
    if p0 is None or len(p0) < 20: return None
    p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, p0, None, winSize=(21, 21), maxLevel=3)
    ok = st.ravel() == 1
    a, b = p0[ok].reshape(-1, 2), p1[ok].reshape(-1, 2)
    if len(a) < 20: return None
    M, inl = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=1.5, maxIters=4000, confidence=0.995)
    if M is None: return None
    return np.vstack([M, [0, 0, 1]]), float(inl.mean()), len(a), a[inl.ravel() == 1]

def main():
    pk = json.loads(PAKET.read_text(encoding='utf-8'))
    g = frames(); H, W = g[0].shape
    rows = []
    for s in pk['tagningar']:
        a0, b0 = s['ut']; T = np.eye(3); inl = []; per = []
        for f in range(a0, b0 - 1):
            r = step(g[f], g[f + 1])
            if r is None: continue
            M, ir, n, pts = r; T = M @ T; inl.append(ir)
            per.append(math.hypot(M[0, 2], M[1, 2]))
        sc = math.sqrt(abs(np.linalg.det(T[:2, :2]))); rot = math.degrees(math.atan2(T[1, 0], T[0, 0]))
        # förflyttning av bildmitten
        c = np.array([W / 2, H / 2, 1.0]); c2 = T @ c
        rows.append({'tagning': s['id'], 'ut': s['ut'], 'rutor': b0 - a0,
            'skala_forsta_till_sista': round(sc, 4), 'rotation_grader': round(rot, 2),
            'mitt_forflyttning_px': [round(float(c2[0] - c[0]), 1), round(float(c2[1] - c[1]), 1)],
            'median_steg_px': round(float(np.median(per)) if per else 0, 2),
            'median_inlier_andel': round(float(np.median(inl)) if inl else 0, 3),
            'paket_kamera': s['kamera']['typ'], 'paket_framat_m': round(s['kamera']['nycklar'][-1][2] - s['kamera']['nycklar'][0][2], 3),
            'bild_px': [W, H]})
    OUT.mkdir(exist_ok=True)
    (OUT / 'kamera_matning.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
    for r in rows: print(json.dumps(r, ensure_ascii=False))

if __name__ == '__main__':
    main()
