# E17: läser ut utfallsriktningen i motorrummet. Korsvaliderad förutsägelse (konton undanhållna); klippen med högst
# och lägst förutsagt utfall inom sitt konto visas med sin motor.
#   ../scen/.venv/Scripts/python.exe -u format/e17_riktning.py [motorer-flash] [antal]
import json, sys
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
E = Path(__file__).resolve().parents[2] / "data" / "format" / "e15"
kalla = sys.argv[1] if len(sys.argv) > 1 else "motorer-flash"; N = int(sys.argv[2]) if len(sys.argv) > 2 else 14
R = [json.loads(l) for l in (E / f"{kalla}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
V = np.load(E / f"vek-{kalla}-hel.npy"); konto = np.array([r["konto"] for r in R])
u = np.array([r["u"] if r.get("u") is not None else np.nan for r in R]); ok = ~np.isnan(u)
C = V.copy()
for k in set(konto): m = konto == k; C[m] -= C[m].mean(0)
rng = np.random.default_rng(3); kk = np.array(sorted(set(konto[ok]))); P = np.zeros(len(R)); n = 0
for _ in range(10):
    rng.shuffle(kk); pred = np.full(len(R), np.nan)
    for v in np.array_split(kk, 5):
        te = np.isin(konto, v); tr = ok & ~te
        _, _, W = np.linalg.svd(C[tr], full_matrices=False); W = W[:30]; X = C[tr] @ W.T; y = u[tr] - u[tr].mean()
        b = np.linalg.solve(X.T @ X + 10 * np.eye(30) * X.var() * len(X) / 100, X.T @ y); pred[te] = C[te] @ W.T @ b
    P += np.nan_to_num(pred); n += 1
P /= n
for k in set(konto): m = konto == k; P[m] -= P[m].mean()
print(f"{len(R)} klipp; förutsagt mot verkligt utfall inom konto: rho {np.corrcoef(rankdata(P[ok]), rankdata(u[ok]))[0,1]:+.3f}\n")
for t, I in [("FÖRUTSAGT HÖGST", np.argsort(P)[-N:][::-1]), ("FÖRUTSAGT LÄGST", np.argsort(P)[:N])]:
    print(t)
    for i in I: print(f"  [{R[i].get('hantverk')}, {R[i].get('hylla') or '-'}, utfall {u[i]:+.1f}] {R[i]['motor'][:200]}")
    print()
for f in ["hantverk", "hylla", "slitage", "utsatthet", "familj"]:
    g = {}
    for r, p in zip(R, P):
        if r.get(f): g.setdefault(r[f], []).append(p)
    print(f"{f}: " + "  ".join(f"{k} {np.mean(v):+.3f} (n {len(v)})" for k, v in sorted(g.items(), key=lambda x: -np.mean(x[1])) if len(v) >= 8))
