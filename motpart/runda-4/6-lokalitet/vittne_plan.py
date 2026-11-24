"""Oberoende lutningsvittne för bords- och brickbilder: stödplanets två flyktpunkter.

Kanter på brickor, bord och bänkar bildar två familjer av parallella linjer i ett vågrätt plan. Deras
flyktpunkter v1, v2 ger planets normal n = (K^-1 v1) x (K^-1 v2) och därmed kamerans lutning mot planet.
Använder bara bildlinjer (LSD) inom säkra stödsegment (OneFormer) och kamerans fokal; varken MoGe-normaler,
GeoCalib eller kroppar. Antagande som redovisas: stödytan är vågrät. Kräver två familjer med minst fyra
linjer vardera, minst 30 graders skillnad, och samstämmighet (6 grader) i minst två nyckelrutor.
"""
from __future__ import annotations
import math
import cv2, numpy as np

STOD = ('table', 'tray', 'countertop', 'counter', 'desk', 'kitchen island', 'bar', 'buffet')


def _linjer(gray, mask, min_len=35):
    seg = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(gray)[0]
    if seg is None:
        return np.empty((0, 4))
    seg = seg.reshape(-1, 4).astype(float); d = seg[:, 2:] - seg[:, :2]; L = np.linalg.norm(d, axis=1)
    mid = ((seg[:, :2] + seg[:, 2:]) / 2).astype(int); H, W = mask.shape
    ok = (L >= min_len) & mask[np.clip(mid[:, 1], 0, H - 1), np.clip(mid[:, 0], 0, W - 1)]
    return seg[ok]


def _vp(seg, rng, undvik=None, tol=1.5):
    """RANSAC-flyktpunkt i homogena koordinater; returnerar (v, inlier-mask)."""
    if len(seg) < 4:
        return None, None
    p1 = np.c_[seg[:, :2], np.ones(len(seg))]; p2 = np.c_[seg[:, 2:], np.ones(len(seg))]
    lin = np.cross(p1, p2); lin /= np.linalg.norm(lin[:, :2], axis=1, keepdims=True)
    mid = (seg[:, :2] + seg[:, 2:]) / 2; dirs = seg[:, 2:] - seg[:, :2]; dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    best, bm = None, None
    for _ in range(600):
        i, j = rng.choice(len(seg), 2, replace=False)
        v = np.cross(lin[i], lin[j])
        if np.linalg.norm(v) < 1e-9:
            continue
        # vinkel mellan segmentets riktning och riktningen från mitten mot v
        if abs(v[2]) > 1e-9:
            t = v[:2] / v[2] - mid
        else:
            t = np.tile(v[:2], (len(seg), 1))
        t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
        err = np.degrees(np.arccos(np.clip(np.abs((t * dirs).sum(1)), -1, 1)))
        inl = err < tol
        if undvik is not None:
            inl &= ~undvik
        if bm is None or inl.sum() > bm.sum():
            best, bm = v, inl
    if bm is None or bm.sum() < 4:
        return None, None
    return best, bm


def matning(gray, mask, f_px, W0, H0, seed=0):
    seg = _linjer(gray, mask)
    if len(seg) < 8:
        return None
    rng = np.random.default_rng(seed)
    v1, m1 = _vp(seg, rng)
    if v1 is None:
        return None
    v2, m2 = _vp(seg, rng, undvik=m1)
    if v2 is None:
        return None
    Kinv = np.linalg.inv(np.array([[f_px, 0, W0 / 2], [0, f_px, H0 / 2], [0, 0, 1.0]]))
    d1, d2 = Kinv @ v1, Kinv @ v2; d1 /= np.linalg.norm(d1); d2 /= np.linalg.norm(d2)
    if math.degrees(math.acos(min(1.0, abs(float(d1 @ d2))))) < 30:
        return None
    n = np.cross(d1, d2); n /= np.linalg.norm(n)
    if n[1] > 0:  # uppåt pekar mot bildens överkant (-y i OpenCV)
        n = -n
    return round(math.degrees(math.asin(max(-1, min(1, float(n[2]))))), 1)  # kamerans lutning (negativ = nedåt)


def vittne(obs, frames, etiketter, f_px, W0, H0):
    varden = []
    for o in obs:
        if 'I' not in o:
            continue
        ids = [i_ for i_, l_ in o['segs'].items() if etiketter.get(l_, '').split(',')[0].strip() in STOD and i_ not in o.get('osakra', [])]
        if not ids:
            continue
        m = cv2.resize(np.isin(o['I'], ids).astype(np.uint8), (W0, H0), interpolation=cv2.INTER_NEAREST).astype(bool)
        if m.mean() < 0.05:
            continue
        p = matning(cv2.cvtColor(frames[o['u']], cv2.COLOR_BGR2GRAY), m, f_px, W0, H0)
        if p is not None:
            varden.append((int(o['u']), p))
    if len(varden) < 2:
        return {'lutning_grader': None, 'skal': f'vittne saknas: {len(varden)} rutor med två kantfamiljer', 'rutor': varden}
    v = np.array([x[1] for x in varden]); med = float(np.median(v))
    if (np.abs(v - med) <= 6).sum() < 2:
        return {'lutning_grader': None, 'skal': 'vittne saknas: rutorna går isär', 'rutor': varden}
    return {'lutning_grader': round(float(np.median(v[np.abs(v - med) <= 6])), 1), 'rutor': varden}


def selftest():
    """Syntetiskt rutnät i ett vågrätt plan sett från känd lutning -> rätt lutning inom 1 grad."""
    f, W0, H0 = 800.0, 540, 960
    for p_sann in (-30, -50, -70):
        p = math.radians(-p_sann)
        R = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])  # kamera nedvinklad
        img = np.zeros((H0, W0), np.uint8); K = np.array([[f, 0, W0 / 2], [0, f, H0 / 2], [0, 0, 1.0]])
        def proj(X):
            Xc = R @ (np.array(X) - np.array([0, -1.0, -0.0])); x = K @ Xc; return (int(x[0] / x[2]), int(x[1] / x[2]))
        for a in np.linspace(-0.4, 0.4, 9):  # två familjer: x-linjer och z-linjer i planet y=0 (kamera 1 m ovanför)
            cv2.line(img, proj([a, 0, 0.6]), proj([a, 0, 1.6]), 255, 2)
        for z in np.linspace(0.6, 1.6, 9):
            cv2.line(img, proj([-0.4, 0, z]), proj([0.4, 0, z]), 255, 2)
        got = matning(img, np.ones((H0, W0), bool), f, W0, H0)
        assert got is not None and abs(got - p_sann) < 1.5, (p_sann, got)
    return True


if __name__ == '__main__':
    print('självtest', selftest())
