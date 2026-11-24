"""Experiment 6 (djup_v5_prompt_ab.py):
VERKLIG A/B-promptoptimering och intentionalitetsmatris på 0..1-skalan över TVÅ skilda lokaltyper
(guacamole = bardisk, gelato = glassbar) via Codex CLI (GPT Image, CODEX_RAA=1):

Prövar ägarens kärnfråga om trade-off och intentionalitet:
  - Rutt A ("naken" / Zero-LLM): EN universell, lokal-agnostisk prompt där img-gen SJÄLV beslutar
    vad som är lokalens stomme vs brus vid abstraktionsnivå ~0.45/1.0 (ingen extra LLM före!).
  - Rutt B ("regisserad" / 0..1 Relevansbrief): Förkuraterad prompt med två skilda intentionaliteter:
      * Intentionalitet I  (0.35 — RoomAnalysis / LeTrend Rumsläsningsmotor): ren, matt, städad
        plan- och möbelgeometri utan brus/etiketter/kablar för maximal 3D-läsbarhet.
      * Intentionalitet II (0.55 — "Good Enough" Produktion / Seedance / Semantisk redigerbarhet):
        förenklad men omisskännligt igenkännbar kundlokal (bardisk / glassdisk) redo för animering.
  - Generaliseringstest av 2-bilds Virtuell Djupsensor på GENOMSKINLIG GLASSMONTER (gelato S1)!

6 sekventiella anrop (ingen race i ~/.codex/generated_images; hoppar över redan skapade filer):
  1. v5_guac_naken_04.png       (Guacamole S4 — Rutt A, naken universell 0.45-prompt)
  2. v5_guac_regi_04_room.png   (Guacamole S4 — Rutt B, regisserad 0.35 RoomAnalysis)
  3. v5_guac_regi_06_prod.png   (Guacamole S4 — Rutt B, regisserad 0.55 Good-Enough Produktion)
  4. v5_gelato_naken_04.png     (Gelato S1    — Rutt A, EXAKT SAMMA universella 0.45-prompt!)
  5. v5_gelato_regi_04_room.png (Gelato S1    — Rutt B, regisserad 0.35 RoomAnalysis)
  6. v5_gelato_regi_05_djup.png (Gelato S1    — Steg B: 2-bilds Turbo-djupkarta [Orig S1 + Tom/0.35 S1]!)

Kör:
  $env:PYTHONIOENCODING="utf-8"
  $env:CODEX_RAA="1"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\djup_v5_prompt_ab.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
RAMAR = HIT / "djup_gt_ramar"
OUT = HIT / "djup_v5_prompt_ab"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROT / "scen/3d/gennedbrytning"))
import codex_bild  # noqa: E402


# EN och samma universella zero-LLM-prompt för BÅDE guacamole (bar) och gelato (glassbar)!
NAKEN_UNIVERSAL_045 = (
    "Edit image 1 into a clean, simplified 3D-readable architectural reference at detail level 0.45 on a 0-to-1 scale "
    "(where 0 = bare empty wireframe box and 1 = full cluttered raw photograph). "
    "You decide what is structurally essential vs visual clutter: "
    "(1) KEEP 100% locked in exact original pixel position, 9:16 portrait aspect ratio, camera lens, and perspective: "
    "the room layout (walls, ceiling, floor planes) and the primary scene-defining furniture/counter silhouette so the "
    "venue type remains immediately unmistakable. "
    "(2) SIMPLIFY the kept furniture and wall surfaces into clean, calm, matte architectural surfaces with crisp planar edges. "
    "(3) REMOVE completely: all people, hands, burned-in subtitle text, small clutter, cables, receipts, price labels, "
    "loose napkins, and busy decorative micro-noise. "
    "Do NOT zoom, crop, shift, tilt, or re-center the camera. Clean realistic-matte architectural visualization."
)

JOBS = [
    (
        "v5_guac_naken_04.png",
        NAKEN_UNIVERSAL_045,
        [RAMAR / "guacamole_S4_raw.png"],
    ),
    (
        "v5_guac_regi_04_room.png",
        "Edit image 1 for a 3D RoomAnalysis engine (detail level 0.35 on a 0-to-1 scale — maximum planar geometric readability, "
        "zero clutter). Keep 100% exact 1:1 camera angle, perspective, 9:16 framing, and pixel positions. "
        "KEEP ONLY these core structural anchors as clean, matte, smooth solid architectural surfaces with razor-sharp plane edges: "
        "(1) the TWO-TIER split-level bar counter (higher flat copper-brown guest bar ledge on left/bottom AND the ~22 cm lower "
        "flat white staff worktop behind it, with an unmistakable crisp vertical step between the two tiers), "
        "(2) the rectangular back-bar stainless cooler block on the right-center, "
        "(3) the simplified geometric frame of the overhead rack, "
        "(4) the flat left wall plane, flat vertical-slat right wall plane, and clean ceiling grid. "
        "REMOVE COMPLETELY: both people, all white subtitle text, the cardboard receipt-rolls box, clear plastic bins, tangled cables, "
        "POS screen, individual liquor bottles/cans, small plant, paper flyers, and surface reflections. "
        "Even neutral soft lighting, sharp corners, zero clutter, zero borders, zero text.",
        [RAMAR / "guacamole_S4_raw.png"],
    ),
    (
        "v5_guac_regi_06_prod.png",
        "Edit image 1 into a 'good enough' simplified production backdrop (detail level 0.55 on a 0-to-1 scale) suitable as a clean "
        "semantic 3D / Seedance video reference that unmistakably resembles this specific Mexican bar without messy micro-clutter. "
        "Keep 100% exact 1:1 camera angle, perspective, 9:16 framing, and pixel positions. "
        "KEEP AND CLEANLY SIMPLIFY: the two-tier bar (warm satin copper guest bar top + clean white marble lower staff worktop), "
        "a clean simplified overhead wine-glass rack silhouette, simplified back-bar cooler with neat uniform dark bottle silhouettes, "
        "a simplified graphic warm-yellow/orange left mural motif, clean olive-wood slatted right wall, and clean ceiling. "
        "REMOVE COMPLETELY: both people, all white subtitle text, cardboard receipt-rolls box, messy wires/cables, plastic storage tub, "
        "receipt spike, flyers, and clutter. Warm cohesive bar lighting, clean editable aesthetic, no text, no borders.",
        [RAMAR / "guacamole_S4_raw.png"],
    ),
    (
        "v5_gelato_naken_04.png",
        NAKEN_UNIVERSAL_045,
        [RAMAR / "gelato_S1_raw.png"],
    ),
    (
        "v5_gelato_regi_04_room.png",
        "Edit image 1 for a 3D RoomAnalysis & simplified venue representation (detail level 0.40 on a 0-to-1 scale): "
        "it must remain unmistakably a gelato display showcase while stripping all people and micro-clutter for clean 3D reading. "
        "Keep 100% exact 1:1 camera angle, perspective, 9:16 portrait framing, and pixel positions. "
        "KEEP ONLY as clean, smooth, matte architectural geometry with crisp edges: "
        "(1) the glass gelato display case frame (horizontal top sneeze-guard ledge across the upper middle, angled side glass frames, "
        "and rectangular stainless-steel recessed well containing neat, simplified matte rectangular gelato pan trays in calm pastel tones "
        "so it clearly reads as a gelato counter without messy scoops/swirls), "
        "(2) the clean rear service counter plane and plain warm neutral back wall behind the counter. "
        "REMOVE COMPLETELY: the staff woman, her arm and hand holding the spoon, all white subtitle text ('Smakproverna vi ger kunder'), "
        "all dark flavor name signs/labels inside the pans, metal serving spatulas, Christmas candy canes, cups, bottles, and glass glare/reflections. "
        "Even clean lighting, razor-sharp furniture planes, zero text, zero people, zero borders.",
        [RAMAR / "gelato_S1_raw.png"],
    ),
    (
        "v5_gelato_regi_05_djup.png",
        "Image 1 is the original gelato-shop photo and image 2 is the exact same empty, clutter-free gelato display showcase "
        "with the staff person, hand, text, and glass glare removed. "
        "Keeping 100% EXACT pixel-for-pixel geometry, camera framing, 9:16 portrait aspect ratio, and object positions of image 2 "
        "(do NOT zoom, crop, shift, or re-center anything), render image 2 as a clean, machine-readable dense metric DEPTH MAP "
        "in standard Turbo colormap for 3D computer-vision ingestion: "
        "nearest foreground (bottom front stainless gelato pan rim and lower glass frame) = bright red/orange; "
        "middle row of recessed gelato pans and upper horizontal sneeze-guard glass shelf edge = bright yellow/yellow-green with "
        "RAZOR-SHARP step edges separating the elevated sneeze-guard ledge, the recessed interior pan wells, and the side glass frame; "
        "rear counter surface behind the showcase = cyan/light blue; "
        "farthest back wall = deep dark blue/indigo. "
        "Smooth planar depth gradients, crisp 3D occlusion boundaries, zero glass-reflection noise, zero text, zero labels, zero people, zero borders.",
        [RAMAR / "gelato_S1_raw.png", OUT / "v5_gelato_regi_04_room.png"],
    ),
]


def main() -> None:
    os.environ["CODEX_RAA"] = "1"
    log = {"start_kvot": codex_bild.kvot(), "anrop": []}
    print("Start kvot:", json.dumps(log["start_kvot"], ensure_ascii=False), flush=True)

    for fname, prompt, bilder in JOBS:
        ut = OUT / fname
        missing = [str(b) for b in bilder if not b.exists()]
        if missing:
            print(f"SKIP {fname}: saknar {missing}", flush=True)
            log["anrop"].append({"fil": fname, "status": "skip_missing", "missing": missing})
            continue
        if ut.exists():
            print(f"FINNS REDAN: {fname}", flush=True)
            log["anrop"].append({"fil": fname, "status": "cached"})
            continue

        print(f"\n>>> Kör Codex image_gen: {fname} (bilder={[b.name for b in bilder]})...", flush=True)
        t0 = time.perf_counter()
        full_prompt = (
            prompt
            + "\n\nUse your image generation tool now to produce exactly one image using the attached input image(s) "
            "(image 1, image 2 in order). Do not ask questions or write code. After generating the image, reply with: done."
        )
        try:
            post = codex_bild.generera(ut, full_prompt, bilder)
            dt = round(time.perf_counter() - t0, 1)
            ok = ut.exists()
            hel = post.get("prompt_fram", {}).get("hel")
            kv_ef = post.get("kvot_efter", {})
            print(f"<<< {fname}: ok={ok}, hel={hel}, {dt}s, kvot_primar={kv_ef.get('primar', {}).get('used_percent')}%", flush=True)
            log["anrop"].append({
                "fil": fname,
                "status": "ok" if ok else "failed",
                "exit": post.get("exit"),
                "hel": hel,
                "sekunder": dt,
                "kvot_efter": kv_ef,
            })
        except Exception as e:
            print(f"!!! FEL {fname}: {e}", flush=True)
            log["anrop"].append({"fil": fname, "status": "error", "fel": str(e)})

    log["slut_kvot"] = codex_bild.kvot()
    (OUT / "v5_prompt_ab_logg.json").write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== KLAR! Slutkvot:", json.dumps(log["slut_kvot"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
