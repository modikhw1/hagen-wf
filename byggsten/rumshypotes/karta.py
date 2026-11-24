"""2D-översikten: rummet ovanifrån, som hjärnan tror att det ser ut efter varje klipp.

Färg efter källa (blå observerad, orange amodal, gul hypotes eller zon). Ellipserna är 2 sigma.
Grönt är fri yta som någon kamera sett igenom. Streckat grått är den näst bästa hypotesen,
och svarta kors är facit (bara för syntetiska prov).
"""
from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle  # noqa: E402

from hjarna import D2R, ent_for, kalla_for, kort, sigma_max  # noqa: E402
from recept import MATT, bordsvinkel, vandning  # noqa: E402
from regler import R  # noqa: E402

FARG = {"observed": "#2f6fd6", "amodal_inferred": "#f08c2a", "relational_hypothesis": "#d9a400"}


def _rektangel(p, w, d, vinkel):
    c, s = math.cos(vinkel), math.sin(vinkel)
    hw, hd = w / 2, d / 2
    return [(p[0] + c * x - s * y, p[1] + s * x + c * y) for x, y in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))]


def _ellips(p, kov, **kw):
    w, v = np.linalg.eigh(kov)
    w = np.maximum(w, 1e-8)
    vinkel = math.degrees(math.atan2(v[1, 1], v[0, 1]))
    return Ellipse(p, 4 * math.sqrt(w[1]), 4 * math.sqrt(w[0]), angle=vinkel, **kw)


def _sak(ax, h, eid, obs, K, farg, alfa=1.0, streck=False, etikett=None):
    e, p = h.ents[eid], h.x["ent"][eid]
    kw = dict(facecolor="none" if streck else farg, edgecolor=farg if not streck else "#888",
              linestyle="--" if streck else "-", alpha=alfa, zorder=6, lw=1.0)
    if e.klass == "bord":
        ax.add_patch(Polygon(_rektangel(p, MATT["bord"][0], MATT["bord"][1], bordsvinkel(h, eid, obs, K)), **kw))
    elif e.klass == "person":
        ax.add_patch(Circle(p, 0.22, **kw))
        v = vandning(h, eid, obs, K)
        if v is not None and not streck:
            ax.annotate("", xy=(p[0] + 0.45 * math.cos(v), p[1] + 0.45 * math.sin(v)), xytext=(p[0], p[1]),
                        arrowprops=dict(arrowstyle="->", color=farg, lw=1.2, alpha=alfa), zorder=7)
    elif e.klass == "dorr":
        vert = e.sida in ("E", "W")
        dx, dy = (0, 0.45) if vert else (0.45, 0)
        ax.plot([p[0] - dx, p[0] + dx], [p[1] - dy, p[1] + dy], color=farg, lw=5, alpha=alfa, zorder=6)
    else:
        ax.add_patch(Rectangle((p[0] - 0.07, p[1] - 0.07), 0.14, 0.14, **kw))
    ax.text(p[0] + 0.24, p[1] + 0.2, etikett or kort(eid), fontsize=6.5, color="#333" if not streck else "#888",
            alpha=alfa, zorder=8)


def rita(h, obs, K: int, fil, titel: str, alt=None, facit: dict | None = None, ram=None):
    fig, ax = plt.subplots(figsize=(4.4, 6.4), dpi=110)
    x0, x1, y0, y1 = h.x["rum"][0]
    rum = Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f3f2ee", edgecolor="none", zorder=0)
    ax.add_patch(rum)
    for k in range(K):
        o = obs.klipp[k]
        if h.rum_av[k] != 0 or o.stralar is None:
            continue
        c = h.x["cam"][k]
        pts = [(c[0], c[1])] + [(c[0] + f * math.cos(c[2] - b * D2R), c[1] + f * math.sin(c[2] - b * D2R))
                                for b, f in zip(o.stralar.bearing_deg, o.stralar.fri_m)]
        ax.add_patch(Polygon(pts, closed=True, facecolor="#5fb85f", alpha=0.10, edgecolor="none", zorder=1))
    sedda = {s for (k, _), s in h.vaggsida.items() if h.rum_av.get(k) == 0}
    sig = np.sqrt(np.maximum(np.diag(h.kov["rum"][0]), 0.0))
    for i, s_ in enumerate(np.minimum(sig, 3.0)):
        if s_ > 0.2:
            if i < 2:
                xv = (x0, x1)[i]
                ax.add_patch(Rectangle((xv - s_, y0), 2 * s_, y1 - y0, facecolor="#999", alpha=0.12, edgecolor="none", zorder=2))
            else:
                yv = (y0, y1)[i - 2]
                ax.add_patch(Rectangle((x0, yv - s_), x1 - x0, 2 * s_, facecolor="#999", alpha=0.12, edgecolor="none", zorder=2))
    for sida, (a, b) in {"W": ((x0, y0), (x0, y1)), "E": ((x1, y0), (x1, y1)),
                         "S": ((x0, y0), (x1, y0)), "N": ((x0, y1), (x1, y1))}.items():
        if sida in sedda:
            ax.plot([a[0], b[0]], [a[1], b[1]], color="#222", lw=2.6, zorder=3)
        else:
            ax.plot([a[0], b[0]], [a[1], b[1]], color="#999", lw=1.2, ls="--", zorder=3)
    # blicklinjer
    par = set()
    for k in range(K):
        for d in obs.klipp[k].detektioner:
            if d.blick_mot:
                a = h.assoc[(k, d.id)]
                m = ent_for(h, d.blick_mot, k, h.rum_av[k])
                if m and (a, m) not in par:
                    par.add((a, m))
                    pa, pm = h.x["ent"][a], h.x["ent"][m]
                    ax.plot([pa[0], pm[0]], [pa[1], pm[1]], color="#b04040", lw=0.7, ls=":", zorder=2)
    if alt is not None:
        for eid, e in sorted(alt.ents.items()):
            if e.rum == 0 and e.klass in ("bord", "person") and (
                    eid not in h.x["ent"] or np.hypot(*(alt.x["ent"][eid] - h.x["ent"][eid])) > 0.5):
                _sak(ax, alt, eid, obs, K, "#888", alfa=0.8, streck=True, etikett=f"{kort(eid)} (alt)")
    for eid, e in sorted(h.ents.items()):
        if e.rum != 0:
            continue
        kall = kalla_for(h, eid, obs, K)
        farg = FARG[kall]
        kov = h.kov["ent"][eid]
        if sigma_max(kov) > R["zon_troskel_m"]:
            el = _ellips(h.x["ent"][eid], kov, facecolor=FARG["relational_hypothesis"], alpha=0.13,
                         edgecolor=FARG["relational_hypothesis"], lw=0.8, zorder=4)
        else:
            el = _ellips(h.x["ent"][eid], kov, facecolor="none", edgecolor=farg, lw=0.8, ls="--", zorder=4)
        ax.add_patch(el)
        el.set_clip_path(rum)
        gammal = e.till is not None and e.till <= K - 1
        _sak(ax, h, eid, obs, K, farg, alfa=0.35 if gammal else 1.0,
             etikett=f"{kort(eid)} (före {obs.klipp[e.till].klipp})" if gammal else None)
    for k in range(K):
        if h.rum_av[k] != 0:
            continue
        c, o = h.x["cam"][k], obs.klipp[k]
        hv = o.kamera.hfov_deg.v / 2 * D2R
        for s in (-1, 1):
            a = c[2] + s * hv
            ax.plot([c[0], c[0] + 0.8 * math.cos(a)], [c[1], c[1] + 0.8 * math.sin(a)], color="#555", lw=0.7, zorder=5)
        ax.add_patch(Polygon(_rektangel(c[:2], 0.22, 0.16, c[2]), facecolor="#555", edgecolor="none", zorder=5))
        ax.text(c[0] - 0.1, c[1] - 0.32, o.klipp, fontsize=6, color="#555", zorder=8)
        kc = h.kov["cam"][k][:2, :2]
        if sigma_max(kc) > 0.15:
            el = _ellips(c[:2], kc, facecolor="none", edgecolor="#777", lw=0.6, ls=":", zorder=4)
            ax.add_patch(el)
            el.set_clip_path(rum)
    if facit:
        for namn, (fx, fy) in facit.items():
            ax.plot(fx, fy, marker="+", color="k", ms=7, mew=1.1, zorder=9)
            if not namn.startswith("cam_"):
                ax.text(fx - 0.15, fy - 0.42, namn.split("_")[0] if namn.startswith("bord") is False else namn,
                        fontsize=5, color="#666", zorder=9)
    if ram is None:
        allx = [x0, x1] + [h.x["cam"][k][0] for k in range(K)]
        ally = [y0, y1] + [h.x["cam"][k][1] for k in range(K)]
        ram = (min(allx) - 0.8, max(allx) + 0.8, min(ally) - 0.8, max(ally) + 0.8)
    ax.set_xlim(ram[0], ram[1])
    ax.set_ylim(ram[2], ram[3])
    ax.set_aspect("equal")
    ax.tick_params(labelsize=6)
    ax.grid(color="#ddd", lw=0.4)
    ax.set_title(titel, fontsize=7.5, loc="left")
    ax.text(0.0, -0.06, "blå observerad · orange amodal · gul zon · grön fri yta · streckat alt · + facit",
            transform=ax.transAxes, fontsize=5.5, color="#555", va="top")
    fig.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.08)
    fig.savefig(fil)
    plt.close(fig)


def tidslinje(filer, ut):
    from PIL import Image
    bilder = [Image.open(f) for f in filer]
    h = max(b.height for b in bilder)
    w = sum(b.width for b in bilder)
    ark = Image.new("RGB", (w, h), "white")
    x = 0
    for b in bilder:
        ark.paste(b, (x, 0))
        x += b.width
    ark.save(ut)
