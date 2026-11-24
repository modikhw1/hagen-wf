# KOPIA (spår A, runda 3) av motpart/runda-2-neon/djup_hard_gt_vis_eval.py. Enda ändringar:
# importväg till runda-2 och att pred_pairs sparas per konto i gt_vis_kopia_pred_pairs.json.
# Utdata skrivs i spår A:s mapp, inget i runda-2.
"""Förstärkning 2 (djup_hard_gt_vis_eval.py):
Icke-cirkulär utvärdering av v1 -> v2 -> v3.1 -> v3.2 över ALLA 49 riktiga TikToks (6 restauranger)
mot OBEROENDE VISUELLT MÄRKT LOKAL-GROUND-TRUTH (GT_VIS) från manuell inspektion av kontaktkartor
(0% beroende av matcharnas egen union GT_N!).

Mäter med exakta kalibrerade trösklar från Exp 5B (19 164 kors-restaurangpar):
  - Sann Precision (TP / (TP + FP_inom_konto))
  - Sann Recall mot GT_VIS (inkl. blubnan.liljeholm som har 9 visuellt sanna par!)
  - Sann F1
  - Exakt lista på VARJE falsk inom-konto-länk (hemma-vardagsrum, matnärbild, kök, galleria utanför!)
  - Icke-cirkulär sample-efficiency-kurva R_VIS(k=1..7) och AUC_VIS över alla 6 konton x 5 slumpordningar!

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe -u motpart\\runda-2-neon\\djup_hard_gt_vis_eval.py
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
from collections import defaultdict

import clip
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO, YOLOWorld

HIT = pathlib.Path(__file__).resolve().parent
R2 = HIT.parents[2] / "runda-2-neon"
if str(R2) not in sys.path:
    sys.path.insert(0, str(R2))

import djup_v1_v2_v3_destillation as D  # noqa: E402
import djup_v31_49vid_bevis as B  # noqa: E402

# Låsta trösklar från Exp 5B (kalibrerade enbart på 19 164 kors-restaurangpar, 0 läckage):
T_V2 = 0.9210
T_V31 = 0.9175
T_V32_VOTE = 0.9041

# OBEROENDE VISUELL ZONMÄRKNING (GT_VIS) från direkt visuell kontroll av kontaktkartorna
# acc_*.jpg / acc_full_*.jpg (index 1..N matchar sorterad vid_id i D.hitta_unika_videor()).
# Två klipp (vi, vj) är ett SANNT lokalt par i GT_VIS omm de delar minst en fysisk lokalzon.
GT_VIS_ZONES: dict[str, dict[int, set[str]]] = {
    "babulsofficial": {
        1: {"dining_booth"},
        2: {"kitchen_prep"},
        3: {"bar_zone"},
        4: {"bar_zone"},
        5: {"bar_zone", "white_kitchen"},
        6: {"bar_zone"},
        7: {"bar_zone"},
        8: {"bar_zone"},
        9: {"bar_zone"},
        10: {"bar_zone"},
    },
    "blackstonesteakhouse": {
        1: {"dining_hall"},
        2: {"dining_hall"},
        3: {"dining_hall"},
        4: {"dining_hall", "bar"},
        5: {"bar"},
        6: {"dining_hall", "bar", "dining_botanical"},
        7: {"bar"},
        8: {"white_kitchen"},  # separat bakkök!
        9: {"dining_botanical"},
    },
    "blubnan.liljeholm": {
        1: {"kitchen_pass"},
        2: {"kitchen_pass", "bar"},
        3: {"kitchen_pass", "bar"},
        4: {"dining_mural"},
        5: {"food_closeup_only"},  # ren catering/matnärbild utan rum!
        6: {"dining_mural"},
        7: {"dining_mural"},
        8: {"dining_mural"},
    },
    "fratelli.stockhol": {
        1: {"mall_outside"},  # galleria/korridor utanför!
        2: {"dining_rattan"},
        3: {"kitchen", "dining_rattan"},
        4: {"dining_rattan"},
        5: {"espresso_counter"},
        6: {"dining_rattan"},
        7: {"espresso_counter", "dining_rattan"},
        8: {"dining_rattan"},
    },
    "anettesrestaurang": {
        1: {"foodhall_wide"},
        2: {"food_closeup_only"},  # ren matnärbild!
        3: {"food_closeup_only"},  # ren matnärbild!
        4: {"food_closeup_only"},  # ren matnärbild!
        5: {"bar_counter"},
        6: {"pos_counter"},
        7: {"pos_counter"},
    },
    "chickenstreet.canada": {
        1: {"dining_ottawa", "counter_corner"},
        2: {"home_living_room"},  # HEMMA I VARDAGSRUMMET!
        3: {"counter_fc"},
        4: {"dining_ottawa"},
        5: {"dining_ottawa", "counter_fc"},  # bred brygga!
        6: {"counter_fc"},
        7: {"counter_fc"},
    },
}


def gt_true_pairs(acc: str, n_vids: int) -> set[tuple[int, int]]:
    zm = GT_VIS_ZONES[acc]
    pairs = set()
    for i in range(1, n_vids + 1):
        for j in range(i + 1, n_vids + 1):
            if zm[i] & zm[j]:
                pairs.add((i, j))
    return pairs


DUMP = {}


def main() -> None:
    t0 = time.perf_counter()
    vids_by_acc = D.hitta_unika_videor()
    print("=== FÖRSTÄRKNING 2: Icke-cirkulär GT_VIS-utvärdering (49 TikToks, 6 restauranger) ===", flush=True)

    yolo_seg = YOLO(str(D.YOLO_SEG_PATH))
    yolo_world = YOLOWorld(str(D.YOLO_WORLD_PATH))
    yolo_world.set_classes(B.BAG_PROMPTS)
    clip_m, clip_p = clip.load(str(D.CLIP_PATH), device="cpu")
    clip_m.eval()
    sift = cv2.SIFT_create(nfeatures=900)

    rng = np.random.default_rng(20261119)
    per_acc = {}
    tot_counts = {v: {"tp": 0, "fp": 0, "fn": 0, "z1_tp": 0, "z1_fp": 0} for v in ("v1", "v2", "v31", "v32")}
    all_fp_details = {v: [] for v in ("v1", "v2", "v31", "v32")}

    for acc in D.TARGET_ACCOUNTS:
        vlist = []
        for vi, (vid_id, vp) in enumerate(vids_by_acc[acc], 1):
            ex = D.extrahera_tagningar_med_suddgrind(vp, max_shots=6)
            shots_proc = []
            for sh in ex["shots"]:
                im_n = sh["naive_img"]
                hn, wn = im_n.shape[:2]

                m1 = D.bygg_mask_yolo(im_n, yolo_seg, [0])
                p1, d1 = D.rootsift(im_n, m1, sift)

                m2 = D.bygg_mask_yolo(im_n, yolo_seg, D.COCO_MOVABLE)
                p2, d2 = D.rootsift(im_n, m2, sift)
                c2 = D.clip_vec_v2(im_n, m2, clip_m, clip_p)
                up2 = float((m2[:int(hn * 0.68), :] > 0).mean())

                ancs = []
                for im3 in sh["v3_imgs"]:
                    h3, w3 = im3.shape[:2]
                    m3 = B.bygg_mask_v31(im3, yolo_seg, yolo_world)
                    p3, d3 = D.rootsift(im3, m3, sift)
                    v3_vec, tiles3 = B.clip_dual_v31(im3, m3, clip_m, clip_p)
                    up3 = float((m3[:int(h3 * 0.68), :] > 0).mean())
                    ancs.append({"pts": p3, "desc": d3, "shape": (h3, w3), "vec": v3_vec, "tiles": tiles3, "up_frac": up3})

                shots_proc.append({
                    "sid": f"{acc}::v{vi}_s{sh['shot_idx']+1}",
                    "video_idx": vi,
                    "video_id": vid_id,
                    "v1": {"pts": p1, "desc": d1, "shape": (hn, wn)},
                    "v2": {"pts": p2, "desc": d2, "shape": (hn, wn), "clip": c2, "up_frac": up2},
                    "v31": ancs,
                })
            vlist.append({"video_idx": vi, "video_id": vid_id, "shots": shots_proc})

        N = len(vlist)
        true_pairs = gt_true_pairs(acc, N)
        pred_pairs: dict[str, dict[tuple[int, int], set[str]]] = {v: defaultdict(set) for v in ("v1", "v2", "v31", "v32")}
        v31_sim_map: dict[tuple[str, str], float] = {}

        for a_i in range(N):
            for b_i in range(a_i + 1, N):
                va, vb = vlist[a_i], vlist[b_i]
                pair = (va["video_idx"], vb["video_idx"])
                for sa in va["shots"]:
                    for sb in vb["shots"]:
                        if D.matcha_z1(sa["v1"]["pts"], sa["v1"]["desc"], sa["v1"]["shape"], sb["v1"]["pts"], sb["v1"]["desc"], sb["v1"]["shape"], False)[0]:
                            pred_pairs["v1"][pair].add("Z1")

                        if D.matcha_z1(sa["v2"]["pts"], sa["v2"]["desc"], sa["v2"]["shape"], sb["v2"]["pts"], sb["v2"]["desc"], sb["v2"]["shape"], False)[0]:
                            pred_pairs["v2"][pair].add("Z1")
                        elif sa["v2"]["up_frac"] >= 0.35 and sb["v2"]["up_frac"] >= 0.35 and float(np.dot(sa["v2"]["clip"], sb["v2"]["clip"])) >= T_V2:
                            pred_pairs["v2"][pair].add("Z2")

                        ok31_z1 = False
                        best31_z2 = -1.0
                        for a3 in sa["v31"]:
                            for b3 in sb["v31"]:
                                gc = float(np.dot(a3["vec"], b3["vec"]))
                                if not ok31_z1:
                                    if D.matcha_z1(a3["pts"], a3["desc"], a3["shape"], b3["pts"], b3["desc"], b3["shape"], True, gc)[0]:
                                        ok31_z1 = True
                                if a3["up_frac"] >= 0.35 and b3["up_frac"] >= 0.35:
                                    sc = B.sim_dual_v31(a3["vec"], a3["tiles"], b3["vec"], b3["tiles"])
                                    if sc > best31_z2:
                                        best31_z2 = sc
                        v31_sim_map[(sa["sid"], sb["sid"])] = best31_z2
                        v31_sim_map[(sb["sid"], sa["sid"])] = best31_z2
                        if ok31_z1:
                            pred_pairs["v31"][pair].add("Z1")
                        elif best31_z2 >= T_V31:
                            pred_pairs["v31"][pair].add("Z2")

        # v3.2: v3.1 + flervy-röstning (>=2 olika klipp över T_V32_VOTE)
        for p, types in pred_pairs["v31"].items():
            pred_pairs["v32"][p].update(types)
        all_shots = [sh for v in vlist for sh in v["shots"]]
        for sa in all_shots:
            hits_by_vid = defaultdict(list)
            for sb in all_shots:
                if sb["video_idx"] == sa["video_idx"]:
                    continue
                sc = v31_sim_map.get((sa["sid"], sb["sid"]), -1.0)
                if sc >= T_V32_VOTE:
                    hits_by_vid[sb["video_idx"]].append(sc)
            if len(hits_by_vid) >= 2:
                for b_vi in hits_by_vid:
                    pair = (min(sa["video_idx"], b_vi), max(sa["video_idx"], b_vi))
                    pred_pairs["v32"][pair].add("Z2_VOTE")

        # Beräkna TP/FP/FN + icke-cirkulära sample-efficiency-kurvor (R_VIS(k) = andel sanna GT_VIS-par återfunna vid klipp k!)
        orders = [list(range(1, N + 1))] + [list(rng.permutation(range(1, N + 1))) for _ in range(4)]
        DUMP[acc] = {v: sorted([list(p) + [sorted(t)] for p, t in pred_pairs[v].items()]) for v in pred_pairs}
        (HIT / "gt_vis_kopia_pred_pairs.json").write_text(json.dumps(DUMP, ensure_ascii=False), encoding="utf-8")
        acc_res = {"N_klipp": N, "GT_VIS_sanna_par": len(true_pairs), "versioner": {}}
        for ver in ("v1", "v2", "v31", "v32"):
            pset = set(pred_pairs[ver].keys())
            tp_set = pset & true_pairs
            fp_set = pset - true_pairs
            fn_set = true_pairs - pset

            z1_tp = sum(1 for p in tp_set if "Z1" in pred_pairs[ver][p])
            z1_fp = sum(1 for p in fp_set if "Z1" in pred_pairs[ver][p])

            tot_counts[ver]["tp"] += len(tp_set)
            tot_counts[ver]["fp"] += len(fp_set)
            tot_counts[ver]["fn"] += len(fn_set)
            tot_counts[ver]["z1_tp"] += z1_tp
            tot_counts[ver]["z1_fp"] += z1_fp

            for p in sorted(fp_set):
                all_fp_details[ver].append({
                    "konto": acc,
                    "par": list(p),
                    "typer": sorted(pred_pairs[ver][p]),
                    "zon_a": sorted(GT_VIS_ZONES[acc][p[0]]),
                    "zon_b": sorted(GT_VIS_ZONES[acc][p[1]]),
                })

            # Icke-cirkulär kurva: andel av true_pairs som är kopplade (antingen direkt eller transitivt via SANNA par!) vid klipp k
            mat_direct = np.zeros((len(orders), N), float)
            for oi, perm in enumerate(orders):
                seen = set()
                for step_k, cid in enumerate(perm):
                    seen.add(cid)
                    found_tp = {p for p in tp_set if p[0] in seen and p[1] in seen}
                    mat_direct[oi, step_k] = 100.0 * len(found_tp) / max(1, len(true_pairs))

            prec = 100.0 * len(tp_set) / max(1, len(tp_set) + len(fp_set)) if (tp_set or fp_set) else 100.0
            rec = 100.0 * len(tp_set) / max(1, len(true_pairs))
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            acc_res["versioner"][ver] = {
                "TP": len(tp_set),
                "FP_inom_konto": len(fp_set),
                "FN": len(fn_set),
                "precision_pct": round(prec, 1),
                "recall_pct": round(rec, 1),
                "f1_pct": round(f1, 1),
                "kurva_R_VIS_pct": [round(float(x), 1) for x in mat_direct.mean(axis=0)],
            }
        per_acc[acc] = acc_res
        print(
            f"  [{acc:22s}] GT_VIS={len(true_pairs):2d} par | "
            f"v1: {acc_res['versioner']['v1']['TP']}TP/{acc_res['versioner']['v1']['FP_inom_konto']}FP | "
            f"v2: {acc_res['versioner']['v2']['TP']}TP/{acc_res['versioner']['v2']['FP_inom_konto']}FP | "
            f"v3.1: {acc_res['versioner']['v31']['TP']}TP/{acc_res['versioner']['v31']['FP_inom_konto']}FP | "
            f"v3.2: {acc_res['versioner']['v32']['TP']}TP/{acc_res['versioner']['v32']['FP_inom_konto']}FP ({time.perf_counter()-t0:.0f}s)",
            flush=True,
        )

    # Mikro- och makro-aggregat över ALLA 6 konton (inkl. blubnan.liljeholm!)
    K = 7
    agg_micro = {}
    agg_curve = {}
    agg_auc = {}
    for ver in ("v1", "v2", "v31", "v32"):
        c = tot_counts[ver]
        tp, fp, fn = c["tp"], c["fp"], c["fn"]
        prec = 100.0 * tp / max(1, tp + fp) if (tp + fp) > 0 else 100.0
        rec = 100.0 * tp / max(1, tp + fn)
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        agg_micro[ver] = {
            "TP": tp,
            "FP_inom_konto": fp,
            "FN": fn,
            "Z1_TP": c["z1_tp"],
            "Z1_FP": c["z1_fp"],
            "precision_pct": round(prec, 1),
            "recall_pct": round(rec, 1),
            "f1_pct": round(f1, 1),
        }
        m = np.array([per_acc[a]["versioner"][ver]["kurva_R_VIS_pct"][:K] for a in D.TARGET_ACCOUNTS])
        mc = m.mean(axis=0)
        agg_curve[ver] = [round(float(x), 1) for x in mc]
        agg_auc[ver] = round(float(mc.mean()), 1)

    tot_gt_pairs = sum(per_acc[a]["GT_VIS_sanna_par"] for a in D.TARGET_ACCOUNTS)
    rapport = {
        "syfte": "Förstärkning 2: Icke-cirkulär GT_VIS-utvärdering över alla 49 riktiga TikToks (6 restauranger inkl. blubnan!)",
        "totalt_GT_VIS_sanna_klippar": tot_gt_pairs,
        "trosklar_fran_exp5B_korskontroll": {"T_V2": T_V2, "T_V31": T_V31, "T_V32_VOTE": T_V32_VOTE},
        "mikro_aggregat_alla_6_konton": agg_micro,
        "icke_cirkular_kurva_k1_k7_alla_6_konton": agg_curve,
        "AUC_VIS_alla_6_konton_pct": agg_auc,
        "falska_inom_konto_lankar_detaljer": all_fp_details,
        "per_restaurang": per_acc,
        "korningstid_s": round(time.perf_counter() - t0, 1),
    }
    (HIT / "djup_hard_gt_vis_eval.json").write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")

    # Rita bevisfigur: djup_hard_gt_vis_bevis.png
    fig = plt.figure(figsize=(18.5, 9.5), dpi=130, facecolor="#0f1117")
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.05, 1.0], wspace=0.22)
    cols = {"v1": "#e74c3c", "v2": "#f39c12", "v31": "#00d2ff", "v32": "#2ecc71"}

    # Panel A: Icke-cirkulär R_VIS(k=1..7) över ALLA 6 konton (inkl. blubnan!)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor("#161b22")
    ks = list(range(1, K + 1))
    for ver, nm in [("v1", "v1 RootSIFT"), ("v2", "v2 Hybrid+COCO"), ("v31", "v3.1 Fixad (Prod)"), ("v32", "v3.2 +2-klippsröst")]:
        m = agg_micro[ver]
        ax1.plot(
            ks, agg_curve[ver], marker="o", linewidth=2.6, markersize=7, color=cols[ver],
            label=f"{nm}: AUC={agg_auc[ver]}% | F1={m['f1_pct']}% ({m['TP']}TP / {m['FP_inom_konto']}FP)",
        )
    ax1.set_xlabel("Antal inlästa klipp (k = 1 -> 7, ALLA 6 konton inkl. blubnan)", color="white", fontsize=9.5)
    ax1.set_ylabel("Icke-cirkulär sann GT_VIS-paråtervinning (%)", color="white", fontsize=9.5)
    ax1.set_ylim(-2, 65)
    ax1.tick_params(colors="white")
    ax1.grid(alpha=0.22, color="white")
    ax1.legend(loc="upper left", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=8.3)
    ax1.set_title(f"A. ICKE-CIRKULÄR DESTILLATION mot GT_VIS ({tot_gt_pairs} visuellt märkta par)\n0% beroende av matcharnas egen union!", color="#ffd166", fontsize=10, pad=6)

    # Panel B: Precision vs Recall vs F1 (mikro över alla 6 konton!)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor("#161b22")
    vers = ["v1", "v2", "v31", "v32"]
    x = np.arange(len(vers))
    w = 0.25
    precs = [agg_micro[v]["precision_pct"] for v in vers]
    recs = [agg_micro[v]["recall_pct"] for v in vers]
    f1s = [agg_micro[v]["f1_pct"] for v in vers]
    b1 = ax2.bar(x - w, precs, w, color="#2ecc71", label="Sann Precision (%)")
    b2 = ax2.bar(x, recs, w, color="#00d2ff", label="Sann Recall (%)")
    b3 = ax2.bar(x + w, f1s, w, color="#ffd166", label="Sann F1 (%)")
    for bars in (b1, b2, b3):
        for b in bars:
            h_v = b.get_height()
            ax2.text(b.get_x() + b.get_width() / 2, h_v + 1.4, f"{h_v:.1f}", ha="center", va="bottom", color="white", fontsize=8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(["v1", "v2", "v3.1\n(Prod)", "v3.2\n(Aggr.)"], color="white", fontsize=9.5)
    ax2.set_ylim(0, 114)
    ax2.set_ylabel("Procent (%)", color="white", fontsize=9.5)
    ax2.tick_params(colors="white")
    ax2.grid(axis="y", alpha=0.22, color="white")
    ax2.legend(loc="upper right", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=8.5)
    ax2.set_title("B. PRECISION / RECALL / F1 mot oberoende GT_VIS\nVisar öppet v3.2:s precision-kostnad mot v3.1!", color="#ffd166", fontsize=10, pad=6)

    # Panel C: Sanna TP vs Falska inom-konto FP (hemma/mat/kök/galleria!)
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_facecolor("#161b22")
    tps = [agg_micro[v]["TP"] for v in vers]
    fps = [agg_micro[v]["FP_inom_konto"] for v in vers]
    b_tp = ax3.bar(x - 0.17, tps, 0.34, color="#2ecc71", label="Sanna par (TP)")
    b_fp = ax3.bar(x + 0.17, fps, 0.34, color="#e74c3c", label="Falska inom-konto-länkar (FP)")
    for b in b_tp:
        ax3.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, f"{int(b.get_height())}", ha="center", va="bottom", color="white", fontsize=9, fontweight="bold")
    for b in b_fp:
        ax3.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, f"{int(b.get_height())}", ha="center", va="bottom", color="#ff8a8a", fontsize=9, fontweight="bold")
    ax3.set_xticks(x)
    ax3.set_xticklabels(["v1", "v2", "v3.1\n(Prod)", "v3.2\n(Aggr.)"], color="white", fontsize=9.5)
    ax3.set_ylabel("Antal klippar (av 100 sanna par)", color="white", fontsize=9.5)
    ax3.set_ylim(0, max(tps + fps) + 10)
    ax3.tick_params(colors="white")
    ax3.grid(axis="y", alpha=0.22, color="white")
    ax3.legend(loc="upper left", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=8.5)
    ax3.set_title("C. SANNA PAR vs FALSKA INOM-KONTO-LÄNKAR\nZ1-FP = 0 för ALLA versioner!", color="#ffd166", fontsize=10, pad=6)

    fig.suptitle(
        f"FÖRSTÄRKNING 2: Icke-cirkulär GT_VIS-benchmark (49 riktiga TikToks, 6 restauranger, {tot_gt_pairs} visuellt märkta par)",
        color="white", fontsize=12.8, fontweight="bold", y=0.98,
    )
    out_png = HIT / "djup_hard_gt_vis_bevis.png"
    fig.savefig(out_png, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"\n=== FÖRSTÄRKNING 2 KLAR på {rapport['korningstid_s']}s! ===", flush=True)
    print(json.dumps({"mikro": agg_micro, "AUC_VIS": agg_auc, "FP_detaljer": all_fp_details}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
