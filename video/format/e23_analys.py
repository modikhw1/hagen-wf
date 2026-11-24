# E23: register och temperatur. Kräver e23/{B,C,D}/*.json. Bäddar själv in villkorens texter (e5-small).
#   HF_HUB_OFFLINE=1 ../scen/.venv/Scripts/python.exe -u format/e23_analys.py
import json, re
from pathlib import Path
import numpy as np, torch
from scipy.stats import rankdata
from transformers import AutoTokenizer, AutoModel

ROT = Path(__file__).resolve().parents[2] / "data" / "format"; E = ROT / "e23"
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
rng = np.random.default_rng(23)
COPY = set(json.loads((E / "copyord.json").read_text(encoding="utf-8")))
R = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
ids = [i for i in json.loads((E / "ids.json").read_text()) if all((E / v / f"{i}.json").exists() for v in "BCD")]
L = {v: {i: json.loads((E / v / f"{i}.json").read_text(encoding="utf-8")) for i in ids} for v in "BCD"}
konto = np.array([R[i]["konto"] for i in ids]); u = np.array([R[i]["u"] for i in ids])
print(f"{len(ids)} klipp med alla tre villkor, {len(set(konto))} konton\n")

TEXT = {"A": [R[i]["hel"] for i in ids]}
for v in "BCD": TEXT[v] = [f"{L[v][i]['vad']} {L[v][i]['vem']}" for i in ids]
ord_ = lambda t: re.findall(r"[a-zåäöé]+", t.lower())
def upp(t):
    w = ord_(t); s = " ".join(w); n = sum(x in COPY for x in w) + s.count("visa upp") + s.count("visar upp")
    return 100 * n / max(len(w), 1)
print("HE23a uppblåsning (copyord per 100 ord), medel:  " + "  ".join(f"{v} {np.mean([upp(t) for t in TEXT[v]]):.1f}" for v in "ABCD"))
print("   medellängd i ord:                             " + "  ".join(f"{v} {np.mean([len(ord_(t)) for t in TEXT[v]]):.0f}" for v in "ABCD"))

tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small"); mod = AutoModel.from_pretrained("intfloat/multilingual-e5-small").eval()
def badda(T):
    ut = []
    for k in range(0, len(T), 64):
        b = tok(["query: " + t for t in T[k:k + 64]], padding=True, truncation=True, max_length=192, return_tensors="pt")
        with torch.no_grad(): h = mod(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).float(); ut.append(torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1).numpy())
    return np.concatenate(ut)
VEK = {v: badda(TEXT[v]) for v in "ABCD"}
VEK["A+B"] = np.hstack([VEK["A"], VEK["B"]]) / np.sqrt(2)

def cen(X):
    X = np.asarray(X, float).copy()
    for k in set(konto): m = konto == k; X[m] -= X[m].mean(0)
    return X
kk = np.array(sorted(set(konto)))
def kors(V, n_ax=30, omg=10):
    C = cen(V); y = cen(u); rs = []
    for _ in range(omg):
        rng.shuffle(kk); p = np.zeros(len(u))
        for f in np.array_split(kk, 5):
            te = np.isin(konto, f); tr = ~te
            _, _, W = np.linalg.svd(C[tr], full_matrices=False); W = W[:n_ax]; X = C[tr] @ W.T
            b = np.linalg.solve(X.T @ X + 10 * np.eye(X.shape[1]) * X.var() * len(X) / 100, X.T @ y[tr]); p[te] = C[te] @ W.T @ b
        rs.append(sp(cen(p), y))
    return np.mean(rs), np.std(rs)
print("\nHE23b utfall inom konto, hela konton undanhållna (rho, ± mellan omgångar):")
for v in ["A", "B", "C", "D", "A+B"]:
    m, s = kors(VEK[v]); print(f"  {v:4s} {m:+.3f} (±{s:.3f})")

ans = np.array([L["B"][i]["anstrangning"] for i in ids], float); y = cen(u); a = cen(ans)
f = sum(abs(sp(a, cen(np.concatenate([rng.permutation(u[konto == k]) if False else u[konto == k] for k in []]) if False else y))) for _ in [])
def perm(x, n=4000):
    r0 = sp(x, y); c = 0
    for _ in range(n):
        z = y.copy()
        for k in set(konto): m = konto == k; z[m] = rng.permutation(z[m])
        c += abs(sp(x, z)) >= abs(r0)
    return r0, (c + 1) / (n + 1)
r, p = perm(a); print(f"\nHE23c ansträngning (B) mot utfall inom konto: rho {r:+.3f}, tvåsidigt p {p:.4f}")
print("   utfall per ansträngning (inom konto): " + "  ".join(f"{k}: {y[ans == k].mean():+.2f} (n {(ans == k).sum()})" for k in range(1, 6) if (ans == k).sum() >= 5))
ansC = np.array([L["C"][i]["anstrangning"] for i in ids]); ansD = np.array([L["D"][i]["anstrangning"] for i in ids])
print(f"   ansträngning lika mellan B och C {np.mean(ans == ansC):.2f}, B och D {np.mean(ans == ansD):.2f}")

stora = np.array([np.sum(konto == k) >= 3 for k in konto])
print("\nHE23d kontot gissas ur närmaste granne (konton med minst 3 klipp):  " + "  ".join(f"{v} {np.mean(konto[np.where(stora, (lambda S: (np.fill_diagonal(S, -9), S.argmax(1))[1])(VEK[v] @ VEK[v].T), 0)][stora] == konto[stora]):.2f}" for v in "ABCD"))

spr = np.array([np.mean([1 - VEK['B'][j] @ VEK['C'][j], 1 - VEK['B'][j] @ VEK['D'][j], 1 - VEK['C'][j] @ VEK['D'][j]]) for j in range(len(ids))])
r, p = perm(cen(spr)); print(f"\nHE23e spridning mellan temperaturerna mot utfall inom konto: rho {r:+.3f}, tvåsidigt p {p:.4f}")
r2, p2 = perm(cen(-spr * 0 + np.array([upp(t) for t in TEXT['A']]))); print(f"   (utforskande) uppblåsningen i A mot utfall inom konto: rho {r2:+.3f}, p {p2:.4f}")

print("\nExempel, samma klipp i fyra versioner:")
for j in rng.choice(len(ids), 3, replace=False):
    print(f"  [{ids[j]}, utfall {u[j]:+.1f}, ansträngning {int(ans[j])}]")
    for v in "ABCD": print(f"    {v}: {TEXT[v][j][:200]}")
