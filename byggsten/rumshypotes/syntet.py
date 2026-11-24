"""Syntetisk diner med facit: stresstestets form (motbilder, servitör, avslöjande).

Facit är ett rum i Blenders ram. Observationerna simuleras med brus i samma format som
Fas 1–2 ska leverera (telemetri.Observationer). Detektionerna har anonyma id:n, så att
hjärnan inte kan läsa facit ur namnen. Allt är deterministiskt för ett givet frö.
"""
from __future__ import annotations

import math

import numpy as np

from telemetri import M, Detektion, Kamera, KlippObs, Observationer, Stralar, Vagg

D2R = math.pi / 180.0


def facit(avstand: float = 5.0, delat: bool = False) -> dict:
    """delat=True: kontrollen där A och B verkligen sitter vid samma bord."""
    y1, y2 = 2.2, 2.2 + avstand
    if delat:
        y2 = y1
    f = dict(
        rum=(-3.0, 3.0, 0.0, 10.0), tak=3.2, alfa_deg=0.0,          # fönstren i öster
        bord_matt=(1.2, 0.6, 0.74),
        bord={"bord_1": (0.0, y1), "bord_2": (0.0, y2)},
        personer={
            "A": dict(pos=(0.0, y1 - 0.75), vand=90.0, pose="sittande", bord="bord_1", blick="B"),
            "B": dict(pos=(0.0, y2 + 0.75), vand=-90.0, pose="sittande", bord="bord_2", blick="A"),
            "C": dict(pos=(-2.35, 3.4), vand=0.0, pose="staende", bord=None, blick=None),
        },
        foremal={"burk_A": dict(pos=(0.30, y1 - 0.05), bord="bord_1")},
        dorrar={"dorr_1": dict(pos=(-3.0, 3.4), sida="W")},
        rumsnycklar={"vagg": "beige", "golv": "tra", "tak": "betong"},
        # id, rutor, kamera (x, y, höjd), yaw, pitch, hfov, borttagna föremål, ser taket
        klipp=[
            ("s1", (0, 60), (0.10, y1 + 0.40, 1.15), -88.0, -6.0, 50.0, (), False),
            ("s2", (60, 115), (-0.08, y2 - 0.35, 1.15), 92.0, -6.0, 50.0, (), False),
            ("s3", (115, 170), (0.05, y1 + 0.42, 1.20), -91.0, -5.0, 50.0, ("burk_A",), False),
            ("s4", (170, 215), (-0.60, 3.25, 1.60), 178.0, -2.0, 55.0, (), True),
            ("s5", (215, 265), (0.06, y2 - 0.30, 1.10), 89.0, -6.0, 50.0, (), False),
            ("s6", (265, 310), (0.12, y1 + 0.38, 1.15), -87.0, -6.0, 50.0, (), False),
            ("s7", (310, 400), (0.35, 1.20, 1.25), 92.0, -4.0, 65.0, (), True),
        ],
    )
    if delat:
        del f["bord"]["bord_2"]
        f["personer"]["B"]["bord"] = "bord_1"
    return f


def _bear(cx, cy, th, px, py):
    vx, vy = px - cx, py - cy
    z = vx * math.cos(th) + vy * math.sin(th)
    x = vx * math.sin(th) - vy * math.cos(th)
    return math.degrees(math.atan2(x, z)), math.hypot(vx, vy), z


def _ray_rum(cx, cy, a, rum):
    x0, x1, y0, y1 = rum
    dx, dy = math.cos(a), math.sin(a)
    t = []
    if dx > 1e-9:
        t.append((x1 - cx) / dx)
    if dx < -1e-9:
        t.append((x0 - cx) / dx)
    if dy > 1e-9:
        t.append((y1 - cy) / dy)
    if dy < -1e-9:
        t.append((y0 - cy) / dy)
    return min(v for v in t if v > 0)


def _ray_cirkel(cx, cy, a, px, py, r):
    dx, dy = math.cos(a), math.sin(a)
    fx, fy = cx - px, cy - py
    b = fx * dx + fy * dy
    c = fx * fx + fy * fy - r * r
    disk = b * b - c
    if disk < 0:
        return math.inf
    t = -b - math.sqrt(disk)
    return t if t > 0 else math.inf


def simulera(f: dict, fro: int = 7, klipp_id: str = "syntet_diner") -> Observationer:
    rng = np.random.default_rng(fro)
    ut = []
    for kid, rutor, (cx, cy, ch), yaw, pitch, hfov, bort, ser_tak in f["klipp"]:
        th = yaw * D2R
        halv = hfov / 2 - 2.0
        dets, namn = [], {}

        def synlig(px, py):
            b, d, z = _bear(cx, cy, th, px, py)
            return (z > 0 and abs(b) < halv and 0.3 < d < 12.0), b, d

        def nid(gt):
            namn[gt] = f"{kid}:d{len(namn) + 1}"
            return namn[gt]

        sedda_bord = {}
        for bid, (px, py) in sorted(f["bord"].items()):
            ok, b, d = synlig(px, py)
            if ok:
                sedda_bord[bid] = (b, d)
        for pid, p in sorted(f["personer"].items()):
            ok, b, d = synlig(*p["pos"])
            if not ok:
                continue
            rel = 0.08 if d < 3 else 0.12
            phi = math.degrees(math.atan2(math.sin(th - p["vand"] * D2R), math.cos(th - p["vand"] * D2R)))
            dets.append(dict(gt=pid, klass="person", nyckel=f"person:{pid}", unik=True,
                             b=b, d=d, rel=rel, phi=phi, pose=p["pose"],
                             blick=f"person:{p['blick']}" if p["blick"] else None,
                             vid=p["bord"] if p["bord"] in sedda_bord else None))
        for bid, (b, d) in sedda_bord.items():
            dets.append(dict(gt=bid, klass="bord", nyckel="bord:tra", unik=False, b=b, d=d, rel=0.15, amodal=d < 1.5))
        for fid, p in sorted(f["foremal"].items()):
            ok, b, d = synlig(*p["pos"])
            if ok and fid not in bort:
                dets.append(dict(gt=fid, klass="foremal", nyckel=f"foremal:{fid}", unik=True, b=b, d=d, rel=0.10,
                                 pa=p["bord"] if p["bord"] in sedda_bord else None))
        for did, p in sorted(f["dorrar"].items()):
            ok, b, d = synlig(*p["pos"])
            if ok:
                dets.append(dict(gt=did, klass="dorr", nyckel="dorr:tra", unik=False, b=b, d=d, rel=0.10, vagg=True))
        for dd in dets:
            nid(dd["gt"])
        detektioner = []
        for dd in dets:
            s_d = dd["rel"] * dd["d"]
            detektioner.append(Detektion(
                id=namn[dd["gt"]], klass=dd["klass"], nyckel=dd["nyckel"], unik=dd["unik"],
                bearing_deg=M(v=round(dd["b"] + rng.normal(0, 1.0), 2), s=1.5),
                djup_m=M(v=round(dd["d"] * (1 + rng.normal(0, dd["rel"] * 0.8)), 3), s=round(s_d, 3)),
                vridning_deg=(M(v=round(dd["phi"] + rng.normal(0, 8.0), 1), s=15.0) if "phi" in dd else None),
                pose=dd.get("pose"), blick_mot=dd.get("blick"),
                vid=namn.get(dd.get("vid")) if dd.get("vid") else None,
                pa=namn.get(dd.get("pa")) if dd.get("pa") else None,
                pa_vagg=dd.get("vagg", False), amodal=dd.get("amodal", False)))
        # väggar: den centrala strålen och bildkanterna avgör vilka som syns
        x0, x1, y0, y1 = f["rum"]
        sidor = set()
        for a in (th, th + halv * D2R, th - halv * D2R):
            t = _ray_rum(cx, cy, a, f["rum"])
            hx, hy = cx + t * math.cos(a), cy + t * math.sin(a)
            sidor.add(min((abs(hx - x1), "E"), (abs(hx - x0), "W"), (abs(hy - y1), "N"), (abs(hy - y0), "S"))[1])
        vaggar = []
        for sida in sorted(sidor):
            omega, avst = {"E": (0.0, x1 - cx), "W": (180.0, cx - x0), "N": (90.0, y1 - cy), "S": (-90.0, cy - y0)}[sida]
            b = math.degrees(math.atan2(math.sin(th - omega * D2R), math.cos(th - omega * D2R)))
            vaggar.append(Vagg(bearing_deg=M(v=round(b + rng.normal(0, 2.0), 1), s=3.0),
                               avstand_m=M(v=round(avst * (1 + rng.normal(0, 0.05)), 3), s=round(0.08 * avst, 3)),
                               nyckel="vagg:beige"))
        # fri yta: höga hinder (personer, väggar); bord skymmer inte
        bear, fri = [], []
        for b in np.linspace(-halv, halv, 11):
            a = th - b * D2R
            t = _ray_rum(cx, cy, a, f["rum"])
            for p in f["personer"].values():
                t = min(t, _ray_cirkel(cx, cy, a, *p["pos"], 0.22))
            bear.append(round(float(b), 2))
            fri.append(round(t * (1 + rng.normal(0, 0.04)), 3))
        man = math.degrees(math.atan2(math.sin(4 * th), math.cos(4 * th)) / 4)
        ljus = math.degrees(math.atan2(math.sin(th - f["alfa_deg"] * D2R), math.cos(th - f["alfa_deg"] * D2R)))
        nycklar = {"vagg": f["rumsnycklar"]["vagg"], "golv": f["rumsnycklar"]["golv"]}
        if ser_tak:
            nycklar["tak"] = f["rumsnycklar"]["tak"]
        ut.append(KlippObs(
            klipp=kid, rutor=rutor,
            kamera=Kamera(hfov_deg=M(v=round(hfov + rng.normal(0, 1.0), 1), s=2.0),
                          hojd_m=M(v=round(ch + rng.normal(0, 0.04), 3), s=0.08),
                          pitch_deg=M(v=round(pitch + rng.normal(0, 1.0), 1), s=2.0)),
            detektioner=detektioner, vaggar=vaggar,
            manhattan_deg=M(v=round(man + rng.normal(0, 1.5), 2), s=2.0),
            ljus_bearing_deg=M(v=round(ljus + rng.normal(0, 12.0), 1), s=20.0),
            takhojd_m=(M(v=round(f["tak"] + rng.normal(0, 0.08), 2), s=0.15) if ser_tak else None),
            rumsnycklar=nycklar,
            stralar=Stralar(bearing_deg=bear, fri_m=fri)))
    return Observationer(klipp_id=klipp_id, fps=30.0, klipp=ut)
