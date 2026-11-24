"""Felinjektion: visar att varje grind kan larma. "0 fel" räknas bara för grindar som larmar här (PROTOKOLL.md:8).

För varje injektion väljs en (tagning, person) där grinden är ok i det omuterade paketet; felet injiceras i en kopia
och grinden ska då ge FEL för samma rad. Samma injektioner körs mot originalets grindar (`byggsten/brygga/grindar.py`)
för jämförelse (A3).
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import numpy as np

from rotation import mat_till_quat, quat_till_mat


def _person_xyz(p, pid, sid, fn):
    for sp in p["rorelse"][pid]:
        if sp["tagning"] != sid:
            continue
        ny = []
        for r in sp["rutor"]:
            X = np.array(r[1:], float).reshape(-1, 3) / 1000
            X = fn(X)
            ny.append([r[0]] + [int(round(c * 1000)) for c in X.reshape(-1)])
        sp["rutor"] = ny


def _kam(p, sid, fn):
    t = next(t for t in p["tagningar"] if t["id"] == sid)
    for k in t["kamera"]["nycklar"]:
        C, R = np.array(k[1:4]), quat_till_mat(k[4:8])
        C, R = fn(C, R)
        k[1:4] = [round(float(x), 4) for x in C]
        k[4:8] = [round(float(x), 5) for x in mat_till_quat(R)]


def _rot_x(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def _rot_z(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def injektioner(p):
    """(namn, grind, val(rad)->bool, mutera(paket, rad))"""
    L = {n: i for i, n in enumerate(p["leder"])}

    def sjunk(q, r):
        _person_xyz(q, r["person"], r["tagning"], lambda X: X - [0, 0, 0.30])

    def svav(q, r):
        _person_xyz(q, r["person"], r["tagning"], lambda X: X + [0, 0, 0.40])

    def lyft_sittande(q, r):
        _person_xyz(q, r["person"], r["tagning"], lambda X: X + [0, 0, 0.30])

    def bord_i_bal(q, r):
        sp = next(s for s in q["rorelse"][r["person"]] if s["tagning"] == r["tagning"])
        X = np.array(sp["rutor"][len(sp["rutor"]) // 2][1:], float).reshape(-1, 3) / 1000
        q["objekt"].append(dict(id="mut_bord", bas="mut_bord", typ="bord", pos=[float(v) for v in X[L["c_spine2"]]], rot=[0, 0, 0],
                                matt=[0.6, 0.6, 0.6], farg="#ff0000", status="mutation", rum="gemensamt", synlig_ut=[[0, q["tidsbas"]["antal_rutor"]]]))

    def vrid_bort(q, r):
        _kam(q, r["tagning"], lambda C, R: (C, _rot_z(100) @ R))

    def skym_huvud(q, r):
        sp = next(s for s in q["rorelse"][r["person"]] if s["tagning"] == r["tagning"])
        t = next(t for t in q["tagningar"] if t["id"] == r["tagning"])
        X = np.array(sp["rutor"][len(sp["rutor"]) // 2][1:], float).reshape(-1, 3) / 1000
        C = np.array(t["kamera"]["nycklar"][0][1:4])
        h = X[L["c_neck"]]
        pos = C + 0.5 * (h - C)
        q["objekt"].append(dict(id="mut_skarm", bas="mut_skarm", typ="foremal", pos=[float(v) for v in pos], rot=[0, 0, 0],
                                matt=[0.5, 0.5, 0.5], farg="#ff0000", status="mutation", rum="gemensamt", synlig_ut=[[0, q["tidsbas"]["antal_rutor"]]]))

    def flytta_sidled(q, r):
        t = next(t for t in q["tagningar"] if t["id"] == r["tagning"])
        R = quat_till_mat(t["kamera"]["nycklar"][0][4:8])
        h = R[:, 0] * 0.6
        _person_xyz(q, r["person"], r["tagning"], lambda X: X + h)

    def luta_kamera(q, r):
        _kam(q, r["tagning"], lambda C, R: (C, R @ _rot_x(12)))

    def kamera_drift(q, r):
        t = next(t for t in q["tagningar"] if t["id"] == r["tagning"])
        a0, b0 = t["ut"]
        k0 = t["kamera"]["nycklar"][0]
        t["kamera"]["statisk"] = False
        t["kamera"]["nycklar"] = [[a0] + k0[1:], [b0 - 1] + [k0[1] + 0.6, k0[2] + 0.4, k0[3]] + k0[4:]]

    def fel_rum(q, r):
        q["rum"].append(dict(id="mut_rum", tagningar=["ingen"], ut=[], platser=[], status="mutation"))
        q["objekt"].append(dict(id="mut_lada", bas="mut_lada", typ="foremal", pos=[50, 50, 0.5], rot=[0, 0, 0], matt=[0.1, 0.1, 0.1],
                                farg="#ff0000", status="mutation", rum="mut_rum", synlig_ut=[[0, q["tidsbas"]["antal_rutor"]]]))

    def ar_sittande(r):
        t = next(t for t in p["tagningar"] if t["id"] == r["tagning"])
        return any(x["id"] == r["person"] and x.get("ankare") for x in t["personer"])

    return [
        ("sjunk_0.30m", "G2_golv", lambda r: r.get("G2_golv", {}).get("ok") is True, sjunk),
        ("svav_0.40m", "G2_golv", lambda r: r.get("G2_golv", {}).get("ok") is True, svav),
        ("lyft_sittande_0.30m", "G3_sate", lambda r: r.get("G3_sate", {}).get("ok") is True and ar_sittande(r), lyft_sittande),
        ("bord_i_balen", "G4_genom", lambda r: r.get("G4_genom", {}).get("ok") is True, bord_i_bal),
        ("kamera_vriden_100deg", "G5_ibild", lambda r: r.get("G5_ibild", {}).get("ok") is True, vrid_bort),
        ("skarm_framfor_huvudet", "G6_skymning", lambda r: r.get("G6_skymning", {}).get("ok") is True, skym_huvud),
        ("person_0.6m_i_sidled", "G7_trohet", lambda r: r.get("G7_trohet", {}).get("ok") is True, flytta_sidled),
        ("kamera_lutad_12deg", "G8_lodlinje", lambda r: r.get("G8_lodlinje", {}).get("ok") is True, luta_kamera),
        ("kamera_drift_0.7m", "G9_kamerarorelse", lambda r: r.get("G9_kamerarorelse", {}).get("ok") is True and
         next(t for t in p["tagningar"] if t["id"] == r["tagning"])["kamera"]["statisk"], kamera_drift),
        ("objekt_i_fel_rum", "G1_rum", lambda r: r.get("G1_rum", {}).get("ok") is True, fel_rum),
    ]


def _normalisera(rader):
    """np.bool_ -> bool, så att `is True`/`is False` nedan gäller både B:s och originalets grindar (rättat 20 nov)."""
    for r in rader:
        for v in r.values():
            if isinstance(v, dict) and v.get("ok") is not None:
                v["ok"] = bool(v["ok"])
    return rader


def kor(paket: dict, mat_fn, max_per=3) -> list[dict]:
    """mat_fn(paket) -> rader. Returnerar en rad per (injektion, provad rad) med larmade/ej larmade."""
    _mat = mat_fn
    mat_fn = lambda p: _normalisera(_mat(p))  # noqa: E731
    bas = mat_fn(paket)
    ut = []
    for namn, grind, val, mutera in injektioner(paket):
        kand = [r for r in bas if r.get("person") and val(r)][:max_per]
        if not kand:
            ut.append(dict(injektion=namn, grind=grind, provad=0, larm=0, notis="ingen rad där grinden var ok före"))
            continue
        larm = 0
        detalj = []
        for r in kand:
            q = copy.deepcopy(paket)
            mutera(q, r)
            ny = mat_fn(q)
            m = next((x for x in ny if x["tagning"] == r["tagning"] and x.get("person") == r["person"]), None)
            res = None if m is None else m.get(grind, {}).get("ok")
            larm += int(res is False)
            detalj.append(dict(tagning=r["tagning"], person=r["person"], efter=res))
        ut.append(dict(injektion=namn, grind=grind, provad=len(kand), larm=larm, detalj=detalj))
    return ut
