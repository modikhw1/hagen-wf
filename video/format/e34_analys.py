# E34: bildtextfynden (E32/E33) på osedda klipp. data/format/e34/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e34_analys.py
import json, re, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
D = Path(__file__).resolve().parents[2] / "data"; rng = np.random.default_rng(34)

def utfall(v, w=10):
    ut = np.full(len(v), np.nan)
    for i in range(len(v)):
        g = np.concatenate([v[max(0, i - w):i], v[i + 1:i + w + 1]])
        if len(g) >= 6: ut[i] = v[i] - np.median(g)
    return ut

rad = []; antal = {"aldre": 0, "nyare": 0, "for_unga": 0}
for f in sorted((D / "format" / "e34" / "listor").glob("*.json")):
    j = json.loads(f.read_text(encoding="utf-8")); k = j["konto"]; h = date.fromisoformat(j["hamtad"][:10])
    gam = json.loads((D / "bank" / k / "lista.json").read_text(encoding="utf-8"))
    sett = {x["id"] for x in gam["klipp"]}; gh = gam["hamtad"][:10]
    gd = sorted(x["datum"] for x in gam["klipp"] if x.get("datum"))
    L = sorted([x for x in j["klipp"] if (x.get("visningar") or 0) > 0 and x.get("datum")], key=lambda x: x["datum"])
    if len(L) < 7: continue
    vis = np.array([x["visningar"] for x in L], float); lv = np.log(vis)
    U = utfall(lv)
    T = {t: utfall(np.log(np.array([(x.get(t) or 0) + 1 for x in L], float)) - lv) for t in ["gillanden", "kommentarer", "delningar"]}
    for i, x in enumerate(L):
        if x["id"] in sett or np.isnan(U[i]): continue
        if gd and x["datum"] < gd[0]: typ = "aldre"
        elif x["datum"] > gh:
            if (h - date.fromisoformat(x["datum"])).days < 5: antal["for_unga"] += 1; continue
            typ = "nyare"
        else: continue  # inom förra fönstret men saknades (borttaget/dolt förut): utesluts
        antal[typ] += 1
        rad.append({"konto": k, "typ": typ, "text": (x.get("text") or "").lower(), "u": U[i], "gill": T["gillanden"][i], "komm": T["kommentarer"][i], "dela": T["delningar"][i], "id": f"{k}-{x['id']}"})
print(f"Osedda klipp: {antal}, {len({r['konto'] for r in rad})} konton")

ka = np.array([r["konto"] for r in rad]); tx = [r["text"] for r in rad]
def cen(v):
    v = np.asarray(v, float).copy()
    for k in set(ka): m = ka == k; v[m] -= v[m].mean()
    return v
uc = cen([r["u"] for r in rad]); Y = {"u": uc}
for t in ["gill", "komm", "dela"]:
    v = cen([r[t] for r in rad]); Y[t] = v - (v @ uc) / (uc @ uc) * uc
def pb(m, yv, n=5000):
    d0 = yv[m].mean() - yv[~m].mean(); c = 0; g = [np.where(ka == k)[0] for k in set(ka)]
    for _ in range(n):
        mm = m.copy()
        for gg in g: mm[gg] = rng.permutation(mm[gg])
        c += abs(yv[mm].mean() - yv[~mm].mean()) >= abs(d0)
    return np.exp(d0), (c + 1) / (n + 1)
has = lambda p: np.array([bool(re.search(p, t)) for t in tx])
pris = has(r"\d\s*kr\b|\d\s*%|gratis")
H = [("HE34a", "pris", pris, "u"), ("HE34b", "pris", pris, "dela"),
     ("HE34c", "tagga/skicka", has(r"tagga|\btag\b|skicka|\bsend\b|\bdela\b"), "dela"),
     ("HE34d", "uppmaning kommentera", has(r"kommentera|\bskriv|\bvem\b|vilken|vilket|vad tycker|comment|tell us|\bwhich\b"), "komm"),
     ("HE34e", "inbjudan i tid", has(r"öppnar|helgen|torsdag|börjar|\bvän"), "dela"),
     ("HE34f", "fråga '?'", np.array(["?" in t for t in tx]), "komm"),
     ("(kontroll)", "tävling", has(r"\bvinn|tävling|giveaway|vinnare|\bwin\b"), "komm")]
print(f"{len(rad)} klipp. Faktor inom konto; gill/komm/dela per visning med u konstant")
for h, n, m, mal in H:
    rr = {t: pb(m, Y[t]) for t in ["u", "gill", "komm", "dela"]}; f, p = rr[mal]
    print(f"  {h:10s} {n:20s} n {m.sum():4d}  " + "  ".join(f"{t} ×{rr[t][0]:.2f} (p {rr[t][1]:.3f})" for t in rr) + (f"  => {'HÅLLER' if f > 1 and p < 0.05 else 'FALLER'}" if h.startswith("HE") else ""))
for typ in ["aldre", "nyare"]:
    s = np.array([r["typ"] == typ for r in rad]); m = pris & s
    print(f"  pris, bara {typ}: n {m.sum()}  u ×{np.exp(uc[m].mean() - uc[s & ~pris].mean()):.2f}")
json.dump([r["id"] for r in rad], open(D / "format" / "e34" / "osedda.json", "w"))
