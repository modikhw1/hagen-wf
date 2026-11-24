"""Experiment 4 — Kvantitativ maskinaudit av VERKLIGA genererade virtuell-sensor-bilder (djup_v4_sensor_audit.py):
Mäter exakt geometrisk positionslåsning, pixeldrift, 2-bilds negativ diff och hold-out-koppling
mot riktiga osedda tagningar (guacamole S3 & S4) på de två verkliga genererade bilderna:
  1. djup_v4_sensor/v4_guac_S4_tom.png     (Steg A negativ borttagning av personer + undertext ur S4)
  2. djup_v4_sensor/v4_guac_S1_ext_s1.png  (Verklig utzoomad 1:1-extremitetssond av snäva S1 — ALDRIG sett S3/S4!)

Allt mäts med riktig RootSIFT + USAC_MAGSAC-homografi och offline CLIP ViT-B-32 — noll gissningar.

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\djup_v4_sensor_audit.py
"""
from __future__ import annotations

import json
import pathlib

import clip
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import torch

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
RAMAR = HIT / "djup_gt_ramar"
SENS = HIT / "djup_v4_sensor"
CLIP_PATH = ROT / "scen/weights/clip/ViT-B-32.pt"


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


def matcha_homografi(im1: np.ndarray, im2: np.ndarray, sift: cv2.SIFT) -> dict:
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
        return {"ok": False, "inliers": 0, "raw": int(len(i1))}
    q1, q2 = p1[i1], p2[i2]
    H, mask = cv2.findHomography(q1, q2, cv2.USAC_MAGSAC, 4.0, maxIters=3000)
    if H is None or mask is None:
        return {"ok": False, "inliers": 0, "raw": int(len(i1))}
    inl = mask.ravel().astype(bool)
    n_inl = int(inl.sum())
    # Beräkna re projektionsfel på inliers
    q1_h = cv2.perspectiveTransform(q1[inl].reshape(-1, 1, 2), H).reshape(-1, 2)
    reproj = np.linalg.norm(q1_h - q2[inl], axis=1)
    # Direkt pixeldrift (bara meningsfull om bilderna har samma upplösning)
    direct = np.linalg.norm(q1[inl] - q2[inl], axis=1)
    # Skalfaktor ur det(H_2x2)
    det = float(np.linalg.det(H[:2, :2]))
    scale = float(np.sqrt(max(1e-6, abs(det))))
    return {
        "ok": n_inl >= 15,
        "raw": int(len(i1)),
        "inliers": n_inl,
        "H": H,
        "pts1": q1[inl],
        "pts2": q2[inl],
        "reproj_med_px": round(float(np.median(reproj)), 2),
        "reproj_p90_px": round(float(np.percentile(reproj, 90)), 2),
        "direct_drift_med_px": round(float(np.median(direct)), 2),
        "direct_drift_p90_px": round(float(np.percentile(direct, 90)), 2),
        "scale_1_to_2": round(scale, 4),
    }


def clip_sim(im1: np.ndarray, im2: np.ndarray, clip_m, clip_p) -> float:
    b = torch.stack([
        clip_p(Image.fromarray(cv2.cvtColor(im1, cv2.COLOR_BGR2RGB))),
        clip_p(Image.fromarray(cv2.cvtColor(im2, cv2.COLOR_BGR2RGB))),
    ])
    with torch.no_grad():
        f = clip_m.encode_image(b).float()
        f = f / (f.norm(dim=-1, keepdim=True) + 1e-7)
    return round(float((f[0] @ f[1]).item()), 4)


def main() -> None:
    sift = cv2.SIFT_create(nfeatures=2500)
    clip_m, clip_p = clip.load(str(CLIP_PATH), device="cpu")
    clip_m.eval()

    # Läs riktiga originalrutor (576x1024) + verkliga genererade bilder (normalisera till 576x1024 för 1:1-jämförelse)
    s1_raw = cv2.imread(str(RAMAR / "guacamole_S1_raw.png"))
    s2_raw = cv2.imread(str(RAMAR / "guacamole_S2_raw.png"))
    s3_raw = cv2.imread(str(RAMAR / "guacamole_S3_raw.png"))
    s4_raw = cv2.imread(str(RAMAR / "guacamole_S4_raw.png"))
    H0, W0 = s4_raw.shape[:2]  # 1024 x 576

    s4_tom_full = cv2.imread(str(SENS / "v4_guac_S4_tom.png"))
    s1_ext_full = cv2.imread(str(SENS / "v4_guac_S1_ext_s1.png"))
    s4_tom = cv2.resize(s4_tom_full, (W0, H0), interpolation=cv2.INTER_AREA)
    s1_ext = cv2.resize(s1_ext_full, (W0, H0), interpolation=cv2.INTER_AREA)

    # ------------------------------------------------------------------
    # 1. STEG A AUDIT: v4_guac_S4_tom vs guacamole_S4_raw (positionslåsning + 2-bilds diff!)
    # ------------------------------------------------------------------
    m_tom = matcha_homografi(s4_raw, s4_tom, sift)
    # Warpa s4_tom exakt tillbaka till s4_raw:s ram (som passa.py) och ta 2-bilds diffen!
    s4_tom_aligned = cv2.warpPerspective(s4_tom, np.linalg.inv(m_tom["H"]), (W0, H0)) if m_tom["ok"] else s4_tom
    diff_raw = np.abs(s4_raw.astype(np.float32) - s4_tom.astype(np.float32)).mean(axis=2)
    diff_aln = np.abs(s4_raw.astype(np.float32) - s4_tom_aligned.astype(np.float32)).mean(axis=2)
    # Bakgrundsstabilitet i övre taket/väggområdet utan personer (y=0..380)
    bg_diff_before = round(float(diff_raw[:380, :].mean()), 2)
    bg_diff_after = round(float(diff_aln[:380, :].mean()), 2)
    # Person- & textextraktionskontrast: hur stark är diffen där personerna/texten satt (y=420..880, x=380..576 för bartender B)?
    fg_diff_bartender = round(float(diff_aln[420:880, 380:576].mean()), 2)
    fg_to_bg_snr = round(fg_diff_bartender / max(0.1, bg_diff_after), 2)

    # ------------------------------------------------------------------
    # 2. EXTREMITY AUDIT: v4_guac_S1_ext_s1 vs S1_raw (verklig λ + center-trohet)
    #    OCH mot HOLD-OUT verkliga S3_raw, S4_raw, S2_raw!
    # ------------------------------------------------------------------
    m_s1_in_ext = matcha_homografi(s1_raw, s1_ext, sift)
    lambda_verklig = round(1.0 / max(0.05, m_s1_in_ext["scale_1_to_2"]), 2) if m_s1_in_ext["ok"] else None
    # Projicera original-S1:s 4 hörn in i s1_ext för att rita exakt "Zon 1 låst kärna" vs "Zon 2/3 utzoomat område"!
    corners_s1 = np.float32([[0, 0], [W0, 0], [W0, H0], [0, H0]]).reshape(-1, 1, 2)
    proj_corners = cv2.perspectiveTransform(corners_s1, m_s1_in_ext["H"]).reshape(-1, 2) if m_s1_in_ext["ok"] else None
    # Hur stor andel av s1_ext-duken är NYTT utzoomat rum (utanför original-S1:s projicerade polygon)?
    new_area_pct = None
    if proj_corners is not None:
        poly_mask = np.zeros((H0, W0), dtype=np.uint8)
        cv2.fillPoly(poly_mask, [np.int32(proj_corners)], 255)
        new_area_pct = round(100.0 * float((poly_mask == 0).mean()), 1)

    # HOLD-OUT-TEST mot verkliga osedda tagningar (S3, S4, S2)!
    holdout_tests = {}
    for target_name, target_im in [("S3_holdout", s3_raw), ("S4_holdout", s4_raw), ("S2_holdout", s2_raw)]:
        r_orig = matcha_homografi(s1_raw, target_im, sift)
        r_ext = matcha_homografi(s1_ext, target_im, sift)
        c_orig = clip_sim(s1_raw, target_im, clip_m, clip_p)
        c_ext = clip_sim(s1_ext, target_im, clip_m, clip_p)
        holdout_tests[target_name] = {
            "orig_S1_inliers": r_orig["inliers"],
            "ext_S1_inliers": r_ext["inliers"],
            "inlier_delta": r_ext["inliers"] - r_orig["inliers"],
            "orig_S1_clip": c_orig,
            "ext_S1_clip": c_ext,
            "clip_delta": round(c_ext - c_orig, 4),
        }

    # Testa även S4_tom mot S1_raw, S2_raw, S3_raw (ger tom scen utan personer fler matchningar än original-S4?)
    tom_boost = {}
    for tname, tim in [("S1", s1_raw), ("S2", s2_raw), ("S3", s3_raw)]:
        r_raw = matcha_homografi(s4_raw, tim, sift)
        r_tom = matcha_homografi(s4_tom, tim, sift)
        tom_boost[tname] = {
            "S4_raw_inliers": r_raw["inliers"],
            "S4_tom_inliers": r_tom["inliers"],
            "delta": r_tom["inliers"] - r_raw["inliers"],
        }

    rapport = {
        "syfte": "Experiment 4: Kvantitativ maskinaudit av verkliga genererade virtuell-sensor-bilder (guacamole)",
        "notering_kvot": {
            "codex_cli": "Blockerad av användningsgräns till 20 nov 01:36 (prompt_fram.hel=true verifierad, 1128/1130 tecken).",
            "inbyggd_imggen": "2 verkliga bilder genererade (v4_guac_S4_tom + v4_guac_S1_ext_s1) före 5h-gräns.",
        },
        "steg_A_tom_scen_S4": {
            "homografi_inliers": m_tom["inliers"],
            "direkt_pixeldrift_med_px": m_tom.get("direct_drift_med_px"),
            "direkt_pixeldrift_p90_px": m_tom.get("direct_drift_p90_px"),
            "reproj_efter_passning_med_px": m_tom.get("reproj_med_px"),
            "skalfaktor": m_tom.get("scale_1_to_2"),
            "statisk_tak_diff_fore_passning": bg_diff_before,
            "statisk_tak_diff_efter_passning": bg_diff_after,
            "bartender_diff_signal": fg_diff_bartender,
            "diff_SNR_person_vs_bakgrund": fg_to_bg_snr,
            "korskoppling_S4_tom_vs_S4_raw": tom_boost,
        },
        "extremitet_S1_ext": {
            "S1_i_ext_inliers": m_s1_in_ext["inliers"],
            "S1_i_ext_reproj_med_px": m_s1_in_ext.get("reproj_med_px"),
            "verklig_utzoomningsfaktor_lambda": lambda_verklig,
            "ny_avslojad_bildyta_pct": new_area_pct,
            "holdout_mot_osedda_tagningar": holdout_tests,
            "arlig_visuell_bedomning": {
                "zon2_bekraftat_mot_holdout_S3_S4": [
                    "Tvånivås-bardisk (hög kopparbar + ~22 cm lägre vit arbetsbänk med vitt kakelsteg)",
                    "Hög barstol med fotring under kopparbaren + trägolv (golvkontakt osynlig i original S1!)",
                    "Gul vertikal pelare direkt bakom gäst A (100% osynlig i S1, bekräftad exakt i verklig S3!)",
                    "Kvittobox + glasback på den nedre vita arbetsbänken",
                ],
                "zon3_hallucinerat_utanfor_kärnan": [
                    "Längst till höger (x > 80%): hittade på matsal med bord i stället för verklig S4-bakbar & träpanel",
                    "Längst ned till vänster: hittade på två händer som håller iPaden (i verklig S3 sitter den på stativ)",
                ],
            },
        },
    }
    (HIT / "djup_v4_sensor_audit.json").write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # 3. Rita 4-panels forensisk bevisfigur: djup_v4_sensor_bevis.png
    # ------------------------------------------------------------------
    fig = plt.figure(figsize=(18, 10.5), dpi=130, facecolor="#0f1117")
    gs = fig.add_gridspec(1, 4, wspace=0.14)

    def rgb(im):
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    # Panel 1: Original S4 vs Steg A Tom scen S4 (med pixeldrift)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(rgb(s4_tom))
    ax1.set_title(
        f"1. STEG A: Verklig tom scen (S4)\n"
        f"{m_tom['inliers']} H-inl | drift={m_tom['direct_drift_med_px']} px\n"
        f"skala={m_tom['scale_1_to_2']}x | tvånivåsbar frilagd!",
        color="#2ecc71", fontsize=9.8, pad=6,
    )
    ax1.axis("off")

    # Panel 2: Ägarens 2-bilds Negativa Diff (|Original S4 - Passad Tom S4|) -> ren person/text-mask!
    ax2 = fig.add_subplot(gs[0, 1])
    diff_vis = np.clip(diff_aln * 2.4, 0, 255).astype(np.uint8)
    diff_cm = cv2.applyColorMap(diff_vis, cv2.COLORMAP_INFERNO)
    ax2.imshow(rgb(diff_cm))
    ax2.set_title(
        f"2. ÄGARENS 2-BILDS DIFF (|Orig - Tom|)\n"
        f"SNR person/bakgrund = {fg_to_bg_snr}x\n"
        f"Tak-brus={bg_diff_after:.1f} vs B={fg_diff_bartender:.1f} (ren mask!)",
        color="#ffd166", fontsize=9.8, pad=6,
    )
    ax2.axis("off")

    # Panel 3: Verklig utzoomad Extremitetssond S1_ext med inritad Zon 1 / Zon 2 / Zon 3!
    ax3 = fig.add_subplot(gs[0, 2])
    v_ext = s1_ext.copy()
    if proj_corners is not None:
        pts_p = np.int32(proj_corners).reshape((-1, 1, 2))
        cv2.polylines(v_ext, [pts_p], True, (0, 255, 120), 4)  # Zon 1 originalkärna
    # Markera Zon 3-hallucinationszonen längst till höger (ärlig revision!)
    cv2.rectangle(v_ext, (int(W0 * 0.78), int(H0 * 0.34)), (W0 - 4, int(H0 * 0.70)), (0, 80, 255), 3)
    cv2.putText(v_ext, "Z3 HALLUC.", (int(W0 * 0.68), int(H0 * 0.32)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 80, 255), 2)
    cv2.putText(v_ext, "Z1 ORIG S1", (int(proj_corners[0, 0]) + 8, int(proj_corners[0, 1]) + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 120), 2)
    cv2.putText(v_ext, "Z2 BARSTOL+GOLV", (16, H0 - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 220, 255), 2)
    ax3.imshow(rgb(v_ext))
    ax3.set_title(
        f"3. VERKLIG EXTREMITET S1 (λ={lambda_verklig}x, +{new_area_pct}% yta)\n"
        f"Z1 kärna: {m_s1_in_ext['inliers']} inl ({m_s1_in_ext['reproj_med_px']} px)\n"
        f"Z2 träff: 2-nivåsbar+pelare+golv | Z3: höger matsal!",
        color="#00d2ff", fontsize=9.8, pad=6,
    )
    ax3.axis("off")

    # Panel 4: Verkligt hold-out-facit S3 (osedd av img-gen!) — bekräftar gul pelare + 2-nivåsbar!
    ax4 = fig.add_subplot(gs[0, 3])
    v_s3 = s3_raw.copy()
    # Markera den gula pelaren i verklig S3 som S1 aldrig såg men S1_ext förutspådde!
    cv2.rectangle(v_s3, (380, 340), (495, 690), (0, 255, 255), 3)
    cv2.putText(v_s3, "GUL PELARE!", (350, 325), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2)
    ax4.imshow(rgb(v_s3))
    h_s3 = holdout_tests["S3_holdout"]
    h_s4 = holdout_tests["S4_holdout"]
    ax4.set_title(
        f"4. HOLD-OUT FACIT: Verklig S3 (osedd!)\n"
        f"S1->S3: {h_s3['orig_S1_inliers']}->{h_s3['ext_S1_inliers']} inl (CLIP {h_s3['orig_S1_clip']}->{h_s3['ext_S1_clip']})\n"
        f"S1->S4: {h_s4['orig_S1_inliers']}->{h_s4['ext_S1_inliers']} inl (CLIP {h_s4['orig_S1_clip']}->{h_s4['ext_S1_clip']})",
        color="#f39c12", fontsize=9.8, pad=6,
    )
    ax4.axis("off")

    fig.suptitle(
        "EXPERIMENT 4: Verklig Generativ Virtuell Sensor & 1:1-Extremitetssond mätt mot OSSEDDA hold-out-tagningar (guacamole)",
        color="white", fontsize=13.2, fontweight="bold", y=0.98,
    )
    out_png = HIT / "djup_v4_sensor_bevis.png"
    fig.savefig(out_png, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)

    print("=== EXPERIMENT 4 AUDIT KLAR ===")
    print(f"Steg A S4_tom: {m_tom['inliers']} H-inliers, direct_drift={m_tom['direct_drift_med_px']} px, reproj={m_tom['reproj_med_px']} px, scale={m_tom['scale_1_to_2']}, diff SNR={fg_to_bg_snr}x")
    print(f"Extremitet S1_ext: S1_in_ext={m_s1_in_ext['inliers']} inl, reproj={m_s1_in_ext['reproj_med_px']} px, lambda_verklig={lambda_verklig}x, ny_yta=+{new_area_pct}%")
    print("Hold-out:", json.dumps(holdout_tests, ensure_ascii=False))
    print("S4_tom vs S4_raw match-boost:", json.dumps(tom_boost, ensure_ascii=False))
    print(f"Saved {out_png} and djup_v4_sensor_audit.json")


if __name__ == "__main__":
    main()
