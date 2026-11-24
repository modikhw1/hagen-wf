# -*- coding: utf-8 -*-
"""Mätning för K8: gick ändringen att utföra, syns (hörs) den, och är resten kvar?

Allt här är mina mått och därmed diagnos, inte ägarens krav. Varje mått har en felinjektion
(kor_k8.py) som visar att det kan larma.

Mått per lager:
  skarmtext  syns: ny text läses i den ritade lådan (difflib >= 0.6) och den gamla läses inte i sin låda (< 0.5)
             kvar: PSNR utanför den ändrade lådan och tiden >= PSNR_MIN; ljudet bitidentiskt (avkodat md5)
  ljud       syns: energin utanför tal (silero-vad på originalet) sjunker >= 10 dB
             kvar: bilden bitidentisk (avkodat md5); talet: ordåterkallelse >= 0.8 mot originalets transkript
  mat        syns: rutorna i den bytta tagningen skiljer sig från originalet (medelabsolutdiff >= 12)
             kvar: PSNR utanför tagningen >= PSNR_MIN; ljudet bitidentiskt; text ovanpå läses igen (>= 0.6)
  montage    syns: längden <= 85 % av originalet
             kvar: behållna tagningar PSNR >= PSNR_MIN mot originalets motsvarande rutor; ordåterkallelse >= 0.8
"""
import difflib
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

from .gemensamt import ROT, abs_, kor_egen, las_rutor

PSNR_MIN = 32.0
PROV_FPS = 4.0


def psnr(a, b, mask=None):
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    d = (a - b) ** 2
    if mask is not None:
        if not mask.any():
            return None
        d = d[mask]
    mse = float(d.mean())
    return 99.0 if mse < 1e-6 else round(10 * np.log10(255 ** 2 / mse), 2)


def md5_strom(video, strom):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-map", f"0:{strom}", "-f", "md5", "-"],
                       capture_output=True, text=True)
    return r.stdout.strip() or None


def _pcm16k(video):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                       capture_output=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0


def energi_utanfor_tal(video, tal_seg, langd):
    x = _pcm16k(video)
    if x.size == 0:
        return None
    m = np.ones(len(x), bool)
    for s in tal_seg:
        m[int(max(0, s["fran"] - 0.15) * 16000):int((s["till"] + 0.15) * 16000)] = False
    if m.sum() < 16000 * 0.5:
        return None
    return round(float(10 * np.log10(np.mean(x[m] ** 2) + 1e-12)), 2)


_wm = {}


def ord_ur(video):
    from .steg_ljud import _whisper
    x = _pcm16k(video)
    seg, _ = _whisper().transcribe(x, beam_size=1, vad_filter=True, condition_on_previous_text=False)
    return " ".join(s.text for s in seg).lower().split()


def _norm_ord(w):
    return [t.strip(".,!?:;\"'()") for t in w if t.strip(".,!?:;\"'()")]


def aterkallelse(orig_ord, nya_ord):
    a, b = _norm_ord(orig_ord), _norm_ord(nya_ord)
    if not a:
        return None
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return round(sum(bl.size for bl in sm.get_matching_blocks()) / len(a), 3)


def las_text(fragor):
    """fragor: [{"video","t","box"}] → samma med "text". Körs i egna venv:en."""
    with tempfile.TemporaryDirectory() as td:
        inn, ut = Path(td) / "in.json", Path(td) / "ut.json"
        inn.write_text(json.dumps([dict(f, video=str(abs_(f["video"]))) for f in fragor], ensure_ascii=False), encoding="utf-8")
        kor_egen("steg_lasruta", inn, ut)
        return json.loads(ut.read_text(encoding="utf-8"))


def lik(a, b):
    a = " ".join(a.lower().split())
    b = " ".join(b.lower().split())
    return round(difflib.SequenceMatcher(None, a, b).ratio(), 3)


def _tider(langd):
    return [round(t, 3) for t in np.arange(0.1, langd - 0.05, 1 / PROV_FPS)]


def _mask_px(W, H, boxar_px, pad=6):
    m = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in boxar_px:
        m[max(0, y0 - pad):min(H, y1 + pad), max(0, x0 - pad):min(W, x1 + pad)] = True
    return m


def bedom(tl, res, ny_video=None, orig_ord=None):
    """Bedöm ett Resultat från operationer.py. ny_video kan peka på en felinjicerad fil i stället."""
    out = dict(utfall=res["utfall"], lager=res["lager"], skal=res["skal"])
    if res["utfall"] != "utford":
        return out
    orig = abs_(tl["kalla"]["video"])
    ny = abs_(ny_video or res["forhandsvisning"])
    W, H, L = tl["kalla"]["bredd"], tl["kalla"]["hojd"], tl["kalla"]["langd"]
    a = res["andrat"]
    lager = res["lager"]
    matt = {}
    if lager == "skarmtext":
        from .operationer import _box_px
        boxar = [_box_px(b, W, H) for b in a["box"]] + list(a.get("ritad_px") or [])
        mask = _mask_px(W, H, boxar)
        a0 = min(t[0] for t in a["tid"]) - 0.1
        a1 = max(t[1] for t in a["tid"]) + 0.1
        tider = _tider(L)
        R0, R1 = las_rutor(orig, tider), las_rutor(ny, tider)
        ut_ps, in_diff = [], []
        for t, f0, f1 in zip(tider, R0, R1):
            if f0 is None or f1 is None:
                continue
            if a0 <= t <= a1:
                ut_ps.append(psnr(f0, f1, ~mask))
                in_diff.append(float(np.abs(f0[mask].astype(float) - f1[mask].astype(float)).mean()))
            else:
                ut_ps.append(psnr(f0, f1))
        matt["psnr_utanfor_min"] = min(p for p in ut_ps if p is not None) if ut_ps else None
        matt["diff_i_lada_medel"] = round(float(np.mean(in_diff)), 2) if in_diff else None
        matt["ljud_identiskt"] = md5_strom(orig, "a") == md5_strom(ny, "a") if tl["kalla"].get("ljud") else None
        tm = (a["tid"][0][0] + a["tid"][0][1]) / 2
        ny_text = (res.get("tidslinje") or {}).get("andring", {}).get("parametrar", {}).get("ny_text")
        gammal = next((x.get("text_original") or x["text"] for x in tl["skarmtext"] if x["box"] == a["box"][0]), None)
        fr = []
        if ny_text and a.get("ritad_px"):
            x0, y0, x1, y1 = a["ritad_px"][0]
            fr.append(dict(video=str(ny), t=tm, box=[x0 / W, y0 / H, x1 / W, y1 / H], vad="ny"))
        fr.append(dict(video=str(ny), t=tm, box=a["box"][0], vad="gammal_i_ny"))
        lasta = las_text(fr)
        for f in lasta:
            if f["vad"] == "ny":
                matt["ny_text_last"] = f["text"]
                matt["ny_text_lik"] = lik(f["text"], ny_text)
            else:
                matt["gammal_text_last"] = f["text"]
                matt["gammal_text_lik"] = lik(f["text"], gammal or "") if gammal else None
        syns = (matt.get("ny_text_lik", 1.0) >= 0.6 if ny_text else True) and (matt.get("gammal_text_lik") or 0) < 0.5
        kvar = (matt["psnr_utanfor_min"] or 0) >= PSNR_MIN and matt["ljud_identiskt"] is not False
    elif lager == "ljud":
        matt["bild_identisk"] = md5_strom(orig, "v") == md5_strom(ny, "v")
        seg = tl["tal"].get("vad", {}).get("segment") or tl["tal"].get("segment") or []
        e0, e1 = energi_utanfor_tal(orig, seg, L), energi_utanfor_tal(ny, seg, L)
        matt["energi_utanfor_tal_db"] = [e0, e1]
        matt["sankning_db"] = None if e0 is None or e1 is None else round(e0 - e1, 2)
        if orig_ord is None:
            orig_ord = ord_ur(orig)
        matt["ord_original"] = len(orig_ord)
        matt["ord_aterkallelse"] = aterkallelse(orig_ord, ord_ur(ny)) if orig_ord else None
        syns = matt["sankning_db"] is not None and matt["sankning_db"] >= 10
        kvar = matt["bild_identisk"] and (matt["ord_aterkallelse"] is None or matt["ord_aterkallelse"] >= 0.8)
    elif lager == "mat":
        s0, s1 = a["tid"][0]
        tider = _tider(L)
        R0, R1 = las_rutor(orig, tider), las_rutor(ny, tider)
        ut_ps, in_diff = [], []
        for t, f0, f1 in zip(tider, R0, R1):
            if f0 is None or f1 is None:
                continue
            if s0 - 0.08 <= t <= s1 + 0.08:
                if s0 + 0.1 <= t <= s1 - 0.1:
                    in_diff.append(float(np.abs(f0.astype(float) - f1.astype(float)).mean()))
            else:
                ut_ps.append(psnr(f0, f1))
        matt["psnr_utanfor_min"] = min(ut_ps) if ut_ps else None
        matt["diff_i_tagning_medel"] = round(float(np.mean(in_diff)), 2) if in_diff else None
        matt["ljud_identiskt"] = md5_strom(orig, "a") == md5_strom(ny, "a") if tl["kalla"].get("ljud") else None
        ovan = [x for x in tl["skarmtext"] if x.get("typ") == "overlag" and min(s1, x["till"]) - max(s0, x["fran"]) > 0.3]
        if ovan:
            fr = [dict(video=str(ny), t=(max(s0, x["fran"]) + min(s1, x["till"])) / 2, box=x["box"], text=x["text"]) for x in ovan]
            lasta = las_text(fr)
            matt["text_ovanpa_lik"] = [lik(f["text"], f["text"] if False else x["text"]) for f, x in zip(lasta, ovan)]
        syns = (matt["diff_i_tagning_medel"] or 0) >= 12
        kvar = (matt["psnr_utanfor_min"] or 0) >= PSNR_MIN and matt["ljud_identiskt"] is not False and \
            all(v >= 0.6 for v in matt.get("text_ovanpa_lik", []))
    elif lager == "montage":
        from .gemensamt import probe
        nl = probe(ny)["langd"]
        matt["langd"] = [round(L, 2), round(nl, 2)]
        ps = []
        for na, nb, oa, ob in a["tidsavbildning"]:
            if nb - na < 0.3:
                continue
            tn = list(np.linspace(na + 0.1, nb - 0.1, 3))
            to = [oa + (t - na) for t in tn]
            for f0, f1 in zip(las_rutor(orig, to), las_rutor(ny, tn)):
                if f0 is not None and f1 is not None:
                    ps.append(psnr(f0, f1))
        matt["psnr_behallna_min"] = min(ps) if ps else None
        if orig_ord is None:
            orig_ord = ord_ur(orig)
        matt["ord_original"] = len(orig_ord)
        matt["ord_aterkallelse"] = aterkallelse(orig_ord, ord_ur(ny)) if orig_ord else None
        syns = nl <= 0.85 * L
        kvar = (matt["psnr_behallna_min"] or 0) >= PSNR_MIN and (matt["ord_aterkallelse"] is None or matt["ord_aterkallelse"] >= 0.8)
    else:
        syns = kvar = None
    out.update(syns=bool(syns), kvar=bool(kvar), matt=matt)
    return out
