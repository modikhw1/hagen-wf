"""0034, provet: "ge glassen med andra handen" som optimering över sekvensen (inte en förtränad kontroller).

  scen/.venv/Scripts/python.exe forvarld/kropp/prov_optimering.py <sekvens.npz> <ut.npz> [--matt <mått.json>]
Det här ÄR: en minimering per ruta, varmstartad från föregående ruta och utjämnad över tiden, i MHR:s globala pose (modellrummet),
med samma form som en kroppskontroller (mål, kontakter, stil). Det här är INTE: en inlärd prior, och ingen fysik.
Fria parametrar per ruta: bålens vridning och lutning åt sidan (rotation av hela överkroppen kring c_spine0), vänster överarm och underarm,
höger överarm och underarm (rotationer av underträden kring leden). Rotvektorer, nollställt = originalet.
Mål (GRANSSNITT.md):
  - vänster handled når originalets högra handled i skopa (28–66) och ge (90–146), med mjuk ramp på 8 rutor
  - höger handled går till originalets vänstra handled speglad över kroppens mittplan (vila), i samma fönster
Stil: kostnad för avvikelse från originalet (bålen dyrare än armen); armbågen får inte översträckas (vinkeln > 178 grader straffas).
Kontakter: fötterna rörs inte (roten och benen är orörda); skeden flyttas till vänster handled i planen.
Ut: ny sekvens (samma nycklar, bara pose ändrad) och mått: avstånd till målen, avvikelse från originalet, bålens vridning, tid.
"""
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.signal import savgol_filter
from scipy.spatial.transform import Rotation as Ro

ROOT = Path(__file__).resolve().parents[2]
N = json.loads((ROOT / 'scen/3d/ingest/mhr_ledernamn.json').read_text()); PAR = json.loads((ROOT / 'scen/3d/klipp2/sam3db/mhr_skelett.json').read_text())['parents']
ix = N.index
BARN = {i: [] for i in range(len(N))}
for i, p in enumerate(PAR):
    if p is not None and p >= 0: BARN[p].append(i)
def under(j):
    ut, st = [], [j]
    while st: k = st.pop(); ut.append(k); st += BARN[k]
    return ut
SPINE, LUP, LLOW, RUP, RLOW = ix('c_spine0'), ix('l_uparm'), ix('l_lowarm'), ix('r_uparm'), ix('r_lowarm')
U_SP, U_LUP, U_LLOW, U_RUP, U_RLOW = under(SPINE), under(LUP), under(LLOW), under(RUP), under(RLOW)
FONSTER = [(28, 66), (90, 146)]; RAMP = 8


def rotera(P, j, uj, rv):
    if not np.any(rv): return P
    R = Ro.from_rotvec(rv); c = P[j, :3].copy(); Q = P.copy()
    Q[uj, :3] = c + R.apply(P[uj, :3] - c); Q[uj, 3:7] = (R * Ro.from_quat(P[uj, 3:7])).as_quat(); return Q


def posa(P0, x):
    P = rotera(P0, SPINE, U_SP, x[0:3]); P = rotera(P, LUP, U_LUP, x[3:6]); P = rotera(P, LLOW, U_LLOW, x[6:9])
    P = rotera(P, RUP, U_RUP, x[9:12]); return rotera(P, RLOW, U_RLOW, x[12:15])


def vikt(f):
    w = 0.
    for a, b in FONSTER:
        if a <= f < b: w = 1.
        elif a - RAMP <= f < a: w = max(w, (f - a + RAMP) / RAMP)
        elif b <= f < b + RAMP: w = max(w, 1 - (f - b + 1) / RAMP)
    return w


def armbage(P, up, low, wr):
    u = P[low, :3] - P[up, :3]; v = P[wr, :3] - P[low, :3]
    return np.degrees(np.arccos(np.clip(-(u @ v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))


def main():
    src, ut = Path(sys.argv[1]), Path(sys.argv[2]); z = dict(np.load(src)); P = z['pose'].astype(float); n = len(P); t0 = time.time()
    X = np.zeros((n, 15)); x = np.zeros(15); mal_v, mal_h = [], []
    for f in range(n):
        p = P[f]; w = vikt(f)
        nv = (p[ix('l_upleg'), :3] - p[ix('r_upleg'), :3]); nv /= np.linalg.norm(nv); c = (p[ix('root'), :3] + p[ix('c_neck'), :3]) / 2
        tv = p[ix('r_wrist'), :3]                                   # vänster hand dit höger hand var
        lw = p[ix('l_wrist'), :3]; th = lw - 2 * ((lw - c) @ nv) * nv   # höger hand dit vänster hand var, speglad (vila)
        mal_v.append(tv); mal_h.append(th)
        if w == 0: X[f] = 0; continue
        def r(x):
            Q = posa(p, x)
            res = [w * (Q[ix('l_wrist'), :3] - tv) / 3., w * .5 * (Q[ix('r_wrist'), :3] - th) / 3.,   # cm -> skala ~ 3 cm
                   3. * x[0:3], .6 * x[3:9], .6 * x[9:15],
                   [max(0., armbage(Q, LUP, LLOW, ix('l_wrist')) - 178) * .5, max(0., armbage(Q, RUP, RLOW, ix('r_wrist')) - 178) * .5]]
            return np.concatenate([np.ravel(a) for a in res])
        x = least_squares(r, x, method='trf', max_nfev=60).x; X[f] = x
    for j in range(15): X[:, j] = savgol_filter(X[:, j], 11, 2)
    Pn = P.copy(); dv, dh, vrid, ab = [], [], [], []
    for f in range(n):
        Pn[f] = posa(P[f], X[f])
        if vikt(f) == 1:
            dv.append(np.linalg.norm(Pn[f, ix('l_wrist'), :3] - mal_v[f])); dh.append(np.linalg.norm(Pn[f, ix('r_wrist'), :3] - mal_h[f]))
            vrid.append(np.degrees(np.linalg.norm(X[f, 0:3]))); ab.append(armbage(Pn[f], LUP, LLOW, ix('l_wrist')))
    s = round(time.time() - t0, 2); z['pose'] = Pn.astype(z['pose'].dtype); np.savez(ut, **z)
    seg = lambda L, a, b: round(float(np.median([v for f, v in zip([f for f in range(n) if vikt(f) == 1], L) if a <= f < b])), 1)
    matt = dict(sekunder=s, rutor=n, vanster_hand_till_mal_cm=dict(skopa=seg(dv, 28, 66), ge=seg(dv, 90, 146)), hoger_hand_till_vila_cm=dict(skopa=seg(dh, 28, 66), ge=seg(dh, 90, 146)),
                bal_rotation_grader=dict(skopa=seg(vrid, 28, 66), ge=seg(vrid, 90, 146)), vanster_armbage_grader=dict(skopa=seg(ab, 28, 66), ge=seg(ab, 90, 146)),
                status='optimering per ruta, utjämnad; ingen inlärd prior')
    print(json.dumps(matt, ensure_ascii=False))
    if '--matt' in sys.argv: Path(sys.argv[sys.argv.index('--matt') + 1]).write_text(json.dumps(matt, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__': main()
