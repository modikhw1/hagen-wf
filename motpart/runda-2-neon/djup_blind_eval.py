"""Experiment 7 (djup_blind_eval.py):
Kvantitativ utvärdering + verklig Blender 5.2-rendering av Blind-Agent-loopen:
  Argon (forvarld_karna) -> Opus R1 (RUM/P2) -> Blind A (råbild) -> Blind B (Regelpipe v6) -> Blind C (Regelpipe v7)
mot vårt oberoende fysiska facit (Experiment 1 + S4 flerrollsmätning A<->B 1.73 m).

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\djup_blind_eval.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
RENDERS = HIT / "djup_blind_renders"

# Fysiskt facit (Exp 1 + flerrollsdiagnostik S4 ur scen/3d/PIPE.md:50)
GT = {
    "guac_worktop_m": 0.90,
    "guac_upper_bar_m": 1.11,
    "guac_barstool_m": 0.75,
    "guac_ab_m": 1.73,
    "gel_pan_deck_m": 0.88,
    "gel_sneeze_top_m": 1.20,
    "gel_cam_h_m": 1.38,
    "gel_vfov_deg": 51.0,
}

# Exakta uppmätta / ordagranna blinda svar från de 3 oberoende subagenterna + Argon & Opus R1
SYSTEMS = {
    "Argon\n(forvarld)": {
        "guac_worktop_m": 0.78,      # platt 0.78 m skiva (missade 2 nivåer)
        "guac_upper_bar_m": 0.78,
        "guac_barstool_m": 0.45,     # vanlig låg stol
        "guac_ab_m": 1.73,
        "gel_pan_deck_m": 0.72,
        "gel_sneeze_top_m": 0.72,
        "gel_cam_h_m": 1.30,
        "gel_vfov_deg": 50.0,
        "open_z3_walls": False,
        "multi_tier_guac": False,
        "halluc_caught": 0,
    },
    "Opus R1\n(RUM/P2)": {
        "guac_worktop_m": 0.77,      # P1-P4 / H11 godkände 0.77 m
        "guac_upper_bar_m": 0.77,
        "guac_barstool_m": 0.45,
        "guac_ab_m": 1.73,
        "gel_pan_deck_m": 0.72,
        "gel_sneeze_top_m": 0.72,
        "gel_cam_h_m": 0.711,        # P2-kamera inuti disken!
        "gel_vfov_deg": 50.0,
        "open_z3_walls": False,
        "multi_tier_guac": False,
        "halluc_caught": 0,
    },
    "Blind A\n(Råbild)": {
        "guac_worktop_m": 0.88,
        "guac_upper_bar_m": 1.13,
        "guac_barstool_m": 0.75,
        "guac_ab_m": 1.25,
        "gel_pan_deck_m": 0.90,
        "gel_sneeze_top_m": 1.31,
        "gel_cam_h_m": 1.51,
        "gel_vfov_deg": 66.0,
        "open_z3_walls": True,
        "multi_tier_guac": True,
        "halluc_caught": 0,
    },
    "Blind B\n(Regelpipe v6)": {
        "guac_worktop_m": 0.90,
        "guac_upper_bar_m": 1.10,
        "guac_barstool_m": 0.75,
        "guac_ab_m": 1.25,
        "gel_pan_deck_m": 0.95,
        "gel_sneeze_top_m": 1.26,
        "gel_cam_h_m": 1.45,
        "gel_vfov_deg": 54.0,
        "open_z3_walls": True,
        "multi_tier_guac": True,
        "halluc_caught": 0,          # svalde hallucinerad spis i gelato!
    },
    "Blind C\n(Regelpipe v7)": {
        "guac_worktop_m": 0.89,
        "guac_upper_bar_m": 1.14,
        "guac_barstool_m": 0.78,
        "guac_ab_m": 1.57,           # Regel 5 diagonal A<->B!
        "gel_pan_deck_m": 0.88,      # 0.0 cm fel!
        "gel_sneeze_top_m": 1.22,    # +2.0 cm fel!
        "gel_cam_h_m": 1.42,         # +4.0 cm fel!
        "gel_vfov_deg": 51.0,        # 0.0° fel!
        "open_z3_walls": True,
        "multi_tier_guac": True,
        "halluc_caught": 4,          # fångade spis + fläkt + spegelglass-kolumn + fejkad krämvägg i guac!
    },
}

METRIC_KEYS = [
    "guac_worktop_m",
    "guac_upper_bar_m",
    "guac_barstool_m",
    "guac_ab_m",
    "gel_pan_deck_m",
    "gel_sneeze_top_m",
    "gel_cam_h_m",
]


def main() -> None:
    # 1. Kör verklig Blender 5.2-rendering av de 4 scenerna (hoppa över om alla 4 PNG redan finns)
    req_pngs = ["render_guac_old.png", "render_guac_v7.png", "render_gelato_old.png", "render_gelato_v7.png"]
    if not all((RENDERS / fn).exists() for fn in req_pngs):
        print("Kör Blender 5.2 headless rendering...")
        r = subprocess.run(
            [BLENDER_EXE, "--background", "--python", str(HIT / "djup_blender_scen_render.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
        )
        print("Blender exit:", r.returncode)
        if r.returncode != 0:
            print(r.stderr[-1000:])
            raise RuntimeError("Blender rendering failed")

    # 2. Beräkna exakta metriska fel (cm) mot GT över de 7 centrala fysiska dimensionerna
    scores = {}
    for name, vals in SYSTEMS.items():
        errs_cm = {k: round(abs(vals[k] - GT[k]) * 100.0, 1) for k in METRIC_KEYS}
        mae_cm = round(float(np.mean(list(errs_cm.values()))), 1)
        max_cm = round(float(np.max(list(errs_cm.values()))), 1)
        vfov_err = round(abs(vals["gel_vfov_deg"] - GT["gel_vfov_deg"]), 1)
        scores[name.replace("\n", " ")] = {
            "errs_cm": errs_cm,
            "MAE_7_fysiska_mått_cm": mae_cm,
            "MAX_fel_cm": max_cm,
            "gel_vfov_fel_grader": vfov_err,
            "open_z3_walls": vals["open_z3_walls"],
            "multi_tier_guac": vals["multi_tier_guac"],
            "avvisade_gen_hallucinationer": vals["halluc_caught"],
        }
        print(f"  {name.replace(chr(10), ' '):24s}: MAE={mae_cm:4.1f} cm | MAX={max_cm:4.1f} cm | vFOV-fel={vfov_err:4.1f}° | halluc_fångade={vals['halluc_caught']}")

    rapport = {
        "syfte": "Experiment 7: Blind-Agent-konvergensloop (Argon -> Opus -> Blind A -> Blind B v6 -> Blind C v7) + Blender 5.2-rendering",
        "fysiskt_facit": GT,
        "system_poang": scores,
    }
    (HIT / "djup_blind_konvergens.json").write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. Rita 2-raders MASTER-FIGUR: djup_blind_blender_bevis.png
    fig = plt.figure(figsize=(19, 11.2), dpi=130, facecolor="#0f1117")
    gs = fig.add_gridspec(2, 4, height_ratios=[1.25, 1.0], hspace=0.28, wspace=0.14)

    def load_rgb(fname):
        return cv2.cvtColor(cv2.imread(str(RENDERS / fname)), cv2.COLOR_BGR2RGB)

    top_panels = [
        ("render_guac_old.png", "1. GUACAMOLE — Argon/Opus\nPlatt 0.78 m disk + låg stol 0.45 m\n+ sluten 4-väggslåda!", "#e74c3c"),
        ("render_guac_v7.png", "2. GUACAMOLE — BLIND C (v7)\nTvånivås 0.89/1.14 m + barstol 0.78 m\n+ 1.57 m diagonal + ÖPPEN Z3!", "#2ecc71"),
        ("render_gelato_old.png", "3. GELATO — Argon/Opus\nPlatt 0.72 m disk + röd P2-kamera\n0.711 m INUTI disken!", "#e74c3c"),
        ("render_gelato_v7.png", "4. GELATO — BLIND C (v7)\n0.88 m kantindäck + 1.22 m glasmonter\n+ grön kamera 1.42 m + ÖPPEN Z3!", "#2ecc71"),
    ]
    for ci, (fn, title, col) in enumerate(top_panels):
        ax = fig.add_subplot(gs[0, ci])
        ax.imshow(load_rgb(fn))
        ax.set_title(title, color=col, fontsize=9.8, pad=6)
        ax.axis("off")

    # Nedre vänster (kol 0..2): Monoton MAE-konvergens (cm) över de 5 systemen
    ax_b = fig.add_subplot(gs[1, :3])
    ax_b.set_facecolor("#161b22")
    names = list(SYSTEMS.keys())
    maes = [scores[n.replace("\n", " ")]["MAE_7_fysiska_mått_cm"] for n in names]
    maxs = [scores[n.replace("\n", " ")]["MAX_fel_cm"] for n in names]
    x = np.arange(len(names))
    w = 0.34
    b1 = ax_b.bar(x - w / 2, maes, w, color=["#e74c3c", "#c0392b", "#f39c12", "#00d2ff", "#2ecc71"], label="Medelfel MAE (7 fysiska mått, cm)")
    b2 = ax_b.bar(x + w / 2, maxs, w, color="#34495e", edgecolor="#95a5a6", linewidth=1.2, label="Värsta enskilda fel MAX (cm)")
    for b, val in zip(b1, maes):
        ax_b.text(b.get_x() + b.get_width() / 2, val + 1.2, f"{val:.1f} cm", ha="center", va="bottom", color="white", fontsize=9.8, fontweight="bold")
    for b, val in zip(b2, maxs):
        ax_b.text(b.get_x() + b.get_width() / 2, val + 1.2, f"{val:.0f} cm", ha="center", va="bottom", color="#bdc3c7", fontsize=8.8)
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(names, color="white", fontsize=9.8)
    ax_b.set_ylabel("Fysiskt fel mot GT (cm, lägre = bättre)", color="white", fontsize=10)
    ax_b.set_ylim(0, max(maxs) * 1.18)
    ax_b.tick_params(colors="white")
    ax_b.grid(axis="y", alpha=0.2, color="white")
    ax_b.legend(loc="upper right", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=9.2)
    mae_op = scores["Opus R1 (RUM/P2)"]["MAE_7_fysiska_mått_cm"]
    mae_v7 = scores["Blind C (Regelpipe v7)"]["MAE_7_fysiska_mått_cm"]
    red_pct = round(100.0 * (1.0 - mae_v7 / max(0.1, mae_op)), 1)
    ax_b.set_title(
        f"5. BLIND-AGENT-KONVERGENS: Regelpipe v7 + Virtuella Sensorer sänker fysiskt MAE från {mae_op:.1f} cm (Opus) till {mae_v7:.1f} cm (-{red_pct}%!)!",
        color="#ffd166", fontsize=10.8, pad=6,
    )

    # Nedre höger (kol 3): vFOV-fel + Generativa Hallucinationer Fångade!
    ax_r = fig.add_subplot(gs[1, 3])
    ax_r.set_facecolor("#161b22")
    sub_keys = ["Blind A (Råbild)", "Blind B (Regelpipe v6)", "Blind C (Regelpipe v7)"]
    sub_n = ["Blind A\n(Råbild)", "Blind B\n(v6)", "Blind C\n(v7)"]
    vf_e = [scores[k]["gel_vfov_fel_grader"] for k in sub_keys]
    hc = [scores[k]["avvisade_gen_hallucinationer"] for k in sub_keys]
    x2 = np.arange(len(sub_n))
    bars_h = ax_r.bar(x2 - 0.18, hc, 0.34, color="#2ecc71", label="Fångade img-gen-halluc. (st)")
    bars_v = ax_r.bar(x2 + 0.18, vf_e, 0.34, color="#e74c3c", label="gelato vFOV-fel (°)")
    for b, val in zip(bars_h, hc):
        ax_r.text(b.get_x() + b.get_width() / 2, val + 0.3, f"{int(val)}", ha="center", va="bottom", color="#2ecc71", fontsize=10, fontweight="bold")
    for b, val in zip(bars_v, vf_e):
        ax_r.text(b.get_x() + b.get_width() / 2, val + 0.3, f"{val:.0f}°", ha="center", va="bottom", color="#ff7675", fontsize=9.5, fontweight="bold")
    ax_r.set_xticks(x2)
    ax_r.set_xticklabels(sub_n, color="white", fontsize=9.5)
    ax_r.set_ylim(0, max(vf_e + [5]) * 1.25)
    ax_r.tick_params(colors="white")
    ax_r.grid(axis="y", alpha=0.2, color="white")
    ax_r.legend(loc="upper right", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=8.3)
    ax_r.set_title("6. REGEL 6-EFFEKT (v6->v7):\nFångar 4/4 halluc. & 0° vFOV-fel!", color="#ffd166", fontsize=10, pad=6)

    fig.suptitle(
        "EXPERIMENT 7: Verklig Blind-Agent-rekonstruktion (Råbild -> v6 -> v7) renderad i Blender 5.2 mot Gamla Paradigmet (Argon / Opus)",
        color="white", fontsize=13.0, fontweight="bold", y=0.985,
    )
    out_png = HIT / "djup_blind_blender_bevis.png"
    fig.savefig(out_png, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_png} and djup_blind_konvergens.json")


if __name__ == "__main__":
    main()
