# E20, beskrivande: hur mycket av motorrummets utfallssignal bär tjänstemötets fyra fält, och vad blir kvar?
# Korsvaliderat med hela konton undanhållna. Kör: ../scen/.venv/Scripts/python.exe -u format/e20_andel.py [motorer-bib]
import json, sys
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
ROT = Path(__file__).resolve().parents[2] / "data" / "format"
kalla = sys.argv[1] if len(sys.argv) > 1 else "motorer-bib"
R = [json.loads(l) for l in (ROT / "e15" / f"{kalla}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
V = np.load(ROT / "e15" / f"vek-{kalla}-hel.npy")
L = {}
for i, r in enumerate(R):
    f = ROT / "e20" / "lasning" / f"{r['id']}.json"
    if f.exists() and r.get("u") is not None: L[i] = json.loads(f.read_text(encoding="utf-8"))
I = np.array(sorted(L)); konto = np.array([R[i]["konto"] for i in I]); u = np.array([R[i]["u"] for i in I]); V = V[I]
FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"]}
D = np.array([[float(L[i][f] == v) for f, vs in FALT.items() for v in vs] for i in I])
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
def cen(X):
    X = X.astype(float).copy()
    for k in set(konto): m = konto == k; X[m] -= X[m].mean(0)
    return X
C, Dc, y = cen(V), cen(D), cen(u)
rng = np.random.default_rng(5); kk = np.array(sorted(set(konto)))
def kors(bygg, n=8):
    rs, P = [], np.zeros(len(u))
    for _ in range(n):
        rng.shuffle(kk); pred = np.zeros(len(u))
        for v in np.array_split(kk, 5):
            te = np.isin(konto, v); X, Xt = bygg(~te, te); b = np.linalg.solve(X.T @ X + 10 * np.eye(X.shape[1]) * X.var() * len(X) / 100, X.T @ y[~te]); pred[te] = Xt @ b
        rs.append(sp(cen(pred), y)); P += pred
    return np.mean(rs), cen(P / n)
def motor(tr, te):
    _, _, W = np.linalg.svd(C[tr], full_matrices=False); W = W[:30]; return C[tr] @ W.T, C[te] @ W.T
def falt(tr, te): return Dc[tr], Dc[te]
def bada(tr, te):
    a, b = motor(tr, te); return np.hstack([a, Dc[tr] * 3]), np.hstack([b, Dc[te] * 3])
rm, pm = kors(motor); rf, pf = kors(falt); rb, _ = kors(bada)
print(f"{len(u)} klipp, {len(kk)} konton (hela konton undanhållna)")
print(f"  motorrummet (30 axlar):          rho {rm:+.3f}")
print(f"  bara tjänstemötets fyra fält:    rho {rf:+.3f}")
print(f"  båda:                            rho {rb:+.3f}")
# det motorrummet ser utöver fälten: motorns förutsägelse rensad från fältens
res = pm - np.polyval(np.polyfit(pf, pm, 1), pf)
print(f"  motorn rensad från fälten:       rho {sp(res, y):+.3f}   (samband motor–fält: {sp(pm, pf):+.2f})")
print("\nDet motorrummet förutsäger högt UTAN att fälten gör det (ledtrådar till fler trådar):")
for j in np.argsort(res)[-10:][::-1]: print(f"  [{L[I[j]]['relation']}, {L[I[j]]['friktion']}, utfall {u[j]:+.1f}] {R[I[j]]['motor'][:185]}")
print("\nDet motorrummet förutsäger lågt trots att fälten säger högt:")
for j in np.argsort(res)[:8]: print(f"  [{L[I[j]]['relation']}, {L[I[j]]['friktion']}, utfall {u[j]:+.1f}] {R[I[j]]['motor'][:185]}")
