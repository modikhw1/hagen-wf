"""Del 1 (metod_r25c_verklig.py):
Granskar Claudes R25c-prototyp (PnP + MoGe-djup) och påståendena C1 och C2 i MENING.md:205-206:
1. R25c på RIKTIGA rörliga tagningar (`gelato S1`, `asketch S1/S4/S5/S7`, `notan S7` + hold-out `b-tilltal`):
   - Mäter verklig 2D-reprojektionsdrift för fast förankrade bakgrundslandmärken genom R25c:s skattade (R_t, C_t).
   - Mäter den odokumenterade SKALBRISTEN i mening_r25.py:471 (`bal_ref = Rr[i] @ c_cam[i, bal] + Cr[i]`):
     `Cr` är i okalibrerad MoGe-skala medan `c_cam` är i R19-kalibrerad SAM/kappa-skala! Hur mycket vandrar
     den STILLASTÅENDE expediten A i `gelato S1` i 3D under R25c (`bal_span_3d_m`, `bal_netto_3d_m`)?
   - Kontrollerar R25c på 11 osedda tagningar i `b-tilltal` (där kameran rör sig och handhålls).
   - Sparar visuellt bevis `metod_r25c_gelato_s1.png` (R25c-återprojicerade bakgrundspunkter på verkliga rutor).
2. Kör Claudes EGNA C1-motprov (`MENING.md:205`) mot R25c:
   - (e) Digital zoom (brännvidd x1.0 -> x1.6 på stilla kamera): flaggar R25c felet eller hallucinerar den 1+ m framåtrörelse?
   - (f) Sidotruck (kameran åker 1.2 m i sidled med fast vinkel): hur bra är R25c vs R25b?
   - (g) Rörlig bakgrund / omaskad förbipasserande som täcker 35% av bakgrunden: kollapsar PnP eller ljuger den tyst?
3. Kör Claudes EGNA C2-motprov (`MENING.md:206`):
   - Patchar in `recept.kameror[].rotation[0..1]` (pitch och roll!) i en minneskopia av `scen_brygga.py` och
     mäter U (IoU, mittfel) och G7-oberoende (led_med) på `gelato S1` och alla 4 klippen!
   - Claude påstod: "Patcha in rotation[0..1] i en kopia och mät U igen. IoU ska stiga från 0.26. Om den inte gör det faller C2."
   - VI KÖR EXAKT DET MOTPROVET!

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\metod_r25c_verklig.py
"""
from __future__ import annotations

import glob
import json
import math
import pathlib
import sys
import tempfile
import types

import cv2
import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
R1 = ROT / "motpart/runda-1-claude"

for p in (str(R1), str(ROT / "forvarld_karna"), str(ROT / "byggsten/brygga")):
    if p not in sys.path:
        sys.path.insert(0, p)

import g7_oberoende as G7  # noqa: E402
import mening_gemensamt as MG  # noqa: E402
import mening_r25 as MR25  # noqa: E402
import mening_rubrik as MRUB  # noqa: E402
from schema import Observationer, Recept  # noqa: E402


def granska_r25c_verkliga() -> dict:
    """Mäter R25c:s reella 2D-bakgrundsreprojektion och 3D-skaldrift på gelato S1, asketch S4/S5, samt b-tilltal."""
    r1_r25 = json.loads((R1 / "mening_ut/mening_r25.json").read_text(encoding="utf-8"))["riktiga"]
    ut = {}

    # 1. Plocka ut nyckeltalen för de 6 R25-tagningarna ur r1_r25 + kör detaljerad reprojektionskontroll på gelato S1 och asketch S4/S5
    for klipp, sid, pid in (("gelato", "s1", "A"), ("asketch", "s1", "A"), ("asketch", "s4", "B"), ("asketch", "s5", "B"), ("notan", "s7", "B")):
        paket = MG.las_paket(klipp)
        rutor = MG.alla_bildrutor(paket, sid)
        M = MG.masker(paket, sid)
        rc = MR25.r25c_verklig(paket, sid, rutor, M)
        H0, W0 = rutor[0].shape[:2]
        f = rc["f_moge"]
        Rs, Cs = rc["R"], rc["C"]

        # Spåra oberoende hörn i bakgrunden (ruta 0 -> sista rutan) med framåt-bakåt-konsistenskoll
        # och mät hur bra R25c:s (R_t, C_t) reprojicerar 3D-punkter lyfta i ruta 0 över hela klippet!
        d0 = np.load(sorted(glob.glob(str(MG.ingest(paket) / sid.upper() / "rum/depth/*.npz")))[0])["depth"]
        skala = 360.0 / W0
        sm = [cv2.resize(r, (360, int(round(H0 * skala)))) for r in rutor]
        gra = [cv2.cvtColor(r, cv2.COLOR_BGR2GRAY) for r in sm]
        h, w = gra[0].shape
        m0 = np.ones((h, w), np.uint8)
        if M is not None:
            pm = cv2.resize(np.asarray(M[0]).astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
            m0[cv2.dilate(pm, np.ones((15, 15), np.uint8)) > 0] = 0
        m0[MR25.textmask(sm[0])] = 0
        p0 = cv2.goodFeaturesToTrack(gra[0], maxCorners=200, qualityLevel=0.02, minDistance=10, mask=m0)
        p0 = p0.reshape(-1, 2) if p0 is not None else np.zeros((0, 2))
        di = (p0 * [d0.shape[1] / w, d0.shape[0] / h]).astype(int)
        di[:, 0] = np.clip(di[:, 0], 0, d0.shape[1] - 1)
        di[:, 1] = np.clip(di[:, 1], 0, d0.shape[0] - 1)
        z0 = d0[di[:, 1], di[:, 0]]
        valid0 = np.isfinite(z0) & (z0 > 0.2) & (z0 < 15.0)
        p_cur = p0[valid0]
        P0_3d = MR25.lyft(p_cur / skala, z0[valid0], f, W0, H0)

        reproj_med_px = []
        n_kvar = []
        aktiv = np.ones(len(p_cur), bool)
        p_track = p_cur.copy()
        for t in range(1, len(gra)):
            idx = np.where(aktiv)[0]
            if len(idx) < 5:
                break
            p1, st, _ = cv2.calcOpticalFlowPyrLK(gra[t - 1], gra[t], p_track[idx].reshape(-1, 1, 2).astype(np.float32), None, winSize=(21, 21), maxLevel=3)
            pb, stb, _ = cv2.calcOpticalFlowPyrLK(gra[t], gra[t - 1], p1, None, winSize=(21, 21), maxLevel=3)
            fb_err = np.linalg.norm(pb.reshape(-1, 2) - p_track[idx], axis=-1)
            ok = (st.ravel() == 1) & (stb.ravel() == 1) & (fb_err < 1.0)
            p1 = p1.reshape(-1, 2)
            ok &= (p1[:, 0] >= 0) & (p1[:, 0] < w) & (p1[:, 1] >= 0) & (p1[:, 1] < h)
            aktiv[idx[~ok]] = False
            p_track[idx[ok]] = p1[ok]
            idx_ok = np.where(aktiv)[0]
            if len(idx_ok) >= 5:
                uv_pred, dep = MR25.projicera(P0_3d[idx_ok], Rs[t], Cs[t], f, W0, H0)
                obs_uv = p_track[idx_ok] / skala
                err = np.linalg.norm(uv_pred - obs_uv, axis=-1)
                reproj_med_px.append(float(np.median(err)))
                n_kvar.append(int(len(idx_ok)))

        # Jämför MoGe-fokal vs paket-fokal och MoGe-djup vid person vs SAM-djup (skalfaktor!)
        t_obj = MG.tagning(paket, sid)
        kam0 = MG.kamera(paket, sid, t_obj["ut"][0])
        f_paket = W0 * kam0[2] / paket["bild"]["sensor_mm"]
        sp = MG.spar_for(paket, pid, sid)
        U, X = MG.X_av(sp)
        L = MG.ix(paket)
        # Mät hur mycket R25c:s skattade kamera + okalibrerade skala får en STILLASTÅENDE persons bröst att röra sig
        C_arr = np.array(Cs)
        step_m = np.linalg.norm(np.diff(C_arr, axis=0), axis=-1)
        # Jämför MoGe-djup på personmask i ruta 0 mot SAM-bröstdjup i ruta 0
        sam_djup_0 = float(np.linalg.norm((X[0, L["c_spine2"]] - kam0[0])))
        moge_person_0 = None
        if M is not None:
            pm0 = cv2.resize(np.asarray(M[0]).astype(np.uint8), (d0.shape[1], d0.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
            vals = d0[pm0 & np.isfinite(d0) & (d0 > 0.2) & (d0 < 20)]
            if len(vals):
                moge_person_0 = float(np.median(vals))

        # Spara detaljerad reprojektionsbild för gelato S1
        if (klipp, sid) == ("gelato", "s1"):
            rita_gelato_r25c_analys(rutor, gra, M, Rs, Cs, f, W0, H0, d0, skala, r1_r25["gelato:s1:A"])

        ut[f"{klipp}:{sid}"] = dict(
            r1_r25c=r1_r25[f"{klipp}:{sid}:{pid}"]["R25c"],
            f_moge=round(f, 1),
            f_paket=round(f_paket, 1),
            moge_person_djup_f0_m=round(moge_person_0, 3) if moge_person_0 else None,
            sam_person_djup_f0_m=round(sam_djup_0, 3),
            skalkvot_sam_over_moge=round(sam_djup_0 / moge_person_0, 3) if moge_person_0 else None,
            kamera_max_hopp_m_per_ruta=round(float(step_m.max()), 3) if len(step_m) else 0.0,
            kamera_total_vaglangd_m=round(float(step_m.sum()), 3),
            ruta0_bakgrund_overlever_rutor=len(reproj_med_px),
            ruta0_reproj_median_px=round(float(np.median(reproj_med_px)), 1) if reproj_med_px else None,
            ruta0_reproj_p90_px=round(float(np.percentile(reproj_med_px, 90)), 1) if reproj_med_px else None,
            ruta0_reproj_max_px=round(float(np.max(reproj_med_px)), 1) if reproj_med_px else None,
        )

    # 2. Kör R25c på 4 tagningar ur hold-out b-tilltal (s1, s5, s8, s10)
    bt_paket = json.loads((HIT / "metod_btilltal_ut/paket.json").read_text(encoding="utf-8"))
    bt_r25c = {}
    for sid in ("s1", "s5", "s8", "s10"):
        rutor = MG.alla_bildrutor(bt_paket, sid)
        M = MG.masker(bt_paket, sid)
        rc = MR25.r25c_verklig(bt_paket, sid, rutor, M)
        C_arr = np.array(rc["C"])
        fwd = np.array([-R[:, 2] for R in rc["R"]])
        yaw = np.degrees(np.arctan2(-fwd[:, 0], -fwd[:, 2]))
        pitch = np.degrees(np.arcsin(np.clip(fwd[:, 1], -1, 1)))
        r25_beslut = [b for b in bt_paket["beslut"] if b["regel"] == "R25_separera_kamerarorelse" and b["tagning"] == sid]
        bt_r25c[sid] = dict(
            r25_fyrade=bool(r25_beslut),
            r25_drift_m=r25_beslut[0]["drift_m"] if r25_beslut else None,
            andel_pnp=round(rc["andel_pnp"], 3),
            kamera_max_m=round(float(np.max(np.linalg.norm(C_arr, axis=-1))), 3),
            kamera_max_hopp_m=round(float(np.max(np.linalg.norm(np.diff(C_arr, axis=0), axis=-1))), 3),
            yaw_span_deg=round(float(np.ptp(yaw)), 1),
            pitch_span_deg=round(float(np.ptp(pitch)), 1),
        )
    ut["btilltal_stickprov"] = bt_r25c
    return ut


def rita_gelato_r25c_analys(rutor, gra, M, Rs, Cs, f, W0, H0, d0, skala, r1_info):
    """Ritar 4 rutor ur gelato S1 med R25c:s skattade kamerabana och reprojicerade ruta-0-punkter vs verkliga LK-spår."""
    # Skapa en 4-panels översikt + ban-plot (Z och XY) för R25c på gelato S1
    C_arr = np.array(Cs)
    n = len(rutor)
    kol = []
    for t in (0, 50, 100, n - 1):
        im = rutor[t].copy()
        # Skriv R25c:s skattade kamera-läge och vinkel i bilden
        fwd = -Rs[t][:, 2]
        yw = math.degrees(math.atan2(-fwd[0], -fwd[2]))
        pt = math.degrees(math.asin(max(-1.0, min(1.0, fwd[1]))))
        c_dist = float(np.linalg.norm(C_arr[t]))
        cv2.putText(im, f"gelato S1 t={t}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
        cv2.putText(im, f"R25c |C|={c_dist:.2f}m yaw={yw:+.1f} pit={pt:+.1f}", (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (80, 255, 120), 3)
        cv2.putText(im, f"C=({C_arr[t,0]:+.2f},{C_arr[t,1]:+.2f},{C_arr[t,2]:+.2f})", (20, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (80, 255, 255), 2)
        kol.append(cv2.resize(im, (288, 512)))
    # Lägg till en 5:e panel med R25c:s bål-drift vs kameradrift
    info_im = np.full((512, 320, 3), 25, np.uint8)
    rader_txt = [
        "R25c pa gelato S1:",
        f"PnP-andel: {r1_info['R25c']['andel_rutor_med_pnp']}",
        f"Kamera max: {r1_info['R25c']['kamera_forflyttning_max_m']} m",
        f"Yaw span: {r1_info['R25c']['kamera_yaw_span_deg']} deg",
        f"Pitch span: {r1_info['R25c']['kamera_pitch_span_deg']} deg",
        f"BAL span 3D: {r1_info['R25c']['bal_span_3d_m']} m",
        f"BAL netto 3D: {r1_info['R25c']['bal_netto_3d_m']} m",
        "(Expediten star bakom disk!)",
    ]
    for i, txt in enumerate(rader_txt):
        cv2.putText(info_im, txt, (10, 45 + i * 38), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (230, 230, 230), 1)
    # Rita |C(t)| över tid nederst i panel 5
    xs = np.linspace(20, 300, len(C_arr)).astype(int)
    cd = np.linalg.norm(C_arr, axis=-1)
    ys = (490 - cd / max(cd.max(), 0.1) * 140).astype(int)
    for i in range(1, len(xs)):
        cv2.line(info_im, (xs[i - 1], ys[i - 1]), (xs[i], ys[i]), (80, 255, 80), 2)
    cv2.putText(info_im, "|C(t)| (m) over tid", (20, 345), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 255, 80), 1)
    kol.append(info_im)
    cv2.imwrite(str(HIT / "metod_r25c_gelato_s1.png"), np.hstack(kol))


def testa_c1_motprov() -> dict:
    """Kör Claudes egna C1-motprov (MENING.md:205) mot R25c: (e) digital zoom, (f) sidotruck, (g) rörlig bakgrund."""
    rng = np.random.default_rng(42)
    W, H = 576, 1024
    f0 = W / (2 * math.tan(math.radians(45) / 2))
    T = 60
    C0 = np.array([0.0, -3.0, 1.30])
    R0 = MR25.kam_R(0.0)
    vagg = np.column_stack([rng.uniform(-3, 3, 500), np.full(500, 3.0), rng.uniform(0.0, 2.8, 500)])
    golv = np.column_stack([rng.uniform(-3, 3, 300), rng.uniform(-1, 3, 300), np.zeros(300)])
    bord = dict(pos=[0.9, 0.9, 0.7], matt=[1.2, 0.6, 0.06], rot=[0, 0, 0])
    horn = MG.grindar.horn(bord)
    bg = np.vstack([vagg, golv, horn])
    tt = np.arange(T)

    # Synliga punkter i ruta 0
    uv0, d0 = MR25.projicera(bg, R0, C0, f0, W, H)
    ok0 = (d0 > 0.2) & (uv0[:, 0] > 30) & (uv0[:, 0] < W - 30) & (uv0[:, 1] > 30) & (uv0[:, 1] < H - 30)
    bg_ok = bg[ok0]
    P_ref = (bg_ok - C0) @ R0 * (1.0 + rng.normal(0, 0.03, ok0.sum()))[:, None]

    ut = {}

    # (e) Digital zoom 1.0x -> 1.6x, helt stilla kamera (sann kamera-förflyttning = 0.00 m!)
    inliers_e, C_est_e, rum_err_e = [], [], []
    for t in range(T):
        f_t = f0 * (1.0 + 0.6 * t / (T - 1))
        uv_t, _ = MR25.projicera(bg_ok, R0, C0, f_t, W, H)
        uv_t = uv_t + rng.normal(0, 0.5, uv_t.shape)
        res = MR25.pnp_pose(P_ref, uv_t, f0, W, H)  # R25c antar fast fokal f0
        if res is None:
            C_est_e.append(np.zeros(3)); inliers_e.append(0.0)
        else:
            Rt, Ct, inl = res
            C_est_e.append(Ct); inliers_e.append(inl)
            uv_h_true, _ = MR25.projicera(horn, R0, C0, f_t, W, H)
            uv_h_pred, _ = MR25.projicera(horn, R0 @ Rt, C0 + R0 @ Ct, f0, W, H)
            rum_err_e.append(float(np.median(np.linalg.norm(uv_h_pred - uv_h_true, axis=-1))))
    ut["e_digital_zoom_1.6x_stilla_kamera"] = dict(
        sann_kamera_forflyttning_m=0.0,
        r25c_hallucinerad_kamera_m=round(float(np.linalg.norm(C_est_e[-1])), 3),
        r25c_pnp_andel_ok=round(float(np.mean([i > 0 for i in inliers_e])), 3),
        r25c_inlier_andel_min=round(float(min(inliers_e)), 3),
        r25c_inlier_andel_sista=round(float(inliers_e[-1]), 3),
        flaggas_av_claudes_grind_pnp_under_09=bool(np.mean([i > 0 for i in inliers_e]) < 0.9),
        rum_2d_fel_max_px=round(max(rum_err_e), 1) if rum_err_e else None,
    )

    # (f) Sidotruck 1.2 m åt höger (fast kamerarotation)
    inliers_f, C_est_f, yaw_f, rum_err_f = [], [], [], []
    for t in range(T):
        C_true = C0 + np.array([1.2 * t / (T - 1), 0.0, 0.0])
        uv_t, _ = MR25.projicera(bg_ok, R0, C_true, f0, W, H)
        uv_t = uv_t + rng.normal(0, 0.5, uv_t.shape)
        res = MR25.pnp_pose(P_ref, uv_t, f0, W, H)
        Rt, Ct, inl = res
        C_est_f.append(R0 @ Ct); inliers_f.append(inl)
        R_w = R0 @ Rt
        fwd = -R_w[:, 2]
        yaw_f.append(-math.degrees(math.atan2(fwd[0], fwd[1])))
        uv_h_true, _ = MR25.projicera(horn, R0, C_true, f0, W, H)
        uv_h_pred, _ = MR25.projicera(horn, R_w, C0 + R0 @ Ct, f0, W, H)
        rum_err_f.append(float(np.median(np.linalg.norm(uv_h_pred - uv_h_true, axis=-1))))
    ut["f_sidotruck_1.2m"] = dict(
        sann_kamera_m=1.2,
        r25c_est_m=round(float(np.linalg.norm(C_est_f[-1])), 3),
        r25c_pos_fel_sista_m=round(float(np.linalg.norm(C_est_f[-1] - np.array([1.2, 0, 0]))), 3),
        r25c_falsk_yaw_deg=round(float(yaw_f[-1]), 2),
        r25c_inlier_min=round(float(min(inliers_f)), 3),
        rum_2d_fel_max_px=round(max(rum_err_f), 1),
    )

    # (g) Stilla kamera, men 45% av bakgrundspunkterna (t.ex. stor omaskad förbipasserande / fordon / skärm) rör sig 1.0 m i sidled
    #     + 30% variant för att se var RANSAC ger upp och om PnP-andel-grinden (<0.9) någonsin märker det!
    for andel_rorlig in (0.30, 0.45, 0.60):
        n_mov = int(len(bg_ok) * andel_rorlig)
        mov_ix = np.arange(n_mov)
        inliers_g, C_est_g, rum_err_g = [], [], []
        for t in range(T):
            bg_t = bg_ok.copy()
            bg_t[mov_ix, 0] += 1.0 * t / (T - 1)
            uv_t, _ = MR25.projicera(bg_t, R0, C0, f0, W, H)
            uv_t = uv_t + rng.normal(0, 0.5, uv_t.shape)
            res = MR25.pnp_pose(P_ref, uv_t, f0, W, H)
            if res is None:
                C_est_g.append(np.zeros(3)); inliers_g.append(0.0)
            else:
                Rt, Ct, inl = res
                C_est_g.append(R0 @ Ct); inliers_g.append(inl)
                uv_h_true, _ = MR25.projicera(horn, R0, C0, f0, W, H)
                uv_h_pred, _ = MR25.projicera(horn, R0 @ Rt, C0 + R0 @ Ct, f0, W, H)
                rum_err_g.append(float(np.median(np.linalg.norm(uv_h_pred - uv_h_true, axis=-1))))
        ut[f"g_rorlig_bakgrund_{int(andel_rorlig*100)}pct"] = dict(
            sann_kamera_m=0.0,
            r25c_hallucinerad_kamera_m=round(float(np.linalg.norm(C_est_g[-1])), 3),
            r25c_pnp_andel_ok=round(float(np.mean([i > 0 for i in inliers_g])), 3),
            r25c_inlier_sista=round(float(inliers_g[-1]), 3),
            flaggas_av_claudes_grind_pnp_under_09=bool(np.mean([i > 0 for i in inliers_g]) < 0.9),
            rum_2d_fel_max_px=round(max(rum_err_g), 1) if rum_err_g else None,
        )

    return ut


def testa_c2_pitch_patch() -> dict:
    """Kör Claudes eget motprov för C2 (MENING.md:206):
    'Patcha in rotation[0..1] i en kopia och mät U igen. IoU ska stiga från 0.26. Om den inte gör det faller C2.'
    """
    src = (ROT / "forvarld_karna/scen_brygga.py").read_text(encoding="utf-8")
    gammal = "        R_cam = _euler_xyz_till_mat(90.0, 0.0, cam_nod.rotation[2])"
    ny = "        R_cam = _euler_xyz_till_mat(cam_nod.rotation[0], cam_nod.rotation[1], cam_nod.rotation[2])  # C2-MOTPROV"
    assert src.count(gammal) == 1
    mod = types.ModuleType("scen_brygga_c2")
    mod.__file__ = str(ROT / "forvarld_karna/scen_brygga.py")
    exec(compile(src.replace(gammal, ny), "scen_brygga_c2", "exec"), mod.__dict__)
    mod.subprocess = types.SimpleNamespace(run=lambda *a, **k: None)

    ut = {}
    for klipp, ing_rel in G7.KLIPP.items():
        ut_k = ROT / "forvarld_karna/ut" / klipp
        obs_raw = json.loads((ut_k / "obs.json").read_text(encoding="utf-8"))
        rec_raw = json.loads((ut_k / "recept.json").read_text(encoding="utf-8"))
        obs = Observationer.model_validate(obs_raw)
        rec = Recept.model_validate(rec_raw)
        paket_orig = json.loads((ut_k / "paket.json").read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as td:
            pf = mod.kompilera_scenpaket(klipp, ROT / ing_rel, obs, rec, pathlib.Path(td) / klipp)
            paket_c2 = json.loads(pf.read_text(encoding="utf-8"))

        g7_orig = {(r["tagning"], r["person"]): r for r in G7.mat_paket(klipp, paket_orig, obs_raw)}
        g7_c2 = {(r["tagning"], r["person"]): r for r in G7.mat_paket(klipp, paket_c2, obs_raw)}

        rader = {}
        for t in paket_c2["tagningar"]:
            sid = t["id"]
            for p in t["personer"]:
                pid = p["id"]
                sp_o = MG.spar_for(paket_orig, pid, sid)
                sp_c = MG.spar_for(paket_c2, pid, sid)
                Uo, Xo = MG.X_av(sp_o)
                Uc, Xc = MG.X_av(sp_c)
                u_o = MRUB.utsnitt(paket_orig, Xo, Uo, sid, pid)
                u_c = MRUB.utsnitt(paket_c2, Xc, Uc, sid, pid)
                rader[f"{sid}:{pid}"] = dict(
                    U_iou_fore=u_o.get("iou_median"), U_iou_efter_pitch=u_c.get("iou_median"),
                    U_mittfel_fore=u_o.get("mittfel_bildhojd"), U_mittfel_efter_pitch=u_c.get("mittfel_bildhojd"),
                    U_poang_fore=u_o.get("poang"), U_poang_efter_pitch=u_c.get("poang"),
                    G7_led_med_fore=g7_orig[(sid, pid)]["led_med"], G7_led_med_efter_pitch=g7_c2[(sid, pid)]["led_med"],
                    kamera_z_fore=g7_orig[(sid, pid)]["kamera_z"], kamera_z_efter_pitch=g7_c2[(sid, pid)]["kamera_z"],
                )
        ut[klipp] = rader
    return ut


def main():
    print("=== 1. R25c PÅ RIKTIGA KLIPP (inkl. gelato S1 & b-tilltal) ===")
    v_res = granska_r25c_verkliga()
    print(json.dumps(v_res, ensure_ascii=False, indent=2))

    print("\n=== 2. C1-MOTPROV (zoom, sidotruck, rörlig bakgrund) ===")
    c1_res = testa_c1_motprov()
    print(json.dumps(c1_res, ensure_ascii=False, indent=2))

    print("\n=== 3. C2-MOTPROV (pitch/roll återinsatta i scen_brygga:254) ===")
    c2_res = testa_c2_pitch_patch()
    for klipp, d in c2_res.items():
        print(f"  [{klipp}]")
        for k, v in d.items():
            if klipp == "gelato" or abs((v["U_iou_efter_pitch"] or 0) - (v["U_iou_fore"] or 0)) > 0.03 or abs((v["G7_led_med_efter_pitch"] or 0) - (v["G7_led_med_fore"] or 0)) > 0.01:
                print(f"    {k}: U_iou {v['U_iou_fore']}->{v['U_iou_efter_pitch']} mittfel {v['U_mittfel_fore']}->{v['U_mittfel_efter_pitch']} "
                      f"G7_led {v['G7_led_med_fore']}->{v['G7_led_med_efter_pitch']} kam_z {v['kamera_z_fore']}->{v['kamera_z_efter_pitch']}")

    ut = dict(r25c_verkliga=v_res, c1_motprov=c1_res, c2_motprov=c2_res)
    (HIT / "metod_r25c_verklig.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nSparade:", HIT / "metod_r25c_verklig.json", "och", HIT / "metod_r25c_gelato_s1.png")


if __name__ == "__main__":
    main()
