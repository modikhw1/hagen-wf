"""0036: motion matching mot liggarens mål, ur rörelsebanken v0, plus en kort IK som landar handen.

  scen/.venv/Scripts/python.exe forvarld/kropp/matcha.py <sekvens.npz> <ut.npz> [--matt <fil>]
Fråga (GRANSSNITT.md, "andra handen"): fönster skopa (källrutor 28–66, ram skopa) och ge (90–146, ram rakna_fram eller ge), aktiv sida
vänster, mål = originalets högra handled ruta för ruta (där tråget och kundens hand nåddes).
1. Bas: tagningen speglad som helhet (en vänsterhänt människa gör samma sak), samma spegling som banken (bank_bygg.spegla).
2. Kandidater per fönster: bankens poster med rätt ram och sida vänster. Varje kandidat samplas om till fönstrets längd och ställs på
   plats: roten läggs på basens rot, och kroppen vrids kring lodaxeln (uppåt ur varld.npz) med den vinkel som minimerar handledens avstånd
   till målet. Poäng = medelavståndet efter vridningen. Bästa kandidaten väljs.
3. Sammanfogning: kandidaten ersätter basen i fönstret; vridningen tonas in och ut över 8 rutor.
4. Landning: en kort minimering per ruta (bål, vänster överarm och underarm, som 0034) med hög kostnad för avvikelse, så att bara de
   sista centimetrarna tas av IK.
Ut: sekvensen och mått (som 0034) plus vald kandidat och poäng per fönster.
"""
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.signal import savgol_filter
from scipy.spatial.transform import Rotation as Ro
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bank_bygg as B
import prov_optimering as O

ROOT = Path(__file__).resolve().parents[2]; BANK = Path(__file__).resolve().parent / 'bank/v0'; ix = B.ix
FONSTER = [('skopa', (28, 66), {'skopa'}), ('ge', (90, 146), {'rakna_fram', 'ge'})]; RAMP = 8; F = B.F


def vrid(P, vinkel, axel, c):
    R = Ro.from_rotvec(axel * vinkel); Q = P.copy(); Q[:, :3] = c + R.apply(P[:, :3] - c); Q[:, 3:7] = (R * Ro.from_quat(P[:, 3:7])).as_quat(); return Q


def main():
    src, ut = Path(sys.argv[1]), Path(sys.argv[2]); t0 = time.time()
    z = dict(np.load(src)); P = z['pose'].astype(float); n = len(P); D = B.D_led(z['rest'])
    V = np.load(ROOT / 'scen/3d/ingest/ut/kand-kennysgelato-tagningar/S1/varld.npz')
    up = np.array([F.T @ V['kam_R'][f].T @ (V['upp'] / np.linalg.norm(V['upp'])) for f in range(n)])
    mal = P[:, ix('r_wrist'), :3].copy()                       # originalets högra handled
    bas = B.spegla(P, D)                                        # 1. hela tagningen speglad
    poster = [json.loads(l) for l in open(BANK / 'poster.jsonl', encoding='utf-8')]
    ut_P = bas.copy(); vinkel = np.zeros(n); val = {}
    for namn, (a, b), ramar in FONSTER:
        kand = [p for p in poster if p['ram'] in ramar and p['kroppsdel_sida'] == 'vanster']
        bast = None
        for p in kand:
            C = np.load(BANK / p['fil'])['pose'].astype(float); m = len(C); idx = np.round(np.linspace(0, m - 1, b - a)).astype(int); C = C[idx]
            C[:, :, :3] += (bas[a:b, ix('root'), :3] - C[:, ix('root'), :3])[:, None, :]      # roten på basens rot
            def kost(v):
                return np.mean([np.linalg.norm(vrid(C[i], v, up[a + i], C[i, ix('root'), :3])[ix('l_wrist'), :3] - mal[a + i]) for i in range(0, b - a, 3)])
            vs = np.radians(np.arange(-60, 61, 5)); k = [kost(v) for v in vs]; v = vs[int(np.argmin(k))]
            if bast is None or min(k) < bast[0]: bast = (min(k), p['id'], C, v)
        poang, pid, C, v = bast; val[namn] = dict(kandidat=pid, kandidater=len(kand), medelavstand_cm=round(float(poang), 1), vridning_grader=round(float(np.degrees(v)), 1))
        ut_P[a:b] = C; vinkel[a:b] = v
        for i in range(1, RAMP + 1):
            if a - i >= 0: vinkel[a - i] = max(vinkel[a - i], v * (1 - i / (RAMP + 1))) if v > 0 else min(vinkel[a - i], v * (1 - i / (RAMP + 1)))
            if b - 1 + i < n: vinkel[b - 1 + i] = v * (1 - i / (RAMP + 1))
    for f in range(n):
        if vinkel[f]: ut_P[f] = vrid(ut_P[f], vinkel[f], up[f], ut_P[f, ix('root'), :3])
    # 4. landning: små ändringar
    X = np.zeros((n, 9)); x = np.zeros(9)
    for f in range(n):
        w = O.vikt(f)
        if w == 0: continue
        p = ut_P[f]
        def r(x):
            Q = O.posa(p, np.r_[x, np.zeros(6)])
            return np.concatenate([w * (Q[ix('l_wrist'), :3] - mal[f]) / 3., 8. * x[0:3], 2. * x[3:9]])
        x = least_squares(r, x, max_nfev=40).x; X[f] = x
    for j in range(9): X[:, j] = savgol_filter(X[:, j], 11, 2)
    Pn = ut_P.copy(); dv, vr, ab = [], [], []
    for f in range(n):
        Pn[f] = O.posa(ut_P[f], np.r_[X[f], np.zeros(6)])
        if O.vikt(f) == 1:
            dv.append((f, np.linalg.norm(Pn[f, ix('l_wrist'), :3] - mal[f]))); vr.append((f, np.degrees(abs(vinkel[f])) + np.degrees(np.linalg.norm(X[f, 0:3]))))
            ab.append((f, O.armbage(Pn[f], O.LUP, O.LLOW, ix('l_wrist'))))
    s = round(time.time() - t0, 2); z['pose'] = Pn.astype(z['pose'].dtype); np.savez(ut, **z)
    med = lambda L, a, b: round(float(np.median([v for f, v in L if a <= f < b])), 1)
    matt = dict(sekunder=s, val=val, vanster_hand_till_mal_cm=dict(skopa=med(dv, 28, 66), ge=med(dv, 90, 146)),
                kroppens_vridning_grader=dict(skopa=med(vr, 28, 66), ge=med(vr, 90, 146)), vanster_armbage_grader=dict(skopa=med(ab, 28, 66), ge=med(ab, 90, 146)),
                landning_IK_rotation_grader_median=round(float(np.degrees(np.median(np.linalg.norm(X[:, 3:9], axis=1)))), 1), status='motion matching ur bank v0 + kort IK')
    print(json.dumps(matt, ensure_ascii=False))
    if '--matt' in sys.argv: Path(sys.argv[sys.argv.index('--matt') + 1]).write_text(json.dumps(matt, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__': main()
