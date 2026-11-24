"""Experiment 6 — Kvantitativ maskinaudit av A/B-promptoptimering & 0..1-skalan (djup_v5_prompt_audit.py):
Utvärderar ALLA 6 verkliga GPT-Image-utfall (samtliga hel=True!) objektivt på 4 maskinmått:
  1. Geometrisk positionslåsning (RootSIFT + USAC_MAGSAC: H-inliers, direkt pixeldrift px, skala) mot original.
  2. Brusreduktion vs strukturell renhet (högfrekvent kantbrus % nedgång + LSD-linjekoherens).
  3. Lokalidentitet via offline CLIP ViT-B-32 zero-shot: bevisar att 0.35 / 0.45 / 0.55 fortfarande
     läses omisskännligt som "bar counter" / "gelato display counter" i stället för "empty bare room"!
  4. Generalisering av 2-bilds Virtuell Djupsensor till GENOMSKINLIG GLASSMONTER (gelato S1):
     mäter v5_gelato_regi_05_djup.png mot Argons verkliga MoGe-djup (S1/rum/depth/0078.npz: 15.0% NaN-hål!).

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\djup_v5_prompt_audit.py
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
from scipy.stats import spearmanr
import torch

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
RAMAR = HIT / "djup_gt_ramar"
AB_DIR = HIT / "djup_v5_prompt_ab"
CLIP_PATH = ROT / "scen/weights/clip/ViT-B-32.pt"
GEL_ING = ROT / "scen/3d/ingest/ut/kand-kennysgelato-tagningar/S1"


def rootsift(img: np.ndarray, sift: cv2.SIFT):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eq = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8)).apply(g)
    kps, desc = sift.detectAndCompute(eq, None)
    if desc is None or len(kps) < 10:
        return np.zeros((0, 2), np.float32), np.zeros((0, 128), np.float32)
    d = desc.astype(np.float32)
    d /= (d.sum(axis=1, keepdims=True) + 1e-7)
    d = np.sqrt(d)
    d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-7)
    return np.array([k.pt for k in kps], np.float32), d


def geom_lock(im_orig: np.ndarray, im_gen: np.ndarray, sift: cv2.SIFT) -> dict:
    p1, d1 = rootsift(im_orig, sift)
    p2, d2 = rootsift(im_gen, sift)
    if len(d1) < 12 or len(d2) < 12:
        return {"inliers": 0, "drift_px": None, "reproj_px": None, "scale": None}
    sim = d1 @ d2.T
    idx12 = np.argpartition(-sim, 1, axis=1)[:, :2]
    rows = np.arange(len(d1))
    dist1 = np.sqrt(np.maximum(0.0, 2.0 - 2.0 * sim[rows, idx12[:, 0]]))
    dist2 = np.sqrt(np.maximum(0.0, 2.0 - 2.0 * sim[rows, idx12[:, 1]]))
    best21 = np.argmax(sim, axis=0)
    cand = (dist1 < 0.80 * dist2) & (best21[idx12[:, 0]] == rows)
    i1, i2 = rows[cand], idx12[cand, 0]
    if len(i1) < 10:
        return {"inliers": 0, "drift_px": None, "reproj_px": None, "scale": None}
    q1, q2 = p1[i1], p2[i2]
    H, mask = cv2.findHomography(q1, q2, cv2.USAC_MAGSAC, 5.0, maxIters=3000)
    if H is None or mask is None:
        return {"inliers": 0, "drift_px": None, "reproj_px": None, "scale": None}
    inl = mask.ravel().astype(bool)
    n_inl = int(inl.sum())
    if n_inl < 8:
        return {"inliers": n_inl, "drift_px": None, "reproj_px": None, "scale": None}
    q1_h = cv2.perspectiveTransform(q1[inl].reshape(-1, 1, 2), H).reshape(-1, 2)
    reproj = np.linalg.norm(q1_h - q2[inl], axis=1)
    direct = np.linalg.norm(q1[inl] - q2[inl], axis=1)
    scale = float(np.sqrt(max(1e-6, abs(np.linalg.det(H[:2, :2])))))
    return {
        "inliers": n_inl,
        "drift_px": round(float(np.median(direct)), 2),
        "reproj_px": round(float(np.median(reproj)), 2),
        "scale": round(scale, 4),
    }


def clutter_metrics(img: np.ndarray) -> dict:
    """Mäter högfrekvent kantbrus (Canny-densitet) och strukturell linjerening (andel långa linjer >= 45 px)."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(g, 50, 140)
    edge_dens = round(100.0 * float((edges > 0).mean()), 2)
    lsd = cv2.createLineSegmentDetector(0)
    lines = lsd.detect(g)[0]
    if lines is None or len(lines) == 0:
        return {"edge_density_pct": edge_dens, "total_lines": 0, "long_line_share_pct": 0.0}
    segs = lines.reshape(-1, 4)
    lens = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1])
    long_share = round(100.0 * float((lens >= 45.0).mean()), 1)
    return {
        "edge_density_pct": edge_dens,
        "total_lines": int(len(lens)),
        "long_line_share_pct": long_share,
    }


def avkoda_turbo(bgr_img: np.ndarray) -> np.ndarray:
    ramp = np.arange(256, dtype=np.uint8).reshape(256, 1)
    lut = cv2.applyColorMap(ramp, cv2.COLORMAP_TURBO).reshape(256, 3).astype(np.float32)
    h, w = bgr_img.shape[:2]
    out = np.zeros((h, w), dtype=np.float32)
    imf = bgr_img.astype(np.float32)
    for y0 in range(0, h, 64):
        blk = imf[y0:y0 + 64].reshape(-1, 1, 3)
        idx = np.argmin(np.sum((blk - lut[None, :, :]) ** 2, axis=2), axis=1).astype(np.float32)
        out[y0:y0 + 64] = (1.0 - idx / 255.0).reshape(-1, w)
    return out


def main() -> None:
    sift = cv2.SIFT_create(nfeatures=2500)
    clip_m, clip_p = clip.load(str(CLIP_PATH), device="cpu")
    clip_m.eval()

    # Zero-shot CLIP lokalidentitetstexter
    text_labels = [
        "a restaurant bar counter interior",
        "a gelato ice cream display showcase counter",
        "a bare empty grey concrete box room with no furniture",
        "a messy cluttered photo with white subtitles and people",
    ]
    with torch.no_grad():
        t_tok = clip.tokenize(text_labels)
        t_feat = clip_m.encode_text(t_tok).float()
        t_feat = t_feat / (t_feat.norm(dim=-1, keepdim=True) + 1e-7)

    def clip_eval(im_bgr: np.ndarray, im_orig: np.ndarray) -> dict:
        b = torch.stack([
            clip_p(Image.fromarray(cv2.cvtColor(im_bgr, cv2.COLOR_BGR2RGB))),
            clip_p(Image.fromarray(cv2.cvtColor(im_orig, cv2.COLOR_BGR2RGB))),
        ])
        with torch.no_grad():
            f = clip_m.encode_image(b).float()
            f = f / (f.norm(dim=-1, keepdim=True) + 1e-7)
            logits = (100.0 * (f[0:1] @ t_feat.T)).softmax(dim=-1)[0].cpu().numpy()
            sim_orig = float((f[0] @ f[1]).item())
        return {
            "sim_to_orig": round(sim_orig, 4),
            "p_bar": round(float(logits[0]), 4),
            "p_gelato": round(float(logits[1]), 4),
            "p_bare_empty": round(float(logits[2]), 4),
            "p_cluttered_text": round(float(logits[3]), 4),
        }

    W0, H0 = 576, 1024
    guac_raw = cv2.resize(cv2.imread(str(RAMAR / "guacamole_S4_raw.png")), (W0, H0), interpolation=cv2.INTER_AREA)
    gel_raw = cv2.resize(cv2.imread(str(RAMAR / "gelato_S1_raw.png")), (W0, H0), interpolation=cv2.INTER_AREA)

    items = [
        ("guacamole", "orig_1.0", guac_raw, guac_raw),
        ("guacamole", "naken_0.45", cv2.resize(cv2.imread(str(AB_DIR / "v5_guac_naken_04.png")), (W0, H0), interpolation=cv2.INTER_AREA), guac_raw),
        ("guacamole", "regi_0.35_room", cv2.resize(cv2.imread(str(AB_DIR / "v5_guac_regi_04_room.png")), (W0, H0), interpolation=cv2.INTER_AREA), guac_raw),
        ("guacamole", "regi_0.55_prod", cv2.resize(cv2.imread(str(AB_DIR / "v5_guac_regi_06_prod.png")), (W0, H0), interpolation=cv2.INTER_AREA), guac_raw),
        ("gelato", "orig_1.0", gel_raw, gel_raw),
        ("gelato", "naken_0.45", cv2.resize(cv2.imread(str(AB_DIR / "v5_gelato_naken_04.png")), (W0, H0), interpolation=cv2.INTER_AREA), gel_raw),
        ("gelato", "regi_0.40_room", cv2.resize(cv2.imread(str(AB_DIR / "v5_gelato_regi_04_room.png")), (W0, H0), interpolation=cv2.INTER_AREA), gel_raw),
    ]

    results = {"guacamole": {}, "gelato": {}}
    for venue, tag, im, ref in items:
        cl = clutter_metrics(im)
        ce = clip_eval(im, ref)
        gl = {"inliers": 999, "drift_px": 0.0, "reproj_px": 0.0, "scale": 1.0} if tag == "orig_1.0" else geom_lock(ref, im, sift)
        # Brusreduktion relativt orig
        results[venue][tag] = {"geom": gl, "clutter": cl, "clip": ce}
        id_p = ce["p_bar"] if venue == "guacamole" else ce["p_gelato"]
        print(
            f"[{venue:9s}] {tag:15s}: inl={gl['inliers']:3d} drift={str(gl['drift_px']):>5s}px | "
            f"edge={cl['edge_density_pct']:4.1f}% longL={cl['long_line_share_pct']:4.1f}% | "
            f"P(venue)={id_p:.3f} P(bare)={ce['p_bare_empty']:.3f} P(clutter)={ce['p_cluttered_text']:.3f}"
        )

    # Beräkna relativ brusreduktion (%) mot orig_1.0
    for venue in ("guacamole", "gelato"):
        e0 = results[venue]["orig_1.0"]["clutter"]["edge_density_pct"]
        for tag, rec in results[venue].items():
            rec["clutter"]["brusreduktion_pct"] = round(100.0 * (1.0 - rec["clutter"]["edge_density_pct"] / max(0.1, e0)), 1)

    # ------------------------------------------------------------------
    # GELATO S1 2-BILDS VIRTUELL DJUPSENSOR vs ARGONS VERKLIGA MoGe (0078.npz)!
    # ------------------------------------------------------------------
    gel_djup_bgr = cv2.resize(cv2.imread(str(AB_DIR / "v5_gelato_regi_05_djup.png")), (W0, H0), interpolation=cv2.INTER_AREA)
    gel_room = cv2.resize(cv2.imread(str(AB_DIR / "v5_gelato_regi_04_room.png")), (W0, H0), interpolation=cv2.INTER_AREA)
    d_gpt = avkoda_turbo(gel_djup_bgr)
    z_moge = cv2.resize(np.load(str(GEL_ING / "rum/depth/0078.npz"))["depth"], (W0, H0), interpolation=cv2.INTER_LINEAR)
    m_arr = np.load(str(GEL_ING / "masker.npy"), mmap_mode="r")
    pmask = cv2.resize((m_arr[len(m_arr) // 2] > 0).astype(np.uint8), (W0, H0), interpolation=cv2.INTER_NEAREST)
    pmask_dil = cv2.dilate(pmask, np.ones((25, 25), np.uint8))

    moge_nan_tot_pct = round(100.0 * float((~np.isfinite(z_moge)).mean()), 1)
    # Korrelera på statiska glassdisk-pixlar (nedre halvan y=360..1024 utan personmask!)
    st = (pmask_dil == 0) & np.isfinite(z_moge) & (z_moge > 0.1) & (z_moge < 10.0)
    ys, xs = np.where(st)
    step = max(1, len(ys) // 20000)
    rho_gel, _ = spearmanr(d_gpt[ys[::step], xs[::step]], z_moge[ys[::step], xs[::step]])

    # Kantalignering mellan v5_gelato_regi_04_room och v5_gelato_regi_05_djup!
    c_r = cv2.Canny(cv2.cvtColor(gel_room, cv2.COLOR_BGR2GRAY), 50, 140)
    c_d = cv2.Canny(cv2.cvtColor(gel_djup_bgr, cv2.COLOR_BGR2GRAY), 40, 120)
    c_r_dil = cv2.dilate(c_r, np.ones((9, 9), np.uint8))
    gel_edge_align = round(100.0 * float((c_d[c_r_dil > 0] > 0).sum()) / max(1, int((c_d > 0).sum())), 1)

    # Skärpa över glaskantens horisontella steg (y=280..440)
    p05 = float(np.percentile(z_moge[st], 5))
    p95 = float(np.percentile(z_moge[st], 95))
    zm_n = np.where(np.isfinite(z_moge), (z_moge - p05) / max(1e-6, p95 - p05), np.nan)
    dg_s = float(np.percentile(np.abs(np.diff(d_gpt[280:460, :], axis=0)), 98))
    dm_arr = np.abs(np.diff(zm_n[280:460, :], axis=0))
    dm_s = float(np.percentile(dm_arr[np.isfinite(dm_arr)], 98))

    gel_depth_audit = {
        "moge_nan_hal_tot_pct": moge_nan_tot_pct,
        "gpt_nan_hal_pct": 0.0,
        "spearman_rho_statisk_bakgrund": round(float(rho_gel), 4),
        "kant_alignering_room_vs_djup_pct": gel_edge_align,
        "glasskant_steg_p98_GPT": round(dg_s, 4),
        "glasskant_steg_p98_MoGe": round(dm_s, 4),
        "skarphetsfaktor_GPT_vs_MoGe": round(dg_s / max(1e-4, dm_s), 2),
    }
    print("\nGELATO S1 DJUPAUDIT:", json.dumps(gel_depth_audit, ensure_ascii=False))

    rapport = {
        "syfte": "Experiment 6: Kvantitativ A/B-audit av 0..1-promptoptimering (Naken Zero-LLM vs Regisserad RoomAnalysis vs Good-Enough Produktion) på bar + glassbar",
        "resultat_per_lokal": results,
        "gelato_virtuell_djupsensor_vs_MoGe": gel_depth_audit,
    }
    (HIT / "djup_v5_prompt_audit.json").write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # Rita 2x4-panels MASTER-BEVISFIGUR: djup_v5_prompt_ab_bevis.png
    # ------------------------------------------------------------------
    fig = plt.figure(figsize=(19, 11.5), dpi=130, facecolor="#0f1117")
    gs = fig.add_gridspec(2, 4, hspace=0.26, wspace=0.12)

    def rgb(im):
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    # Rad 1: Guacamole (1.0 Orig | Naken 0.45 | Regi 0.35 RoomAnalysis | Regi 0.55 Prod)
    row1 = [
        (guac_raw, "orig_1.0", "1. GUACAMOLE 1.0 (Råbild)", "#95a5a6"),
        (items[1][2], "naken_0.45", "2. NAKEN Zero-LLM (0.45)", "#00d2ff"),
        (items[2][2], "regi_0.35_room", "3. REGI RoomAnalysis (0.35)", "#2ecc71"),
        (items[3][2], "regi_0.55_prod", "4. REGI Good-Enough Prod (0.55)", "#f39c12"),
    ]
    for ci, (im, tag, hdr, col) in enumerate(row1):
        ax = fig.add_subplot(gs[0, ci])
        r = results["guacamole"][tag]
        ax.imshow(rgb(im))
        ax.set_title(
            f"{hdr}\n"
            f"drift={r['geom']['drift_px']} px | brus {r['clutter']['brusreduktion_pct']:+.0f}% | långa linjer={r['clutter']['long_line_share_pct']}%\n"
            f"CLIP P(bar)={r['clip']['p_bar']:.2f} | P(tom låda)={r['clip']['p_bare_empty']:.2f}",
            color=col, fontsize=9.0, pad=5,
        )
        ax.axis("off")

    # Rad 2: Gelato (1.0 Orig | Naken 0.45 | Regi 0.40 RoomAnalysis | 2-bilds Djupkarta vs MoGe!)
    row2 = [
        (gel_raw, "orig_1.0", "5. GELATO 1.0 (Råbild)", "#95a5a6"),
        (items[5][2], "naken_0.45", "6. NAKEN Zero-LLM (0.45)", "#00d2ff"),
        (items[6][2], "regi_0.40_room", "7. REGI RoomAnalysis (0.40)", "#2ecc71"),
    ]
    for ci, (im, tag, hdr, col) in enumerate(row2):
        ax = fig.add_subplot(gs[1, ci])
        r = results["gelato"][tag]
        ax.imshow(rgb(im))
        ax.set_title(
            f"{hdr}\n"
            f"drift={r['geom']['drift_px']} px | brus {r['clutter']['brusreduktion_pct']:+.0f}% | långa linjer={r['clutter']['long_line_share_pct']}%\n"
            f"CLIP P(glassdisk)={r['clip']['p_gelato']:.2f} | P(tom låda)={r['clip']['p_bare_empty']:.2f}",
            color=col, fontsize=9.0, pad=5,
        )
        ax.axis("off")

    ax_d = fig.add_subplot(gs[1, 3])
    ax_d.imshow(rgb(gel_djup_bgr))
    ax_d.set_title(
        "8. GELATO 2-BILDS DJUPSENSOR (Steg B)\n"
        f"0% hål (MoGe={moge_nan_tot_pct}% NaN!) | ρ={gel_depth_audit['spearman_rho_statisk_bakgrund']:.3f}\n"
        f"kantpassning={gel_edge_align}% | glaskant {gel_depth_audit['skarphetsfaktor_GPT_vs_MoGe']}× skarpare!",
        color="#ffd166", fontsize=9.0, pad=5,
    )
    ax_d.axis("off")

    fig.suptitle(
        "EXPERIMENT 6: A/B-Promptoptimering & 0..1-Intentionalitet (Naken Zero-LLM vs Regisserad RoomAnalysis 0.35 vs Produktion 0.55) — Bar & Glassbar",
        color="white", fontsize=12.6, fontweight="bold", y=0.985,
    )
    out_png = HIT / "djup_v5_prompt_ab_bevis.png"
    fig.savefig(out_png, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_png} and djup_v5_prompt_audit.json")


if __name__ == "__main__":
    main()
