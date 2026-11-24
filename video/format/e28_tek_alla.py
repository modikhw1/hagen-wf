# E28, lager 1 på alla klipp med utfall (utforskande utöver förregistreringens 400): varje mått och lagret som helhet.
import json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
ROT = Path(__file__).resolve().parents[2] / "data" / "format"
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1]); rng = np.random.default_rng(28)
R = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
TEK = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e28" / "tek.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
nya = set(json.loads((ROT / "e19" / "ids.json").read_text()))
ids = [i for i in R if i in TEK and R[i].get("u") is not None]
konto = np.array([R[i]["konto"] for i in ids]); u = np.array([R[i]["u"] for i in ids]); kk = np.array(sorted(set(konto)))
TF = ["langd", "takt", "skott_median", "skott_max", "skott_max_andel", "skott_cv", "forsta_byte", "byten_3s", "rorelse", "rorelse_2s", "rorelse_kvot", "ljud_andel", "pauser", "lufs", "lra"]
T = np.array([[TEK[i][f] if TEK[i][f] == TEK[i][f] else 0 for f in TF] for i in ids], float); T[:, [0, 2, 3, 6]] = np.log1p(np.clip(T[:, [0, 2, 3, 6]], 0, None))
T = (T - T.mean(0)) / (T.std(0) + 1e-9)
def cen(X):
    X = np.asarray(X, float).copy()
    for k in set(konto): m = konto == k; X[m] -= X[m].mean(0)
    return X
y = cen(u); C = cen(T)
print(f"{len(ids)} klipp, {len(kk)} konton. Varje mått mot utfall inom konto (bibliotek / replikering / alla):")
ny = np.array([i in nya for i in ids])
for j, f in enumerate(TF): print(f"  {f:16s} {sp(C[~ny, j], y[~ny]):+.3f}  {sp(C[ny, j], y[ny]):+.3f}  {sp(C[:, j], y):+.3f}")
def kors(X, lam, omg=10):
    rs = []
    for _ in range(omg):
        rng.shuffle(kk); p = np.zeros(len(u))
        for fo in np.array_split(kk, 5):
            te = np.isin(konto, fo); tr = ~te; b = np.linalg.solve(X[tr].T @ X[tr] + lam * np.eye(X.shape[1]), X[tr].T @ y[tr]); p[te] = X[te] @ b
        rs.append(sp(cen(p), y))
    return np.mean(rs), np.std(rs)
m, s = kors(C, 50); print(f"\nTekniskt lager som helhet, konton undanhållna: rho {m:+.3f} (±{s:.3f})")
# Frusen på biblioteket, prövad på replikeringen
b = np.linalg.solve(C[~ny].T @ C[~ny] + 50 * np.eye(len(TF)), C[~ny].T @ y[~ny]); p = C[ny] @ b
kon = konto[ny]; pp, yy = p.copy(), y[ny].copy()
print(f"Frusen på biblioteket, prövad på replikeringen: rho {sp(pp, yy):+.3f}")
print("Vikter: " + "  ".join(f"{f} {w:+.3f}" for f, w in sorted(zip(TF, b), key=lambda t: -abs(t[1]))))
