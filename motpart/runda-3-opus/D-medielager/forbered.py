# -*- coding: utf-8 -*-
"""Förbered ingest i delsteg som kan köras parallellt (alla cachas i _cache/, återskapbara).

    scen/.venv/Scripts/python.exe -X utf8 forbered.py <steg> [urval|holdout]
    steg: tagningar | ocr | sep | tal

ocr och sep körs som delprocesser i _cache/venv. tal (whisper + vad) och tagningar körs i scen/.venv.
kor_k8.py använder cacharna och kör resten (bild, mätning, operationer).
"""
import json
import sys
import time
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))

from medielager.gemensamt import CACHE, LAGER, abs_, kor_egen, las, skriv  # noqa: E402


def lista(lage):
    U = json.loads((D / "urval.json").read_text(encoding="utf-8"))
    return [abs_(u["video"]) for u in (U["holdout"] if lage == "holdout" else U["urval"])]


def main():
    steg = sys.argv[1]
    lage = sys.argv[2] if len(sys.argv) > 2 else "urval"
    for v in lista(lage):
        k = v.stem
        t = time.time()
        if steg == "tagningar":
            from medielager import steg_tagningar
            f = CACHE / "tagningar" / f"{k}.json"
            if not f.exists():
                skriv(f, list(steg_tagningar.tagningar(v, LAGER / k)))
        elif steg == "ocr":
            f = CACHE / "ocr" / f"{k}.json"
            tf = CACHE / "tagningar" / f"{k}.json"
            if not f.exists():
                granser = [x["fran"] for x in las(tf)[0][1:]] if tf.exists() else []
                f.parent.mkdir(parents=True, exist_ok=True)
                kor_egen("steg_text", v, f, json.dumps(granser))
        elif steg == "sep":
            f = CACHE / "stammar" / k / "separation.json"
            if not f.exists():
                kor_egen("steg_separation", v, f.parent)
        elif steg == "tal":
            from medielager.steg_ljud import tal_lasning
            tal_lasning(v, CACHE / "tal" / f"{k}.json")
        print(steg, k, round(time.time() - t, 1), "s", flush=True)


if __name__ == "__main__":
    main()
