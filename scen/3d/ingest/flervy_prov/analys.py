"""Uppdrag 0006: analys av vggt_resultat.pkl: FOV per tagning, relativ pose per par, stabilitet mellan bildurval, skala, plan ur punktmängden, topdown-bild.
Körs (från scen/): .venv/Scripts/python.exe -B 3d/ingest/flervy_prov/analys.py   Skriver analys.json, analys.md och bilder/topdown_*.png"""
import itertools, json, math, os, pickle, sys
import cv2, numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); ING = os.path.dirname(HERE); D3 = os.path.dirname(ING)
os.makedirs(f'{HERE}/bilder', exist_ok=True)
R = pickle.load(open(f'{HERE}/vggt_resultat.pkl', 'rb'))
for _r in R['resultat']:
    for _k in ('world_points', 'world_conf', 'depth', 'depth_conf'): _r[_k] = np.nan_to_num(_r[_k].astype(np.float32), nan=0., posinf=0., neginf=0.)
PLAN = json.load(open(f'{D3}/kontrakt/ut/b-tilltal-ravara_n06-fler/narvaro/plan.json', encoding='utf8'))
GRUPPER = {'b': [['S1', 'S2'], ['S3', 'S4'], ['S6', 'S7'], ['S8', 'S9', 'S10']], 'e': [['S1', 'S3']]}      # delar kameraplats enligt 0002 (SIFT)
PLANKAM = {}
for s in PLAN['scener']:
    u0, u1 = s['ut']; M = np.array(PLAN['renderkamera']['nycklar'][(u0 + u1 - 1) // 2]['matris']); PLANKAM[s['id'].upper()] = M[:3, 3]
ut = dict(korningar={}, fov={}, par={}, stabilitet={}, skala={}, plan={})


def pose(r):
    ex = r['extrinsic']; Rcw = ex[:, :3, :3]; t = ex[:, :3, 3]
    C = np.array([-Rcw[i].T @ t[i] for i in range(len(t))]); Rwc = np.array([Rcw[i].T for i in range(len(t))]); return C, Rwc


def vinkel(a, b):
    c = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12)); return math.degrees(math.acos(max(-1., min(1., c))))


for r in R['resultat']:
    klipp = r['namn'].split('_')[0]; sid = [i.split('_')[0] for i in r['ids']]; H0, W0 = r['orig_storlek']; S = 518. / max(H0, W0)
    fx = r['intrinsic'][:, 0, 0]; fy = r['intrinsic'][:, 1, 1]
    rad = {}
    for k, s in enumerate(sid):
        f0 = float(fy[k] / S)
        rad[s] = dict(fokal_orig_px=round(f0, 1), vfov_grader=round(math.degrees(2 * math.atan(518 / (2 * fy[k]))), 1), hfov_grader=round(math.degrees(2 * math.atan(W0 * S / (2 * fx[k]))), 1))
    ut['fov'][r['namn']] = rad
for klipp in ('b', 'e'):
    namn = sorted(n for n in ut['fov'] if n.startswith(klipp + '_')); tag = list(ut['fov'][namn[0]])
    ut['fov'][klipp] = {s: dict(fokal_median_px=round(float(np.median([ut['fov'][n][s]['fokal_orig_px'] for n in namn])), 1),
                                 fokal_per_urval=[ut['fov'][n][s]['fokal_orig_px'] for n in namn],
                                 vfov_median=round(float(np.median([ut['fov'][n][s]['vfov_grader'] for n in namn])), 1),
                                 spridning_urval_px=round(float(np.ptp([ut['fov'][n][s]['fokal_orig_px'] for n in namn])), 1)) for s in tag}
# --- relativ pose per par och stabilitet mellan bildurval ---
for klipp in ('b', 'e'):
    namn = sorted(n for n in ut['fov'] if n.startswith(klipp + '_') and len(n) > 2); res = [r for r in R['resultat'] if r['namn'] in namn]
    sid = [i.split('_')[0] for i in res[0]['ids']]; per_urval = []
    for r in res:
        C, Rwc = pose(r); D = np.linalg.norm(C[:, None] - C[None], axis=-1); sk = float(np.median(D[np.triu_indices(len(C), 1)])) + 1e-9; per_urval.append((C, Rwc, D / sk, sk))
    grupp = {frozenset(p) for g in GRUPPER[klipp] for p in itertools.combinations(g, 2)}
    for a, b in itertools.combinations(range(len(sid)), 2):
        d = [u[2][a, b] for u in per_urval]; rot = [math.degrees(math.acos(max(-1., min(1., (np.trace(u[1][a].T @ u[1][b]) - 1) / 2)))) for u in per_urval]
        rikt = [u[0][b] - u[0][a] for u in per_urval]; rikt_sprid = max(vinkel(x, y) for x, y in itertools.combinations(rikt, 2))
        ut['par'][f'{klipp}:{sid[a]}-{sid[b]}'] = dict(delar_plats_sift=frozenset([sid[a], sid[b]]) in grupp, norm_avstand=[round(float(x), 3) for x in d],
                                                    avstand_cv=round(float(np.std(d) / (np.mean(d) + 1e-9)), 2), rotation_grader=[round(x, 1) for x in rot],
                                                    riktning_spridning_grader=round(rikt_sprid, 1))
    ut['stabilitet'][klipp] = dict(median_avstand_cv=round(float(np.median([v['avstand_cv'] for k, v in ut['par'].items() if k.startswith(klipp + ':')])), 2))
# --- skala ur personens avstånd (läst: planens kamera till personplats), och diskhöjd ur planen i punktmängden (b, urval q50) ---
ank = {a['id']: np.array(a['pos_m'][:2]) for a in PLAN['plats'][0]['uppmatta_ankare']}; PERS = {'S1': 'A', 'S2': 'A', 'S3': 'B', 'S4': 'B'}
I = f'{ING}/ut/b-tilltal-ravara-tagningar'
for r in R['resultat']:
    if not r['namn'].startswith('b_'): continue
    sid = [i.split('_')[0] for i in r['ids']]; fr = [int(i.split('_')[1]) for i in r['ids']]; C, Rwc = pose(r); sk = {}
    for k, s in enumerate(sid):
        M = np.load(f'{I}/{s}/masker.npy', allow_pickle=True); m = cv2.resize(M[min(fr[k], len(M) - 1)].astype(np.uint8), (int(576 * 518 / 1024), 518), interpolation=cv2.INTER_NEAREST)
        full = np.zeros((518, 518), np.uint8); off = (518 - m.shape[1]) // 2; full[:, off:off + m.shape[1]] = m
        mm = cv2.resize(full, r['depth'].shape[1:][::-1], interpolation=cv2.INTER_NEAREST) > 0
        d = r['depth'][k].astype(float); dc = r['depth_conf'][k].astype(float); ok = mm & (dc >= np.percentile(dc, 30))
        if ok.sum() < 20: continue
        dm = float(np.median(d[ok])); pe = ank['staplats_' + PERS.get(s, 'C')]; c_plan = PLANKAM[s][:2]
        lasat = float(np.linalg.norm(pe - c_plan))
        sk[s] = dict(djup_modell=round(dm, 3), last_m=round(lasat, 2), meter_per_modellenhet=round(lasat / dm, 3))
    ut['skala'][r['namn']] = sk
for n, sk in ut['skala'].items():
    v = [x['meter_per_modellenhet'] for x in sk.values()]
    if v: ut['skala'][n]['_median_cv'] = dict(median=round(float(np.median(v)), 3), cv=round(float(np.std(v) / np.mean(v)), 2), antal=len(v))
# --- planer i punktmängden: golv och diskens ovansida som höjdtoppar i b_q50 för tagningar S6–S11 ---
r = next(x for x in R['resultat'] if x['namn'] == 'b_q50'); sid = [i.split('_')[0] for i in r['ids']]; C, Rwc = pose(r)
upp = -np.mean(Rwc[:, :, 1], axis=0); upp /= np.linalg.norm(upp); kam_h = C @ upp
sel = [k for k, s in enumerate(sid) if s in ('S6', 'S7', 'S8', 'S9', 'S10', 'S11')]
P = np.concatenate([r['world_points'][k].reshape(-1, 3).astype(float)[(r['world_conf'][k].reshape(-1) >= np.percentile(r['world_conf'][k], 50))] for k in sel])
h = P @ upp; lo, hi = np.percentile(h, [1, 99]); bins = np.linspace(lo, hi, 120); hist, kant = np.histogram(h, bins)
topp = [round(float((kant[i] + kant[i + 1]) / 2), 3) for i in np.argsort(hist)[::-1][:12]]
ut['plan'] = dict(kamerahojd_modell=[round(float(x), 3) for x in kam_h[sel]], histogramtoppar_hojd_modell=sorted(topp), upp_vektor=[round(float(x), 3) for x in upp],
                  anm='Höjder längs medelvärdet av kamerornas uppvektor i modellenheter; golv och disk ska synas som toppar under kamerahöjden.')
# --- topdown-bilder ---
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
for namn in ('b_q50', 'e_q50'):
    r = next(x for x in R['resultat'] if x['namn'] == namn); sid = [i.split('_')[0] for i in r['ids']]; C, Rwc = pose(r)
    up = -np.mean(Rwc[:, :, 1], axis=0); up /= np.linalg.norm(up); a1 = np.cross(up, [1, 0, 0]); a1 /= np.linalg.norm(a1); a2 = np.cross(up, a1)
    fig, ax = plt.subplots(figsize=(7, 7), dpi=110)
    for k in range(len(sid)):
        Pk = r['world_points'][k].reshape(-1, 3).astype(float); ck = r['world_conf'][k].reshape(-1); ok = ck >= np.percentile(ck, 60)
        ax.scatter((Pk[ok] @ a1)[::6], (Pk[ok] @ a2)[::6], s=1, alpha=.25)
    for k, s in enumerate(sid):
        c = (C[k] @ a1, C[k] @ a2); f = Rwc[k][:, 2]; fv = np.array([f @ a1, f @ a2]); fv /= np.linalg.norm(fv) + 1e-9
        ax.annotate(s, xy=(c[0] + .25 * fv[0] * np.ptp(C @ a1 + 1e-9), c[1] + .25 * fv[1] * np.ptp(C @ a1 + 1e-9)), xytext=c, arrowprops=dict(arrowstyle='-|>', color='k'), fontsize=8)
    ax.set_aspect('equal'); ax.set_title(f'{namn}: kameror (pilar) och punktmängd sedd uppifrån, modellenheter', fontsize=9); ax.grid(True, lw=.3)
    lim = np.percentile(np.abs(np.concatenate([C @ a1, C @ a2])), 100) * 3; ax.set_xlim(C[:, :] @ a1 - 0 if False else (np.min(C @ a1) - lim, np.max(C @ a1) + lim)); ax.set_ylim(np.min(C @ a2) - lim, np.max(C @ a2) + lim)
    fig.savefig(f'{HERE}/bilder/topdown_{namn}.png', bbox_inches='tight'); plt.close(fig)
json.dump(ut, open(f'{HERE}/analys.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1, default=float)
print('FOV b (median fokal px, vFOV, spridning mellan urval):')
for s, v in ut['fov']['b'].items(): print(' ', s, v['fokal_median_px'], v['vfov_median'], v['spridning_urval_px'])
print('FOV e:', {s: (v['fokal_median_px'], v['vfov_median'], v['spridning_urval_px']) for s, v in ut['fov']['e'].items()})
print('stabilitet', ut['stabilitet'])
for k, v in sorted(ut['par'].items(), key=lambda kv: kv[1]['norm_avstand'][1]):
    if v['delar_plats_sift'] or k.startswith('e:'): print(k, v)
print('skala', {n: sk.get('_median_cv') for n, sk in ut['skala'].items()})
print('plan', ut['plan'])
