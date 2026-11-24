# -*- coding: utf-8 -*-
"""Skärmtext: text, position, tid och stil. Körs i D-medielager/.venv (RapidOCR 3.10, PP-OCRv6 small, lokalt).

Gång:
1. OCR på en ruta per SAMPEL_S sekunder (540 px bred).
2. Rader som ligger tätt i höjdled slås ihop till block (flerradig text).
3. Block följs över sampel: lika text (difflib >= 0.72) och överlapp i bild, eller samma
   text på nytt ställe. Ett spår = ett skärmtextobjekt.
4. Start och slut förfinas på 10 rutor/s med normerad korskorrelation mot blockets
   utsnitt (kanter), så att tiden inte låses till samplet.
5. Typ: "overlag" om lådan står still i bild (medelavvikelse < 1,5 % av bilden) över minst
   två sampel eller över en hård gräns; "scen" om lådan rör sig; annars "osaker".
6. Stil: Otsu i lådan delar glyfer och bakgrund; den mindre klassen räknas som glyfer.
   Platta = bakgrunden jämn (std < 20) och skiljer sig från ringen utanför lådan.

Alla trösklar är mina och är diagnos.
Kör: python -m medielager.steg_text <video> <ut.json> [tagningsgranser_json]
"""
import difflib
import json
import sys
from pathlib import Path

import cv2
import numpy as np

SAMPEL_S = 1.0
BREDD = 540
FORFINA_FPS = 10.0


def _ocr_motor():
    import logging
    from rapidocr import RapidOCR
    logging.getLogger("RapidOCR").setLevel(logging.ERROR)
    return RapidOCR()


def _rutor(video, tider, bredd=BREDD):
    cap = cv2.VideoCapture(str(video))
    for t in tider:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if not ok:
            yield t, None
            continue
        h, w = f.shape[:2]
        yield t, cv2.resize(f, (bredd, int(round(bredd * h / w))), interpolation=cv2.INTER_AREA)
    cap.release()


def _block(rader, H):
    """Slå ihop rader till block. rader: (text, [x0,y0,x1,y1] px, score)."""
    rader = sorted(rader, key=lambda r: r[1][1])
    block = []
    for txt, b, s in rader:
        h = b[3] - b[1]
        for bl in block:
            bb = bl["box"]
            lh = bl["radhojd"]
            gap = b[1] - bb[3]
            nara_y = -0.45 * min(h, lh) <= gap < 0.9 * max(h, lh)
            overlapp_x = min(b[2], bb[2]) - max(b[0], bb[0]) > 0.3 * min(b[2] - b[0], bb[2] - bb[0])
            likhojd = 0.5 < h / max(lh, 1) < 2.0
            if nara_y and overlapp_x and likhojd:
                bl["rader"].append(txt)
                bl["box"] = [min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3])]
                bl["score"] = min(bl["score"], s)
                bl["radhojd"] = max(lh, h)
                break
        else:
            block.append(dict(rader=[txt], box=list(b), score=s, radhojd=h, rad0=(txt, list(b))))
    return block


def _iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0.0


def _lika(a, b):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _stil(img, box):
    """Färg på glyfer och bakgrund, platta, storlek. img = BGR i analysupplösning, box i px."""
    H, W = img.shape[:2]
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    crop = img[y0:y1, x0:x1]
    if crop.size == 0:
        return {}
    g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    vit, svart = g > 200, g < 55
    fv, fs = float(vit.mean()), float(svart.mean())
    kontur = None
    if fv > 0.6 and fs > 0.03:
        glyf = svart                      # mörk text på ljus platta
    elif fs > 0.6 and fv > 0.03:
        glyf = vit                        # ljus text på mörk platta
    elif fv >= 0.06:
        glyf = vit                        # ljus text över bild
        kontur = "#000000" if fs >= 0.04 else None
    elif fs >= 0.06:
        glyf = svart
        kontur = "#ffffff" if fv >= 0.04 else None
    else:
        _, m = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        ljus = m > 0
        glyf = ljus if ljus.mean() < 0.5 else ~ljus
    def hexf(px):
        if px.size == 0:
            return None
        c = np.median(px.reshape(-1, 3), axis=0)
        return "#%02x%02x%02x" % (int(c[2]), int(c[1]), int(c[0]))
    bak = crop[~glyf]
    bak_std = float(np.std(cv2.cvtColor(bak.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY))) if bak.size else 999.0
    # Ring utanför lådan
    p = max(3, int(0.15 * (y1 - y0)))
    rx0, ry0, rx1, ry1 = max(0, x0 - p), max(0, y0 - p), min(W, x1 + p), min(H, y1 + p)
    ring = img[ry0:ry1, rx0:rx1].copy().astype(np.float32)
    mask = np.ones(ring.shape[:2], bool)
    mask[y0 - ry0:y1 - ry0, x0 - rx0:x1 - rx0] = False
    ring_med = np.median(ring[mask], axis=0) if mask.any() else None
    bak_med = np.median(bak.reshape(-1, 3), axis=0) if bak.size else None
    platta = bool(bak_std < 28 and bak_med is not None and ring_med is not None
                  and float(np.abs(bak_med - ring_med).mean()) < 25)
    gl_g = float(np.median(g[glyf])) if glyf.any() else 0.0
    return dict(glyffarg=hexf(crop[glyf]), kontur=kontur, bakgrund=hexf(bak), platta=platta,
                bakgrund_std=round(bak_std, 1), ljus_text=bool(gl_g > 127),
                andel_vit=round(fv, 3), andel_svart=round(fs, 3))


def _forfina(video, item, motor, langd):
    """Förfina start och slut på 10 rutor/s: igenkänning (utan detektion) på blockets första rad.

    Raden räknas som kvar om den lästa texten liknar spårets text (difflib >= 0.7).
    Steget går högst ett sampel bakåt och framåt.
    """
    fr, ti = item["_t"][0], item["_t"][-1]
    rtxt, rb = item["_rad0"]
    def kvar(f):
        H, W = f.shape[:2]
        p = 0.25 * (rb[3] - rb[1])
        x0, y0 = int(max(0, rb[0] - p)), int(max(0, rb[1] - p))
        x1, y1 = int(min(W, rb[2] + p)), int(min(H, rb[3] + p))
        c = f[y0:y1, x0:x1]
        if c.size == 0:
            return False
        r = motor(c, use_det=False, use_cls=False, use_rec=True)
        if not r.txts:
            return False
        return _lika(r.txts[0], rtxt) >= 0.7 and float(r.scores[0]) >= 0.5
    steg = 1.0 / FORFINA_FPS
    start = fr
    bak = list(np.arange(fr - steg, max(-1e-6, fr - SAMPEL_S + steg / 2), -steg))
    for t, f in _rutor(video, bak):
        if f is None or not kvar(f):
            break
        start = t
    slut = ti + steg
    fram = list(np.arange(ti + steg, min(langd, ti + SAMPEL_S - steg / 2), steg))
    for t, f in _rutor(video, fram):
        if f is None or not kvar(f):
            break
        slut = t + steg
    return max(0.0, float(start)), min(langd, float(slut))


def skarmtext(video, granser=()):
    cap = cv2.VideoCapture(str(video))
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.release()
    langd = float(n / fps)
    motor = _ocr_motor()
    tider = list(np.arange(0.25, max(0.3, langd - 0.05), SAMPEL_S))
    spar = []
    H = W = None
    from .gemensamt import las_rutor
    for t, f in zip(tider, las_rutor(video, tider, bredd=BREDD)):
        if f is None:
            continue
        H, W = f.shape[:2]
        r = motor(f)
        rader = []
        if r.boxes is not None:
            for b, txt, s in zip(r.boxes, r.txts, r.scores):
                if s < 0.6 or len(txt.strip()) < 2:
                    continue
                xs, ys = [p[0] for p in b], [p[1] for p in b]
                rader.append((txt.strip(), [min(xs), min(ys), max(xs), max(ys)], float(s)))
        for bl in _block(rader, H):
            txt = "\n".join(bl["rader"])
            bx = bl["box"]
            # Matcha mot öppna spår
            bast, bv = None, 0.0
            for sp in spar:
                if t - sp["_t"][-1] > SAMPEL_S * 1.6:
                    continue
                v = _lika(txt, sp["_texter"][-1])
                o = _iou(bx, sp["_boxar"][-1])
                if (v >= 0.72 and o > 0.15) or v >= 0.9:
                    poang = v + o
                    if poang > bv:
                        bast, bv = sp, poang
            if bast is None:
                bast = dict(_t=[], _texter=[], _boxar=[], _score=[], _boxpx=bx, _stil=_stil(f, bx), _rad0=bl["rad0"])
                spar.append(bast)
            else:
                bast["_rad_sist"] = bl["rad0"]
            bast["_t"].append(float(t))
            bast["_texter"].append(txt)
            bast["_boxar"].append(bx)
            bast["_score"].append(bl["score"])
    ut = []
    for i, sp in enumerate(sorted(spar, key=lambda s: s["_t"][0]), 1):
        boxar = np.array(sp["_boxar"], float)
        mitt = np.c_[(boxar[:, 0] + boxar[:, 2]) / 2 / W, (boxar[:, 1] + boxar[:, 3]) / 2 / H]
        avvik = float(np.mean(np.linalg.norm(mitt - mitt.mean(0), axis=1))) if len(mitt) > 1 else None
        fran, till = _forfina(video, sp, motor, langd)
        over_grans = any(fran + 0.1 < g < till - 0.1 for g in granser)
        if avvik is not None and avvik < 0.015 and (len(mitt) >= 2):
            typ = "overlag"
        elif over_grans and (avvik is None or avvik < 0.03):
            typ = "overlag"
        elif avvik is not None and avvik >= 0.03:
            typ = "scen"
        else:
            typ = "osaker"
        # vanligaste texten, viktad med score
        vikter = {}
        for tx, s in zip(sp["_texter"], sp["_score"]):
            vikter[tx] = vikter.get(tx, 0) + s
        text = max(vikter, key=vikter.get)
        b = boxar.mean(0)
        nb = [round(b[0] / W, 4), round(b[1] / H, 4), round(b[2] / W, 4), round(b[3] / H, 4)]
        cy = (nb[1] + nb[3]) / 2
        cx = (nb[0] + nb[2]) / 2
        rader = text.count("\n") + 1
        stil = dict(sp["_stil"])
        stil.update(radhojd_rel=round((nb[3] - nb[1]) / rader, 4),
                    position="ovre" if cy < 0.33 else ("nedre" if cy > 0.66 else "mitt"),
                    justering="center" if abs(cx - 0.5) < 0.08 else ("vanster" if cx < 0.5 else "hoger"),
                    versaler=bool(text.upper() == text and any(c.isalpha() for c in text)))
        ut.append(dict(id=f"x{i}", text=text, fran=round(fran, 2), till=round(till, 2), box=nb, typ=typ,
                       sakerhet=round(float(np.mean(sp["_score"])), 3), sampel=len(sp["_t"]),
                       rorelse_i_bild=None if avvik is None else round(avvik, 4), over_grans=over_grans,
                       varianter=sorted(set(sp["_texter"]))[:4], stil=stil))
    # Textremsa: minst tre objekt på samma höjd (mitt +-1,5 % av bilden), centrerade, i följd.
    # Ett enstaka "osaker" som ingår i en remsa räknas som överlägg (textning eller etiketter).
    remsor = []
    for x in ut:
        cy = (x["box"][1] + x["box"][3]) / 2
        if x["stil"]["justering"] != "center":
            continue
        for r in remsor:
            if abs(r["cy"] - cy) < 0.015:
                r["ids"].append(x["id"])
                break
        else:
            remsor.append(dict(cy=cy, ids=[x["id"]]))
    for k, r in enumerate([r for r in remsor if len(r["ids"]) >= 3], 1):
        for x in ut:
            if x["id"] in r["ids"]:
                x["remsa"] = f"r{k}"
                if x["typ"] == "osaker":
                    x["typ"] = "overlag"
                    x["typ_skal"] = "ingår i textremsa"
    return ut, dict(motor="RapidOCR 3.10 (PP-OCRv6 det/rec small, onnxruntime, CPU)", sampel_s=SAMPEL_S,
                    analysbredd=BREDD, forfining_fps=FORFINA_FPS, langd=round(langd, 3))


if __name__ == "__main__":
    video, ut = sys.argv[1], sys.argv[2]
    granser = json.loads(sys.argv[3]) if len(sys.argv) > 3 else []
    items, meta = skarmtext(video, granser)
    Path(ut).write_text(json.dumps(dict(skarmtext=items, meta=meta), ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(items), "objekt")
