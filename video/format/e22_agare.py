# E22: ägaren som gles sond mot de sju fälten (E20 + E21). Bara avläsning, inget justeras.
#   ../scen/.venv/Scripts/python.exe -u format/e22_agare.py
# 1. Fältmodellen fryses på ALLA klipp med utfall (bibliotek + replikering), centrerat per konto.
# 2. Pass 7: väljer ägaren klippet med högst förutsagt utfall?  3. Pass 4–6: passform inom kund mot förutsagt utfall.
# 4. Urval till ägaren: klipp där fältmodellen och bibliotekets hylla (ägarnära harness v6) går mest isär.
import json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROT = Path(__file__).resolve().parents[2] / "data" / "format"
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
NAMN = [f"{k}={x}" for k, xs in FALT.items() for x in xs]


def falt(id_):
    a, b = ROT / "e20" / "lasning" / f"{id_}.json", ROT / "e21" / "lasning" / f"{id_}.json"
    if not (a.exists() and b.exists()): return None
    return {**json.loads(a.read_text(encoding="utf-8")), **json.loads(b.read_text(encoding="utf-8"))}


vek = lambda f: np.array([float(f.get(k) == x) for k, xs in FALT.items() for x in xs])
R = [json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
X, y, kon, ids = [], [], [], []
for r in R:
    f = falt(r["id"])
    if f and r.get("u") is not None: X.append(vek(f)); y.append(r["u"]); kon.append(r["konto"]); ids.append(r["id"])
X, y, kon = np.array(X), np.array(y), np.array(kon)
Xc, yc = X.copy(), y.copy()
for k in set(kon): m = kon == k; Xc[m] -= Xc[m].mean(0); yc[m] -= yc[m].mean()
b = np.linalg.solve(Xc.T @ Xc + 5 * np.eye(X.shape[1]), Xc.T @ yc)
poang = lambda id_: (vek(falt(id_)) @ b) if falt(id_) else None
print(f"Fältmodell frusen på {len(y)} klipp från {len(set(kon))} konton. Vikter (log visningar inom konto):")
print("  " + "  ".join(f"{n} {w:+.2f}" for n, w in sorted(zip(NAMN, b), key=lambda t: -t[1])))
np.save(ROT / "e21" / "faltvikter.npy", b)

# 2. Pass 7
P = json.loads((ROT / "harness" / "pass7" / "forregistrering.json").read_text(encoding="utf-8"))["par"]
A = json.loads((ROT / "harness" / "pass7" / "agare.json").read_text(encoding="utf-8"))["val"]
ratt = fel = lika = sakn = 0
for p in P:
    val = A.get(str(p["nr"])); v, h = poang(p["vanster"]["id"]), poang(p["hoger"]["id"])
    if not val: continue
    if v is None or h is None: sakn += 1; continue
    d = v - h
    if abs(d) < 1e-9: lika += 1
    elif (d > 0) == (val == "v"): ratt += 1
    else: fel += 1
print(f"\nPass 7 (biblioteksval): {ratt} rätt, {fel} fel, {lika} lika, {sakn} saknar fält  (nytta6 gav 16 av 19, grundvärdet 10)")

# 3. Pass 4–6 passform inom kund
plan = json.loads((ROT / "e13" / "plan.json").read_text(encoding="utf-8")); rad = []
for k, p in plan.items():
    for c in p["kandidater"]:
        if c.get("agare") is None: continue
        s = poang(c["id"])
        if s is not None: rad.append((k, c["agare"], s))
if rad:
    kk = np.array([r[0] for r in rad]); a = np.array([r[1] for r in rad], float); s = np.array([r[2] for r in rad])
    for k in set(kk): m = kk == k; a[m] -= a[m].mean(); s[m] -= s[m].mean()
    print(f"Pass 4–6 passform inom kund ({len(rad)} par): rho {sp(a, s):+.2f}  (familj +0,54, Argon b2 +0,61, E14 hemma +0,56)")

# 4. Urval till ägaren: bibliotekets hylla mot fältmodellen
bib = json.loads((ROT / "harness" / "bibliotek-v6.json").read_text(encoding="utf-8"))
H = {k["id"]: k for k in sum(bib["hyllor"].values(), [])}
rang = {"karna": 2, "mitten": 1, "situation": 1, "capcut_referens": 0, "ute": 0}
kand = [(i, poang(i), H[i]) for i in H if poang(i) is not None]
pz = rankdata([c[1] for c in kand]) / len(kand)
ut = []
for (i, s, h), q in zip(kand, pz):
    if rang[h["hylla"]] == 0 and q > 0.9: ut.append(("ute_men_falt_hogt", q, i, h))
    if rang[h["hylla"]] == 2 and q < 0.1: ut.append(("karna_men_falt_lagt", 1 - q, i, h))
ut.sort(key=lambda t: -t[1])
val = {}
for typ in ["ute_men_falt_hogt", "karna_men_falt_lagt"]:
    val[typ] = [{"id": i, "url": h.get("url"), "hylla": h["hylla"], "karna": h.get("karna"), "falt": falt(i), "percentil": round(float(q), 2)} for t, q, i, h in ut if t == typ][:10]
(ROT / "e22").mkdir(exist_ok=True)
(ROT / "e22" / "urval-till-agaren.json").write_text(json.dumps(val, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nUrval till ägaren (e22/urval-till-agaren.json):")
for typ, L in val.items():
    print(f"  {typ}: {len(L)}")
    for c in L[:5]: print(f"    {c['hylla']:6s} p{c['percentil']:.2f} {c['falt']['relation']}/{c['falt']['friktion']}/{c['falt']['uttryck']}: {(c['karna'] or '')[:120]}")
