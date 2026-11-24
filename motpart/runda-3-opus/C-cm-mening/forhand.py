"""Minimal förhandsvisning av ett paket genom paketets egen kamera. PIL, ingen Blender, inget generativt.

Projektionen är grindarnas (`byggsten/brygga/grindar.proj`, samma kamerakonvention som emit_bpy).
Lådor ritas med målaralgoritmen efter klippning mot ett närplan; kroppar som ben mellan leder.
Föremål med `faste` (en hand) följer leden ruta för ruta. Platshållare får sin etikett utskriven.
Det här är en kontrollbild för ägarens blinda dom (K2-förberedelse), inte en rendering av slutlooken.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROT / "byggsten/brygga"))
import grindar  # noqa: E402

NARA = 0.08
BEN = [("c_spine0", "c_spine2"), ("c_spine2", "c_neck"), ("c_neck", "c_head"), ("c_neck", "l_uparm"), ("c_neck", "r_uparm"),
       ("l_uparm", "l_lowarm"), ("l_lowarm", "l_wrist"), ("r_uparm", "r_lowarm"), ("r_lowarm", "r_wrist"),
       ("c_spine0", "l_upleg"), ("c_spine0", "r_upleg"), ("l_upleg", "l_lowleg"), ("l_lowleg", "l_foot"), ("l_foot", "l_ball"),
       ("r_upleg", "r_lowleg"), ("r_lowleg", "r_foot"), ("r_foot", "r_ball"), ("l_wrist", "l_hand_mitt"), ("r_wrist", "r_hand_mitt")]
SIDOR = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
LJUS = np.array([0.4, -0.5, 0.75])
LJUS = LJUS / np.linalg.norm(LJUS)


def _font(storlek):
    for f in ("arial.ttf", "DejaVuSans.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(f, storlek)
        except Exception:
            pass
    return ImageFont.load_default()


def _hex(h):
    h = (h or "#999999").lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _kamera(t, u):
    """Kamera vid ruta u, linjär mellan nycklar (grindar.kamera tar närmaste föregående nyckel)."""
    import drag
    pose = drag.kamera_vid(t, u)
    from rotation import quat_till_mat
    return np.array(pose[:3]), quat_till_mat(pose[3:7]), pose[7]


def _klipp_narplan(pc):
    """Sutherland–Hodgman mot planet z_kam = -NARA (kameran tittar längs -z)."""
    ut = []
    n = len(pc)
    for i in range(n):
        a, b = pc[i], pc[(i + 1) % n]
        ia, ib = -a[2] >= NARA, -b[2] >= NARA
        if ia:
            ut.append(a)
        if ia != ib:
            t = (-NARA - a[2]) / (b[2] - a[2])
            ut.append(a + t * (b - a))
    return ut


def _till_bild(pc, lins, W, H, S):
    fok = lins / S * W
    d = -pc[2]
    return (pc[0] / d * fok + W / 2, -pc[1] / d * fok + H / 2)


def rita(P, u, storlek=(270, 480), rubrik=None, markera: set | None = None):
    """Paketet vid ruta u (global ruta i paketets tidslinje)."""
    W0, H0, S = P["bild"]["bredd"], P["bild"]["hojd"], P["bild"]["sensor_mm"]
    t = next((t for t in P["tagningar"] if t["ut"][0] <= u < t["ut"][1]), P["tagningar"][-1])
    C, R, lins = _kamera(t, u)
    img = Image.new("RGB", (W0, H0), (34, 36, 40))
    dr = ImageDraw.Draw(img, "RGBA")
    prim = []  # (djup, typ, data)
    L = {n: i for i, n in enumerate(P["leder"])}
    leder_u = {}
    for pid, sp in P["rorelse"].items():
        for s in sp:
            if s["ut"][0] <= u < s["ut"][1]:
                r = next((r for r in s["rutor"] if r[0] == u), None)
                if r is None:
                    r = min(s["rutor"], key=lambda r: abs(r[0] - u))
                leder_u[pid] = np.array(r[1:], float).reshape(-1, 3) / 1000
    for o in P["objekt"]:
        if not grindar.synlig(o, u):
            continue
        o2 = o
        if o.get("faste") and o["faste"].get("person") in leder_u:
            X = leder_u[o["faste"]["person"]]
            o2 = dict(o, pos=list(X[L[o["faste"]["led"]]]))
        hv = grindar.horn(o2)
        farg = np.array(_hex(o.get("farg")), float)
        for sida in SIDOR:
            v = hv[list(sida)]
            nrm = np.cross(v[1] - v[0], v[2] - v[0])
            nn = np.linalg.norm(nrm)
            sk = 0.55 + 0.45 * abs(float(nrm @ LJUS) / nn) if nn > 1e-9 else 0.8
            pc = [(p - C) @ R for p in v]
            pk = _klipp_narplan(pc)
            if len(pk) < 3:
                continue
            uv = [_till_bild(p, lins, W0, H0, S) for p in pk]
            djup = float(np.mean([-p[2] for p in pk]))
            alfa = 255 if o["typ"] not in ("vagg",) else 235
            prim.append((djup, "poly", (uv, tuple(int(c * sk) for c in farg) + (alfa,), o)))
    for pid, X in leder_u.items():
        farg = _hex(P["personer"].get(pid, {}).get("farg"))
        for a, b in BEN:
            if a not in L or b not in L:
                continue
            pa, pb = (X[L[a]] - C) @ R, (X[L[b]] - C) @ R
            if -pa[2] < NARA or -pb[2] < NARA:
                continue
            prim.append((float((-pa[2] - pb[2]) / 2) - 0.05, "ben", (_till_bild(pa, lins, W0, H0, S), _till_bild(pb, lins, W0, H0, S), farg)))
        ph = (X[L["c_head"]] - C) @ R
        if -ph[2] >= NARA:
            prim.append((float(-ph[2]) - 0.06, "huvud", (_till_bild(ph, lins, W0, H0, S), farg, lins / S * W0 * 0.11 / -ph[2], pid)))
    prim.sort(key=lambda x: -x[0])
    etiketter = {}
    for djup, typ, data in prim:
        if typ == "poly":
            uv, f, o = data
            dr.polygon([tuple(map(float, p)) for p in uv], fill=f, outline=(0, 0, 0, 90))
            if (o.get("form_status") == "platshallare" or (markera and o["id"] in markera)) and o["typ"] not in ("golv", "vagg"):
                etiketter.setdefault(o["id"], (o.get("etikett") or o["id"], []))[1].append(np.mean(np.array(uv), axis=0))
        elif typ == "ben":
            a, b, f = data
            dr.line([a, b], fill=f + (255,), width=max(3, int(W0 / 90)))
        else:
            c, f, rad, pid = data
            dr.ellipse([c[0] - rad, c[1] - rad, c[0] + rad, c[1] + rad], fill=f + (255,), outline=(0, 0, 0, 160))
    fnt = _font(int(W0 / 22))
    for text, centra in etiketter.values():
        c = np.mean(np.array(centra), axis=0)
        dr.rectangle([c[0] - 4, c[1] - W0 / 40, c[0] + len(text) * W0 / 40 + 4, c[1] + W0 / 40], fill=(255, 255, 255, 200))
        dr.text((c[0], c[1] - W0 / 45), text, fill=(0, 0, 0), font=fnt)
    if P.get("miljo"):
        dr.text((10, H0 - W0 / 12), f"miljö: {P['miljo']['namn']} (platshållare)", fill=(255, 255, 210), font=fnt)
    if rubrik:
        dr.rectangle([0, 0, W0, W0 / 13], fill=(0, 0, 0, 170))
        dr.text((10, 6), rubrik, fill=(255, 255, 255), font=fnt)
    return img.resize(storlek, Image.LANCZOS)


def original_ruta(K, u, storlek=(270, 480)):
    """Originalets videoruta vid ruta u (tagningens mp4 i ingestmappen)."""
    import cv2
    t = next((t for t in K.paket["tagningar"] if t["ut"][0] <= u < t["ut"][1]), None)
    if t is None:
        return Image.new("RGB", storlek, (0, 0, 0))
    f = ROT / "scen/3d/ingest/ut" / K.ingestnamn / "klipp" / f"S{t['id'][1:]}.mp4"
    cap = cv2.VideoCapture(str(f))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(u - t["ut"][0]))
    ok, bild = cap.read()
    cap.release()
    if not ok:
        return Image.new("RGB", storlek, (0, 0, 0))
    return Image.fromarray(bild[:, :, ::-1]).resize(storlek, Image.LANCZOS)


def remsa(P, rutor, storlek=(135, 240), etikett=True):
    bilder = []
    fps = P["tidsbas"]["fps"]
    for u in rutor:
        t = next((t for t in P["tagningar"] if t["ut"][0] <= u < t["ut"][1]), None)
        rub = f"{t['id'] if t else '?'} {u / fps:.1f}s" if etikett else None
        bilder.append(rita(P, u, storlek, rubrik=rub))
    ut = Image.new("RGB", (storlek[0] * len(bilder), storlek[1]), (0, 0, 0))
    for i, b in enumerate(bilder):
        ut.paste(b, (i * storlek[0], 0))
    return ut


def jamnt(P, n=6):
    N = P["tidsbas"]["antal_rutor"]
    return [int(min(N - 1, round((i + 0.5) * N / n))) for i in range(n)]
