"""Kamerans 6-DOF-bana inom en tagning ur bakgrunden (ersätter R25, A2).

R25 (`forvarld_karna/scen_brygga.py:380–390`) flyttade all lågfrekvent bäckendrift > 0,18 m från kroppen till kameran,
så en person som lutar sig fram eller går blev en kamera som åker. Här mäts kameran i stället där den syns: i
bakgrunden. Punkter utanför personmasken spåras med Lucas–Kanade, lyfts till 3D med tagningens MoGe-djup (samma
fokal och kappa som resten av kedjan) och kamerans läge skattas per ruta med PnP + RANSAC. Kroppen behåller sin egen
rörelse: X(t) = C(t) + R(t) · c_kamera(t).

Prototypen kommer från runda 1 (`motpart/runda-1-claude/mening_r25.py`, R25c), här omskriven för kedjan.
Antaganden som redovisas i utdata: fast fokal (zoom ser ut som inåkning), statisk bakgrund, tillräckligt många punkter.
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

FCV = np.diag([1.0, -1.0, -1.0])  # Blenders kameraram <-> OpenCV
BREDD_SPAR = 360
STILLA_ROT_DEG = 1.0
STILLA_TRANS_M = 0.04


def _textmask(fr):
    vit = fr.min(axis=2) > 225
    rod = (fr[..., 2] > 170) & (fr[..., 1] < 90) & (fr[..., 0] < 90)
    return cv2.dilate((vit | rod).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0


def _lyft(uv, djup, f, W, H):
    x = (uv[:, 0] - W / 2) / f * djup
    y = -(uv[:, 1] - H / 2) / f * djup
    return np.column_stack([x, y, -djup])


def _pnp(P_ref, uv, f, W, H):
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


def _las_rutor(mp4: Path, N: int, W: int, H: int):
    cap = cv2.VideoCapture(str(mp4))
    ut = []
    for _ in range(N):
        ok, img = cap.read()
        if not ok or img is None:
            break
        ut.append(cv2.resize(img, (W, H)) if (img.shape[1] != W or img.shape[0] != H) else img)
    cap.release()
    return ut


def _rot_vinkel(R):
    return math.degrees(math.acos(float(np.clip((np.trace(R) - 1) / 2, -1, 1))))


def kamerabana(mapp: Path, mp4: Path, f_px: float, kappa: float, W: int, H: int, N: int, ref_ruta: int) -> dict:
    """Returnerar R_rel (N,3,3) och C_rel (N,3) relativt referensrutan (Blenders kameraram), plus mått och flaggor."""
    dfiler = {int(p.stem): p for p in (mapp / "rum/depth").glob("*.npz")}
    rutor = _las_rutor(mp4, N, W, H) if mp4.exists() else []
    if len(rutor) < 3 or 0 not in dfiler:
        return dict(statisk=True, orsak="för få rutor eller inget djup i ruta 0", andel_pnp=0.0, flaggor=["kamerabana_saknas"])
    M = np.load(mapp / "masker.npy") if (mapp / "masker.npy").exists() else None
    k = BREDD_SPAR / W
    sm = [cv2.resize(r, (BREDD_SPAR, int(round(H * k)))) for r in rutor]
    gra = [cv2.cvtColor(r, cv2.COLOR_BGR2GRAY) for r in sm]
    h, w = gra[0].shape

    def mask_for(t):
        m = np.ones((h, w), np.uint8)
        if M is not None and t < len(M):
            pm = cv2.resize(np.asarray(M[t]).astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
            m[cv2.dilate(pm, np.ones((15, 15), np.uint8)) > 0] = 0
        m[_textmask(sm[t])] = 0
        return m

    def nya_punkter(t, R_t, C_t, befintliga):
        D = np.load(dfiler[t])["depth"].astype(float) * kappa
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
        ok = np.isfinite(z) & (z > 0.2) & (z < 25)
        b = _lyft(p0[ok] / k, z[ok], f_px, W, H)
        return p0[ok], b @ R_t.T + C_t

    Rs, Cs, kval = [np.eye(3)], [np.zeros(3)], [1.0]
    pts, P = nya_punkter(0, np.eye(3), np.zeros(3), [])
    n_bra = 0
    for t in range(1, len(gra)):
        if len(pts):
            p1, st, _ = cv2.calcOpticalFlowPyrLK(gra[t - 1], gra[t], pts.reshape(-1, 1, 2).astype(np.float32), None,
                                                 winSize=(21, 21), maxLevel=3)
            ok = st.ravel() == 1
            p1 = p1.reshape(-1, 2)
            ok &= (p1[:, 0] >= 0) & (p1[:, 0] < w) & (p1[:, 1] >= 0) & (p1[:, 1] < h)
            if M is not None and t < len(M):
                pm = cv2.resize(np.asarray(M[t]).astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
                pi = p1.astype(int)
                pi[:, 0] = np.clip(pi[:, 0], 0, w - 1)
                pi[:, 1] = np.clip(pi[:, 1], 0, h - 1)
                ok &= pm[pi[:, 1], pi[:, 0]] == 0
            pts, P = p1[ok], P[ok]
        res = _pnp(P, pts / k, f_px, W, H) if len(pts) >= 12 else None
        if res is None:
            Rs.append(Rs[-1]); Cs.append(Cs[-1]); kval.append(0.0)
        else:
            Rs.append(res[0]); Cs.append(res[1]); kval.append(res[2]); n_bra += 1
        if t in dfiler and len(pts) < 150:
            np_, nP = nya_punkter(t, Rs[-1], Cs[-1], pts)
            if len(np_):
                pts = np.vstack([pts, np_]) if len(pts) else np_
                P = np.vstack([P, nP]) if len(P) else nP
    n = len(Rs)
    andel = n_bra / max(1, n - 1)
    # jämna banan (rotation via kvaternion-medel i fönster, läge via medel)
    from scipy.spatial.transform import Rotation as Rot
    rv = Rot.from_matrix(np.array(Rs)).as_rotvec()
    C = np.array(Cs)
    def jamna(a, f=5):
        ut = np.empty_like(a)
        for i in range(len(a)):
            lo, hi = max(0, i - f // 2), min(len(a), i + f // 2 + 1)
            ut[i] = a[lo:hi].mean(0)
        return ut
    Rj = Rot.from_rotvec(jamna(rv)).as_matrix()
    Cj = jamna(C)
    # fyll ut till N rutor (om videon var kortare)
    while len(Rj) < N:
        Rj = np.concatenate([Rj, Rj[-1:]]); Cj = np.concatenate([Cj, Cj[-1:]])
    r = min(ref_ruta, N - 1)
    Rr, Cr = Rj[r], Cj[r]
    R_rel = np.einsum("ij,njk->nik", Rr.T, Rj)
    C_rel = (Cj - Cr) @ Rr
    rot_span = max(_rot_vinkel(R_rel[i]) for i in range(N))
    trans_span = float(np.linalg.norm(C_rel.max(0) - C_rel.min(0)))
    flaggor = []
    if andel < 0.6:
        flaggor.append(f"pnp_andel_{andel:.2f}")
    statisk = rot_span < STILLA_ROT_DEG and trans_span < STILLA_TRANS_M
    if andel < 0.6:
        statisk = True
        flaggor.append("kamerabana_osaker_satt_statisk")
    framat = float(abs(C_rel[:, 2]).max())
    if not statisk and trans_span > 0.2 and framat > 0.8 * trans_span:
        flaggor.append("inakning_kan_vara_zoom")
    return dict(statisk=bool(statisk), R_rel=R_rel, C_rel=C_rel, andel_pnp=round(andel, 3), rot_span_deg=round(rot_span, 2),
                trans_span_m=round(trans_span, 3), flaggor=flaggor)
