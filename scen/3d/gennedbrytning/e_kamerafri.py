"""0021 punkt 1–2: kamerafri och förgrundsfri källa för gelato S1.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/e_kamerafri.py
1. Avbildning per ruta (likformig: skala och förskjutning, ingen vridning) som lägger hennes överkropp på samma plats och i samma storlek
   som i ruta 0. Skattad ur dagens 2D-leder (c_head, c_neck, l_uparm, r_uparm ur ingestens kropp/1, projicerade), minsta kvadrat per ruta,
   saknade rutor interpolerade, sedan utjämnad över tiden (Savitzky–Golay, 15 rutor, ordning 2) så att den inte för in eget skak.
   Sparas i kamerafri/avbildning.json som 2x3-matriser källa -> kamerafri ram, och inversen.
2. Bara hennes pixlar (ingestens personmask, 270x480 uppskalad och lätt mjukad i kanten) läggs på jämn grå duk i den kamerafria ramen.
   Disk, rum, text och kundens hand finns då inte i källan. Det som hamnar utanför originalets bild blir grått.
"""
import json
from pathlib import Path
import cv2, numpy as np
from scipy.signal import savgol_filter

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; S1 = ING / 'ut/kand-kennysgelato-tagningar/S1'
N = json.loads((ING / 'mhr_ledernamn.json').read_text()); LED = ['c_head', 'c_neck', 'l_uparm', 'r_uparm']
UT = HIT / 'kamerafri'; GRA = 200; W, H, R0 = 1080, 1920, 7


def punkter(i):
    f = S1 / f'kropp/1/{i:04d}.npz'
    if not f.exists(): return None
    z = np.load(f); k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); fl = float(z['focal_length'])
    return np.array([[fl * k[N.index(n), 0] / k[N.index(n), 2] + W / 2, fl * k[N.index(n), 1] / k[N.index(n), 2] + H / 2] for n in LED])


def likformig(P, Q):
    """skala s och förskjutning t så att s*P + t ≈ Q (minsta kvadrat)."""
    pm, qm = P.mean(0), Q.mean(0); s = float(((P - pm) * (Q - qm)).sum() / ((P - pm) ** 2).sum())
    return s, qm - s * pm


def main():
    UT.mkdir(exist_ok=True)
    cap = cv2.VideoCapture(str(HIT / 'luma-agaren/1_kalla_gelato_S1.mp4')); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(f)
    n = len(F); P0 = punkter(R0); S, T = np.full(n, np.nan), np.full((n, 2), np.nan)
    for i in range(n):
        P = punkter(i + R0)
        if P is not None: S[i], T[i] = likformig(P, P0)
    ok = ~np.isnan(S); x = np.arange(n)
    S = np.interp(x, x[ok], S[ok]); T = np.stack([np.interp(x, x[ok], T[ok, j]) for j in range(2)], 1)
    rå = dict(s=S.copy(), t=T.copy())
    # logaritmisk skala utjämnas; förskjutningen utjämnas
    S = np.exp(savgol_filter(np.log(S), 15, 2)); T = np.stack([savgol_filter(T[:, j], 15, 2) for j in range(2)], 1)
    M = np.load(S1 / 'masker.npy'); vw = cv2.VideoWriter(str(UT / 'kamerafri.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 29.97, (W, H))
    avb = []; bort = []; hopvaxt = []
    for i in range(n):
        A = np.array([[S[i], 0, T[i, 0]], [0, S[i], T[i, 1]]]); Ai = cv2.invertAffineTransform(A)
        avb.append(dict(ruta=i, ingestruta=i + R0, skala=round(float(S[i]), 5), forskjutning=[round(float(T[i, 0]), 2), round(float(T[i, 1]), 2)],
                        A=A.round(6).tolist(), invers=Ai.round(6).tolist(), lasta_leder=bool(ok[i])))
        # kundens hand kommer in från bildkanten: maskdelar som rör kanten tas bort, utom den största (hon själv)
        lo = M[min(i + R0, len(M) - 1)].astype(np.uint8); nk, lab, st, _ = cv2.connectedComponentsWithStats(lo)
        if nk > 2:
            stor = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); hm, wm = lo.shape
            for c in range(1, nk):
                x0, y0, ww, hh = st[c, :4]
                if c != stor and (x0 == 0 or y0 == 0 or x0 + ww >= wm or y0 + hh >= hm): lo[lab == c] = 0; bort.append(i)
        if nk > 1:
            st0 = st[1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))]
            if st0[1] + st0[3] >= lo.shape[0]: hopvaxt.append(i)
        m = cv2.resize(lo.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
        m = cv2.GaussianBlur(m, (9, 9), 0)[..., None]
        bild = (F[i] * m + GRA * (1 - m)).astype(np.uint8)
        vw.write(cv2.warpAffine(bild, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(GRA, GRA, GRA)))
    vw.release()
    jamn = float(np.abs(np.diff(np.log(rå['s']))).mean()); efter = float(np.abs(np.diff(np.log(S))).mean())
    (UT / 'avbildning.json').write_text(json.dumps(dict(metod=__doc__.split('\n')[3].strip(), leder=LED, ruta0_ingest=R0, rutor=avb,
                                                       skala_omfang=[round(float(S.min()), 3), round(float(S.max()), 3)],
                                                       skalskak_fore_efter_utjamning=[round(jamn, 5), round(efter, 5)],
                                                       kanthand_borttagen_rutor=sorted(set(bort)), storsta_delen_ror_nederkanten_rutor=sorted(set(hopvaxt))), ensure_ascii=False, indent=1), encoding='utf-8')
    # översikt: originalets rutor och den kamerafria källan
    c = cv2.VideoCapture(str(UT / 'kamerafri.mp4')); K = []
    while True:
        ok2, f = c.read()
        if not ok2: break
        K.append(f)
    rutor = [0, 30, 55, 80, 112, 146]
    cv2.imwrite(str(UT / 'oversikt.jpg'), np.hstack([np.vstack([cv2.resize(F[r], (180, 320)), cv2.resize(K[r], (180, 320))]) for r in rutor]))
    print('skala', round(float(S.min()), 3), '-', round(float(S.max()), 3), 'skak', round(jamn, 5), '->', round(efter, 5))


if __name__ == '__main__': main()
