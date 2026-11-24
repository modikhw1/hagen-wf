"""Rumshjärnan: läser klipp för klipp, håller flera hypoteser om rummet och omprövar dem.

En hypotes är en uppsättning val om vad observationerna är: vilket bord en detektion är,
om klippet hör till samma rum, om en person har flyttat. Givet valen löses lägena för
kameror, saker, väggar och ljus som minsta kvadrat, med reglerna (regler.py) som
residualer. Poängen är passning + struktur + rum + synlighet, i nats. De B bästa
hypoteserna lever vidare till nästa klipp (beam). När den mest sannolika hypotesen
byter struktur loggas en omprövning med skälen.

Ramen är hjärnans egen: första kameran står i origo och tittar ungefär längs +y.
recept.py flyttar ramen till rummets mitt.
"""
from __future__ import annotations

import itertools
import math
from collections import Counter
from dataclasses import dataclass, field, replace

import numpy as np
from scipy.optimize import least_squares

from regler import FOREMAL_PRIS, R
from telemetri import Observationer

D2R = math.pi / 180.0
FASTA = ("person", "bord", "stol", "dorr")
SIDA_VINKEL = {"E": 0.0, "N": 90.0, "W": 180.0, "S": -90.0}


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def wrap90(a):
    q = math.pi / 2
    return (a + q / 2) % q - q / 2


def kort(eid: str) -> str:
    return eid.split("@")[0]


def sida_for(vinkel: float) -> str:
    """Världsriktning (radianer) till närmaste väggsida."""
    g = math.degrees(wrap(vinkel))
    return min(SIDA_VINKEL, key=lambda s: abs(math.degrees(wrap(math.radians(g - SIDA_VINKEL[s])))))


def bearing(cam, p):
    """Bearing (radianer, positiv åt höger) och avstånd från kameran (x, y, yaw) till punkten p."""
    vx, vy = p[0] - cam[0], p[1] - cam[1]
    c, s = math.cos(cam[2]), math.sin(cam[2])
    z = vx * c + vy * s
    x = vx * s - vy * c
    return math.atan2(x, z), math.hypot(vx, vy)


def _vaggavst(sida, px, py, x0, x1, y0, y1):
    if sida == "E":
        return x1 - px
    if sida == "N":
        return y1 - py
    if sida == "W":
        return px - x0
    return py - y0


def _inne(px, py, x0, x1, y0, y1, m):
    s = R["sigma_inne_m"]
    return (max(0.0, x0 + m - px) / s, max(0.0, px - (x1 - m)) / s,
            max(0.0, y0 + m - py) / s, max(0.0, py - (y1 - m)) / s)


def _rumsstorlek(x0, x1, y0, y1):
    w, d = x1 - x0, y1 - y0
    return ((w - R["rum_typ_m"]) / R["sigma_rum_typ_m"], (d - R["rum_typ_m"]) / R["sigma_rum_typ_m"],
            max(0.0, R["rum_min_m"] - w) / 0.05, max(0.0, R["rum_min_m"] - d) / 0.05)


def _rob(r):
    """Mjuk L1: kvadratisk nära noll, linjär långt ut. För ledtrådar som ibland ljuger (vinklar, väggar)."""
    return math.copysign(math.sqrt(2.0 * (math.sqrt(1.0 + r * r) - 1.0)), r)


def _strale(cx, cy, t, ex, ey, bb, sb, dd, sd):
    vx, vy = ex - cx, ey - cy
    c, s = math.cos(t), math.sin(t)
    return (wrap(math.atan2(vx * s - vy * c, vx * c + vy * s) - bb) / sb, (math.hypot(vx, vy) - dd) / sd)


# ---------------------------------------------------------------- hypoteser

@dataclass(frozen=True)
class Ent:
    id: str
    klass: str
    nyckel: str | None
    unik: bool
    rum: int
    fran: int
    till: int | None = None
    sida: str | None = None

    def giltig(self, k: int) -> bool:
        return self.fran <= k and (self.till is None or k < self.till)


@dataclass
class Hyp:
    id: str
    ents: dict
    assoc: dict
    rum_av: dict
    val: list
    vaggsida: dict
    foralder: str | None = None
    x: dict = field(default_factory=dict)
    kov: dict = field(default_factory=dict)
    termer: dict = field(default_factory=dict)
    poang: float = -1e18
    storst: list = field(default_factory=list)
    saknade: list = field(default_factory=list)

    def signatur(self):
        return (tuple(sorted(self.assoc.items())), tuple(sorted(self.rum_av.items())),
                tuple(sorted((e.id, e.fran, e.till) for e in self.ents.values())))


def ent_for(h: Hyp, nyckel: str, k: int, rum: int | None = None):
    hit = None
    for e in sorted(h.ents.values(), key=lambda e: e.fran):
        if e.nyckel == nyckel and e.unik and e.giltig(k) and (rum is None or e.rum == rum):
            hit = e.id
    return hit


def relationer(h: Hyp, obs: Observationer, K: int):
    rel = set()
    for k in range(K):
        dets = {d.id: d for d in obs.klipp[k].detektioner}
        for d in obs.klipp[k].detektioner:
            if d.vid and d.vid in dets:
                rel.add(("vid", h.assoc[(k, d.id)], h.assoc[(k, d.vid)]))
            if d.pa and d.pa in dets:
                rel.add(("pa", h.assoc[(k, d.id)], h.assoc[(k, d.pa)]))
    return rel


def beskriv(h: Hyp, obs: Observationer, K: int) -> str:
    vid = {a: b for t, a, b in relationer(h, obs, K) if t == "vid"}
    bord = sorted(e.id for e in h.ents.values() if e.klass == "bord")
    delar = [f"{len(bord)} bord"]
    pers = sorted((e for e in h.ents.values() if e.klass == "person"), key=lambda e: (e.nyckel or "", e.fran))
    senaste = {e.nyckel: e for e in pers}
    for _, e in sorted(senaste.items()):
        if e.id in vid:
            delar.append(f"{kort(e.id)} vid {vid[e.id]}")
    flytt = sorted({f"{kort(e.id)} i {e.id.split('@')[1]}" for e in pers if "@" in e.id})
    if flytt:
        delar.append("flyttat: " + ", ".join(flytt))
    nrum = len({h.rum_av[k] for k in range(K)})
    if nrum > 1:
        delar.append(f"{nrum} rum")
    return "; ".join(delar)


def karna(h: Hyp, obs: Observationer, K: int) -> str:
    """Kärntron: vilka av rollerna som sitter vid samma bord, flyttar och rum. Bakgrund och föremål ingår inte."""
    vid = {a: b for t, a, b in relationer(h, obs, K) if t == "vid"}
    senaste = {}
    for e in sorted(h.ents.values(), key=lambda e: e.fran):
        if e.klass == "person" and e.unik:
            senaste[e.nyckel] = e.id
    grupper = {}
    for eid in senaste.values():
        if eid in vid:
            grupper.setdefault(vid[eid], []).append(kort(eid))
    delar = []
    for namn in sorted((sorted(v) for v in grupper.values()), key=lambda v: v[0]):
        delar.append(" och ".join(namn) + (" vid samma bord" if len(namn) > 1 else " vid eget bord"))
    flytt = sorted({kort(e.id) for e in h.ents.values() if e.klass == "person" and "@" in e.id})
    if flytt:
        delar.append("flyttat: " + ", ".join(flytt))
    nrum = len({h.rum_av[k] for k in range(K)})
    if nrum > 1:
        delar.append(f"{nrum} rum")
    return "; ".join(delar) or "ingen sittande roll"


def par_i(text: str) -> dict:
    """Par av roller och om de sitter ihop, ur kärntrons text."""
    ihop, alla = {}, []
    for d in text.split("; "):
        for slut, tillsammans in ((" vid samma bord", True), (" vid eget bord", False)):
            if d.endswith(slut):
                namn = d[: -len(slut)].split(" och ")
                alla.append(namn)
                for i, a in enumerate(namn):
                    for b in namn[i + 1:]:
                        ihop[tuple(sorted((a, b)))] = tillsammans
    platt = [(n, gi) for gi, g in enumerate(alla) for n in g]
    for i, (a, ga) in enumerate(platt):
        for b, gb in platt[i + 1:]:
            ihop.setdefault(tuple(sorted((a, b))), ga == gb)
    return ihop


def motsager(gammal: str, ny: str) -> bool:
    g, n = par_i(gammal), par_i(ny)
    if any(g[k] != n[k] for k in g if k in n):
        return True
    return ("flyttat" in ny and "flyttat" not in gammal) or (" rum" in ny and " rum" not in gammal)


# ---------------------------------------------------------------- lösning

class _Bygge:
    def __init__(self, h: Hyp, K: int):
        self.idx, n = {}, 0
        for k in range(K):
            self.idx[("cam", k)] = n
            n += 3
        for eid in sorted(h.ents):
            self.idx[("ent", eid)] = n
            n += 2
        for r in sorted({h.rum_av[k] for k in range(K)}):
            self.idx[("rum", r)] = n
            n += 4
        self.idx[("alfa",)] = n
        self.n = n + 1
        self.termer, self.m = [], 0

    def T(self, fn, nycklar, namn, nout=1):
        ix = [self.idx[key] + off for key, off in nycklar]
        self.termer.append((fn, ix, self.m, nout, namn))
        self.m += nout


def _C(k):
    return [(("cam", k), i) for i in range(3)]


def _E(e):
    return [(("ent", e), i) for i in range(2)]


def _RM(r):
    return [(("rum", r), i) for i in range(4)]


_A = [(("alfa",), 0)]


def _bygg(h: Hyp, obs: Observationer, K: int) -> _Bygge:
    b = _Bygge(h, K)
    th0 = h.x["cam"][0][2]
    b.T(lambda x, y, t: (x / 1e-3, y / 1e-3, wrap(t - th0) / 1e-3), _C(0), "ram", 3)
    for k in range(K):
        o = obs.klipp[k]
        r = h.rum_av[k]
        if o.manhattan_deg is not None and k > 0:
            m, s = o.manhattan_deg.v * D2R, max(o.manhattan_deg.s, R["sigma_manhattan_deg"]) * D2R
            b.T(lambda x, y, t, m=m, s=s: (_rob(wrap90(t - m) / s),), _C(k), f"{o.klipp} manhattan")
        if o.ljus_bearing_deg is not None:
            ll, s = o.ljus_bearing_deg.v * D2R, max(o.ljus_bearing_deg.s, R["sigma_ljus_deg"]) * D2R
            b.T(lambda x, y, t, a, ll=ll, s=s: (_rob(wrap(t - ll - a) / s),), _C(k) + _A, f"{o.klipp} ljus")
        for d in o.detektioner:
            e = h.assoc[(k, d.id)]
            bb, sb = d.bearing_deg.v * D2R, max(d.bearing_deg.s, 0.3) * D2R
            dd, sd = d.djup_m.v, max(d.djup_m.s, 0.02)
            b.T(lambda cx, cy, t, ex, ey, bb=bb, sb=sb, dd=dd, sd=sd: _strale(cx, cy, t, ex, ey, bb, sb, dd, sd),
                _C(k) + _E(e), f"{o.klipp} {kort(e)} stråle", 2)
            if d.blick_mot and d.vridning_deg is not None:
                mal = ent_for(h, d.blick_mot, k, r)
                if mal is not None and mal != e:
                    phi = d.vridning_deg.v * D2R
                    s = math.hypot(d.vridning_deg.s * D2R, R["sigma_blick_deg"] * D2R)
                    b.T(lambda px, py, qx, qy, cx, cy, t, phi=phi, s=s:
                        (_rob(wrap(math.atan2(qy - py, qx - px) - (t - phi)) / s),),
                        _E(e) + _E(mal) + _C(k), f"{o.klipp} blick {kort(e)}→{kort(mal)}")
        for i, w in enumerate(o.vaggar):
            sida = h.vaggsida[(k, i)]
            dv, sv = w.avstand_m.v, max(w.avstand_m.s, 0.03)
            b.T(lambda cx, cy, t, x0, x1, y0, y1, sida=sida, dv=dv, sv=sv:
                (_rob((_vaggavst(sida, cx, cy, x0, x1, y0, y1) - dv) / sv),),
                _C(k) + _RM(r), f"{o.klipp} vägg {sida}")
        b.T(lambda cx, cy, t, x0, x1, y0, y1: _inne(cx, cy, x0, x1, y0, y1, 0.1), _C(k) + _RM(r),
            f"{o.klipp} kamera inne", 4)
        for e in sorted(h.ents.values(), key=lambda e: e.id):
            if e.rum == r and e.giltig(k) and e.klass in ("person", "bord"):
                rad = R["kamera_fri_radie_m"] if e.klass == "person" else R["kamera_fri_bord_m"]
                b.T(lambda cx, cy, t, ex, ey, rad=rad:
                    (max(0.0, rad - math.hypot(ex - cx, ey - cy)) / R["sigma_kropp_m"],),
                    _C(k) + _E(e.id), f"{o.klipp} kameran i {kort(e.id)}")
        if k > 0:
            b.T(lambda cx, cy, t, x0, x1, y0, y1: ((cx - (x0 + x1) / 2) / R["svag_prior_m"],
                                                   (cy - (y0 + y1) / 2) / R["svag_prior_m"]),
                _C(k) + _RM(r), "svag", 2)
    for typ, a, c in sorted(relationer(h, obs, K)):
        if typ == "vid":
            b.T(lambda ax, ay, bx, by: ((math.hypot(ax - bx, ay - by) - R["vid_avstand_m"]) / R["sigma_vid_m"],),
                _E(a) + _E(c), f"{kort(a)} vid {kort(c)}")
        else:
            b.T(lambda ax, ay, bx, by: (math.hypot(ax - bx, ay - by) / R["sigma_pa_m"],),
                _E(a) + _E(c), f"{kort(a)} på {kort(c)}")
    ents = sorted(h.ents.values(), key=lambda e: e.id)
    for e in ents:
        if e.sida:
            b.T(lambda ex, ey, x0, x1, y0, y1, s=e.sida: (_vaggavst(s, ex, ey, x0, x1, y0, y1) / R["sigma_vagg_pa_m"],),
                _E(e.id) + _RM(e.rum), f"{kort(e.id)} i vägg {e.sida}")
        else:
            b.T(lambda ex, ey, x0, x1, y0, y1: _inne(ex, ey, x0, x1, y0, y1, R["marginal_vagg_m"]),
                _E(e.id) + _RM(e.rum), f"{kort(e.id)} inne", 4)
        b.T(lambda ex, ey, x0, x1, y0, y1: ((ex - (x0 + x1) / 2) / R["svag_prior_m"],
                                            (ey - (y0 + y1) / 2) / R["svag_prior_m"]),
            _E(e.id) + _RM(e.rum), "svag", 2)
    pers = [e for e in ents if e.klass == "person"]
    for e1, e2 in itertools.combinations(pers, 2):
        if e1.rum == e2.rum:
            if e1.rum == e2.rum and (e1.till is None or e2.fran < e1.till) and (e2.till is None or e1.fran < e2.till):
                b.T(lambda ax, ay, bx, by: (max(0.0, R["person_minsta_avstand_m"] - math.hypot(ax - bx, ay - by))
                                            / R["sigma_kollision_m"],),
                    _E(e1.id) + _E(e2.id), f"{kort(e1.id)} i {kort(e2.id)}")
    bord = [e for e in ents if e.klass == "bord"]
    for e1, e2 in itertools.combinations(bord, 2):
        if e1.rum == e2.rum:
            b.T(lambda ax, ay, bx, by: (max(0.0, R["bord_minsta_avstand_m"] - math.hypot(ax - bx, ay - by))
                                        / R["sigma_kollision_m"],),
                _E(e1.id) + _E(e2.id), f"{e1.id} i {e2.id}")
    for r in sorted({h.rum_av[k] for k in range(K)}):
        b.T(_rumsstorlek, _RM(r), f"rum {r} storlek", 4)
    b.T(lambda a, a0=h.x["alfa"]: (wrap(a - a0) / math.pi,), _A, "svag")
    return b


def _fun(p, b: _Bygge):
    pl = p.tolist()
    r = np.empty(b.m)
    for fn, ix, o, n, _ in b.termer:
        r[o:o + n] = fn(*[pl[i] for i in ix])
    return r


def _jac(p, b: _Bygge):
    pl = p.tolist()
    J = np.zeros((b.m, b.n))
    st = 1e-6
    for fn, ix, o, n, _ in b.termer:
        args = [pl[i] for i in ix]
        f0 = fn(*args)
        for j, i in enumerate(ix):
            a2 = list(args)
            a2[j] += st
            f1 = fn(*a2)
            for q in range(n):
                d = f1[q] - f0[q]
                if -1.0 < d < 1.0:            # vinkelns hopp vid ±pi räknas inte
                    J[o + q, i] += d / st
    return J


def _packa(h: Hyp, b: _Bygge):
    p = np.zeros(b.n)
    for key, i in b.idx.items():
        if key[0] == "cam":
            p[i:i + 3] = h.x["cam"][key[1]]
        elif key[0] == "ent":
            p[i:i + 2] = h.x["ent"][key[1]]
        elif key[0] == "rum":
            p[i:i + 4] = h.x["rum"][key[1]]
        else:
            p[i] = h.x["alfa"]
    return p


def _los(h: Hyp, obs: Observationer, K: int, max_nfev: int = 120):
    b = _bygg(h, obs, K)
    res = least_squares(lambda p: _fun(p, b), _packa(h, b), jac=lambda p: _jac(p, b),
                        method="trf", x_scale="jac", max_nfev=max_nfev, ftol=1e-6, xtol=1e-6)
    p = res.x
    J = res.jac
    kov = np.linalg.pinv(J.T @ J + 1e-9 * np.eye(b.n))
    h.kov = {"cam": {}, "ent": {}, "rum": {}, "alfa": 0.0}
    for key, i in b.idx.items():
        if key[0] == "cam":
            v = p[i:i + 3].copy()
            v[2] = wrap(v[2])
            h.x["cam"][key[1]] = v
            h.kov["cam"][key[1]] = kov[i:i + 3, i:i + 3]
        elif key[0] == "ent":
            h.x["ent"][key[1]] = p[i:i + 2].copy()
            h.kov["ent"][key[1]] = kov[i:i + 2, i:i + 2]
        elif key[0] == "rum":
            h.x["rum"][key[1]] = p[i:i + 4].copy()
            h.kov["rum"][key[1]] = kov[i:i + 4, i:i + 4]
        else:
            h.x["alfa"] = wrap(p[i])
            h.kov["alfa"] = float(kov[i, i])
    f = res.fun
    passning = -0.5 * float(f @ f)
    bidrag = []
    for fn, ix, o, n, namn in b.termer:
        if namn not in ("svag", "ram"):
            bidrag.append((namn, float(f[o:o + n] @ f[o:o + n])))
    bidrag.sort(key=lambda t: -t[1])
    h.storst = [(n, round(v, 1)) for n, v in bidrag[:3] if v > 2.0]
    return passning


HOJD = {"bord": 0.74, "dorr": 1.0, "foremal": 0.8, "stol": 0.6}


def _djupdiff(o, cam, p, z_e):
    """Projicera en punkt i tagningens kamera. Returnerar uppmätt djup minus punktens djup i den pixeln
    (positivt: kameran ser förbi punkten, så något där borde ha synts), eller None om okänt eller utanför bild."""
    g = o.djupgrid
    W, H = o.kamera.bild_px
    f = (W / 2) / math.tan(o.kamera.hfov_deg.v / 2 * D2R)
    th, pit, h0 = cam[2], o.kamera.pitch_deg.v * D2R, o.kamera.hojd_m.v
    vx, vy, vz = p[0] - cam[0], p[1] - cam[1], z_e - h0
    ct, st, cp, sp = math.cos(th), math.sin(th), math.cos(pit), math.sin(pit)
    zc = vx * ct * cp + vy * st * cp + vz * sp
    if zc < 0.3:
        return None
    xc = vx * st - vy * ct
    yc = -vx * ct * sp - vy * st * sp + vz * cp
    u, v = W / 2 + f * xc / zc, H / 2 - f * yc / zc
    if not (0 <= u < W and 0 <= v < H):
        return None
    d = g.varden[int(v / H * g.rader) * g.kolumner + int(u / W * g.kolumner)]
    return None if d < 0 else d - zc


def _fri(o, b_rad):
    if o.stralar is None or not o.stralar.bearing_deg:
        return None
    return float(np.interp(math.degrees(b_rad), o.stralar.bearing_deg, o.stralar.fri_m))


def _poang(h: Hyp, obs: Observationer, K: int, passning: float):
    struktur = 0.0
    bar = {b for t, a, b in relationer(h, obs, K) if t == "vid" and h.ents[a].unik}
    for e in h.ents.values():
        if e.klass != "person" and not e.unik:
            if e.klass == "foremal":
                typ = (e.nyckel or "").split(":")[-1].split("_")
                struktur -= next((FOREMAL_PRIS[t] for t in typ if t in FOREMAL_PRIS), R["pris_smasak"])
            elif e.klass == "fonster":
                struktur -= R["pris_smasak"]
            elif e.klass == "bord" and e.id not in bar:
                struktur -= R["pris_bakgrundsbord"]      # lokaler har många bord; bara rollernas bord är få
            else:
                struktur -= R["pris_entitet"]
    for _, n in Counter(e.nyckel for e in h.ents.values() if e.klass == "person").items():
        struktur -= R["pris_flytt"] * max(0, n - 1)
    rum_set = {h.rum_av[k] for k in range(K)}
    struktur -= R["pris_nytt_rum"] * (len(rum_set) - 1)
    rum = 0.0
    for k in range(1, K):
        o = obs.klipp[k]
        samma = [obs.klipp[j] for j in range(k) if h.rum_av[j] == h.rum_av[k]]
        for kat, v in o.rumsnycklar.items():
            if samma:
                sett = {j.rumsnycklar.get(kat) for j in samma} - {None}
                if sett:
                    rum += math.log(R["rum_lika_samma"] if v in sett else 1 - R["rum_lika_samma"])
            else:
                sett = {obs.klipp[j].rumsnycklar.get(kat) for j in range(k)} - {None}
                if sett:
                    rum += math.log(R["rum_lika_annat"] if v in sett else 1 - R["rum_lika_annat"])
    syn = 0.0
    h.saknade = []
    for k in range(K):
        o = obs.klipp[k]
        r = h.rum_av[k]
        cam = h.x["cam"][k]
        sedda = {h.assoc[(k, d.id)] for d in o.detektioner}
        halv = (o.kamera.hfov_deg.v / 2 - 3) * D2R
        for e in sorted(h.ents.values(), key=lambda e: e.id):
            if e.rum != r or not e.giltig(k) or e.id in sedda or e.klass not in FASTA + ("foremal",):
                continue
            if e.id in h.kov.get("ent", {}) and sigma_max(h.kov["ent"][e.id]) > R["synlighet_max_sigma_m"]:
                continue                                   # okänt läge: kan inte säga att det borde synas
            bb, dist = bearing(cam, h.x["ent"][e.id])
            if o.djupgrid is not None:                    # i bildplanet mot det kalibrerade djupet
                z_e = HOJD.get(e.klass, 1.0)
                if e.klass == "person":
                    z_e = 1.3 if any(d.pose == "staende" for k2 in range(K) for d in obs.klipp[k2].detektioner
                                     if h.assoc.get((k2, d.id)) == e.id) else 1.0
                diff = _djupdiff(o, cam, h.x["ent"][e.id], z_e)
                # personer upptäcks nästan alltid när de syns: frånvaro räknas om de inte är tydligt skymda
                grans = -R["synlighet_marginal_m"] if e.klass == "person" else R["synlighet_marginal_m"]
                if diff is None or diff < grans:
                    continue
            else:
                if abs(bb) > halv or dist < 0.5 or dist > 12:
                    continue
                fri = _fri(o, bb)
                if fri is None:
                    continue
                if dist > fri + (0.3 if e.klass == "dorr" else -0.3):
                    continue
            pm = R["p_miss_foremal"] if e.klass == "foremal" else R["p_miss_fast"]
            syn += math.log(pm)
            h.saknade.append(f"{o.klipp}: {kort(e.id)} borde synas ({dist:.1f} m)")
    h.termer = {"passning": round(passning, 2), "struktur": round(struktur, 2),
                "rum": round(rum, 2), "synlighet": round(syn, 2)}
    h.poang = passning + struktur + rum + syn


# ---------------------------------------------------------------- utbyggnad klipp för klipp

_raknare = itertools.count(1)


def _alternativ(h: Hyp, d, k: int, r: int):
    if d.unik and d.nyckel:
        eid = ent_for(h, d.nyckel, k, r)
        if eid is None:
            return [("ny", None)]
        alt = [("finns", eid)]
        if d.klass == "person":
            alt.append(("flytt", eid))
        return alt
    alt = [("finns", e.id) for e in sorted(h.ents.values(), key=lambda e: e.id)
           if e.klass == d.klass and e.rum == r and e.giltig(k) and not e.unik
           and (d.nyckel is None or e.nyckel is None or e.nyckel == d.nyckel)]
    return alt + [("ny", None)]


def _riktning(t):
    return np.array([math.cos(t), math.sin(t)])


def _nytt_id(ents, d, o):
    if d.unik and d.nyckel:
        bas = d.nyckel.split(":", 1)[-1]
        return bas if bas not in ents else f"{bas}@{o.klipp}"
    n = 1 + sum(1 for e in ents.values() if e.klass == d.klass)
    return f"{d.klass}_{n}"


def _barn(h: Hyp, obs: Observationer, k: int, r_val, komb, th: float):
    o = obs.klipp[k]
    ents, assoc, rum_av = dict(h.ents), dict(h.assoc), dict(h.rum_av)
    val, vaggsida = list(h.val), dict(h.vaggsida)
    x = {"cam": {kk: v.copy() for kk, v in h.x.get("cam", {}).items()},
         "ent": {kk: v.copy() for kk, v in h.x.get("ent", {}).items()},
         "rum": {kk: v.copy() for kk, v in h.x.get("rum", {}).items()},
         "alfa": h.x.get("alfa", 0.0)}
    if r_val == "nytt":
        r = 1 + max(x["rum"]) if x["rum"] else 0
        val.append(f"{o.klipp}: annat rum")
    else:
        r = r_val
    rum_av[k] = r
    # kamerans läge ur detektioner som knyts till befintliga saker
    pos = []
    for d, (typ, eid) in zip(o.detektioner, komb):
        if typ == "finns":
            pos.append(x["ent"][eid] - d.djup_m.v * _riktning(th - d.bearing_deg.v * D2R))
    if k == 0:
        c = np.zeros(2)
    elif pos:
        c = np.mean(pos, axis=0)
    elif r in x["rum"]:
        x0, x1, y0, y1 = x["rum"][r]
        c = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        for i, w in enumerate(o.vaggar):
            s = sida_for(th - w.bearing_deg.v * D2R)
            if s == "E":
                c[0] = x1 - w.avstand_m.v
            elif s == "W":
                c[0] = x0 + w.avstand_m.v
            elif s == "N":
                c[1] = y1 - w.avstand_m.v
            else:
                c[1] = y0 + w.avstand_m.v
    else:
        ovr = max((v[1] for v in x["rum"].values()), default=0.0)
        c = np.array([ovr + 12.0, 0.0])
    x["cam"][k] = np.array([c[0], c[1], th])
    if k == 0 and o.ljus_bearing_deg is not None:
        x["alfa"] = wrap(th - o.ljus_bearing_deg.v * D2R)
    # nya saker
    for d, (typ, eid) in zip(o.detektioner, komb):
        p = c + d.djup_m.v * _riktning(th - d.bearing_deg.v * D2R)
        if typ == "finns":
            assoc[(k, d.id)] = eid
            continue
        if typ == "flytt":
            ents[eid] = replace(ents[eid], till=k)
            nid = f"{kort(eid)}@{o.klipp}"
            val.append(f"{o.klipp}: {kort(eid)} har flyttat")
        else:
            nid = _nytt_id(ents, d, o)
            if not d.unik:
                val.append(f"{o.klipp}: nytt {d.klass} ({nid})")
        ents[nid] = Ent(nid, d.klass, d.nyckel, d.unik, r, k)
        x["ent"][nid] = p
        assoc[(k, d.id)] = nid
    # rummets gränser: ett nytt rum tar väggarna rakt av, ett befintligt vidgas bara
    ny = r not in x["rum"]
    if ny:
        x["rum"][r] = np.array([c[0] - 3.0, c[0] + 3.0, c[1] - 3.0, c[1] + 3.0])
    g = x["rum"][r]
    for i, w in enumerate(o.vaggar):
        s = sida_for(th - w.bearing_deg.v * D2R)
        vaggsida[(k, i)] = s
        v = w.avstand_m.v
        if s == "E":
            g[1] = c[0] + v if ny else max(g[1], c[0] + v)
        elif s == "W":
            g[0] = c[0] - v if ny else min(g[0], c[0] - v)
        elif s == "N":
            g[3] = c[1] + v if ny else max(g[3], c[1] + v)
        else:
            g[2] = c[1] - v if ny else min(g[2], c[1] - v)
    for eid, e in ents.items():
        if e.rum == r and eid in x["ent"]:
            px, py = x["ent"][eid]
            g[0], g[1] = min(g[0], px - 0.3), max(g[1], px + 0.3)
            g[2], g[3] = min(g[2], py - 0.3), max(g[3], py + 0.3)
    # dörrar och fönster sitter i närmaste vägg
    for d, (typ, eid) in zip(o.detektioner, komb):
        nid = assoc[(k, d.id)]
        if d.pa_vagg and ents[nid].sida is None:
            px, py = x["ent"][nid]
            avst = {"W": abs(px - g[0]), "E": abs(g[1] - px), "S": abs(py - g[2]), "N": abs(g[3] - py)}
            ents[nid] = replace(ents[nid], sida=min(avst, key=avst.get))
    return Hyp(id=f"h{next(_raknare)}", ents=ents, assoc=assoc, rum_av=rum_av, val=val,
               vaggsida=vaggsida, foralder=h.id, x=x)


def _yaw_alternativ(h: Hyp, o, k: int):
    if k == 0:
        m = o.manhattan_deg.v * D2R if o.manhattan_deg is not None else 0.0
        return [wrap(m + math.pi / 2)]
    ll = o.ljus_bearing_deg.v * D2R if o.ljus_bearing_deg is not None else None
    if o.manhattan_deg is None:
        return [wrap(ll + h.x["alfa"])] if ll is not None else [h.x["cam"][k - 1][2]]
    bas = [wrap(o.manhattan_deg.v * D2R + j * math.pi / 2) for j in range(4)]
    if ll is not None:
        return [min(bas, key=lambda t: abs(wrap(t - ll - h.x["alfa"])))]
    return bas        # utan ljus: fyra vridningar prövas som egna hypoteser


def _expandera(h: Hyp, obs: Observationer, k: int):
    o = obs.klipp[k]
    rumsval = [0] if k == 0 else sorted({h.rum_av[j] for j in range(k)}) + ["nytt"]
    barn = []
    dets = o.detektioner
    iu = [i for i, d in enumerate(dets) if d.unik and d.nyckel]
    ig = [i for i, d in enumerate(dets) if not (d.unik and d.nyckel)]
    for r_val in rumsval:
        r = (1 + max(h.x["rum"])) if r_val == "nytt" else r_val
        alt = [_alternativ(h, d, k, r) if r_val != "nytt" else [("ny", None)] for d in dets]
        for th in _yaw_alternativ(h, o, k):
            for uk in itertools.product(*[alt[i] for i in iu]) if iu else [()]:
                ank = [h.x["ent"][eid] - dets[i].djup_m.v * _riktning(th - dets[i].bearing_deg.v * D2R)
                       for i, (typ, eid) in zip(iu, uk) if typ == "finns"]
                c0 = np.mean(ank, axis=0) if ank else None
                galt = []
                for i in ig:
                    a = alt[i]
                    if c0 is not None:
                        d = dets[i]
                        pv = c0 + d.djup_m.v * _riktning(th - d.bearing_deg.v * D2R)
                        grind = 3 * d.djup_m.s + 1.0
                        a = [x for x in a if x[0] != "finns" or np.linalg.norm(h.x["ent"][x[1]] - pv) < grind]
                    galt.append(a)
                for gk in itertools.product(*galt) if galt else [()]:
                    komb = [None] * len(dets)
                    for i, v in zip(iu, uk):
                        komb[i] = v
                    for i, v in zip(ig, gk):
                        komb[i] = v
                    valda = [eid for typ, eid in komb if typ == "finns"]
                    if len(valda) != len(set(valda)):
                        continue
                    c = _barn(h, obs, k, r_val, komb, th)
                    passning = _los(c, obs, k + 1, max_nfev=8)
                    _poang(c, obs, k + 1, passning)
                    barn.append(c)
    return barn


def _dela(h: Hyp, obs: Observationer, K: int):
    """Omprövning av gamla kopplingar: en generisk sak som kopplats ihop över flera klipp delas,
    så att detektionerna i ett av klippen blir en egen sak. Behålls bara om den förklarar bättre."""
    sedd = {}
    for (k, did), eid in h.assoc.items():
        e = h.ents[eid]
        if not e.unik and e.klass in ("bord", "person", "dorr", "foremal"):
            sedd.setdefault(eid, set()).add(k)
    ut = []
    for eid, ks in sorted(sedd.items()):
        if len(ks) < 2:
            continue
        e = h.ents[eid]
        for j in sorted(ks):
            o = obs.klipp[j]
            ents, assoc = dict(h.ents), dict(h.assoc)
            x = {"cam": {kk: v.copy() for kk, v in h.x["cam"].items()},
                 "ent": {kk: v.copy() for kk, v in h.x["ent"].items()},
                 "rum": {kk: v.copy() for kk, v in h.x["rum"].items()}, "alfa": h.x["alfa"]}
            n = 1 + sum(1 for q in ents.values() if q.klass == e.klass)
            nid = f"{e.klass}_{n}"
            while nid in ents:
                n += 1
                nid = f"{e.klass}_{n}"
            ents[nid] = Ent(nid, e.klass, e.nyckel, e.unik, e.rum, j, sida=e.sida)
            cam = x["cam"][j]
            pos = []
            for d in o.detektioner:
                if assoc.get((j, d.id)) == eid:
                    assoc[(j, d.id)] = nid
                    pos.append(cam[:2] + d.djup_m.v * _riktning(cam[2] - d.bearing_deg.v * D2R))
            x["ent"][nid] = np.mean(pos, axis=0)
            ut.append(Hyp(id=f"h{next(_raknare)}", ents=ents, assoc=assoc, rum_av=dict(h.rum_av),
                          val=list(h.val) + [f"omprövat: {o.klipp}: {e.klass} är en egen ({nid}), inte {eid}"],
                          vaggsida=dict(h.vaggsida), foralder=h.foralder, x=x))
    return ut


@dataclass
class Steg:
    k: int
    klipp: str
    stråle: list
    sannolikhet: list
    alla: dict


def softmax(v):
    v = np.asarray(v, dtype=float)
    e = np.exp(v - v.max())
    return e / e.sum()


def kor(obs: Observationer, beam: int | None = None):
    """Läs alla klipp i ordning. Returnerar ett Steg per klipp."""
    B = beam or int(R["beam"])
    rot = Hyp(id="h0", ents={}, assoc={}, rum_av={}, val=[], vaggsida={}, x={"cam": {}, "ent": {}, "rum": {}, "alfa": 0.0})
    strale = [rot]
    historik = []
    for k in range(len(obs.klipp)):
        barn = []
        for h in strale:
            barn.extend(_expandera(h, obs, k))
        barn.sort(key=lambda c: (-c.poang, c.id))
        valda = barn[:3 * B]
        forra = [c for c in barn if c.foralder == strale[0].id]
        raka = [c for c in forra if not any(("flyttat" in v or "annat rum" in v) for v in c.val[len(strale[0].val):])]
        for c in forra[:2] + raka[:1]:
            if c not in valda:
                valda.append(c)
        for c in valda:                        # fas 2: full lösning för de bästa
            _poang(c, obs, k + 1, _los(c, obs, k + 1))
        valda.sort(key=lambda c: (-c.poang, c.id))
        for c in valda[:2]:                    # omprövning av gamla kopplingar (dela)
            for d in _dela(c, obs, k + 1):
                _poang(d, obs, k + 1, _los(d, obs, k + 1))
                valda.append(d)
        barn = valda
        unika = {}
        for c in barn:
            s = c.signatur()
            if s not in unika or c.poang > unika[s].poang:
                unika[s] = c
        barn = sorted(unika.values(), key=lambda c: (-c.poang, c.id))
        strale = barn[:B]
        sedda = {karna(c, obs, k + 1) for c in strale}
        for c in barn[B:3 * B]:
            kt = karna(c, obs, k + 1)
            if kt not in sedda and len(sedda) < B:
                strale = strale[:-1] + [c] if len(strale) >= B else strale + [c]
                sedda = {karna(x, obs, k + 1) for x in strale}
        strale.sort(key=lambda c: (-c.poang, c.id))
        historik.append(Steg(k, obs.klipp[k].klipp, strale, softmax([c.poang for c in strale]).tolist(),
                             {c.id: c for c in barn}))
    return historik


def kalla_for(h: Hyp, eid: str, obs: Observationer, K: int) -> str:
    if sigma_max(h.kov["ent"][eid]) > R["zon_troskel_m"]:
        return "relational_hypothesis"
    dets = [d for k in range(K) for d in obs.klipp[k].detektioner if h.assoc.get((k, d.id)) == eid]
    if dets and all(d.amodal for d in dets):
        return "amodal_inferred"
    return "observed"


def sedd_i(h: Hyp, eid: str, obs: Observationer, K: int) -> list:
    return [obs.klipp[k].klipp for k in range(K)
            if any(h.assoc.get((k, d.id)) == eid for d in obs.klipp[k].detektioner)]


# ---------------------------------------------------------------- logg

def sigma_max(kov2) -> float:
    return float(math.sqrt(max(np.linalg.eigvalsh(kov2).max(), 0.0)))


def logg(historik, obs: Observationer):
    """Ett steg per klipp: tro, sannolikhet, omprövning med skäl och vad klippet tillförde."""
    rader = []
    forra = None
    for st in historik:
        K = st.k + 1
        bast = {}
        for c in st.stråle:
            kt = karna(c, obs, K)
            bast[kt] = max(bast.get(kt, -1e18), c.poang)
        namn = list(bast)
        samlat = dict(zip(namn, softmax([bast[n] for n in namn]).tolist()))
        tro = max(samlat, key=samlat.get)
        h = next(c for c in st.stråle if karna(c, obs, K) == tro)
        hyps = []
        sedda = set()
        for c, p in zip(st.stråle, st.sannolikhet):
            besk = beskriv(c, obs, K)
            hyps.append(dict(id=c.id, beskrivning=besk, poang=round(c.poang, 2), sannolikhet=round(p, 4),
                             termer=c.termer))
            sedda.add(besk)
        osak = {kort(e): round(sigma_max(h.kov["ent"][e]), 2) for e in sorted(h.ents)}
        ompr = None
        bidrag = None
        if forra is not None:
            ftro, fh = forra
            if motsager(ftro, tro):
                gamla = sorted((c for c in st.alla.values() if not motsager(ftro, karna(c, obs, K))),
                               key=lambda c: -c.poang)
                n0 = len(fh.val)
                raka = [c for c in gamla if not any(("flyttat" in v or "annat rum" in v) for v in c.val[n0:])]
                delar = [f"Tron '{ftro}' övergavs för '{tro}'." if samlat[tro] >= R["omprovning_min_p"]
                         else f"Vacklar (P {samlat[tro]:.2f}): '{ftro}' mot '{tro}'."]
                if raka:
                    r0 = raka[0]
                    mots = "; ".join(f"{n} (chi2 {v})" for n, v in r0.storst) or "inga enskilda"
                    delar.append(f"Om tron gällt oförändrad: poäng {r0.poang - h.poang:+.1f} mot den nya, "
                                 f"största motsägelser: {mots}.")
                    if r0.saknade:
                        delar.append("Saknas i bild: " + "; ".join(r0.saknade[-2:]) + ".")
                rad = [c for c in st.alla.values() if c.foralder == fh.id and c not in raka
                       and any(("flyttat" in v or "annat rum" in v) for v in c.val[n0:])]
                rad.sort(key=lambda c: -c.poang)
                if rad:
                    g = rad[0]
                    delar.append(f"Att rädda den hade krävt: {', '.join(g.val[n0:])} "
                                 f"(poäng {g.poang - h.poang:+.1f}).")
                ompr = " ".join(delar)
            f_osak = {kort(e): round(sigma_max(fh.kov["ent"][e]), 2) for e in fh.ents}
            krymp = [f"{e} {f_osak[e]:.1f}→{v:.1f} m" for e, v in osak.items()
                     if e in f_osak and f_osak[e] > 0.2 and v < 0.7 * f_osak[e]]
            nya = [e for e in osak if e not in f_osak]
            delar = []
            if nya:
                delar.append("nytt: " + ", ".join(nya))
            if krymp:
                delar.append("skärpt: " + ", ".join(krymp))
            bidrag = "; ".join(delar) or "bekräftar"
        else:
            bidrag = "nytt: " + ", ".join(osak)
        rader.append(dict(klipp=st.klipp, tro=tro, sannolikhet=round(samlat[tro], 4), hypoteser=hyps,
                          omprovning=ompr, osakerhet_m=osak, bidrag=bidrag))
        forra = (tro, h)
    return rader
