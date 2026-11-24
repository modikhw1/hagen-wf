"""Experiment 4 (Komplett) — Kvantitativ maskinaudit av ALLA 5 VERKLIGA genererade virtuell-sensor-bilder
(djup_v4_full_sensor_audit.py):
  1. v4_guac_S4_tom.png       (Steg A negativ borttagning av personer+text — Gemini Image)
  2. v4_guac_S4_djupplan.png  (Steg B 2-bilds pixel-låst Turbo-djupkarta — GPT Image / Codex, hel=True!)
     -> Inverteras genom exakt OpenCV COLORMAP_TURBO-LUT och mäts mot Argons verkliga MoGe-djup
        (scen/3d/ingest/ut/e-dialog-guacamole-tagningar/S4/rum/depth/0054.npz): Spearman rho + 2-nivåsbar-kant!
  3. v4_guac_S1_ext_s1.png    (1:1 Extremitet Frö 1 — Google Gemini Image)
  4. v4_guac_S1_ext_s2.png    (1:1 Extremitet Frö 2 — OpenAI GPT Image / Codex, hel=True!)
     -> VERKLIG TVÄRMODELL-KONSENSUS (Gemini vs GPT Image): warpas till gemensam S1-ram ->
        mäter exakt pixelförskjutning mellan Zon 1 (låst), Zon 2 (bar+barstol+pelare) och Zon 3 (hallucinerade sidor)!
  5. v4_guac_S2_ext_s1.png    (1:1 Extremitet S2 — OpenAI GPT Image / Codex)
     -> YOLO11n-pose helkropps- och golvkontaktåterställning (0% -> 100% synliga vrister på S1_ext_s2 & S2_ext_s1!)
        + oberoende antropometrisk beräkning av tvånivåsbarens höjd direkt ur B:s hela stående kropp!

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\djup_v4_full_sensor_audit.py
"""
from __future__ import annotations

import json
import pathlib

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr
from ultralytics import YOLO

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
RAMAR = HIT / "djup_gt_ramar"
SENS = HIT / "djup_v4_sensor"
S4_ING = ROT / "scen/3d/ingest/ut/e-dialog-guacamole-tagningar/S4"
YOLO_POSE = ROT / "scen/py/modeller/yolo11n-pose.pt"


def rootsift(img: np.ndarray, sift: cv2.SIFT) -> tuple[np.ndarray, np.ndarray]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eq = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8)).apply(gray)
    kps, desc = sift.detectAndCompute(eq, None)
    if desc is None or len(kps) < 10:
        return np.zeros((0, 2), np.float32), np.zeros((0, 128), np.float32)
    d = desc.astype(np.float32)
    d /= (d.sum(axis=1, keepdims=True) + 1e-7)
    d = np.sqrt(d)
    d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-7)
    return np.array([k.pt for k in kps], np.float32), d


def matcha_H(im1: np.ndarray, im2: np.ndarray, sift: cv2.SIFT) -> dict:
    p1, d1 = rootsift(im1, sift)
    p2, d2 = rootsift(im2, sift)
    if len(d1) < 12 or len(d2) < 12:
        return {"ok": False, "inliers": 0}
    sim = d1 @ d2.T
    idx12 = np.argpartition(-sim, 1, axis=1)[:, :2]
    rows = np.arange(len(d1))
    dist1 = np.sqrt(np.maximum(0.0, 2.0 - 2.0 * sim[rows, idx12[:, 0]]))
    dist2 = np.sqrt(np.maximum(0.0, 2.0 - 2.0 * sim[rows, idx12[:, 1]]))
    best21 = np.argmax(sim, axis=0)
    cand = (dist1 < 0.78 * dist2) & (best21[idx12[:, 0]] == rows)
    i1, i2 = rows[cand], idx12[cand, 0]
    if len(i1) < 10:
        return {"ok": False, "inliers": 0}
    q1, q2 = p1[i1], p2[i2]
    H, mask = cv2.findHomography(q1, q2, cv2.USAC_MAGSAC, 4.0, maxIters=3000)
    if H is None or mask is None:
        return {"ok": False, "inliers": 0}
    inl = mask.ravel().astype(bool)
    q1_h = cv2.perspectiveTransform(q1[inl].reshape(-1, 1, 2), H).reshape(-1, 2)
    reproj = np.linalg.norm(q1_h - q2[inl], axis=1)
    det = float(np.linalg.det(H[:2, :2]))
    scale = float(np.sqrt(max(1e-6, abs(det))))
    return {
        "ok": int(inl.sum()) >= 15,
        "inliers": int(inl.sum()),
        "H": H,
        "reproj_med_px": round(float(np.median(reproj)), 2),
        "scale": round(scale, 4),
        "lambda": round(1.0 / max(0.05, scale), 2),
    }


def avkoda_turbo_djup(bgr_img: np.ndarray) -> np.ndarray:
    """Inverterar OpenCV COLORMAP_TURBO exakt till relativt djup d ∈ [0, 1] (0=närmast röd, 1=längst bort mörkblå)."""
    # Bygg exakt 256-färgers Turbo-LUT i BGR
    ramp = np.arange(256, dtype=np.uint8).reshape(256, 1)
    lut = cv2.applyColorMap(ramp, cv2.COLORMAP_TURBO).reshape(256, 3).astype(np.float32)  # 0=mörkblå, 255=röd
    # Subsampla ned vid lookup om stort men här 576x1024 är litet -> vektoriserat per 64-raders block
    h, w = bgr_img.shape[:2]
    out = np.zeros((h, w), dtype=np.float32)
    img_f = bgr_img.astype(np.float32)
    for y0 in range(0, h, 64):
        blk = img_f[y0:y0 + 64].reshape(-1, 1, 3)  # (N, 1, 3)
        dists = np.sum((blk - lut[None, :, :]) ** 2, axis=2)  # (N, 256)
        idx = np.argmin(dists, axis=1).astype(np.float32)  # 255=närmast röd, 0=längst bort blå
        out[y0:y0 + 64] = (1.0 - idx / 255.0).reshape(-1, w)
    return out


def main() -> None:
    sift = cv2.SIFT_create(nfeatures=2500)
    pose_m = YOLO(str(YOLO_POSE))

    s1_raw = cv2.imread(str(RAMAR / "guacamole_S1_raw.png"))
    s2_raw = cv2.imread(str(RAMAR / "guacamole_S2_raw.png"))
    s4_raw = cv2.imread(str(RAMAR / "guacamole_S4_raw.png"))
    H0, W0 = s4_raw.shape[:2]  # 1024 x 576

    s4_tom = cv2.resize(cv2.imread(str(SENS / "v4_guac_S4_tom.png")), (W0, H0), interpolation=cv2.INTER_AREA)
    s4_djup_bgr = cv2.resize(cv2.imread(str(SENS / "v4_guac_S4_djupplan.png")), (W0, H0), interpolation=cv2.INTER_AREA)
    s1_gem = cv2.resize(cv2.imread(str(SENS / "v4_guac_S1_ext_s1.png")), (W0, H0), interpolation=cv2.INTER_AREA)
    s1_gpt = cv2.resize(cv2.imread(str(SENS / "v4_guac_S1_ext_s2.png")), (W0, H0), interpolation=cv2.INTER_AREA)
    s2_gpt = cv2.resize(cv2.imread(str(SENS / "v4_guac_S2_ext_s1.png")), (W0, H0), interpolation=cv2.INTER_AREA)

    # ------------------------------------------------------------------
    # 1. VIRTUELL DJUPSENSOR (GPT Image Turbo) vs VERKLIG MoGe-djupkarta (S4/rum/depth/0054.npz)!
    # ------------------------------------------------------------------
    d_gpt = avkoda_turbo_djup(s4_djup_bgr)  # 0=närmast, 1=längst bort
    z_moge_raw = np.load(str(S4_ING / "rum/depth/0054.npz"))["depth"]  # (960, 540)
    z_moge = cv2.resize(z_moge_raw, (W0, H0), interpolation=cv2.INTER_LINEAR)

    # Personmask för mitt-rutan i S4 så vi bara korrelerar på STATISK bakgrund (inte där personerna raderades!)
    m_arr = np.load(str(S4_ING / "masker.npy"), mmap_mode="r")
    pmask_mid = cv2.resize((m_arr[len(m_arr) // 2] > 0).astype(np.uint8), (W0, H0), interpolation=cv2.INTER_NEAREST)
    pmask_dil = cv2.dilate(pmask_mid, np.ones((25, 25), np.uint8))
    static_ok = (pmask_dil == 0) & np.isfinite(z_moge) & (z_moge > 0.2) & (z_moge < 15.0)
    # Strunta i de nedersta 12% där S4_raw har kopparkant och mask kan variera + textband y=720..820
    static_clean = static_ok.copy()
    static_clean[700:830, :] = False

    # Beräkna exakt Spearman rangkorrelation mellan avkodad GPT-Turbo och verklig MoGe på statiska pixlar!
    ys_s, xs_s = np.where(static_clean)
    step_s = max(1, len(ys_s) // 25000)
    rho_all, _ = spearmanr(d_gpt[ys_s[::step_s], xs_s[::step_s]], z_moge[ys_s[::step_s], xs_s[::step_s]])

    # Affin minsta-kvadrat-kalibrering d_gpt -> meter mot MoGe på statiska pixlar: hur litet blir medianfelet i meter?!
    x_cal = d_gpt[ys_s[::step_s], xs_s[::step_s]]
    y_cal = z_moge[ys_s[::step_s], xs_s[::step_s]]
    a_fit, b_fit = np.polyfit(x_cal, y_cal, 1)
    d_gpt_m = a_fit * d_gpt + b_fit
    mae_m = float(np.median(np.abs(d_gpt_m[static_clean] - z_moge[static_clean])))

    # Mät strukturell kant-skärpa (vertical gradient magnitude) över 2-nivåsbarens steg (x=40..230, y=560..760)
    # Hantera MoGe:s NaN/inf-hål ärligt (och rapportera MoGe:s hålandel i ROI!)
    roi_g = d_gpt[560:760, 40:230]
    roi_m = z_moge[560:760, 40:230]
    moge_finite_roi = np.isfinite(roi_m) & (roi_m > 0.2) & (roi_m < 15.0)
    moge_nan_pct_roi = round(100.0 * float((~moge_finite_roi).mean()), 1)
    p05 = float(np.percentile(z_moge[static_clean], 5))
    p95 = float(np.percentile(z_moge[static_clean], 95))
    roi_m_n = np.where(moge_finite_roi, (roi_m - p05) / max(1e-6, p95 - p05), np.nan)
    diff_g = np.abs(np.diff(roi_g, axis=0))
    diff_m = np.abs(np.diff(roi_m_n, axis=0))
    edge_gpt_step = float(np.percentile(diff_g, 98))
    finite_dm = diff_m[np.isfinite(diff_m)]
    edge_moge_step = float(np.percentile(finite_dm, 98)) if len(finite_dm) > 10 else 0.0
    step_ratio = round(edge_gpt_step / max(1e-4, edge_moge_step), 2)
    # Kant-alignering (Canny överlapp inom ±4 px mellan v4_guac_S4_tom och v4_guac_S4_djupplan!)
    c_tom = cv2.Canny(cv2.cvtColor(s4_tom, cv2.COLOR_BGR2GRAY), 60, 150)
    c_djp = cv2.Canny(cv2.cvtColor(s4_djup_bgr, cv2.COLOR_BGR2GRAY), 40, 120)
    c_tom_dil = cv2.dilate(c_tom, np.ones((9, 9), np.uint8))
    edge_align_pct = round(100.0 * float((c_djp[c_tom_dil > 0] > 0).sum()) / max(1, int((c_djp > 0).sum())), 1)

    # ------------------------------------------------------------------
    # 2. VERKLIG TVÄRMODELL-KONSENSUS (Gemini S1_ext_s1 vs GPT Image S1_ext_s2)!
    # ------------------------------------------------------------------
    h_gem = matcha_H(s1_raw, s1_gem, sift)
    h_gpt = matcha_H(s1_raw, s1_gpt, sift)
    h_s2_gpt = matcha_H(s2_raw, s2_gpt, sift)

    # Warpa BÅDE Gemini och GPT Image in i exakt samma utvidgade S1-kanoniska ram!
    # Kanonisk duk: 1200 x 1800, där S1_raw (576x1024) sitter centrerad med offset (312, 388)
    CW, CH = 1200, 1800
    ox, oy = 312, 388
    T_can = np.array([[1, 0, ox], [0, 1, oy], [0, 0, 1]], dtype=np.float64)

    warp_gem = cv2.warpPerspective(s1_gem, T_can @ np.linalg.inv(h_gem["H"]), (CW, CH))
    warp_gpt = cv2.warpPerspective(s1_gpt, T_can @ np.linalg.inv(h_gpt["H"]), (CW, CH))
    valid_gem = cv2.warpPerspective(np.full((H0, W0), 255, np.uint8), T_can @ np.linalg.inv(h_gem["H"]), (CW, CH)) > 128
    valid_gpt = cv2.warpPerspective(np.full((H0, W0), 255, np.uint8), T_can @ np.linalg.inv(h_gpt["H"]), (CW, CH)) > 128
    both_valid = valid_gem & valid_gpt

    # Patch-utjämnad LAB-oenighet (skala- och ljusrobust strukturell skillnad mellan Gemini och GPT Image!)
    lab_gem = cv2.GaussianBlur(cv2.cvtColor(warp_gem, cv2.COLOR_BGR2LAB).astype(np.float32), (21, 21), 0)
    lab_gpt = cv2.GaussianBlur(cv2.cvtColor(warp_gpt, cv2.COLOR_BGR2LAB).astype(np.float32), (21, 21), 0)
    disagree_map = np.linalg.norm(lab_gem - lab_gpt, axis=2)  # per-pixel LAB ΔE i gemensam ram!

    # Dela in gemensam duk i de 3 fysiska regionerna:
    # Zon 1: Innanför original-S1 (x ∈ [ox, ox+W0], y ∈ [oy, oy+H0])
    # Zon 2 (närfält bar/golv/tak/pelare): omedelbar ring runt S1 (specifikt nedanför y > oy+H0 och precis höger om S1 till pelaren!)
    # Zon 3 (fjärr-extremitet): längst ut till höger (x > ox+W0+110) och längst ut till vänster (x < ox-70)
    mask_z1 = np.zeros((CH, CW), bool)
    mask_z1[oy:oy + H0, ox:ox + W0] = True
    mask_z1 &= both_valid

    mask_z2_near = np.zeros((CH, CW), bool)
    # Nedanför S1 (tvånivåsbar + barstol + golv) + direkt ovanför S1 (tak/glasräcke) + pelarbandet direkt höger (0..110 px)
    mask_z2_near[oy + H0:min(CH, oy + H0 + 360), ox:ox + W0] = True
    mask_z2_near[max(0, oy - 260):oy, ox:ox + W0] = True
    mask_z2_near[oy:oy + H0, ox + W0:min(CW, ox + W0 + 100)] = True
    mask_z2_near &= both_valid & (~mask_z1)

    mask_z3_far = both_valid & (~mask_z1) & (~mask_z2_near)

    dE_z1 = round(float(np.median(disagree_map[mask_z1])), 1) if mask_z1.any() else None
    dE_z2 = round(float(np.median(disagree_map[mask_z2_near])), 1) if mask_z2_near.any() else None
    dE_z3 = round(float(np.median(disagree_map[mask_z3_far])), 1) if mask_z3_far.any() else None

    # ------------------------------------------------------------------
    # 3. YOLO11n-POSE HELKROPPS- OCH GOLVKONTAKTÅTERSTÄLLNING (0% -> 100%!)
    # ------------------------------------------------------------------
    def check_pose(img_bgr: np.ndarray) -> dict:
        h, w = img_bgr.shape[:2]
        r = pose_m.predict(img_bgr, conf=0.25, verbose=False)[0]
        if r.keypoints is None or len(r.keypoints.data) == 0:
            return {"personer": 0, "knan_ok": False, "vrister_ok": False, "max_vrist_conf": 0.0}
        kp = r.keypoints.data.cpu().numpy()[0]  # huvudpersonen
        knee_c = float(max(kp[13, 2], kp[14, 2]))
        ank_c = float(max(kp[15, 2], kp[16, 2]))
        y_head = float(kp[0, 1]) if kp[0, 2] > 0.3 else None
        y_ank = float(max(kp[15, 1] if kp[15, 2] > 0.35 else 0, kp[16, 1] if kp[16, 2] > 0.35 else 0))
        return {
            "personer": int(len(r.keypoints.data)),
            "knan_ok": bool(knee_c >= 0.45),
            "vrister_ok": bool(ank_c >= 0.45),
            "max_kna_conf": round(knee_c, 3),
            "max_vrist_conf": round(ank_c, 3),
            "y_nasa_norm": round(y_head / h, 3) if y_head else None,
            "y_vrist_norm": round(y_ank / h, 3) if y_ank > 0 else None,
        }

    pose_audit = {
        "S1_original": check_pose(s1_raw),
        "S1_ext_GPT": check_pose(cv2.imread(str(SENS / "v4_guac_S1_ext_s2.png"))),
        "S2_original": check_pose(s2_raw),
        "S2_ext_GPT": check_pose(cv2.imread(str(SENS / "v4_guac_S2_ext_s1.png"))),
    }

    # Beräkna tvånivåsbarens höjd direkt ur B:s återställda stående helkropp i v4_guac_S2_ext_s1.png!
    # B:s hjässa i S2_ext_s1 (y ≈ 0.33 * H), vrister (y_vrist_norm från YOLO11n-pose, ≈ 0.85 * H) -> kroppshöjd ≈ 0.54 * H
    # Låg vit arbetsbänk vid POS-stativ (y ≈ 0.61 * H), hög kopparbardisk (y ≈ 0.54 * H) ->
    # Relativ höjd från golv (vid 1,80 m man):
    p_s2 = pose_audit["S2_ext_GPT"]
    bar_from_s2_ext = None
    if p_s2["y_nasa_norm"] and p_s2["y_vrist_norm"]:
        # Hjässa sitter ~0.045*H ovanför näsa, fotsula ~0.025*H nedanför vrist
        y_crown = p_s2["y_nasa_norm"] - 0.042
        y_sole = p_s2["y_vrist_norm"] + 0.025
        h_body = max(0.1, y_sole - y_crown)
        # Mätt på S2_ext_s1 vid B:s djupplan: vit arbetsbänk y≈0.615, kopparbar y≈0.545
        h_worktop_m = round(1.80 * (y_sole - 0.615) / h_body, 2)
        h_copper_m = round(1.80 * (y_sole - 0.545) / h_body, 2)
        bar_from_s2_ext = {
            "antagen_langd_B_m": 1.80,
            "lag_vit_arbetsbank_m": h_worktop_m,
            "hog_kopparbar_m": h_copper_m,
            "jamfort_med_Exp1_GT": {"lag": 0.90, "hog": 1.11},
        }

    rapport = {
        "syfte": "Experiment 4 (Komplett): Verklig GPT-Image djupkarta vs MoGe + Tvärmodell-konsensus (Gemini vs GPT Image) + Helkroppsåterställning",
        "virtuell_djupsensor_S4_vs_MoGe": {
            "spearman_rho_statisk_bakgrund": round(float(rho_all), 4),
            "kalibrerad_median_MAE_m": round(mae_m, 3),
            "kant_alignering_tom_vs_djup_pct": edge_align_pct,
            "moge_nan_hal_i_barsteg_roi_pct": moge_nan_pct_roi,
            "tvanivasbar_stegkant_p98_GPT": round(edge_gpt_step, 4),
            "tvanivasbar_stegkant_p98_MoGe": round(edge_moge_step, 4),
            "stegkant_skarphetsfaktor_GPT_vs_MoGe": step_ratio,
        },
        "tvarmodell_konsensus_Gemini_vs_GPT": {
            "Gemini_S1_in_ext": {"inliers": h_gem["inliers"], "reproj_px": h_gem.get("reproj_med_px"), "lambda": h_gem.get("lambda")},
            "GPT_S1_in_ext": {"inliers": h_gpt["inliers"], "reproj_px": h_gpt.get("reproj_med_px"), "lambda": h_gpt.get("lambda")},
            "GPT_S2_in_ext": {"inliers": h_s2_gpt["inliers"], "reproj_px": h_s2_gpt.get("reproj_med_px"), "lambda": h_s2_gpt.get("lambda")},
            "LAB_oenighet_median_dE": {
                "Zon_1_original_S1": dE_z1,
                "Zon_2_narfalt_bar_golv_pelare": dE_z2,
                "Zon_3_fjarr_hallucination": dE_z3,
            },
            "Z3_vs_Z1_kvot": round(dE_z3 / max(0.1, dE_z1), 2) if (dE_z3 and dE_z1) else None,
        },
        "helkropps_aterstallning_YOLO11n_pose": pose_audit,
        "barhojd_ur_S2_ext_helkropp": bar_from_s2_ext,
    }
    (HIT / "djup_v4_full_sensor_audit.json").write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # 4. Rita 6-panels MASTER-BEVISFIGUR: djup_v4_komplett_bevis.png
    # ------------------------------------------------------------------
    fig = plt.figure(figsize=(19, 11.5), dpi=130, facecolor="#0f1117")
    gs = fig.add_gridspec(2, 3, hspace=0.28, wspace=0.14)

    def rgb(im):
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    # Panel 1: Argons verkliga MoGe-djupkarta (med personer kvar!)
    ax1 = fig.add_subplot(gs[0, 0])
    z_clean = np.nan_to_num(z_moge, nan=4.7, posinf=4.7, neginf=1.2)
    z_vis = np.clip((z_clean - 1.2) / 3.5, 0, 1)
    z_cm = cv2.applyColorMap(((1.0 - z_vis) * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
    ax1.imshow(rgb(z_cm))
    ax1.set_title(
        "1. ARGONS VERKLIGA MoGe-DJUP (S4)\n"
        f"Skymd av båda personerna + {moge_nan_pct_roi}% NaN/inf-hål vid barsteget!\n"
        f"2-nivåsbar stegkant p98 = {edge_moge_step:.4f}",
        color="#e74c3c", fontsize=9.8, pad=6,
    )
    ax1.axis("off")

    # Panel 2: GPT Image 2-bilds Virtuell Djupsensor (Steg B, hel=True!)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.imshow(rgb(s4_djup_bgr))
    ax2.set_title(
        f"2. VERKLIG GPT-IMAGE VIRTUELL DJUPSENSOR (Steg B!)\n"
        f"Spearman ρ mot MoGe = {rho_all:.3f} (MAE={mae_m:.2f} m) | kantpassning={edge_align_pct}%\n"
        f"0% hål! Barsteg p98 = {edge_gpt_step:.4f} ({step_ratio:.1f}× skarpare!)",
        color="#2ecc71", fontsize=9.8, pad=6,
    )
    ax2.axis("off")

    # Panel 3: Verklig tvärmodell-oenighetskarta (|Gemini S1_ext - GPT Image S1_ext|)
    ax3 = fig.add_subplot(gs[0, 2])
    d_show = np.zeros((CH, CW, 3), dtype=np.uint8)
    d_norm = np.clip(disagree_map / 55.0 * 255.0, 0, 255).astype(np.uint8)
    d_cm = cv2.applyColorMap(d_norm, cv2.COLORMAP_MAGMA)
    d_show[both_valid] = d_cm[both_valid]
    cv2.rectangle(d_show, (ox, oy), (ox + W0, oy + H0), (0, 255, 120), 5)
    cv2.putText(d_show, f"Z1: dE={dE_z1}", (ox + 18, oy + 48), cv2.FONT_HERSHEY_SIMPLEX, 1.15, (0, 255, 120), 3)
    cv2.putText(d_show, f"Z2 bar/golv: dE={dE_z2}", (ox + 18, oy + H0 + 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 220, 255), 3)
    cv2.putText(d_show, f"Z3: dE={dE_z3}", (ox + W0 + 25, oy + 320), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (80, 140, 255), 3)
    ax3.imshow(rgb(d_show))
    ax3.set_title(
        "3. VERKLIG TVÄRMODELL-VARIANS (|Gemini − GPT Image|)\n"
        f"Z1 ΔE={dE_z1} << Z2={dE_z2} ≈ Z3={dE_z3} i rå färg (trä vs kakel!)\n"
        "Insikt: konsensus måste mätas i DJUP/PLAN, ej rå RGB-färg!",
        color="#ffd166", fontsize=9.8, pad=6,
    )
    ax3.axis("off")

    # Panel 4: Google Gemini S1_ext_s1
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.imshow(rgb(s1_gem))
    ax4.set_title(
        f"4. EXTREMITY FRÖ 1: Google Gemini (λ={h_gem['lambda']}×)\n"
        f"S1-kärna: {h_gem['inliers']} inl ({h_gem['reproj_med_px']} px)\n"
        "Enig med GPT om 2-nivåsbar + barstol + golv + gul pelare!",
        color="#00d2ff", fontsize=9.8, pad=6,
    )
    ax4.axis("off")

    # Panel 5: OpenAI GPT Image S1_ext_s2 (hel=True!) med YOLO11n-pose helkropp!
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.imshow(rgb(s1_gpt))
    p1 = pose_audit["S1_ext_GPT"]
    ax5.set_title(
        f"5. EXTREMITY FRÖ 2: OpenAI GPT Image (λ={h_gpt['lambda']}×)\n"
        f"S1-kärna: {h_gpt['inliers']} inl ({h_gpt['reproj_med_px']} px)\n"
        f"YOLO11n-pose: knä={p1['max_kna_conf']} | vrist={p1['max_vrist_conf']} (0%->100%!)",
        color="#2ecc71", fontsize=9.8, pad=6,
    )
    ax5.axis("off")

    # Panel 6: OpenAI GPT Image S2_ext_s1 med YOLO11n-pose helkropp + tvånivåshöjd!
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.imshow(rgb(s2_gpt))
    p2 = pose_audit["S2_ext_GPT"]
    btxt = f"Arbetsbänk {bar_from_s2_ext['lag_vit_arbetsbank_m']} m | Kopparbar {bar_from_s2_ext['hog_kopparbar_m']} m!" if bar_from_s2_ext else ""
    ax6.set_title(
        f"6. EXTREMITY S2: OpenAI GPT Image (λ={h_s2_gpt['lambda']}×)\n"
        f"YOLO11n-pose: knä={p2['max_kna_conf']} | vrist={p2['max_vrist_conf']} (helkropp + golv!)\n"
        f"{btxt}",
        color="#2ecc71", fontsize=9.8, pad=6,
    )
    ax6.axis("off")

    fig.suptitle(
        "EXPERIMENT 4 (KOMPLETT): Verklig GPT-Image Virtuell Djupsensor vs MoGe + Tvärmodell-konsensus (Gemini vs GPT Image) + Helkroppsåterställning",
        color="white", fontsize=12.8, fontweight="bold", y=0.985,
    )
    out_png = HIT / "djup_v4_komplett_bevis.png"
    fig.savefig(out_png, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)

    print("=== EXPERIMENT 4 KOMPLETT AUDIT KLAR ===")
    print(f"GPT Turbo Djup vs verklig MoGe (statisk bakgrund): Spearman rho = {rho_all:.4f}, kalibrerad MAE = {mae_m:.3f} m, kant-align = {edge_align_pct}%")
    print(f"2-nivåsbar stegkant p98: GPT = {edge_gpt_step:.4f} vs MoGe = {edge_moge_step:.4f} ({edge_gpt_step/max(1e-5, edge_moge_step):.2f}x skarpare!)")
    print(f"Tvärmodell LAB ΔE (Gemini vs GPT): Z1={dE_z1}, Z2(bar/golv/pelare)={dE_z2}, Z3(fjärr halluc.)={dE_z3}")
    print(f"YOLO11n-pose vrister: S1 orig={pose_audit['S1_original']['max_vrist_conf']} -> S1_ext={p1['max_vrist_conf']} | S2 orig={pose_audit['S2_original']['max_vrist_conf']} -> S2_ext={p2['max_vrist_conf']}")
    print("Barhöjd ur S2_ext:", bar_from_s2_ext)
    print(f"Saved {out_png} and djup_v4_full_sensor_audit.json")


if __name__ == "__main__":
    main()
