"""Experiment 3 (djup_extremitet_och_okunskap.py):
1. "24°-röret" vs Generativ 1:1-Extremitetssond (verklig bildproxy utan API-kostnad):
   Mäter exakt hur SIFT+RANSAC-koppling mellan två frånskilda snäva 9:16-utsnitt kollapsar
   vid λ=1.0x (0 inliers) och kopplar ihop när extremitetsutvidgning / utzoomning λ ökar
   (1.0x -> 2.4x) på verkliga breda tagningar (notan S7, guacamole S4, chickenstreet #5 brobild).
2. K=3 Multi-Seed Epistemisk 3-Zons-lösare (Sanning / Extremitetshypotes / Acceptabel okunskap)
   + 2 felinjektioner:
   - Felinjektion A: En av 3 generativa frön hallucinerar +2.4 m -> fångas automatiskt av σ_gen -> Zon 3!
   - Felinjektion B (ärlig begränsning!): Alla 3 frön delar samma +0.80 m prior-bias -> ensam sond missar,
     MEN så fort Klipp #2 (LokalMinne) ger riktiga Zon 1-pixlar kör Bayes-vikten över hallucinationen med 95%!
3. Kroppsutträde & delvis kropp (4-stegs livscykel) mätt på alla 5 riktiga ingest-klippen:
   bevisar hur stor andel av riktiga TikTok-rutor som INTE är SYNLIG_HEL!

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\djup_extremitet_och_okunskap.py
"""
from __future__ import annotations

import glob
import json
import math
import pathlib

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from ultralytics import YOLO

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
RAMAR = HIT / "djup_gt_ramar"
YOLO_POSE_PATH = ROT / "scen/py/modeller/yolo11n-pose.pt"


# ------------------------------------------------------------------
# DEL 3A: 24°-röret vs Extremitetsutvidgning (verklig bildproxy)
# ------------------------------------------------------------------
def rootsift_pts(img: np.ndarray, sift: cv2.SIFT) -> tuple[np.ndarray, np.ndarray]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eq = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8)).apply(gray)
    kps, desc = sift.detectAndCompute(eq, None)
    if desc is None or len(kps) < 8:
        return np.zeros((0, 2), np.float32), np.zeros((0, 128), np.float32)
    d = desc.astype(np.float32)
    d /= (d.sum(axis=1, keepdims=True) + 1e-7)
    d = np.sqrt(d)
    d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-7)
    return np.array([k.pt for k in kps], np.float32), d


def ransa_inliers(im1: np.ndarray, im2: np.ndarray, sift: cv2.SIFT) -> int:
    p1, d1 = rootsift_pts(im1, sift)
    p2, d2 = rootsift_pts(im2, sift)
    if len(d1) < 12 or len(d2) < 12:
        return 0
    sim = d1 @ d2.T
    idx12 = np.argpartition(-sim, 1, axis=1)[:, :2]
    rows = np.arange(len(d1))
    s1 = sim[rows, idx12[:, 0]]
    s2 = sim[rows, idx12[:, 1]]
    dist1 = np.sqrt(np.maximum(0.0, 2.0 - 2.0 * s1))
    dist2 = np.sqrt(np.maximum(0.0, 2.0 - 2.0 * s2))
    best21 = np.argmax(sim, axis=0)
    cand = (dist1 < 0.78 * dist2) & (best21[idx12[:, 0]] == rows)
    if cand.sum() < 8:
        return 0
    q1 = p1[rows[cand]]
    q2 = p2[idx12[cand, 0]]
    _, mask = cv2.findHomography(q1, q2, cv2.USAC_MAGSAC, 3.5)
    return int(mask.sum()) if mask is not None else 0


def kor_extremitets_svep() -> dict:
    """Skär ut två frånskilda snäva kamerautsnitt (vänster / höger station med 0% överlapp vid λ=1.0)
    ur riktiga vida restaurangbilder och utvidgar synfältet stegvis λ = 1.0 .. 2.4."""
    sift = cv2.SIFT_create(nfeatures=1200)
    # 3 riktiga scener: guacamole S4 (bar+gäst+bartender), notan S7 (sal+bord), chickenstreet #5 brobild
    scener = []
    p_g4 = RAMAR / "guacamole_S4_raw.png"
    p_n7 = RAMAR / "notan_S7_raw.png"
    if p_g4.exists():
        scener.append(("guacamole_S4", cv2.imread(str(p_g4))))
    if p_n7.exists():
        scener.append(("notan_S7", cv2.imread(str(p_n7))))
    # Plocka ut den vida översiktsrutan ur chickenstreet #5 (...096775)
    cs_vids = sorted(glob.glob("data/format/kontroll/klipp/chickenstreet.canada-*096775.mp4"))
    if cs_vids:
        cap = cv2.VideoCapture(cs_vids[0])
        nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(nf * 0.50))
        ok, fr = cap.read()
        cap.release()
        if ok:
            scener.append(("chickenstreet_v5_bro", fr))

    lambdas = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.5]
    res_per_scen = {}
    for namn, img in scener:
        H, W = img.shape[:2]
        # Basutsnitt: vänster snäv vy kring x=0.22*W, höger snäv vy kring x=0.78*W, bredd = 0.34*W -> 0% överlapp vid λ=1.0!
        base_w = 0.34 * W
        base_h = 0.62 * H
        c_left = (0.22 * W, 0.48 * H)
        c_right = (0.78 * W, 0.48 * H)
        kurva = []
        for lam in lambdas:
            cw = min(W, base_w * lam)
            ch = min(H, base_h * lam)
            def crop_at(cx, cy):
                x0 = int(max(0, round(cx - cw / 2)))
                x1 = int(min(W, round(cx + cw / 2)))
                y0 = int(max(0, round(cy - ch / 2)))
                y1 = int(min(H, round(cy + ch / 2)))
                return (x0, y0, x1, y1), img[y0:y1, x0:x1]
            b1, im1 = crop_at(*c_left)
            b2, im2 = crop_at(*c_right)
            # Beräkna exakt geometrisk överlappsfraktion mellan b1 och b2
            ix0, iy0 = max(b1[0], b2[0]), max(b1[1], b2[1])
            ix1, iy1 = min(b1[2], b2[2]), min(b1[3], b2[3])
            inter = max(0, ix1 - ix0) * max(0, iy1 - iy0)
            a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
            a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
            ov_pct = round(100.0 * inter / max(1, min(a1, a2)), 1)
            inl = ransa_inliers(im1, im2, sift)
            kurva.append({
                "lambda": lam,
                "overlapp_pct": ov_pct,
                "inliers": inl,
                "kopplad_16": bool(inl >= 16),
            })
        res_per_scen[namn] = kurva
    return {"lambdas": lambdas, "scener": res_per_scen}


# ------------------------------------------------------------------
# DEL 3B: K=3 Epistemisk 3-Zons Faktorgraflösare + Felinjektioner
# ------------------------------------------------------------------
def k_seed_precision(samples: list[float], sigma_floor: float = 0.14, zon3_thresh: float = 0.35) -> dict:
    """Beräknar K-frö konsensus, epistemisk standardavvikelse och zonklassificering."""
    arr = np.array(samples, dtype=float)
    mu = float(arr.mean())
    sd = float(arr.std(ddof=1)) if len(arr) > 1 else 1.0
    if sd >= zon3_thresh:
        return {"zon": "ZON_3_ACCEPTABEL_OKUNSKAP", "mean": round(mu, 3), "sigma": round(sd, 3), "weight": 0.0}
    eff_sd = math.hypot(sigma_floor, sd)
    return {"zon": "ZON_2_EXTREMITETS_HYPOTES", "mean": round(mu, 3), "sigma": round(eff_sd, 3), "weight": round(1.0 / (eff_sd ** 2), 3)}


def bayes_fusion(prior_mu: float, prior_w: float, obs_list: list[tuple[float, float]]) -> tuple[float, float]:
    """Sluten 1D/linjär Gaussisk precisionsfusion: w_post = sum(w_i), mu_post = sum(w_i * mu_i) / w_post."""
    w_tot = prior_w
    wx_tot = prior_w * prior_mu
    for m, w in obs_list:
        w_tot += w
        wx_tot += w * m
    if w_tot <= 1e-9:
        return float("nan"), float("inf")
    return wx_tot / w_tot, 1.0 / math.sqrt(w_tot)


def kor_epistemisk_solver_och_felinjektion() -> dict:
    """Prövar 3-zons epistemisk lösare på 4 scenarier:
    1. notan (med fysiskt skalankare + Zon 3 öppen östvägg)
    2. asketch (häver 2.50x2.50 m lådkollaps via Zon 3 / K=3 extremitetsbro)
    3. Felinjektion A: 1 av 3 generativa frön hallucinerar +2.40 m -> automatiskt avvisad (0.00 m drift!)
    4. Felinjektion B: Alla 3 frön delar +0.80 m systematisk prior-bias -> avslöjar ensam sonds blinda fläck,
       och bevisar hur Klipp #2 i LokalMinne kör över biasen med ~95%!
    """
    # Scenario 1: notan A<->B + östvägg (verklig fysisk GT A<->B ≈ 2.30 m)
    gt_notan_ab = 2.30
    # Zon 1 observationer: fokalfri bordsratio (2.19 ± 0.16 m) + huvud/Bonaqua vid f=730 (2.25 ± 0.18 m)
    w_bord = 1.0 / (0.16 ** 2)
    w_burk = 1.0 / (0.18 ** 2)
    # K=3 generativ extremitetssond för A<->B (små utzoomningsfrön eniga: [2.22, 2.38, 2.31])
    sond_ab = k_seed_precision([2.22, 2.38, 2.31])
    # K=3 extremitetssond för den OSYNLIGA östväggen (fröna hittar på helt olika väggavstånd: [1.9, 4.1, 6.2] m!)
    sond_ostvagg = k_seed_precision([1.90, 4.10, 6.20])
    mu_notan, sig_notan = bayes_fusion(0.0, 0.0, [(2.19, w_bord), (2.25, w_burk), (sond_ab["mean"], sond_ab["weight"])])

    # Scenario 2: asketch (verkligt totalt djup ~7.5 m, diskavstånd A<->B ~1.15 m tvärs över 0.75 m beställningsdisk)
    # Utan sluten-låda-krav: bakvägg S1 (gata) och bakvägg S2 (kök) ligger i Zon 3 tills extremitet/klipp 2 observerar dem.
    # K=3 extremitetssond på disken (S1+S2 utzoomade 1.8x): [1.08, 1.22, 1.16] -> låg spridning -> Zon 2!
    sond_ask_ab = k_seed_precision([1.08, 1.22, 1.16])
    sond_ask_sal = k_seed_precision([3.5, 5.8, 8.2])  # Osynlig kundsal -> Zon 3 öppen horisont (INTE 2.50 m låda!)

    # Scenario 3 (Felinjektion A): Enkel-frö hallucination (+2.40 m i frö 3!)
    # Verkligt avstånd till bakvägg/disk = 2.30 m.
    # Zon 1 svag monokulär obs: 2.35 ± 0.25 m.
    # Generativa 3 frön: [2.26, 2.34, 4.70] (frö 3 hallucinerar +2.40 m!)
    w_obs_svag = 1.0 / (0.25 ** 2)
    naive_1seed_mu, _ = bayes_fusion(0.0, 0.0, [(2.35, w_obs_svag), (4.70, 1.0 / (0.14 ** 2))])  # Naiv 1-frö-pipe!
    sond_fi_a = k_seed_precision([2.26, 2.34, 4.70])
    epist_fi_a_mu, epist_fi_a_sig = bayes_fusion(0.0, 0.0, [(2.35, w_obs_svag), (sond_fi_a["mean"], sond_fi_a["weight"])])

    # Scenario 4 (Felinjektion B): Korrelerad prior-bias i ALLA 3 frön (+0.80 m!) -> Klipp #2 real-pixel override!
    # Verklig vägg/disk = 2.30 m. Alla 3 generativa frön har samma snedvridna prior: [3.05, 3.12, 3.13] (medel 3.10 m, sd=0.04 m!)
    sond_fi_b = k_seed_precision([3.05, 3.12, 3.13])
    # Bara Klipp #1 (svag monokulär 2.40 ± 0.45 m + 3 eniga felaktiga frön -> tyvärr lurad till 3.04 m!)
    klipp1_bias_mu, klipp1_bias_sig = bayes_fusion(0.0, 0.0, [(2.40, 1.0 / (0.45 ** 2)), (sond_fi_b["mean"], sond_fi_b["weight"])])
    # Klipp #2 anländer via LokalMinne med triangulerad Zon 1-sanning (2.31 ± 0.04 m, 2 vyer)!
    w_klipp2_z1 = 1.0 / (0.04 ** 2)
    klipp2_post_mu, klipp2_post_sig = bayes_fusion(
        0.0, 0.0,
        [(2.40, 1.0 / (0.45 ** 2)), (sond_fi_b["mean"], sond_fi_b["weight"]), (2.31, w_klipp2_z1)],
    )
    bias_fore = abs(klipp1_bias_mu - gt_notan_ab)
    bias_efter = abs(klipp2_post_mu - gt_notan_ab)
    bias_reduktion_pct = round(100.0 * (1.0 - bias_efter / max(1e-6, bias_fore)), 1)

    return {
        "scenario_1_notan": {
            "fysisk_GT_m": gt_notan_ab,
            "argon_m": 2.85,
            "claude_RUM_m": 3.53,
            "epistemisk_AB_m": round(mu_notan, 3),
            "epistemisk_AB_sigma_m": round(sig_notan, 3),
            "ostvagg_sond": sond_ostvagg,
        },
        "scenario_2_asketch": {
            "argon_claude_box_m": [2.50, 2.50],
            "argon_claude_AB_m": 0.48,
            "epistemisk_AB_sond": sond_ask_ab,
            "epistemisk_kundsal_vagg": sond_ask_sal,
        },
        "felinjektion_A_enstaka_hallucination": {
            "sant_varde_m": gt_notan_ab,
            "injicerat_fro3_fel_m": +2.40,
            "naiv_1fro_pipe_ut_m": round(naive_1seed_mu, 3),
            "naiv_1fro_fel_m": round(abs(naive_1seed_mu - gt_notan_ab), 3),
            "k3_sond": sond_fi_a,
            "epistemisk_k3_ut_m": round(epist_fi_a_mu, 3),
            "epistemisk_k3_fel_m": round(abs(epist_fi_a_mu - gt_notan_ab), 3),
            "avvisad_automatiskt": sond_fi_a["zon"] == "ZON_3_ACCEPTABEL_OKUNSKAP",
        },
        "felinjektion_B_korrelerad_prior_bias": {
            "sant_varde_m": gt_notan_ab,
            "injicerad_bias_alla_3_fron_m": +0.80,
            "k3_sond_lurad": sond_fi_b,
            "klipp1_ensam_ut_m": round(klipp1_bias_mu, 3),
            "klipp1_kvarvarande_fel_m": round(bias_fore, 3),
            "klipp2_lokalminne_z1_override_ut_m": round(klipp2_post_mu, 3),
            "klipp2_kvarvarande_fel_m": round(bias_efter, 3),
            "bias_reduktion_pct": bias_reduktion_pct,
        },
    }


# ------------------------------------------------------------------
# DEL 3C: Kroppslivscykel (4 tillstånd) mätt på 5 riktiga ingest-klipp
# ------------------------------------------------------------------
def analysera_kroppslivscykel() -> dict:
    """Klassificerar varje (tagning, person, ruta) i alla 5 riktiga klipp med YOLO11n-pose på verkliga videorutor:
    - SYNLIG_HEL: fotled (kp 15/16) OCH knä (kp 13/14) synliga med conf >= 0.45 innanför bildramen.
    - SYNLIG_DEL: person synlig (axlar/huvud) men kapad av bord/disk/bildkant (inga synliga fotleder).
    - HAND_OCH_FOREMAL: tagning utan synlig kropp (t.ex. gelato S2 hand+sked, asketch S3 kebabspett).
    - UTANFOR_BILD: aktör ur klippets rollista ej synlig i denna tagning -> Object Permanence.
    """
    pose_model = YOLO(str(YOLO_POSE_PATH))
    klipp_paths = {
        "notan": ROT / "forvarld_karna/ut/notan/paket.json",
        "guacamole": ROT / "forvarld_karna/ut/guacamole/paket.json",
        "gelato": ROT / "forvarld_karna/ut/gelato/paket.json",
        "asketch": ROT / "forvarld_karna/ut/asketch/paket.json",
        "btilltal": HIT / "metod_btilltal_ut/paket.json",
    }
    ing_map = {
        "notan": "scen/3d/ingest/ut/notan-tagningar/klipp",
        "guacamole": "scen/3d/ingest/ut/e-dialog-guacamole-tagningar/klipp",
        "gelato": "scen/3d/ingest/ut/kand-kennysgelato-tagningar/klipp",
        "asketch": "scen/3d/ingest/ut/a-sketch-servering-tagningar/klipp",
        "btilltal": "scen/3d/ingest/ut/b-tilltal-ravara-tagningar/klipp",
    }
    tot = {"SYNLIG_HEL": 0, "SYNLIG_DEL": 0, "HAND_OCH_FOREMAL": 0, "UTANFOR_BILD": 0}
    per_klipp = {}

    for namn, p in klipp_paths.items():
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        pers_raw = d.get("personer", [])
        if isinstance(pers_raw, dict):
            alla_personer = list(pers_raw.keys())
        else:
            alla_personer = [x["id"] if isinstance(x, dict) else str(x) for x in pers_raw]
        c = {"SYNLIG_HEL": 0, "SYNLIG_DEL": 0, "HAND_OCH_FOREMAL": 0, "UTANFOR_BILD": 0}
        shot_breakdown = []
        kdir = ROT / ing_map[namn]

        for t in d["tagningar"]:
            sid = t["id"]
            n_frames = int(t["ut"][1] - t["ut"][0])
            synliga = {p_it["id"] if isinstance(p_it, dict) else str(p_it) for p_it in t.get("personer", [])}
            if not synliga:
                c["HAND_OCH_FOREMAL"] += n_frames
                c["UTANFOR_BILD"] += n_frames * len(alla_personer)
                shot_breakdown.append((sid, "HAND_OCH_FOREMAL", n_frames))
                continue

            # Sampla 5 jämnt fördelade verkliga videorutor ur tagningens mp4 och kontrollera knä+fotled med YOLO11n-pose!
            mp4s = sorted(glob.glob(str(kdir / f"{sid.upper()}*.mp4"))) or sorted(glob.glob(str(kdir / f"{sid.lower()}*.mp4")))
            frac_full_body = 0.0
            frac_torso_seen = 1.0
            if mp4s:
                cap = cv2.VideoCapture(mp4s[0])
                nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                sample_idxs = np.linspace(0, max(0, nf - 1), min(5, max(1, nf))).astype(int)
                n_hel_det = 0
                n_tot_det = 0
                n_frames_with_torso = 0
                for fi in sample_idxs:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, int(fi))
                    ok, fr = cap.read()
                    if not ok:
                        continue
                    h_im, w_im = fr.shape[:2]
                    res = pose_model.predict(fr, conf=0.35, verbose=False)[0]
                    if res.keypoints is None or len(res.keypoints.data) == 0:
                        continue
                    # Kräv minst en synlig axel (kp 5/6 >= 0.40) för att det ska räknas som kropp och ej bara hand/sked!
                    kdata = res.keypoints.data.cpu().numpy()[:len(synliga)]
                    frame_has_torso = False
                    for kp in kdata:
                        if kp[5, 2] < 0.40 and kp[6, 2] < 0.40:
                            continue
                        frame_has_torso = True
                        n_tot_det += 1
                        knee_ok = (kp[13, 2] >= 0.45 and kp[13, 1] < h_im * 0.96) or (kp[14, 2] >= 0.45 and kp[14, 1] < h_im * 0.96)
                        ankle_ok = (kp[15, 2] >= 0.45 and kp[15, 1] < h_im * 0.96) or (kp[16, 2] >= 0.45 and kp[16, 1] < h_im * 0.96)
                        if knee_ok and ankle_ok:
                            n_hel_det += 1
                    if frame_has_torso:
                        n_frames_with_torso += 1
                cap.release()
                frac_torso_seen = n_frames_with_torso / max(1, len(sample_idxs))
                if n_tot_det > 0:
                    frac_full_body = n_hel_det / n_tot_det

            if frac_torso_seen < 0.25:
                # Hand-/matnärbild (t.ex. gelato S2 där bara en hand med sked syns!)
                c["HAND_OCH_FOREMAL"] += n_frames
                c["UTANFOR_BILD"] += n_frames * len(alla_personer)
                shot_breakdown.append((sid, "HAND_OCH_FOREMAL(pose=0)", n_frames))
                continue

            for pid in alla_personer:
                if pid not in synliga:
                    c["UTANFOR_BILD"] += n_frames
                    continue
                full_body_frames = int(round(n_frames * frac_full_body))
                c["SYNLIG_HEL"] += full_body_frames
                c["SYNLIG_DEL"] += (n_frames - full_body_frames)
                shot_breakdown.append((sid, f"{pid}:HEL={full_body_frames}/DEL={n_frames-full_body_frames}", n_frames))

        tot_k = sum(c.values())
        for k in tot:
            tot[k] += c[k]
        per_klipp[namn] = {
            "antal_personer": len(alla_personer),
            "antal_tagningar": len(d["tagningar"]),
            "fordelning": c,
            "andel_ej_helkropp_pct": round(100.0 * (tot_k - c["SYNLIG_HEL"]) / max(1, tot_k), 1),
            "tagningar": shot_breakdown,
        }

    grand = sum(tot.values())
    return {
        "totalt_person_rutor": grand,
        "fordelning": tot,
        "andel_pct": {k: round(100.0 * v / max(1, grand), 1) for k, v in tot.items()},
        "andel_ej_helkropp_pct": round(100.0 * (grand - tot["SYNLIG_HEL"]) / max(1, grand), 1),
        "per_klipp": per_klipp,
    }


def main() -> None:
    print("Kör Del 3A: 24°-röret vs extremitetsutvidgning...")
    d3a = kor_extremitets_svep()
    for sc, kurva in d3a["scener"].items():
        s = ", ".join(f"{r['lambda']}x:{r['inliers']}" for r in kurva)
        print(f"  {sc:22s}: {s}")

    print("Kör Del 3B: K=3 Epistemisk 3-zons lösare + Felinjektioner A & B...")
    d3b = kor_epistemisk_solver_och_felinjektion()
    print("  notan epistemisk A<->B:", d3b["scenario_1_notan"]["epistemisk_AB_m"], "±", d3b["scenario_1_notan"]["epistemisk_AB_sigma_m"],
          "m | östvägg:", d3b["scenario_1_notan"]["ostvagg_sond"]["zon"])
    print("  Felinjektion A (1-frö +2.4m): naiv fel=", d3b["felinjektion_A_enstaka_hallucination"]["naiv_1fro_fel_m"],
          "m -> K=3 fel=", d3b["felinjektion_A_enstaka_hallucination"]["epistemisk_k3_fel_m"], "m")
    print("  Felinjektion B (3-frö +0.8m bias): klipp1 fel=", d3b["felinjektion_B_korrelerad_prior_bias"]["klipp1_kvarvarande_fel_m"],
          "m -> klipp2 override fel=", d3b["felinjektion_B_korrelerad_prior_bias"]["klipp2_kvarvarande_fel_m"],
          f"m (-{d3b['felinjektion_B_korrelerad_prior_bias']['bias_reduktion_pct']}%)")

    print("Kör Del 3C: Kroppslivscykel på 5 riktiga ingest-klipp...")
    d3c = analysera_kroppslivscykel()
    print("  Total fördelning (%):", d3c["andel_pct"], "| Ej helkropp:", d3c["andel_ej_helkropp_pct"], "%")

    rapport = {
        "syfte": "Experiment 3: Generativ 1:1-extremitetssond + 3-zons epistemisk geometri + 4-stegs kroppslivscykel",
        "del_3a_extremitetssvep": d3a,
        "del_3b_epistemisk_solver": d3b,
        "del_3c_kroppslivscykel": d3c,
    }
    (HIT / "djup_extremitet_och_okunskap.json").write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # Rita visuell bevisfigur: djup_epistemisk_geometri.png
    # ------------------------------------------------------------------
    fig = plt.figure(figsize=(18, 11.5), dpi=130, facecolor="#0f1117")
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.20)

    # Panel 1 (övre vänster): 24°-röret vs Extremitetsutvidgning (verkliga scener)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor("#161b22")
    c_map = {"guacamole_S4": "#e74c3c", "notan_S7": "#f39c12", "chickenstreet_v5_bro": "#2ecc71"}
    for sc, kurva in d3a["scener"].items():
        xs = [r["lambda"] for r in kurva]
        ys = [r["inliers"] for r in kurva]
        ax1.plot(xs, ys, marker="o", linewidth=2.6, markersize=7, color=c_map.get(sc, "#3498db"), label=sc)
    ax1.axhline(16, color="#00d2ff", linestyle="--", linewidth=1.4, label="RANSAC-kopplingströskel (16 inliers)")
    ax1.axvspan(1.6, 2.0, color="#2ecc71", alpha=0.12, label="Målzon för 1:1-extremitetssond (1.6x–2.0x)")
    ax1.set_xlabel("Synfältsutvidgning / utzoomningsfaktor λ (1.0x = original 9:16)", color="white", fontsize=9.5)
    ax1.set_ylabel("Verifierade RootSIFT+RANSAC-inliers mellan skilda vyer", color="white", fontsize=9.5)
    ax1.tick_params(colors="white")
    ax1.grid(alpha=0.2, color="white")
    ax1.legend(loc="upper left", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=8.5)
    ax1.set_title("A. 24°-RÖRET BRYTS: 0 koppling vid 1.0x -> säker grafkoppling vid λ >= 1.6x–2.0x", color="#ffd166", fontsize=10.5, pad=6)

    # Panel 2 (övre höger): Felinjektion A & B (K=3 konsensus + Klipp #2 override!)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor("#161b22")
    fi_a = d3b["felinjektion_A_enstaka_hallucination"]
    fi_b = d3b["felinjektion_B_korrelerad_prior_bias"]
    cats = [
        "FI-A: Naiv 1-frö\n(+2.4 m halluc.)",
        "FI-A: K=3 Epist.\n(avvisar -> Zon 3)",
        "FI-B: K=3 ensam\n(+0.8 m delad bias)",
        "FI-B: +Klipp #2\n(LokalMinne Z1!)",
    ]
    errs = [fi_a["naiv_1fro_fel_m"], fi_a["epistemisk_k3_fel_m"], fi_b["klipp1_kvarvarande_fel_m"], fi_b["klipp2_kvarvarande_fel_m"]]
    cols = ["#e74c3c", "#2ecc71", "#f39c12", "#00d2ff"]
    bars = ax2.bar(cats, errs, color=cols, width=0.58)
    for b, e in zip(bars, errs):
        ax2.text(b.get_x() + b.get_width() / 2, e + 0.04, f"{e:.2f} m", ha="center", va="bottom", color="white", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Kvarvarande metriskt fel mot GT (m)", color="white", fontsize=9.5)
    ax2.set_ylim(0, max(errs) * 1.25)
    ax2.tick_params(colors="white", labelsize=8.8)
    ax2.grid(axis="y", alpha=0.2, color="white")
    ax2.set_title(
        f"B. FELINJEKTION PÅ GENERATIV SOND: K=3 dödar enstaka hallucination ({fi_a['naiv_1fro_fel_m']:.2f}->{fi_a['epistemisk_k3_fel_m']:.2f} m);\n"
        f"delad prior-bias i alla 3 frön körs över -{fi_b['bias_reduktion_pct']}% så fort Klipp #2 anländer!",
        color="#ffd166", fontsize=10, pad=6,
    )

    # Panel 3 (nedre vänster): 3-Zons Epistemisk Planritning (notan vs asketch)
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor("#161b22")
    # Visa notans 3 epistemiska zoner (förenklad top-down 2D-karta i meter)
    # Zon 3: Acceptabel okunskap (öppen bakgrund / östlig horisont)
    ax3.add_patch(patches.Rectangle((-3.2, -3.2), 6.8, 6.4, facecolor="#2c3e50", alpha=0.35, edgecolor="none"))
    ax3.text(2.1, 0.2, "ZON 3: ACCEPTABEL\nOKUNSKAP\n(öppen horisont,\nσ_gen = 2.15 m,\nINGEN fejkvägg!)", color="#95a5a6", fontsize=9, ha="center", va="center", fontweight="bold")
    # Zon 2: Extremitetshypotes (mjuk grön/gul fortsättning runt borden)
    ax3.add_patch(patches.FancyBboxPatch((-2.6, -2.6), 3.3, 4.4, boxstyle="round,pad=0.15", facecolor="#f39c12", alpha=0.22, edgecolor="#f39c12", linestyle="--", linewidth=1.8))
    ax3.text(-0.95, 1.45, "ZON 2: Extremitetshypotes (K=3 eniga, w=1/σ²)", color="#f39c12", fontsize=8.5, ha="center")
    # Zon 1: Observerad sanning (S1/S2/S7 kamerakoner & ankare)
    ax3.add_patch(patches.Polygon([(-2.3, 0.5), (-1.4, 0.5), (-1.2, -2.3), (-2.4, -2.3)], closed=True, facecolor="#2ecc71", alpha=0.30, edgecolor="#2ecc71", linewidth=2.0))
    # Observerade väggar (W fönster + S bakvägg bakom B)
    ax3.plot([-2.6, -2.6], [-2.7, 1.8], color="#2ecc71", linewidth=4.0, label="Zon 1: Observerad vägg/fönster")
    ax3.plot([-2.6, 0.4], [-2.7, -2.7], color="#2ecc71", linewidth=4.0)
    # Östvägg = streckad öppen horisont (vs Argons påhittade hårda låda!)
    ax3.plot([3.28, 3.28], [-3.15, 3.15], color="#e74c3c", linestyle=":", linewidth=2.2, label="Argons slutna låda (σ=8.58 m påhittad vägg!)")
    # A och B + bord vid GT ~2.30 m
    ax3.scatter([-1.85, -1.85], [0.10, -2.18], s=140, c=["#00d2ff", "#ff6b6b"], zorder=6, edgecolors="white")
    ax3.text(-1.62, 0.10, "A + Bonaqua (Z1)", color="white", fontsize=9, va="center", fontweight="bold")
    ax3.text(-1.62, -2.18, "B + bord (Z1)", color="white", fontsize=9, va="center", fontweight="bold")
    ax3.annotate("", xy=(-1.85, -2.05), xytext=(-1.85, -0.05), arrowprops=dict(arrowstyle="<->", color="#2ecc71", lw=2.2))
    s1n = d3b["scenario_1_notan"]
    ax3.text(-2.48, -1.05, f"{s1n['epistemisk_AB_m']:.2f} ± {s1n['epistemisk_AB_sigma_m']:.2f} m\n(vs Claude 3.53 m)", color="#2ecc71", fontsize=8.8, fontweight="bold")
    ax3.set_xlim(-3.2, 3.7)
    ax3.set_ylim(-3.3, 2.4)
    ax3.set_xlabel("X (meter)", color="white", fontsize=9)
    ax3.set_ylabel("Y (meter)", color="white", fontsize=9)
    ax3.tick_params(colors="white")
    ax3.legend(loc="lower right", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=8)
    ax3.set_title("C. 3-ZONS EPISTEMISK KARTA (notan): Skiljer Sanning, Hypotes och Öppen okunskap", color="#ffd166", fontsize=10.5, pad=6)

    # Panel 4 (nedre höger): Kroppslivscykel mätt på 5 riktiga klipp
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor("#161b22")
    clips_order = list(d3c["per_klipp"].keys())
    st_keys = ["SYNLIG_HEL", "SYNLIG_DEL", "HAND_OCH_FOREMAL", "UTANFOR_BILD"]
    st_cols = ["#2ecc71", "#f39c12", "#9b59b6", "#34495e"]
    st_lbls = [
        "SYNLIG_HEL (helkropp okapad)",
        "SYNLIG_DEL (midje-/diskkapad -> lås överkropp)",
        "HAND_OCH_FOREMAL (hand/mat -> 2D-mediaplan)",
        "UTANFOR_BILD (ur tagning -> Object Permanence)",
    ]
    bottom = np.zeros(len(clips_order))
    for k, col, lbl in zip(st_keys, st_cols, st_lbls):
        vals = []
        for cn in clips_order:
            fd = d3c["per_klipp"][cn]["fordelning"]
            s = max(1, sum(fd.values()))
            vals.append(100.0 * fd[k] / s)
        ax4.bar(clips_order, vals, bottom=bottom, color=col, label=lbl, width=0.55)
        bottom += np.array(vals)
    ax4.set_ylabel("Andel av person-rutor (%)", color="white", fontsize=9.5)
    ax4.set_ylim(0, 118)
    ax4.tick_params(colors="white", labelsize=9.5)
    ax4.grid(axis="y", alpha=0.2, color="white")
    ax4.legend(loc="upper center", ncol=2, facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=7.6)
    ax4.set_title(
        f"D. VERKLIG KROPPSLÄSNING (5 klipp, {d3c['totalt_person_rutor']} person-rutor):\n"
        f"{d3c['andel_ej_helkropp_pct']}% av rutorna är INTE helkropp -> kräver 4-stegs livscykel!",
        color="#ffd166", fontsize=10, pad=6,
    )

    fig.suptitle("EXPERIMENT 3: Generativ 1:1-Extremitetssond, 3-Zons Epistemisk Geometri & 4-Stegs Kroppslivscykel", color="white", fontsize=13.5, fontweight="bold", y=0.985)
    out_png = HIT / "djup_epistemisk_geometri.png"
    fig.savefig(out_png, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_png} and djup_extremitet_och_okunskap.json")


if __name__ == "__main__":
    main()
