"""Kör rumshjärnan och skriv kartor, logg, recept och Jutsu-skript.

    scen/.venv/Scripts/python.exe byggsten/rumshypotes/kor.py syntet [--avstand 5.0] [--fro 7]
    scen/.venv/Scripts/python.exe byggsten/rumshypotes/kor.py <obs.json> --ut <mapp>

Utdata i ut/<namn>/: obs.json, karta_<klipp>.png, karta_tidslinje.png, LOGG.md,
recept.json, jutsu_bygg.py och, för syntetiska prov, jamforelse.json.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
import time

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIT))

import syntet  # noqa: E402
from hjarna import D2R, beskriv, karna, kor, logg  # noqa: E402
from jutsu_adapter import skript  # noqa: E402
from karta import rita, tidslinje  # noqa: E402
from recept import bygg  # noqa: E402
from telemetri import Observationer  # noqa: E402


def facit_punkter(f: dict) -> dict:
    p = {f"cam_{kid}": (c[0], c[1]) for kid, _, c, *_ in f["klipp"]}
    p.update({n: v["pos"] for n, v in f["personer"].items()})
    p.update(dict(f["bord"]))
    p.update({n: v["pos"] for n, v in f["dorrar"].items()})
    return p


def facit_i_ram(f: dict, h) -> dict:
    """Facit flyttat in i hjärnans ram via första kameran (samma ankare som hjärnan använder)."""
    _, _, (gx, gy, _), yaw, *_ = f["klipp"][0]
    rho = h.x["cam"][0][2] - yaw * D2R
    c, s = math.cos(rho), math.sin(rho)
    return {n: (c * (x - gx) - s * (y - gy), s * (x - gx) + c * (y - gy)) for n, (x, y) in facit_punkter(f).items()}


def jamfor(f: dict, h, obs) -> dict:
    """Stel passning (Kabsch) av facit mot hjärnans kameror; sedan fel per sak."""
    K = len(obs.klipp)
    gt = facit_punkter(f)
    par = [(np.array(gt[f"cam_{obs.klipp[k].klipp}"]), h.x["cam"][k][:2]) for k in range(K)]
    A = np.array([a for a, _ in par])
    B = np.array([b for _, b in par])
    ca, cb = A.mean(0), B.mean(0)
    U, _, Vt = np.linalg.svd((A - ca).T @ (B - cb))
    Rm = (U @ Vt).T
    if np.linalg.det(Rm) < 0:
        Vt[-1] *= -1
        Rm = (U @ Vt).T

    def T(p):
        return Rm @ (np.array(p) - ca) + cb

    ut = {"kameror_m": {}, "saker_m": {}}
    for k in range(K):
        kid = obs.klipp[k].klipp
        ut["kameror_m"][kid] = round(float(np.linalg.norm(T(gt[f"cam_{kid}"]) - h.x["cam"][k][:2])), 3)
    for eid, e in h.ents.items():
        if e.till is not None:
            continue
        kand = [n for n in gt if not n.startswith("cam_") and (n == eid.split("@")[0] or n.startswith(e.klass))]
        if kand:
            n = min(kand, key=lambda n: np.linalg.norm(T(gt[n]) - h.x["ent"][eid]))
            ut["saker_m"][eid] = {"facit": n, "fel_m": round(float(np.linalg.norm(T(gt[n]) - h.x["ent"][eid])), 3)}
    bord = sorted(e for e in h.ents if h.ents[e].klass == "bord")
    if len(bord) >= 2:
        d = float(np.linalg.norm(h.x["ent"][bord[0]] - h.x["ent"][bord[1]]))
        g = (float(np.linalg.norm(np.array(f["bord"]["bord_1"]) - np.array(f["bord"]["bord_2"])))
             if "bord_2" in f["bord"] else None)
        ut["bordsavstand_m"] = {"skattat": round(d, 3), "facit": g}
    x0, x1, y0, y1 = h.x["rum"][0]
    fx0, fx1, fy0, fy1 = f["rum"]
    ut["rum_m"] = {"skattat": sorted([round(float(x1 - x0), 2), round(float(y1 - y0), 2)]),
                   "facit": sorted([fx1 - fx0, fy1 - fy0])}
    return ut


def skriv_logg(rader, fil, tid):
    L = [f"# Hypoteslogg ({tid:.1f} s)", ""]
    for r in rader:
        L.append(f"## {r['klipp']}: {r['tro']} (P {r['sannolikhet']:.2f})")
        L.append(f"- Klippet tillför: {r['bidrag']}")
        if r["omprovning"]:
            L.append(f"- **Omprövning.** {r['omprovning']}")
        for hh in r["hypoteser"][1:3]:
            L.append(f"- Alternativ ({hh['sannolikhet']:.2f}): {hh['beskrivning']}  `{hh['termer']}`")
        L.append(f"- Osäkerhet (m): {r['osakerhet_m']}")
        L.append("")
    pathlib.Path(fil).write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kalla")
    ap.add_argument("--avstand", type=float, default=5.0)
    ap.add_argument("--fro", type=int, default=7)
    ap.add_argument("--beam", type=int, default=None)
    ap.add_argument("--ut", default=None)
    ap.add_argument("--delat", action="store_true", help="kontroll: A och B vid samma bord")
    a = ap.parse_args()
    f = None
    if a.kalla == "syntet":
        f = syntet.facit(a.avstand, delat=a.delat)
        obs = syntet.simulera(f, a.fro)
        ut = pathlib.Path(a.ut or HIT / "ut" / "syntet")
    else:
        obs = Observationer.model_validate_json(pathlib.Path(a.kalla).read_text(encoding="utf-8"))
        ut = pathlib.Path(a.ut or HIT / "ut" / obs.klipp_id)
    ut.mkdir(parents=True, exist_ok=True)
    (ut / "obs.json").write_text(obs.model_dump_json(indent=1), encoding="utf-8")
    t = time.time()
    hist = kor(obs, a.beam)
    tid = time.time() - t
    rader = logg(hist, obs)
    filer = []
    xs, ys = [], []
    for st in hist:
        hh = st.stråle[0]
        x0, x1, y0, y1 = hh.x["rum"][0]
        xs += [x0, x1] + [hh.x["cam"][k][0] for k in range(st.k + 1)]
        ys += [y0, y1] + [hh.x["cam"][k][1] for k in range(st.k + 1)]
        if f:
            for px, py in facit_i_ram(f, hh).values():
                xs.append(px)
                ys.append(py)
    ram = (min(xs) - 0.8, max(xs) + 0.8, min(ys) - 0.8, max(ys) + 0.8)
    for st, rad in zip(hist, rader):
        h, K = st.stråle[0], st.k + 1
        h = next(c for c in st.stråle if karna(c, obs, K) == rad["tro"])
        alt = next((c for c, p in zip(st.stråle, st.sannolikhet)
                    if p > 0.08 and karna(c, obs, K) != rad["tro"]), None)
        titel = f"{st.klipp}: {rad['tro']}\nP {rad['sannolikhet']:.2f}"
        if alt is not None:
            pa = st.sannolikhet[st.stråle.index(alt)]
            titel += f"   alt ({pa:.2f}): {karna(alt, obs, K)}"
        fil = ut / f"karta_{st.klipp}.png"
        rita(h, obs, K, fil, titel, alt=alt, facit=facit_i_ram(f, h) if f else None, ram=ram)
        filer.append(fil)
    tidslinje(filer, ut / "karta_tidslinje.png")
    skriv_logg(rader, ut / "LOGG.md", tid)
    recept = bygg(hist, obs, rader)
    (ut / "recept.json").write_text(recept.model_dump_json(indent=1), encoding="utf-8")
    (ut / "jutsu_bygg.py").write_text(skript(recept), encoding="utf-8")
    print(f"hjärnan: {tid:.1f} s, {sum(len(s.alla) for s in hist)} lösta hypoteser")
    for r in rader:
        print(f"{r['klipp']}: {r['tro']}  P {r['sannolikhet']:.2f}  | {r['bidrag']}")
        if r["omprovning"]:
            print("   OMPRÖVNING:", r["omprovning"])
    if f:
        j = jamfor(f, hist[-1].stråle[0], obs)
        (ut / "jamforelse.json").write_text(json.dumps(j, indent=1, ensure_ascii=False), encoding="utf-8")
        print("jämförelse:", json.dumps(j, ensure_ascii=False))
    print("ut:", ut)


if __name__ == "__main__":
    main()
