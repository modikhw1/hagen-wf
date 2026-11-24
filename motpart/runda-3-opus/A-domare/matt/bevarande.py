# -*- coding: utf-8 -*-
"""Bevarande (mått c): ändrar en ändring något UTANFÖR sin räckvidd?

Jämför tillståndet före och efter en ändring och delar varje skillnad i "inom räckvidd" och
"utanför räckvidd". Räckvidden anges av den som gör ändringen (eller av routern) INNAN
ändringen körs, som en lista med sökvägsmönster (fnmatch) över det platta tillståndet.

Format som stöds:
  .json  — nästlad JSON; varje löv får en sökväg som "tagningar/2/personer/A/leder/14/0"
  .npz   — varje nyckel blir en sökväg; arrayer jämförs elementvis (max-avvikelse per nyckel)
  bild   — --bild-fore/--bild-efter (+ valfri --mask där ändring är tillåten, vit = tillåten)

Körning:
  python bevarande.py --fore a.json --efter b.json --rackvidd "tagningar/*/personer/A/*" \
        [--tol 0.001] [--logg ut.json]
  python bevarande.py --bild-fore a.png --bild-efter b.png --mask m.png [--pixtol 12]
  python bevarande.py --sjalvtest

Utfall: "bevarad" om noll skillnader utanför räckvidden över toleransen, annars "lackage"
med listan. Om INGEN skillnad finns inom räckvidden blir utfallet "ingen_andring"
(ändringen syns inte i tillståndet; det är ett eget fel, inte bevarande).

Toleransen är ett eget val (diagnos, inte ägarens krav). Standard 1 mm för meterfält.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path

import numpy as np


def platta(x, prefix="", ut=None):
    if ut is None:
        ut = {}
    if isinstance(x, dict):
        if not x and prefix:
            ut[prefix] = "{}"
        for k, v in x.items():
            platta(v, f"{prefix}/{k}" if prefix else str(k), ut)
    elif isinstance(x, list):
        if not x and prefix:
            ut[prefix] = "[]"
        for i, v in enumerate(x):
            platta(v, f"{prefix}/{i}" if prefix else str(i), ut)
    else:
        ut[prefix] = x
    return ut


def las(p: Path) -> dict:
    if p.suffix.lower() == ".npz":
        d = np.load(p, allow_pickle=False)
        return {k: np.asarray(d[k]) for k in d.files}
    return platta(json.loads(p.read_text(encoding="utf-8")))


def inom(vag: str, monster: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(vag, m) or fnmatch.fnmatchcase(vag, m.rstrip("/") + "/*") for m in monster)


def jamfor(a: dict, b: dict, monster: list[str], tol: float) -> dict:
    inne, ute = [], []
    for k in sorted(set(a) | set(b)):
        if k not in a:
            post = {"vag": k, "typ": "tillagd", "efter": _kort(b[k])}
        elif k not in b:
            post = {"vag": k, "typ": "borttagen", "fore": _kort(a[k])}
        else:
            va, vb = a[k], b[k]
            if isinstance(va, np.ndarray) or isinstance(vb, np.ndarray):
                va, vb = np.asarray(va), np.asarray(vb)
                if va.shape != vb.shape:
                    post = {"vag": k, "typ": "form", "fore": list(va.shape), "efter": list(vb.shape)}
                elif va.dtype.kind in "fiub" and vb.dtype.kind in "fiub":
                    d = np.abs(va.astype(float) - vb.astype(float))
                    d = d[np.isfinite(d)]
                    m = float(d.max()) if d.size else 0.0
                    if m <= tol and np.array_equal(np.isfinite(va.astype(float)), np.isfinite(vb.astype(float))):
                        continue
                    post = {"vag": k, "typ": "array", "max_avvikelse": m,
                            "andel_andrade": float((d > tol).mean()) if d.size else 0.0}
                else:
                    if np.array_equal(va, vb):
                        continue
                    post = {"vag": k, "typ": "array_ej_numerisk"}
            elif isinstance(va, bool) or isinstance(vb, bool) or not (
                    isinstance(va, (int, float)) and isinstance(vb, (int, float))):
                if va == vb:
                    continue
                post = {"vag": k, "typ": "varde", "fore": _kort(va), "efter": _kort(vb)}
            else:
                d = abs(float(va) - float(vb))
                if d <= tol or (np.isnan(float(va)) and np.isnan(float(vb))):
                    continue
                post = {"vag": k, "typ": "tal", "fore": va, "efter": vb, "avvikelse": d}
        (inne if inom(k, monster) else ute).append(post)
    if ute:
        utfall = "lackage"
    elif not inne:
        utfall = "ingen_andring"
    else:
        utfall = "bevarad"
    grupper = {}
    for p in ute:
        g = "/".join(p["vag"].split("/")[:2])
        grupper[g] = grupper.get(g, 0) + 1
    return {"utfall": utfall, "antal_inom": len(inne), "antal_utanfor": len(ute),
            "utanfor_per_grupp": grupper, "utanfor": ute[:200], "inom_prov": inne[:20]}


def _kort(v):
    s = v if isinstance(v, (int, float, bool)) or v is None else str(v)
    return s if not isinstance(s, str) else s[:80]


def jamfor_bild(fa: Path, fb: Path, mask: Path | None, pixtol: int) -> dict:
    import cv2
    a = cv2.imread(str(fa)).astype(int)
    b = cv2.imread(str(fb)).astype(int)
    if a.shape != b.shape:
        return {"utfall": "lackage", "orsak": f"olika storlek {a.shape} {b.shape}"}
    d = np.abs(a - b).max(axis=2) > pixtol
    if mask is not None:
        m = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE) > 127
    else:
        m = np.zeros(d.shape, bool)
    ute = float(d[~m].mean()) if (~m).any() else 0.0
    inne = float(d[m].mean()) if m.any() else 0.0
    utfall = "lackage" if ute > 0.002 else ("ingen_andring" if inne < 0.002 else "bevarad")
    return {"utfall": utfall, "andel_andrade_pixlar_utanfor": round(ute, 5),
            "andel_andrade_pixlar_inom": round(inne, 5), "gräns_utanfor": 0.002, "pixtol": pixtol}


def sjalvtest() -> int:
    rng = np.random.default_rng(0)
    bas = {
        "kamera": {"pos": [0.0, -2.0, 1.4], "f_px": 980.0},
        "objekt": [{"id": "bord_1", "pos": [0.0, 0.0, 0.37], "matt": [0.8, 0.8, 0.74]},
                   {"id": "stol_1", "pos": [0.5, 0.2, 0.22], "matt": [0.4, 0.4, 0.45]}],
        "personer": {"A": {"leder": rng.normal(size=(5, 3)).round(4).tolist()},
                     "B": {"leder": rng.normal(size=(5, 3)).round(4).tolist()}},
        "skarmtext": [{"text": "Hej", "t": [0.0, 2.0]}],
    }
    import copy
    fall = []

    def fall_(namn, efter, monster, vantat):
        r = jamfor(platta(bas), platta(efter), monster, 1e-3)
        fall.append({"fall": namn, "vantat": vantat, "fick": r["utfall"], "ratt": r["utfall"] == vantat,
                     "utanfor": r["antal_utanfor"]})

    e = copy.deepcopy(bas); e["personer"]["A"]["leder"][2][0] += 0.3
    fall_("ren_andring_inom", e, ["personer/A/*"], "bevarad")
    e = copy.deepcopy(bas)
    fall_("ingen_andring_alls", e, ["personer/A/*"], "ingen_andring")
    e = copy.deepcopy(bas); e["personer"]["A"]["leder"][2][0] += 0.3; e["personer"]["B"]["leder"][0][2] += 0.002
    fall_("inj_B_rubbad_2mm", e, ["personer/A/*"], "lackage")
    e = copy.deepcopy(bas); e["personer"]["A"]["leder"][2][0] += 0.3; e["kamera"]["pos"][2] = 1.35
    fall_("inj_kamera_flyttad", e, ["personer/A/*"], "lackage")
    e = copy.deepcopy(bas); e["personer"]["A"]["leder"][2][0] += 0.3; e["objekt"].pop(1)
    fall_("inj_stol_borttagen", e, ["personer/A/*"], "lackage")
    e = copy.deepcopy(bas); e["personer"]["A"]["leder"][2][0] += 0.3; e["skarmtext"][0]["text"] = "Hej!"
    fall_("inj_text_andrad", e, ["personer/A/*"], "lackage")
    e = copy.deepcopy(bas); e["personer"]["A"]["leder"][2][0] += 0.3; e["personer"]["B"]["leder"][0][2] += 0.0004
    fall_("brus_under_tol_0.4mm", e, ["personer/A/*"], "bevarad")
    e = copy.deepcopy(bas); e["skarmtext"][0]["text"] = "Välkommen"
    fall_("textbyte_inom_textlager", e, ["skarmtext/*"], "bevarad")

    # npz-läge
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        a = {"A": rng.normal(size=(30, 26, 3)), "B": rng.normal(size=(30, 26, 3))}
        b = {k: v.copy() for k, v in a.items()}
        b["A"][10:20] += 0.1
        np.savez(Path(td) / "a.npz", **a); np.savez(Path(td) / "b.npz", **b)
        r = jamfor(las(Path(td) / "a.npz"), las(Path(td) / "b.npz"), ["A"], 1e-3)
        fall.append({"fall": "npz_ren", "vantat": "bevarad", "fick": r["utfall"], "ratt": r["utfall"] == "bevarad"})
        b["B"][5, 3, 0] += 0.01
        np.savez(Path(td) / "c.npz", **b)
        r = jamfor(las(Path(td) / "a.npz"), las(Path(td) / "c.npz"), ["A"], 1e-3)
        fall.append({"fall": "npz_inj_B_1cm", "vantat": "lackage", "fick": r["utfall"], "ratt": r["utfall"] == "lackage"})
        # bildläge
        import cv2
        img = (rng.random((200, 120, 3)) * 255).astype(np.uint8)
        img2 = img.copy(); img2[50:100, 30:60] = 0
        mask = np.zeros((200, 120), np.uint8); mask[45:105, 25:65] = 255
        cv2.imwrite(str(Path(td) / "i1.png"), img); cv2.imwrite(str(Path(td) / "i2.png"), img2)
        cv2.imwrite(str(Path(td) / "m.png"), mask)
        r = jamfor_bild(Path(td) / "i1.png", Path(td) / "i2.png", Path(td) / "m.png", 12)
        fall.append({"fall": "bild_ren", "vantat": "bevarad", "fick": r["utfall"], "ratt": r["utfall"] == "bevarad"})
        img3 = img2.copy(); img3[150:160, 10:30] = 255 - img3[150:160, 10:30]
        cv2.imwrite(str(Path(td) / "i3.png"), img3)
        r = jamfor_bild(Path(td) / "i1.png", Path(td) / "i3.png", Path(td) / "m.png", 12)
        fall.append({"fall": "bild_inj_utanfor_mask", "vantat": "lackage", "fick": r["utfall"], "ratt": r["utfall"] == "lackage"})
    ok = sum(f["ratt"] for f in fall)
    for f in fall:
        print(f"{'OK ' if f['ratt'] else 'FEL'} {f['fall']:28s} väntat={f['vantat']:13s} fick={f['fick']}")
    print(f"självtest: {ok}/{len(fall)} rätt")
    Path(__file__).with_name("bevarande_sjalvtest.json").write_text(
        json.dumps({"ratt": ok, "av": len(fall), "fall": fall}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if ok == len(fall) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fore"); ap.add_argument("--efter")
    ap.add_argument("--rackvidd", nargs="*", default=[])
    ap.add_argument("--tol", type=float, default=1e-3)
    ap.add_argument("--bild-fore"); ap.add_argument("--bild-efter"); ap.add_argument("--mask")
    ap.add_argument("--pixtol", type=int, default=12)
    ap.add_argument("--logg")
    ap.add_argument("--sjalvtest", action="store_true")
    a = ap.parse_args()
    if a.sjalvtest:
        sys.exit(sjalvtest())
    if a.bild_fore:
        r = jamfor_bild(Path(a.bild_fore), Path(a.bild_efter), Path(a.mask) if a.mask else None, a.pixtol)
    else:
        if not (a.fore and a.efter):
            ap.error("--fore och --efter krävs")
        r = jamfor(las(Path(a.fore)), las(Path(a.efter)), a.rackvidd, a.tol)
        r["rackvidd"] = a.rackvidd
        r["tol"] = a.tol
    txt = json.dumps(r, ensure_ascii=False, indent=1, default=float)
    if a.logg:
        Path(a.logg).write_text(txt, encoding="utf-8")
    print(f"BEVARANDE: {r['utfall']}  (utanför: {r.get('antal_utanfor', '-')}, inom: {r.get('antal_inom', '-')})")
    for p in r.get("utanfor", [])[:15]:
        print("  utanför:", json.dumps(p, ensure_ascii=False, default=float)[:160])
    sys.exit(0 if r["utfall"] == "bevarad" else 3)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
