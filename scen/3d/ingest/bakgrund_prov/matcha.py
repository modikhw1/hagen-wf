"""Uppdrag 0002: mät överlapp mellan tagningar ur bakgrunden (personer maskade).
Körs: scen/.venv/Scripts/python.exe -B -I matcha.py <ingestmapp> <prefix> [--overlay x0,y0,x1,y1] [--fok 1024]
Skriver <prefix>_par.json, <prefix>_par.md, <prefix>_maskprov.jpg och <prefix>_match_<A>_<B>.jpg (de tre tydligaste paren).
Egna trösklar (N0 = 15 inliers, kvot 0,8) är diagnos, inte krav. Skala är okänd i monokulär matchning."""
import argparse, itertools, json, math, os, sys
import cv2, numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('ingest'); ap.add_argument('prefix')
ap.add_argument('--overlay', default=''); ap.add_argument('--fok', type=float, default=1024.); ap.add_argument('--k', type=int, default=4)
a = ap.parse_args()
I = os.path.abspath(os.path.join(HERE, '..', 'ut', a.ingest))
T = json.load(open(f'{I}/tagningar.json', encoding='utf8', errors='replace'))['tagningar']
N0, KVOT, ZERO_PX = 15, .8, 2.0
sift = cv2.SIFT_create(nfeatures=3000)
clahe = cv2.createCLAHE(clipLimit=2., tileGridSize=(8, 8))
ovl = [float(v) for v in a.overlay.split(',')] if a.overlay else None


def hamta(sid, I=I):
    """K jämnt fördelade bildrutor och deras personmasker (True = ingen person att mäta på)."""
    cap = cv2.VideoCapture(f'{I}/klipp/{sid}.mp4'); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    mfil = f'{I}/{sid}/masker.npy'; M = np.load(mfil, allow_pickle=True) if os.path.exists(mfil) else None
    ut = []
    for q in np.linspace(.12, .88, a.k):
        f = int(round(q * (n - 1))); cap.set(cv2.CAP_PROP_POS_FRAMES, f); ok, img = cap.read()
        if not ok: continue
        h, w = img.shape[:2]; fri = np.full((h, w), 255, np.uint8)
        if M is not None and len(M) == n:
            pm = cv2.resize(M[f].astype(np.uint8) * 255, (w, h), interpolation=cv2.INTER_NEAREST)
            fri[cv2.dilate(pm, np.ones((25, 25), np.uint8)) > 0] = 0
        if ovl:
            fri[int(ovl[1] * h):int(ovl[3] * h), int(ovl[0] * w):int(ovl[2] * w)] = 0
        g = clahe.apply(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        kp, d = sift.detectAndCompute(g, fri)
        ut.append(dict(f=f, img=img, kp=kp, d=d, fri=fri))
    return ut, (n, M is not None and len(M) == n)


data = {}; info = {}
for t in T:
    data[t['id']], info[t['id']] = hamta(t['id'])
    print(t['id'], 'rutor', info[t['id']][0], 'masker', info[t['id']][1], 'kp/ruta', [len(r['kp']) for r in data[t['id']]])
# maskprov: en ruta per klipp med fritt område markerat
for sid in list(data)[:1]:
    r = data[sid][len(data[sid]) // 2]; v = r['img'].copy(); v[r['fri'] == 0] = (v[r['fri'] == 0] * .25 + np.array([0, 0, 160]) * .75).astype(np.uint8)
    cv2.imwrite(f'{HERE}/{a.prefix}_maskprov.jpg', cv2.drawKeypoints(v, r['kp'], None, color=(0, 255, 0)))
K = np.array([[a.fok, 0, 288.], [0, a.fok, 512.], [0, 0, 1.]])
bf = cv2.BFMatcher(cv2.NORM_L2)


def vinkel(R):
    return math.degrees(math.acos(max(-1., min(1., (np.trace(R) - 1) / 2.))))


def para(ra, rb):
    if ra['d'] is None or rb['d'] is None or len(ra['kp']) < 8 or len(rb['kp']) < 8: return None
    m = [x[0] for x in bf.knnMatch(ra['d'], rb['d'], k=2) if len(x) == 2 and x[0].distance < KVOT * x[1].distance]
    p1 = np.float32([ra['kp'][x.queryIdx].pt for x in m]); p2 = np.float32([rb['kp'][x.trainIdx].pt for x in m])
    if len(m) == 0: return dict(n_match=0, n_statiska=0, H_inl=0, F_inl=0)
    stat = np.linalg.norm(p1 - p2, axis=1) < ZERO_PX                # överlägg och annat som ligger still i bilden
    m = [x for x, s in zip(m, stat) if not s]; p1, p2 = p1[~stat], p2[~stat]
    r = dict(n_match=len(m), n_statiska=int(stat.sum()), H_inl=0, F_inl=0, m=m)
    if len(m) < 8: return r
    H, mh = cv2.findHomography(p1, p2, cv2.USAC_MAGSAC, 3.0); F, mf = cv2.findFundamentalMat(p1, p2, cv2.USAC_MAGSAC, 1.5)
    r['H_inl'] = int(mh.sum()) if mh is not None else 0; r['F_inl'] = int(mf.sum()) if mf is not None else 0
    r['H'] = H; r['maskF'] = mf.ravel().astype(bool) if mf is not None else None; r['p1'] = p1; r['p2'] = p2
    if r['F_inl'] >= 8:
        E, me = cv2.findEssentialMat(p1, p2, K, cv2.USAC_MAGSAC, .999, 1.0)
        if E is not None and E.shape == (3, 3):
            n, R, tt, mp = cv2.recoverPose(E, p1, p2, K, mask=me)
            r.update(E_inl=int(me.sum()), pose_inl=int(n), R_grader=round(vinkel(R), 2), t_riktning=[round(float(v), 3) for v in tt.ravel()])
            ang = {}
            for fk in (700., 1024., 1400.):                          # okänd lins: hur mycket rör sig vinkeln?
                K2 = np.array([[fk, 0, 288.], [0, fk, 512.], [0, 0, 1.]]); E2, me2 = cv2.findEssentialMat(p1, p2, K2, cv2.USAC_MAGSAC, .999, 1.0)
                if E2 is not None and E2.shape == (3, 3):
                    _, R2, _, _ = cv2.recoverPose(E2, p1, p2, K2, mask=me2); ang[int(fk)] = round(vinkel(R2), 2)
            r['R_grader_per_fokal'] = ang
    if r['H_inl'] >= 8 and H is not None and np.all(np.isfinite(H)):
        Rh = np.linalg.inv(K) @ H @ K; dh = abs(np.linalg.det(Rh))
        if np.isfinite(dh) and dh > 1e-9:
            U, _, Vt = np.linalg.svd(Rh / np.cbrt(dh)); Rr = U @ Vt; r['H_rotation_grader'] = round(vinkel(Rr), 2)
    return r


rader = []
for s1, s2 in itertools.combinations(data, 2):
    bast = None; alla = []
    for i, ra in enumerate(data[s1]):
        for j, rb in enumerate(data[s2]):
            r = para(ra, rb)
            if r is None: continue
            r['ruta'] = (ra['f'], rb['f']); alla.append(r['F_inl'])
            if bast is None or (r['F_inl'], r['H_inl']) > (bast['F_inl'], bast['H_inl']): bast = r
    if bast is None: rader.append(dict(par=[s1, s2], orsak='för få särdrag')); continue
    modell = 'ingen mätbar'
    if bast['F_inl'] >= N0: modell = 'homografi (samma plats eller plan vägg)' if bast['H_inl'] >= .85 * bast['F_inl'] else 'essentiell (flyttad kamera)'
    post = dict(par=[s1, s2], bastaruta=bast['ruta'], n_match=bast['n_match'], n_statiska_bort=bast['n_statiska'], H_inl=bast['H_inl'], F_inl=bast['F_inl'],
                F_inl_median_alla_rutpar=float(np.median(alla)), inl_andel_F=round(bast['F_inl'] / max(1, bast['n_match']), 3), modell=modell)
    for k in ('E_inl', 'pose_inl', 'R_grader', 't_riktning', 'R_grader_per_fokal', 'H_rotation_grader'):
        if k in bast: post[k] = bast[k]
    rader.append(post); post['_bast'] = bast
    print(f'{s1}-{s2}: match {bast["n_match"]} (statiska bort {bast["n_statiska"]}) H {bast["H_inl"]} F {bast["F_inl"]}  {modell}  R={post.get("R_grader")}')

# ritade matchningar för de tre tydligaste paren
rader_ok = [r for r in rader if '_bast' in r]
for r in sorted(rader_ok, key=lambda r: -r['F_inl'])[:3]:
    s1, s2 = r['par']; b = r['_bast']; f1, f2 = r['bastaruta']
    i1 = next(x for x in data[s1] if x['f'] == f1); i2 = next(x for x in data[s2] if x['f'] == f2)
    if b.get('maskF') is not None:
        mm = [m for m, ok in zip(b['m'], b['maskF']) if ok]
        bild = cv2.drawMatches(i1['img'], i1['kp'], i2['img'], i2['kp'], mm[:120], None, matchColor=(0, 255, 0), flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
        cv2.imwrite(f'{HERE}/{a.prefix}_match_{s1}_{s2}.jpg', bild)
for r in rader: r.pop('_bast', None)
json.dump(dict(ingest=a.ingest, fokal_antagen_px=a.fok, N0=N0, ratio=KVOT, rutor_per_tagning=a.k, par=rader), open(f'{HERE}/{a.prefix}_par.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
sid = list(data)
mat = {(r['par'][0], r['par'][1]): r for r in rader}
with open(f'{HERE}/{a.prefix}_par.md', 'w', encoding='utf8') as f:
    f.write(f'Antal inliers för fundamentalmatris (F) per par, bästa av {a.k}x{a.k} rutpar. Inom parentes: homografins inliers.\n\n| |' + '|'.join(sid) + '|\n|---|' + '---|' * len(sid) + '\n')
    for x in sid:
        f.write(f'|{x}|' + '|'.join('' if x == y else (f'{mat[(x, y) if (x, y) in mat else (y, x)].get("F_inl", 0)} ({mat[(x, y) if (x, y) in mat else (y, x)].get("H_inl", 0)})') for y in sid) + '|\n')
    f.write('\n| par | match | F | H | modell | R° (E, fokal 700/1024/1400) |\n|---|---|---|---|---|---|\n')
    for r in rader: f.write(f'| {r["par"][0]}–{r["par"][1]} | {r.get("n_match", "")} | {r.get("F_inl", "")} | {r.get("H_inl", "")} | {r.get("modell", r.get("orsak"))} | {r.get("R_grader", "")} {r.get("R_grader_per_fokal", "")} |\n')
print('klart')

# --- nollkontroll: samma matchning mot ett annat rum (ingen verklig överlappning); visar hur många "inliers" slumpen ger ---
if os.environ.get('KONTROLL'):
    I2 = os.path.abspath(os.path.join(HERE, '..', 'ut', os.environ['KONTROLL']))
    T2 = json.load(open(f'{I2}/tagningar.json', encoding='utf8', errors='replace'))['tagningar']
    d2 = {t['id']: hamta(t['id'], I2)[0] for t in T2}
    kont = []
    for s1 in data:
        for s2 in d2:
            f_ = [r['F_inl'] for ra in data[s1] for rb in d2[s2] for r in [para(ra, rb)] if r is not None]
            kont.append(dict(par=[s1, 'kontroll_' + s2], F_inl_max=max(f_), F_inl_median=float(np.median(f_))))
    mx = sorted(k['F_inl_max'] for k in kont)
    print('NOLLKONTROLL F_inl (max per tagningspar, mot annat rum): min', mx[0], 'median', mx[len(mx) // 2], 'p90', mx[int(.9 * len(mx))], 'max', mx[-1])
    json.dump(dict(kontroll_ingest=os.environ['KONTROLL'], par=kont), open(f'{HERE}/{a.prefix}_nollkontroll.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
