# E15: geometri ur inbäddningarna. G1 igenkänning, G2 avläsning mot ägaren, G3 röd tråd, G4 axlar mot utfall.
#   ../scen/.venv/Scripts/python.exe format/e15_analys.py [falt]
import json, sys
from pathlib import Path
import numpy as np

ROT = Path(__file__).resolve().parents[2] / "data"
E = ROT / "format" / "e15"
falt = sys.argv[1] if len(sys.argv) > 1 else "text"
R = [json.loads(l) for l in (E / "klipp.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
V = np.load(E / f"vek-klipp-{falt}.npy")
ix = {r["id"]: i for i, r in enumerate(R)}
konto = np.array([r["konto"] for r in R])
rng = np.random.default_rng(1)


from scipy.stats import rankdata as rang


def spearman(a, b):
    a, b = rang(np.asarray(a, float)), rang(np.asarray(b, float))
    return float(np.corrcoef(a, b)[0, 1]) if a.std() and b.std() else float("nan")


def auc(egna, andra):
    if not len(egna) or not len(andra): return float("nan")
    return float(np.mean([(a > b) + 0.5 * (a == b) for a in egna for b in andra]))


def narhet(v, moln, k=5):
    s = np.sort(moln @ v)[::-1]
    return float(s[:k].mean())


print(f"fält: {falt}, {len(R)} klipp, {len(set(konto))} konton\n")

# G1: samma undanhållna klipp som E14
sj = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (ROT / "format" / "e14" / "sjalv").glob("*.json")}
undan = {k: [i for i in v["undan"] if i in ix] for k, v in sj.items()}
alla = [i for v in undan.values() for i in v]
aucs = []
print("G1: igenkänning av kundens egna undanhållna klipp")
for k, egna in undan.items():
    moln = V[[i for i in np.where(konto == k)[0] if R[i]["id"] not in set(alla)]]
    if len(moln) < 10 or not egna: continue
    e = [narhet(V[ix[i]], moln) for i in egna]
    a = [narhet(V[ix[i]], moln) for i in alla if i not in egna]
    aucs.append(auc(e, a)); print(f"  {k:24s} egna {len(e)}  främmande {len(a)}  AUC {aucs[-1]:.2f}")
print(f"  medel-AUC {np.mean(aucs):.2f} över {len(aucs)} kunder (slump 0,50)\n")

# G2: avläsning mot ägarens passform
plan = json.loads((ROT / "format" / "e13" / "plan.json").read_text(encoding="utf-8"))
par = []
for k, p in plan.items():
    moln = V[konto == k]
    for c in p["kandidater"]:
        if c.get("agare") is None or c["id"] not in ix or len(moln) < 10: continue
        v = V[ix[c["id"]]]
        par.append((k, c["agare"], narhet(v, moln), float(moln.mean(0) @ v), narhet(v, moln, 30)))
if par:
    ks = np.array([p[0] for p in par]); ag = np.array([p[1] for p in par], float)
    def inom(x):
        x = np.array(x, float); a = ag.copy()
        for k in set(ks): m = ks == k; a[m] -= a[m].mean(); x[m] -= x[m].mean()
        return spearman(a, x)
    print(f"G2: närhet till kundens moln mot ägarens passform ({len(par)} par)")
    for n, j in [("fem närmaste", 2), ("centroid", 3), ("trettio närmaste", 4)]:
        x = [p[j] for p in par]; print(f"  {n:18s} rho {spearman(ag, x):.2f}  inom kund {inom(x):.2f}")
    print()

# G3: röd tråd. Klipp centrerade per konto; axlar från halva kontona prövas på andra halvan.
C = V.copy()
for k in set(konto): m = konto == k; C[m] -= C[m].mean(0)
kk = np.array(sorted(set(konto))); kvoter = []
for _ in range(20):
    rng.shuffle(kk); A = np.isin(konto, kk[: len(kk) // 2]); B = ~A
    _, _, Wa = np.linalg.svd(C[A], full_matrices=False); _, sb, _ = np.linalg.svd(C[B], full_matrices=False)
    n = 20; kvoter.append(float(((C[B] @ Wa[:n].T) ** 2).sum() / (sb[:n] ** 2).sum()))
_, s, W = np.linalg.svd(C, full_matrices=False)
print(f"G3: axlar från halva kontona förklarar {np.mean(kvoter):.2f} (min {np.min(kvoter):.2f}) av det den andra halvans egna 20 axlar förklarar")
print(f"    de 20 första axlarna bär {float((s[:20] ** 2).sum() / (s ** 2).sum()):.2f} av variansen inom konto; de 5 första {float((s[:5] ** 2).sum() / (s ** 2).sum()):.2f}\n")

# G4: axlar mot utfall inom konto (log visningar minus kontots median)
vis = np.array([np.log(r["visningar"]) if r.get("visningar") else np.nan for r in R])
u = vis.copy()
for k in set(konto): m = (konto == k) & ~np.isnan(vis); u[m] -= np.median(vis[m]) if m.sum() >= 10 else np.nan
ok = ~np.isnan(u); P = C[ok] @ W[:20].T; uu = u[ok]; kon = konto[ok]
def perm_p(x, n=200):
    r0 = abs(spearman(x, uu)); f = 0
    for _ in range(n):
        y = uu.copy()
        for k in set(kon): m = kon == k; y[m] = rng.permutation(y[m])
        f += abs(spearman(x, y)) >= r0
    return (f + 1) / (n + 1)
print(f"G4: axlar mot utfall inom konto ({ok.sum()} klipp). Tröskel efter korrigering: p < {0.05 / 20:.4f}")
texter = [(r.get("innehall") or "") for r in R]
for a in range(20):
    r = spearman(P[:, a], uu)
    if abs(r) < 0.04: continue
    p = perm_p(P[:, a]); pr = C @ W[a]; hog = np.argsort(pr)[-3:][::-1]; lag = np.argsort(pr)[:3]
    print(f"  axel {a + 1:2d}  rho {r:+.2f}  p {p:.4f}{'  *' if p < 0.05 / 20 else ''}")
    print("     +: " + " | ".join(texter[i][:70] for i in hog)); print("     −: " + " | ".join(texter[i][:70] for i in lag))
np.save(E / f"axlar-{falt}.npy", W[:50].astype("float32"))
