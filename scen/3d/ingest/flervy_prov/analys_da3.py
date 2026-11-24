"""Uppdrag 0011: analys av da3_resultat.pkl: fokal, kameragrupper, skala i meter, golv och diskyta (RANSAC, gravitation okänd), personplatser, topdown.
Körs (från scen/): .venv/Scripts/python.exe -B 3d/ingest/flervy_prov/analys_da3.py   Skriver analys_da3.json och bilder/da3_topdown_*.png"""
import itertools, json, math, os, pickle, sys
import cv2, numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); ING = os.path.dirname(HERE); D3 = os.path.dirname(ING)
R = pickle.load(open(f'{HERE}/da3_resultat.pkl', 'rb'))
I = {'b': f'{ING}/ut/b-tilltal-ravara-tagningar', 'e': f'{ING}/ut/e-dialog-guacamole-tagningar'}
GRUPPER = {'b': [['S1', 'S2'], ['S3', 'S4'], ['S6', 'S7'], ['S8', 'S9', 'S10']], 'e': [['S1', 'S3']]}
PERSONPLATS = {'b': {'S1': 'A', 'S2': 'A', 'S3': 'B', 'S4': 'B', **{f'S{i}': 'C' for i in range(5, 12)}}, 'e': {'S1': 'A', 'S2': 'B', 'S3': 'A', 'S4': 'B'}}
rng = np.random.default_rng(3)
ut = dict(fokal={}, par={}, skala={}, plan={}, personplatser={}, med_mask={})


def las_masker(klipp, sid, ruta, hw):
    M = np.load(f'{I[klipp]}/{sid}/masker.npy', allow_pickle=True); m = M[min(ruta, len(M) - 1)].astype(np.uint8)
    return cv2.resize(m, (hw[1], hw[0]), interpolation=cv2.INTER_NEAREST) > 0


def punkter(r, k, hw=None):
    """Världspunkter (m) för bild k: bakprojicera depth_z med kameramatrisen i bearbetad upplösning."""
    d = r['depth_z'][k].astype(np.float32); h, w = d.shape; K = r['intrinsic'][k]; u, v = np.meshgrid(np.arange(w), np.arange(h))
    X = np.stack([(u - K[0, 2]) / K[0, 0] * d, (v - K[1, 2]) / K[1, 1] * d, d], -1).reshape(-1, 3)
    Ecw = r['extrinsic_cw'][k]; Rcw, t = Ecw[:3, :3], Ecw[:3, 3]
    return (X - t) @ Rcw, d.reshape(-1)                                                       # världspunkt = Rcw^T (X - t)


def pose(r):
    E = r['extrinsic_cw']; Rcw = E[:, :3, :3]; t = E[:, :3, 3]; C = np.array([-Rcw[i].T @ t[i] for i in range(len(E))]); return C, np.array([Rcw[i].T for i in range(len(E))])


def ransac_plan(P, normal_nara=None, max_grad=25., tol=.03, iter=1500):
    best = None; n = len(P)
    for _ in range(iter):
        i = rng.choice(n, 3, replace=False); nv = np.cross(P[i[1]] - P[i[0]], P[i[2]] - P[i[0]]); l = np.linalg.norm(nv)
        if l < 1e-9: continue
        nv /= l
        if normal_nara is not None and math.degrees(math.acos(min(1., abs(float(nv @ normal_nara))))) > max_grad: continue
        dist = np.abs((P - P[i[0]]) @ nv); inl = dist < tol
        if best is None or inl.sum() > best[2].sum(): best = (nv, float(nv @ P[i[0]]), inl)
    if best is None: return None
    nv, d0, inl = best; return nv, d0, inl


for r in R['resultat']:
    klipp = r['namn'][0]; sid = [i.split('_')[0] for i in r['ids']]; H0, W0 = r['orig_storlek']; Hp, Wp = r['proc_storlek']
    ut['fokal'][r['namn']] = {s: dict(fokal_orig_px=round(float(r['intrinsic'][k][1, 1] * H0 / Hp), 1), vfov=round(math.degrees(2 * math.atan(Hp / (2 * r['intrinsic'][k][1, 1]))), 1)) for k, s in enumerate(sid)}
    C, Rwc = pose(r); D = np.linalg.norm(C[:, None] - C[None], axis=-1); grp = {frozenset(p) for g in GRUPPER[klipp] for p in itertools.combinations(g, 2)}
    for a, b in itertools.combinations(range(len(sid)), 2):
        rot = math.degrees(math.acos(max(-1., min(1., (np.trace(Rwc[a].T @ Rwc[b]) - 1) / 2))))
        ut['par'].setdefault(f'{klipp}:{sid[a]}-{sid[b]}', dict(delar_plats_sift=frozenset([sid[a], sid[b]]) in grp, per_korning={}))['per_korning'][r['namn']] = dict(avstand_m=round(float(D[a, b]), 3), rotation_grader=round(rot, 1))
    # --- golv och diskyta (RANSAC, gravitation ur kamerornas uppvektor som start) för b, tagningar S6–S11, och egna personplatser ---
    upp = -np.mean(Rwc[:, :, 1], axis=0); upp /= np.linalg.norm(upp)
    plan = {}
    if klipp == 'b':
        sel = [k for k, s in enumerate(sid) if s in ('S6', 'S7', 'S8', 'S9', 'S10', 'S11')]; allp = []
        for k in sel:
            P, d = punkter(r, k); ok = np.ones(len(P), bool)
            if not r['maskerad']:
                ok = ~las_masker(klipp, sid[k], int(r['ids'][k].split('_')[1]), r['depth_z'][k].shape).reshape(-1)           # personpunkter bort efteråt
            if r['conf'] is not None: ok &= r['conf'][k].reshape(-1) >= np.percentile(r['conf'][k], 30)
            allp.append(P[ok][::5])
        P = np.concatenate(allp)
        sub = P[rng.choice(len(P), min(len(P), 20000), replace=False)]
        golv = ransac_plan(sub, upp)
        if golv:
            nv, d0, inl = golv; rest = sub[~inl]
            disk = ransac_plan(rest, nv, max_grad=10., tol=.03) if len(rest) > 100 else None
            hj = lambda p: np.median(p @ nv) if len(p) else None
            plan = dict(golv_andel=round(float(inl.mean()), 3), golv_normal_mot_upp_grader=round(math.degrees(math.acos(min(1., abs(float(nv @ upp))))), 1))
            if disk:
                n2, e0, inl2 = disk; plan.update(disk_andel_av_rest=round(float(inl2.mean()), 3), vinkel_golv_disk_grader=round(math.degrees(math.acos(min(1., abs(float(nv @ n2))))), 1),
                                                 hojdskillnad_m=round(float(abs(np.median(rest[inl2] @ nv) - np.median(sub[inl] @ nv))), 3))
        ut['plan'][r['namn']] = plan
    # --- personplatser: personpunkter (kroppsmask) mot gemensam horisontell plan ---
    if not r['maskerad']:
        plats = {}
        e1 = np.cross(upp, [0, 0, 1.] if abs(upp[2]) < .9 else [1., 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(upp, e1)
        for k, s in enumerate(sid):
            P, d = punkter(r, k); m = las_masker(klipp, s, int(r['ids'][k].split('_')[1]), r['depth_z'][k].shape).reshape(-1)
            if m.sum() < 50: continue
            pc = np.median(P[m], axis=0); plats[s] = [round(float(pc @ e1), 3), round(float(pc @ e2), 3)]
        ut['personplatser'][r['namn']] = plats
json.dump(ut, open(f'{HERE}/analys_da3.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1, default=float)
print('fokal b (med personer, median över q):')
for s in [f'S{i}' for i in range(1, 12)]:
    v = [ut['fokal'][n][s]['fokal_orig_px'] for n in ut['fokal'] if n.startswith('b_') and n.endswith('_med')]; w = [ut['fokal'][n][s]['fokal_orig_px'] for n in ut['fokal'] if n.startswith('b_') and n.endswith('_mask')]
    print(' ', s, round(float(np.median(v)), 1), v, '| maskerad', round(float(np.median(w)), 1))
print('fokal e:', {s: (round(float(np.median([ut['fokal'][n][s]['fokal_orig_px'] for n in ut['fokal'] if n.startswith('e_') and n.endswith('_med')])), 1)) for s in ['S1', 'S2', 'S3', 'S4']})
print('skala (DA3 metrisk) per körning:', {r['namn']: round(r['skala'], 3) for r in R['resultat']})
print('plan:', json.dumps(ut['plan'], ensure_ascii=False))
for k, v in ut['par'].items():
    if v['delar_plats_sift']: print(k, {n: (x['avstand_m'], x['rotation_grader']) for n, x in v['per_korning'].items() if n.endswith('_med')})
print('personplatser q50 med:', ut['personplatser'].get('b_q50_med'))
