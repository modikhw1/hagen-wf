"""Uppdrag 0008 del A: korskontroll av bildrutor mellan tagningar som delar kameraplats, utan modell.
Homografi (SIFT + MAGSAC, personer och överlägg maskade) för över rutan från tagning A till B; jämförs med B:s egen ruta (IoU och kantavstånd).
Körs (från scen/): .venv/Scripts/python.exe -B 3d/ingest/rutprov/korskontroll.py   Skriver korskontroll.json och korskontroll.md."""
import json, math, os, sys
import cv2, numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); ING = os.path.dirname(HERE); D3 = os.path.dirname(ING)
I = f'{ING}/ut/b-tilltal-ravara-tagningar'; W, H = 576., 1024.
DEKL = json.load(open(f'{I}/brief/uppsattning3/deklaration_n06_detekterad.json', encoding='utf8'))
PLAN = json.load(open(f'{D3}/kontrakt/ut/b-tilltal-ravara_n06-fler/narvaro/plan.json', encoding='utf8'))
BOX = {}
for eid, d in list(DEKL['platser'].items()) + list(DEKL['foremal'].items()):
    for b in d.get('bilder') or []: BOX.setdefault(eid, {})[b['tagning']] = b['box_2d']
# rätta kanter avlästa på ögat i nyckelbilderna (svar 0001): bordsytans övre kant, ca 0,87 av höjden
BOX.setdefault('disk_C_rattad', {}).update({'S6': [870, 0, 1000, 1000], 'S7': [875, 0, 1000, 1000]})
sift = cv2.SIFT_create(nfeatures=4000); clahe = cv2.createCLAHE(2., (8, 8)); bf = cv2.BFMatcher(cv2.NORM_L2)


def ruta(sid):
    cap = cv2.VideoCapture(f'{I}/klipp/{sid}.mp4'); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); f = n // 2; cap.set(cv2.CAP_PROP_POS_FRAMES, f)
    ok, img = cap.read(); M = np.load(f'{I}/{sid}/masker.npy', allow_pickle=True)
    fri = np.full((int(H), int(W)), 255, np.uint8)
    fri[cv2.dilate(cv2.resize(M[f].astype(np.uint8) * 255, (int(W), int(H)), interpolation=cv2.INTER_NEAREST), np.ones((25, 25), np.uint8)) > 0] = 0
    fri[int(.47 * H):int(.75 * H), int(.09 * W):int(.92 * W)] = 0
    kp, d = sift.detectAndCompute(clahe.apply(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)), fri); return kp, d, n


def homografi(a, b):
    ka, da, _ = ruta(a); kb, db, _ = ruta(b)
    m = [x[0] for x in bf.knnMatch(da, db, k=2) if len(x) == 2 and x[0].distance < .8 * x[1].distance]
    if len(m) < 8: return None, 0, len(m)
    p1 = np.float32([ka[x.queryIdx].pt for x in m]); p2 = np.float32([kb[x.trainIdx].pt for x in m])
    Hm, mask = cv2.findHomography(p1, p2, cv2.USAC_MAGSAC, 3.0)
    return Hm, int(mask.sum()) if mask is not None else 0, len(m)


def hornen(box):
    y0, x0, y1, x1 = box; return np.float32([[x0 / 1000 * W, y0 / 1000 * H], [x1 / 1000 * W, y0 / 1000 * H], [x1 / 1000 * W, y1 / 1000 * H], [x0 / 1000 * W, y1 / 1000 * H]])


def iou(a, b):
    ix = max(0., min(a[3], b[3]) - max(a[1], b[1])); iy = max(0., min(a[2], b[2]) - max(a[0], b[0])); i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i; return i / u if u > 0 else 0.


def kam(sid):
    u0, u1 = [s for s in PLAN['scener'] if s['id'].upper() == sid][0]['ut']; M = np.array(PLAN['renderkamera']['nycklar'][(u0 + u1 - 1) // 2]['matris']); return M[:3, 3]


def parallax(a, b, z_obj, z_bg=2.6, r_px=250.):
    """Väntat homografifel i px för ett objekt på djupet z_obj, när bakgrunden (planet) ligger på z_bg: sidoförflyttning och djupförflyttning ur planens kameror."""
    d = kam(b) - kam(a); lat = abs(d[0]); dz = abs(d[1]); k = 1024. * abs(1 / z_obj - 1 / z_bg)
    return round(lat * k + r_px * dz * abs(1 / z_obj - 1 / z_bg), 1), round(float(lat), 2), round(float(dz), 2)


PAR = [('disk_C', 'S6', 'S7'), ('disk_C', 'S7', 'S6'), ('disk_C_rattad', 'S6', 'S7'), ('disk_C_rattad', 'S7', 'S6'), ('disk_C', 'S8', 'S9'), ('disk_C', 'S9', 'S8'),
       ('disk_C', 'S11', 'S8'), ('disk_C', 'S11', 'S9'), ('disk_C', 'S8', 'S11'), ('vag', 'S8', 'S9'), ('vag', 'S9', 'S8'), ('vag', 'S8', 'S10'), ('vag', 'S10', 'S8'),
       ('vag', 'S9', 'S10'), ('vag', 'S10', 'S9'), ('vag', 'S11', 'S8'), ('vag', 'S11', 'S9'), ('vag', 'S11', 'S10'), ('vag', 'S8', 'S11'), ('vag', 'S10', 'S11')]
cache = {}; rader = []
for eid, a, b in PAR:
    nyckel = (a, b)
    if nyckel not in cache: cache[nyckel] = homografi(a, b)
    Hm, inl, nm = cache[nyckel]; ba = BOX[eid].get(a); bb = BOX[eid].get(b)
    post = dict(element=eid, fran=a, till=b, homografi_inliers=inl, matchningar=nm)
    if Hm is None or inl < 40 or ba is None or bb is None:
        post['utfall'] = 'ingen koppling (för få inliers)' if (Hm is None or inl < 40) else 'ruta saknas'; rader.append(post); continue
    pts = cv2.perspectiveTransform(hornen(ba)[None], Hm)[0]; y0, x0 = pts[:, 1].min() / H * 1000, pts[:, 0].min() / W * 1000; y1, x1 = pts[:, 1].max() / H * 1000, pts[:, 0].max() / W * 1000
    t = [float(np.clip(y0, -1000, 2000)), float(np.clip(x0, -1000, 2000)), float(np.clip(y1, -1000, 2000)), float(np.clip(x1, -1000, 2000))]
    ct = [min(max(v, 0.), 1000.) for v in t]                              # klipp mot bildramen före IoU
    kanter = dict(topp=round((ct[0] - bb[0]) / 1000 * H), vanster=round((ct[1] - bb[1]) / 1000 * W), botten=round((ct[2] - bb[2]) / 1000 * H), hoger=round((ct[3] - bb[3]) / 1000 * W))
    z_obj = 1.0 if eid.startswith('disk') else .7
    post.update(overford_ruta=[round(v) for v in ct], egen_ruta=bb, iou=round(iou(ct, bb), 3), kantavstand_px=kanter,
                max_kantavstand_px=max(abs(v) for v in kanter.values()), vantat_parallaxfel_px=parallax(a, b, z_obj)[0], sidoforskjutning_m=parallax(a, b, z_obj)[1], djupforskjutning_m=parallax(a, b, z_obj)[2])
    rader.append(post)
json.dump(rader, open(f'{HERE}/korskontroll.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
with open(f'{HERE}/korskontroll.md', 'w', encoding='utf8') as f:
    f.write('| element | från→till | inliers | IoU | max kantavstånd px | väntat parallaxfel px | utfall |\n|---|---|---|---|---|---|---|\n')
    for r in rader:
        f.write(f"| {r['element']} | {r['fran']}→{r['till']} | {r['homografi_inliers']} | {r.get('iou', '–')} | {r.get('max_kantavstand_px', '–')} | {r.get('vantat_parallaxfel_px', '–')} | {r.get('utfall', '')} |\n")
print(open(f'{HERE}/korskontroll.md', encoding='utf8').read())
