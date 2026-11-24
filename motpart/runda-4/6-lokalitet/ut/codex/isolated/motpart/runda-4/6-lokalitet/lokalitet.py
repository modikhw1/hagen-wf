"""Lager 2: lokalitet per tagning ur observationer (obs/*.npz) + ev. kroppsspår (ingest_v2) och 2D-led.

Allmänna regler, inga klippkonstanter, ingen manuell inmatning:
  L1 Lodlinje: Manhattan-axlar ur MoGe-normaler; uppåtaxeln väljs med semantiska röster
     (golv/bänkskiva uppåt, vägg/dörr/fönster vertikala, tak nedåt) och stående persons bål. Ingen klamp.
  L2 Skala: kroppen som linjal (SAM3D-djup mot MoGe-djup på personytan). Saknas kropp: MoGe-metrik, märkt.
  L3 Kamera statisk per tagning. Position registreras mot 2D-led när kropp finns (projektionen bevaras).
  L4 Kamerahöjd: golvet när det syns, annars fötterna, annars antagen (märkt).
  L5 Objekt lyfts ur etikettområden: golv, väggar/dörrar/fönster, bänkar/bord/spis/skåp, maträtter.
     Mått och färg ur bilden; antaganden (t.ex. golvstående låda, skymt djup) märks per objekt.
     Objekt gäller bara i sin tagning (synlig_ut), inget smetas över klippet.
  L6 Maträtt nära en hand (<0,15 m) följer händerna; annars står den still.
Utdata: ut/<nyckel>/paket_L.json (scenpaket/2) och ut/<nyckel>/lokalitet.json (alla mått, källor, antaganden).
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, sys, time
from pathlib import Path
import cv2, numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from geom import q2R, R2q, f_px, project, world_to_cv, led_rutor  # noqa: E402

ROOT = HERE.parents[2]
STEG = 3  # pixelsteg vid lyft
COCO = {5: 'l_uparm', 6: 'r_uparm', 7: 'l_lowarm', 8: 'r_lowarm', 9: 'l_wrist', 10: 'r_wrist',
        11: 'l_upleg', 12: 'r_upleg', 13: 'l_lowleg', 14: 'r_lowleg', 15: 'l_foot', 16: 'r_foot'}
GRUPP = {
    'golv': ['floor', 'rug', 'carpet', 'sidewalk', 'road', 'path', 'earth', 'ground', 'grass', 'field'],
    'tak': ['ceiling'],
    'vagg': ['wall', 'door', 'windowpane', 'window', 'curtain', 'mirror', 'screen door', 'column', 'railing', 'fence'],
    'bank': ['countertop', 'counter', 'kitchen island', 'bar', 'buffet', 'sink'],
    'bord': ['table', 'desk', 'pool table', 'coffee table'],
    'spis': ['stove', 'oven', 'microwave', 'hood', 'dishwasher'],
    'skap': ['cabinet', 'chest of drawers', 'shelf', 'refrigerator', 'wardrobe', 'case', 'bookcase'],
    'karl': ['plate', 'tray'],
    'mat': ['food', 'bowl'],
    'person': ['person'],
}
STOD = ('golv', 'bank', 'bord', 'spis', 'skap')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _np(o):
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.ndarray): return o.tolist()
    raise TypeError(type(o))


def B_from_cv(v):
    v = np.asarray(v, float)
    return np.stack([v[..., 0], -v[..., 1], -v[..., 2]], axis=-1)


def gruppkarta(etiketter):
    out = {}
    for i, namn in etiketter.items():
        delar = [d.strip() for d in namn.lower().split(',')]
        for g, ord_ in GRUPP.items():
            if any(d == o or d.startswith(o + ' ') or o == d.split(' ')[-1] for d in delar for o in ord_):
                out[int(i)] = g; break
    return out


def ladda(out, u, gk, kalla='obs'):
    z = np.load(out / kalla / f'{u:04d}.npz')
    extra = {}
    if 'depth' in z.files:  # GPU-format: halv upplösning, djup + normerad intrinsik
        d = z['depth'].astype(np.float32); h, w = d.shape; K = z['intrinsics']
        xs = (np.arange(w) + 0.5) / w; ys = (np.arange(h) + 0.5) / h; X, Y = np.meshgrid(xs, ys)
        P = np.stack([(X - K[0, 2]) / K[0, 0] * d, (Y - K[1, 2]) / K[1, 1] * d, d], -1)
        N = z['normal'].astype(np.float32) / 127.0; M = z['mask'] & (d > 0); L = z['labels']
        segl = json.loads(bytes(z['segment']).decode())
        extra = {'I': z['instans'], 'segs': {s_['id']: s_['etikett'] for s_ in segl}, 'osakra': [s_['id'] for s_ in segl if s_['score'] < 0.75]}
        if 'geocalib' in z.files:
            extra['geo'] = json.loads(bytes(z['geocalib']).decode())
    else:
        P = z['points'].astype(np.float32)[::STEG, ::STEG]; N = z['normal'].astype(np.float32)[::STEG, ::STEG]
        M = z['mask'][::STEG, ::STEG]; L = z['labels'][::STEG, ::STEG]
    M = M & np.isfinite(P).all(-1) & np.isfinite(N).all(-1)
    G = np.full(L.shape, '', dtype=object)
    for i, g in gk.items():
        G[L == i] = g
    for i_ in extra.get('osakra', []):  # låg segmentpoäng: får inte rösta om lodlinje, golvhöjd eller lådobjekt
        G[extra['I'] == i_] = ''
    nn = np.linalg.norm(N, axis=-1, keepdims=True); N = N / np.maximum(nn, 1e-6)
    return {'P': P, 'N': N, 'M': M, 'G': G, 'L': L, 'K': z['intrinsics'], **extra}


def dominant_axel(N, w, undvik=(), fonster=math.radians(12)):
    """Dominant oriktad riktning (n och -n samma) bland normaler, ortogonal mot redan funna axlar."""
    if len(N) < 30:
        return None, 0.0
    rng = np.random.default_rng(0); best = (None, 0.0); c = math.cos(fonster)
    for idx in rng.choice(len(N), size=min(60, len(N)), replace=False):
        a = N[idx]
        if any(abs(a @ v) > math.sin(math.radians(20)) for v in undvik):
            continue
        for _ in range(6):
            d = N @ a; sel = np.abs(d) > c
            if sel.sum() < 5: break
            a = (N[sel] * np.sign(d[sel])[:, None] * w[sel, None]).sum(0); a /= np.linalg.norm(a)
            for v in undvik:
                a = a - (a @ v) * v; a /= np.linalg.norm(a)
        s = float(w[np.abs(N @ a) > c].sum())
        if s > best[1]:
            best = (a, s)
    return best


def lodlinje(obs_list, torso_cv=None):
    """Uppåt i kamerakoordinater (OpenCV: y ned). Returnerar (u, källa, detaljer)."""
    Ns, Gs = [], []
    for o in obs_list:
        sel = o['M'] & np.isin(o['G'], ['golv', 'tak', 'vagg', 'bank', 'bord', 'spis', 'skap', 'karl'])
        Ns.append(o['N'][sel]); Gs.append(o['G'][sel])
    N = np.concatenate(Ns) if Ns else np.zeros((0, 3)); G = np.concatenate(Gs) if Gs else np.zeros(0, object)
    detalj = {'strukturpixlar': int(len(N))}
    if len(N) > 20000:  # fast urval: samma resultat i förväntan, sekunder i stället för minuter
        idx = np.random.default_rng(1).choice(len(N), 20000, replace=False); N, G = N[idx], G[idx]
    axlar = []
    w = np.ones(len(N))
    for _ in range(3):
        a, s = dominant_axel(N, w, undvik=axlar)
        if a is None or s < max(40, 0.04 * len(N)):
            break
        axlar.append(a)
    if len(axlar) == 2:
        axlar.append(np.cross(axlar[0], axlar[1]))
    kand = []
    for a in axlar:
        for sgn in (1, -1):
            kand.append(sgn * a)
    if torso_cv is not None:
        t = torso_cv / np.linalg.norm(torso_cv); kand.append(t)
    if not kand:
        return None, 'ingen', detalj
    c20 = math.cos(math.radians(20))
    res = []
    for u in kand:
        d = N @ u
        golv = float(((G == 'golv') & (d > c20)).sum())
        tak = float(((G == 'tak') & (d < -c20)).sum())
        topp = float((np.isin(G, ['bank', 'bord', 'spis', 'skap']) & (d > c20)).sum()) + 0.5 * float(((G == 'karl') & (d > c20)).sum())
        fel_stod = float((np.isin(G, ['golv']) & (np.abs(d) < 0.5)).sum())
        vert_ok = float(((G == 'vagg') & (np.abs(d) < math.sin(math.radians(15)))).sum())
        vert_fel = float(((G == 'vagg') & (np.abs(d) > 0.6)).sum())
        poang = 3 * golv + 2 * tak + 1.5 * topp + 1.0 * vert_ok - 2 * vert_fel - 2 * fel_stod
        if u[1] > 0.25:      # pekar nedåt i bild: orimligt för uppåt
            poang -= 1e9
        if u[2] > math.sin(math.radians(20)):  # kameran skulle titta uppåt >20°: orimligt i 9:16-matklipp (uttalad prior)
            poang -= 1e9
        if abs(u[0]) > math.sin(math.radians(35)):  # kraftig rullning är ovanlig i stående video
            poang -= 0.5 * len(N)
        if torso_cv is not None:
            poang += 0.15 * len(N) * max(0.0, float(u @ (torso_cv / np.linalg.norm(torso_cv))) - c20) / (1 - c20)
        res.append((poang, u, {'golv': golv, 'tak': tak, 'topp': topp, 'vagg_vertikal': vert_ok, 'vagg_fel': vert_fel}))
    res.sort(key=lambda r: -r[0])
    p, u, rost = res[0]
    if p < -1e8:
        return None, 'ingen', detalj | {'roster': rost}
    fysik = p <= 0 and torso_cv is None  # semantiken säger emot; fysisk rimlighet avgör och märks
    # förfina med normaler som stöder valet
    d = N @ u; sel = (np.isin(G, list(STOD)) & (d > math.cos(math.radians(15))))
    if sel.sum() > 30:
        u2 = N[sel].mean(0); u = u2 / np.linalg.norm(u2)
    kalla = 'manhattan+semantik' if rost['golv'] + rost['topp'] + rost['tak'] > 0 else ('bål' if torso_cv is not None and u @ torso_cv > 0.9 else 'manhattan+väggar')
    if fysik:
        kalla = 'manhattan+fysisk rimlighet (etiketter motsäger: vägg som bara kan ses underifrån tolkas som liggande yta)'
    return u, kalla, detalj | {'roster': rost, 'axlar': len(axlar), 'poang': round(p, 1)}


def align_up(heading_w, up_local):
    u = up_local / np.linalg.norm(up_local); f = np.array([0, 0, -1.0])
    h = f - (f @ u) * u
    if np.linalg.norm(h) < 1e-6:
        h = np.array([0, 1.0, 0]) - u[1] * u
    h /= np.linalg.norm(h)
    hw = np.array([heading_w[0], heading_w[1], 0.0]); hw /= np.linalg.norm(hw); ez = np.array([0, 0, 1.0])
    return np.stack([hw, ez, np.cross(hw, ez)], 1) @ np.stack([h, u, np.cross(h, u)], 1).T


def euler_from_R(R):
    return [round(math.atan2(R[2, 1], R[2, 2]), 4), round(math.asin(max(-1, min(1, -R[2, 0]))), 4), round(math.atan2(R[1, 0], R[0, 0]), 4)]


def R_from_normal(n):
    n = n / np.linalg.norm(n); z = np.array([0, 0, 1.0]); v = np.cross(z, n); s = np.linalg.norm(v); c = z @ n
    if s < 1e-8:
        return np.eye(3) if c > 0 else np.diag([1, -1, -1.0])
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * ((1 - c) / s ** 2)


def farg(bgr, mask_full):
    px = bgr[mask_full]
    if len(px) < 10:
        return '#888888', None
    med = np.median(px, axis=0)[::-1]
    pal = None
    if len(px) > 50:
        Z = px[::max(1, len(px) // 4000)].astype(np.float32)
        _, lab, cen = cv2.kmeans(Z, 3, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 2, cv2.KMEANS_PP_CENTERS)
        order = np.argsort(-np.bincount(lab.ravel(), minlength=3))
        pal = ['#%02x%02x%02x' % tuple(int(v) for v in cen[i][::-1]) for i in order]
    return '#%02x%02x%02x' % tuple(int(v) for v in med), pal


# ---------- kroppar ----------
def fit_kamera_mot_2d(A, pose, sid, pids, C, R, lens, W, H, ix, sk):
    f = f_px(lens, W); obs = []
    for pid in pids:
        fr, X = led_rutor(A, pid, sid)
        if X is None:
            continue
        for u, J in list(zip(fr, X))[::2]:
            pp = pose['rutor'][u]['personer'] if u < len(pose['rutor']) else []
            if not pp:
                continue
            uv, _ = project(J, C, R, f, W, H); uv = uv * sk
            cen = uv[[ix['l_uparm'], ix['r_uparm'], ix['l_upleg'], ix['r_upleg']]].mean(0)
            p = min(pp, key=lambda p: np.hypot((p['box'][0] + p['box'][2]) / 2 - cen[0], (p['box'][1] + p['box'][3]) / 2 - cen[1]))
            kp = np.array(p['kp'])
            e = [np.linalg.norm(uv[ix[j]] - kp[c, :2]) for c, j in COCO.items() if kp[c, 2] > .5]
            if len(e) < 3 or np.median(e) > 350:
                continue
            for c, j in COCO.items():
                if kp[c, 2] > 0.5:
                    obs.append((J[ix[j]], kp[c, :2] / sk))
    if len(obs) < 12:
        return C, None, None, len(obs)
    Pj = np.array([o[0] for o in obs]); Q = np.array([o[1] for o in obs])

    def res(dx):
        uv, _ = project(Pj, C + dx, R, f, W, H); return (uv - Q).reshape(-1)
    r0 = float(np.median(np.linalg.norm(res(np.zeros(3)).reshape(-1, 2), axis=1)) * sk)
    s = least_squares(res, np.zeros(3), loss='soft_l1', f_scale=15.0, bounds=([-1.5, -2.0, -1.5], [1.5, 2.0, 1.5]))
    r1 = float(np.median(np.linalg.norm(s.fun.reshape(-1, 2), axis=1)) * sk)
    return C + s.x, round(r0, 1), round(r1, 1), len(obs)


def spar_2d(A, pose, sid, pids, C, R, lens, W, H, ix, sk):
    """Per spår: projicerad 2D-ruta per ruta och medianfel mot närmaste 2D-person (originalets leder)."""
    f = f_px(lens, W); ut = {}
    for pid in pids:
        fr, X = led_rutor(A, pid, sid)
        if X is None:
            continue
        lador, fel = {}, []
        for u, J in zip(fr, X):
            uv, z = project(J, C, R, f, W, H); uv = uv * sk; ok = z > 0
            if ok.sum() < 5:
                continue
            q = uv[ok]; lador[int(u)] = (q[:, 0].min(), q[:, 1].min(), q[:, 0].max(), q[:, 1].max())
            pp = pose['rutor'][u]['personer'] if pose and u < len(pose['rutor']) else []
            best = None
            for p_ in pp:
                kp = np.array(p_['kp'])
                e = [np.linalg.norm(uv[ix[j]] - kp[c, :2]) for c, j in COCO.items() if kp[c, 2] > .5 and z[ix[j]] > 0]
                if len(e) >= 3:
                    m = float(np.median(e)); best = m if best is None else min(best, m)
            if best is not None:
                fel.append(best)
        ut[pid] = {'lador': lador, 'fel': float(np.median(fel)) if fel else None, 'n2d': len(fel)}
    return ut


def ta_bort_dubbletter_2d(info2d, pids):
    """L3b: två spår är samma person om deras projicerade 2D-rutor överlappar (median-IoU > 0,4),
    oavsett djup. Spåret med lägst 2D-fel (annars flest rutor) behålls."""
    def iou(a, b):
        x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
        i = max(0, x1 - x0) * max(0, y1 - y0); u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
        return i / u if u > 0 else 0.0
    rang = sorted([p for p in pids if p in info2d], key=lambda p: (info2d[p]['fel'] if info2d[p]['fel'] is not None else 1e9, -len(info2d[p]['lador'])))
    keep, bort = [], []
    for p in rang:
        dub = False
        for q in keep:
            gem = set(info2d[p]['lador']) & set(info2d[q]['lador'])
            if len(gem) >= 3 and np.median([iou(info2d[p]['lador'][u], info2d[q]['lador'][u]) for u in gem]) > 0.4:
                dub = True; break
        (bort if dub else keep).append(p)
    return keep + [p for p in pids if p not in info2d], bort


def ta_bort_dubbletter(A, sid, pids, ix):
    if len(pids) < 2:
        return pids, []
    i = ix['c_spine2']; X = {p: led_rutor(A, p, sid)[1] for p in pids}
    keep = []; bort = []
    langd = {p: len(X[p]) for p in pids}
    for p in sorted(pids, key=lambda p: -langd[p]):
        if any(np.median(np.linalg.norm(X[p][:min(len(X[p]), len(X[q]))][:, i] - X[q][:min(len(X[p]), len(X[q]))][:, i], axis=1)) < 0.6 for q in keep):
            bort.append(p)
        else:
            keep.append(p)
    return keep, bort


# ---------- objekt ----------
def komponenter(mask, min_px):
    n, lab = cv2.connectedComponents(mask.astype(np.uint8), connectivity=8)
    return [lab == k for k in range(1, n) if (lab == k).sum() >= min_px]


def lyft_objekt(o, Xw, up_w, sid, a0, b0, bgr, H0, W0, nr):
    """Objekt i världen ur en nyckelruta. Xw: världspunkter (h,w,3)."""
    ut = []; M = o['M']; G = o['G']
    big = lambda m: cv2.resize(m.astype(np.uint8), (W0, H0), interpolation=cv2.INTER_NEAREST).astype(bool)
    golv = M & (G == 'golv')
    if golv.sum() > max(40, 0.005 * M.sum()):
        pts = Xw[golv]; lo = np.percentile(pts[:, :2], 2, 0); hi = np.percentile(pts[:, :2], 98, 0)
        fg, _ = farg(bgr, big(golv))
        ut.append({'id': f'golv_{sid}', 'bas': 'golv', 'typ': 'golv', 'pos': [*((lo + hi) / 2).round(3).tolist(), -0.02], 'rot': [0, 0, 0],
                   'matt': [*(hi - lo + 0.6).round(2).tolist(), 0.04], 'farg': fg, 'tilltro': 'skattad_ur_bild', 'rum': sid,
                   'synlig_ut': [[a0, b0]], 'kalla': f'golvpixlar {int(golv.sum())}'})
    def komp(g, min_px):
        if 'I' in o:
            return [c for c in ((o['I'] == i_) & M for i_, lab in o['segs'].items() if o['gk'].get(lab) == g) if c.sum() >= min_px]
        return komponenter(M & (G == g), min_px)
    for g in ('vagg', 'bank', 'bord', 'spis', 'skap'):
        for k, comp in enumerate(komp(g, 25 if g != 'vagg' else 40)):
            pts = Xw[comp]; nrm = o['Nw'][comp]
            fg, _ = farg(bgr, big(comp)); oid = f'{g}_{sid}_{nr}{k}'
            if g == 'vagg':
                hn = nrm - (nrm @ up_w)[:, None] * up_w; hn = np.median(hn, 0)
                if np.linalg.norm(hn) < 0.3:
                    continue
                hn /= np.linalg.norm(hn); t = np.cross(up_w, hn)
                s_ = pts @ t; d_ = pts @ hn
                lo, hi = np.percentile(s_, 3), np.percentile(s_, 97); z0, z1 = max(0.0, np.percentile(pts[:, 2], 3)), np.percentile(pts[:, 2], 97)
                if hi - lo < 0.15 or z1 - z0 < 0.15:
                    continue
                c = t * (lo + hi) / 2 + hn * np.median(d_); c[2] = (z0 + z1) / 2
                yaw = math.atan2(t[1], t[0])
                ut.append({'id': oid, 'bas': 'vagg', 'typ': 'vagg', 'pos': c.round(3).tolist(), 'rot': [0, 0, round(yaw, 4)],
                           'matt': [round(hi - lo, 2), 0.04, round(z1 - z0, 2)], 'farg': fg, 'tilltro': 'skattad_ur_bild', 'rum': sid,
                           'synlig_ut': [[a0, b0]], 'kalla': f'vertikalt plan ur {int(comp.sum())} punkter; spridning {np.std(d_):.2f} m'})
                continue
            topp = (nrm @ up_w) > math.cos(math.radians(25))
            antag = []
            if topp.sum() >= 12:
                top_z = float(np.median(pts[topp, 2]))
            else:
                top_z = float(np.percentile(pts[:, 2], 95)); antag.append('topp skymd: översta synliga punkt')
            xy = pts[:, :2]; m0 = xy.mean(0); cov = np.cov((xy - m0).T)
            if not np.all(np.isfinite(cov)):
                continue
            ev, evec = np.linalg.eigh(cov); ax = evec[:, 1]; yaw = math.atan2(ax[1], ax[0])
            Rz = np.array([[math.cos(yaw), -math.sin(yaw)], [math.sin(yaw), math.cos(yaw)]])
            loc = (xy - m0) @ Rz; lo = np.percentile(loc, 4, 0); hi = np.percentile(loc, 96, 0)
            dim = hi - lo
            if dim[1] < 0.25:
                antag.append('djup skymt: minst 0,40 m antaget'); dim[1] = 0.4
            if dim[0] < 0.1 or top_z < 0.15 or top_z > 2.6:
                continue
            cen = m0 + Rz @ ((lo + hi) / 2)
            p5 = float(np.percentile(pts[:, 2], 5))
            if p5 > 0.6:
                botten = p5; antag.append('väggmonterad: underkant = lägsta synliga punkt')
            else:
                botten = 0.0; antag.append('antas stå på golvet')
            ut.append({'id': oid, 'bas': g, 'typ': {'bank': 'bank', 'bord': 'bord', 'spis': 'spis', 'skap': 'prop'}[g],
                       'pos': [round(float(cen[0]), 3), round(float(cen[1]), 3), round((top_z + botten) / 2, 3)], 'rot': [0, 0, round(yaw, 4)],
                       'matt': [round(float(dim[0]), 2), round(float(dim[1]), 2), round(top_z - botten, 2)], 'farg': fg,
                       'tilltro': 'skattad_ur_bild' if len(antag) <= 1 else 'harledd_mall', 'rum': sid, 'synlig_ut': [[a0, b0]],
                       'kalla': f'{int(comp.sum())} punkter, topp {"uppmätt" if topp.sum() >= 12 else "skymd"} {top_z:.2f} m', 'antaganden': antag})
    retter = []
    if 'I' in o:  # kärl (tallrik/skål/bricka) som instanser; mat som rör ett kärl slås ihop med det
        namn_ = o['namn']; kar, mat = [], []
        for i_, lab in o['segs'].items():
            if o['gk'].get(lab) not in ('mat', 'karl'):
                continue
            m_ = (o['I'] == i_) & M
            if m_.sum() < 15:
                continue
            (mat if 'food' in namn_.get(lab, '') else kar).append(m_)
        for m_ in mat:
            dil = cv2.dilate(m_.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
            hit = [j for j, k_ in enumerate(kar) if (k_ & dil).any()]
            if hit:
                kar[hit[0]] = kar[hit[0]] | m_
            else:
                kar.append(m_)
        mat_komp = kar
    else:
        mat_komp = komponenter(M & np.isin(G, ['mat', 'karl']), 15)
    for k, comp in enumerate(mat_komp):
        pts = Xw[comp]; m0 = pts.mean(0); U, S, Vt = np.linalg.svd(pts - m0, full_matrices=False)
        n = Vt[2]; n = n if n @ up_w > 0 else -n
        r = float(np.percentile(np.linalg.norm((pts - m0) - ((pts - m0) @ n)[:, None] * n, axis=1), 95))
        if not 0.03 < r < 0.4:
            continue
        lab = o['L'][comp]; namn = o['namn']; typer = [namn.get(int(v), '') for v in lab]
        typ = 'mat_skal' if sum('bowl' in t for t in typer) > 0.4 * len(typer) else 'mat_bricka' if sum('tray' in t for t in typer) > 0.4 * len(typer) else 'mat_tallrik'
        fg, pal = farg(bgr, big(comp))
        retter.append({'centrum': m0, 'normal': n, 'diameter': 2 * r, 'typ': typ, 'farg': fg, 'palett': pal, 'punkter': int(comp.sum())})
    return ut, retter


def fusera_lodlinje(u_moge, spridning, obs, torso):
    """L1b: vittnen viktas efter osäkerhet; den som avviker > 2,5 sigma från fusionen stryks (en omgång).
    MoGe-Manhattan: sigma = max(3, medianspridning mellan nyckelrutor). GeoCalib: egen osäkerhet, x4 över 20 graders lutning (underskattar branta vinklar).
    Stående bål: 6 grader."""
    vitt = []
    if u_moge is not None:
        vitt.append(['moge', u_moge / np.linalg.norm(u_moge), max(3.0, float(np.median(spridning)) if spridning else 3.0)])  # median: en avvikande ruta fäller inte vittnet
    gv = [np.array(o['geo']['gravity_vec3d'], float) for o in obs if o.get('geo') and 'gravity_vec3d' in o['geo']]
    if gv:
        ug = np.median(np.array([v / np.linalg.norm(v) for v in gv]), 0); ug /= np.linalg.norm(ug)
        sg = float(np.median([math.degrees(o['geo'].get('gravity_uncertainty', math.radians(10))) for o in obs if o.get('geo') and 'gravity_vec3d' in o['geo']]))
        if abs(math.degrees(math.asin(max(-1, min(1, ug[2]))))) > 20:  # GeoCalib underskattar branta vinklar i detta material
            sg *= 4
        vitt.append(['geocalib', ug, max(1.5, sg)])
    if torso is not None:
        vitt.append(['bål', torso / np.linalg.norm(torso), 6.0])
    if not vitt:
        return None, []
    def fus(vv):
        u = sum(v[1] / v[2] ** 2 for v in vv); return u / np.linalg.norm(u)
    u = fus(vitt)
    ang = lambda a_, b_: math.degrees(math.acos(max(-1, min(1, float(a_ @ b_)))))
    ut = [v for v in vitt if ang(v[1], u) <= 2.5 * v[2]] or vitt
    if len(ut) < len(vitt):
        u = fus(ut)
    rapport = [{'vittne': v[0], 'sigma_grader': round(v[2], 1), 'avvikelse_grader': round(ang(v[1], u), 1), 'med': v in ut} for v in vitt]
    return u, rapport


def _rz(th):
    c_, s_ = math.cos(th), math.sin(th)
    return np.array([[c_, -s_, 0], [s_, c_, 0], [0, 0, 1.0]])


def rum_over_tagningar(tdata, frames, W0, H0, min_inl=40, tro_m=0.10):
    """L7: tagningar på samma plats binds i en gemensam ram.
    SIFT (personer maskade) -> fundamentalmatris (MAGSAC) -> 3D-punkter ur båda tagningarnas världsram ->
    stel transform med gir + förflyttning (lodlinjen är redan gemensam) via RANSAC. Grupper via spännande träd."""
    sift = cv2.SIFT_create(4000); kp = {}
    for t in tdata:
        g = cv2.cvtColor(frames[t['u']], cv2.COLOR_BGR2GRAY)
        pm = cv2.resize(t['pers'].astype(np.uint8), (W0, H0), interpolation=cv2.INTER_NEAREST).astype(bool)
        mask = (~pm).astype(np.uint8) * 255
        mask[: int(0.06 * H0)] = 0  # logotyper/text i överkant följer inte rummet
        kp[t['sid']] = sift.detectAndCompute(g, mask)
    bf = cv2.BFMatcher(); kanter = []; par = {}

    def X(t, p_):
        h, w = t['Xw'].shape[:2]
        xi = np.clip((p_[:, 0] * w / W0).astype(int), 0, w - 1); yi = np.clip((p_[:, 1] * h / H0).astype(int), 0, h - 1)
        return t['Xw'][yi, xi], t['M'][yi, xi]

    for i in range(len(tdata)):
        for j in range(i + 1, len(tdata)):
            a_, b_ = tdata[i], tdata[j]; ka, da = kp[a_['sid']]; kb, db = kp[b_['sid']]
            if da is None or db is None or len(ka) < 50 or len(kb) < 50:
                continue
            mm = [m for m, n in bf.knnMatch(da, db, k=2) if m.distance < 0.75 * n.distance]
            if len(mm) < min_inl:
                continue
            pa = np.float32([ka[m.queryIdx].pt for m in mm]); pb = np.float32([kb[m.trainIdx].pt for m in mm])
            Fm, inl = cv2.findFundamentalMat(pa, pb, cv2.USAC_MAGSAC, 1.5, 0.999, 10000)
            if Fm is None or inl is None or inl.sum() < min_inl:
                continue
            inl = inl.ravel().astype(bool); pa, pb = pa[inl], pb[inl]
            XA, vA = X(a_, pa); XB, vB = X(b_, pb)
            ok = vA & vB & np.isfinite(XA).all(1) & np.isfinite(XB).all(1)
            XA, XB = XA[ok], XB[ok]
            if len(XA) < 20:
                continue
            rng = np.random.default_rng(0); bast = (None, 0)
            for _ in range(400):  # RANSAC: gir + förflyttning ur två punkter (B -> A)
                i1, i2 = rng.choice(len(XA), 2, replace=False)
                va, vb = XA[i2, :2] - XA[i1, :2], XB[i2, :2] - XB[i1, :2]
                if np.linalg.norm(va) < 0.1 or np.linalg.norm(vb) < 0.1:
                    continue
                th = math.atan2(va[1], va[0]) - math.atan2(vb[1], vb[0]); Rz = _rz(th); tv = XA[i1] - Rz @ XB[i1]
                n = int((np.linalg.norm(XA - (XB @ Rz.T + tv), axis=1) < tro_m).sum())
                if n > bast[1]:
                    bast = ((th, tv), n)
            if bast[0] is None or bast[1] < 20:
                continue
            th, tv = bast[0]; Rz = _rz(th)
            sel = np.linalg.norm(XA - (XB @ Rz.T + tv), axis=1) < tro_m
            A2, B2 = XA[sel], XB[sel]; ma, mb = A2.mean(0), B2.mean(0)
            Hm = (B2[:, :2] - mb[:2]).T @ (A2[:, :2] - ma[:2]); th = math.atan2(Hm[0, 1] - Hm[1, 0], Hm[0, 0] + Hm[1, 1])
            Rz = _rz(th); tv = ma - Rz @ mb
            r = np.linalg.norm(A2 - (B2 @ Rz.T + tv), axis=1)
            par[(a_['sid'], b_['sid'])] = {'sift_inliers': int(inl.sum()), 'punkter_3d': int(len(XA)), 'inliers_3d': int(sel.sum()),
                                           'andel_3d': round(float(sel.mean()), 2), 'median_rest_cm': round(float(np.median(r)) * 100, 1),
                                           'gir_grader': round(math.degrees(th), 1), 'T': (Rz, tv)}
            if sel.sum() >= 20 and sel.mean() >= 0.25:
                kanter.append((int(sel.sum()), a_['sid'], b_['sid']))
    ids = [t['sid'] for t in tdata]; grann = {i: [] for i in ids}
    for n, a_, b_ in sorted(kanter, reverse=True):
        grann[a_].append((b_, n)); grann[b_].append((a_, n))
    T = {}; grupper = []; sett = set()
    for start in sorted(ids, key=lambda i: -sum(n for _, n in grann[i])):
        if start in sett or not grann[start]:
            continue
        T[start] = (np.eye(3), np.zeros(3)); ko = [start]; sett.add(start); grp = [start]
        while ko:
            x = ko.pop(0)
            for y, _ in sorted(grann[x], key=lambda z: -z[1]):
                if y in sett:
                    continue
                if (x, y) in par:  # par[(a,b)] mappar b:s ram in i a:s
                    Rz, tv = par[(x, y)]['T']
                else:
                    Rz0, tv0 = par[(y, x)]['T']; Rz = Rz0.T; tv = -Rz0.T @ tv0
                Rx, tx = T[x]; T[y] = (Rx @ Rz, Rx @ tv + tx); sett.add(y); ko.append(y); grp.append(y)
        grupper.append(grp)
    rap = {'grupper': grupper, 'par': {f'{a_}-{b_}': {k_: v_ for k_, v_ in d.items() if k_ != 'T'} for (a_, b_), d in par.items()}}
    return T, rap


def bygg_nat(o, Xw, Zc, namn, gk, F=3, hopp=0.06, andra=(), kamera=None):
    """Instanser som texturerade nät: rutnät ur djupet, en bit per OneFormer-instans, personer utanför.
    Trianglar över djupsprång (> hopp relativt) eller instansgränser tas bort. UV pekar i originalbilden."""
    if 'I' not in o:
        return None
    I = o['I'][::F, ::F]; V = Xw[::F, ::F]; Z = Zc[::F, ::F]; M = o['M'][::F, ::F] & np.isfinite(V).all(-1) & (Z > 0)
    h0, w0 = o['P'].shape[:2]; h, w = I.shape
    ii, jj = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    U = np.stack([(jj * F + 0.5) / w0, 1.0 - (ii * F + 0.5) / h0], -1)
    lab = {i_: l_ for i_, l_ in o['segs'].items()}
    grupp_av = lambda i_: gk.get(lab.get(int(i_), -1), 'ovrigt') if int(i_) in lab else 'ovrigt'
    person = np.vectorize(lambda i_: grupp_av(i_) == 'person')(I) if I.size else np.zeros_like(M)
    person = cv2.dilate(person.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    M = M & ~person
    I = I.astype(np.int32).copy(); V = V.copy(); Z = Z.copy()
    # Hål bakom personen: (1) observerad bakgrund ur andra nyckelrutor (statisk kamera = samma pixelstråle)
    hal = person.copy(); fyllt_obs = 0
    kalla_id = {}
    for kk, (o2, X2, Z2) in enumerate(andra):
        kalla_id[-(10 + kk)] = o2['u']
        I2 = o2['I'][::F, ::F]; ok2 = o2['M'][::F, ::F] & np.isfinite(X2[::F, ::F]).all(-1) & (Z2[::F, ::F] > 0)
        p2 = np.vectorize(lambda i_: o2['gk'].get(o2['segs'].get(int(i_), -1), '') == 'person')(I2) if I2.size else np.zeros_like(ok2)
        p2 = cv2.dilate(p2.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)  # försiktig: hellre antaget än person på väggen
        tag = hal & ok2 & ~p2
        V[tag] = X2[::F, ::F][tag]; Z[tag] = Z2[::F, ::F][tag]; I[tag] = -(10 + kk); M[tag] = True; hal &= ~tag; fyllt_obs += int(tag.sum())
    # (2) det som aldrig syns: bara DJUPET fylls från omgivningen och punkten läggs på pixelns stråle (antaget, egen bit).
    # Att fylla världskoordinater gav vilda skärvor från andra vinklar.
    fyllt_ant = 0
    if hal.any() and M.any() and kamera is not None:
        C_, R_, fxn, fyn = kamera
        kand = (M & ~hal).astype(np.float32); zz = np.where(M & ~hal, Z, 0).astype(np.float32)
        Zf = np.zeros_like(zz)
        for sig in (4.0, 12.0, 36.0):  # normaliserad faltning: slät fyllnad, grövre skala där hålet är stort
            num = cv2.GaussianBlur(zz * kand, (0, 0), sig); den = cv2.GaussianBlur(kand, (0, 0), sig)
            Zf = np.where((Zf == 0) & (den > 1e-3), num / np.maximum(den, 1e-6), Zf)
        xn = (jj * F + 0.5) / w0; yn = (ii * F + 0.5) / h0
        ray = np.stack([(xn - 0.5) / fxn, (yn - 0.5) / fyn, np.ones_like(xn)], -1)
        Vf = C_ + (R_ @ B_from_cv(ray * Zf[..., None]).reshape(-1, 3).T).T.reshape(ray.shape)
        V = np.where(hal[..., None], Vf, V); Z = np.where(hal, Zf, Z)
        I[hal] = -3; M = M | (hal & (Z > 0)); fyllt_ant = int(hal.sum())
    a_, b_, c_, d_ = (slice(0, -1), slice(0, -1)), (slice(0, -1), slice(1, None)), (slice(1, None), slice(0, -1)), (slice(1, None), slice(1, None))
    idx = (ii * w + jj)
    bitar = []; pos_all = []; uv_all = []; ind_all = []; off_v = 0
    tris = []
    for (p, q, r) in ((a_, c_, b_), (b_, c_, d_)):
        ok = M[p] & M[q] & M[r]
        zmax = np.maximum(np.maximum(Z[p], Z[q]), Z[r]); zmin = np.minimum(np.minimum(Z[p], Z[q]), Z[r])
        ok &= (zmax / np.maximum(zmin, 1e-6)) < 1 + hopp
        # Gränstrianglar (kontinuerligt djup) tillhör majoritetsinstansen: inga sprickor, bitarna förblir separata
        maj = np.where((I[p] == I[q]) | (I[p] == I[r]), I[p], np.where(I[q] == I[r], I[q], I[p]))
        tris.append((idx[p][ok], idx[q][ok], idx[r][ok], maj[ok]))
    T = np.concatenate([np.stack(t[:3], 1) for t in tris]); TI = np.concatenate([t[3] for t in tris])
    Vf = V.reshape(-1, 3); Uf = U.reshape(-1, 2)
    for inst in np.unique(TI):
        tt = T[TI == inst]
        if len(tt) < 8:
            continue
        uniq, inv = np.unique(tt.ravel(), return_inverse=True)
        pos = Vf[uniq].astype(np.float32); uv = Uf[uniq].astype(np.float32); ind = inv.astype(np.uint32)
        l_ = lab.get(int(inst), -1)
        if int(inst) in kalla_id:
            etik = f'bakom person (observerad i ruta {kalla_id[int(inst)]})'
        elif int(inst) == -3:
            etik = 'bakom person (antagen, fylld från omgivningen)'
        else:
            etik = namn.get(l_, 'omärkt') if l_ != -1 else 'omärkt'
        bitar.append({'instans': int(inst), 'etikett': etik, 'grupp': 'bakom_person' if inst < -1 else grupp_av(inst),
                      'tilltro': 'antagen' if inst == -3 else 'skattad_ur_bild',
                      'textur_ruta': kalla_id.get(int(inst)), 'textur': 'ingen' if inst == -3 else ('fryst' if int(inst) in kalla_id else 'original'),
                      'nv': int(len(pos)), 'ni': int(len(ind)), 'centrum': pos.mean(0).round(3).tolist(),
                      'min': pos.min(0).round(3).tolist(), 'max': pos.max(0).round(3).tolist()})
        pos_all.append(pos); uv_all.append(uv); ind_all.append(ind)
    if not bitar:
        return None
    blob = b''; off = 0
    for bi, pos, uv, ind in zip(bitar, pos_all, uv_all, ind_all):
        for nyck, arr in (('pos', pos), ('uv', uv), ('ind', ind)):
            raw = arr.tobytes(); bi[nyck] = [off, len(raw)]; blob += raw; off += len(raw)
    return bitar, blob


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('nyckel'); ap.add_argument('--obs', choices=['gpu', 'cpu'], default=None); a = ap.parse_args()
    t0 = time.perf_counter(); out = HERE / 'ut' / a.nyckel
    kalla = a.obs or ('gpu' if (out / 'obs_gpu.json').is_file() else 'cpu')
    obsdir, suffix = ('obs_gpu', '') if kalla == 'gpu' else ('obs', '_cpu')
    meta = json.loads((out / (obsdir + '.json')).read_text(encoding='utf-8'))
    gk = gruppkarta(meta['etiketter']); namn = {int(k): v for k, v in meta['etiketter'].items()}
    W0, H0 = meta['bild_px']
    video = ROOT / 'data/format/kontroll/klipp' / (meta['klipp'] + '.mp4')
    cap = cv2.VideoCapture(str(video)); frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    A_fil = next((p_ for p_ in (ROOT / 'arbetsbord/data/ingest_v2' / a.nyckel / 'paket.json', out / 'ingest_v2' / 'paket.json') if p_.is_file()), out / 'saknas.json')
    A = json.loads(A_fil.read_text(encoding='utf-8')) if A_fil.is_file() else None
    pose = json.loads((out / 'pose2d.json').read_text(encoding='utf-8')) if (out / 'pose2d.json').is_file() else None
    if A:
        L = copy.deepcopy(A); ix = {n: i for i, n in enumerate(A['leder'])}; W, H = A['bild']['bredd'], A['bild']['hojd']
    else:
        L = {'schema': 'scenpaket/2', 'klipp': {'id': meta['klipp'], 'nyckel': a.nyckel}, 'tidsbas': {'fps': meta['fps'], 'antal_rutor': meta['antal_rutor'], 'regel': 'original'},
             'bild': {'bredd': W0, 'hojd': H0, 'sensor_mm': 36.0}, 'koordinater': 'Blender: Z upp, meter; kvaternion (w,x,y,z); leder i hel-mm.',
             'golv_z': 0.0, 'objekt': [], 'tagningar': [], 'personer': {}, 'leder': [], 'rorelse': {}}
        ix = {}; W, H = W0, H0
    sk = W0 / W
    L['klipp']['variant'] = 'L: lokalitet/1 (motpart/runda-4/6-lokalitet)'
    rapport = {'variant': 'L', 'klipp': meta['klipp'], 'kalla_sha256': meta['kalla_sha256'], 'kod_sha256': sha(__file__),
               'A_paket_sha256': sha(A_fil) if A else None, 'modeller': meta['modeller'], 'tagningar': {}}
    objekt = []; nya_tagningar = []; nya_rorelse = {p: [] for p in (A['rorelse'] if A else {})}; nat_manifest = {}; tdata = []
    for s in meta['tagningar']:
        sid = s['id']; a0, b0 = s['ut']; info = {'nyckelrutor': s['nyckelrutor']}
        obs = []
        for u in s['nyckelrutor']:
            o = ladda(out, u, gk, obsdir); o['u'] = u; o['namn'] = namn; o['gk'] = gk; obs.append(o)
        K = obs[len(obs) // 2]['K']; fx_n = float(K[0, 0]); lens_moge = round(36.0 * fx_n, 2)
        tA = next((t for t in A['tagningar'] if t['id'] == sid), None) if A else None
        pids = [p['id'] for p in tA['personer']] if tA else []
        if tA:
            kA = tA['kamera']['nycklar'][0]; R_A = q2R(kA[4:8]); lens = float(kA[8]); C0 = np.array([0, 0, 1.38])
            pids, dub = ta_bort_dubbletter(A, sid, pids, ix)
            info2d = spar_2d(A, pose, sid, pids, C0, R_A, lens, W, H, ix, sk)
            pids, dub2 = ta_bort_dubbletter_2d(info2d, pids)
            dub = dub + dub2
            if dub:
                info['dubbletter_bort'] = dub
            info['spar_2d_fel_px'] = {p: (round(v['fel'], 1) if v['fel'] is not None else None) for p, v in info2d.items()}
            C_reg, e0, e1, nobs = fit_kamera_mot_2d(A, pose, sid, pids, C0, R_A, lens, W, H, ix, sk) if pose else (C0, None, None, 0)
            info['registrering_2d_px'] = {'fore': e0, 'efter': e1, 'observationer': nobs}
            kropp_ok = [p for p in pids if e1 is not None]
            # L3c: spår utan stöd i originalets 2D-led (fel > 3x bästa och > 120 px) märks antagna och påverkar inte skala/lodlinje/höjd
            fel_ok = [v['fel'] for v in info2d.values() if v['fel'] is not None]
            bast = min(fel_ok) if fel_ok else None
            utan_stod = [p for p in kropp_ok if bast is None or info2d.get(p, {}).get('fel') is None or info2d[p]['fel'] > max(3 * bast, 120)]
            if bast is not None and len(utan_stod) == len(kropp_ok):
                utan_stod = [p for p in utan_stod if info2d.get(p, {}).get('fel') != bast]
            if utan_stod:
                info['spar_utan_2d_stod'] = utan_stod
            heading = R_A @ np.array([0, 0, -1.0])
        else:
            lens = lens_moge; R_A = None; C_reg = None; kropp_ok = []; heading = np.array([0, 1.0, 0]); utan_stod = []
        info['lins_mm'] = {'anvand': round(lens, 2), 'moge_denna_korning': lens_moge}
        f_m = f_px(lens, W)
        # En intrinsik för allt: MoGe-punkterna projiceras om till kamerans brännvidd (djup skalas med kvoten),
        # så att kropp (SAM3D, A:s brännvidd), kamera och rum delar samma strålar.
        fxA, fyA = f_m / W, f_m / H
        for o in obs:
            Kn = o['K']; X, Y, Z = o['P'][..., 0], o['P'][..., 1], o['P'][..., 2]
            with np.errstate(divide='ignore', invalid='ignore'):
                un = Kn[0, 0] * X / Z + Kn[0, 2]; vn = Kn[1, 1] * Y / Z + Kn[1, 2]
                Z2 = Z * fxA / Kn[0, 0]
                o['P'] = np.stack([(un - 0.5) / fxA * Z2, (vn - 0.5) / fyA * Z2, Z2], -1).astype(np.float32)
            o['M'] = o['M'] & np.isfinite(o['P']).all(-1)
        # kroppar i kamerakoordinater (OpenCV), via registrerad kamera
        Jcv = {}
        for p in kropp_ok:
            fr, X = led_rutor(A, p, sid); Jcv[p] = (fr, world_to_cv(X, C_reg, R_A))
        # L2 skala: personytans MoGe-djup mot kroppens djup
        skalor = []
        for o in obs:
            for p, (fr, J) in Jcv.items():
                if o['u'] not in list(fr):
                    continue
                Ju = J[list(fr).index(o['u'])]
                tor = Ju[[ix['l_uparm'], ix['r_uparm'], ix['l_upleg'], ix['r_upleg'], ix['c_spine2']]]
                uv = np.stack([f_m * tor[:, 0] / tor[:, 2] + W / 2, f_m * tor[:, 1] / tor[:, 2] + H / 2], 1) * sk * (o['P'].shape[1] / W0)
                zs = []
                for x, y in uv:
                    xi, yi = int(round(x)), int(round(y))
                    if 0 <= yi < o['P'].shape[0] and 0 <= xi < o['P'].shape[1]:
                        win = (slice(max(0, yi - 2), yi + 3), slice(max(0, xi - 2), xi + 3))
                        sel = o['M'][win] & (o['G'][win] == 'person')
                        if sel.sum() >= 3:
                            zs.append(float(np.median(o['P'][win][sel][:, 2])))
                if len(zs) >= 3:
                    skalor.append((float(np.median(tor[:, 2])) - 0.08) / float(np.median(zs)))
        if skalor:
            skala = float(np.median(skalor)); info['skala'] = {'varde': round(skala, 3), 'kalla': 'kropp (SAM3D-djup mot MoGe-personyta)', 'prov': len(skalor)}
        else:
            skala = 1.0; info['skala'] = {'varde': 1.0, 'kalla': 'MoGe-metrik, ej ankrad (antagen)'}
        # L1 lodlinje
        torso = None
        if Jcv:
            v = [];
            for p, (fr, J) in Jcv.items():
                if A['personer'][p]['pose'] == 'staende' and p not in utan_stod:
                    v += list(J[:, ix['c_neck']] - J[:, ix['c_spine0']])
            if v:
                t = np.median(np.array(v), 0); torso = t / np.linalg.norm(t)  # bålens uppåtriktning i cv
        u_cv, kalla, det = lodlinje(obs, None)  # W1 ren MoGe+semantik (bålen är eget vittne)
        if u_cv is None:
            if R_A is not None:
                up_loc = R_A.T @ np.array([0, 0, 1.0]); u_cv = np.array([up_loc[0], -up_loc[1], -up_loc[2]])
            else:
                u_cv = np.array([0, -1.0, 0])
            kalla = 'reserv: A-rotation' if R_A is not None else 'reserv: bildens uppåt (antagen)'
        info['lodlinje'] = {'kalla': kalla, **det}
        # Diagnos: lodlinje per nyckelruta (statisk kamera => bör sammanfalla)
        per = [lodlinje([o], None)[0] for o in obs]
        vink = [round(math.degrees(math.acos(max(-1, min(1, float(p_ @ u_cv))))), 1) for p_ in per if p_ is not None]
        info['lodlinje']['spridning_per_ruta_grader'] = vink
        # L1b: fusion av vittnen (MoGe, GeoCalib, stående bål)
        u_f, vrap = fusera_lodlinje(u_cv if not kalla.startswith('reserv') else None, vink, obs, torso)
        if u_f is not None:
            info['lodlinje']['vittnen'] = vrap; info['lodlinje']['moge_kalla'] = kalla
            kalla = 'fusion: ' + ', '.join(v['vittne'] for v in vrap if v['med']); u_cv = u_f
            info['lodlinje']['kalla'] = kalla
        R = align_up(heading, B_from_cv(u_cv))
        fwd = R @ np.array([0, 0, -1.0]); info['lutning_grader'] = round(math.degrees(math.asin(max(-1, min(1, fwd[2])))), 1)
        if R_A is not None:
            fA = R_A @ np.array([0, 0, -1.0]); info['A_lutning_grader'] = round(math.degrees(math.asin(fA[2])), 1)
        # L2b Kontaktskala: står personen och syns golvet ska fötterna stå på golvet. Golvets höjd under kameran
        # (MoGe, oskalad) mot fötternas (kropp) ger skalan; personytans djup blir diagnos.
        golv_h0 = []
        for o in obs:
            sel = o['M'] & (o['G'] == 'golv')
            if sel.sum() > max(40, 0.005 * o['M'].sum()):  # relativ golvandel: enstaka felmärkta pixlar ger ingen höjd
                golv_h0.append(-float(np.median(o['P'][sel] @ u_cv)))
        fot0 = []
        for p, (fr, J) in Jcv.items():
            if A['personer'][p]['pose'] == 'staende' and p not in utan_stod:
                fot0 += list(-(np.minimum(J[:, ix['l_foot']] @ u_cv, J[:, ix['r_foot']] @ u_cv)) + 0.08)
        if golv_h0 and fot0 and np.median(golv_h0) > 0.2:
            yt = info['skala'].get('varde')
            skala = float(np.median(fot0) / np.median(golv_h0))
            info['skala'] = {'varde': round(skala, 3), 'kalla': 'fotkontakt (fötter på MoGe-golv)', 'personyta_skulle_ge': yt}
        # L4 kamerahöjd
        hojder = []
        for o in obs:
            sel = o['M'] & (o['G'] == 'golv')
            if sel.sum() > max(40, 0.005 * o['M'].sum()):  # relativ golvandel: enstaka felmärkta pixlar ger ingen höjd
                hojder.append(-float(np.median(o['P'][sel] @ u_cv)) * skala)
        fot = []
        for p, (fr, J) in Jcv.items():
            if p in utan_stod:
                continue
            fot += list(-(np.minimum(J[:, ix['l_foot']] @ u_cv, J[:, ix['r_foot']] @ u_cv)) + 0.08)
        if hojder:
            h = float(np.median(hojder)); info['kamerahojd'] = {'m': round(h, 3), 'kalla': 'golv (MoGe)'}
        elif fot:
            h = float(np.median(fot)); info['kamerahojd'] = {'m': round(h, 3), 'kalla': 'fötter (kropp)'}
        else:
            stod = []
            for o in obs:
                d = o['N'] @ u_cv; sel = o['M'] & np.isin(o['G'], ['bank', 'bord', 'spis']) & (d > math.cos(math.radians(25)))
                if sel.sum() > 20:
                    stod.append(-float(np.median(o['P'][sel] @ u_cv)) * skala + 0.9)
            if stod:
                h = float(np.median(stod)); info['kamerahojd'] = {'m': round(h, 3), 'kalla': 'bänkskiva + antagen bänkhöjd 0,90 m'}
            else:
                h = 1.4; info['kamerahojd'] = {'m': 1.4, 'kalla': 'antagen 1,40 m'}
        if fot and hojder:
            info['kamerahojd']['fotter_m'] = round(float(np.median(fot)), 3)
        C = np.array([0.0, 0.0, h])
        # världspunkter
        up_w = np.array([0, 0, 1.0]); rets = []
        for o in obs:
            Pc = o['P'] * skala
            o['Nw'] = (R @ B_from_cv(o['N']).reshape(-1, 3).T).T.reshape(o['N'].shape)
            Xw = C + (R @ B_from_cv(Pc).reshape(-1, 3).T).T.reshape(Pc.shape)
            o['Xw'] = Xw; o['Zc'] = Pc[..., 2]
            obj, ret = lyft_objekt(o, Xw, up_w, sid, a0, b0, frames[o['u']], H0, W0, len(rets))
            for o_ in obj:
                o_['_ruta'] = len(rets)
            objekt += obj; rets.append((o['u'], ret))
        # Texturerade instanser ur mittrutan; hål bakom personer fylls ur övriga rutor
        om = obs[len(obs) // 2]
        res_nat = bygg_nat(om, om['Xw'], om['Zc'], namn, gk, andra=[(o2, o2['Xw'], o2['Zc']) for o2 in obs if o2 is not om],
                           kamera=(C, R, fxA, fyA))
        if res_nat:
            bitar, blob = res_nat; (out / 'nat').mkdir(exist_ok=True)
            tmp = out / 'nat' / f'{sid}.tmp'; tmp.write_bytes(blob); tmp.replace(out / 'nat' / f'{sid}.bin')
            nat_manifest[sid] = {'fil': f'{sid}.bin', 'ruta': om['u'], 'bitar': bitar}
        if 'I' in om:
            pers_g = np.vectorize(lambda i_: gk.get(om['segs'].get(int(i_), -1), '') == 'person')(om['I'])
        else:
            pers_g = om['G'] == 'person'
        tdata.append({'sid': sid, 'u': om['u'], 'Xw': om['Xw'], 'M': om['M'], 'pers': pers_g})
        # Statiska delar tas ur mittrutan (kameran är statisk per tagning)
        mitt = s['nyckelrutor'][len(s['nyckelrutor']) // 2]
        mi = len(s['nyckelrutor']) // 2
        objekt = [o_ for o_ in objekt if o_.get('_ruta', mi) == mi or o_.get('rum') != sid]
        # kroppar in i L-världen
        Tw = lambda Jc: C + (R @ B_from_cv(Jc).T).T
        for p, (fr, J) in Jcv.items():
            rows = [[int(u)] + [int(round(v * 1000)) for v in Tw(Ju).reshape(-1)] for u, Ju in zip(fr, J)]
            spar = {'tagning': sid, 'ut': [a0, b0], 'rutor': rows}
            if p in utan_stod:
                spar['tilltro'] = {'overkropp': 'skymd_antagen', 'underkropp': 'skymd_antagen'}
            nya_rorelse[p].append(spar)
            fz = np.minimum(Tw(J[:, ix['l_foot']])[:, 2], Tw(J[:, ix['r_foot']])[:, 2])
            info.setdefault('fot_over_golv_m', {})[p] = round(float(np.median(fz)), 3)
        # L6 maträtter
        nr = 0
        for u, ret in rets:
            for r_ in ret:
                hand = None
                for p, (fr, J) in Jcv.items():
                    if u in list(fr):
                        Ju = Tw(J[list(fr).index(u)])
                        dmin = min(np.linalg.norm(Ju[ix['l_hand_mitt']] - r_['centrum']), np.linalg.norm(Ju[ix['r_hand_mitt']] - r_['centrum'])) - r_['diameter'] / 2
                        if dmin < 0.15:
                            hand = (p, r_['centrum'] - (Ju[ix['l_hand_mitt']] + Ju[ix['r_hand_mitt']]) / 2)
                base = {'bas': 'mat', 'typ': r_['typ'], 'mat_stil': 'skal' if r_['typ'] == 'mat_skal' else 'tallrik', 'farg': r_['farg'], 'farg_palett': r_['palett'],
                        'rot': euler_from_R(R_from_normal(r_['normal'])), 'matt': [round(r_['diameter'], 3)] * 2 + [0.07 if r_['typ'] != 'mat_skal' else 0.10],
                        'tilltro': 'skattad_ur_bild', 'rum': sid}
                if hand and u == mitt:
                    p, off = hand; fr, J = Jcv[p]
                    for uu, Jc in zip(fr, J):
                        Ju = Tw(Jc); c = (Ju[ix['l_hand_mitt']] + Ju[ix['r_hand_mitt']]) / 2 + off
                        objekt.append(base | {'id': f'mat_{sid}_{nr}_{uu}', 'pos': c.round(3).tolist(), 'synlig_ut': [[int(uu), int(uu) + 1]],
                                              'kalla': f'MoGe-yta {r_["punkter"]} punkter, diameter {r_["diameter"]:.2f} m; följer händerna'})
                    nr += 1
                elif u == mitt:
                    objekt.append(base | {'id': f'mat_{sid}_{nr}', 'pos': r_['centrum'].round(3).tolist(), 'synlig_ut': [[a0, b0]],
                                          'kalla': f'MoGe-yta {r_["punkter"]} punkter, diameter {r_["diameter"]:.2f} m'})
                    nr += 1
        info['matratter'] = nr
        if any(o_['bas'] == 'golv' and o_['rum'] == sid for o_ in objekt):
            info['ytor_over_golv_m'] = {o_['id']: round(o_['matt'][2], 2) for o_ in objekt if o_['rum'] == sid and o_['bas'] in ('bank', 'bord', 'spis') and not any('topp skymd' in x for x in o_.get('antaganden', []))}
        nya_tagningar.append({'id': sid, 'ut': [a0, b0], 'personer': [{'id': p, 'ankare': None} for p in Jcv], 'klass': tA['klass'] if tA else 'okand',
                              'kamera': {'typ': 'statisk', 'statisk': True, 'nycklar': [[a0, *C.round(4).tolist(), *R2q(R), round(lens, 2)]],
                                         'kalla_L': f"lodlinje {kalla}; höjd {info['kamerahojd']['kalla']}; position {'2D-registrerad kropp' if Jcv else 'origo'}"}})
        rapport['tagningar'][sid] = info
    # L7: rum över tagningar
    T7, rap7 = rum_over_tagningar(tdata, frames, W0, H0)
    rapport['rum_over_tagningar'] = rap7
    rum_id = {sid: f'rum{gi + 1}' for gi, grp in enumerate(rap7['grupper']) for sid in grp}
    for t in nya_tagningar:
        sid = t['id']; t['rum'] = rum_id.get(sid, f'egen_{sid}'); rapport['tagningar'][sid]['rum'] = t['rum']
        if sid not in T7:
            continue
        Rz, tv = T7[sid]; k = t['kamera']['nycklar'][0]
        C = Rz @ np.array(k[1:4]) + tv; Rc = Rz @ q2R(k[4:8])
        t['kamera']['nycklar'][0] = [k[0], *[round(float(v), 4) for v in C], *R2q(Rc), k[8]]
        for pid, tracks in nya_rorelse.items():
            for tr in tracks:
                if tr['tagning'] == sid:
                    for row in tr['rutor']:
                        J = np.array(row[1:], float).reshape(-1, 3) / 1000.0
                        row[1:] = [int(round(v * 1000)) for v in (J @ Rz.T + tv).reshape(-1)]
        for o in objekt:
            if o.get('rum') == sid:
                o['pos'] = [round(float(v), 3) for v in (Rz @ np.array(o['pos'], float) + tv)]
                o['rot'] = [o['rot'][0], o['rot'][1], round(float(o['rot'][2] + math.atan2(Rz[1, 0], Rz[0, 0])), 4)]
        if sid in nat_manifest:
            M4 = np.eye(4); M4[:3, :3] = Rz; M4[:3, 3] = tv
            nat_manifest[sid]['transform'] = M4.round(5).tolist()
    for sid in nat_manifest:
        nat_manifest[sid]['rum'] = rum_id.get(sid, f'egen_{sid}')
    keep = []
    for o in objekt:
        o.pop('_ruta', None); o['tagning'] = o.get('rum'); o['rum'] = rum_id.get(o.get('rum'), o.get('rum')); keep.append(o)
    L['objekt'] = keep; L['tagningar'] = nya_tagningar
    if A:
        L['rorelse'] = {p: v for p, v in nya_rorelse.items() if v}
    rapport['objekt'] = {'antal': len(keep), 'per_typ': {t: sum(1 for o in keep if o['typ'] == t) for t in sorted({o['typ'] for o in keep})}}
    rapport['sek'] = round(time.perf_counter() - t0, 2)
    rapport['observationer'] = {'kalla': kalla, 'obsv': meta.get('obsv', 'obs/2 (CPU, ViT-S, SegFormer-B2)')}
    (out / f'paket_L{suffix}.json').write_text(json.dumps(L, ensure_ascii=False, default=_np), encoding='utf-8')
    rapport['L_paket_sha256'] = sha(out / f'paket_L{suffix}.json')
    if nat_manifest and suffix == '':
        man = {'schema': 'lokalitet-nat/1', 'textur': 'originalets pixlar (projektiv; video levande eller nyckelruta fryst)',
               'koordinater': 'samma världsram som paket_L.json', 'tagningar': nat_manifest}
        tmp = out / 'nat.json.tmp'; tmp.write_text(json.dumps(man, ensure_ascii=False, default=_np), encoding='utf-8'); tmp.replace(out / 'nat.json')
        rapport['nat'] = {sid: {'bitar': len(v['bitar']), 'trianglar': sum(b_['ni'] for b_ in v['bitar']) // 3} for sid, v in nat_manifest.items()}
    (out / f'lokalitet{suffix}.json').write_text(json.dumps(rapport, ensure_ascii=False, indent=1, default=_np), encoding='utf-8')
    for sid, i in rapport['tagningar'].items():
        print(sid, i.get('lutning_grader'), '(A', i.get('A_lutning_grader'), ')', i['lodlinje']['kalla'], '| höjd', i['kamerahojd'], '| skala', i['skala']['varde'], i['skala']['kalla'][:12],
              '| 2D', i.get('registrering_2d_px'), '| fot', i.get('fot_over_golv_m'), '| rätter', i['matratter'])
    print(rapport['objekt'], rapport['sek'], 's')


if __name__ == '__main__':
    main()
