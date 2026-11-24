# E31: fält (E20/E21) och tal (E30), frysta på biblioteket, prövade på replikeringen. data/format/e31/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e31_analys.py
import json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
ROT = Path(__file__).resolve().parents[2] / "data" / "format"; rng = np.random.default_rng(31)
jl = lambda p: {json.loads(l)["id"]: json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}
R = jl(ROT / "e15" / "motorer-flash.jsonl"); TAL = jl(ROT / "e30" / "tal.jsonl")
L = lambda d, i: json.loads((ROT / d / f"{i}.json").read_text(encoding="utf-8"))
nya = set(json.loads((ROT / "e19" / "ids.json").read_text()))
ids = [i for i in R if i in TAL and R[i].get("u") is not None and TAL[i]["langd"] >= 0.5 and (ROT / "e20/lasning" / f"{i}.json").exists() and (ROT / "e21/lasning" / f"{i}.json").exists()]
konto = np.array([R[i]["konto"] for i in ids]); u = np.array([R[i]["u"] for i in ids], float); ny = np.array([i in nya for i in ids])
FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
F = np.array([[float({**L("e20/lasning", i), **L("e21/lasning", i)}.get(k) == x) for k, xs in FALT.items() for x in xs] for i in ids])
T = np.array([[np.log1p(TAL[i]["tal_segment"]), TAL[i]["tal_andel"], (TAL[i]["forsta_tal"] if TAL[i]["forsta_tal"] is not None else TAL[i]["langd"]) / TAL[i]["langd"]] for i in ids])
def cen(X):
    X = np.asarray(X, float).copy()
    for k in set(konto): m = konto == k; X[m] -= X[m].mean(0)
    return X
y = cen(u); rk = lambda x: cen(rankdata(x))
def frys(X, lam=5.0):
    C = cen(X); s = C[~ny].std(0) + 1e-9; C = C / s
    b = np.linalg.solve(C[~ny].T @ C[~ny] + lam * np.eye(C.shape[1]), C[~ny].T @ y[~ny]); return C @ b
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
pF, pT, pFT = frys(F), frys(T), frys(np.hstack([F, T]))
print(f"{len(ids)} klipp ({ny.sum()} replikering), frysta på biblioteket, prövade på replikeringen (rho inom konto):")
for n, p in [("sju fält", pF), ("tal (tre mått)", pT), ("fält + tal", pFT)]: print(f"  {n:16s} bibliotek {sp(p[~ny], y[~ny]):+.3f}   replikering {sp(p[ny], y[ny]):+.3f}")
d0 = sp(pFT[ny], y[ny]) - sp(pF[ny], y[ny])
# bootstrap över konton för skillnaden
kn = np.array(sorted(set(konto[ny]))); ds = []
for _ in range(2000):
    v = rng.choice(kn, len(kn)); ix = np.concatenate([np.where(ny & (konto == k))[0] for k in v])
    ds.append(sp(pFT[ix], y[ix]) - sp(pF[ix], y[ix]))
print(f"HE31b skillnad fält+tal mot fält {d0:+.3f} (95 % över konton {np.percentile(ds, 2.5):+.3f} till {np.percentile(ds, 97.5):+.3f})")
# HE31a: partiell
xs, ys, z = rk(T[:, 0])[ny], rk(u)[ny], rk(pF)[ny]; ks = konto[ny]
xs = xs - z * (xs @ z) / (z @ z); ys2 = ys - z * (ys @ z) / (z @ z); r0 = np.corrcoef(xs, ys2)[0, 1]; c = 0
for _ in range(4000):
    yy = ys.copy()
    for k in set(ks): m = ks == k; yy[m] = rng.permutation(yy[m])
    yy = yy - z * (yy @ z) / (z @ z); c += abs(np.corrcoef(xs, yy)[0, 1]) >= abs(r0)
print(f"HE31a talsegment | fältpoäng på replikeringen: rho {r0:+.3f} p {(c + 1) / 4001:.4f}")
print(f"HE31c rho(fältpoäng, talsegment) inom konto: {np.corrcoef(rk(pF), rk(T[:, 0]))[0, 1]:+.3f}")
# vilka fält hänger ihop med tal
print("\nTalsegment per fältvärde (median, alla klipp):")
for j, (k, x) in enumerate((k, x) for k, xs in FALT.items() for x in xs):
    m = F[:, j] == 1
    if m.sum() > 30: print(f"  {k}={x:18s} n {m.sum():4d}  talsegment {np.median(np.expm1(T[m, 0])):.0f}  utan {np.median(np.expm1(T[~m, 0])):.0f}")
