# -*- coding: utf-8 -*-
"""Prövning av Neons Exp 4/6 (virtuell djupsensor) mot ett oberoende ordningsfacit.

Facit: punktpar i ORIGINALRUTAN (guacamole S4, videoruta 244 = Neons guacamole_S4_raw.png) där
det syns vilken punkt som är närmast kameran: skymning (A ligger framför B) eller perspektiv inom
samma plan (takplattornas fogar tätnar, likadana glas blir mindre). Märkt av spår A från råbilden;
ingen djupmodell används för facit. Paren delas i:
  - "promptstyrd": promptens färgordning (v4_guac_S4_djupplan.png.codex.json) bestämmer svaret
  - "fri": prompten säger inget om ordningen (inom samma yta, eller tak mot vägg där prompten
           påstår att taket är längst bort)

Jämförs: den genererade Turbo-djupkartan (Neons avkodning, kopierad), MoGe (ingestens djup) och
en slumpbaslinje. Dessutom felinjektion mot Neons eget mått "kantalignering": samma mått på
(a) tom-bild mot djupkarta (Neons), (b) RÅBILD mot djupkarta, (c) tom-bild mot djupkarta från ett
annat klipp (gelato, negativ kontroll), (d) tom-bild mot djupkarta förskjuten 24 px.

Kör: python prov_djupsensor.py   -> prov_djupsensor.json + prov_djupsensor.png
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

HIT = Path(__file__).resolve().parent
ROT = HIT.parents[3]
R2 = ROT / "motpart/runda-2-neon"
RAW = R2 / "djup_gt_ramar/guacamole_S4_raw.png"
GEN = R2 / "djup_v4_sensor/v4_guac_S4_djupplan.png"
TOM = R2 / "djup_v4_sensor/v4_guac_S4_tom.png"
GEL = R2 / "djup_v5_prompt_ab/v5_gelato_regi_05_djup.png"
MOGE = ROT / "scen/3d/ingest/ut/e-dialog-guacamole-tagningar/S4/rum/depth/0054.npz"

# (namn, närmare punkt (x,y), längre bort punkt (x,y), typ, belägg i råbilden)
PAR = [
    ("tak_nara_vs_tak_langre", (450, 40), (450, 300), "fri",
     "takplattornas fogar tätnar mot väggen vid y~340; samma plan, punkten högst upp ligger närmast"),
    ("tak_nara_vs_tak_mitten", (520, 120), (380, 260), "fri", "samma takplan, perspektiv"),
    ("tak_nara_vs_traviagg", (450, 40), (470, 450), "fri",
     "taket rakt ovanför kameran mot slatväggen bakom disken; prompten säger tak = längst bort"),
    ("tak_nara_vs_flaskor", (520, 20), (330, 540), "fri",
     "tak ovanför kameran mot flaskorna i bakbaren; prompten säger tak = längst bort"),
    ("stort_glas_vs_litet_glas", (40, 110), (230, 430), "fri",
     "likadana vinglas i samma hängställ; glaset uppe till vänster är flera gånger större"),
    ("koppardisk_nara_vs_koppardisk_bort", (300, 1000), (30, 640), "fri",
     "samma gästdisk; den löper bort åt vänster där A sitter"),
    ("vit_bank_nara_vs_vit_bank_bort", (300, 870), (200, 700), "fri",
     "samma vita arbetsbänk; kvittolådan längre in är mindre"),
    ("glasstall_vs_muralvagg", (60, 330), (150, 520), "promptstyrd", "glasstället skymmer muralen"),
    ("flaskor_vs_traviagg", (330, 530), (480, 400), "promptstyrd", "flaskorna står framför slatväggen"),
    ("kassaskarm_vs_kylskap", (330, 690), (370, 620), "promptstyrd", "kassaskärmen skymmer kylen"),
    ("koppardisk_vs_vit_bank", (300, 980), (300, 860), "promptstyrd", "koppardisken skymmer bänkens framkant"),
]


def avkoda_turbo(bgr: np.ndarray) -> np.ndarray:
    """Kopia av Neons avkoda_turbo_djup (djup_v4_full_sensor_audit.py:87-101): 0 = närmast, 1 = längst bort."""
    ramp = np.arange(256, dtype=np.uint8).reshape(256, 1)
    lut = cv2.applyColorMap(ramp, cv2.COLORMAP_TURBO).reshape(256, 3).astype(np.float32)
    h, w = bgr.shape[:2]
    out = np.zeros((h, w), np.float32)
    f = bgr.astype(np.float32)
    for y0 in range(0, h, 64):
        blk = f[y0:y0 + 64].reshape(-1, 1, 3)
        idx = np.argmin(np.sum((blk - lut[None]) ** 2, axis=2), axis=1).astype(np.float32)
        out[y0:y0 + 64] = (1.0 - idx / 255.0).reshape(-1, w)
    return out


def prov(d: np.ndarray, p, r=4):
    x, y = p
    v = d[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1]
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else float("nan")


def kantalign(a_bgr, d_bgr):
    """Neons mått (djup_v4_full_sensor_audit.py:166-169)."""
    c_a = cv2.Canny(cv2.cvtColor(a_bgr, cv2.COLOR_BGR2GRAY), 60, 150)
    c_d = cv2.Canny(cv2.cvtColor(d_bgr, cv2.COLOR_BGR2GRAY), 40, 120)
    c_a = cv2.dilate(c_a, np.ones((9, 9), np.uint8))
    return round(100.0 * float((c_d[c_a > 0] > 0).sum()) / max(1, int((c_d > 0).sum())), 1)


def main():
    raw = cv2.imread(str(RAW))
    H, W = raw.shape[:2]
    gen_bgr = cv2.resize(cv2.imread(str(GEN)), (W, H), interpolation=cv2.INTER_AREA)
    tom = cv2.resize(cv2.imread(str(TOM)), (W, H), interpolation=cv2.INTER_AREA)
    gel = cv2.resize(cv2.imread(str(GEL)), (W, H), interpolation=cv2.INTER_AREA)
    d_gen = avkoda_turbo(gen_bgr)
    z = cv2.resize(np.load(MOGE)["depth"].astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    z[~np.isfinite(z)] = np.nan
    rng = np.random.default_rng(0)
    rader = []
    for namn, a, b, typ, belagg in PAR:
        ga, gb = prov(d_gen, a), prov(d_gen, b)
        ma, mb = prov(z, a), prov(z, b)
        rader.append({
            "par": namn, "typ": typ, "belagg": belagg, "nara": a, "bort": b,
            "gen": [round(ga, 3), round(gb, 3)], "gen_ratt": bool(ga < gb - 0.01),
            "gen_lika": bool(abs(ga - gb) <= 0.01),
            "moge": [None if np.isnan(ma) else round(ma, 2), None if np.isnan(mb) else round(mb, 2)],
            "moge_ratt": None if (np.isnan(ma) or np.isnan(mb)) else bool(ma < mb),
        })

    def sammanf(typ):
        rr = [r for r in rader if r["typ"] == typ]
        m = [r for r in rr if r["moge_ratt"] is not None]
        return {"n": len(rr), "gen_ratt": sum(r["gen_ratt"] for r in rr), "gen_lika_(platt)": sum(r["gen_lika"] for r in rr),
                "moge_ratt": sum(r["moge_ratt"] for r in m), "moge_matbara": len(m)}

    skift = np.roll(gen_bgr, 24, axis=1)
    brus = cv2.applyColorMap((rng.random((H, W)) * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
    kant = {
        "a_neon_tom_mot_djup": kantalign(tom, gen_bgr),
        "b_rabild_mot_djup": kantalign(raw, gen_bgr),
        "c_neg_kontroll_tom_guac_mot_djup_gelato": kantalign(tom, gel),
        "d_inj_djup_forskjuten_24px": kantalign(tom, skift),
    }
    hal = {
        "gen_andel_hal_pct": round(100 * float((~np.isfinite(d_gen)).mean()), 2),
        "neg_kontroll_slumpbrus_turbo_andel_hal_pct": round(100 * float((~np.isfinite(avkoda_turbo(brus))).mean()), 2),
        "moge_andel_hal_pct": round(100 * float(np.isnan(z).mean()), 2),
    }
    ut = {
        "facit": "ordning ur skymning och perspektiv i råbilden, märkt av spår A (ingen djupmodell)",
        "par": rader,
        "sammanfattning": {"fri": sammanf("fri"), "promptstyrd": sammanf("promptstyrd")},
        "kantalignering_felinjektion": kant,
        "hal": hal,
        "prompt_utdrag": json.loads((GEN.parent / (GEN.name + ".codex.json")).read_text(encoding="utf-8"))["prompt"][:700],
    }
    (HIT / "prov_djupsensor.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
    # bild: råbild med paren + genererad + MoGe
    vis = []
    zz = np.where(np.isfinite(z), z, np.nanmax(z))
    lo, hi = np.nanpercentile(z, 2), np.nanpercentile(z, 98)
    zc = cv2.applyColorMap((255 * (1 - np.clip((zz - lo) / (hi - lo), 0, 1))).astype(np.uint8), cv2.COLORMAP_TURBO)
    for im in (raw.copy(), gen_bgr.copy(), zc):
        for r in rader:
            col = (0, 255, 0) if r["typ"] == "fri" else (255, 0, 255)
            cv2.arrowedLine(im, tuple(r["nara"]), tuple(r["bort"]), col, 2, tipLength=0.04)
            cv2.circle(im, tuple(r["nara"]), 6, (255, 255, 255), -1)
        vis.append(im)
    for i, txt in enumerate(["rabild + par (vit = nara)", "genererad djupkarta", "MoGe"]):
        cv2.putText(vis[i], txt, (8, H - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.imwrite(str(HIT / "prov_djupsensor.png"), np.hstack(vis))
    print(json.dumps({k: v for k, v in ut.items() if k in ("sammanfattning", "kantalignering_felinjektion", "hal")},
                     ensure_ascii=False, indent=1))
    for r in rader:
        print(f"{r['typ']:11s} {r['par']:36s} gen={r['gen']} rätt={r['gen_ratt']}  moge={r['moge']} rätt={r['moge_ratt']}")


if __name__ == "__main__":
    main()
