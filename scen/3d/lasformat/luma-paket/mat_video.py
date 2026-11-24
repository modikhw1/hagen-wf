"""Mäter Lumas videoutfall (STEG2-VIDEO) mot originalets SAM-läsning, ruta för ruta.
  python mat_video.py forbered   -> mat_video/<arm>_<klipp>/jobb.json + lage.json (var originalramen ligger i utfallet) + yolo.json
  modal run ../../ingest/modal_sam3db.py --klipp <utfall.mp4> --jobb mat_video/<arm>_<klipp>/jobb.json --ut mat_video/<arm>_<klipp>/kropp --fokal <ur lage.json>
  python mat_video.py analys     -> mat_video/resultat.json + panel_<arm>_<klipp>.jpg
Originalramens läge i utfallet skattas per ruta med SIFT + likformighetsavbildning (skala, flytt, liten vridning).
Leder mappas tillbaka till originalets pixlar, så driften är jämförbar med Wan-måttet i ../mat_klipp.py."""
import json, sys
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; UT = HIT / 'mat_video'; UT.mkdir(exist_ok=True)
SCEN = HIT.parents[2]; ING = HIT.parents[1] / 'ingest' / 'ut' / 'notan-tagningar'
KORNINGAR = [('V1', 'S4', '1'), ('V2', 'S1', '1'), ('V3', 'S4', '1'), ('V3', 'S1', '1')]   # arm, klipp, person-id i ingesten
OVRE = list(range(9)); HANDER = list(range(21, 63)); HANDLED = [41, 62]; BEN = [11, 12, 13, 14]; FOT = [13, 14, 17, 20]

def rutor(f):
    cap = cv2.VideoCapture(str(f)); R = []
    while True:
        ok, im = cap.read()
        if not ok: break
        R.append(im)
    return R

def finns():
    for arm, s, pid in KORNINGAR:
        f = HIT / 'utfall' / 'video' / arm / f'{s}.mp4'
        if f.exists(): yield arm, s, pid, f

def procrustes(A, B, skala):
    a, b = A - A.mean(0), B - B.mean(0)
    U, S, Vt = np.linalg.svd(a.T @ b); R = U @ Vt
    if np.linalg.det(R) < 0: U[:, -1] *= -1; R = U @ Vt
    s = S.sum() / (a ** 2).sum() if skala else 1.0
    return np.linalg.norm(s * a @ R - b, axis=1).mean()

if sys.argv[1] == 'forbered':
    from ultralytics import YOLO
    pose = YOLO(str(SCEN / 'py' / 'modeller' / 'yolo11n-pose.pt')); sift = cv2.SIFT_create(3000); bf = cv2.BFMatcher()
    for arm, s, pid, f in finns():
        d = UT / f'{arm}_{s}'; d.mkdir(exist_ok=True)
        O, G = rutor(ING / 'klipp' / f'{s}.mp4'), rutor(f); P = json.loads((ING / s / 'personer.json').read_text(encoding='utf-8'))[pid]
        n = min(len(O), len(G)); M, inl, antal_g, antal_o = [], [], [], []
        for i in range(n):
            ko, do = sift.detectAndCompute(cv2.cvtColor(O[i], cv2.COLOR_BGR2GRAY), None); kg, dg = sift.detectAndCompute(cv2.cvtColor(G[i], cv2.COLOR_BGR2GRAY), None)
            bra = [m for m, k in bf.knnMatch(do, dg, k=2) if m.distance < 0.75 * k.distance]
            A = None
            if len(bra) >= 8:
                A, mask = cv2.estimateAffinePartial2D(np.float32([ko[m.queryIdx].pt for m in bra]), np.float32([kg[m.trainIdx].pt for m in bra]), ransacReprojThreshold=4)
                inl.append(int(mask.sum()) if A is not None else 0)
            else: inl.append(0)
            M.append(A.tolist() if A is not None else None)
            antal_g.append(int(len(pose(G[i], verbose=False)[0].boxes))); antal_o.append(int(len(pose(O[i], verbose=False)[0].boxes)))
        giltiga = np.array([m for m in M if m is not None]); med = np.median(giltiga, axis=0)
        skala = float(np.hypot(med[0, 0], med[1, 0])); Hg, Wg = G[0].shape[:2]; Ho, Wo = O[0].shape[:2]
        fok_o = float(np.load(ING / s / 'kropp' / pid / '0000.npz')['focal_length'])
        jobb = []
        for i in range(n):
            b = P.get(str(i))
            if b is None: continue
            A = np.array(M[i] if M[i] is not None else med)
            hörn = np.array([[b[0], b[1]], [b[2], b[1]], [b[0], b[3]], [b[2], b[3]]]) @ A[:, :2].T + A[:, 2]
            x0, y0, x1, y1 = hörn[:, 0].min(), hörn[:, 1].min(), hörn[:, 0].max(), hörn[:, 1].max()
            if b[3] > Ho - 8 and (np.array([0, Ho]) @ A[:, :2].T + A[:, 2])[1] < Hg - 8: y1 = Hg - 1    # rutan nådde originalets nederkant och utfallet är breddat nedåt
            jobb.append([i, 'p', [float(max(x0, 0)), float(max(y0, 0)), float(min(x1, Wg - 1)), float(min(y1, Hg - 1))]])
        json.dump(jobb, open(d / 'jobb.json', 'w'))
        lage = dict(fil=str(f.relative_to(HIT)), rutor_original=len(O), rutor_utfall=len(G), storlek_utfall=[Wg, Hg], skala=round(skala, 4), flytt=[round(float(med[0, 2]), 1), round(float(med[1, 2]), 1)],
                    fokal_original=fok_o, fokal_utfall=round(fok_o * skala, 1), inliers_median=int(np.median(inl)), rutor_utan_lage=int(sum(m is None for m in M)),
                    skala_spridning=round(float(np.std([np.hypot(m[0][0], m[1][0]) for m in M if m is not None])), 4), M=M, M_median=med.tolist())
        json.dump(lage, open(d / 'lage.json', 'w')); json.dump(dict(utfall=antal_g, original=antal_o), open(d / 'yolo.json', 'w'))
        print(arm, s, {k: v for k, v in lage.items() if k not in ('M', 'M_median')}, 'jobb', len(jobb))

else:
    res = {}
    for arm, s, pid, f in finns():
        d = UT / f'{arm}_{s}'
        if not (d / 'kropp' / 'p').exists(): print('ingen kropp', arm, s); continue
        L = json.load(open(d / 'lage.json')); Y = json.load(open(d / 'yolo.json')); Wg, Hg = L['storlek_utfall']; n = min(L['rutor_original'], L['rutor_utfall'])
        def gen(i):
            f = d / 'kropp' / 'p' / f'{i:04d}.npz'; return np.load(f) if f.exists() else None
        def org(i):
            f = ING / s / 'kropp' / pid / f'{i:04d}.npz'; return np.load(f) if f.exists() else None
        def tillbaka(kp, i):     # utfallets pixlar -> originalets pixlar
            A = np.array(L['M'][i] if L['M'][i] is not None else L['M_median']); return (kp - A[:, 2]) @ np.linalg.inv(A[:, :2]).T
        Gk = {i: gen(i) for i in range(n)}; Ok = {i: org(i) for i in range(n)}
        def drift(i, j, led):   # utfallets ruta i mot originalets ruta j
            if Gk.get(i) is None or Ok.get(j) is None: return None
            return float(np.median(np.linalg.norm(tillbaka(Gk[i]['pred_keypoints_2d'][led], i) - Ok[j]['pred_keypoints_2d'][led], axis=1)))
        # tajmning: vilken förskjutning i rutor ger minst drift i händer och överkropp
        forskj = {}
        for k in range(-6, 7):
            v = [drift(i, i + k, OVRE + HANDLED) for i in range(n)]; v = [x for x in v if x is not None]
            if len(v) > n * 0.7: forskj[k] = float(np.median(v))
        bast = min(forskj, key=forskj.get)
        r = dict(rutor=n, rutor_last=sum(g is not None for g in Gk.values()), lage=dict(skala=L['skala'], flytt=L['flytt'], inliers=L['inliers_median'], skala_spridning=L['skala_spridning']),
                 basta_forskjutning_rutor=bast, drift_vid_forskjutning={str(k): round(v, 1) for k, v in forskj.items() if k in (-2, -1, 0, 1, 2, bast)})
        for namn, led in (('overkropp', OVRE), ('handleder', HANDLED), ('fingrar', HANDER)):
            v = [x for x in (drift(i, i, led) for i in range(n)) if x is not None]
            r[f'drift_{namn}_px'] = dict(median=round(float(np.median(v)), 1), p90=round(float(np.percentile(v, 90)), 1), max=round(float(np.max(v)), 1))
        par = [(Gk[i], Ok[i]) for i in range(n) if Gk[i] is not None and Ok[i] is not None]
        bh = np.median([o['bbox'][3] - o['bbox'][1] for g, o in par])
        p2 = [procrustes(g['pred_keypoints_2d'][:21], o['pred_keypoints_2d'][:21], True) / (o['bbox'][3] - o['bbox'][1]) * 100 for g, o in par]
        p3 = [procrustes(g['pred_keypoints_3d'][:21], o['pred_keypoints_3d'][:21], False) * 100 for g, o in par]
        ph = [procrustes(g['pred_keypoints_3d'][HANDER], o['pred_keypoints_3d'][HANDER], False) * 100 for g, o in par]
        r['pose2d_procrustes_procent'] = dict(median=round(float(np.median(p2)), 1), p90=round(float(np.percentile(p2, 90)), 1))
        r['pose3d_cm'] = dict(median=round(float(np.median(p3)), 1), p90=round(float(np.percentile(p3, 90)), 1))
        r['hander3d_cm'] = dict(median=round(float(np.median(ph)), 1), p90=round(float(np.percentile(ph, 90)), 1))
        r['kroppshojd_original_px'] = round(float(bh), 0)
        r['ben_i_bild'] = dict(utfall=f"{sum(all(0 <= x < Wg and 0 <= y < Hg for x, y in g['pred_keypoints_2d'][BEN]) for g, o in par)}/{len(par)}",
                               original=f"{sum(all(0 <= x < 576 and 0 <= y < 1024 for x, y in o['pred_keypoints_2d'][BEN]) for g, o in par)}/{len(par)}")
        r['langd_m'] = dict(utfall=round(float(np.median([np.ptp(g['pred_vertices'][:, 1]) for g, o in par])), 3), original=round(float(np.median([np.ptp(o['pred_vertices'][:, 1]) for g, o in par])), 3))
        skak = lambda R: round(float(np.percentile(np.linalg.norm(np.diff(np.array(R), 2, axis=0), axis=1), 95) * 100), 3)
        r['rotskak_p95_cm'] = dict(utfall=skak([g['pred_cam_t'] for g, o in par]), original=skak([o['pred_cam_t'] for g, o in par]))
        fot = np.array([g['pred_keypoints_3d'][FOT] + g['pred_cam_t'] for g, o in par]); steg = np.linalg.norm(np.diff(fot, axis=0), axis=2) * 100
        r['fotrorelse_cm_per_ruta'] = dict(median=round(float(np.median(steg)), 2), p90=round(float(np.percentile(steg, 90)), 2))
        fot2 = np.array([g['pred_keypoints_2d'][FOT] for g, o in par]); r['fot_2d_spridning_px'] = round(float(np.median(np.std(fot2, axis=0))), 1)
        r['personer_yolo'] = dict(utfall_median=float(np.median(Y['utfall'])), utfall_max=int(max(Y['utfall'])), original_median=float(np.median(Y['original'])), original_max=int(max(Y['original'])))
        res[f'{arm}_{s}'] = r
        # panel: tre rutor, original med originalets leder (gröna) | utfall med utfallets leder (röda) och originalets leder mappade dit (gröna)
        O, G = rutor(ING / 'klipp' / f'{s}.mp4'), rutor(f); rad = []
        for i in (n // 6, n // 2, n * 5 // 6):
            o, g = O[i].copy(), G[i].copy()
            if Ok[i] is not None:
                A = np.array(L['M'][i] if L['M'][i] is not None else L['M_median'])
                for x, y in Ok[i]['pred_keypoints_2d'][:63]: cv2.circle(o, (int(x), int(y)), 3, (0, 255, 0), -1)
                for x, y in Ok[i]['pred_keypoints_2d'][:63] @ A[:, :2].T + A[:, 2]: cv2.circle(g, (int(x), int(y)), 4, (0, 255, 0), -1)
            if Gk[i] is not None:
                for x, y in Gk[i]['pred_keypoints_2d'][:63]: cv2.circle(g, (int(x), int(y)), 3, (0, 0, 255), -1)
            o = cv2.resize(o, (int(o.shape[1] * g.shape[0] / o.shape[0]), g.shape[0])); rad.append(np.hstack([o, g]))
        cv2.imwrite(str(UT / f'panel_{arm}_{s}.jpg'), cv2.resize(np.hstack(rad), None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 82])
    json.dump(res, open(UT / 'resultat.json', 'w'), indent=1, ensure_ascii=False)
    for k, v in res.items():
        print(k)
        for a, b in v.items(): print('  ', a, b)
