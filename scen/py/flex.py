"""Flexibilitetstest: hur mycket går det att röra på varje klipp och fortfarande ligga på 80+ i närhet?

För varje scen med en figur provas alla motiv × {fart 0,66 / 1 / 1,5} × {spegel av/på}. Rapporteras:
  andel_80   : andel av alla prövade rörelsebyten som når 80+
  motiv_80   : antal motiv (av K) som når 80+ i minst en variant
Struktur: ta bort / dubbla / halvera / dubbla längd per scen, poäng mot bankens fördelningar.
Scengränser jämförs mot handmärkta gränser (fält 'facit').
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from motiv import vektor

ROT = Path(__file__).resolve().parent.parent
bib = json.load(open(ROT / "data/bibliotek/motiv.json", encoding="utf-8"))
ref = json.load(open(ROT / "data/bibliotek/referens.json", encoding="utf-8"))
st = json.load(open(ROT / "data/bibliotek/struktur.json", encoding="utf-8"))
R = np.array(ref["X"]).reshape(-1, ref["dim"]); d90 = ref["d90"]
KX = np.array(ref["kontext"]); D90K = ref["d90_kontext"]
def poang(v, k=None):
    RR, dd = (R[KX == k], D90K[k]) if k else (R, d90)
    return float(np.clip(100 * (1 - 0.2 * np.sqrt(((RR - v) ** 2).sum(1)).min() / dd), 0, 100))
spoang = lambda x, k: float(np.clip(100 * (1 - 0.2 * abs(np.log(max(.05, x)) - st[k]["median_log"]) / st[k]["q90"]), 0, 100))

FACIT = {  # handmärkta scengränser (sekunder) ur kontaktark 2 fps
    "a-sketch-servering": [2.0, 4.5, 6.0, 9.5, 17.0, 18.5, 20.5],
    "b-tilltal-ravara": [3.4, 6.9, 8.5, 10.5],
    "c-sketch-tre": [],
}


def variant(m, fart, spegel):
    P = np.array(m["pose"]); Rl = np.array(m["rel"]); T = len(P)
    idx = np.clip((np.arange(T) * fart).astype(int), 0, T - 1); P = P[idx]; Rl = Rl[idx] * fart
    if spegel:
        P = P[:, [0, 2, 1, 4, 3, 6, 5, 8, 7]] * [-1, 1]; Rl = Rl * [-1, 1, 1]
    return vektor(P, Rl)


VV = {(m["id"], f, s): variant(m, f, s) for m in bib["motiv"] for f in (0.66, 1.0, 1.5) for s in (False, True)}
VAR = {k: poang(v) for k, v in VV.items()}


def granser(scener):
    return [s["start"] for s in scener[1:]]


def traff(auto, facit, tol=0.5):
    if not facit: return {"precision": 1.0 if not auto else 0.0, "recall": 1.0}
    tp = sum(any(abs(a - f) <= tol for a in auto) for f in facit)
    fp = sum(not any(abs(a - f) <= tol for f in facit) for a in auto)
    return {"recall": round(tp / len(facit), 2), "precision": round((len(auto) - fp) / max(1, len(auto)), 2)}


ut = {}
for namn, metod in [("a-sketch-servering", "2d"), ("b-tilltal-ravara", "semantisk"), ("c-sketch-tre", "rum")]:
    S = json.load(open(ROT / f"data/{namn}/scen-{metod}.json", encoding="utf-8"))
    sc = S["scener"]; L = sum(s["slut"] - s["start"] for s in sc)
    orig = [m["narhet"] for s in sc for f in s["figurer"] for m in f["motiv"]]
    # rörelsebyten: samma uppsättning för alla scener med figur (motivet ersätter originalet)
    med_figur = [s for s in sc if s["figurer"]]
    alla = list(VAR.values())
    motiv_80 = len({k[0] for k, v in VAR.items() if v >= 80})
    # villkorat på scenens utsnitt + hastighet från originalsegmentet
    byten = []
    for s_ in med_figur:
        for f_ in [f for f in s_["figurer"] if f["motiv"]][:3]:
            for seg in f_["motiv"][:2]:
                vo = np.array(seg["vek"])
                for (mid, fa, sp), _ in VAR.items():
                    vv = VV[(mid, fa, sp)]
                    byten.append({"kontext": seg["kontext"], "p": poang(vv, seg["kontext"]), "h": float(np.sqrt(((vv - vo) ** 2).sum()) / d90)})
    ok = [b for b in byten if b["p"] >= 80]
    hast = {}
    for lo, hi, nm in [(0, 1, "nära_orig(<1)"), (1, 2, "mellan(1-2)"), (2, 99, "långt(>2)")]:
        bb = [b for b in byten if lo <= b["h"] < hi]
        hast[nm] = {"n": len(bb), "andel_80": round(float(np.mean([b["p"] >= 80 for b in bb])), 2) if bb else None}
    struktur = []
    for i, s in enumerate(sc):
        l = s["slut"] - s["start"]
        for namn_op, nl, ns, nL in [("ta_bort", None, len(sc) - 1, L - l), ("dubbla", l, len(sc) + 1, L + l),
                                    ("halvera", l / 2, len(sc), L - l / 2), ("dubbel_längd", l * 2, len(sc), L + l)]:
            p = [spoang(ns, "antal_scener"), spoang(nL, "klipplangd")] + ([spoang(nl, "scenlangd")] if nl else [])
            struktur.append({"scen": i + 1, "op": namn_op, "min": round(min(p), 1)})
    sg = granser(sc) if metod != "semantisk" else granser(json.load(open(ROT / f"data/{namn}/spar.json", encoding="utf-8"))["scener"])
    ut[namn] = {
        "metod": metod, "scener": len(sc), "scener_med_figur": len(med_figur), "aktorer": len(S["aktorer"]),
        "orig_motivsegment": len(orig), "orig_narhet_median": round(float(np.median(orig)), 1) if orig else None,
        "orig_andel_80": round(float(np.mean([x >= 80 for x in orig])), 2) if orig else None,
        "rorelsebyten_fri_andel_80": round(float(np.mean([v >= 80 for v in alla])), 2),
        "rorelsebyten_provade": len(byten), "rorelsebyten_kontext_andel_80": round(float(np.mean([b["p"] >= 80 for b in byten])), 2) if byten else None,
        "kontexter": sorted({b["kontext"] for b in byten}), "hastighet": hast,
        "orig_narhet_kontext_median": round(float(np.median([m["narhet"] for s_ in sc for f_ in s_["figurer"] for m in f_["motiv"]])), 1) if orig else None,
        "motiv_som_nar_80": f"{motiv_80}/{len(bib['motiv'])}",
        "struktur_andel_80": round(float(np.mean([x["min"] >= 80 for x in struktur])), 2),
        "struktur_samst": sorted(struktur, key=lambda x: x["min"])[:3],
        "scengranser_auto_mot_facit": traff(sg, FACIT[namn]),
        "handelser": sum(len(s.get("handelser", [])) for s in sc),
        "avsikt_satt": sum(1 for s in sc if s.get("avsikt")),
    }
per_variant = {}
for (mid, f, s), v in VAR.items():
    per_variant.setdefault(f"fart{f}{'_spegel' if s else ''}", []).append(v >= 80)
ut["_varianter_andel_80"] = {k: round(float(np.mean(v)), 2) for k, v in per_variant.items()}
ut["_kontroller"] = bib["kontroller"]
json.dump(ut, open(ROT / "data/flex.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(ut, ensure_ascii=False, indent=1))
