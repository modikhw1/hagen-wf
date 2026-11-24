# -*- coding: utf-8 -*-
"""Sammanställer ägarpanelen: läser svar.json + nyckel.json.

    .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-4\\A-domare\\panel\\sammanstall.py [--svar svar.json] [--session s_x]

Per par gäller det senaste svaret (över alla sessioner, eller bara --session).
Skriver utfallet till stdout och till sammanstallning.json bredvid svarsfilen.
Giltighet (K2): ogiltig om något kontrollpar inte fälls.
  saknas  -> fälls om a = nej
  annat   -> fälls om b = nej eller delvis
  fel_scen (1:1) -> fälls om samma_scen = nej
Förslag till tröskel (SYFTE §4 K2): ja på både a och b i minst 70 % av de riktiga ändringsparen.
Det är ägarens tröskel att sätta; siffran här är diagnos.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PANEL = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--svar", default=str(PANEL / "svar.json"))
    ap.add_argument("--session", default=None)
    arg = ap.parse_args()
    svarfil = Path(arg.svar)
    nyckel = json.loads((PANEL / "nyckel.json").read_text(encoding="utf-8"))
    nyck = {p["id"]: p for p in nyckel["par"]}
    svar = json.loads(svarfil.read_text(encoding="utf-8")) if svarfil.exists() else []
    if arg.session:
        svar = [s for s in svar if s.get("session") == arg.session]
    sessioner = sorted({s.get("session") for s in svar})
    senast: dict[str, dict] = {}
    for s in svar:  # listan är i tidsordning; senare skriver över
        if s.get("par") in nyck:
            senast[s["par"]] = s

    rader = []
    for pid in nyckel["ordning"]:
        k, s = nyck[pid], senast.get(pid)
        rader.append({"nr": nyckel["ordning"].index(pid) + 1, "id": pid, "sektion": k["sektion"], "system": k["system"],
                      "klipp": k.get("klipp"), "andringstyp": k["andringstyp"], "kontroll": k.get("kontroll"),
                      "mening": k.get("mening"), "a": s and s.get("a"), "b": s and s.get("b"),
                      "samma_scen": s and s.get("samma_scen"), "kommentar": s and s.get("kommentar"),
                      "sekunder": s and s.get("sekunder"), "egna_matt_D": k.get("egna_matt_D")})

    # kontrollpar
    kontroller = []
    for r in rader:
        if not r["kontroll"]:
            continue
        if r["kontroll"] == "saknas":
            falld = r["a"] == "nej" if r["a"] else None
        elif r["kontroll"] == "annat":
            falld = r["b"] in ("nej", "delvis") if r["b"] else None
        else:
            falld = r["samma_scen"] == "nej" if r["samma_scen"] else None
        kontroller.append({"nr": r["nr"], "kontroll": r["kontroll"], "system_stil": r["system"], "mening": r["mening"],
                           "a": r["a"], "b": r["b"], "samma_scen": r["samma_scen"], "falld": falld})
    besvarade_k = [k for k in kontroller if k["falld"] is not None]
    if len(besvarade_k) < len(kontroller):
        giltighet = "ofullständig: alla kontrollpar är inte besvarade"
    elif all(k["falld"] for k in kontroller):
        giltighet = "giltig: alla kontrollpar fälldes"
    else:
        giltighet = "OGILTIG: minst ett kontrollpar fälldes inte"

    def tabell(grupp_nyckel, sektion):
        g = defaultdict(lambda: {"n": 0, "besvarade": 0, "a_ja": 0, "b_ja": 0, "bada_ja": 0, "a_delvis": 0, "b_delvis": 0,
                                 "samma_ja": 0, "samma_delvis": 0})
        for r in rader:
            if r["sektion"] != sektion or r["kontroll"]:
                continue
            x = g[r[grupp_nyckel]]
            x["n"] += 1
            if sektion == "andring" and r["a"] and r["b"]:
                x["besvarade"] += 1
                x["a_ja"] += r["a"] == "ja"
                x["b_ja"] += r["b"] == "ja"
                x["a_delvis"] += r["a"] == "delvis"
                x["b_delvis"] += r["b"] == "delvis"
                x["bada_ja"] += r["a"] == "ja" and r["b"] == "ja"
            if sektion == "ett_till_ett" and r["samma_scen"]:
                x["besvarade"] += 1
                x["samma_ja"] += r["samma_scen"] == "ja"
                x["samma_delvis"] += r["samma_scen"] == "delvis"
        return dict(g)

    riktiga = [r for r in rader if r["sektion"] == "andring" and not r["kontroll"] and r["a"] and r["b"]]
    bada = sum(r["a"] == "ja" and r["b"] == "ja" for r in riktiga)
    ut = {
        "svarsfil": svarfil.name, "sessioner": sessioner, "antal_svar_totalt": len(svar),
        "besvarade_par": len(senast), "par_totalt": len(rader),
        "giltighet": giltighet, "kontrollpar": kontroller,
        "andring_per_system": tabell("system", "andring"),
        "andring_per_typ": tabell("andringstyp", "andring"),
        "ett_till_ett_per_system": tabell("system", "ett_till_ett"),
        "k2_diagnos": {"riktiga_andringspar_besvarade": len(riktiga), "ja_pa_bada": bada,
                       "andel": round(bada / len(riktiga), 3) if riktiga else None,
                       "forslag_trosket": 0.70, "not": "Förslag till tröskel, ägarens att sätta. Ogiltig omgång räknas inte."},
        "rader": rader,
    }
    (svarfil.parent / (svarfil.stem + "_sammanstallning.json")).write_text(
        json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")

    p = print
    p(f"Svar: {len(svar)} i {svarfil.name}, sessioner {sessioner}, besvarade par {len(senast)}/{len(rader)}")
    p(f"GILTIGHET: {giltighet}")
    for k in kontroller:
        p(f"  kontroll nr {k['nr']:>2} {k['kontroll']:<8} a={k['a']} b={k['b']} scen={k['samma_scen']} -> fälld={k['falld']}")
    p("\nÄndringspar per system (n, besvarade, a=ja, b=ja, båda ja):")
    for s, x in ut["andring_per_system"].items():
        p(f"  {s:<62} {x['n']:>2} {x['besvarade']:>2}  a={x['a_ja']} b={x['b_ja']} båda={x['bada_ja']}")
    p("\nÄndringspar per ändringstyp:")
    for s, x in ut["andring_per_typ"].items():
        p(f"  {s:<30} {x['n']:>2} {x['besvarade']:>2}  a={x['a_ja']} b={x['b_ja']} båda={x['bada_ja']}")
    p("\n1:1 per system (n, besvarade, ja, delvis):")
    for s, x in ut["ett_till_ett_per_system"].items():
        p(f"  {s:<62} {x['n']:>2} {x['besvarade']:>2}  ja={x['samma_ja']} delvis={x['samma_delvis']}")
    d = ut["k2_diagnos"]
    p(f"\nK2-diagnos: ja på båda i {d['ja_pa_bada']}/{d['riktiga_andringspar_besvarade']} riktiga ändringspar"
      f" ({d['andel']}); förslag 0,70. {'Räknas inte: omgången är inte giltig.' if not giltighet.startswith('giltig') else ''}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
