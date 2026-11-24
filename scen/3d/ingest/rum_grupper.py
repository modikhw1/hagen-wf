"""Mätta kameragrupper: vilka tagningar i ett klipp delar kameraplats (uppdrag 0010, punkt 1; ur bakgrund_prov/matcha.py från svar 0002).

    python rum_grupper.py <ingestmapp> [--nollklipp <ingestmapp>] [--overlay x0,y0,x1,y1] [--ut <fil>]
    -> <ingestmapp>/grupper.json: `delar_plats` (grupper av tagningar, status `matt`), tal per par och tagningar utan mätbar koppling.

Bakgrundsmatchning med maskade personer (SIFT, förhållandetest 0,8, MAGSAC). Ett par är mätt när:
  1. bästa F-inliers når parets nollgräns: den större av en absolut gräns (p99 mot ett annat klipps tagningar) och 1,5 gånger det parets slumpade (permuterade) matchningar högst nådde,
  2. homografin förklarar minst 60 % av F-inliers (samma plats eller plan vägg, inte en förflyttad kamera),
  3. relativ rotation ur essentiell matris är högst 30 grader (kakelalias ger osammanhängande rotationer),
  4. minst hälften av bildrutparen når nollgränsen.
Nollgränsen är härledd ur data; punkt 2–4 är valda (diagnos, inte krav) och redovisas i utdata.
"""
import argparse, itertools, json, math
from pathlib import Path

import numpy as np

H_ANDEL, MAX_ROT, MIN_ANDEL_RUTPAR, K_RUTOR, PERM_FAKTOR = .6, 30., .5, 4, 1.5


def nollgrans(abs_nollor):
    """Absolut nollgräns = p99 av maxvärdena i F-inliers mot ett annat klipps tagningar (minst 15)."""
    return max(15., float(np.percentile(abs_nollor, 99))) if len(abs_nollor) else 15.


def pargrans(abs_grans, perm_max):
    """Gränsen för ett enskilt par: den absoluta nollgränsen eller PERM_FAKTOR gånger det högsta F-inlier-antalet som slumpade matchningar
    nådde för just det paret (permutationen behåller antalet matchningar, så kakelrika par får högre gräns)."""
    return max(abs_grans, PERM_FAKTOR * perm_max)


def ar_matt(par, grans):
    """Bedömning av ett par ur dess tal och dess egen gräns. Returnerar (status, orsaker)."""
    orsaker = []
    if par['F_inl'] < grans: orsaker.append(f"F-inliers {par['F_inl']} under parets nollgräns {grans:.0f}")
    if par['F_inl'] and par['H_inl'] < H_ANDEL * par['F_inl']: orsaker.append('homografin förklarar under 60 % (flyttad kamera)')
    rot = par.get('R_grader')
    if rot is None or rot > MAX_ROT: orsaker.append('relativ rotation saknas eller över 30 grader')
    if par.get('andel_rutpar_over_grans', 0) < MIN_ANDEL_RUTPAR: orsaker.append('under hälften av rutparen når nollgränsen')
    return ('matt' if not orsaker else 'ingen mätbar koppling'), orsaker


def bilda_grupper(tagningar, par):
    """Sammanhängande grupper (union-find) av mätta par. Returnerar (grupper med minst två, tagningar utan koppling)."""
    forael = {t: t for t in tagningar}

    def rot(x):
        while forael[x] != x: forael[x] = forael[forael[x]]; x = forael[x]
        return x
    for p in par:
        if p['status'] == 'matt': forael[rot(p['par'][0])] = rot(p['par'][1])
    grp = {}
    for t in tagningar: grp.setdefault(rot(t), []).append(t)
    grupper = sorted([sorted(g, key=lambda s: int(s[1:])) for g in grp.values() if len(g) > 1], key=lambda g: int(g[0][1:]))
    return grupper, sorted([g[0] for g in grp.values() if len(g) == 1], key=lambda s: int(s[1:]))


# ---- mätning ur bilder ----
def _rutor(cv2, I, sid, k, overlay, sift, clahe):
    cap = cv2.VideoCapture(str(I / 'klipp' / f'{sid}.mp4')); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); h, w = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    mf = I / sid / 'masker.npy'; M = np.load(mf, allow_pickle=True) if mf.exists() else None; ut = []
    for q in np.linspace(.12, .88, k):
        f = int(round(q * (n - 1))); cap.set(cv2.CAP_PROP_POS_FRAMES, f); ok, img = cap.read()
        if not ok: continue
        fri = np.full((h, w), 255, np.uint8)
        if M is not None and len(M) == n: fri[cv2.dilate(cv2.resize(M[f].astype(np.uint8) * 255, (w, h), interpolation=cv2.INTER_NEAREST), np.ones((25, 25), np.uint8)) > 0] = 0
        if overlay: fri[int(overlay[1] * h):int(overlay[3] * h), int(overlay[0] * w):int(overlay[2] * w)] = 0
        kp, d = sift.detectAndCompute(clahe.apply(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)), fri); ut.append((kp, d))
    return ut, (w, h)


def _par(cv2, bf, a, b, K, permutera=None, rng=None):
    (kpa, da), (kpb, db) = a, b
    if da is None or db is None or len(kpa) < 8 or len(kpb) < 8: return None
    m = [x[0] for x in bf.knnMatch(da, db, k=2) if len(x) == 2 and x[0].distance < .8 * x[1].distance]
    if len(m) < 8: return dict(F_inl=0, H_inl=0, n_match=len(m))
    p1 = np.float32([kpa[x.queryIdx].pt for x in m]); p2 = np.float32([kpb[x.trainIdx].pt for x in m])
    stat = np.linalg.norm(p1 - p2, axis=1) < 2.; p1, p2 = p1[~stat], p2[~stat]
    if len(p1) < 8: return dict(F_inl=0, H_inl=0, n_match=len(m))
    if permutera is not None: p2 = p2[rng.permutation(len(p2))]                       # nollmodell: geometrin slumpas, deskriptorerna behålls
    Hm, mh = cv2.findHomography(p1, p2, cv2.USAC_MAGSAC, 3.0); F, mf = cv2.findFundamentalMat(p1, p2, cv2.USAC_MAGSAC, 1.5)
    r = dict(n_match=len(p1), H_inl=int(mh.sum()) if mh is not None else 0, F_inl=int(mf.sum()) if mf is not None else 0)
    if permutera is None and r['F_inl'] >= 8:
        E, me = cv2.findEssentialMat(p1, p2, K, cv2.USAC_MAGSAC, .999, 1.0)
        if E is not None and E.shape == (3, 3):
            _, Rm, _, _ = cv2.recoverPose(E, p1, p2, K, mask=me); r['R_grader'] = round(math.degrees(math.acos(max(-1., min(1., (np.trace(Rm) - 1) / 2.)))), 2)
    return r


def mat_grupper(ingest, nollklipp=None, overlay=None, k=K_RUTOR, seed=1):
    import cv2
    I = Path(ingest); rng = np.random.default_rng(seed); sift = cv2.SIFT_create(nfeatures=3000); clahe = cv2.createCLAHE(2., (8, 8)); bf = cv2.BFMatcher(cv2.NORM_L2)
    tagningar = sorted([p.parent.name for p in I.glob('S*/meta.json')], key=lambda s: int(s[1:])); data = {}; storlek = None
    for t in tagningar: data[t], storlek = _rutor(cv2, I, t, k, overlay, sift, clahe)
    K = np.array([[max(storlek) * 1., 0, storlek[0] / 2.], [0, max(storlek) * 1., storlek[1] / 2.], [0, 0, 1.]])       # antagen fokal = längsta sidan (rotationen är bara en kontroll)
    rader = []; nollor = []
    for s1, s2 in itertools.combinations(tagningar, 2):
        alla = []
        for ra in data[s1]:
            for rb in data[s2]:
                r = _par(cv2, bf, ra, rb, K)
                if r: alla.append(r)
        if not alla: rader.append(dict(par=[s1, s2], status='ingen mätbar koppling', orsaker=['för få särdrag'], F_inl=0, H_inl=0)); continue
        best = max(alla, key=lambda r: (r['F_inl'], r['H_inl']))
        nr = [_par(cv2, bf, ra, rb, K, permutera=True, rng=rng) or {} for ra in data[s1][:2] for rb in data[s2][:2] for _ in range(5)]
        pmax = max((r.get('F_inl', 0) for r in nr), default=0); nollor.append(pmax)
        rader.append(dict(par=[s1, s2], null_F_permuterad=pmax, _alla=[(r['F_inl'], r.get('n_match', 0)) for r in alla], **{x: best[x] for x in best}))
    kontroll = []
    if nollklipp:
        J = Path(nollklipp); andra = sorted([p.parent.name for p in J.glob('S*/meta.json')], key=lambda s: int(s[1:])); d2 = {t: _rutor(cv2, J, t, 2, None, sift, clahe)[0] for t in andra}
        for t in tagningar:
            for u in andra:
                f_ = [(_par(cv2, bf, ra, rb, K) or {}).get('F_inl', 0) for ra in data[t][:2] for rb in d2[u]]; kontroll.append(max(f_) if f_ else 0)
    grans = nollgrans(kontroll)
    for r in rader:
        alla = r.pop('_alla', [])
        g = pargrans(grans, r.get('null_F_permuterad', 0)); r['grans_par'] = round(g, 1)
        if alla: r['andel_rutpar_over_grans'] = round(float(np.mean([f >= g for f, _ in alla])), 2); r['median_F_rutpar'] = float(np.median([f for f, _ in alla]))
        r['status'], r['orsaker'] = ar_matt(r, g) if alla else (r.get('status'), r.get('orsaker'))
    grupper, utan = bilda_grupper(tagningar, rader)
    return dict(klipp=I.name, delar_plats=grupper, utan_koppling=utan, nollgrans_abs_F_inliers=round(grans, 1),
                nollgrans_ursprung=dict(annat_klipp_par=len(kontroll), absolut_ur='p99 av max-F mot annat klipp' if kontroll else 'ingen nollklipp: golv 15', per_par='PERM_FAKTOR x max F i 20 permuterade matchningar för paret'),
                valda_troskel=dict(h_andel=H_ANDEL, max_rotation_grader=MAX_ROT, min_andel_rutpar=MIN_ANDEL_RUTPAR, perm_faktor=PERM_FAKTOR, rutor_per_tagning=k), par=rader)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('ingest'); a.add_argument('--nollklipp'); a.add_argument('--overlay'); a.add_argument('--ut'); x = a.parse_args()
    ov = [float(v) for v in x.overlay.split(',')] if x.overlay else None
    res = mat_grupper(x.ingest, x.nollklipp, ov)
    ut = Path(x.ut) if x.ut else Path(x.ingest) / 'grupper.json'; ut.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print('delar_plats', res['delar_plats'], '| utan koppling', res['utan_koppling'], '| absolut nollgräns', res['nollgrans_abs_F_inliers'], '->', ut)
