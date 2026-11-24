"""Uppdrag 0004: oberoende fokalskattning ur bilden: försvinningspunkter från linjesegment (kakelfogar, dörr- och fönsterkanter).
Per tagning: LSD på 3 bildrutor, RANSAC för två till tre försvinningspunkter, f² = -(v1-c)·(v2-c) för ortogonala riktningspar.
Körs: scen/.venv/Scripts/python.exe -B -I vp.py   Skriver vp_resultat.json och vp_tabell.md. Skattningen är grov (diagnos, inte krav)."""
import json, math, os, sys
import cv2, numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); UT = os.path.dirname(HERE)
I = os.path.abspath(os.path.join(UT, '..', '..', 'ingest', 'ut', 'b-tilltal-ravara-tagningar'))
W, H = 576., 1024.; C = np.array([W / 2, H / 2, 1.])
rng = np.random.default_rng(1)
lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)


def segment(sid, q):
    cap = cv2.VideoCapture(f'{I}/klipp/{sid}.mp4'); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); f = int(q * (n - 1)); cap.set(cv2.CAP_PROP_POS_FRAMES, f)
    ok, img = cap.read(); g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    M = np.load(f'{I}/{sid}/masker.npy', allow_pickle=True); pm = cv2.dilate(cv2.resize(M[f].astype(np.uint8) * 255, (576, 1024), interpolation=cv2.INTER_NEAREST), np.ones((25, 25), np.uint8))
    fri = np.full((1024, 576), 255, np.uint8); fri[pm > 0] = 0; fri[int(.47 * H):int(.75 * H), int(.09 * W):int(.92 * W)] = 0   # person + överlägg
    L = lsd.detect(g)[0]
    if L is None: return np.zeros((0, 4))
    L = L.reshape(-1, 4); mx = ((L[:, 0] + L[:, 2]) / 2).astype(int).clip(0, 575); my = ((L[:, 1] + L[:, 3]) / 2).astype(int).clip(0, 1023)
    ln = np.hypot(L[:, 2] - L[:, 0], L[:, 3] - L[:, 1]); keep = (fri[my, mx] > 0) & (ln > 35)
    return L[keep]


def linjer(L):
    p1 = np.c_[L[:, 0:2], np.ones(len(L))]; p2 = np.c_[L[:, 2:4], np.ones(len(L))]; l = np.cross(p1, p2); l /= np.linalg.norm(l[:, :2], axis=1, keepdims=True) + 1e-9
    return l, (p1 + p2) / 2


def vp_ransac(l, mid, iter=1500, tol_deg=1.8):
    best = None
    for _ in range(iter):
        i, j = rng.choice(len(l), 2, replace=False); v = np.cross(l[i], l[j])
        if abs(v[2]) < 1e-9: v = v / (np.linalg.norm(v) + 1e-12) * 1e9; v[2] = 1e-9
        d = mid[:, :2] - (v[:2] / v[2] if abs(v[2]) > 1e-12 else v[:2] * 1e9); dm = v[:2] / v[2] - mid[:, :2] if abs(v[2]) > 1e-12 else None
        if dm is None: continue
        ang = np.degrees(np.arccos(np.clip(np.abs(np.sum(dm / (np.linalg.norm(dm, axis=1, keepdims=True) + 1e-9) * np.c_[-l[:, 1], l[:, 0]], axis=1)), 0, 1)))
        inl = ang < tol_deg
        if best is None or inl.sum() > best[1].sum(): best = (v, inl)
    return best


def fokaler(sid):
    res = []
    for q in (.2, .5, .8):
        L = segment(sid, q)
        if len(L) < 25: continue
        l, mid = linjer(L); vps = []; rest = np.arange(len(l))
        for _ in range(3):
            if len(rest) < 12: break
            b = vp_ransac(l[rest], mid[rest])
            if b is None or b[1].sum() < 10: break
            v = b[0]; vps.append((v / v[2], int(b[1].sum()))); rest = rest[~b[1]]
        for a in range(len(vps)):
            for b_ in range(a + 1, len(vps)):
                va, vb = vps[a][0], vps[b_][0]; f2 = -float((va[:2] - C[:2]) @ (vb[:2] - C[:2]))
                if f2 > 0: res.append(dict(q=q, f=round(math.sqrt(f2), 0), inl=(vps[a][1], vps[b_][1]), vp=[[round(float(x), 0) for x in va[:2]], [round(float(x), 0) for x in vb[:2]]]))
    return res


ut = {}
for sid in ['S%d' % i for i in range(1, 12)]:
    ut[sid] = fokaler(sid); print(sid, [(r['f'], r['inl']) for r in ut[sid]])
json.dump(ut, open(f'{HERE}/vp_resultat.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
allf = [r['f'] for v in ut.values() for r in v if 300 <= r['f'] <= 3000 and min(r['inl']) >= 12]
print('alla kandidater 300–3000 px med >=12 inliers per punkt:', len(allf), 'median', np.median(allf) if allf else None, 'kvartiler', np.percentile(allf, [25, 75]).tolist() if allf else None)
with open(f'{HERE}/vp_tabell.md', 'w', encoding='utf8') as f:
    f.write('| tagn | kandidater f (px), >=12 inliers per försvinningspunkt | median |\n|---|---|---|\n')
    for sid, v in ut.items():
        c = [r['f'] for r in v if 300 <= r['f'] <= 3000 and min(r['inl']) >= 12]
        f.write(f'| {sid} | {c} | {np.median(c) if c else "–"} |\n')
