"""HISTORISK KOPIA (före GOLV2): läser rå cam_t med golvstegets skala. Pipelinen använder ingest/plats.py."""
"""plats.py: lägger ett klipps tagningar i EN plats (en värld i meter, tyngdkraftsriktad) och skriver platsbeskrivningen.

    scen/.venv/Scripts/python.exe scen/3d/ingest/plats.py <ingestmapp> [--ut <utmapp>] [--scen3d <fil>] [--hand <fil>] [--video <klipp.mp4>]

<ingestmapp> är antingen en ensam ingest-mapp (har meta.json: ett klipp, en tagning) eller en mapp med tagningsmappar S1, S2, ...
Läser bara det som tidigare steg redan skrivit (varld.npz, sekvens_*.npz, rum.json, masker.npy, rum/depth/*.npz, tagningsvideor).
Kör inga steg om, inga nätanrop, ingen GPU. Utdata (standard <ingestmapp>/plats/, för en ensam mapp krävs --ut):

    plats.json       platsen: golv, sammanslagna objekt, ankare, tagningarnas transform in i platsen med kvalitet, bindningar
    plats_matt.json  mätloggen: siffrorna bakom varje beslut (personer, objekt, bildmatchning, scengrammatik)
    plats.md         kort sammanfattning

Vad som är mätt och vad som är antaget, i den ordning det används:
  1. Bildmatchning (SIFT + RANSAC mot 3D från MoGe-djup, personerna maskade) lägger tagningar som står på samma ställe i samma
     ram. Det är den enda rent bildbaserade kopplingen mellan tagningar; den accepteras bara över tydliga tröskelvärden (se TROSKEL).
  2. Personer som landmärken: en person som sitter stilla har ett bäcken på golvet och en torsoriktning, båda mätta i tagningen.
     Samma roll i flera tagningar hamnar på samma ankare (stol_<roll>).
  3. Scengrammatik (ANTAGEN, märks så): två huvudroller i dialog vänder sig mot varandra längs en axel, och kameran i en
     motbild står ungefär vid motpartens huvud. Avståndet mellan stolarna kommer från kamerornas uppmätta avstånd till personerna.
  4. Det som varken mätningen eller grammatiken når (en roll som bara syns i en tagning, utan koppling) får ett ställe med
     handgjord eller godtycklig blickriktning och märks antagen med skäl.
Skala är 1,0 överallt (antagen; kropparnas storlek är jämn mellan tagningar, se plats_matt.json). Golvet är z = 0 i platsen när
flera tagningar läggs ihop. I en ensam tagning (identitetsfallet) är platsen tagningens egen Blender-värld, oförändrad.
"""
import argparse
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIT))   # även med python -I vid determinismkontrollen
F = np.diag([1., -1., -1.])          # OpenCV-kamerarum = F @ MHR-modellrum (som mhr_rig.py och kompilera.py)
VERSION = 'plats/1'
TROSKEL = dict(min_inliers=150, max_sampson_px=1.0, min_andel_3d=0.7, max_rotationsskillnad_grader=2.0, max_median_3d_m=0.15)
STOL_MAX_BACKENHOJD_M = 0.82      # över detta räknas en person som stående (mitt mellan klustren 0,77 och 0,87 m i notan; antagen gräns)
STILLA_MAX_SPRIDNING_M = 0.25     # en person som rör sig mer än så bär inget ankare
SAMMANSLAGNING = dict(max_avstand_m=0.5, max_toppskillnad_m=0.25, min_stodpunkter=1000, bord_hojd_m=(0.55, 1.10), stol_max_bredd_m=0.8, stol_min_matt_m=0.25)


# ------------------------------------------------------------------ små hjälpare
def ladda(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def skriv(p, data):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def gravitation(upp):
    """Samma funktion som kompilera.gravitation: roterar världen så att upp blir +Z."""
    u = np.asarray(upp) / np.linalg.norm(upp); z = np.array([0., 0., 1.]); c = float(u @ z)
    if c < -1 + 1e-10: return np.diag([1., -1., -1.])
    x, y, z = np.cross(u, z); vx = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.], [s, c, 0.], [0., 0., 1.]])


def matris(yaw, t):
    m = np.eye(4); m[:3, :3] = rz(yaw); m[:3, 3] = t
    return m


def vinkel_diff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


def cirkular_medel(v, vikt=None, period=2 * math.pi):
    v = np.asarray(v, float) * (2 * math.pi / period); w = np.ones(len(v)) if vikt is None else np.asarray(vikt, float)
    return math.atan2((w * np.sin(v)).sum(), (w * np.cos(v)).sum()) * period / (2 * math.pi)


def avrunda(x, n=4):
    if isinstance(x, (float, np.floating)): return round(float(x), n)
    if isinstance(x, dict): return {k: avrunda(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [avrunda(v, n) for v in x]
    if isinstance(x, np.ndarray): return avrunda(x.tolist(), n)
    if isinstance(x, (np.integer,)): return int(x)
    return x


# ------------------------------------------------------------------ tagningar och personer
def hitta_tagningar(mapp):
    mapp = Path(mapp)
    if (mapp / 'meta.json').exists(): return [(mapp.name, mapp)], True
    ds = [p for p in mapp.iterdir() if p.is_dir() and (p / 'meta.json').exists() and p.name[:1] == 'S' and p.name[1:].isdigit()]
    if not ds: raise SystemExit('Hittade varken meta.json eller tagningsmappar S1, S2, ... i ' + str(mapp))
    return [(p.name, p) for p in sorted(ds, key=lambda p: int(p.name[1:]))], False


def ladda_tagning(tid, d):
    """Allt platssteget behöver ur en tagnings befintliga utdata."""
    V = dict(np.load(d / 'varld.npz')); G = gravitation(V['upp'])
    rum = ladda(d / 'rum.json') if (d / 'rum.json').exists() else None
    meta = ladda(d / 'meta.json'); lednamn = ladda(HIT / 'mhr_ledernamn.json'); ix = {n: i for i, n in enumerate(lednamn)}
    statisk = bool(np.allclose(V['kam_C'], V['kam_C'][0], rtol=0, atol=1e-8))
    golv = None
    if rum: golv = dict(hojd_m=float(rum['floor']['height']), kalla=rum['floor']['source'], verifierad=bool(rum['floor'].get('verified')),
                        uppmatt_ur_fotter=rum['floor']['source'] == 'synliga fötter')
    personer = {}
    for p in sorted(d.glob('sekvens_*.npz')):
        pid = p.stem[8:]; S = np.load(p); inom = np.flatnonzero(S['inom'])
        if not len(inom): continue

        def led(f, n): return G @ (V['kam_C'][f] + V['kam_R'][f] @ (F @ (S['pose'][f, ix[n], :3] / 100) + S['cam_t'][f]))
        bak = np.array([led(f, 'root') for f in inom]); huvud = np.array([led(f, 'c_head') for f in inom])
        kam = np.array([G @ V['kam_C'][f] for f in inom])
        sh = np.array([led(f, 'l_uparm') - led(f, 'r_uparm') for f in inom]); sh[:, 2] = 0
        fram = np.cross(sh, [0., 0., 1.]); fram /= np.linalg.norm(fram, axis=1, keepdims=True)
        az = np.arctan2(fram[:, 1], fram[:, 0]); az_m = cirkular_medel(az)
        mot_kam = -(huvud - kam)[:, :2]; mot_kam = np.arctan2(mot_kam[:, 1], mot_kam[:, 0])
        fot = (np.array([led(f, 'l_foot') for f in inom]) + np.array([led(f, 'r_foot') for f in inom])) / 2
        personer[pid] = dict(rutor=len(inom), backen=np.median(bak, 0), huvud=np.median(huvud, 0), kam=np.median(kam, 0),
                             spridning_m=float(np.linalg.norm(bak[:, :2].std(0))), framat_rad=az_m,
                             framat_mot_kamera_grader=float(np.degrees(cirkular_medel(az - mot_kam))),
                             huvudavstand_m=float(np.median(np.hypot(*(huvud - kam)[:, :2].T))),
                             kroppsskala=float(np.median(S['pose'][inom, :, 7])), ben_synliga=int(S['ben_synliga'].sum()),
                             fot_z=float(np.median(fot[:, 2])),
                             knoglangder_cm={n: float(np.median(np.linalg.norm(S['pose'][inom, ix[a], :3] - S['pose'][inom, ix[b], :3], axis=1)))
                                             for n, (a, b) in dict(lar=('l_upleg', 'l_lowleg'), underben=('l_lowleg', 'l_foot'), overarm=('l_uparm', 'l_lowarm'),
                                                                   underarm=('l_lowarm', 'l_wrist'), axelbredd=('l_uparm', 'r_uparm'), hals_huvud=('c_spine3', 'c_head')).items()},
                             fokal_px=float(S['fokal']))
        S.close()
    fram_cam = G @ np.array([0., 0., 1.]) if statisk else None
    return dict(id=tid, mapp=d, meta=meta, V=V, G=G, rum=rum, golv=golv, personer=personer, statisk=statisk, N=meta['N'],
                kamera_blick_rad=float(math.atan2(fram_cam[1], fram_cam[0])) if statisk else None,
                kamera_lutning_grader=float(np.degrees(np.arcsin(-fram_cam[2]))) if statisk else None)


def roller(tagningar, scen3d):
    """Roll per (tagning, ingest-id): samma regel som kalla_flera.py (flest rutor i bild får den första rollen)."""
    uppg = {}
    if scen3d and Path(scen3d).exists():
        s3 = ladda(scen3d); uppg = {s['id']: [a['id'] for a in s['actors']] for s in s3['shots']}
    res = {}
    for t in tagningar:
        ids = sorted(t['personer'], key=lambda p: (-t['personer'][p]['rutor'], p)); akt = uppg.get(t['id'], [])
        # Hela ingest-listan (även personer utan sekvens i bild) ger samma rangordning som kalla_flera.
        alla = sorted(p.stem[8:] for p in t['mapp'].glob('sekvens_*.npz'))
        antal = {}
        for pid in alla:
            S = np.load(t['mapp'] / f'sekvens_{pid}.npz'); antal[pid] = int(S['inom'].sum()); S.close()
        rang = sorted(alla, key=lambda p: (-antal[p], p)); tilld = dict(zip(rang, akt))
        for pid in alla: res[(t['id'], pid)] = tilld.get(pid) or f'okand_{t["id"].lower()}_{pid}'
    return res


# ------------------------------------------------------------------ bildmatchning
def bildruta(t, args, N0):
    """En ruta ur tagningens video: den ruta med MoGe-djup som ligger närmast mitten."""
    import cv2
    djup = sorted(int(p.stem) for p in (t['mapp'] / 'rum/depth').glob('*.npz'))
    if not djup: return None
    mitt = t['N'] // 2; f = min(djup, key=lambda x: abs(x - mitt))
    kandidater = [(t['mapp'].parent / 'klipp' / f'{t["id"]}.mp4', 0)]
    if t['meta'].get('kallvideo'): kandidater.append((Path(t['meta']['kallvideo']), 0))
    if args.video: kandidater.append((Path(args.video), N0))
    for p, off in kandidater:
        if p.exists():
            cap = cv2.VideoCapture(str(p)); cap.set(1, f + off); ok, img = cap.read(); cap.release()
            if ok: return f, img, str(p)
    return None


def matcha_par(tagningar, args):
    """Parvis SIFT-matchning mellan alla tagningar, sedan rigid 3D-anpassning med MoGe-djup (metriskt).
    Returnerar (matt-lista, accepterade par med transform av tagning j in i tagning i, båda i tyngdkraftsriktade världen)."""
    import cv2
    cv2.setRNGSeed(0)
    sift = cv2.SIFT_create(nfeatures=5000); data = {}; start = 0
    for t in tagningar:
        r = bildruta(t, args, start); start += t['N']
        if r is None: continue
        f, img, kalla = r; g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); h, w = g.shape
        M = np.load(t['mapp'] / 'masker.npy'); mk = np.any(M, axis=0).astype(np.uint8) * 255
        mk = cv2.dilate(cv2.resize(mk, (w, h), interpolation=cv2.INTER_NEAREST), np.ones((15, 15), np.uint8))
        kp, de = sift.detectAndCompute(g, np.where(mk > 0, 0, 255).astype(np.uint8))
        d = np.load(t['mapp'] / f'rum/depth/{f:04d}.npz'); intr = d['intrinsics']; dh, dw = d['depth'].shape
        data[t['id']] = dict(kp=kp, de=de, f=f, kalla=kalla, depth=d['depth'], fx=float(intr[0, 0] * w), fy=float(intr[1, 1] * h), w=w, h=h, dw=dw, dh=dh)
    bf = cv2.BFMatcher(); matt = []; accept = {}

    def lyft(dd, pt):
        u = float(np.clip(pt[0] * dd['dw'] / dd['w'], 0, dd['dw'] - 1)); v = float(np.clip(pt[1] * dd['dh'] / dd['h'], 0, dd['dh'] - 1))
        z = dd['depth'][int(v), int(u)]
        return np.array([(pt[0] + .5 - dd['w'] / 2) / dd['fx'] * z, (pt[1] + .5 - dd['h'] / 2) / dd['fy'] * z, z])
    for a, b in itertools.combinations([t['id'] for t in tagningar if t['id'] in data], 2):
        da, db = data[a], data[b]; rad = dict(par=[a, b])
        if da['de'] is None or db['de'] is None or len(da['kp']) < 8 or len(db['kp']) < 8: rad.update(status='for_fa_punkter'); matt.append(rad); continue
        m = bf.knnMatch(da['de'], db['de'], k=2); bra = [x[0] for x in m if len(x) == 2 and x[0].distance < 0.8 * x[1].distance]
        rad['bra_matchningar'] = len(bra)
        if len(bra) < 12: rad.update(status='for_fa_matchningar'); matt.append(rad); continue
        p1 = np.float32([da['kp'][x.queryIdx].pt for x in bra]); p2 = np.float32([db['kp'][x.trainIdx].pt for x in bra])
        n1 = (p1 - [da['w'] / 2, da['h'] / 2]) / [da['fx'], da['fy']]; n2 = (p2 - [db['w'] / 2, db['h'] / 2]) / [db['fx'], db['fy']]
        E, mk = cv2.findEssentialMat(n1.reshape(-1, 1, 2), n2.reshape(-1, 1, 2), np.eye(3), cv2.USAC_MAGSAC, 0.999, 1.5 / da["fx"])
        if E is None or E.shape != (3, 3): rad.update(status='essentiell_matris_misslyckades'); matt.append(rad); continue
        mk = mk.ravel() > 0; ni = int(mk.sum()); rad['e_inliers'] = ni
        _, R_e, t_e, _ = cv2.recoverPose(E, n1[mk].reshape(-1, 1, 2), n2[mk].reshape(-1, 1, 2), np.eye(3))
        vinkel = lambda R: float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))
        Fm = np.linalg.inv(np.diag([db['fx'], db['fy'], 1])).T @ E @ np.linalg.inv(np.diag([da['fx'], da['fy'], 1]))
        x1 = np.c_[p1[mk] - [da['w'] / 2, da['h'] / 2], np.ones(ni)] * [1, 1, 1]; x2 = np.c_[p2[mk] - [db['w'] / 2, db['h'] / 2], np.ones(ni)]
        Fx1, Ftx2 = x1 @ Fm.T, x2 @ Fm
        sampson = np.abs((x2 * Fx1).sum(1)) / np.sqrt(Fx1[:, 0] ** 2 + Fx1[:, 1] ** 2 + Ftx2[:, 0] ** 2 + Ftx2[:, 1] ** 2)
        rad.update(e_rotation_grader=vinkel(R_e), sampson_median_px=float(np.median(sampson)),
                   andel_i_nedre_bilddelen=float((p1[mk][:, 1] > da['h'] * .62).mean()))
        if ni < 8: rad.update(status='for_fa_inliers'); matt.append(rad); continue
        P = np.array([lyft(da, q) for q in p1[mk]]); Q = np.array([lyft(db, q) for q in p2[mk]])
        rng = np.random.default_rng(0); basta = None
        for _ in range(600):
            idx = rng.choice(ni, 4, replace=False); R, tt = rigid(P[idx], Q[idx]); r = np.linalg.norm(P @ R.T + tt - Q, axis=1); c = int((r < 0.15).sum())
            if basta is None or c > basta[0]: basta = (c, R, tt)
        inl = np.linalg.norm(P @ basta[1].T + basta[2] - Q, axis=1) < 0.15
        if inl.sum() < 4: rad.update(status='for_fa_3d_inliers', inliers_3d=int(inl.sum())); matt.append(rad); continue
        R3, t3 = rigid(P[inl], Q[inl]); res = np.linalg.norm(P[inl] @ R3.T + t3 - Q[inl], axis=1)
        rad.update(inliers_3d=int(inl.sum()), rotation_3d_grader=vinkel(R3), translation_3d_m=float(np.linalg.norm(t3)), median_3d_rest_m=float(np.median(res)),
                   rotationsskillnad_e_mot_3d_grader=abs(vinkel(R3) - vinkel(R_e)))
        Tt = TROSKEL
        ok = (ni >= Tt['min_inliers'] and rad['sampson_median_px'] <= Tt['max_sampson_px'] and inl.sum() / ni >= Tt['min_andel_3d']
              and rad['rotationsskillnad_e_mot_3d_grader'] <= Tt['max_rotationsskillnad_grader'] and rad['median_3d_rest_m'] <= Tt['max_median_3d_m'])
        rad['status'] = 'accepterad' if ok else 'avvisad_under_troskel'
        matt.append(rad)
        if ok:
            ta, tb = next(t for t in tagningar if t['id'] == a), next(t for t in tagningar if t['id'] == b)
            # Korrespondenser i de tyngdkraftsriktade världarna: b -> a. Kamerorna är statiska, så världen = G @ kamerakoordinater.
            Xa = (ta['G'] @ P[inl].T).T; Xb = (tb['G'] @ Q[inl].T).T
            accept[(b, a)] = dict(Xfran=Xb, Xtill=Xa, matt=rad)
    return matt, accept


def rigid(P, Q):
    mp, mq = P.mean(0), Q.mean(0); U, S, Vt = np.linalg.svd((P - mp).T @ (Q - mq)); d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return R, mq - R @ mp


def rigid_yaw(X, Y):
    """Yaw + xy-translation som bäst lägger X på Y (z lämnas åt golven). Returnerar (yaw, t_xy)."""
    mx, my = X[:, :2].mean(0), Y[:, :2].mean(0); a, b = X[:, :2] - mx, Y[:, :2] - my
    yaw = math.atan2((a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]).sum(), (a * b).sum())
    R = rz(yaw)[:2, :2]
    return yaw, my - R @ mx


# ------------------------------------------------------------------ platsen
def objekt_i_platsen(t, M):
    """Rummets objekt och väggar i tagningens värld (som kompilera.rumobjekt) och i platsen via transformen M (4x4)."""
    ut = []
    if not t['rum']: return ut
    G = t['G']; Rm = M[:3, :3]; yaw = math.atan2(M[1, 0], M[0, 0])
    for o in t['rum']['objects']:
        c = M[:3, :3] @ (G @ np.array(o['centre'])) + M[:3, 3]
        ut.append(dict(tagning=t['id'], id=o['id'], etikett=o['label'], centrum=c, matt=list(o['size']), yaw=o['yaw'] + yaw, top_slope=o.get('top_slope', 0),
                       stod=int(o.get('support_points', 0)), tvaa=bool(o.get('antagen'))))
    return ut


def sla_ihop(obs, avvisade):
    S = SAMMANSLAGNING; rena = []
    for o in obs:
        topp = o['centrum'][2] + o['matt'][2] / 2; kant = o['etikett']
        if o['stod'] < S['min_stodpunkter']: avvisade.append(dict(tagning=o['tagning'], id=o['id'], etikett=kant, orsak=f'för få stödpunkter ({o["stod"]} < {S["min_stodpunkter"]})')); continue
        if kant == 'table' and not S['bord_hojd_m'][0] <= topp <= S['bord_hojd_m'][1]:
            avvisade.append(dict(tagning=o['tagning'], id=o['id'], etikett=kant, orsak=f'bordets ovansida {topp:.2f} m över golvet ligger utanför {S["bord_hojd_m"][0]}–{S["bord_hojd_m"][1]} m')); continue
        if kant == 'chair' and (max(o['matt'][:2]) > S['stol_max_bredd_m'] or min(o['matt'][:2]) < S['stol_min_matt_m']):
            avvisade.append(dict(tagning=o['tagning'], id=o['id'], etikett=kant, orsak=f'stolens mått {o["matt"][0]:.2f} × {o["matt"][1]:.2f} m är inte rimliga för en stol (0,25–0,8 m)')); continue
        rena.append(dict(o, topp=topp))
    grupper = []
    for o in sorted(rena, key=lambda o: (-o['stod'], o['tagning'], o['id'])):
        for g in grupper:
            c0 = g['obs'][0]
            if (g['etikett'] == o['etikett'] and np.linalg.norm(o['centrum'][:2] - c0['centrum'][:2]) < S['max_avstand_m']
                    and abs(o['topp'] - c0['topp']) < S['max_toppskillnad_m']):
                g['obs'].append(o); break
        else: grupper.append(dict(etikett=o['etikett'], obs=[o]))
    res = []
    for g in grupper:
        ob = g['obs']; w = np.array([o['stod'] for o in ob], float)
        c = (np.array([o['centrum'] for o in ob]) * w[:, None]).sum(0) / w.sum()
        res.append(dict(etikett=g['etikett'], centrum=c, yaw=cirkular_medel([o['yaw'] for o in ob], w, period=math.pi),
                        matt=[max(o['matt'][0] for o in ob), max(o['matt'][1] for o in ob), float((np.array([o['matt'][2] for o in ob]) * w).sum() / w.sum())],
                        top_slope=0, obs=ob, spridning_m=float(max(np.linalg.norm(o['centrum'][:2] - c[:2]) for o in ob))))
    return res


def kant_narmast(o, p):
    """Punkten på objektets fotavtryck (rektangel med yaw) som ligger närmast p (xy), och avståndet."""
    c, y = o['centrum'][:2], o['yaw']; R = rz(y)[:2, :2]; lok = R.T @ (np.asarray(p[:2]) - c)
    h = np.array([o['matt'][0], o['matt'][1]]) / 2; kl = np.clip(lok, -h, h)
    if np.all(np.abs(lok) <= h):   # innanför: närmaste kant
        d = h - np.abs(lok); i = int(np.argmin(d)); kl = lok.copy(); kl[i] = np.sign(lok[i] if lok[i] else 1) * h[i]
    q = c + R @ kl
    return q, float(np.linalg.norm(q - np.asarray(p[:2])))


def bygg_plats(args):
    mapp = Path(args.ingest).resolve(); tl, ensam = hitta_tagningar(mapp)
    ut = Path(args.ut).resolve() if args.ut else mapp / 'plats'
    if ensam and not args.ut: raise SystemExit('En ensam ingest-mapp får inte skrivas till: ange --ut.')
    tagningar = [ladda_tagning(i, d) for i, d in tl]
    rollmap = roller(tagningar, args.scen3d) if not ensam else {(t['id'], p): p for t in tagningar for p in t['personer']}
    hand = ladda(args.hand) if args.hand else (ladda(ut / 'hand.json') if (ut / 'hand.json').exists() else {})
    matt = dict(version=VERSION, troskel=TROSKEL, sammanslagning=SAMMANSLAGNING)
    for t in tagningar:
        if not t['golv']: raise SystemExit(f'{t["id"]}: rum.json saknas; kör rumsteget först.')

    # ---------- (a) personer och (b) objekt per tagning, i tagningens egen värld
    matt['a_personer'] = [dict(tagning=t['id'], ingest_id=p, roll=rollmap[(t['id'], p)], **avrunda({k: v for k, v in pp.items() if k not in ('kam',)}, 4))
                          for t in tagningar for p, pp in t['personer'].items()]
    matt['b_objekt_per_tagning'] = [dict(tagning=t['id'], golv=t['golv'], objekt=[dict(id=o['id'], etikett=o['label'], centrum_g=avrunda(t['G'] @ np.array(o['centre']), 3),
                                    matt=avrunda(o['size'], 3), yaw=round(o['yaw'], 3), stod=o.get('support_points')) for o in t['rum']['objects']],
                                    vaggar=len(t['rum']['walls'])) for t in tagningar]

    ident = len(tagningar) == 1
    reg = {}; par = []   # PATCH flera/: par definierad även utan dialogpar
    stationer = []
    if ident or not all(t['statisk'] for t in tagningar):
        # Identitet: platsen är tagningens egen värld. Ett klipp med rörlig kamera får aldrig flyttas av platssteget.
        for t in tagningar:
            reg[t['id']] = dict(M=np.eye(4), metod='identitet', status='uppmatt', residual_m=None, skala=1.0,
                                kommentar='Platsen är tagningens egen tyngdkraftsriktade Blender-värld; ingen flytt.' + ('' if ident else ' Rörlig kamera i minst en tagning: ingen registrering försökt.'))
        matt['c_bildmatchning'] = []
        matt['d_grammatik'] = dict(anvand=False, orsak='en tagning' if ident else 'rörlig kamera')
    else:
        mt, accept = matcha_par(tagningar, args); matt['c_bildmatchning'] = avrunda(mt, 3)
        # stationer = sammanhängande grupper av accepterade par (union-find); referens = tagningen med flest personrutor
        foralder = {t['id']: t['id'] for t in tagningar}

        def rot(x):
            while foralder[x] != x: x = foralder[x]
            return x
        for (j, i) in accept: foralder[rot(j)] = rot(i)
        grupper = {}
        for t in tagningar: grupper.setdefault(rot(t['id']), []).append(t['id'])
        tid = {t['id']: t for t in tagningar}
        for ids in grupper.values():
            ids = sorted(ids, key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
            refs = max(ids, key=lambda x: (sum(p['rutor'] for p in tid[x]['personer'].values()), -ids.index(x)))
            stationer.append(dict(ids=ids, ref=refs))
        stationer.sort(key=lambda s: int(s['ref'][1:]))
        # ---- roller, dialogpar
        roll_rutor = {}
        for t in tagningar:
            for p, pp in t['personer'].items(): roll_rutor[rollmap[(t['id'], p)]] = roll_rutor.get(rollmap[(t['id'], p)], 0) + pp['rutor']
        kand = {r: n for r, n in roll_rutor.items() if not r.startswith('okand_')}
        par = sorted(kand, key=lambda r: (-kand[r], r))[:2]
        huvudroll = {}   # tagning -> (ingest-id, roll) för personen med flest rutor som har en känd roll
        for t in tagningar:
            c = [(pp['rutor'], p) for p, pp in t['personer'].items() if not rollmap[(t['id'], p)].startswith('okand_')]
            if c: p = max(c)[1]; huvudroll[t['id']] = (p, rollmap[(t['id'], p)])
        # Station per roll: stationens referens ska bära stationens huvudroll.
        info = dict(roll_rutor=roll_rutor, dialogpar=par, huvudroll=huvudroll, stationer=stationer)
        if len(par) < 2:
            for t in tagningar: reg[t['id']] = dict(M=np.eye(4), metod='identitet', status='antagen', residual_m=None, skala=1.0,
                                                    kommentar='Färre än två kända roller: ingen scengrammatik tillämpbar; tagningarna ligger över varandra som före platssteget.')
            matt['d_grammatik'] = dict(anvand=False, orsak='färre än två roller', **info)
        else:
            r1, r2 = par

            def seat_data(roll, tagn):
                p, rr = huvudroll[tagn]; return tid[tagn]['personer'][p]
            # Stationen med flest rutor för roll 1 definierar ramen: roll 1 på (0,0), vänd mot +Y.
            def station_av(roll):
                c = [s for s in stationer if huvudroll.get(s['ref'], (None, None))[1] == roll]
                return max(c, key=lambda s: roll_rutor_stat(s, roll)) if c else None

            def roll_rutor_stat(s, roll): return sum(tid[x]['personer'][huvudroll[x][0]]['rutor'] for x in s['ids'] if x in huvudroll and huvudroll[x][1] == roll)
            s1 = station_av(r1)
            if s1 is None: raise SystemExit(f'Ingen station har {r1} som huvudroll i sin referenstagning.')
            # Avstånd kamera -> huvud per tagning (horisontellt) för de två rollerna
            def avst(roll): return [(x, tid[x]['personer'][huvudroll[x][0]]['huvudavstand_m'], tid[x]['personer'][huvudroll[x][0]]['framat_mot_kamera_grader'])
                                    for x in tid if x in huvudroll and huvudroll[x][1] == roll]
            a1, a2 = avst(r1), avst(r2)
            nara = lambda lst: [e for e in lst if e[1] <= 1.5 * min(x[1] for x in lst)]
            d1 = float(np.median([e[1] for e in nara(a1)])); d2 = float(np.median([e[1] for e in nara(a2)]))
            est = {'stationer_ihop': dict(varde_m=d1 + d2, forklaring=f'kamerans avstånd till {r1} ({d1:.2f} m, {len(nara(a1))} tagningar) + till {r2} ({d2:.2f} m, {len(nara(a2))} tagningar): motbilderna antas stå på samma ställe, vända åt var sitt håll')}
            bredd = [e for e in a2 if e[1] > 1.5 * min(x[1] for x in a2) and abs(e[2]) <= 15]
            if bredd:
                e = max(bredd, key=lambda e: e[1]); est['vidvinkel'] = dict(varde_m=e[1], tagning=e[0], forklaring=f'{e[0]} visar {r2} på {e[1]:.2f} m med torsot vänd mot kameran ({e[2]:.1f} grader); kameran antas stå vid {r1}:s huvud (utsikt från {r1}:s plats)')
            D = float(np.mean([v['varde_m'] for v in est.values()])); osak = float((max(v['varde_m'] for v in est.values()) - min(v['varde_m'] for v in est.values())) / 2)
            if 'stolsavstand_m' in hand.get('layout', {}):
                D = float(hand['layout']['stolsavstand_m'])
                est['hand'] = dict(varde_m=D, status='antagen', forklaring=hand['layout']['orsak'])
            matt['d_grammatik'] = dict(anvand=True, dialogpar=par, stolsavstand_m=D, stolsavstand_osakerhet_m=osak, skattningar=avrunda(est, 3), kamera_avstand=avrunda(dict(roll1=a1, roll2=a2), 3),
                                       regler=['De två rollerna med flest rutor är i dialog och sitter vända mot varandra längs en axel (+Y från roll 1 till roll 2).',
                                               'Torsots uppmätta riktning används: roll 1 vänder sig mot +Y, roll 2 mot −Y; kamerorna får den förskjutning/vridning de mätta tagningarna ger.',
                                               'Stolsavstånd = medel av de skattningar som finns; osäkerheten är halva spannet.'], **{k: avrunda(v, 3) for k, v in info.items() if k not in ('stationer', 'dialogpar')}, stationer=stationer)
            mal = {r1: dict(pos=np.array([0., 0.]), yaw=math.pi / 2), r2: dict(pos=np.array([0., D]), yaw=-math.pi / 2)}

            def landmark(tagn, roll):
                t = tid[tagn]; pp = t['personer'][huvudroll[tagn][0]]
                yaw = mal[roll]['yaw'] - pp['framat_rad']; M = matris(yaw, [0, 0, -t['golv']['hojd_m']])
                M[:3, 3] = [*(mal[roll]['pos'] - rz(yaw)[:2, :2] @ pp['backen'][:2]), -t['golv']['hojd_m']]
                return M
            # Referenser först
            for s in stationer:
                ref = s['ref']
                if ref in huvudroll and huvudroll[ref][1] in mal:
                    roll = huvudroll[ref][1]; tg = tid[ref]; pp = tg['personer'][huvudroll[ref][0]]
                    reg[ref] = dict(M=landmark(ref, roll), metod='landmark', status='antagen', residual_m=None, skala=1.0, station=s['ids'],
                                    kommentar=f'{roll}:s uppmätta bäcken på golvet = stol_{roll}; torsot vänd {"mot" if roll == r1 else "mot"} motparten (antagen dialogaxel). ' +
                                              ('Definierar platsens ram.' if roll == r1 and s is s1 else 'Läget längs axeln följer stolsavståndet (antaget).'))
            # Gruppmedlemmar via matchning
            for s in stationer:
                ref = s['ref']
                if ref not in reg: continue
                for j in s['ids']:
                    if j == ref: continue
                    ak = accept.get((j, ref))
                    if ak is None:
                        for (a, b), v in accept.items():   # kedja via en tredje tagning
                            if a == j and b in reg and b in s['ids']: ak = dict(v, kedja=b); break
                    if ak is None: continue
                    mot = ak.get('kedja', ref); yaw, txy = rigid_yaw(ak['Xfran'], ak['Xtill'])
                    N = matris(yaw, [*txy, tid[mot]['golv']['hojd_m'] - tid[j]['golv']['hojd_m']])
                    Mj = reg[mot]['M'] @ N
                    rest = np.linalg.norm((ak['Xfran'] @ N[:3, :3].T + N[:3, 3]) - ak['Xtill'], axis=1)
                    d_ = (ak['Xfran'] @ N[:3, :3].T + N[:3, 3]) - ak['Xtill']
                    xy_rest = float(np.median(np.linalg.norm(d_[:, :2], axis=1))); z_av = float(np.median(d_[:, 2]))
                    fullrest = float(np.median(np.linalg.norm(ak['Xfran'] @ rigid(ak['Xfran'], ak['Xtill'])[0].T + rigid(ak['Xfran'], ak['Xtill'])[1] - ak['Xtill'], axis=1)))
                    # kontroll: samma persons bäcken i tagning j via matchad transform mot referensens uppmätta
                    kontroll = None
                    if j in huvudroll and ref in huvudroll and huvudroll[j][1] == huvudroll[ref][1]:
                        pj = tid[j]['personer'][huvudroll[j][0]]['backen']; pr = tid[ref]['personer'][huvudroll[ref][0]]['backen']
                        kontroll = float(np.linalg.norm((N[:3, :3] @ pj + N[:3, 3])[:2] - pr[:2]))
                    tilt = float(np.degrees(np.arccos(np.clip(np.trace(rigid(ak['Xfran'], ak['Xtill'])[0] @ rz(yaw).T) / 2 - .5, -1, 1))))
                    reg[j] = dict(M=Mj, metod='matchning', status='uppmatt', residual_m=float(np.median(rest)), skala=1.0, station=s['ids'], mot=mot,
                                  inliers=ak['matt']['inliers_3d'], rotation_grader=ak['matt']['rotation_3d_grader'], translation_m=ak['matt']['translation_3d_m'],
                                  lutning_kvar_grader=tilt, personbacken_avvikelse_m=kontroll, rest_xy_m=xy_rest, hojdskillnad_mot_golvantagandet_m=z_av, rest_fri_rigid_m=fullrest,
                                  kommentar=f'Bildmatchning mot {mot}: {ak["matt"]["e_inliers"]} inliers, Sampson-median {ak["matt"]["sampson_median_px"]:.2f} px, 3D-rest {np.median(rest)*100:.1f} cm (varav höjdskillnad {z_av*100:+.0f} cm mellan matchningen och golvantagandet; fri rigid anpassning ger {fullrest*100:.1f} cm); yaw och xy ur 3D-anpassning, z ur golven (ett golv).')
            # Övriga tagningar med känd roll i paret: landmärke
            for x in tid:
                if x in reg or x not in huvudroll or huvudroll[x][1] not in mal: continue
                roll = huvudroll[x][1]
                reg[x] = dict(M=landmark(x, roll), metod='landmark', status='antagen', residual_m=None, skala=1.0,
                              kommentar=f'{roll}:s uppmätta bäcken = stol_{roll}, torsot vänd mot motparten (antagen dialogaxel); ingen bildkoppling till andra tagningar (se c_bildmatchning).')
            # Rester: stationsprior. Kamerastationen = medelläget för de nära motbildskamerorna i platsen.
            kam_pl = [reg[x]['M'] @ np.array([0, 0, 0, 1.]) for x in reg if x in huvudroll and huvudroll[x][1] in mal and
                      tid[x]['personer'][huvudroll[x][0]]['huvudavstand_m'] <= 1.5 * min(e[1] for e in (a1 if huvudroll[x][1] == r1 else a2))]
            for x in tid:
                if x in reg: continue
                t = tid[x]; h = hand.get(x, {}); blick = math.radians(h['kamera_blick_grader']) if 'kamera_blick_grader' in h else 0.0
                st = np.mean([k[:2] for k in kam_pl], 0) if kam_pl else np.zeros(2)
                yaw = blick - t['kamera_blick_rad']; M = matris(yaw, [*st, -t['golv']['hojd_m']])
                if 'person_pos_m' in h and x in huvudroll:
                    pp = t['personer'][huvudroll[x][0]]
                    target = np.array(h['person_pos_m'], float); target[2] = pp['backen'][2]-t['golv']['hojd_m']
                    M[:3,3] = target - M[:3,:3] @ pp['backen']
                reg[x] = dict(M=M, metod='antagande', status='antagen', residual_m=None, skala=1.0,
                              kommentar=('Ingen bildkoppling och ingen roll i dialogparet. Kameran placeras på dialogkamerornas medelställe (en fotograf som vänder sig), blickriktning ' +
                                         (f'{h["kamera_blick_grader"]:.0f} grader i platsen: {h.get("orsak", "handgjort")}.' if 'kamera_blick_grader' in h else '0 grader (+X): godtyckligt val, ingen uppgift finns.')),
                              hand=h or None)
                if 'person_pos_m' in h:
                    reg[x]['kommentar'] = ('Ingen bildkoppling. Bäckenets XY sätts till handangivet läge, Z följer det befintliga golvet. Kamera och person flyttas tillsammans så deras uppmätta relation bevaras. Antaget: ' + h.get('orsak','handgjort läge'))
        for t in tagningar:
            if t['id'] not in reg: raise SystemExit('Ingen registrering för ' + t['id'])

    # ---------- golv, objekt, ankare, bindningar
    gol = []
    for t in tagningar:
        gol.append(dict(tagning=t['id'], hojd_i_tagningen_m=t['golv']['hojd_m'], kalla=t['golv']['kalla'], status='uppmatt' if t['golv']['uppmatt_ur_fotter'] else 'antagen'))
    golv_h = -tagningar[0]['golv']['hojd_m'] + tagningar[0]['golv']['hojd_m'] if not ident else tagningar[0]['golv']['hojd_m']
    if ident: golv_h = tagningar[0]['golv']['hojd_m']
    else: golv_h = 0.0
    alla_antagna = all(g['status'] == 'antagen' for g in gol)
    golv = dict(hojd_m=golv_h, normal=[0.0, 0.0, 1.0], status='antagen' if alla_antagna else 'uppmatt',
                kalla='; '.join(sorted({g['kalla'] for g in gol})), per_tagning=gol,
                kommentar='Alla tagningars golv läggs i ett plan.' if not ident else 'Tagningens eget golv.')
    avvisade = []; objekt = []; vaggar = []
    if ident:
        t = tagningar[0]; G = t['G']
        for o in t['rum']['objects']:
            objekt.append(dict(id=o['id'], etikett=o['label'], typ='fast', centrum_m=(G @ np.array(o['centre'])).tolist(), matt_m=list(o['size']), yaw_rad=o['yaw'],
                               top_slope=o.get('top_slope', 0), status='uppmatt' if not o.get('antagen') else 'antagen', delvis=True, textur=None,
                               observationer=[dict(tagning=t['id'], id=o['id'], stodpunkter=o.get('support_points'))]))
        for w in t['rum']['walls']:
            tg = G @ w['tangent']
            vaggar.append(dict(id=w['id'], centrum_m=(G @ w['centre']).tolist(), yaw_rad=math.atan2(tg[1], tg[0]), bredd_m=w['width'], hojd_m=w['height'],
                               status='antagen' if w.get('antagen') else 'uppmatt', stodpunkter=w.get('support'), textur=None))
    else:
        obs = [o for t in tagningar for o in objekt_i_platsen(t, reg[t['id']]['M'])]
        sl = sla_ihop(obs, avvisade)
        for t in tagningar:   # väggfragment: bara hela väggar med stöd tas in
            for w in t['rum']['walls']:
                if w['height'] < 1.8 or w.get('support', 0) < 1000:
                    avvisade.append(dict(tagning=t['id'], id=w['id'], etikett='vägg', orsak=f'väggfragment {w["width"]:.1f} × {w["height"]:.1f} m med {w.get("support", 0)} stödpunkter: lägre än 1,8 m eller under 1000 punkter, inget rum kan byggas på det'))
        objekt_raw = sl
    # ankare ur personer
    ankare, bindningar = [], []
    if not ident and tagningar:
        # Stationära personer per roll, deras bäcken i platsen över alla tagningar där de syns
        per_roll = {}
        for t in tagningar:
            M = reg[t['id']]['M']
            for p, pp in t['personer'].items():
                r = rollmap[(t['id'], p)]
                pos = M[:3, :3] @ pp['backen'] + M[:3, 3]; fr = cirkular_medel([pp['framat_rad']]) + math.atan2(M[1, 0], M[0, 0])
                per_roll.setdefault(r, []).append(dict(tagning=t['id'], ingest_id=p, pos=pos, framat=fr, sprid=pp['spridning_m'], rutor=pp['rutor'],
                                                       backenhojd=float(pp['backen'][2] - t['golv']['hojd_m']), ben=pp['ben_synliga'], huvud_h=float(pp['huvud'][2] - t['golv']['hojd_m'])))
        for r, lst in sorted(per_roll.items()):
            if r.startswith('okand_'): continue
            if max(e['sprid'] for e in lst) > STILLA_MAX_SPRIDNING_M: continue
            best = max(lst, key=lambda e: e['rutor']); hojd = float(np.median([e['backenhojd'] for e in lst]))
            staende = hojd > STOL_MAX_BACKENHOJD_M; kind = 'staplats' if staende else 'sate'; aid = f'{"staplats" if staende else "stol"}_{r}'
            # läget: antagen om rollen är ankare i grammatiken, annars medel av mätningarna
            pos = np.average([e['pos'] for e in lst], axis=0, weights=[e['rutor'] for e in lst]); pos[2] = golv_h
            ankare.append(dict(id=aid, typ=kind, etikett=('stol för ' if kind == 'sate' else 'ståplats för ') + r, pos_m=pos.tolist(),
                               riktning_rad=cirkular_medel([e['framat'] for e in lst], [e['rutor'] for e in lst]), hojd_m=hojd,
                               status='antagen' if reg[best['tagning']]['status'] == 'antagen' else 'uppmatt', osakerhet_m=float(max(np.linalg.norm(e['pos'][:2] - pos[:2]) for e in lst)) if len(lst) > 1 else None,
                               metod=('Personens uppmätta bäcken på golvet (median över tagningens rutor), placerad via tagningens transform. ' +
                                      ('Läget i platsen är antaget (dialogaxel).' if reg[best['tagning']]['metod'] != 'matchning' else '')).strip(),
                               roll=r, backenhojd_gräns_m=STOL_MAX_BACKENHOJD_M))
            for e in lst:
                bindningar.append(dict(tagning=e['tagning'], ingest_id=e['ingest_id'], roll=r, ankare=aid, hallning='star' if staende else 'sitter', status='antagen',
                                       avstand_till_ankare_m=float(np.linalg.norm(e['pos'][:2] - np.array(ankare[-1]['pos_m'][:2])))))
        # bordsankare och sammanslagna objekt
        sorterade = sorted(objekt_raw, key=lambda o: (o['etikett'], o['centrum'][1], o['centrum'][0])); seats = [a for a in ankare if a['typ'] == 'sate']; namnat = {}
        for a in seats:   # varje stol ger namn åt närmaste bord inom 1 m
            kand = [(kant_narmast(o, a['pos_m'])[1], k) for k, o in enumerate(sorterade) if o['etikett'] == 'table' and k not in namnat]
            if kand and min(kand)[0] < 1.0: namnat[min(kand)[1]] = f'bord_{a["roll"]}'
        for k, o in enumerate(sorterade):
            namn = namnat.get(k) or f'{"bord" if o["etikett"] == "table" else o["etikett"]}_{k + 1}'
            n_tag = sorted({x['tagning'] for x in o['obs']})
            objekt.append(dict(id=namn, etikett=o['etikett'], typ='fast', centrum_m=o['centrum'].tolist(), matt_m=o['matt'], yaw_rad=o['yaw'], top_slope=0,
                               status='antagen', delvis=True, textur=None,
                               observationer=[dict(tagning=x['tagning'], id=x['id'], stodpunkter=x['stod']) for x in sorted(o['obs'], key=lambda x: (x['tagning'], x['id']))],
                               kommentar=f'Sammanslagen ur {len(o["obs"])} enkelvyslådor i {", ".join(n_tag)}; centrum = stödviktat medel, mått = största sedda fotavtryck. Fotavtrycket är det som syns (bildkanten kapar ytan); spridning mellan observationerna {o["spridning_m"]*100:.0f} cm.'))
        for a in [a for a in ankare if a['typ'] == 'sate']:
            bord = [o for o in objekt if o['etikett'] == 'table']
            if not bord: continue
            ob = min(bord, key=lambda o: kant_narmast(dict(centrum=np.array(o['centrum_m']), matt=o['matt_m'], yaw=o['yaw_rad']), a['pos_m'])[1])
            q, d = kant_narmast(dict(centrum=np.array(ob['centrum_m']), matt=ob['matt_m'], yaw=ob['yaw_rad']), a['pos_m'])
            if d < 1.0:
                dd = np.array(a['pos_m'][:2]) - q
                ankare.append(dict(id=f'bordskant_{a["roll"]}', typ='bordskant', etikett='bordskant närmast ' + a['id'], pos_m=[float(q[0]), float(q[1]), float(ob['centrum_m'][2] + ob['matt_m'][2] / 2)],
                                   riktning_rad=float(math.atan2(dd[1], dd[0])), hojd_m=float(ob['centrum_m'][2] + ob['matt_m'][2] / 2 - golv_h), status='antagen', osakerhet_m=d,
                                   metod=f'Närmaste punkt på {ob["id"]}:s sedda fotavtryck från {a["id"]}; avståndet bäcken–kant är {d:.2f} m. Riktningen pekar mot stolen.', roll=a['roll']))
    elif ident:
        for t in tagningar:
            for p, pp in sorted(t['personer'].items()):
                if pp['spridning_m'] > STILLA_MAX_SPRIDNING_M: continue
                aid = f'staplats_{p}'; pos = pp['backen'].copy(); pos[2] = golv_h
                ankare.append(dict(id=aid, typ='staplats', etikett=f'ståplats för person {p}', pos_m=pos.tolist(), riktning_rad=pp['framat_rad'], hojd_m=float(pp['backen'][2] - golv_h),
                                   status='uppmatt', osakerhet_m=pp['spridning_m'], metod='Personens uppmätta bäcken (median), tagningens egen värld.', roll=p, backenhojd_gräns_m=STOL_MAX_BACKENHOJD_M))
                bindningar.append(dict(tagning=t['id'], ingest_id=p, roll=p, ankare=aid, hallning='star', status='uppmatt', avstand_till_ankare_m=0.0))
    ankare.sort(key=lambda a: (a['typ'], a['id']))

    # ---------- skriv
    def regpost(t):
        r = reg[t['id']]; M = r['M']; yaw = math.atan2(M[1, 0], M[0, 0])
        q = dict(metod=r['metod'], status=r['status'], skala_status='antagen', residual_m=r['residual_m'], kommentar=r['kommentar'])
        for k in ('mot', 'inliers', 'rotation_grader', 'translation_m', 'lutning_kvar_grader', 'personbacken_avvikelse_m', 'rest_xy_m', 'hojdskillnad_mot_golvantagandet_m', 'rest_fri_rigid_m', 'station', 'hand'):
            if r.get(k) is not None: q[k] = r[k]
        return dict(id=t['id'], mapp=t['mapp'].name, antal_rutor=t['N'], statisk_kamera=t['statisk'],
                    till_plats=dict(yaw_rad=yaw, translation_m=M[:3, 3].tolist(), skala=1.0, matris=M.tolist()),
                    kamera_i_platsen=dict(pos_m=(M[:3, 3] + M[:3, :3] @ (tagningar and t['G'] @ t['V']['kam_C'][0])).tolist(), blick_rad=(yaw + t['kamera_blick_rad']) if t['kamera_blick_rad'] is not None else None,
                                          lutning_ner_grader=t['kamera_lutning_grader']) if t['statisk'] else None,
                    kvalitet=q, personer=[dict(ingest_id=p, roll=rollmap[(t['id'], p)], rutor=pp['rutor']) for p, pp in sorted(t['personer'].items())])
    plats = dict(schema_version=VERSION, id='plats_1', klipp=mapp.name, typ='okand',
                 beskrivning=('Platsen alla tagningar utspelar sig på: en värld i meter, tyngdkraftsriktad (+Z upp), ' + ('tagningens egen Blender-värld.' if ident else 'origo på golvet under första rollens stol, +Y mot andra rollens stol.')),
                 ramar=dict(enhet='m', upp='+Z', origo='tagningens egen origo (kameran i första rutan)' if ident else (f'golvet under stol_{par[0]}' if par else 'identitet: tagningarnas egna världar (PATCH flera/)'),
                            axlar='X höger, Y framåt, Z upp (högerhänt)' if ident else (f'+Y från stol_{par[0]} mot stol_{par[1]}, X höger sett längs +Y, Z upp' if len(par)>1 else 'tagningarnas egna axlar (PATCH flera/)'), skala='1,0 (antagen: se plats_matt.json a_personer)'),
                 golv=golv, objekt=objekt, vaggar=vaggar, avvisade=avvisade, ankare=ankare, bindningar=bindningar,
                 tagningar=[regpost(t) for t in tagningar],
                 antaganden=[a for a in [
                     'Skala 1,0 i alla tagningar: kropparnas storlek är jämn mellan tagningar av samma person (plats_matt.json), men brännvidden är satt till 1024 px i de flesta tagningar.' if not ident else None,
                     'Golvet ligger 1,45 m under kameran i tagningar utan synliga fötter (ingest-steget golv).' if any(g['status'] == 'antagen' for g in gol) else None,
                     'Dialogaxel, motbildskamera vid motpartens huvud och stolsavstånd är scengrammatik (plats_matt.json d_grammatik), inte mätt.' if not ident and matt['d_grammatik'].get('anvand') else None] if a])
    if not ident and not matt['d_grammatik'].get('anvand'): plats['antaganden'].append('Ingen scengrammatik kunde tillämpas: ' + str(matt['d_grammatik'].get('orsak')))
    if hand.get('layout'):
        plats['layout'] = hand['layout']
        plats['antaganden'].append(hand['layout']['orsak'])
    # En ensam äldre tagning behåller identitetsflödet tills en mall valts.
    # Det gör bland annat bars gamla plan byte-identisk.
    if not ident or hand.get('rumsmall') or getattr(args, 'rumsmall', None):
        from rumsmall import moblera
        moblera(plats, getattr(args, 'rumsmall', None) or hand.get('rumsmall'))
        fitted = plats['rumsmall']['ankare']; tol = .35   # antagen tolerans, meter
        for t in tagningar:
            M = reg[t['id']]['M']
            upptagna = {b['ankare'] for b in bindningar if b['tagning']==t['id']}
            for pid, pp in t['personer'].items():
                roll = rollmap[(t['id'],pid)]
                if not roll.startswith('okand_'): continue
                pos = M[:3,:3] @ pp['backen']+M[:3,3]
                seats = [(float(np.linalg.norm(pos[:2]-np.array(a['pos_m'][:2]))),a) for a in fitted if a['typ']=='sate' and a['id'] not in upptagna]
                dist,a = min(seats,key=lambda x:x[0]) if seats else (None,None)
                if a and dist <= tol:
                    bindningar.append(dict(tagning=t['id'],ingest_id=pid,roll=roll,ankare=a['id'],hallning='sitter',status='antagen',avstand_till_ankare_m=dist))
                    upptagna.add(a['id'])
                else:
                    plats['utelamnade'].append(dict(tagning=t['id'],ingest_id=pid,person=roll,avstand_m=dist,tolerans_m=tol,status='antagen',
                                                   orsak='Ingen roll eller bindning; ingen ledig mallsits inom toleransen. Renderas inte utan stöd.'))
        matt['rumsmall'] = dict(id=plats['rumsmall']['id'],passning=plats['rumsmall']['passning'],utelamnade=plats['utelamnade'])
    return plats, matt, ut, tagningar, reg


def sammanfatta(plats, matt):
    rad = ['# Plats ' + plats['id'], '', plats['beskrivning'], '', f'Golv: z = {plats["golv"]["hojd_m"]:.2f} m ({plats["golv"]["status"]}). Objekt: {len(plats["objekt"])}, ankare: {len(plats["ankare"])}, avvisade observationer: {len(plats["avvisade"])}.', '',
           '| tagning | metod | skala | residual (m) | status |', '|---|---|---|---|---|']
    for t in plats['tagningar']:
        q = t['kvalitet']; rad.append(f'| {t["id"]} | {q["metod"]} | {t["till_plats"]["skala"]} | {"–" if q["residual_m"] is None else round(q["residual_m"], 3)} | {q["status"]} |')
    rad += ['', '| ankare | typ | position (m) | riktning (grad) | status |', '|---|---|---|---|---|']
    for a in plats['ankare']: rad.append(f'| {a["id"]} | {a["typ"]} | {", ".join(f"{x:.2f}" for x in a["pos_m"])} | {math.degrees(a["riktning_rad"]):.0f} | {a["status"]} |')
    rad += ['', 'Antaganden:'] + ['- ' + a for a in plats['antaganden']]
    if plats.get('rumsmall'):
        r = plats['rumsmall']
        rad += ['', '## Rumsmall', '', f'Mall: {r["id"]}. Rigid ankarrest RMS: {r["passning"]["rms_m"]:.3f} m. Därefter fästs stöd till ankare, se justeringar i plats.json. Alla mått och material är mallvärden. Djupfragmenten ovan är enbart evidens.',
                '', 'Utelämnade: ' + ', '.join(x['person']+': '+x['orsak'] for x in plats['utelamnade'])]
    return '\n'.join(rad) + '\n'


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('ingest'); a.add_argument('--ut'); a.add_argument('--scen3d', default=str(HIT.parent / 'scen3d.json')); a.add_argument('--hand'); a.add_argument('--video')
    a.add_argument('--rumsmall', help='Mall-id i kontrakt/rumsmall, eller lokal JSON-fil.')
    x = a.parse_args()
    import time
    t0 = time.time(); plats, matt, ut, tagningar, reg = bygg_plats(x); matt['tid_s'] = None
    ut.mkdir(parents=True, exist_ok=True)
    skriv(ut / 'plats.json', plats); skriv(ut / 'plats_matt.json', {k: v for k, v in matt.items() if k != 'tid_s'}); (ut / 'plats.md').write_text(sammanfatta(plats, matt), encoding='utf-8', newline='\n')
    print(f'plats.py: {len(tagningar)} tagning(ar), {len(plats["objekt"])} objekt, {len(plats["ankare"])} ankare, {time.time() - t0:.1f} s -> {ut}')


if __name__ == '__main__':
    main()
