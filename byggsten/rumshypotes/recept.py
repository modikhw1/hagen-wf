"""Receptet (SceneTelemetry): hjärnans tro i scenens ram, med osäkerhet och historik.

Ramen flyttas så att rummets mitt ligger i origo. Måtten för saker är klassens typmått
tills Fas 2 levererar egna mått. Allt står på golvet (z = 0), utom föremål på bord.
"""
from __future__ import annotations

import math

import numpy as np

from hjarna import D2R, Hyp, kalla_for, relationer, sedd_i, sigma_max
from regler import R
from telemetri import KameraNod, Ljus, LoggSteg, Nod, Observationer, Recept, Rum, Vaggnod, Zon

MATT = {"bord": (1.2, 0.6, 0.74), "foremal": (0.07, 0.07, 0.12), "dorr": (0.9, 0.08, 2.05),
        "stol": (0.45, 0.45, 0.9), "fonster": (1.0, 0.08, 1.2)}
PERSON = {"sittande": (0.5, 0.5, 1.30), "staende": (0.5, 0.35, 1.75)}


def vandning(h: Hyp, eid: str, obs: Observationer, K: int):
    """Personens vändning i världen (radianer): cirkulärt medel över detektionernas vridning."""
    v = []
    for k in range(K):
        th = h.x["cam"][k][2]
        for d in obs.klipp[k].detektioner:
            if h.assoc.get((k, d.id)) == eid and d.vridning_deg is not None:
                v.append(th - d.vridning_deg.v * D2R)
    if not v:
        return None
    return math.atan2(sum(math.sin(a) for a in v), sum(math.cos(a) for a in v))


def bordsvinkel(h: Hyp, eid: str, obs: Observationer, K: int) -> float:
    """Man sitter längs långsidan: långsidan står vinkelrätt mot den sittandes vändning."""
    for t, a, b in sorted(relationer(h, obs, K)):
        if t == "vid" and b == eid:
            v = vandning(h, a, obs, K)
            if v is not None:
                return round((v + math.pi / 2) / (math.pi / 2)) * (math.pi / 2)
    return 0.0


def konfidens(s: float) -> float:
    return float(min(0.99, max(0.02, math.exp(-s / 0.6))))


def bygg(historik, obs: Observationer, loggrader: list) -> Recept:
    from hjarna import karna
    h = next(c for c in historik[-1].stråle
             if karna(c, obs, len(obs.klipp)) == loggrader[-1]["tro"])
    K = len(obs.klipp)
    x0, x1, y0, y1 = (float(v) for v in h.x["rum"][0])
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2

    def P(p):
        return round(float(p[0] - mx), 4), round(float(p[1] - my), 4)

    pa = {a: b for t, a, b in relationer(h, obs, K) if t == "pa"}
    noder = []
    for eid, e in sorted(h.ents.items()):
        if e.rum != 0:
            continue
        p, kov = P(h.x["ent"][eid]), h.kov["ent"][eid]
        s = sigma_max(kov)
        pose = None
        if e.klass == "person":
            pose = next((d.pose for k in range(K) for d in obs.klipp[k].detektioner
                         if h.assoc.get((k, d.id)) == eid and d.pose), "staende")
            dims = PERSON[pose]
            v = vandning(h, eid, obs, K)
            rot = (0.0, 0.0, round(math.degrees(v) - 90.0, 2) if v is not None else 0.0)
            z = dims[2] / 2
        else:
            dims = MATT.get(e.klass, (0.3, 0.3, 0.3))
            if e.klass == "bord":
                rot = (0.0, 0.0, round(math.degrees(bordsvinkel(h, eid, obs, K)), 2))
            elif e.klass in ("dorr", "fonster"):
                rot = (0.0, 0.0, 90.0 if e.sida in ("E", "W") else 0.0)
            else:
                rot = (0.0, 0.0, 0.0)
            z = dims[2] / 2
            if e.klass == "foremal":
                bordet = pa.get(eid) or min((b for b in h.ents if h.ents[b].klass == "bord"),
                                            key=lambda b: np.linalg.norm(h.x["ent"][b] - h.x["ent"][eid]), default=None)
                if bordet and np.linalg.norm(h.x["ent"][bordet] - h.x["ent"][eid]) < 0.8:
                    z = MATT["bord"][2] + dims[2] / 2
            if e.klass == "fonster":
                z = 1.45
        zon = None
        if s > R["zon_troskel_m"] and e.klass != "foremal":
            sx, sy = math.sqrt(max(kov[0, 0], 0.0)), math.sqrt(max(kov[1, 1], 0.0))
            a0, a1 = max(x0 - mx + 0.1, p[0] - 2 * sx), min(x1 - mx - 0.1, p[0] + 2 * sx)
            b0, b1 = max(y0 - my + 0.1, p[1] - 2 * sy), min(y1 - my - 0.1, p[1] + 2 * sy)
            zon = Zon(centrum=(round((a0 + a1) / 2, 4), round((b0 + b1) / 2, 4), round(dims[2] / 2, 4)),
                      matt=(round(max(a1 - a0, dims[0]), 4), round(max(b1 - b0, dims[1]), 4), dims[2]))
        giltig = None
        if e.till is not None or "@" in eid:
            giltig = [obs.klipp[k].klipp for k in range(K) if e.giltig(k)]
        noder.append(Nod(
            id=eid, klass=e.klass, nyckel=e.nyckel, position=(p[0], p[1], round(z, 4)), rotation=rot,
            dimensions=dims, position_variance=(round(float(kov[0, 0]), 5), round(float(kov[1, 1]), 5), 0.0009),
            confidence_score=round(konfidens(s), 3), evidence_shots=sedd_i(h, eid, obs, K),
            geometry_source=kalla_for(h, eid, obs, K), pose=pose, giltig_i=giltig, zon=zon))

    sig = np.sqrt(np.maximum(np.diag(h.kov["rum"][0]), 0.0))
    sedda: dict = {}
    for (k, _), sida in h.vaggsida.items():
        if h.rum_av.get(k) == 0:
            sedda.setdefault(sida, set()).add(obs.klipp[k].klipp)
    vaggar = [Vaggnod(sida=sd, lage_m=round(lage, 4), sigma_m=round(float(sig[i]), 3),
                      geometry_source="observed" if sd in sedda else "amodal_inferred",
                      evidence_shots=sorted(sedda.get(sd, set())))
              for sd, i, lage in (("W", 0, x0 - mx), ("E", 1, x1 - mx), ("S", 2, y0 - my), ("N", 3, y1 - my))]
    tak = [o.takhojd_m for o in obs.klipp if o.takhojd_m is not None]
    # takhöjd: MoGe:s skala är oförankrad (stor sigma), vägd mot en prior för lokaler (2,8 ± 0,4 m)
    w = [1 / max(t.s, 0.6) ** 2 for t in tak] + [1 / 0.4 ** 2]
    v = [t.v for t in tak] + [2.8]
    takh, taks = sum(a * b for a, b in zip(v, w)) / sum(w), (1 / sum(w)) ** 0.5
    nycklar: dict = {}
    for o in obs.klipp:
        nycklar.update(o.rumsnycklar)
    rum = Rum(granser=(round(x0 - mx, 4), round(x1 - mx, 4), round(y0 - my, 4), round(y1 - my, 4)),
              takhojd_m=round(takh, 3), takhojd_sigma_m=round(taks, 3), vaggar=vaggar, rumsnycklar=nycklar)

    kameror = []
    for k in range(K):
        if h.rum_av[k] != 0:
            continue
        o, c, kc = obs.klipp[k], h.x["cam"][k], h.kov["cam"][k]
        s = math.sqrt(max(np.linalg.eigvalsh(kc[:2, :2]).max(), 0.0))
        p = P(c)
        kameror.append(KameraNod(
            id=f"CAM_{o.klipp}", klipp=o.klipp, rutor=o.rutor,
            position=(p[0], p[1], round(o.kamera.hojd_m.v, 3)),
            rotation=(round(90.0 + o.kamera.pitch_deg.v, 3), round(o.kamera.roll_deg.v, 3),
                      round(math.degrees(c[2]) - 90.0, 3)),
            hfov_deg=o.kamera.hfov_deg.v, bild_px=o.kamera.bild_px,
            position_variance=(round(float(kc[0, 0]), 5), round(float(kc[1, 1]), 5), round(o.kamera.hojd_m.s ** 2, 5)),
            yaw_sigma_deg=round(math.degrees(math.sqrt(max(kc[2, 2], 0.0))), 2), confidence_score=round(konfidens(s), 3)))
    ljus = Ljus(azimut_deg=round(math.degrees(h.x["alfa"]), 2),
                sigma_deg=round(math.degrees(math.sqrt(max(h.kov.get("alfa", 0.0), 0.0))), 2))
    return Recept(klipp_id=obs.klipp_id, fps=obs.fps, rutor=max(o.rutor[1] for o in obs.klipp),
                  tro=loggrader[-1]["tro"], sannolikhet=loggrader[-1]["sannolikhet"], rum=rum, noder=noder,
                  kameror=kameror, ljus=ljus, logg=[LoggSteg(**r) for r in loggrader],
                  regler={k: float(v) for k, v in R.items()})
