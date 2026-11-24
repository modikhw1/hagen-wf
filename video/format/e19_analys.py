# E19: fryser utfallsmodellen på biblioteksmotorerna och prövar den på replikeringsklippen.
#   ../scen/.venv/Scripts/python.exe -u format/e19_analys.py frys   (före inbäddning av E19: sparar e17/modell.npz)
#   ../scen/.venv/Scripts/python.exe -u format/e19_analys.py prov   (läser modell.npz, prövar på E19-klippen)
# Underlag: e15/motorer-flash.jsonl med vek-motorer-flash-{hel,svag}.npy (alla klipp med motor, i samma ordning).
import json, sys
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROT = Path(__file__).resolve().parents[2] / "data"
E15, E17, E19 = ROT / "format" / "e15", ROT / "format" / "e17", ROT / "format" / "e19"
lage = sys.argv[1] if len(sys.argv) > 1 else "prov"
R = [json.loads(l) for l in (E15 / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
nya = set(json.loads((E19 / "ids.json").read_text(encoding="utf-8")))
konto = np.array([r["konto"] for r in R]); ny = np.array([r["id"] in nya for r in R])
u = np.array([r["u"] if r.get("u") is not None else np.nan for r in R]); ok = ~np.isnan(u)
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
rng = np.random.default_rng(19)


def centrera(V, mask):
    C = V.copy()
    for k in set(konto[mask]):
        m = mask & (konto == k); C[m] -= C[m].mean(0)
    return C


if lage == "frys":
    ut = {}
    for n in ["hel", "svag"]:
        V = np.load(E15 / f"vek-motorer-flash-{n}.npy"); tr = ~ny & ok
        C = centrera(V, ~ny); _, _, W = np.linalg.svd(C[tr], full_matrices=False); W = W[:30]
        X = C[tr] @ W.T; y = u[tr] - u[tr].mean()
        b = np.linalg.solve(X.T @ X + 10 * np.eye(30) * X.var() * len(X) / 100, X.T @ y)
        ut[f"W_{n}"] = W; ut[f"b_{n}"] = b
        print(f"{n}: tränad på {tr.sum()} klipp från {len(set(konto[tr]))} konton (inga E19-klipp)")
    np.savez(E17 / "modell.npz", **ut); print("sparad: e17/modell.npz")
    sys.exit()

M = np.load(E17 / "modell.npz"); te = ny & ok
print(f"E19: {ny.sum()} replikeringsklipp med motor, {te.sum()} med utfall, {len(set(konto[te]))} konton\n")


def inom(x, y, kon):
    x, y = x.copy(), y.copy()
    for k in set(kon):
        m = kon == k; x[m] -= x[m].mean(); y[m] -= y[m].mean()
    return x, y


def perm(x, y, kon, n=5000):
    r0 = sp(x, y); f = 0
    for _ in range(n):
        z = y.copy()
        for k in set(kon):
            m = kon == k; z[m] = rng.permutation(z[m])
        f += sp(x, z) >= r0
    return (f + 1) / (n + 1)


res = {}
for n, namn in [("hel", "motor"), ("svag", "svag text")]:
    V = np.load(E15 / f"vek-motorer-flash-{n}.npy"); C = centrera(V, ny)
    p = C[te] @ M[f"W_{n}"].T @ M[f"b_{n}"]; x, y = inom(p, u[te], konto[te]); res[n] = (x, y)
    print(f"HE19{'a' if n == 'hel' else 'b'}: {namn:10s} frusen modell mot utfall inom konto: rho {sp(x, y):+.3f}, p {perm(x, y, konto[te]):.4f}")

# HE19c: hantverk
h = np.array([r.get("hantverk") or "" for r in R]); bar = np.isin(h, ["i_iden", "i_personen"])
_, y = inom(np.zeros(te.sum()), u[te], konto[te]); b = bar[te]
d0 = y[b].mean() - y[~b].mean(); f = 0
for _ in range(5000):
    z = b.copy()
    for k in set(konto[te]):
        m = konto[te] == k; z[m] = rng.permutation(z[m])
    f += (y[z].mean() - y[~z].mean()) >= d0
print(f"\nHE19c: värdet i idén eller personen (n {b.sum()}) mot bilden, klippningen eller erbjudandet (n {(~b).sum()}): skillnad {d0:+.3f} i log visningar inom konto (×{np.exp(d0):.2f}), p {(f + 1) / 5001:.4f}")
for v in sorted(set(h[te])):
    m = h[te] == v
    if m.sum() >= 10: print(f"   {v:16s} n {m.sum():4d}  medel {y[m].mean():+.3f}")
print("\nUtfallsriktningen i replikeringen, ytterklippen (förutsagt högst och lägst inom sitt konto):")
x, y = res["hel"]; I = np.where(te)[0]
for t, J in [("högst", np.argsort(x)[-8:][::-1]), ("lägst", np.argsort(x)[:8])]:
    for j in J: print(f"  {t} (utfall {y[j]:+.2f}) {R[I[j]]['motor'][:170]}")
