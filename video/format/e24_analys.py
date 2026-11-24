# E24: neutral logg (tankar av, tre läsningar vid temperatur 1,3). HE24a–f mot A, B och N på samma klipp.
#   HF_HUB_OFFLINE=1 ../scen/.venv/Scripts/python.exe -u format/e24_analys.py
import json, re
from pathlib import Path
import numpy as np, torch
from scipy.stats import rankdata
from transformers import AutoTokenizer, AutoModel

ROT = Path(__file__).resolve().parents[2] / "data" / "format"; E = ROT / "e24"
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1]); rng = np.random.default_rng(24)
R = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
TEK = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e28" / "tek.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
L = lambda d, i: json.loads((ROT / d / f"{i}.json").read_text(encoding="utf-8"))
ids = [i for i in json.loads((ROT / "e23" / "ids.json").read_text()) if all((E / f"p{p}" / f"{i}.json").exists() for p in (1, 2, 3))]
COPY = set(json.loads((ROT / "e23" / "copyord.json").read_text(encoding="utf-8")))
ord_ = lambda t: re.findall(r"[a-zåäöé]+", t.lower())
def upp(t):
    w = ord_(t); s = " ".join(w); return 100 * (sum(x in COPY for x in w) + s.count("visa upp") + s.count("visar upp")) / max(len(w), 1)
logg = {p: {i: L(f"e24/p{p}", i)["logg"] for i in ids} for p in (1, 2, 3)}
txt = lambda rad: " ".join(f"{r['vem']} {r['gor']} {r['med']}".strip() + (f": {r['sags']}" if r["sags"] else "") for r in rad)
print(f"{len(ids)} klipp med tre läsningar\n")
T = {"A motor": [R[i]["hel"] for i in ids], "B vardaglig": [L("e23/B", i)["vad"] + " " + L("e23/B", i)["vem"] for i in ids], "N återberättelse": [L("e26/lasning", i)["aterberattelse"] for i in ids]}
for p in (1, 2, 3): T[f"E24 läsning {p}"] = [txt(logg[p][i]) for i in ids]
print("HE24a copyord per 100 ord:  " + "  ".join(f"{n} {np.mean([upp(t) for t in x]):.1f}" for n, x in T.items() if not n.endswith(("2", "3"))))
tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small"); mod = AutoModel.from_pretrained("intfloat/multilingual-e5-small").eval()
def badda(X):
    ut = []
    for k in range(0, len(X), 64):
        b = tok(["query: " + t for t in X[k:k + 64]], padding=True, truncation=True, max_length=384, return_tensors="pt")
        with torch.no_grad(): h = mod(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).float(); ut.append(torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1).numpy())
    return np.concatenate(ut)
V = {n: badda(x) for n, x in T.items()}
K = (V["E24 läsning 1"] + V["E24 läsning 2"] + V["E24 läsning 3"]); V["E24 konsensus"] = K / np.linalg.norm(K, axis=1, keepdims=True)
V["A + E24"] = np.hstack([V["A motor"], V["E24 konsensus"]]) / np.sqrt(2); V["N + E24"] = np.hstack([V["N återberättelse"], V["E24 konsensus"]]) / np.sqrt(2)
konto = np.array([R[i]["konto"] for i in ids]); u = np.array([R[i]["u"] for i in ids]); kk = np.array(sorted(set(konto)))
def cen(X):
    X = np.asarray(X, float).copy()
    for k in set(konto): m = konto == k; X[m] -= X[m].mean(0)
    return X
y = cen(u)
def kors(X, omg=10):
    C = cen(X); rs = []
    for _ in range(omg):
        rng.shuffle(kk); p = np.zeros(len(u))
        for f in np.array_split(kk, 5):
            te = np.isin(konto, f); tr = ~te; _, _, W = np.linalg.svd(C[tr], full_matrices=False); W = W[:30]; Xt = C[tr] @ W.T
            b = np.linalg.solve(Xt.T @ Xt + 10 * np.eye(30) * Xt.var() * len(Xt) / 100, Xt.T @ y[tr]); p[te] = C[te] @ W.T @ b
        rs.append(sp(cen(p), y))
    return np.mean(rs), np.std(rs)
stora = np.array([np.sum(konto == k) >= 3 for k in konto])
print("\nHE24b/c/f utfall inom konto (konton undanhållna) och kontot gissat ur närmaste granne:")
for n in ["A motor", "B vardaglig", "N återberättelse", "E24 läsning 1", "E24 konsensus", "A + E24", "N + E24"]:
    m, s = kors(V[n]); S = V[n] @ V[n].T; np.fill_diagonal(S, -9)
    print(f"  {n:18s} utfall {m:+.3f} (±{s:.3f})   kontot {np.mean(konto[S.argmax(1)][stora] == konto[stora]):.2f}")
def perm(x, n=4000):
    x = cen(x); r0 = sp(x, y); c = 0
    for _ in range(n):
        z = y.copy()
        for k in set(konto): m = konto == k; z[m] = rng.permutation(z[m])
        c += abs(sp(x, z)) >= abs(r0)
    return r0, (c + 1) / (n + 1)
rader = np.array([np.mean([len(logg[p][i]) for p in (1, 2, 3)]) / max(TEK.get(i, {}).get("langd", 10), 1) for i in ids])
verb = np.array([np.mean([len({r["gor"].split(" ")[0].lower() for r in logg[p][i] if r["gor"]}) for p in (1, 2, 3)]) for i in ids])
tomma = np.array([np.mean([sum(not r["gor"] for r in logg[p][i]) / max(len(logg[p][i]), 1) for p in (1, 2, 3)]) for i in ids])
stab = np.array([np.mean([V["E24 läsning 1"][j] @ V["E24 läsning 2"][j], V["E24 läsning 1"][j] @ V["E24 läsning 3"][j], V["E24 läsning 2"][j] @ V["E24 läsning 3"][j]]) for j in range(len(ids))])
print("\nHE24d/e (tvåsidigt):")
for n, x in [("rader per sekund", rader), ("olika verb", verb), ("andel rader utan handling", tomma), ("stabilitet mellan läsningarna", stab)]:
    r, p = perm(x); print(f"  {n:28s} medel {x.mean():.3f}  rho {r:+.3f}  p {p:.4f}")
print("\nExempel (läsning 1):")
for j in [0, 1]: print(f"  {ids[j]}: {T['E24 läsning 1'][j][:300]}")
