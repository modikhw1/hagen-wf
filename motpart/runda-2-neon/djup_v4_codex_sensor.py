"""Experiment 4 (djup_v4_codex_sensor.py):
VERKLIGT pilottest av GPT Image (via ägarens Codex-plan: scen/3d/gennedbrytning/codex_bild.py)
som pipe-vänlig virtuell sensor och 1:1-extremitetssond på guacamole (där S4 utgör verkligt
hold-out-facit för S1 och S2!).

5 strikt budgeterade anrop (sekventiellt för att undvika race i ~/.codex/generated_images):
  1. v4_guac_S4_tom.png       — Steg A (negativ strategi): ta bort personer + text ur guacamole S4.
  2. v4_guac_S4_djupplan.png  — Steg B (2-bilds låst positionalitet): original S4 + tom S4 ->
                                 högkontrast metrisk djup-/plan-karta (Turbo) som skiljer tvånivåsbaren!
  3. v4_guac_S1_ext_s1.png    — Extremitetssond λ≈1.8x (Frö 1) på snäva S1 (har ALDRIG sett S2/S4!).
  4. v4_guac_S1_ext_s2.png    — Extremitetssond λ≈1.8x (Frö 2, oberoende session) -> verklig K=2 σ_gen!
  5. v4_guac_S2_ext_s1.png    — Extremitetssond λ≈1.8x på snäva S2 -> testa korskoppling S1_ext <-> S2_ext
                                 OCH mot hold-out verklig S4!

Kör:
  $env:PYTHONIOENCODING="utf-8"
  $env:CODEX_RAA="1"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\djup_v4_codex_sensor.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time

import cv2
import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
RAMAR = HIT / "djup_gt_ramar"
OUT = HIT / "djup_v4_sensor"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROT / "scen/3d/gennedbrytning"))
import codex_bild  # noqa: E402


PROMPTS = {
    "v4_guac_S4_tom.png": (
        "Edit image 1 using strict negative removal only: remove both people (the seated man on the left "
        "and the standing man in the green polo shirt on the right) and remove all white overlaid subtitle text. "
        "Keep the EXACT camera angle, lens perspective, framing, 9:16 portrait aspect ratio, and every static architectural "
        "element locked in its exact original pixel position: the high copper-brown guest bar counter on the left and bottom, "
        "the lower white marble worktop behind it with the white receipt-rolls box and black POS terminal, the back-bar stainless "
        "cooler with wine bottles and cans, the overhead hanging wine glass rack, the colorful Mexican skull mural wall, and the "
        "vertical wooden wall slats on the right. Reconstruct only the empty counter surfaces and wall sections previously hidden "
        "behind the two people. Do not zoom, crop, shift, re-center, or invent new objects. Photorealistic, matching original lighting.",
        [RAMAR / "guacamole_S4_raw.png"],
    ),
    "v4_guac_S4_djupplan.png": (
        "Image 1 is the original bar photo and image 2 is the exact same empty bar scene with the people and text removed. "
        "Keeping 100% EXACT pixel-for-pixel geometry, camera framing, 9:16 portrait aspect ratio, and object positions of image 2 "
        "(do NOT shift, zoom, crop, or re-center anything), render image 2 as a crisp, clean, machine-readable dense metric depth map "
        "in standard Turbo colormap (nearest foreground copper bar edge = bright red/orange; mid-near lower white worktop, POS screen, "
        "and upper copper guest bar top = yellow/bright green with a RAZOR-SHARP step edge along the two-tier vertical drop between the "
        "higher copper guest bar counter and the lower white staff worktop; overhead hanging glass rack = cyan; back-bar fridge and wine "
        "bottles = medium blue; farthest Mexican mural wall, slatted wood wall, and ceiling = deep dark blue/indigo). "
        "Flat smooth depth gradients on planar surfaces, razor-sharp depth discontinuities at every furniture edge and occlusion step. "
        "No text, no labels, no legend bar, no people, no borders.",
        [RAMAR / "guacamole_S4_raw.png", OUT / "v4_guac_S4_tom.png"],
    ),
    "v4_guac_S1_ext_s1.png": (
        "Outpaint and zoom out (approximately 1.8x wider camera field of view, 9:16 portrait aspect ratio) from image 1 to reveal "
        "the surrounding restaurant bar room geometry for 3D spatial mapping. Keep the ENTIRE original scene of image 1 strictly preserved "
        "in the center with identical camera perspective, bar angle, hanging wine glass rack, colorful Mexican mural, and seated man — "
        "only remove the white subtitle text. Realistically extend the room outward in all four directions: especially extend to the RIGHT "
        "along the copper bar counter, lower white staff worktop behind the bar, hanging wine glass rack, and back-bar bottle shelf/wall; "
        "extend DOWNWARD to show the base of the high bar counter, bar stool, and restaurant floor; extend UPWARD to show the ceiling. "
        "Do not add borders or picture frames. Natural smartphone wide-angle photograph matching original lighting and perspective.",
        [RAMAR / "guacamole_S1_raw.png"],
    ),
    "v4_guac_S1_ext_s2.png": (
        "Outpaint and zoom out (approximately 1.8x wider camera field of view, 9:16 portrait aspect ratio) from image 1 to reveal "
        "the surrounding restaurant bar room geometry for 3D spatial mapping. Keep the ENTIRE original scene of image 1 strictly preserved "
        "in the center with identical camera perspective, bar angle, hanging wine glass rack, colorful Mexican mural, and seated man — "
        "only remove the white subtitle text. Realistically extend the room outward in all four directions: especially extend to the RIGHT "
        "along the copper bar counter, lower white staff worktop behind the bar, hanging wine glass rack, and back-bar bottle shelf/wall; "
        "extend DOWNWARD to show the base of the high bar counter, bar stool, and restaurant floor; extend UPWARD to show the ceiling. "
        "Do not add borders or picture frames. Natural smartphone wide-angle photograph matching original lighting and perspective.",
        [RAMAR / "guacamole_S1_raw.png"],
    ),
    "v4_guac_S2_ext_s1.png": (
        "Outpaint and zoom out (approximately 1.8x wider camera field of view, 9:16 portrait aspect ratio) from image 1 to reveal "
        "the surrounding restaurant bar room geometry for 3D spatial mapping. Keep the ENTIRE original scene of image 1 strictly preserved "
        "in the center with identical camera perspective, standing bartender, back-bar wine bottles, hanging glass rack, and wooden slat wall — "
        "only remove the white subtitle text. Realistically extend the room outward in all four directions: especially extend to the LEFT "
        "along the overhead hanging wine glass rack, copper guest bar counter, lower white worktop with POS terminal, and colorful Mexican "
        "back wall; extend DOWNWARD to show the full two-tier bar counter and floor; extend UPWARD to show the ceiling. "
        "Do not add borders or picture frames. Natural smartphone wide-angle photograph matching original lighting and perspective.",
        [RAMAR / "guacamole_S2_raw.png"],
    ),
}


def main() -> None:
    os.environ["CODEX_RAA"] = "1"
    log = {"start_kvot": codex_bild.kvot(), "anrop": []}
    print("Start kvot:", json.dumps(log["start_kvot"], ensure_ascii=False))

    order = [
        "v4_guac_S4_tom.png",
        "v4_guac_S4_djupplan.png",
        "v4_guac_S1_ext_s1.png",
        "v4_guac_S1_ext_s2.png",
        "v4_guac_S2_ext_s1.png",
    ]

    for fname in order:
        ut = OUT / fname
        prompt, bilder = PROMPTS[fname]
        missing = [str(b) for b in bilder if not b.exists()]
        if missing:
            print(f"SKIP {fname}: saknar indata {missing}")
            log["anrop"].append({"fil": fname, "status": "skip_missing", "missing": missing})
            continue
        if ut.exists():
            print(f"FINNS REDAN: {fname} (hoppar över omkörning)")
            log["anrop"].append({"fil": fname, "status": "cached"})
            continue

        print(f"\n>>> Kör Codex image_gen: {fname} (bilder={[b.name for b in bilder]})...")
        t0 = time.perf_counter()
        try:
            full_prompt = (
                prompt
                + "\n\nUse your image generation tool now to create exactly one image from the attached input image(s) "
                "(image 1, image 2 in order). Do not ask questions or write code. After generating the image, reply with: done."
            )
            post = codex_bild.generera(ut, full_prompt, bilder)
            dt = round(time.perf_counter() - t0, 1)
            ok = ut.exists()
            hel = post.get("prompt_fram", {}).get("hel")
            kv_ef = post.get("kvot_efter", {})
            print(f"<<< {fname}: ok={ok}, hel={hel}, {dt}s, kvot_primar={kv_ef.get('primar', {}).get('used_percent')}%")
            log["anrop"].append({
                "fil": fname,
                "status": "ok" if ok else "failed",
                "exit": post.get("exit"),
                "hel": hel,
                "sekunder": dt,
                "kvot_efter": kv_ef,
            })
        except Exception as e:
            print(f"!!! FEL vid {fname}: {e}")
            log["anrop"].append({"fil": fname, "status": "error", "fel": str(e)})

    log["slut_kvot"] = codex_bild.kvot()
    (OUT / "v4_codex_logg.json").write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== KLAR! Slutkvot:", json.dumps(log["slut_kvot"], ensure_ascii=False))


if __name__ == "__main__":
    main()
