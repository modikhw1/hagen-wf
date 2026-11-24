"""0027 punkt 2: rätta kroppens plats i världen. Fötterna står still; kameran tar upp originalets inåkning.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/r_rot.py <g_forvarld-variant> <samspel.json> [--fot-rutor 7 22]
Felet (r_fel.py): projektionen i originalets bild är nästan rätt, men planens kamera står still med fast lins, så originalets inåkning
(avbildningens skala 1,0 -> 0,53) tas upp av att kroppen färdas mot kameran (fötterna glider 1,8 m). Rättningen vänder på det:
1. Kroppen flyttas som helhet per ruta (bara förskjutning, form och ledvinklar orörda) så att fotledernas mitt står still i världen:
   på medianen av rutorna --fot-rutor (början, där avbildningens skala är cirka 1) i golvplanet, och på 0,065 m över golvet.
   I sekvensen: cam_t += Rw^T G^T Mp^T Δ (mhr_rig placerar roten som T = Mp (G (C + Rw cam_t)), Mp = scenens till_plats). Ingen led ur någon annan läsning.
2. Renderkameran får ett läge per ruta (rotationen och linsen behålls): kamerans centrum löses så att kroppens överkroppsleder projiceras
   där dagens 2D-läsning av originalet har dem (bara leder inom bilden), utjämnat över tiden. Jämförs med en ren zoom (läget fast, linsen per ruta).
   Målen i bild är originalet där det syns; kroppen kommer ur genereringen.
Ut: g_forvarld/<variant>_rot/sekvens_1.npz, plan.json (renderkameran med nytt läge, rörelsen ur den nya sekvensen), rot.json (mått),
samspel/<namn>_rot.json (lederna i världen efter flytten, för s_scen).
"""
import copy, json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.signal import savgol_filter

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; from tagning import TAG as S1, DAG, HANDLING   # 0030
N = json.loads((ING / 'mhr_ledernamn.json').read_text()); Y_MAX = .30   # kameran stannar på kundens sida om diskens framkant (cirka 0,4 m efter flytten), antagen
OVER = ['c_head', 'c_neck', 'l_uparm', 'r_uparm', 'l_lowarm', 'r_lowarm', 'l_wrist', 'r_wrist']


def grav(V):
    u = V['upp'] / np.linalg.norm(V['upp']); z = np.array([0, 0, 1.]); v = np.cross(u, z); c = float(u @ z)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + vx + vx @ vx / (1 + c)


def mal2d(u):
    f = DAG / f'{u:04d}.npz'
    if not f.exists(): return None
    z = np.load(f); k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); fl = float(z['focal_length'])
    q = np.array([[fl * k[N.index(n), 0] / k[N.index(n), 2] + 540, fl * k[N.index(n), 1] / k[N.index(n), 2] + 960] for n in OVER])
    return q, (q[:, 0] >= 0) & (q[:, 0] < 1080) & (q[:, 1] >= 0) & (q[:, 1] < 1920)


def proj(P, R, C, lins):
    f = lins / 36 * 1080; x = (P - C) @ R; return np.c_[f * x[:, 0] / -x[:, 2] + 540, -f * x[:, 1] / -x[:, 2] + 960]


def main():
    v, spf = sys.argv[1], Path(sys.argv[2]); a0, a1 = (int(sys.argv[sys.argv.index('--fot-rutor') + 1]), int(sys.argv[sys.argv.index('--fot-rutor') + 2])) if '--fot-rutor' in sys.argv else (7, 22)
    G0 = HIT / 'g_forvarld' / v; ut = HIT / 'g_forvarld' / f'{v}_rot'; ut.mkdir(exist_ok=True)
    V = np.load(S1 / 'varld.npz'); Gm = grav(V); sp = json.loads(spf.read_text()); R = sp['rutor']; n = len(R)
    fot = np.array([(np.array(r['leder']['l_foot']['huvud']) + np.array(r['leder']['r_foot']['huvud'])) / 2 for r in R])
    mal = np.r_[np.median(fot[a0:a1 + 1, :2], 0), 0.065]; D = mal - fot                       # flytt per ruta i världen
    # 1. sekvensen
    S = dict(np.load(G0 / 'sekvens_1.npz')); Rw = V['kam_R'][:n]
    plan0 = json.loads((G0 / 'plan.json').read_text(encoding='utf-8')); s1 = next(x for x in plan0['scener'] if x['id'] == 's1')
    Mp = np.array(s1.get('till_plats') or np.eye(4))[:3, :3]                                    # platsens transform (0027: missad i första körningen)
    S['cam_t'] = S['cam_t'] + np.einsum('fji,fj->fi', Rw, (Gm.T @ Mp.T @ D.T).T)           # Rw^T G^T Mp^T Δ per ruta
    np.savez(ut / 'sekvens_1.npz', **S)
    # lederna i världen efter flytten
    sp2 = copy.deepcopy(sp)
    for r, d in zip(sp2['rutor'], D):
        for le in r['leder'].values(): le['huvud'] = list(np.array(le['huvud']) + d); le['svans'] = list(np.array(le['svans']) + d)
        if r.get('sked'): r['sked'] = list(np.array(r['sked']) + d)
    spf2 = spf.with_name(spf.stem + '_rot.json'); spf2.write_text(json.dumps(sp2))
    # 2. kameran per ruta
    plan = json.loads((G0 / 'plan.json').read_text(encoding='utf-8')); nk = plan['renderkamera']['nycklar']
    C0 = np.array(nk[0]['matris'])[:3, 3]; lins0 = nk[0]['lins_mm']; Cs, Ls, fel_fore, fel_dolly, fel_zoom = [], [], [], [], []
    for u in range(n):
        Rk = np.array(nk[u]['matris'])[:3, :3]; m = mal2d(u); P = np.array([sp2['rutor'][u]['leder'][j]['huvud'] for j in OVER])
        Pg = np.array([sp['rutor'][u]['leder'][j]['huvud'] for j in OVER])
        if m is None or m[1].sum() < 3: Cs.append(None); Ls.append(None); continue
        q, s = m
        # 0027: höjden låst (planens kamerahöjd) och kameran på kundens sida (y <= Y_MAX); fritt i golvplanet och i linsen.
        # Fri 3D-förflyttning sänkte kameran till diskens höjd, vilket projicerar rätt men ställer kameran i möbeln.
        r_d = lambda x: np.r_[(proj(P[s], Rk, np.r_[x[:2], C0[2]], x[2]) - q[s]).ravel(), 3 * (x[2] - lins0) / lins0]
        x = least_squares(r_d, [C0[0], C0[1], lins0], bounds=([-3, -4, 15], [3, Y_MAX, 250]), loss='soft_l1', f_scale=20).x; Cs.append(np.r_[x[:2], C0[2], x[2]])
        r_z = lambda p: (proj(P[s], Rk, C0, p[0]) - q[s]).ravel()
        lz = least_squares(r_z, [lins0], bounds=([10], [400])).x[0]; Ls.append(lz)
        md = lambda x: float(np.median(np.linalg.norm(x.reshape(-1, 2), axis=1)) / 1920 * 1000)
        fel_fore.append((u, md((proj(Pg[s], Rk, C0, lins0) - q[s]).ravel()))); fel_dolly.append((u, md(r_d(x)[:-1]))); fel_zoom.append((u, md(r_z([lz]))))
    ok = np.array([c is not None for c in Cs]); idx = np.nonzero(ok)[0]; Cm = np.array([c for c in Cs if c is not None])
    full = np.stack([np.interp(np.arange(n), idx, Cm[:, j]) for j in range(4)], 1); full = np.stack([savgol_filter(full[:, j], 31, 2) for j in range(4)], 1)   # x, y, z, lins; 31 rutor (15 gav en skakig väg)
    for u in range(n):
        M = np.array(nk[u]['matris']); M[:3, 3] = full[u, :3]; nk[u]['matris'] = M.tolist(); nk[u]['lins_mm'] = float(full[u, 3])
    fel_utj = []
    for u in range(n):
        m = mal2d(u)
        if m is None or m[1].sum() < 3: continue
        q, s = m; Rk = np.array(nk[u]['matris'])[:3, :3]; P = np.array([sp2['rutor'][u]['leder'][j]['huvud'] for j in OVER])
        fel_utj.append((u, float(np.median(np.linalg.norm(proj(P[s], Rk, full[u, :3], full[u, 3]) - q[s], axis=1)) / 1920 * 1000)))
    sc = next(x for x in plan['scener'] if x['id'] == 's1')
    for pm in sc['personer']: pm['rorelse'] = str(ut / 'sekvens_1.npz')
    plan.setdefault('beslut', []).append('0027: fötterna låsta i världen (kroppen flyttad som helhet), renderkameran med läge per ruta löst mot originalets synliga överkropp (gennedbrytning/r_rot.py).')
    (ut / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
    seg = {s['id']: s['rutor_plan'] for s in json.loads(HANDLING.read_text(encoding='utf-8'))['segment']}
    def med(lst, a, b): x = [e for u, e in lst if a <= u <= b]; return round(float(np.median(x)), 1) if x else None
    vag = np.linalg.norm(np.diff(full[:, :3], axis=0), axis=1).sum()
    res = dict(variant=v, fotternas_mal=mal.round(3).tolist(), kroppens_flytt_m=dict(max=round(float(np.linalg.norm(D, axis=1).max()), 3), median=round(float(np.median(np.linalg.norm(D, axis=1))), 3)),
               kamera=dict(vag_m=round(float(vag), 3), start=full[a0].round(3).tolist(), narmast_kroppen=full[int(np.argmin(np.linalg.norm(full[:, :2] - mal[:2], axis=1)))].round(3).tolist(), lins_mm=[round(float(full[:, 3].min()), 1), round(float(full[:, 3].max()), 1)],
                           zoom_modell_lins_mm=dict(min=round(float(min(l for l in Ls if l)), 1), max=round(float(max(l for l in Ls if l)), 1))),
               projektionsfel_promille={sid: dict(fore=med(fel_fore, *seg[sid]), dolly=med(fel_dolly, *seg[sid]), zoom=med(fel_zoom, *seg[sid]), dolly_utjamnad=med(fel_utj, *seg[sid])) for sid in seg},
               hela=dict(fore=med(fel_fore, 0, 200), dolly=med(fel_dolly, 0, 200), zoom=med(fel_zoom, 0, 200), dolly_utjamnad=med(fel_utj, 0, 200)))
    (ut / 'rot.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__': main()
