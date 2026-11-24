# -*- coding: utf-8 -*-
"""Rumsskala (mått a): kamerahöjd och möbelhöjder mot oberoende ankare i råpixlar.

Metod: enkelbildsmetrologi (Criminisi, Reid & Zisserman 2000). Ur en ruta i ORIGINALVIDEON märker
en människa (eller en agent som inte byggt systemet):
  - horisonten: två familjer av parallella vågräta linjer i rummet (golvplattor, bordskanter,
    hyllor, takskarvar), vars flyktpunkter ger horisontlinjen; eller en familj + antagandet
    att kameran inte rullar; eller ett y-intervall;
  - valfritt: lodräta linjer (dörrkarm, hörn) för den lodräta flyktpunkten;
  - referenser: lodräta sträckor fot (på golvet) -> topp med känd höjd INOM ETT INTERVALL
    (dörrblad 2,00-2,10 m, stående vuxen 1,55-1,95 m, standardkyl, ...);
  - mått: lodräta sträckor fot -> topp vars höjd ska skattas (disk, bord, stolsits, hylla).

För en lodrät sträcka med fot b och topp t gäller (l = horisonten, v = lodrät flyktpunkt):
    Z / Zc = 1 - d(t,l) d(b,v) / ( d(b,l) d(t,v) )
där Zc är kamerahöjden. Referenserna ger Zc, och Zc ger varje mått. Ingen brännvidd, ingen
djupmodell, ingen SAM/MoGe: facit beror bara på pixlar och standardstorlekar.

Osäkerhet: Monte Carlo över pixelbrus (sigma per punkt), referenshöjdens intervall och
horisontens linjeanpassning. Utdata är p05/p50/p95. FACIT ÄR EN UPPSKATTNING: det är så bra som
märkningen och antagandet att referensen har standardstorlek. Det säger det uttryckligen i utdata.

Körning:
  python rumsskala.py --ankare ankare.json [--pastaende system.json] [--logg ut.json]
  python rumsskala.py --sjalvtest

system.json:  {"kamera_hojd_m": 1.42, "matt": {"disk_topp": 0.91, "bord": 0.74}}
Utfall per post: "inom" om värdet ligger i [p05, p95], annars "utanfor" med avståndet i cm.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

N_MC = 4000


def _h(p):
    return np.array([p[0], p[1], 1.0])


def flyktpunkt(linjer: np.ndarray) -> np.ndarray:
    """Minsta-kvadrat-skärning av linjer [N, 4] (x1,y1,x2,y2) -> homogen punkt."""
    L = []
    for x1, y1, x2, y2 in linjer:
        l = np.cross([x1, y1, 1.0], [x2, y2, 1.0])
        L.append(l / np.linalg.norm(l[:2]))
    L = np.array(L)
    _, _, vt = np.linalg.svd(L)
    return vt[-1]


def linje_genom(p, q) -> np.ndarray:
    l = np.cross(p, q)
    return l / np.linalg.norm(l[:2])


def sd(pt_h, l):
    """Signerat avstånd från punkt (homogen) till linje l (normerad)."""
    return float(l @ (pt_h / pt_h[2]))


def avst(p_h, v_h):
    if abs(v_h[2]) < 1e-9 * np.linalg.norm(v_h[:2]):
        return None  # oändligt avlägsen
    a = p_h[:2] / p_h[2]
    b = v_h[:2] / v_h[2]
    return float(np.linalg.norm(a - b))


def kvot(b, t, l, v) -> float:
    """Z/Zc för en lodrät sträcka fot b, topp t."""
    bh, th = _h(b), _h(t)
    db, dt = sd(bh, l), sd(th, l)
    if v is None:
        r = 1.0
    else:
        dbv, dtv = avst(bh, v), avst(th, v)
        r = 1.0 if (dbv is None or dtv is None) else dbv / dtv
    return 1.0 - (dt / db) * r


def horisont_fran(ank, rng, sig):
    h = ank["horisont"]
    w, hh = ank["bild"]
    if "y" in h:
        y = rng.uniform(*h["y"]) if isinstance(h["y"], list) else h["y"] + rng.normal(0, sig)
        l = np.array([0.0, 1.0, -y])
        return l, "y-intervall"
    fam = h.get("vp_familjer") or [h["vp_familj"]]
    vps = []
    for f in fam:
        ln = np.array(f, float) + rng.normal(0, sig, (len(f), 4))
        vps.append(flyktpunkt(ln))
    if len(vps) >= 2:
        l = linje_genom(vps[0], vps[1])
        # orientera så att golvpunkter (bildens nederkant) får positivt avstånd
        if l @ np.array([w / 2, hh, 1.0]) < 0:
            l = -l
        return l, "två flyktpunkter"
    v0 = vps[0]
    y0 = v0[1] / v0[2]
    rull = h.get("rull_deg", 0.0)
    a = np.deg2rad(rull + rng.normal(0, h.get("rull_sigma_deg", 1.0)))
    l = np.array([-np.sin(a), np.cos(a), 0.0])
    l[2] = -(l[0] * v0[0] / v0[2] + l[1] * y0)
    if l @ np.array([w / 2, hh, 1.0]) < 0:
        l = -l
    return l, "en flyktpunkt + antagen rullvinkel"


def vert_fran(ank, rng, sig):
    """Lodrät flyktpunkt: ur märkta lodräta linjer, annars ur själva fot->topp-sträckorna
    (de är lodräta per definition). Med färre än två sträckor antas den oändligt avlägsen."""
    v = ank.get("vertikal")
    if v and v.get("vp"):
        s = float(v.get("vp_sigma", sig))
        return np.array([v["vp"][0] + rng.normal(0, s), v["vp"][1] + rng.normal(0, s), 1.0])
    if v and v.get("linjer"):
        lin = list(v["linjer"])
    else:
        lin = [list(e["fot"]) + list(e["topp"]) for e in ank["referenser"] + ank.get("matt", [])]
        if v is not None and v.get("oandlig"):
            return None
    if len(lin) < 2:
        return None
    ln = np.array(lin, float) + rng.normal(0, sig, (len(lin), 4))
    return flyktpunkt(ln)


def skatta(ank: dict, n: int = N_MC, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    sig = float(ank.get("pixel_sigma", 2.0))
    refs, matt = ank["referenser"], ank.get("matt", [])
    zc_per_ref = {r["namn"]: [] for r in refs}
    zc_all, z_m = [], {m["namn"]: [] for m in matt}
    for _ in range(n):
        l, hmetod = horisont_fran(ank, rng, sig)
        v = vert_fran(ank, rng, sig)
        zcs = []
        for r in refs:
            b = np.array(r["fot"], float) + rng.normal(0, sig, 2)
            t = np.array(r["topp"], float) + rng.normal(0, sig, 2)
            q = kvot(b, t, l, v)
            H = rng.uniform(*r["hojd_m"])
            if q <= 0.02:
                continue
            zc = H / q
            zc_per_ref[r["namn"]].append(zc)
            zcs.append(zc)
        if not zcs:
            continue
        zc = float(np.median(zcs))
        zc_all.append(zc)
        for m in matt:
            b = np.array(m["fot"], float) + rng.normal(0, sig, 2)
            t = np.array(m["topp"], float) + rng.normal(0, sig, 2)
            z_m[m["namn"]].append(zc * kvot(b, t, l, v))

    def pct(a):
        a = np.asarray(a)
        if a.size == 0:
            return None
        p = np.percentile(a, [5, 50, 95])
        return {"p05": round(float(p[0]), 3), "p50": round(float(p[1]), 3), "p95": round(float(p[2]), 3),
                "bredd_cm": round(float(p[2] - p[0]) * 100, 1)}

    per_ref = {k: pct(v) for k, v in zc_per_ref.items()}
    # konsekvens: överlappar referensernas 90 %-intervall för kamerahöjden?
    iv = [(v["p05"], v["p95"]) for v in per_ref.values() if v]
    konsekvent = (max(a for a, _ in iv) <= min(b for _, b in iv)) if len(iv) >= 2 else None
    return {
        "klipp": ank.get("klipp"), "ruta": ank.get("ruta"),
        "horisontmetod": hmetod,
        "kamera_hojd_m": pct(zc_all),
        "kamera_hojd_per_referens": per_ref,
        "referenser_konsekventa": konsekvent,
        "matt": {k: pct(v) for k, v in z_m.items()},
        "facit_ar_uppskattning": ("Facit = enkelbildsmetrologi ur egen pixelmärkning och standardstorlekar "
                                  "(" + "; ".join(f"{r['namn']}: {r['hojd_m'][0]}-{r['hojd_m'][1]} m"
                                                  for r in refs) + "). Det är inte uppmätt på plats."),
    }


def jamfor(est: dict, pas: dict) -> dict:
    ut = {}
    poster = []
    if "kamera_hojd_m" in pas and est["kamera_hojd_m"]:
        poster.append(("kamera_hojd_m", pas["kamera_hojd_m"], est["kamera_hojd_m"]))
    for k, v in (pas.get("matt") or {}).items():
        if est["matt"].get(k):
            poster.append((k, v, est["matt"][k]))
    for k, v, e in poster:
        if v is None:
            ut[k] = {"utfall": "saknas"}
            continue
        if e["p05"] <= v <= e["p95"]:
            ut[k] = {"utfall": "inom", "varde": v, "intervall": [e["p05"], e["p95"]]}
        else:
            d = (e["p05"] - v) if v < e["p05"] else (v - e["p95"])
            ut[k] = {"utfall": "utanfor", "varde": v, "intervall": [e["p05"], e["p95"]],
                     "avstand_cm": round(d * 100, 1)}
    n_ut = sum(1 for x in ut.values() if x["utfall"] == "utanfor")
    return {"utfall": "larm" if n_ut else "inom_alla", "antal_utanfor": n_ut, "poster": ut}


# ---------------------------------------------------------------- självtest (syntetisk kamera)

def _kamera(H, pitch_deg, roll_deg, f, w, h):
    th = np.deg2rad(pitch_deg)
    right = np.array([1.0, 0, 0]); fwd = np.array([0, np.cos(th), -np.sin(th)])
    down = np.cross(fwd, right)
    R = np.stack([right, down, fwd])
    a = np.deg2rad(roll_deg)
    Rr = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    R = Rr @ R
    C = np.array([0, 0, H])

    def proj(P):
        pc = R @ (np.asarray(P, float) - C)
        return [f * pc[0] / pc[2] + w / 2, f * pc[1] / pc[2] + h / 2]
    return proj


def syntetisk(rng):
    w, h = 1080, 1920
    H = rng.uniform(1.1, 1.7); pitch = rng.uniform(4, 18); roll = rng.uniform(-2, 2)
    f = rng.uniform(800, 1500)
    P = _kamera(H, pitch, roll, f, w, h)
    yaw = rng.uniform(-25, 25)
    c, s = np.cos(np.deg2rad(yaw)), np.sin(np.deg2rad(yaw))
    d1, d2 = np.array([c, s, 0]), np.array([-s, c, 0])

    def seg(p0, d, L):
        a, b = P(p0), P(np.asarray(p0) + d * L)
        return [a[0], a[1], b[0], b[1]]
    fam1 = [seg(np.array([x, 4.0, 0.0]), d2, 2.0) for x in (-1.0, 0.0, 1.0)]
    fam2 = [seg(np.array([-1.5, y, 0.0]), d1, 3.0) for y in (3.0, 4.5, 6.0)]
    sann = {"dorr": rng.uniform(2.00, 2.10), "person": rng.uniform(1.55, 1.95),
            "disk": rng.uniform(0.85, 1.15), "bord": rng.uniform(0.70, 0.78), "sits": rng.uniform(0.42, 0.80)}
    pos = {"dorr": [-1.2, 6.5], "person": [0.6, 4.2], "disk": [0.2, 3.6], "bord": [-0.5, 3.0], "sits": [0.9, 3.1]}

    def vert(k):
        x, y = pos[k]
        return {"fot": P([x, y, 0.0]), "topp": P([x, y, sann[k]])}
    ank = {"klipp": "syntetisk", "bild": [w, h], "pixel_sigma": 1.5,
           "horisont": {"vp_familjer": [fam1, fam2]},
           "referenser": [dict(namn="dorr", hojd_m=[2.00, 2.10], **vert("dorr")),
                          dict(namn="person", hojd_m=[1.55, 1.95], **vert("person"))],
           "matt": [dict(namn=k, **vert(k)) for k in ("disk", "bord", "sits")]}
    # pixelbrus i märkningen (den som märker gör fel)
    for grp in ("referenser", "matt"):
        for e in ank[grp]:
            e["fot"] = list(np.array(e["fot"]) + rng.normal(0, 1.5, 2))
            e["topp"] = list(np.array(e["topp"]) + rng.normal(0, 1.5, 2))
    return ank, sann, H


def sjalvtest() -> int:
    rng = np.random.default_rng(7)
    tackning = {"kamera": 0, "disk": 0, "bord": 0, "sits": 0}
    larm_inj, larm_ren, n = 0, 0, 40
    bredder = []
    for i in range(n):
        ank, sann, H = syntetisk(rng)
        e = skatta(ank, n=800, seed=i)
        kh = e["kamera_hojd_m"]
        tackning["kamera"] += kh["p05"] <= H <= kh["p95"]
        for k in ("disk", "bord", "sits"):
            m = e["matt"][k]
            tackning[k] += m["p05"] <= sann[k] <= m["p95"]
            bredder.append(m["bredd_cm"])
        ren = {"kamera_hojd_m": H, "matt": {k: sann[k] for k in ("disk", "bord", "sits")}}
        larm_ren += jamfor(e, ren)["utfall"] == "larm"
        # felinjektion: disken 20 cm för låg (som en platt 'standardskiva') och kameran 25 cm för låg
        inj = {"kamera_hojd_m": H - 0.25, "matt": {"disk": sann["disk"] - 0.20, "bord": sann["bord"], "sits": sann["sits"]}}
        larm_inj += jamfor(e, inj)["utfall"] == "larm"
    res = {
        "n_scener": n,
        "tackning_90pct_intervall": {k: round(v / n, 3) for k, v in tackning.items()},
        "median_intervallbredd_cm": round(float(np.median(bredder)), 1),
        "larm_pa_injektion_(disk_-20cm,_kamera_-25cm)": f"{larm_inj}/{n}",
        "falsklarm_pa_sanna_varden": f"{larm_ren}/{n}",
    }
    print(json.dumps(res, ensure_ascii=False, indent=1))
    ok = all(v / n >= 0.8 for v in tackning.values()) and larm_inj >= 0.9 * n and larm_ren <= 0.3 * n
    print("självtest:", "OK" if ok else "FEL")
    Path(__file__).with_name("rumsskala_sjalvtest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1),
                                                                    encoding="utf-8")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ankare", nargs="+")
    ap.add_argument("--pastaende")
    ap.add_argument("--logg")
    ap.add_argument("--n", type=int, default=N_MC)
    ap.add_argument("--sjalvtest", action="store_true")
    a = ap.parse_args()
    if a.sjalvtest:
        sys.exit(sjalvtest())
    ut = []
    for f in a.ankare:
        ank = json.loads(Path(f).read_text(encoding="utf-8"))
        e = skatta(ank, n=a.n)
        e["ankarfil"] = f
        if a.pastaende:
            pas = json.loads(Path(a.pastaende).read_text(encoding="utf-8"))
            pas = pas.get(ank.get("klipp"), pas) if isinstance(pas, dict) else pas
            e["jamforelse"] = jamfor(e, pas)
        ut.append(e)
    txt = json.dumps(ut, ensure_ascii=False, indent=1)
    if a.logg:
        Path(a.logg).write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
