# E31, utforskande: modellfri poäng (tekniskt lager E28 + tal E30), fryst på biblioteket, prövad på replikeringen.
import json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
ROT = Path(__file__).resolve().parents[2] / "data" / "format"
jl = lambda p: {json.loads(l)["id"]: json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}
R = jl(ROT / "e15/motorer-flash.jsonl"); TAL = jl(ROT / "e30/tal.jsonl"); TEK = jl(ROT / "e28/tek.jsonl")
nya = set(json.loads((ROT / "e19/ids.json").read_text()))
ids = [i for i in R if i in TAL and i in TEK and R[i].get("u") is not None and TAL[i]["langd"] >= 0.5]
konto = np.array([R[i]["konto"] for i in ids]); u = np.array([R[i]["u"] for i in ids], float); ny = np.array([i in nya for i in ids])
TF = ["langd", "takt", "skott_median", "skott_max", "skott_cv", "byten_3s", "rorelse", "rorelse_kvot", "ljud_andel", "pauser", "lufs", "lra"]
g = lambda v: 0.0 if v is None or v != v else float(v)
T = np.array([[g(TEK[i][f]) for f in TF] for i in ids]); T[:, [0, 2, 3]] = np.log1p(np.clip(T[:, [0, 2, 3]], 0, None))
S = np.array([[np.log1p(TAL[i]["tal_segment"]), TAL[i]["tal_andel"], (TAL[i]["forsta_tal"] if TAL[i]["forsta_tal"] is not None else TAL[i]["langd"]) / TAL[i]["langd"]] for i in ids])
def cen(X):
    X = np.asarray(X, float).copy()
    for k in set(konto): m = konto == k; X[m] -= X[m].mean(0)
    return X
y = cen(u); sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
def frys(X, lam):
    C = cen(X); C = C / (C[~ny].std(0) + 1e-9); b = np.linalg.solve(C[~ny].T @ C[~ny] + lam * np.eye(C.shape[1]), C[~ny].T @ y[~ny]); return C @ b, b
for n, X in [("tekniskt", T), ("tal", S), ("tekniskt + tal", np.hstack([T, S]))]:
    p, b = frys(X, 20); print(f"  {n:16s} bibliotek {sp(p[~ny], y[~ny]):+.3f}  replikering {sp(p[ny], y[ny]):+.3f}")
p, b = frys(np.hstack([T, S]), 20)
print("  vikter:", ", ".join(f"{n} {v:+.3f}" for n, v in sorted(zip(TF + ["tal_segment", "tal_andel", "forsta_tal_rel"], b), key=lambda x: -abs(x[1]))[:8]))
# utfall per kvintil av den frysta poängen på replikeringen
q = np.quantile(p[ny], [0.2, 0.4, 0.6, 0.8]); kv = np.digitize(p[ny], q)
print("  replikering, utfall inom konto per kvintil (lägst till högst):", " ".join(f"×{np.exp(y[ny][kv == j].mean()):.2f}" for j in range(5)))
