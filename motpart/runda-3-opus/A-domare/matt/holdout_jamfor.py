# -*- coding: utf-8 -*-
"""Jämför ett systems påstående om hold-out-klippen mot spår A:s facit (holdout_facit/*.facit.json).

Påstående, generiskt format (ett spår fyller det ur sitt eget paket; se holdout_facit/README.md):
  {"<klipp-id>": {"rutor": {"<videoruta>": {"kamera_hojd_m": 1.48,
                                           "kamera_hojd_status": "matt" | "antagen",
                                           "matt": {"<namn>": 0.91}}}}}
Videorutan är rutans index i ORIGINALVIDEON (0-baserat), inte i en tagning.

Utfall per (klipp, ruta):
  metrologi-facit:   "inom" om värdet ligger i facits 90 %-intervall, annars "utanfor" (+ avstånd i cm)
  ordningsgränser:   "inom_granser" eller "utanfor_granser" (+ avstånd i cm)
  epistemik:         status "matt" där facit säger att golvet inte syns => "varning_matt_utan_golv"
                     (inget larm: ett system kan ha andra ledtrådar, men källan ska då redovisas)
  saknas:            facit har rutan men påståendet inte => "saknas" (räknas inte som inom)
Hela utfallet blir "larm" om någon post är utanför. Facit är en uppskattning; se facit-filerna.

  python holdout_jamfor.py --pastaende pas.json [--facit-mapp ../holdout_facit] [--logg ut.json]
  python holdout_jamfor.py --sjalvtest
"""
import argparse
import json
import sys
from pathlib import Path

FACIT = Path(__file__).resolve().parents[1] / "holdout_facit"


def las_facit(mapp: Path) -> dict:
    return {json.loads(f.read_text(encoding="utf-8"))["klipp"]: json.loads(f.read_text(encoding="utf-8"))
            for f in sorted(mapp.glob("*.facit.json"))}


def jamfor(facit: dict, pas: dict) -> dict:
    ut, n_ut, n_inom, n_saknas, n_varn = [], 0, 0, 0, 0
    for k, F in facit.items():
        P = (pas.get(k) or {}).get("rutor", {})
        for r in F["rutor"]:
            p = P.get(str(r["ruta"]))
            post = {"klipp": k, "ruta": r["ruta"]}
            if p is None or p.get("kamera_hojd_m") is None:
                if r.get("kamera_hojd_m") or any(x is not None for x in (r.get("kamera_hojd_granser_m") or [])):
                    post["utfall"] = "saknas"; n_saknas += 1
                    ut.append(post)
                continue
            v = float(p["kamera_hojd_m"]); post["varde"] = v
            if r.get("kamera_hojd_matbar"):
                f = r["kamera_hojd_m"]
                post["facit"] = [f["p05"], f["p95"]]
                if f["p05"] <= v <= f["p95"]:
                    post["utfall"] = "inom"; n_inom += 1
                else:
                    post["utfall"] = "utanfor"; n_ut += 1
                    post["avstand_cm"] = round(100 * (f["p05"] - v if v < f["p05"] else v - f["p95"]), 1)
                for namn, fm in (r.get("matt") or {}).items():
                    pv = (p.get("matt") or {}).get(namn)
                    if fm and pv is not None:
                        ok = fm["p05"] <= pv <= fm["p95"]
                        post.setdefault("matt", {})[namn] = {"varde": pv, "facit": [fm["p05"], fm["p95"]],
                                                            "utfall": "inom" if ok else "utanfor"}
                        n_ut += (not ok)
            else:
                lo, hi = (r.get("kamera_hojd_granser_m") or [None, None])
                post["granser"] = [lo, hi]
                if lo is not None and v < lo:
                    post["utfall"] = "utanfor_granser"; post["avstand_cm"] = round(100 * (lo - v), 1); n_ut += 1
                elif hi is not None and v > hi:
                    post["utfall"] = "utanfor_granser"; post["avstand_cm"] = round(100 * (v - hi), 1); n_ut += 1
                else:
                    post["utfall"] = "inom_granser"; n_inom += 1
                if p.get("kamera_hojd_status") == "matt":
                    post["epistemik"] = "varning_matt_utan_golv"; n_varn += 1
            ut.append(post)
    return {"utfall": "larm" if n_ut else "inom_alla", "antal_utanfor": n_ut, "antal_inom": n_inom,
            "antal_saknas": n_saknas, "antal_epistemikvarningar": n_varn, "poster": ut,
            "obs": "Facit är en uppskattning ur egen pixelmärkning; 'inom' betyder förenligt med facit, inte rätt."}


def sjalvtest() -> int:
    facit = {
        "X": {"klipp": "X", "rutor": [
            {"ruta": 10, "kamera_hojd_matbar": True, "kamera_hojd_m": {"p05": 1.36, "p50": 1.51, "p95": 1.61},
             "matt": {"bord": {"p05": 0.70, "p50": 0.74, "p95": 0.78}}},
            {"ruta": 50, "kamera_hojd_matbar": False, "kamera_hojd_granser_m": [0.95, 1.97]}]}}
    fall = {
        "ren_p50": ({"X": {"rutor": {"10": {"kamera_hojd_m": 1.51, "matt": {"bord": 0.74}},
                                     "50": {"kamera_hojd_m": 1.4, "kamera_hojd_status": "antagen"}}}}, "inom_alla", 0),
        "inj_kamera_+25cm": ({"X": {"rutor": {"10": {"kamera_hojd_m": 1.76, "matt": {"bord": 0.74}},
                                              "50": {"kamera_hojd_m": 1.4}}}}, "larm", 0),
        "inj_bord_platt_0.45": ({"X": {"rutor": {"10": {"kamera_hojd_m": 1.5, "matt": {"bord": 0.45}},
                                                 "50": {"kamera_hojd_m": 1.4}}}}, "larm", 0),
        "inj_under_ordningsgrans": ({"X": {"rutor": {"10": {"kamera_hojd_m": 1.5},
                                                     "50": {"kamera_hojd_m": 0.6}}}}, "larm", 0),
        "inj_matt_utan_golv": ({"X": {"rutor": {"10": {"kamera_hojd_m": 1.5},
                                                "50": {"kamera_hojd_m": 1.4, "kamera_hojd_status": "matt"}}}}, "inom_alla", 1),
        "inj_tomt_pastaende": ({}, "inom_alla", 0),
    }
    ratt = 0
    res = {}
    for namn, (pas, vantat, varn) in fall.items():
        r = jamfor(facit, pas)
        ok = r["utfall"] == vantat and r["antal_epistemikvarningar"] == varn
        if namn == "inj_tomt_pastaende":
            ok = ok and r["antal_saknas"] == 2 and r["antal_inom"] == 0
        ratt += ok
        res[namn] = {"vantat": vantat, "fick": r["utfall"], "saknas": r["antal_saknas"],
                     "varningar": r["antal_epistemikvarningar"], "ratt": ok}
        print(f"{'OK ' if ok else 'FEL'} {namn:28s} väntat={vantat:10s} fick={r['utfall']}")
    out = {"ratt": ratt, "av": len(fall), "fall": res,
           "obs": "Ett tomt påstående ger 'inom_alla' men antal_saknas > 0 och antal_inom = 0; läs alltid antalen."}
    Path(__file__).with_name("holdout_jamfor_sjalvtest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                                       encoding="utf-8")
    print(f"självtest: {ratt}/{len(fall)} rätt")
    return 0 if ratt == len(fall) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pastaende"); ap.add_argument("--facit-mapp", default=str(FACIT)); ap.add_argument("--logg")
    ap.add_argument("--sjalvtest", action="store_true")
    a = ap.parse_args()
    if a.sjalvtest:
        sys.exit(sjalvtest())
    r = jamfor(las_facit(Path(a.facit_mapp)), json.loads(Path(a.pastaende).read_text(encoding="utf-8")))
    txt = json.dumps(r, ensure_ascii=False, indent=1)
    if a.logg:
        Path(a.logg).write_text(txt, encoding="utf-8")
    print(txt)
    sys.exit(0 if r["utfall"] == "inom_alla" else 3)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
