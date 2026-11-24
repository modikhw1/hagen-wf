"""rum_jamfor.py — jämför obs.json + recept.json mellan två körningar (t.ex. Argons lagrade mot omkörning).

    python rum_jamfor.py <mapp_A> <mapp_B> [--json ut.json]

<mapp> innehåller obs.json och recept.json (t.ex. forvarld_karna/ut/notan eller rum_ut/med_dekl/notan).
Skriver en kort textrapport: bindningar (vid/pa), roller, kamera-delning, noder (tagningar, conf),
sluttro, P per tagning, osäkerhet per tagning och avstånd mellan rollerna A, B (C).
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib


def las(mapp: pathlib.Path):
    obs = json.loads((mapp / "obs.json").read_text(encoding="utf-8"))
    rec = json.loads((mapp / "recept.json").read_text(encoding="utf-8"))
    return obs, rec


def obs_sammandrag(obs):
    ut = {}
    for k in obs["klipp"]:
        dets = []
        for d in k["detektioner"]:
            dets.append(dict(id=d["id"], nyckel=d.get("nyckel"), unik=d.get("unik"), pose=d.get("pose"),
                             vid=d.get("vid"), pa=d.get("pa"), djup=d["djup_m"]["v"], bearing=d["bearing_deg"]["v"]))
        ut[k["klipp"]] = dict(
            dets=dets,
            delar_kamera_med=k.get("delar_kamera_med"),
            manhattan=(k.get("manhattan_deg") or {}).get("v"),
            ljus=(k.get("ljus_bearing_deg") or {}).get("v"),
            skala=k.get("skala"),
            hfov=k["kamera"]["hfov_deg"]["v"],
            hojd=k["kamera"]["hojd_m"]["v"],
            pitch=k["kamera"]["pitch_deg"]["v"],
        )
    return ut


def recept_sammandrag(rec):
    noder = {n["id"]: dict(klass=n["klass"], nyckel=n.get("nyckel"), pos=[round(x, 3) for x in n["position"]],
                           conf=n["confidence_score"], tagn=n["evidence_shots"], zon=n.get("zon") is not None)
             for n in rec["noder"]}
    roller = {i: noder[i]["pos"] for i in ("A", "B", "C") if i in noder}
    avst = {}
    for a in roller:
        for b in roller:
            if a < b:
                avst[f"{a}-{b}"] = round(math.dist(roller[a][:2], roller[b][:2]), 3)
    logg = [dict(klipp=r["klipp"], tro=r["tro"], P=r["sannolikhet"], osak=r["osakerhet_m"],
                 omprovning=bool(r["omprovning"])) for r in rec["logg"]]
    kameror = {c["id"]: dict(pos=[round(x, 3) for x in c["position"]], rot=c["rotation"]) for c in rec["kameror"]}
    return dict(tro=rec["tro"], P=rec["sannolikhet"], noder=noder, avstand=avst, logg=logg, kameror=kameror,
                rum=rec["rum"]["granser"])


def bindningar(os_):
    """Kompakt: per tagning, lista 'nyckel[pose] vid=..' och 'foremal pa=..'."""
    ut = {}
    for k, v in os_.items():
        rad = []
        for d in v["dets"]:
            if d["nyckel"] and d["nyckel"].startswith("person"):
                rad.append(f"{d['id']}:{d['nyckel']}/{d['pose']}" + (f" vid {d['vid']}" if d["vid"] else ""))
            elif d["nyckel"] and d["nyckel"].startswith("foremal"):
                rad.append(f"{d['id']}:{d['nyckel'].split(':')[1]}" + (f" pa {d['pa']}" if d["pa"] else " pa -"))
            else:
                rad.append(f"{d['id']}:{d['nyckel']}")
        ut[k] = rad
    return ut


def jamfor(a: pathlib.Path, b: pathlib.Path):
    oa, ra = las(a)
    ob, rb = las(b)
    sa, sb = obs_sammandrag(oa), obs_sammandrag(ob)
    qa, qb = recept_sammandrag(ra), recept_sammandrag(rb)
    rap = {"A": str(a), "B": str(b), "obs": {}, "recept": {}}
    ba, bb = bindningar(sa), bindningar(sb)
    for k in sorted(set(sa) | set(sb), key=lambda s: int(s[1:])):
        x, y = sa.get(k), sb.get(k)
        if x is None or y is None:
            rap["obs"][k] = "saknas i en körning"
            continue
        dd = {}
        if ba[k] != bb[k]:
            dd["bindningar"] = {"A": ba[k], "B": bb[k]}
        for f in ("delar_kamera_med", "manhattan", "ljus", "skala", "hfov", "hojd", "pitch"):
            if x[f] != y[f]:
                dd[f] = {"A": x[f], "B": y[f]}
        if len(x["dets"]) == len(y["dets"]):
            dmax = max((abs(p["djup"] - q["djup"]) for p, q in zip(x["dets"], y["dets"])), default=0.0)
            if dmax > 1e-6:
                dd["djup_maxdiff_m"] = round(dmax, 4)
        rap["obs"][k] = dd or "identisk"
    rr = {}
    for f in ("tro", "P", "avstand", "rum"):
        rr[f] = {"A": qa[f], "B": qb[f]}
    nd = {}
    for n in sorted(set(qa["noder"]) | set(qb["noder"])):
        x, y = qa["noder"].get(n), qb["noder"].get(n)
        if x is None or y is None:
            nd[n] = {"A": x, "B": y}
        elif (x["tagn"], x["conf"], x["pos"]) != (y["tagn"], y["conf"], y["pos"]):
            nd[n] = {"A": (x["tagn"], x["conf"], x["pos"]), "B": (y["tagn"], y["conf"], y["pos"])}
    rr["noder_som_skiljer"] = nd
    rr["noder_A"] = {n: (v["tagn"], v["conf"]) for n, v in qa["noder"].items()}
    rr["noder_B"] = {n: (v["tagn"], v["conf"]) for n, v in qb["noder"].items()}
    rr["logg_A"] = [(r["klipp"], r["tro"], r["P"], r["osak"].get("B")) for r in qa["logg"]]
    rr["logg_B"] = [(r["klipp"], r["tro"], r["P"], r["osak"].get("B")) for r in qb["logg"]]
    rap["recept"] = rr
    return rap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--json", default=None)
    x = ap.parse_args()
    rap = jamfor(pathlib.Path(x.a), pathlib.Path(x.b))
    txt = json.dumps(rap, ensure_ascii=False, indent=1)
    if x.json:
        pathlib.Path(x.json).write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
