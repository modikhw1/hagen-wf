# -*- coding: utf-8 -*-
"""K8: kör ingest, fyra CM-meningar (ett per lager), mätning, felinjektion, manus och granskningsark.

    scen/.venv/Scripts/python.exe -X utf8 kor_k8.py urval            # de 20 i urval.json
    scen/.venv/Scripts/python.exe -X utf8 kor_k8.py holdout          # spår A:s hold-out, med fryst kod
    scen/.venv/Scripts/python.exe -X utf8 kor_k8.py klipp <sökväg.mp4>

Meningarna är fasta och skrivna före körningen (MENINGAR). Resultat: k8/resultat.jsonl (en rad per klipp och lager),
förhandsvisningar i forhands/<klipp>/, granskningsark i granskning/, manus i manus/.
"""
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))

from medielager import api, matning, operationer as op  # noqa: E402
from medielager.gemensamt import FORHANDS, ROT, abs_, ff, las, las_rutor, rel, skriv  # noqa: E402
from medielager.ingest import ingest  # noqa: E402
from medielager.manus import manus, manus_md  # noqa: E402

MENINGAR = [
    ("skarmtext", "byt texten till 'Testa vår nya meny i helgen'"),
    ("ljud", "ta bort musiken"),
    ("broll", "byt matbilden mot en annan av våra rätter"),
    ("montage", "korta montaget med 30 %"),
]
K8 = D / "k8"
GRANSK = D / "granskning"
MANUS = D / "manus"
FELINJ_PER_LAGER = 3


def granskningsark(tl, res, namn):
    """Före (övre rad) och efter (nedre rad) vid fyra tider i det ändrade området."""
    import cv2
    import numpy as np
    orig = abs_(tl["kalla"]["video"])
    ny = abs_(res["forhandsvisning"])
    a = res["andrat"]
    if a.get("tidsavbildning"):
        avb = [x for x in a["tidsavbildning"] if x[1] - x[0] > 0.2][:4]
        tn = [(x[0] + x[1]) / 2 for x in avb]
        to = [x[2] + (t - x[0]) for x, t in zip(avb, tn)]
    else:
        s0, s1 = a["tid"][0]
        s1 = min(s1, tl["kalla"]["langd"] - 0.05)
        tn = to = list(np.linspace(s0 + 0.15, max(s0 + 0.2, s1 - 0.15), 4))
    R0 = las_rutor(orig, to, bredd=180)
    R1 = las_rutor(ny, tn, bredd=180)
    rad = lambda R: np.hstack([r if r is not None else np.zeros((320, 180, 3), np.uint8) for r in R])
    h = min(r.shape[0] for r in R0 + R1 if r is not None)
    R0 = [r[:h] if r is not None else None for r in R0]
    R1 = [r[:h] if r is not None else None for r in R1]
    ark = np.vstack([rad(R0), np.full((6, 180 * len(R0), 3), 255, np.uint8), rad(R1)])
    p = GRANSK / f"{tl['klipp']}__{namn}.jpg"
    p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(p), ark, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return rel(p)


def felinjektion(tl, res):
    """Två trasiga varianter per utförd ändring: (a) ingen ändring alls, (b) ändring plus en ändring utanför lagret.
    Båda ska fällas av måttet (a: syns, b: kvar); annars är måttet blint."""
    orig = abs_(tl["kalla"]["video"])
    ny = abs_(res["forhandsvisning"])
    lager = res["lager"]
    ut = []
    a_fil = ny.with_name(ny.stem + "__fel_a.mp4")
    b_fil = ny.with_name(ny.stem + "__fel_b.mp4")
    if lager == "montage":
        ff("-i", orig, "-c", "copy", a_fil)   # samma längd som originalet
    else:
        ff("-i", orig, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "copy", a_fil)
    if lager == "ljud":
        # bilden ändras lite (ljusare) men musiken tas bort som vanligt
        ff("-i", ny, "-vf", "eq=brightness=0.06", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "copy", b_fil)
    elif lager == "montage":
        ff("-i", ny, "-vf", "eq=brightness=0.06", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "copy", b_fil)
    else:
        # en grå list över nedre femtedelen under hela klippet, utanför den ändrade lådan/tagningen
        H = tl["kalla"]["hojd"]
        ff("-i", ny, "-vf", f"drawbox=x=0:y={int(H*0.9)}:w=iw:h={int(H*0.06)}:color=gray@0.7:t=fill",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "copy", b_fil)
    for vad, fil, ska in (("a_ingen_andring", a_fil, "syns"), ("b_andring_utanfor", b_fil, "kvar")):
        try:
            if lager == "montage" and vad == "a_ingen_andring":
                r = dict(res, andrat=dict(res["andrat"], tidsavbildning=[[0, tl["kalla"]["langd"], 0, tl["kalla"]["langd"]]]))
            else:
                r = res
            b = matning.bedom(tl, r, ny_video=fil)
            ut.append(dict(variant=vad, ska_falla=ska, syns=b.get("syns"), kvar=b.get("kvar"),
                           larmade=(b.get(ska) is False), matt=b.get("matt")))
        except Exception as e:
            ut.append(dict(variant=vad, fel=repr(e)))
        fil.unlink(missing_ok=True)   # egna mellanfiler, återskapbara
    return ut


def kor_klipp(video, stratum, felinj_kvar, holdout=False):
    t0 = time.time()
    tl_fil = ingest(video)
    tl = las(tl_fil)
    ingest_s = round(time.time() - t0, 1)
    rader = []
    m0 = manus(tl)
    MANUS.mkdir(parents=True, exist_ok=True)
    (MANUS / f"{tl['klipp']}.md").write_text(manus_md(m0), encoding="utf-8")
    skriv(MANUS / f"{tl['klipp']}.json", m0)
    orig_ord = None
    for lager, mening in MENINGAR:
        t = time.time()
        rad = dict(klipp=tl["klipp"], stratum=stratum, holdout=holdout, lager=lager, mening=mening, ingest_s=ingest_s)
        try:
            param = {}
            if lager == "broll":
                param["kundmaterial"] = op.kundmaterial(tl)
                rad["kundmaterial_mattagningar"] = sum(1 for k in param["kundmaterial"] if k.get("klass") == "mat")
            res = api.utfor(tl, mening, **param)
            rad["op_s"] = round(time.time() - t, 1)
            if res["utfall"] == "utford" and lager in ("ljud", "montage") and orig_ord is None:
                orig_ord = matning.ord_ur(abs_(tl["kalla"]["video"]))
            b = matning.bedom(tl, res, orig_ord=orig_ord)
            rad.update(utfall=res["utfall"], skal=res["skal"], metoder=res["metoder"], generativt=res["generativt"],
                       forhandsvisning=res["forhandsvisning"], syns=b.get("syns"), kvar=b.get("kvar"), matt=b.get("matt"),
                       alternativ=res.get("alternativ"))
            if res["utfall"] == "utford":
                rad["granskning"] = granskningsark(tl, res, lager)
                skriv(FORHANDS / tl["klipp"] / f"{lager}.tidslinje.json", res["tidslinje"])
                mm = manus(res["tidslinje"])
                (MANUS / f"{tl['klipp']}__{lager}.md").write_text(manus_md(mm), encoding="utf-8")
                if felinj_kvar.get(lager, 0) > 0:
                    rad["felinjektion"] = felinjektion(tl, res)
                    felinj_kvar[lager] -= 1
        except Exception as e:
            rad.update(utfall="fel", skal=repr(e), spar=traceback.format_exc()[-1500:])
        rad["tot_s"] = round(time.time() - t, 1)
        rader.append(rad)
        print(f"  {lager:9s} {rad.get('utfall'):9s} syns={rad.get('syns')} kvar={rad.get('kvar')}  {rad.get('skal','')[:110]}", flush=True)
    return rader


def main():
    lage = sys.argv[1] if len(sys.argv) > 1 else "urval"
    U = json.loads((D / "urval.json").read_text(encoding="utf-8"))
    if lage == "urval":
        lista = [(u["video"], u["stratum"], False) for u in U["urval"]]
        ut = K8 / "resultat.jsonl"
    elif lage == "holdout":
        op.UNDANTAG.clear()
        lista = [(h["video"], h.get("stratum") or "?", True) for h in U["holdout"]]
        ut = K8 / "resultat_holdout.jsonl"
    else:
        lista = [(sys.argv[2], "?", False)]
        ut = K8 / "resultat_enstaka.jsonl"
    if lage != "holdout":
        op.UNDANTAG.update(h["klipp"] for h in U["holdout"])
    K8.mkdir(parents=True, exist_ok=True)
    klara = set()
    if ut.exists():
        klara = {json.loads(r)["klipp"] for r in ut.read_text(encoding="utf-8").splitlines() if r.strip()}
    felinj = {l: FELINJ_PER_LAGER for l, _ in MENINGAR}
    if ut.exists():
        for r in ut.read_text(encoding="utf-8").splitlines():
            r = json.loads(r)
            if r.get("felinjektion"):
                felinj[r["lager"]] -= 1
    for video, stratum, ho in lista:
        k = Path(video).stem
        if k in klara:
            continue
        print(k, stratum, flush=True)
        try:
            rader = kor_klipp(video, stratum, felinj, ho)
        except Exception as e:
            rader = [dict(klipp=k, stratum=stratum, holdout=ho, lager="ingest", utfall="fel", skal=repr(e),
                          spar=traceback.format_exc()[-1500:])]
            print("  ingest fel", repr(e)[:200], flush=True)
        with open(ut, "a", encoding="utf-8") as f:
            for r in rader:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
