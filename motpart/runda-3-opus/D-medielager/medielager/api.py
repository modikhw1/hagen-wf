# -*- coding: utf-8 -*-
"""Ingång för spår C (routern) och för CM: en mening om ett medielager → operation → Resultat.

    from medielager.api import utfor
    r = utfor("data/format/kontroll/klipp/<id>.mp4", "byt texten till 'Prova vår nya pizza'",
              lager="skarmtext", typ="byter")

- `kalla`: en videosökväg (ingest körs om tidslinjen saknas, minuter) eller en tidslinje (dict eller sökväg till json).
- `lager` och `typ` är routerns fält ur `C-cm-mening/router.py` (`r_medie`): lager i {skarmtext, ljud, repliker,
  broll, montage, manus}, typ i {tar_bort, lagger_till, byter}. Saknas de läses de ur meningen med samma slags regler.
- `param` går direkt till operationen (t.ex. kalla=<ljudfil> för byt_musik, mal="x3" för byt_text).
Utfall och fält: se operationer.py. Tolkningen av meningen här är regler, ingen modell.
"""
import re
from pathlib import Path

from . import operationer as op
from .gemensamt import las

CITAT = r"[\"'“”‘’«»]([^\"'“”‘’«»]+)[\"'“”‘’«»]"


def _tidslinje(kalla):
    if isinstance(kalla, dict):
        return kalla
    p = Path(kalla)
    if p.suffix == ".json":
        return las(p)
    from .ingest import ingest
    return las(ingest(p))


def _lager_ur_mening(n):
    if re.search(r"\b(text\w*|undertext\w*|textrad\w*|rubrik\w*|textning)\b", n):
        return "skarmtext"
    if re.search(r"\b(musik\w*|låten|sången|ljudet|ljud)\b", n):
        return "ljud"
    if re.search(r"\b(matbild\w*|mat\w*|rätt\w*|bild\w* på|b-roll|närbild\w*)\b", n):
        return "broll"
    if re.search(r"\b(montage\w*|klipp\w*|tagning\w*)\b", n):
        return "montage"
    if re.search(r"\breplik\w*\b|\bsäga\b|\bsäger\b", n):
        return "repliker"
    return None


def _typ_ur_mening(n):
    if re.search(r"\b(ta bort|stryk|plocka bort|utan|tysta|stäng av)\b", n):
        return "tar_bort"
    if re.search(r"\b(lägg (på|in|till)|skriv|infoga)\b", n):
        return "lagger_till"
    return "byter"


def utfor(kalla, mening, lager=None, typ=None, **param):
    n = mening.lower().strip()
    lager = lager or _lager_ur_mening(n)
    typ = typ or _typ_ur_mening(n)
    citat = re.findall(CITAT, mening)
    tl = _tidslinje(kalla)
    if lager == "skarmtext":
        if typ == "tar_bort":
            return op.ta_bort_text(tl, mal=param.get("mal") or (citat[0] if citat else None))
        if typ == "lagger_till":
            text = param.get("text") or (citat[-1] if citat else None)
            if not text:
                return op._resultat("motfraga", "Vad ska det stå?", "skarmtext")
            pos = "ovre" if re.search(r"överst|uppe|toppen", n) else ("nedre" if re.search(r"nederst|nere|botten", n) else "mitt")
            return op.lagg_till_text(tl, text, fran=param.get("fran", 0.0), till=param.get("till"), position=pos)
        ny = param.get("ny_text") or (citat[-1] if citat else None)
        if not ny:
            m = re.search(r"\btill\b\s+(.+)$", mening)
            ny = m.group(1).strip() if m else None
        if not ny:
            return op._resultat("motfraga", "Vad ska den nya texten vara?", "skarmtext")
        mal = param.get("mal") or (citat[0] if len(citat) >= 2 else None)
        return op.byt_text(tl, ny, mal=mal)
    if lager == "ljud":
        if typ == "tar_bort" and re.search(r"musik|låt|sång|bakgrund", n):
            return op.ta_bort_musik(tl)
        if re.search(r"musik|låt", n):
            return op.byt_musik(tl, param.get("kalla"))
        return op._resultat("motfraga", "Gäller det musiken eller talet? Talet byts i manuset; ny röst genereras inte.",
                            "ljud", alternativ=["ta bort musiken", "byt musiken (bifoga fil)", "ändra repliken i manuset"])
    if lager == "broll":
        mot = param.get("mot")
        if not mot:
            m = re.search(r"\b(mot|till|med)\s+(en |ett |vår |våra |er |era )?([\wåäöé\- ]+?)(\s+i stället|\s+istället)?$", n)
            mot = m.group(3).strip() if m else None
            if mot and re.fullmatch(r"(en )?annan( matbild| bild| rätt)?|något annat", mot):
                mot = None
        return op.byt_matbild(tl, mot=mot, kundmaterial_lista=param.get("kundmaterial"))
    if lager == "montage":
        m = re.search(r"till\s+(\d+(?:[.,]\d+)?)\s*s", n)
        p = re.search(r"(\d+)\s*(%|procent)", n)
        mal_s = float(m.group(1).replace(",", ".")) if m else param.get("mal_s")
        andel = float(p.group(1)) / 100 if p else param.get("andel", 0.3)
        return op.korta_montage(tl, andel=andel, mal_s=mal_s)
    if lager == "repliker":
        return op._resultat("nej", "Repliker byts i manuset, som kunden spelar in efter. Förhandsvisningen behåller "
                                   "originalets röst: en ny röst vore generativ (K7).", "repliker")
    if lager == "manus":
        return op._resultat("nej", "Kläder och spel står i manuset; förhandsvisningen ändras inte.", "manus")
    return op._resultat("motfraga", "Vilket lager menar du: text, musik, matbild eller montage?", None,
                        alternativ=["skarmtext", "ljud", "broll", "montage"])
