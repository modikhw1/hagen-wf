"""Oberoende lodlinjevittne ur bildlinjer (flyktpunkt för vertikaler), automatiskt.

Linjeanpassningen (`fit`) är Codex motprov (ut/codex/vp.py, 21 nov) oförändrad i sak: LSD-segment, robust
konsensus, vinkelanpassning, bootstrap, grindar (>=5 inlierlinjer, >=25 % bildbredd, CI <=10 grader).
Skillnad mot motprovet: regionerna väljs automatiskt ur OneFormer-segment med hög poäng i arkitektoniska
klasser (vägg, dörr, fönster, skåp, spis, kyl, pelare), personer bortmaskade, i stället för handvalda rutor.
Vittnet använder varken MoGe-normaler, GeoCalib eller kroppar, och hålls utanför lodlinjefusionen.
Det är villkorat på kamerans fokal (samma intrinsik som ingesten), precis som motprovet.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import cv2, numpy as np
from scipy.optimize import least_squares

ARKITEKTUR = ('wall', 'door', 'windowpane', 'window', 'cabinet', 'refrigerator', 'column', 'stove', 'oven',
              'shelf', 'wardrobe', 'bookcase', 'screen door', 'doorframe', 'pillar', 'hood', 'chest of drawers')


def pitch(par):
    v = np.array([par[0], -1., par[1]])
    return math.degrees(math.asin(v[2] / np.linalg.norm(v)))


def fit(seg, W, H, f):
    """Ur ut/codex/vp.py (Codex motprov 21 nov)."""
    if len(seg) < 5:
        return {'valid': False, 'reason': 'färre än fem separerade linjer'}
    mid = (seg[:, :2] + seg[:, 2:]) / 2; d = seg[:, 2:] - seg[:, :2]
    d = d * np.where(d[:, 1:2] < 0, -1, 1); lengths = np.linalg.norm(d, axis=1)
    xy = (mid - [W / 2, H / 2]) / f; slopes = d[:, 0] / d[:, 1]
    A = np.stack([np.ones(len(seg)), slopes * xy[:, 1] - xy[:, 0]], 1); b = -slopes

    def residual(par):
        pred = np.stack([par[0] - xy[:, 0] * par[1], -1 - xy[:, 1] * par[1]], 1)
        cross = pred[:, 0] * d[:, 1] - pred[:, 1] * d[:, 0]
        return np.degrees(np.arcsin(np.clip(cross / (np.linalg.norm(pred, axis=1) * lengths), -1, 1)))
    pairs = np.array([(i, j) for i in range(len(seg)) for j in range(i + 1, len(seg))])
    if len(pairs) > 2000:
        pairs = pairs[np.random.default_rng(829).choice(len(pairs), 2000, replace=False)]
    best = None
    for ids in pairs:
        if abs(np.linalg.det(A[ids])) < .02:
            continue
        par = np.linalg.solve(A[ids], b[ids]); err = np.abs(residual(par)); sel = err < .8
        if abs(math.degrees(math.atan(par[0]))) > 35:
            continue
        score = float(np.minimum(lengths[sel], 200).sum())
        if best is None or score > best[0]:
            best = (score, par, sel)
    if best is None:
        return {'valid': False, 'reason': 'ingen stabil linjehypotes'}
    _, par, sel = best
    for _ in range(3):
        par = least_squares(lambda x: residual(x)[sel] * np.sqrt(np.minimum(lengths[sel], 200)), par, loss='soft_l1', f_scale=3).x
        sel = np.abs(residual(par)) < .8
    span = float(np.ptp(mid[sel, 0])) if sel.any() else 0
    rng = np.random.default_rng(54); boots = []; ids = np.where(sel)[0]
    for _ in range(150):
        ii = rng.choice(ids, len(ids), replace=True)
        if np.linalg.matrix_rank(A[ii]) < 2:
            continue
        q = np.linalg.lstsq(A[ii] * lengths[ii, None], b[ii] * lengths[ii], rcond=None)[0]
        boots.append(pitch(q))
    ci = np.percentile(boots, [2.5, 97.5]).tolist() if boots else [-90, 90]
    reasons = []
    if sel.sum() < 5: reasons.append('färre än 5 inlierlinjer')
    if span < .25 * W: reasons.append('horisontellt stöd <25 % av bilden')
    if ci[1] - ci[0] > 10: reasons.append('bootstrapintervall bredare än 10 grader')
    return {'valid': not reasons, 'reason': '; '.join(reasons), 'pitch': pitch(par), 'ci95': ci, 'n_inliers': int(sel.sum()), 'n_lines': len(seg)}


def detect(gray, mask, min_length=40):
    seg = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(gray)[0]
    if seg is None:
        return np.empty((0, 4))
    seg = seg.reshape(-1, 4).astype(float); d = seg[:, 2:] - seg[:, :2]; mid = (seg[:, :2] + seg[:, 2:]) / 2
    ok = (np.linalg.norm(d, axis=1) >= min_length) & (np.abs(d[:, 0]) < np.abs(d[:, 1]) * math.tan(math.radians(35)))
    H, W = mask.shape
    mx = np.clip(mid[:, 0].astype(int), 0, W - 1); my = np.clip(mid[:, 1].astype(int), 0, H - 1)
    ok &= mask[my, mx]
    seg = seg[ok]; d = seg[:, 2:] - seg[:, :2]; length = np.linalg.norm(d, axis=1); kept = []
    for j in np.argsort(-length):
        v = d[j] / length[j]; p = seg[j, :2]; dup = False
        for k in kept:
            vk = d[k] / length[k]
            if math.degrees(math.acos(np.clip(abs(v @ vk), -1, 1))) < 0.5 and abs(v[0] * (seg[k, 1] - p[1]) - v[1] * (seg[k, 0] - p[0])) < 6:
                dup = True; break
        if not dup:
            kept.append(j)
    return seg[kept]


def arkitekturmask(o, etiketter, H0, W0):
    """Säkra (poäng >= 0,75) arkitektoniska segment, uppskalade till originalbilden; personer aldrig med."""
    if 'I' not in o:
        return None
    ids = [i_ for i_, lab in o['segs'].items() if any(n.strip() in ARKITEKTUR for n in etiketter.get(lab, '').split(',')) and i_ not in o.get('osakra', [])]
    m = np.isin(o['I'], ids)
    m = cv2.resize(m.astype(np.uint8), (W0, H0), interpolation=cv2.INTER_NEAREST).astype(bool)
    return cv2.erode(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)


def vittne(obs, frames, etiketter, f_px, H0, W0):
    """Per tagning: median av minst två godkända nyckelrutor, annars 'saknas' med skäl."""
    rutor = []
    for o in obs:
        m = arkitekturmask(o, etiketter, H0, W0)
        if m is None or m.mean() < 0.03:
            rutor.append({'ruta': o['u'], 'valid': False, 'reason': 'för lite säker arkitektur i bilden'}); continue
        r = fit(detect(cv2.cvtColor(frames[o['u']], cv2.COLOR_BGR2GRAY), m), W0, H0, f_px)
        r['ruta'] = o['u']; rutor.append(r)
    ok = [r for r in rutor if r['valid']]
    if len(ok) >= 2:
        return {'lutning_grader': round(float(np.median([r['pitch'] for r in ok])), 1), 'rutor': rutor}
    return {'lutning_grader': None, 'skal': 'vittne saknas: ' + '; '.join(sorted({r['reason'] for r in rutor if not r['valid']})), 'rutor': rutor}


def selftest():
    """Syntetiska vertikaler med känd lutning: vittnet ska träffa inom 0,2 grader och larma vid 15 graders fel."""
    rng = np.random.default_rng(332); ut = []
    for p in [-50, -15, 0, 15]:
        par = np.array([.04, math.tan(math.radians(p)) * math.sqrt(1 + .04 ** 2)]); seg = []
        for x, y in zip(np.linspace(45, 495, 20), rng.uniform(200, 700, 20)):
            mid = np.array([x, y]); xy = (mid - [270, 480]) / 800
            d = np.array([par[0] - xy[0] * par[1], -1 - xy[1] * par[1]]); d = d / np.linalg.norm(d) * 60
            seg.append(np.r_[mid - d, mid + d] + rng.normal(0, .05, 4))
        r = fit(np.array(seg), 540, 960, 800)
        assert r['valid'] and abs(r['pitch'] - p) < .2, (p, r)
        ut.append((p, round(r['pitch'], 2)))
    assert abs(ut[1][1] - (-15 + 15)) > 10  # en ingest som har fel med 15 grader fångas
    return ut


if __name__ == '__main__':
    print('självtest', selftest())
