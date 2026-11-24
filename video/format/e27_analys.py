# E27: replikering av E26 (HE27a–c). Kör: HF_HUB_OFFLINE=1 ../scen/.venv/Scripts/python.exe -u format/e27_analys.py
# Samma korsvalidering som E23 (hela konton undanhållna) på samma 400 klipp.
import json
from pathlib import Path
import numpy as np, torch
from scipy.stats import rankdata
from transformers import AutoTokenizer, AutoModel
ROT = Path(__file__).resolve().parents[2] / "data" / "format"
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1]); rng = np.random.default_rng(23)
R = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
U = json.loads((ROT / "e27" / "urval.json").read_text()); ids = [i for i in U["replikering"] + U["bibliotek"] if (ROT / "e27" / "lasning" / f"{i}.json").exists()]
L = lambda d, i: json.loads((ROT / d / f"{i}.json").read_text(encoding="utf-8"))
T = {"A motor": [R[i]["hel"] for i in ids], 
     "N återberättelse": [L("e27/lasning", i)["aterberattelse"] for i in ids], "S säljtext": [L("e27/lasning", i)["saljtext"] for i in ids]}
tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small"); mod = AutoModel.from_pretrained("intfloat/multilingual-e5-small").eval()
def badda(X):
    ut = []
    for k in range(0, len(X), 64):
        b = tok(["query: " + t for t in X[k:k + 64]], padding=True, truncation=True, max_length=256, return_tensors="pt")
        with torch.no_grad(): h = mod(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).float(); ut.append(torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1).numpy())
    return np.concatenate(ut)
V = {n: badda(x) for n, x in T.items()}
V["A + N"] = np.hstack([V["A motor"], V["N återberättelse"]]) / np.sqrt(2); V["N − S (huvudrummet som riktning)"] = V["N återberättelse"] - V["S säljtext"]
konto = np.array([R[i]["konto"] for i in ids]); u = np.array([R[i]["u"] for i in ids]); kk = np.array(sorted(set(konto)))
def cen(X):
    X = np.asarray(X, float).copy()
    for k in set(konto): m = konto == k; X[m] -= X[m].mean(0)
    return X
def kors(X, omg=10):
    C = cen(X); y = cen(u); rs = []
    for _ in range(omg):
        rng.shuffle(kk); p = np.zeros(len(u))
        for f in np.array_split(kk, 5):
            te = np.isin(konto, f); tr = ~te; _, _, W = np.linalg.svd(C[tr], full_matrices=False); W = W[:30]; Xt = C[tr] @ W.T
            b = np.linalg.solve(Xt.T @ Xt + 10 * np.eye(30) * Xt.var() * len(Xt) / 100, Xt.T @ y[tr]); p[te] = C[te] @ W.T @ b
        rs.append(sp(cen(p), y))
    return np.mean(rs), np.std(rs)
stora = np.array([np.sum(konto == k) >= 3 for k in konto])
for n, X in V.items():
    m, s = kors(X); S = X @ X.T; np.fill_diagonal(S, -9)
    print(f"  {n:34s} utfall {m:+.3f} (±{s:.3f})   kontot gissas {np.mean(konto[S.argmax(1)][stora] == konto[stora]):.2f}")
nya = set(U["replikering"])
for namn, mask in [("replikering", np.array([i in nya for i in ids])), ("bibliotek", np.array([i not in nya for i in ids]))]:
    if mask.sum() < 100: continue
    ids0, konto0, u0 = ids, konto, u
    print(f"\n{namn} ({mask.sum()} klipp):")
    for n in ["A motor", "N återberättelse", "S säljtext"]:
        X = V[n][mask]; konto, u = konto0[mask], u0[mask]; kk = np.array(sorted(set(konto)))
        m, s = kors(X); print(f"  {n:20s} utfall {m:+.3f} (±{s:.3f})")
    konto, u, kk = konto0, u0, np.array(sorted(set(konto0)))
# HE27d: N + sju fält på replikeringen
b = np.load(ROT / "e21" / "faltvikter.npy")
FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
def falt(i):
    f = {**L("e20/lasning", i), **L("e21/lasning", i)}; return np.array([float(f.get(k) == x) for k, xs in FALT.items() for x in xs]) @ b
