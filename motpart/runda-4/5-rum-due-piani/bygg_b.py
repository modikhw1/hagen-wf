"""Variant B: bildstödd rum-/kamerarättning av Due Piani utan image-gen.

Läser det frysta paketet A (skrivs aldrig över) och skriver ut/paket_B.json + ut/recept_B.json.
Regler (allmänna; indata per tagning redovisas i receptet):
  B1  Ingen schablonåkning: kameran är statisk per tagning. Kroppsspåren skattades per ruta i
      kamerans egna koordinater med stillastående kamera, så verklig kamerarörelse finns redan i
      motivets rörelse. Bildmätningen (kamera_matning.json) redovisas som kontroll.
  B2  Kamerans position registreras mot oberoende 2D-led (yolo11n-pose) med kroppsspåren orörda.
  B3  Lodlinje: där A:s kameralutning ligger på ingestens klampgräns (18 grader) ersätts den av
      bildstöd: vilande rund yta (tallrik/panna, ellips -> plannormal) eller rak bål hos stående
      person. Kamera och kroppar i tagningen roteras tillsammans kring kameran (projektionen bevaras).
  B4  Dubblettspår av samma person i en tagning: behåll spåret med lägst 2D-fel.
  B5  Inga påhittade stöd: bord_1 och bord_s8 tas bort. Stöd läggs bara där bilden visar dem
      (spis i S8, bänk i S10) med antagen höjd 0,90 m.
  B6  Maträtt: ellipsbaserad pose där kartläggning finns (S2/S8/S10), i händerna där en stående
      person håller den (S1/S3/S11/S12), annars märks A:s schablon harledd_mall.
"""
from __future__ import annotations
import copy, hashlib, json, math, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from geom import q2R, R2q, f_px, project, world_to_cv, led_rutor  # noqa: E402
from sparval import COCO  # noqa: E402

ROOT = HERE.parents[2]
A_FIL = ROOT / 'arbetsbord/data/ingest_v2/duepiani/paket.json'
OUT = HERE / 'ut'
KLAMP_GRADER = 17.9
BANKHOJD = 0.90           # antagen
TALLRIK_KANT_OVER_STOD = 0.03
PANNA_KANT_OVER_STOD = 0.12  # galler 0,02 + pannans djup 0,10 (antaget)
FOT = None  # sätts per spår från A (bevarar A:s golvkontakt)


def _np(o):
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, np.ndarray): return o.tolist()
    raise TypeError(type(o))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def B_from_cv(v):
    v = np.asarray(v, float)
    return np.array([v[0], -v[1], -v[2]])


def pitch_deg(R):
    fwd = R @ np.array([0, 0, -1.0])
    return math.degrees(math.asin(max(-1, min(1, fwd[2]))))


def align_up(R_A, up_local):
    """Ny kamerarotation där lokal vektor up_local blir världens +Z; kursen behålls från A."""
    u = up_local / np.linalg.norm(up_local)
    f = np.array([0, 0, -1.0])
    h = f - (f @ u) * u; h /= np.linalg.norm(h)
    fw = R_A @ f; hw = np.array([fw[0], fw[1], 0.0]); hw /= np.linalg.norm(hw)
    ez = np.array([0, 0, 1.0])
    L = np.stack([h, u, np.cross(h, u)], axis=1)
    Wm = np.stack([hw, ez, np.cross(hw, ez)], axis=1)
    return Wm @ L.T


def circle_pose(pts, f, cx, cy, r):
    """Cirkel med radie r ur bildpunkter på kanten. Returnerar lösningar (kostnad, mitt_cv, normal_cv)."""
    P = np.asarray(pts, float)
    d = np.stack([(P[:, 0] - cx) / f, (P[:, 1] - cy) / f, np.ones(len(P))], axis=1)
    import cv2
    e = cv2.fitEllipse(P.astype(np.float32))
    c0 = np.array([(e[0][0] - cx) / f, (e[0][1] - cy) / f, 1.0])
    c0 *= f * 2 * r / max(e[1])

    def res(x):
        c = x[:3]; n = np.array([x[3], x[4], -1.0]); n /= np.linalg.norm(n)
        t = (n @ c) / (d @ n)
        X = d * t[:, None]
        return np.linalg.norm(X - c, axis=1) - r

    sols = []
    for a in np.linspace(-1.6, 1.6, 7):
        for b in np.linspace(-1.6, 1.6, 7):
            s = least_squares(res, np.r_[c0, a, b], method='lm', max_nfev=400)
            n = np.array([s.x[3], s.x[4], -1.0]); n /= np.linalg.norm(n)
            if s.x[2] <= 0:
                continue
            cost = float(np.sqrt(np.mean(s.fun ** 2)))
            if not any(np.linalg.norm(n - m) < 0.05 for _, _, m in sols):
                sols.append((cost, s.x[:3].copy(), n))
    sols.sort(key=lambda z: z[0])
    best = sols[0][0]
    return [s for s in sols if s[0] < best * 1.5 + 0.003], e


def euler_from_normal(n):
    n = n / np.linalg.norm(n); z = np.array([0, 0, 1.0]); v = np.cross(z, n); s = np.linalg.norm(v); c = z @ n
    if s < 1e-8:
        R = np.eye(3)
    else:
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = np.eye(3) + vx + vx @ vx * ((1 - c) / s ** 2)
    a = math.atan2(R[2, 1], R[2, 2]); b = math.asin(max(-1, min(1, -R[2, 0]))); g = math.atan2(R[1, 0], R[0, 0])
    return [round(a, 4), round(b, 4), round(g, 4)]


def transform_tracks(pk, sid, pids, fn):
    for pid in pids:
        for tr in pk['rorelse'].get(pid, []):
            if tr['tagning'] != sid:
                continue
            for row in tr['rutor']:
                J = np.array(row[1:], float).reshape(-1, 3) / 1000.0
                J = fn(J)
                row[1:] = [int(round(v * 1000)) for v in J.reshape(-1)]


def fit_translation(pk, pose, sid, pids, C, R, lens, W, H, ix):
    """Kameraposition (3 frihetsgrader) mot 2D-led; rotation och kroppar låsta."""
    sk = 540.0 / W; f = f_px(lens, W); obs = []
    # Endast spår som faktiskt motsvarar en 2D-person (bakgrundsfigurer utan 2D-led tas inte med)
    from sparval import fel_per_spar
    tmp = copy.deepcopy(pk); tt = next(x for x in tmp['tagningar'] if x['id'] == sid)
    tt['kamera'] = {'typ': 'statisk', 'statisk': True, 'nycklar': [[tt['ut'][0], *C, *R2q(R), lens]]}
    fel = {p: v['median_px'] for p, v in fel_per_spar(tmp, pose, sid).items() if v['median_px'] is not None and p in pids}
    if fel:
        m = min(fel.values()); pids = [p for p in pids if p in fel and fel[p] <= max(2.0 * m, m + 60)]
    for pid in pids:
        fr, X = led_rutor(pk, pid, sid)
        if X is None:
            continue
        for u, J in list(zip(fr, X))[::2]:
            pp = pose['rutor'][u]['personer']
            if not pp:
                continue
            uv, z = project(J, C, R, f, W, H); uv = uv * sk
            cen = uv[[ix['l_uparm'], ix['r_uparm'], ix['l_upleg'], ix['r_upleg']]].mean(0)
            p = min(pp, key=lambda p: np.hypot((p['box'][0] + p['box'][2]) / 2 - cen[0], (p['box'][1] + p['box'][3]) / 2 - cen[1]))
            kp = np.array(p['kp'])
            for c, j in COCO.items():
                if kp[c, 2] > 0.5:
                    obs.append((J[ix[j]], kp[c, :2] / sk))
    if len(obs) < 12:
        return C, None, None, len(obs)
    Pj = np.array([o[0] for o in obs]); Q = np.array([o[1] for o in obs])

    def res(dx):
        uv, z = project(Pj, C + dx, R, f, W, H)
        return (uv - Q).reshape(-1)

    r0 = np.median(np.linalg.norm(res(np.zeros(3)).reshape(-1, 2), axis=1)) * sk
    s = least_squares(res, np.zeros(3), loss='soft_l1', f_scale=15.0, bounds=([-1.2, -1.5, -1.0], [1.2, 1.5, 1.0]))
    r1 = np.median(np.linalg.norm(s.fun.reshape(-1, 2), axis=1)) * sk
    return C + s.x, round(float(r0), 1), round(float(r1), 1), len(obs)


def main():
    t0 = time.perf_counter()
    A = json.loads(A_FIL.read_text(encoding='utf-8'))
    pose = json.loads((OUT / 'pose2d.json').read_text(encoding='utf-8'))
    kart = json.loads((HERE / 'kartlaggning_manuell.json').read_text(encoding='utf-8'))
    matning = {r['tagning']: r for r in json.loads((OUT / 'kamera_matning.json').read_text(encoding='utf-8'))}
    B = copy.deepcopy(A)
    B['klipp']['variant'] = 'B: bildstödd rum/kamera utan image-gen (motpart/runda-4/5-rum-due-piani)'
    ix = {n: i for i, n in enumerate(A['leder'])}
    W, H = A['bild']['bredd'], A['bild']['hojd']
    sk = 540.0 / W
    recept = {'variant': 'B', 'a_paket_sha256': sha(A_FIL), 'kod_sha256': sha(__file__),
              'kartlaggning_sha256': sha(HERE / 'kartlaggning_manuell.json'),
              'pose2d_sha256': sha(OUT / 'pose2d.json'), 'antaganden': {
                  'bankhojd_m': BANKHOJD, 'tallrik_diameter_m': kart['storleksprior_m']['tallrik'],
                  'panna_diameter_m': kart['storleksprior_m']['panna'], 'panna_kant_over_stod_m': PANNA_KANT_OVER_STOD},
              'manuella_inslag': [], 'tagningar': {}}
    nya_objekt = [o for o in A['objekt'] if o['id'] == 'golv']
    borttagna = []
    for o in A['objekt']:
        if o['id'] == 'golv':
            continue
        if o['typ'] == 'bord':
            borttagna.append(o['id']); continue
        nya_objekt.append(copy.deepcopy(o))
    obj_by_id = {o['id']: o for o in nya_objekt}

    for t in B['tagningar']:
        sid = t['id']; a0, b0 = t['ut']; k = t['kamera']['nycklar'][0]
        R_A = q2R(k[4:8]); lens = float(k[8]); C_A = np.array([0.0, 0.0, 1.38])
        f = f_px(lens, W); info = {'A_lutning_grader': round(pitch_deg(R_A), 1),
                                   'A_kamera': t['kamera']['typ'], 'A_framat_m': round(t['kamera']['nycklar'][-1][2] - k[2], 3),
                                   'bildmatning': {kk: matning[sid][kk] for kk in ('skala_forsta_till_sista', 'mitt_forflyttning_px', 'median_inlier_andel')},
                                   'regler': ['B1']}
        pids = [p['id'] for p in t['personer']]
        R = R_A.copy(); C = C_A.copy()

        # B4: dubbletter
        if len(pids) > 1:
            from sparval import fel_per_spar
            tmp = copy.deepcopy(A)
            tt = next(x for x in tmp['tagningar'] if x['id'] == sid)
            tt['kamera'] = {'typ': 'statisk', 'statisk': True, 'nycklar': [[a0, 0, 0, 1.38, *k[4:8], lens]]}
            fel = fel_per_spar(tmp, pose, sid)
            ok = {p: v['median_px'] for p, v in fel.items() if v['median_px'] is not None}
            if ok:
                bast = min(ok, key=ok.get)
                dubb = [p for p, v in ok.items() if p != bast and v > 0 and _overlap(A, sid, p, bast)]
                if dubb:
                    info['regler'].append('B4'); info['dubbletter_bort'] = dubb; info['spar_2d_fel_px'] = ok
                    for p in dubb:
                        B['rorelse'][p] = [tr for tr in B['rorelse'][p] if tr['tagning'] != sid]
                    t['personer'] = [p for p in t['personer'] if p['id'] not in dubb]
                    pids = [p['id'] for p in t['personer']]

        kt = kart['tagningar'].get(sid)
        klampad = abs(pitch_deg(R_A)) >= KLAMP_GRADER
        # B3 + B6 för kartlagda maträtter
        if kt:
            r = kart['storleksprior_m'][kt['foremal']] / 2
            recept['manuella_inslag'].append({'tagning': sid, 'nyckelrutor': list(kt['nycklar']), 'punkter': sum(len(v) for v in kt['nycklar'].values())})
            poses = {}
            for n, pts in kt['nycklar'].items():
                pts540 = np.array(pts, float)
                sols, e = circle_pose(pts540 / sk, f, W / 2, H / 2, r)
                poses[int(n)] = sols
            if kt['stod'] in ('spis', 'bank'):
                n0 = sorted(poses)[len(poses) // 2]; sols = poses[n0]
                best = max(sols, key=lambda s: (R_A @ B_from_cv(s[2]))[2])
                cost, c_cv, n_cv = best
                up_local = B_from_cv(n_cv)
                R = align_up(R_A, up_local)
                rim_z = BANKHOJD + (PANNA_KANT_OVER_STOD if kt['foremal'] == 'panna' else TALLRIK_KANT_OVER_STOD)
                c_w_rel = R @ B_from_cv(c_cv)
                C = np.array([0.0, 0.0, rim_z - c_w_rel[2]])
                center = C + c_w_rel
                info['regler'] += ['B3', 'B5', 'B6']
                info['lodlinje'] = f"{kt['foremal']} vilar på {kt['stod']}: ellipsnormal (manuell kartläggning, ruta {n0})"
                info['ellips_rms_m'] = round(cost, 4); info['tvetydiga_losningar'] = len(sols)
                info['avstand_kamera_foremal_m'] = round(float(np.linalg.norm(c_cv)), 3)
                Rrel = R @ R_A.T
                transform_tracks(B, sid, pids, lambda J: (J - C_A) @ Rrel.T + C)
                oid = f'mat_{sid}'; old = obj_by_id.get(oid, {})
                pal = old.get('farg_palett')
                if kt['foremal'] == 'panna':
                    mat = {'id': oid, 'bas': 'mat', 'typ': 'mat_skal', 'mat_stil': 'skal', 'etikett': 'Panna (s8)',
                           'farg': old.get('farg', '#9a6a3a'), 'farg_palett': pal, 'pos': [round(v, 3) for v in (center - np.array([0, 0, 0.05]))],
                           'rot': [0, 0, 0], 'matt': [2 * r, 2 * r, 0.10], 'tilltro': 'skattad_ur_bild', 'rum': 'gemensamt', 'synlig_ut': [[a0, b0]],
                           'kalla': 'ellips ur manuell kartläggning + antagen diameter 0,34 m'}
                    under = {'id': f'spis_{sid}', 'bas': 'spis', 'typ': 'spis', 'farg': '#8d9196',
                             'pos': [round(center[0], 3), round(center[1] + 0.12, 3), BANKHOJD / 2], 'rot': [0, 0, round(math.atan2((R @ [0, 0, -1.0])[1], (R @ [0, 0, -1.0])[0]) - math.pi / 2, 4)],
                             'matt': [0.9, 0.7, BANKHOJD], 'tilltro': 'harledd_mall', 'rum': 'gemensamt', 'synlig_ut': [[a0, b0]],
                             'kalla': 'spishäll syns i bild; mått och höjd 0,90 m antagna'}
                else:
                    mat = {'id': oid, 'bas': 'mat', 'typ': 'mat_tallrik', 'mat_stil': 'tallrik', 'etikett': f'Tallrik ({sid})',
                           'farg': old.get('farg', '#a4621c'), 'farg_palett': pal, 'pos': [round(v, 3) for v in center],
                           'rot': [0, 0, 0], 'matt': [2 * r, 2 * r, 0.07], 'tilltro': 'skattad_ur_bild', 'rum': 'gemensamt', 'synlig_ut': [[a0, b0]],
                           'kalla': 'ellips ur manuell kartläggning + antagen diameter 0,30 m'}
                    under = {'id': f'bank_{sid}', 'bas': 'bank', 'typ': 'bank', 'farg': '#a3a7ab',
                             'pos': [round(center[0], 3), round(center[1] + 0.15, 3), BANKHOJD / 2], 'rot': [0, 0, round(math.atan2((R @ [0, 0, -1.0])[1], (R @ [0, 0, -1.0])[0]) - math.pi / 2, 4)],
                             'matt': [1.4, 0.7, BANKHOJD], 'tilltro': 'harledd_mall', 'rum': 'gemensamt', 'synlig_ut': [[a0, b0]],
                             'kalla': 'stålbänk syns i bild; mått och höjd 0,90 m antagna'}
                obj_by_id[oid] = mat; obj_by_id[under['id']] = under
                for ex in kt.get('extra_foremal', []):
                    px = np.array(ex['pixel'], float) / sk
                    dv = np.array([(px[0] - W / 2) / f, (px[1] - H / 2) / f, 1.0]); dv /= np.linalg.norm(dv)
                    rim_cv = dv * ex['avstand_m']
                    n_cv = -dv + np.array([0, ex['oppning_mot_kamera_och_ned'], 0]); n_cv /= np.linalg.norm(n_cv)
                    n_w = R @ B_from_cv(n_cv); rim_w = C + R @ B_from_cv(rim_cv)
                    obj_by_id[ex['id']] = {'id': ex['id'], 'bas': 'mat', 'typ': ex['typ'], 'mat_stil': 'skal', 'etikett': ex['etikett'],
                                           'farg': '#9a6a3a', 'farg_palett': pal, 'pos': [round(float(v), 3) for v in rim_w - n_w * ex['djup_m'] / 2],
                                           'rot': euler_from_normal(n_w), 'matt': [ex['diameter_m'], ex['diameter_m'], ex['djup_m']],
                                           'tilltro': 'harledd_mall', 'rum': 'gemensamt', 'synlig_ut': [[a0, b0]], 'kalla': ex['kalla']}
                    recept['manuella_inslag'].append({'tagning': sid, 'objekt': ex['id'], 'art': 'manuell iscensättning (antagen)'})
            elif kt['stod'] == 'hand':
                info['regler'] += ['B3', 'B6']
                if klampad and pids:
                    ups = []
                    for pid in pids:
                        fr, X = led_rutor(B, pid, sid)
                        ups += list(X[:, ix['c_neck']] - X[:, ix['c_spine0']])
                    up_w = np.median(np.array(ups), axis=0); up_w /= np.linalg.norm(up_w)
                    info['bal_lutning_A_grader'] = round(math.degrees(math.acos(up_w[2])), 1)
                    R = align_up(R_A, R_A.T @ up_w)
                    Rrel = R @ R_A.T
                    transform_tracks(B, sid, pids, lambda J: (J - C_A) @ Rrel.T + C_A)
                    info['lodlinje'] = 'stående persons bål rätas upp (A låg på klampgränsen)'
                C, e0, e1, nobs = fit_translation(B, pose, sid, pids, C_A, R, lens, W, H, ix)
                info['regler'].append('B2'); info['registrering_2d_px'] = {'fore': e0, 'efter': e1, 'observationer': nobs}
                # per-ruta-tallrik ur ellipserna, interpolerad mellan nyckelrutor
                keys = sorted(poses)
                wpose = {}
                for n in keys:
                    sols = poses[n]
                    best = max(sols, key=lambda s: (R @ B_from_cv(s[2]))[2])
                    wpose[n] = (C + R @ B_from_cv(best[1]), R @ B_from_cv(best[2]), best[0])
                info['ellips_rms_m'] = {str(n): round(wpose[n][2], 4) for n in keys}
                old = obj_by_id.pop(f'mat_{sid}', {})
                for u in range(a0, b0):
                    if u <= keys[0]:
                        p, nrm = wpose[keys[0]][:2]
                    elif u >= keys[-1]:
                        p, nrm = wpose[keys[-1]][:2]
                    else:
                        k0 = max(x for x in keys if x <= u); k1 = min(x for x in keys if x > u); a = (u - k0) / (k1 - k0)
                        p = wpose[k0][0] * (1 - a) + wpose[k1][0] * a; nrm = wpose[k0][1] * (1 - a) + wpose[k1][1] * a
                    obj_by_id[f'mat_{sid}_{u}'] = {'id': f'mat_{sid}_{u}', 'bas': 'mat', 'typ': 'mat_tallrik', 'mat_stil': 'tallrik',
                                                   'farg': old.get('farg', '#a4621c'), 'farg_palett': old.get('farg_palett'),
                                                   'pos': [round(float(v), 3) for v in p], 'rot': euler_from_normal(nrm),
                                                   'matt': [2 * r, 2 * r, 0.07], 'tilltro': 'skattad_ur_bild', 'rum': 'gemensamt',
                                                   'synlig_ut': [[u, u + 1]], 'kalla': 'ellips per nyckelruta, interpolerad'}
                hands = []
                for pid in pids:
                    fr, X = led_rutor(B, pid, sid)
                    for u, J in zip(fr, X):
                        if u in wpose:
                            hands.append(min(np.linalg.norm(J[ix['l_hand_mitt']] - wpose[u][0]), np.linalg.norm(J[ix['r_hand_mitt']] - wpose[u][0])) - r)
                info['hand_till_tallrikskant_m'] = [round(float(h), 3) for h in hands]
        elif pids:
            C, e0, e1, nobs = fit_translation(B, pose, sid, pids, C_A, R, lens, W, H, ix)
            if e1 is not None:
                info['regler'].append('B2'); info['registrering_2d_px'] = {'fore': e0, 'efter': e1, 'observationer': nobs}
            else:
                C = C_A; info['registrering_2d_px'] = {'fore': None, 'efter': None, 'observationer': nobs, 'not': 'för få 2D-led; A-position'}
            oid = f'mat_{sid}'; old = obj_by_id.get(oid)
            stand = [p for p in pids if A['personer'][p]['pose'] == 'staende']
            hold = []
            if old and stand:
                fr, X = led_rutor(B, stand[0], sid)
                for u, J in zip(fr, X):
                    lh, rh = J[ix['l_hand_mitt']], J[ix['r_hand_mitt']]
                    if np.linalg.norm(lh - rh) < 0.55:
                        hold.append((u, (lh + rh) / 2))
            if old and len(hold) >= 0.8 * (b0 - a0) and sid in ('s1', 's3', 's11', 's12'):
                obj_by_id.pop(oid)
                for u, p in hold:
                    obj_by_id[f'{oid}_{u}'] = {'id': f'{oid}_{u}', 'bas': 'mat', 'typ': 'mat_tallrik', 'mat_stil': 'tallrik',
                                              'farg': old['farg'], 'farg_palett': old.get('farg_palett'),
                                              'pos': [round(float(v), 3) for v in p], 'rot': [0, 0, 0], 'matt': [0.30, 0.30, 0.07],
                                              'tilltro': 'skattad_ur_bild', 'rum': 'gemensamt', 'synlig_ut': [[u, u + 1]],
                                              'kalla': 'mitt mellan händerna (kroppsspår); diameter 0,30 m antagen'}
                info['regler'].append('B6'); info['matratt'] = f'i händerna {len(hold)}/{b0 - a0} rutor'
            elif old:
                old['tilltro'] = 'harledd_mall'; old['kalla'] = 'A-schablon (0,34 m, placering ur handled/bål); ej prövad i B'
                info['matratt'] = 'A-schablon märkt harledd_mall'
        t['kamera'] = {'typ': 'statisk', 'statisk': True, 'nycklar': [[a0, *[round(float(v), 4) for v in C], *R2q(R), lens]],
                       'kalla_B': info.get('lodlinje', 'rotation från A') + '; position: ' + (
                           'registrerad mot 2D-led' if 'B2' in info['regler'] else 'ur föremålets storlek och antagen stödhöjd' if kt else 'A')}
        info['B_lutning_grader'] = round(pitch_deg(R), 1)
        info['B_kamera_pos'] = [round(float(v), 3) for v in C]
        info['regler'] = sorted(set(info['regler']))
        recept['tagningar'][sid] = info

    B['objekt'] = list(obj_by_id.values())
    recept['borttagna_objekt'] = borttagna
    recept['objekt_harledd_mall'] = [o['id'] for o in B['objekt'] if o.get('tilltro') == 'harledd_mall']
    recept['sek'] = round(time.perf_counter() - t0, 2)
    OUT.mkdir(exist_ok=True)
    (OUT / 'paket_B.json').write_text(json.dumps(B, ensure_ascii=False, default=_np), encoding='utf-8')
    recept['b_paket_sha256'] = sha(OUT / 'paket_B.json')
    (OUT / 'recept_B.json').write_text(json.dumps(recept, ensure_ascii=False, indent=1, default=_np), encoding='utf-8')
    print(json.dumps(recept, ensure_ascii=False, indent=1, default=_np)[:6000])


def _overlap(A, sid, p, q):
    """Två spår i samma tagning är dubbletter om deras bålar ligger inom 0,6 m i A."""
    _, X = led_rutor(A, p, sid); _, Y = led_rutor(A, q, sid)
    if X is None or Y is None:
        return False
    i = A['leder'].index('c_spine2')
    return float(np.median(np.linalg.norm(X[:, i] - Y[:, i], axis=1))) < 0.6


if __name__ == '__main__':
    main()
