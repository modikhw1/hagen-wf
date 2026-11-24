# E19 Argon-kontroll (e19/tillagg-argon.json): HA1 fält ur Argons motor mot fält ur Flashs, HA2 överensstämmelse.
#   ../scen/.venv/Scripts/python.exe -u format/e19_argon.py
import json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROT = Path(__file__).resolve().parents[2] / "data" / "format"
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
vek = lambda f: np.array([float(f.get(k) == x) for k, xs in FALT.items() for x in xs])
R = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
nya = set(json.loads((ROT / "e19" / "ids.json").read_text()))


def las(id_, suff):
    a, b = ROT / "e20" / f"lasning{suff}" / f"{id_}.json", ROT / "e21" / f"lasning{suff}" / f"{id_}.json"
    return {**json.loads(a.read_text(encoding="utf-8")), **json.loads(b.read_text(encoding="utf-8"))} if a.exists() and b.exists() else None


# Vikter frusna på biblioteket (Flash), samma som HE21d
X, y, k = [], [], []
for i, r in R.items():
    f = las(i, "")
    if i in nya or f is None or r.get("u") is None: continue
    X.append(vek(f)); y.append(r["u"]); k.append(r["konto"])
X, y, k = np.array(X), np.array(y), np.array(k)
for kk in set(k): m = k == kk; X[m] -= X[m].mean(0); y[m] -= y[m].mean()
b = np.linalg.solve(X.T @ X + 5 * np.eye(X.shape[1]), X.T @ y)

ids = [i for i in json.loads((ROT / "e19" / "argon-ids.json").read_text()) if las(i, "-argon") and las(i, "") and R.get(i, {}).get("u") is not None]
print(f"{len(ids)} replikeringsklipp med fält ur både Argons och Flashs motor\n")
print("HA2 överensstämmelse mellan fälten:")
for falt in FALT:
    lika = np.mean([las(i, "")[falt] == las(i, "-argon")[falt] for i in ids]); print(f"  {falt:9s} {lika:.2f}{'  (tröskel 0,75)' if falt in ('relation', 'friktion') else ''}")
kon = np.array([R[i]["konto"] for i in ids]); u = np.array([R[i]["u"] for i in ids])


def inom(x):
    x = np.asarray(x, float).copy()
    for kk in set(kon): m = kon == kk; x[m] -= x[m].mean()
    return x


pf = inom([vek(las(i, "")) @ b for i in ids]); pa = inom([vek(las(i, "-argon")) @ b for i in ids]); uu = inom(u)
print(f"\nHA1 frusna sju fält mot utfall inom konto: ur Flashs motor rho {sp(pf, uu):+.3f}, ur Argons motor rho {sp(pa, uu):+.3f}")
rng = np.random.default_rng(4); d = []
for _ in range(2000):
    j = rng.integers(0, len(ids), len(ids)); d.append(sp(pa[j], uu[j]) - sp(pf[j], uu[j]))
print(f"   skillnad Argon − Flash {sp(pa, uu) - sp(pf, uu):+.3f}, 95 % bootstrap [{np.percentile(d, 2.5):+.3f}, {np.percentile(d, 97.5):+.3f}]")
