# -*- coding: utf-8 -*-
"""Fryst hold-out för runda 3 (spår A). Körs EN gång; resultatet skrivs till
motpart/runda-3-opus/HOLDOUT.md av människa/agent efter granskning av utskriften.

Regel (förregistrerad i denna fil före dragningen):
  pool      = alla .mp4 i data/format/kontroll/klipp/ (råvideo ur banken, riktiga 9:16-klipp)
  behörig   = stående (h > b), 5-90 s, och biblioteksläsningen i
              byggsten/hand/ut/fingrar.jsonl säger rum >= 0.5 och
              (ansikte >= 0.5 eller samspel >= 0.5)   [befintlig data, ej min bedömning]
  utesluten = klipp-id (hela stammen ELLER det numeriska id:t) förekommer i någon
              textfil under forvarld_karna/, byggsten/ (utom byggsten/hand/ut/, som är
              bibliotekslistor över alla 1 480 kort), scen/, motpart/ (alla rundor och spår),
              karta/, delegat/
  dragning  = random.Random(FRO).sample(sorted(behöriga), K)
"""
import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

FRO = 20261119  # dagens datum som heltal, valt före dragningen
K = 4
ROT = Path(__file__).resolve().parents[3]
POOL = ROT / "data" / "format" / "kontroll" / "klipp"
SOK = ["forvarld_karna", "byggsten", "scen", "motpart", "karta", "delegat"]
UNDANTAG = [ROT / "byggsten" / "hand" / "ut"]
EXT = {".py", ".md", ".json", ".jsonl", ".txt", ".js", ".ts", ".html", ".csv", ".yaml", ".yml", ".toml", ".log"}
MAX_BYTE = 8_000_000


def korpus():
    delar, n = [], 0
    for d in SOK:
        for rot, kat, filer in os.walk(ROT / d):
            p = Path(rot)
            if any(str(p).startswith(str(u)) for u in UNDANTAG):
                kat[:] = []
                continue
            kat[:] = [k for k in kat if k not in {".venv", "node_modules", "__pycache__", ".git"}]
            for f in filer:
                fp = p / f
                if fp.suffix.lower() not in EXT:
                    continue
                try:
                    if fp.stat().st_size > MAX_BYTE:
                        continue
                    delar.append(fp.read_text(encoding="utf-8", errors="ignore"))
                    n += 1
                except OSError:
                    pass
    return "\n".join(delar), n


def prob(fp):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", str(fp)],
                       capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    s = (j.get("streams") or [{}])[0]
    return s.get("width", 0), s.get("height", 0), float((j.get("format") or {}).get("duration", 0) or 0)


def main():
    fing = {}
    with open(ROT / "byggsten" / "hand" / "ut" / "fingrar.jsonl", encoding="utf-8") as fh:
        for rad in fh:
            j = json.loads(rad)
            fing[j["id"]] = j["f"]
    text, nfiler = korpus()
    print(f"sökte i {nfiler} textfiler")
    beh, logg = [], []
    for fp in sorted(POOL.glob("*.mp4")):
        kid = fp.stem
        num = kid.rsplit("-", 1)[-1]
        if kid in text or num in text:
            logg.append((kid, "nämnt"))
            continue
        f = fing.get(kid)
        if not f:
            logg.append((kid, "ingen biblioteksläsning"))
            continue
        rum, ans, sam = f.get("rum"), f.get("ansikte"), f.get("samspel")
        if rum is None or rum < 0.5 or not ((ans or 0) >= 0.5 or (sam or 0) >= 0.5):
            logg.append((kid, f"ej behörig rum={rum} ansikte={ans} samspel={sam}"))
            continue
        w, h, dur = prob(fp)
        if not (h > w and 5 <= dur <= 90):
            logg.append((kid, f"format {w}x{h} {dur:.1f}s"))
            continue
        beh.append(kid)
    print(f"pool={len(list(POOL.glob('*.mp4')))} behöriga={len(beh)}")
    for k, s in logg:
        print("  ut:", k, s)
    val = random.Random(FRO).sample(beh, K)
    lista = "\n".join(val) + "\n"
    print("BEHÖRIGA:", json.dumps(beh))
    print("VAL:", json.dumps(val))
    print("SHA256(lista):", hashlib.sha256(lista.encode("utf-8")).hexdigest())
    for k in val:
        fp = POOL / f"{k}.mp4"
        print(k, hashlib.sha256(fp.read_bytes()).hexdigest(), prob(fp))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
