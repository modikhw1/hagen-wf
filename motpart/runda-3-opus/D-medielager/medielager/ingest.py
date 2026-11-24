# -*- coding: utf-8 -*-
"""Ingest av medielager för ett klipp: tagningar, skärmtext, tal, musik, mat/person. Lokalt, allmänt.

    from medielager.ingest import ingest
    tidslinje_fil = ingest("data/format/kontroll/klipp/<id>.mp4")

Körs i scen/.venv. OCR och källseparation körs som delprocesser i D-medielager/_cache/venv.
Utdata: lager/<id>/tidslinje.json (schema medielager/1) och lager/<id>/rutor/ (en nyckelruta per tagning).
Råfiler som går att räkna om (OCR-rådata, ljudstammar) hamnar i _cache/.
"""
import json
import sys
import time
from pathlib import Path

from .gemensamt import CACHE, LAGER, SCHEMA, abs_, kor_egen, las, probe, rel, sha16, skriv


def _overlapp(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def _kort(klipp):
    """Befintliga etiketter ur banken (andra läsaren, Gemini), bara för jämförelse och manus. Ändras inte."""
    from .gemensamt import ROT
    ut = {}
    e4 = ROT / "data/format/e4/lager-gemini-3.1-flash-lite" / f"{klipp}.json"
    if e4.exists():
        e = las(e4)
        ut["e4"] = {k: e.get(k) for k in ("skarmtext", "musik", "trendljud", "montage", "klipp", "mat_andel", "tal",
                                          "personer", "tilltal", "dialog", "kamera")}
    kj = ROT / "byggsten/hand/ut/klipp.jsonl"
    if kj.exists():
        for rad in open(kj, encoding="utf-8"):
            if rad.startswith('{"id": "' + klipp + '"'):
                r = json.loads(rad)
                l2, l4 = r.get("l2") or {}, r.get("l4") or {}
                ut["l2"] = {k: l2.get(k) for k in ("typ", "montage", "text_tung", "personer_max", "innehall")}
                if l4:
                    ut["l4"] = dict(handling=l4.get("handling"), karna=l4.get("karna"),
                                    beats=[dict(vad=b.get("vad"), funktion=b.get("funktion"), bar=b.get("bar"))
                                           for b in l4.get("beats") or []],
                                    platser=l4.get("platser"), sprak=l4.get("sprak"))
                break
    return ut


def ingest(video, tvinga=False):
    from . import steg_bild, steg_ljud, steg_tagningar
    video = abs_(video)
    klipp = video.stem
    mapp = LAGER / klipp
    fil = mapp / "tidslinje.json"
    if fil.exists() and not tvinga:
        return fil
    tider = {}
    m = probe(video)

    t = time.time()
    tag_fil = CACHE / "tagningar" / f"{klipp}.json"
    if tag_fil.exists() and not tvinga and (mapp / "rutor").exists():
        tagningar, tag_s = las(tag_fil)
    else:
        tagningar, tag_s = steg_tagningar.tagningar(video, mapp)
        skriv(tag_fil, [tagningar, tag_s])
    tider["tagningar"] = round(time.time() - t, 1)
    granser = [x["fran"] for x in tagningar[1:]]

    t = time.time()
    ocr_fil = CACHE / "ocr" / f"{klipp}.json"
    if tvinga or not ocr_fil.exists():
        ocr_fil.parent.mkdir(parents=True, exist_ok=True)
        kor_egen("steg_text", video, ocr_fil, json.dumps(granser))
    ocr = las(ocr_fil)
    tider["skarmtext"] = round(time.time() - t, 1)

    t = time.time()
    stam_mapp = CACHE / "stammar" / klipp
    sep_fil = stam_mapp / "separation.json"
    if m["ljud"] and (tvinga or not sep_fil.exists()):
        kor_egen("steg_separation", video, stam_mapp)
    tider["separation"] = round(time.time() - t, 1)

    t = time.time()
    ljud = steg_ljud.ljud(video, sep_fil if sep_fil.exists() else None, m["langd"],
                          cache_fil=CACHE / "tal" / f"{klipp}.json") if m["ljud"] else \
        dict(tal=dict(segment=[], sekunder=0), musik=dict(finns=False, skal="klippet saknar ljudspår"))
    if ljud.get("musik", {}).get("stammar"):
        st = ljud["musik"]["stammar"]
        st["tal"] = rel(stam_mapp / st["tal"])
        st["musik"] = rel(stam_mapp / st["musik"])
    tider["tal_musik"] = round(time.time() - t, 1)

    t = time.time()
    steg_bild.klassa_tagningar(video, tagningar)
    tider["bild"] = round(time.time() - t, 1)

    text = ocr["skarmtext"]
    for tg in tagningar:
        tg["skarmtext"] = [x["id"] for x in text if _overlapp(tg["fran"], tg["till"], x["fran"], x["till"]) > 0.2]
        tg["tal"] = [i for i, s in enumerate(ljud["tal"]["segment"])
                     if _overlapp(tg["fran"], tg["till"], s["fran"], s["till"]) > 0.2]
    for x in text:
        x["tagningar"] = [tg["id"] for tg in tagningar if _overlapp(tg["fran"], tg["till"], x["fran"], x["till"]) > 0.2]

    klass = [tg.get("klass") for tg in tagningar]
    montage = dict(
        antal_tagningar=len(tagningar), median_langd=tag_s["median_langd"], klipp_per_10s=tag_s["klipp_per_10s"],
        ar_montage=bool(len(tagningar) >= 4 and tag_s["klipp_per_10s"] >= 1.5),
        b_roll_tagningar=[tg["id"] for tg in tagningar if tg.get("klass") in ("mat", "miljo", "text")],
        regel="montage = minst 4 tagningar och minst 1,5 klipp per 10 s (min tröskel, diagnos)",
        detektor=tag_s)
    fps = m["fps"] or 30
    tl = dict(
        schema=SCHEMA, klipp=klipp,
        kalla=dict(video=rel(video), sha1_4mb=sha16(video), **m),
        tidsbas="sekunder från klippets start; intervall [fran, till)",
        tagningar=tagningar, skarmtext=text, skarmtext_meta=ocr["meta"],
        tal=ljud["tal"], musik=ljud["musik"],
        mat=dict(tagningar_mat=[tg["id"] for tg, k in zip(tagningar, klass) if k == "mat"],
                 tagningar_person_med_mat=[tg["id"] for tg, k in zip(tagningar, klass) if k == "person_med_mat"],
                 andel_mat_s=round(sum(tg["langd"] for tg in tagningar if tg.get("klass") in ("mat", "person_med_mat"))
                                   / max(m["langd"], 1e-6), 3)),
        montage=montage,
        scenpaket2=dict(fps=fps, regel="ut = [round(fran*fps), round(till*fps)), samma tidsbas som scenpaket/2",
                        tagningar={tg["id"]: [round(tg["fran"] * fps), round(tg["till"] * fps)] for tg in tagningar}),
        andra_lasare=_kort(klipp),
        tider_s=tider, proveniens=dict(av="motpart/runda-3-opus/D-medielager/medielager/ingest.py",
                                      skapad=time.strftime("%Y-%m-%dT%H:%M:%S")))
    skriv(fil, tl)
    return fil


if __name__ == "__main__":
    for v in [a for a in sys.argv[1:] if not a.startswith("--")]:
        t = time.time()
        f = ingest(v, tvinga="--tvinga" in sys.argv)
        print(f, round(time.time() - t, 1), "s", flush=True)
