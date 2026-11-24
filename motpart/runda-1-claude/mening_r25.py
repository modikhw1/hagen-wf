"""A2: Vad gör R25_separera_kamerarorelse när en person faktiskt rör sig – och en prototyp till bättre separation.

Kör:  scen/.venv/Scripts/python.exe motpart/runda-1-claude/mening_r25.py

Del 1 (syntetiskt, facit känt): fyra scenarier genom exakt samma R25-kod som scen_brygga.py:380–390
        (kopierad nedan, med scen_brygga._mjuk_bana importerad) och genom prototypen R25b.
Del 2 (riktiga klipp): bakgrundsrörelse ur videorutorna (Lucas–Kanade på punkter utanför personmasken,
        4-DOF-likhet med RANSAC mellan på varandra följande rutor, ackumulerad) mot kroppens drift.

R25b (prototyp):
  1. A_t = likhetsavbildning (skala s, rotation, translation) för BAKGRUNDEN ruta 0 -> t.
  2. Kamerans rörelse tolkas som panorering/tiltning (bakgrundstranslation -> vinkel via fokal) +
     inåkning (bakgrundsskala -> framåtrörelse = Z_bg * (1 - 1/s), Z_bg = MoGe-medeldjup utanför personen).
  3. Kroppen behåller sin egen kameraramsbana; världsbanan = R_t * c_cam(t) + C_t.
  Antagande (deklarerat): ingen ren sidoförflyttning av kameran (truck). Det är ett mätbart antagande –
  parallax mellan person och bakgrund avslöjar när det bryts (se rapporten).
"""
from __future__ import annotations

import glob
import json
import math

import cv2
import numpy as np

import mening_gemensamt as G
import scen_brygga  # noqa: E402  (läses, ändras inte)

RNG = np.random.default_rng(7)


# ------------------------------------------------------------------ R25 exakt som i scen_brygga.py:380–390
def r25(X: np.ndarray, C_world: np.ndarray, sp0: int):
    backen_xy = X[:, sp0, :2]
    ankare_xy = np.median(backen_xy, axis=0)
    drift_span = float(np.linalg.norm(backen_xy.max(axis=0) - backen_xy.min(axis=0)))
    if drift_span > 0.18:
        delta_xy = scen_brygga._mjuk_bana(backen_xy - ankare_xy, fonster=9)
        delta_3d = np.column_stack([delta_xy, np.zeros(len(X))])
        return X - delta_3d[:, None, :], C_world[None, :] - delta_3d, drift_span, True
    return X.copy(), np.tile(C_world, (len(X), 1)), drift_span, False


# ------------------------------------------------------------------ geometri
def kam_R(yaw_deg: float, pitch_deg: float = 0.0) -> np.ndarray:
    """Kamerarotation (kolumner = kamerans x, y, z i världen). Blender: kameran tittar längs -z.
    yaw 0 = tittar längs +Y i världen (samma som scen_brygga Euler(90,0,rz))."""
    return G.euler_xyz(90.0 + pitch_deg, 0.0, yaw_deg)


def projicera(Xw: np.ndarray, R: np.ndarray, C: np.ndarray, f: float, W: int, H: int):
    c = (Xw - C) @ R
    d = -c[..., 2]
    uv = c[..., :2] / np.maximum(d[..., None], 1e-6) * np.array([f, -f]) + np.array([W / 2, H / 2])
    return uv, d


def likhet_kedja(punkter_per_ruta: list[np.ndarray]) -> list[np.ndarray]:
    """Ackumulerar 4-DOF-likheter mellan på varandra följande rutor (korresponderande punktuppsättningar)."""
    A = [np.eye(3)]
    for t in range(1, len(punkter_per_ruta)):
        p0, p1 = punkter_per_ruta[t - 1], punkter_per_ruta[t]
        M, inl = cv2.estimateAffinePartial2D(p0.astype(np.float32), p1.astype(np.float32), method=cv2.RANSAC,
                                             ransacReprojThreshold=2.0)
        M3 = np.eye(3)
        if M is not None:
            M3[:2] = M
        A.append(M3 @ A[-1])
    return A


def dela_upp(A: np.ndarray, W: int, H: int, f: float):
    """Bildmittens förflyttning (px), skala och rotation ur en likhet."""
    s = math.hypot(A[0, 0], A[1, 0])
    rot = math.degrees(math.atan2(A[1, 0], A[0, 0]))
    c = np.array([W / 2, H / 2, 1.0])
    c2 = A @ c
    return dict(s=s, rot=rot, tx=float(c2[0] - c[0]), ty=float(c2[1] - c[1]))


def r25b_kamera(A_lista, R0, C0, f, W, H, Z_bg):
    """Kamerabana ur bakgrundslikheterna: panorering/tiltning + inåkning (prototyp)."""
    Rs, Cs, info = [], [], []
    for A in A_lista:
        dd = dela_upp(A, W, H, f)
        # bakgrunden flyttas åt höger i bild (tx>0) när kameran panorerar åt vänster (yaw +)
        yaw = math.degrees(math.atan2(dd["tx"], f))
        pitch = math.degrees(math.atan2(dd["ty"], f))   # bakgrunden flyttas uppåt (ty<0) när kameran tiltar ned (pitch<0)
        fram = Z_bg * (1.0 - 1.0 / max(dd["s"], 1e-3))
        # rotera i kamerans egen ram: yaw kring kamerans y (upp, + = vänster), pitch kring kamerans x (+ = upp)
        R = R0 @ G.ry(yaw) @ G.rx(pitch)
        C = C0 + (-R[:, 2]) * fram
        Rs.append(R)
        Cs.append(C)
        info.append(dict(yaw=yaw, pitch=pitch, fram=fram, **dd))
    return Rs, Cs, info


# ------------------------------------------------------------------ R25c: 6-DOF kamera ur bakgrund + MoGe-djup (PnP)
FCV = np.diag([1.0, -1.0, -1.0])   # Blender-kameraram <-> OpenCV-kameraram


def pnp_pose(P_ref: np.ndarray, uv: np.ndarray, f: float, W: int, H: int):
    """Kamerapose (R_t, C_t) i referensramen (ruta 0:s Blender-kameraram) ur 3D-punkter + 2D-observationer."""
    K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1.0]])
    ok, rvec, tvec, inl = cv2.solvePnPRansac(P_ref.astype(np.float64), uv.astype(np.float64), K, None,
                                             reprojectionError=3.0, iterationsCount=200, flags=cv2.SOLVEPNP_EPNP)
    if not ok or inl is None or len(inl) < 8:
        return None
    ii = inl.ravel()
    ok, rvec, tvec = cv2.solvePnP(P_ref[ii].astype(np.float64), uv[ii].astype(np.float64), K, None, rvec, tvec,
                                  useExtrinsicGuess=True, flags=cv2.SOLVEPNP_ITERATIVE)
    Rcv, _ = cv2.Rodrigues(rvec)
    R_t = Rcv.T @ FCV
    C_t = -R_t @ FCV @ tvec.ravel()
    return R_t, C_t, len(ii) / len(P_ref)


def lyft(uv: np.ndarray, djup: np.ndarray, f: float, W: int, H: int) -> np.ndarray:
    """2D + djup (längs optiska axeln) -> Blender-kameraramens 3D (x höger, y upp, z bakåt)."""
    x = (uv[:, 0] - W / 2) / f * djup
    y = -(uv[:, 1] - H / 2) / f * djup
    return np.column_stack([x, y, -djup])


# ------------------------------------------------------------------ Del 1: syntetiska scenarier
def t1_mall() -> tuple[np.ndarray, list[str]]:
    """En verklig stående T1-pose (notan C, S4, första rutan), centrerad på bäckenet i XY."""
    p = G.las_paket("notan")
    sp = G.spar_for(p, "C", "s4")
    _, X = G.X_av(sp)
    L = G.ix(p)
    x = X[0].copy()
    x[:, :2] -= x[L["c_spine0"], :2]
    return x, p["leder"]


def syntet():
    W, H = 576, 1024
    f = W / (2 * math.tan(math.radians(45) / 2))
    mall, leder = t1_mall()
    L = {n: i for i, n in enumerate(leder)}
    sp0 = L["c_spine0"]
    T = 60
    C0 = np.array([0.0, -3.0, 1.30])
    # bakgrund: vägg y=+3, golv, samt ett bord (hörn används för "rummet i bild")
    vagg = np.column_stack([RNG.uniform(-3, 3, 500), np.full(500, 3.0), RNG.uniform(0.0, 2.8, 500)])
    golv = np.column_stack([RNG.uniform(-3, 3, 300), RNG.uniform(-1, 3, 300), np.zeros(300)])
    bord = dict(pos=[0.9, 0.9, 0.7], matt=[1.2, 0.6, 0.06], rot=[0, 0, 0])
    horn = G.grindar.horn(bord)
    bg = np.vstack([vagg, golv, horn])
    Z_bg_fallback = None

    scen = {}
    tt = np.arange(T)
    # (a) statisk kamera, person går 1.8 m i sidled
    pa = np.column_stack([-0.9 + 1.8 * tt / (T - 1), np.full(T, 0.4), np.zeros(T)])
    scen["a_gar_sidled_statisk_kamera"] = dict(p=pa, C=np.tile(C0, (T, 1)), yaw=np.zeros(T))
    # (b) inåkning 0.8 m mot stillastående person
    pb = np.tile([0.0, 0.4, 0.0], (T, 1))
    Cb = C0 + np.column_stack([np.zeros(T), 0.8 * tt / (T - 1), np.zeros(T)])
    scen["b_inakning_still_person"] = dict(p=pb, C=Cb, yaw=np.zeros(T))
    # (c) panorering som följer en gående person (kameran står still men vrids)
    yaw_c = -np.degrees(np.arctan2(pa[:, 0] - C0[0], pa[:, 1] - C0[1]))
    scen["c_panorering_foljer_gaende"] = dict(p=pa, C=np.tile(C0, (T, 1)), yaw=yaw_c)
    # (d) statisk kamera, person går 1.5 m rakt mot kameran (fram till disken)
    pd_ = np.column_stack([np.zeros(T), 1.6 - 1.5 * tt / (T - 1), np.zeros(T)])
    scen["d_gar_mot_kameran_statisk"] = dict(p=pd_, C=np.tile(C0, (T, 1)), yaw=np.zeros(T))

    ut = {}
    for namn, s in scen.items():
        # sanning
        Xs = np.array([mall + s["p"][t] for t in range(T)])
        Rs_true = [kam_R(s["yaw"][t]) for t in range(T)]
        # vad SAM 3D Body ger: kameraramens leder (+1 cm brus)
        c_cam = np.array([(Xs[t] - s["C"][t]) @ Rs_true[t] for t in range(T)]) + RNG.normal(0, 0.01, Xs.shape)
        # scen_brygga: lyft med den statiska receptkameran (position C0, yaw = första rutans)
        R0 = Rs_true[0]
        Xw = np.array([c_cam[t] @ R0.T + C0 for t in range(T)])
        X25, C25, drift, fyrade = r25(Xw, C0, sp0)
        # 2D-bevarande (det R25 lovar) – kroppen genom R25-kameran mot sanningen
        uv_sann = np.array([projicera(Xs[t], Rs_true[t], s["C"][t], f, W, H)[0] for t in range(T)])
        uv25 = np.array([projicera(X25[t], R0, C25[t], f, W, H)[0] for t in range(T)])
        # rummet: bordets hörn genom R25-kameran mot sanningen
        rum_sann = np.array([projicera(horn, Rs_true[t], s["C"][t], f, W, H)[0] for t in range(T)])
        rum25 = np.array([projicera(horn, R0, C25[t], f, W, H)[0] for t in range(T)])
        # R25b: bakgrundspunkter (utanför personens ruta) -> likheter -> kamera
        pkt = []
        for t in range(T):
            uvb, db = projicera(bg, Rs_true[t], s["C"][t], f, W, H)
            pkt.append(uvb + RNG.normal(0, 0.5, uvb.shape))
        pkt0 = np.array(pkt)
        # ta bort punkter som skyms av personens ruta i någon ruta (enkel mask)
        bx = np.array([[u[:, 0].min() - 30, u[:, 1].min() - 30, u[:, 0].max() + 30, u[:, 1].max() + 30] for u in uv_sann])
        ok = np.ones(len(bg), bool)
        for t in range(T):
            inne = (pkt0[t, :, 0] > bx[t, 0]) & (pkt0[t, :, 0] < bx[t, 2]) & (pkt0[t, :, 1] > bx[t, 1]) & (pkt0[t, :, 1] < bx[t, 3])
            ok &= ~inne
            ok &= (pkt0[t, :, 0] > 0) & (pkt0[t, :, 0] < W) & (pkt0[t, :, 1] > 0) & (pkt0[t, :, 1] < H)
        A = likhet_kedja([pkt0[t, ok] for t in range(T)])
        _, d0 = projicera(bg[ok], Rs_true[0], s["C"][0], f, W, H)
        Z_bg = float(np.median(d0))
        Rb, Cb_, info = r25b_kamera(A, R0, C0, f, W, H, Z_bg)
        Xb = np.array([c_cam[t] @ Rb[t].T + Cb_[t] for t in range(T)])
        uvb_kropp = np.array([projicera(Xb[t], Rb[t], Cb_[t], f, W, H)[0] for t in range(T)])
        rumb = np.array([projicera(horn, Rb[t], Cb_[t], f, W, H)[0] for t in range(T)])

        def sammanf(Xest, Cest, uv_k, uv_r):
            kropp_sann = Xs[-1, sp0, :2] - Xs[0, sp0, :2]
            kropp_est = Xest[-1, sp0, :2] - Xest[0, sp0, :2]
            kam_sann = s["C"][-1] - s["C"][0]
            kam_est = Cest[-1] - Cest[0]
            return dict(
                kropp_forflyttning_sann_m=round(float(np.linalg.norm(kropp_sann)), 3),
                kropp_forflyttning_est_m=round(float(np.linalg.norm(kropp_est)), 3),
                kropp_banfel_median_m=round(float(np.median(np.linalg.norm(Xest[:, sp0, :2] - Xs[:, sp0, :2] - (Xest[0, sp0, :2] - Xs[0, sp0, :2]), axis=-1))), 3),
                kamera_forflyttning_sann_m=round(float(np.linalg.norm(kam_sann)), 3),
                kamera_forflyttning_est_m=round(float(np.linalg.norm(kam_est)), 3),
                kropp_2d_fel_px_median=round(float(np.median(np.linalg.norm(uv_k - uv_sann, axis=-1))), 2),
                rum_2d_fel_px_sista_ruta=round(float(np.median(np.linalg.norm(uv_r[-1] - rum_sann[-1], axis=-1))), 1),
                rum_2d_fel_px_max=round(float(np.max(np.median(np.linalg.norm(uv_r - rum_sann, axis=-1), axis=1))), 1),
            )

        # R25c: bakgrundspunkter lyfts till 3D med (brusigt, 3 %) djup i ruta 0, PnP per ruta
        P_ref = (bg[ok] - C0) @ R0
        djup_brus = 1.0 + RNG.normal(0, 0.03, len(P_ref))
        P_ref = P_ref * djup_brus[:, None]
        Rc, Cc = [], []
        for t in range(T):
            res = pnp_pose(P_ref, pkt0[t, ok], f, W, H)
            R_t, C_t = (np.eye(3), np.zeros(3)) if res is None else res[:2]
            Rc.append(R0 @ R_t)
            Cc.append(C0 + R0 @ C_t)
        Xc = np.array([c_cam[t] @ Rc[t].T + Cc[t] for t in range(T)])
        uvc_kropp = np.array([projicera(Xc[t], Rc[t], Cc[t], f, W, H)[0] for t in range(T)])
        rumc = np.array([projicera(horn, Rc[t], Cc[t], f, W, H)[0] for t in range(T)])
        fram_c = -Rc[-1][:, 2]
        yaw_est = -math.degrees(math.atan2(fram_c[0], fram_c[1]))
        ut[namn] = dict(
            R25=dict(fyrade=fyrade, drift_m=round(drift, 3), **sammanf(X25, C25, uv25, rum25)),
            R25b=dict(Z_bg_m=round(Z_bg, 2), yaw_sista=round(info[-1]["yaw"], 2), skala_sista=round(info[-1]["s"], 3),
                      **sammanf(Xb, np.array(Cb_), uvb_kropp, rumb)),
            R25c=dict(yaw_sista=round(yaw_est, 2), **sammanf(Xc, np.array(Cc), uvc_kropp, rumc)),
            sann_yaw_sista=round(float(s["yaw"][-1]), 2),
        )
        if namn == "a_gar_sidled_statisk_kamera":
            np.savez(G.UT / "mening_r25_syntet_a.npz", Xs=Xs, X25=X25, C25=C25, Xb=Xb, Cb=np.array(Cb_), C0=C0, R0=R0, f=f)
            rita_syntet(namn, Xs, X25, C25, R0, s, Rs_true, horn, f, W, H, L)
    return ut


def rita_syntet(namn, Xs, X25, C25, R0, s, Rs_true, horn, f, W, H, L):
    """Bildbevis: sanningen vs R25 för scenario (a) i ruta 0, 30, 59 (2D, samma kamera som renderingen)."""
    kol = []
    for t in (0, 30, 59):
        for etikett, X, R, C in (("sanning", Xs[t], Rs_true[t], s["C"][t]), ("R25", X25[t], R0, C25[t])):
            img = np.full((H, W, 3), 40, np.uint8)
            uvh, dh = projicera(horn, R, C, f, W, H)
            from mening_rubrik import KANTER, BEN
            for i, j in KANTER:
                cv2.line(img, tuple(int(v) for v in uvh[i]), tuple(int(v) for v in uvh[j]), (40, 140, 255), 3)
            uv, _ = projicera(X, R, C, f, W, H)
            for a, b in BEN:
                cv2.line(img, tuple(int(v) for v in uv[L[a]]), tuple(int(v) for v in uv[L[b]]), (245, 139, 76), 4)
            # golvlinjer var 0.5 m för att visa rummets läge
            for y in np.arange(-1.0, 3.01, 0.5):
                p = np.array([[-3, y, 0], [3, y, 0]], float)
                uvp, dp = projicera(p, R, C, f, W, H)
                if (dp > 0).all():
                    cv2.line(img, tuple(int(v) for v in uvp[0]), tuple(int(v) for v in uvp[1]), (90, 90, 90), 1)
            cv2.putText(img, f"{etikett} t={t}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
            kol.append(cv2.resize(img, (288, 512)))
    cv2.imwrite(str(G.UT / "mening_r25_syntet_a.png"), np.hstack(kol))


# ------------------------------------------------------------------ Del 2: riktiga klipp
def textmask(fr: np.ndarray) -> np.ndarray:
    vit = fr.min(axis=2) > 225
    rod = (fr[..., 2] > 170) & (fr[..., 1] < 90) & (fr[..., 0] < 90)
    return cv2.dilate((vit | rod).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0


def bakgrundsrorelse(rutor: list[np.ndarray], masker: np.ndarray | None, skala_b: int = 288):
    """LK-spårning av bakgrundspunkter (utanför person- och textmask), 4-DOF RANSAC mellan rutor."""
    H0, W0 = rutor[0].shape[:2]
    k = skala_b / W0
    sm = [cv2.resize(r, (skala_b, int(round(H0 * k)))) for r in rutor]
    gra = [cv2.cvtColor(r, cv2.COLOR_BGR2GRAY) for r in sm]
    h, w = gra[0].shape
    A = [np.eye(3)]
    inl_andel, n_pkt = [], []
    for t in range(1, len(gra)):
        m = np.ones((h, w), np.uint8)
        if masker is not None and t - 1 < len(masker):
            pm = cv2.resize(np.asarray(masker[t - 1]).astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
            m[cv2.dilate(pm, np.ones((15, 15), np.uint8)) > 0] = 0
        m[textmask(sm[t - 1])] = 0
        p0 = cv2.goodFeaturesToTrack(gra[t - 1], maxCorners=400, qualityLevel=0.01, minDistance=6, mask=m)
        M3 = np.eye(3)
        if p0 is not None and len(p0) >= 12:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(gra[t - 1], gra[t], p0, None, winSize=(21, 21), maxLevel=3)
            ok = st.ravel() == 1
            if ok.sum() >= 12:
                M, inl = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.0)
                if M is not None:
                    M3[:2] = M
                    inl_andel.append(float(inl.mean()))
                    n_pkt.append(int(ok.sum()))
        A.append(M3 @ A[-1])
    # skala tillbaka till full upplösning
    S = np.diag([1 / k, 1 / k, 1.0])
    A_full = [S @ a @ np.linalg.inv(S) for a in A]
    return A_full, (float(np.median(inl_andel)) if inl_andel else 0.0), (int(np.median(n_pkt)) if n_pkt else 0)


def r25c_verklig(paket: dict, sid: str, rutor: list[np.ndarray], M, bredd_sp: int = 360):
    """6-DOF kamerabana ur riktiga rutor: LK-spår utanför person/text, 3D ur MoGe-djup (var 6:e ruta), PnP.
    Referensram = ruta 0:s kameraram (Blender-konvention). Returnerar listor R_t, C_t (None där PnP saknas)."""
    S_dir = G.ingest(paket) / sid.upper()
    dfiler = {int(pathlib_stem(p)): p for p in glob.glob(str(S_dir / "rum/depth/*.npz"))}
    if 0 not in dfiler:
        return None
    H0, W0 = rutor[0].shape[:2]
    k = bredd_sp / W0
    sm = [cv2.resize(r, (bredd_sp, int(round(H0 * k)))) for r in rutor]
    gra = [cv2.cvtColor(r, cv2.COLOR_BGR2GRAY) for r in sm]
    h, w = gra[0].shape
    q0 = np.load(dfiler[0])
    Kn = q0["intrinsics"]
    f = float(Kn[0, 0] * W0)  # MoGe-fokal i fullupplösning (samma fokal för lyft och PnP)

    def mask_for(t):
        m = np.ones((h, w), np.uint8)
        if M is not None and t < len(M):
            pm = cv2.resize(np.asarray(M[t]).astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
            m[cv2.dilate(pm, np.ones((15, 15), np.uint8)) > 0] = 0
        m[textmask(sm[t])] = 0
        return m

    def nya_punkter(t, R_t, C_t, befintliga):
        q = np.load(dfiler[t])
        D = q["depth"]
        m = mask_for(t)
        for p in befintliga:
            cv2.circle(m, (int(p[0]), int(p[1])), 6, 0, -1)
        p0 = cv2.goodFeaturesToTrack(gra[t], maxCorners=300, qualityLevel=0.01, minDistance=7, mask=m)
        if p0 is None:
            return np.zeros((0, 2)), np.zeros((0, 3))
        p0 = p0.reshape(-1, 2)
        di = (p0 * [D.shape[1] / w, D.shape[0] / h]).astype(int)
        di[:, 0] = np.clip(di[:, 0], 0, D.shape[1] - 1)
        di[:, 1] = np.clip(di[:, 1], 0, D.shape[0] - 1)
        z = D[di[:, 1], di[:, 0]]
        ok = np.isfinite(z) & (z > 0.2) & (z < 15)
        uv_full = p0[ok] / k
        b = lyft(uv_full, z[ok], f, W0, H0)
        return p0[ok], b @ R_t.T + C_t

    Rs, Cs = [np.eye(3)], [np.zeros(3)]
    pts, P = nya_punkter(0, np.eye(3), np.zeros(3), [])
    n_bra = 0
    for t in range(1, len(gra)):
        if len(pts):
            p1, st, _ = cv2.calcOpticalFlowPyrLK(gra[t - 1], gra[t], pts.reshape(-1, 1, 2).astype(np.float32), None,
                                                 winSize=(21, 21), maxLevel=3)
            ok = (st.ravel() == 1)
            p1 = p1.reshape(-1, 2)
            inne = (p1[:, 0] >= 0) & (p1[:, 0] < w) & (p1[:, 1] >= 0) & (p1[:, 1] < h)
            ok &= inne
            pts, P = p1[ok], P[ok]
        res = pnp_pose(P, pts / k, f, W0, H0) if len(pts) >= 12 else None
        if res is None:
            Rs.append(Rs[-1]); Cs.append(Cs[-1])
        else:
            Rs.append(res[0]); Cs.append(res[1]); n_bra += 1
        if t in dfiler and len(pts) < 150:
            np_, nP = nya_punkter(t, Rs[-1], Cs[-1], pts)
            if len(np_):
                pts = np.vstack([pts, np_]) if len(pts) else np_
                P = np.vstack([P, nP]) if len(P) else nP
    return dict(R=Rs, C=Cs, f_moge=f, andel_pnp=n_bra / max(1, len(gra) - 1))


def pathlib_stem(p):
    import pathlib
    return pathlib.Path(p).stem


def interp_kamera(paket, sid, U):
    t = G.tagning(paket, sid)
    ks = t["kamera"]["nycklar"]
    if t["kamera"]["statisk"] or len(ks) == 1:
        return np.tile(np.array(ks[0][1:4]), (len(U), 1))
    ku = np.array([k[0] for k in ks])
    kc = np.array([k[1:4] for k in ks])
    return np.column_stack([np.interp(U, ku, kc[:, j]) for j in range(3)])


def riktiga():
    ut = {}
    for klipp in G.KLIPP:
        paket = G.las_paket(klipp)
        W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
        L = G.ix(paket)
        r25_tagn = {b["tagning"]: b for b in paket["beslut"] if b["regel"] == "R25_separera_kamerarorelse"}
        for t in paket["tagningar"]:
            sid = t["id"]
            if not t["personer"]:
                continue
            pid = t["personer"][0]["id"]
            sp = G.spar_for(paket, pid, sid)
            U, X = G.X_av(sp)
            a0 = t["ut"][0]
            rutor = G.alla_bildrutor(paket, sid)
            M = G.masker(paket, sid)
            A, inl, npkt = bakgrundsrorelse(rutor, M)
            kam0 = G.kamera(paket, sid, U[0])
            R0 = kam0[1]
            f = W * kam0[2] / paket["bild"]["sensor_mm"]
            C_t = interp_kamera(paket, sid, U)
            C0 = np.median(C_t, axis=0)
            # kameraramens bål (oberoende av R25: X - C(t) är invariant under R25)
            bal = L["c_spine2"]
            c_cam = np.array([(X[i] - C_t[i]) @ R0 for i in range(len(U))])
            # bakgrundens medeldjup ur MoGe (ruta 0, utanför personen)
            dfil = sorted(glob.glob(str(G.ingest(paket) / sid.upper() / "rum/depth/*.npz")))
            Z_bg = None
            if dfil:
                q = np.load(dfil[0])
                D = q["depth"]
                if M is not None:
                    pm = cv2.resize(np.asarray(M[0]).astype(np.uint8), (D.shape[1], D.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
                    D = np.where(pm, np.nan, D)
                Z_bg = float(np.nanmedian(D[np.isfinite(D) & (D < 30)]))
            Z_bg = Z_bg or 2.5
            A_U = [A[min(u - a0, len(A) - 1)] for u in U]
            Rb, Cb, info = r25b_kamera(A_U, R0, C0, f, W, H, Z_bg)
            Xb_bal = np.array([Rb[i] @ c_cam[i, bal] + Cb[i] for i in range(len(U))])
            # person i bild (oberoende tracker) mot bakgrundens rörelse vid personens startpunkt
            sp_id = G.spar_id_for_person(paket, sid, pid)
            rr = G.detektorrutor(paket, sid, sp_id) if sp_id else {}
            ks = sorted(rr)
            pers_px = bg_px = None
            if len(ks) > 5:
                c0 = np.r_[(rr[ks[0]][:2] + rr[ks[0]][2:]) / 2, 1.0]
                cs = np.array([(rr[k][:2] + rr[k][2:]) / 2 for k in ks])
                bgs = np.array([(A[min(k, len(A) - 1)] @ np.linalg.inv(A[ks[0]]) @ c0)[:2] for k in ks])
                pers_px = float(np.max(np.linalg.norm(cs - cs[0], axis=-1)))
                bg_px = float(np.max(np.linalg.norm(bgs - cs[0], axis=-1)))
                resid_px = float(np.max(np.linalg.norm(cs - bgs, axis=-1)))
                h0 = rr[ks[0]][3] - rr[ks[0]][1]
                hs = np.array([rr[k][3] - rr[k][1] for k in ks])
                pers_skala = float(np.max(hs) / max(h0, 1) if np.max(hs) / max(h0, 1) > 1 else np.min(hs) / max(h0, 1))
            else:
                resid_px, pers_skala = None, None
            tx = [i["tx"] for i in info]
            ty = [i["ty"] for i in info]
            s_ = [i["s"] for i in info]
            bal_r25 = X[:, bal, :2]
            # R25c (PnP + MoGe-djup)
            rc = r25c_verklig(paket, sid, rutor, M)
            r25c = None
            Xc_bal = Cc_w = None
            if rc is not None:
                Rr = [rc["R"][min(u - a0, len(rc["R"]) - 1)] for u in U]
                Cr = [rc["C"][min(u - a0, len(rc["C"]) - 1)] for u in U]
                fwd = np.array([-R[:, 2] for R in Rr])
                yaw = np.degrees(np.arctan2(-fwd[:, 0], -fwd[:, 2]))
                pitch = np.degrees(np.arcsin(np.clip(fwd[:, 1], -1, 1)))
                bal_ref = np.array([Rr[i] @ c_cam[i, bal] + Cr[i] for i in range(len(U))])
                Xc_bal = bal_ref @ R0.T + C0
                Cc_w = np.array(Cr) @ R0.T + C0
                r25c = dict(
                    andel_rutor_med_pnp=round(rc["andel_pnp"], 2),
                    kamera_forflyttning_max_m=round(float(np.max(np.linalg.norm(np.array(Cr), axis=-1))), 3),
                    kamera_yaw_span_deg=round(float(np.ptp(yaw)), 1),
                    kamera_pitch_span_deg=round(float(np.ptp(pitch)), 1),
                    bal_span_3d_m=round(float(np.linalg.norm(np.ptp(bal_ref, axis=0))), 3),
                    bal_netto_3d_m=round(float(np.linalg.norm(bal_ref[-1] - bal_ref[0])), 3),
                )
            ut[f"{klipp}:{sid}:{pid}"] = dict(
                R25_fyrade=sid in r25_tagn, R25_drift_m=r25_tagn.get(sid, {}).get("drift_m"),
                bg_inlier_andel=round(inl, 2), bg_punkter=npkt,
                bg_tx_span_px=round(float(np.ptp(tx)), 1), bg_ty_span_px=round(float(np.ptp(ty)), 1),
                bg_skala_min_max=[round(float(min(s_)), 3), round(float(max(s_)), 3)],
                r25b_yaw_span_deg=round(float(np.ptp([i["yaw"] for i in info])), 1),
                r25b_pitch_span_deg=round(float(np.ptp([i["pitch"] for i in info])), 1),
                r25b_inakning_span_m=round(float(np.ptp([i["fram"] for i in info])), 2),
                Z_bg_m=round(Z_bg, 2),
                person_bild_drift_px=None if pers_px is None else round(pers_px, 1),
                bakgrund_vid_person_drift_px=None if bg_px is None else round(bg_px, 1),
                person_residual_px=None if resid_px is None else round(resid_px, 1),
                person_hojd_kvot=None if pers_skala is None else round(pers_skala, 2),
                bal_xy_span_paket_m=round(float(np.linalg.norm(np.ptp(bal_r25, axis=0))), 3),
                bal_xy_span_r25b_m=round(float(np.linalg.norm(np.ptp(Xb_bal[:, :2], axis=0))), 3),
                R25c=r25c,
                bildhojd=H,
            )
            if (klipp, sid) in (("gelato", "s1"), ("asketch", "s1"), ("notan", "s7"), ("asketch", "s7")) and Xc_bal is not None:
                rita_verklig(klipp, sid, rutor, A, info, U, a0, rr, ks, C_t, Cc_w, X, Xc_bal, bal)
    return ut


def rita_verklig(klipp, sid, rutor, A, info, U, a0, rr, ks, C_t, Cb, X, Xb_bal, bal):
    """Rutor med bakgrundens rörelse (gröna pilar från ruta 0) och personens ruta; plus banor ovanifrån."""
    n = len(rutor)
    val = [0, n // 3, 2 * n // 3, n - 1]
    H0, W0 = rutor[0].shape[:2]
    gx, gy = np.meshgrid(np.linspace(0.1, 0.9, 5) * W0, np.linspace(0.1, 0.9, 9) * H0)
    rut = np.column_stack([gx.ravel(), gy.ravel(), np.ones(gx.size)])
    kol = []
    for t in val:
        im = rutor[t].copy()
        p = (A[t] @ rut.T).T[:, :2]
        for a, b in zip(rut[:, :2], p):
            cv2.arrowedLine(im, tuple(int(v) for v in a), tuple(int(v) for v in b), (60, 255, 60), max(2, W0 // 200), tipLength=0.15)
        if t in rr:
            r = rr[t]
            cv2.rectangle(im, (int(r[0]), int(r[1])), (int(r[2]), int(r[3])), (255, 120, 60), max(2, W0 // 150))
        cv2.putText(im, f"{sid.upper()} t={t}", (20, int(H0 * 0.05)), cv2.FONT_HERSHEY_SIMPLEX, W0 / 600, (0, 255, 255), max(2, W0 // 300))
        kol.append(cv2.resize(im, (288, 512)))
    # ovanifrån: bålens bana i paketet (efter R25) vs R25b, och kamerorna
    top = np.full((512, 512, 3), 30, np.uint8)
    alla = np.vstack([X[:, bal, :2], Xb_bal[:, :2], C_t[:, :2], np.array(Cb)[:, :2]])
    lo, hi = alla.min(0) - 0.3, alla.max(0) + 0.3
    sk = 480 / max(hi - lo)

    def px(p):
        return (int(16 + (p[0] - lo[0]) * sk), int(496 - (p[1] - lo[1]) * sk))

    for bana, farg in ((X[:, bal, :2], (80, 80, 255)), (C_t[:, :2], (80, 80, 160)), (Xb_bal[:, :2], (80, 255, 80)), (np.array(Cb)[:, :2], (60, 160, 60))):
        for i in range(1, len(bana)):
            cv2.line(top, px(bana[i - 1]), px(bana[i]), farg, 2)
        cv2.circle(top, px(bana[0]), 5, farg, -1)
    cv2.putText(top, "rod: R25 bal/kamera", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 80, 255), 2)
    cv2.putText(top, "gron: R25c bal/kamera", (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 255, 80), 2)
    cv2.putText(top, "ovanifran, 1 m = %d px" % int(sk), (10, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1)
    kol.append(cv2.resize(top, (288, 288)).repeat(1, axis=0))
    top_r = np.full((512, 288, 3), 30, np.uint8)
    top_r[112:400] = cv2.resize(top, (288, 288))
    kol[-1] = top_r
    cv2.imwrite(str(G.UT / f"mening_r25_verklig_{klipp}_{sid}.png"), np.hstack(kol))


if __name__ == "__main__":
    s = syntet()
    print("=== Del 1: syntetiska scenarier (facit känt)")
    for k, v in s.items():
        print(k)
        print("   R25 :", json.dumps(v["R25"], ensure_ascii=False))
        print("   R25b:", json.dumps(v["R25b"], ensure_ascii=False), "sann yaw sista:", v["sann_yaw_sista"])
        print("   R25c:", json.dumps(v["R25c"], ensure_ascii=False))
    r = riktiga()
    print("=== Del 2: riktiga klipp")
    for k, v in r.items():
        print(k, json.dumps(v, ensure_ascii=False))
    G.spara_json("mening_r25.json", dict(syntet=s, riktiga=r))
