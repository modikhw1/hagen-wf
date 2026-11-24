# E28: tre lager mot utfall inom konto på E23:s 400 klipp. HE28a–e.
#   HF_HUB_OFFLINE=1 ../scen/.venv/Scripts/python.exe -u format/e28_analys.py
import json
from pathlib import Path
import numpy as np, torch
from scipy.stats import rankdata
from transformers import AutoTokenizer, AutoModel

ROT = Path(__file__).resolve().parents[2] / "data" / "format"
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1]); rng = np.random.default_rng(28)
R = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
TEK = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e28" / "tek.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
L = lambda d, i: json.loads((ROT / d / f"{i}.json").read_text(encoding="utf-8"))
ids = [i for i in json.loads((ROT / "e23" / "ids.json").read_text()) if i in TEK and (ROT / "e28" / "lasning" / f"{i}.json").exists() and (ROT / "e26" / "lasning" / f"{i}.json").exists()]
konto = np.array([R[i]["konto"] for i in ids]); u = np.array([R[i]["u"] for i in ids]); kk = np.array(sorted(set(konto)))
print(f"{len(ids)} klipp med alla lager, {len(kk)} konton\n")
def cen(X):
    X = np.asarray(X, float).copy()
    for k in set(konto): m = konto == k; X[m] -= X[m].mean(0)
    return X
y = cen(u)
def perm(x, n=5000):
    x = cen(x); r0 = sp(x, y); c = 0
    for _ in range(n):
        z = y.copy()
        for k in set(konto): m = konto == k; z[m] = rng.permutation(z[m])
        c += abs(sp(x, z)) >= abs(r0)
    return r0, (c + 1) / (n + 1)
def kors(X, n_ax=None, lam=10.0, omg=10):
    C = cen(X); rs, P = [], np.zeros(len(u))
    for _ in range(omg):
        rng.shuffle(kk); p = np.zeros(len(u))
        for f in np.array_split(kk, 5):
            te = np.isin(konto, f); tr = ~te
            if n_ax: _, _, W = np.linalg.svd(C[tr], full_matrices=False); W = W[:n_ax]; Xt, Xe = C[tr] @ W.T, C[te] @ W.T
            else: Xt, Xe = C[tr], C[te]
            b = np.linalg.solve(Xt.T @ Xt + lam * np.eye(Xt.shape[1]) * Xt.var() * len(Xt) / 100, Xt.T @ y[tr]); p[te] = Xe @ b
        p = cen(p); rs.append(sp(p, y)); P += p
    return np.mean(rs), np.std(rs), P / omg

# Lager 1: tekniskt
TF = ["langd", "takt", "skott_median", "skott_max", "skott_max_andel", "skott_cv", "forsta_byte", "byten_3s", "rorelse", "rorelse_2s", "rorelse_kvot", "ljud_andel", "pauser", "lufs", "lra"]
T = np.array([[TEK[i][f] if TEK[i][f] == TEK[i][f] else 0 for f in TF] for i in ids], float); T[:, [0, 2, 3, 6]] = np.log1p(T[:, [0, 2, 3, 6]])
T = (T - T.mean(0)) / (T.std(0) + 1e-9)
print("Lager 1, tekniskt, ett mått i taget mot utfall inom konto:")
for j, f in enumerate(TF):
    r, p = perm(T[:, j], 2000); print(f"  {f:16s} rho {r:+.3f}  p {p:.3f}{'  *' if p < 0.05 else ''}")
mT, sT, pT = kors(T, lam=30); print(f"HE28a tekniskt lager som helhet (konton undanhållna): rho {mT:+.3f} (±{sT:.3f})\n")

# Lager 2: semantisk-tekniskt
S2 = {i: L("e28/lasning", i) for i in ids}
def sv(i):
    s = S2[i]; sc = s["scener"] or [{"start": 0, "slut": TEK[i]["langd"], "repliker": 0, "tid": "bar"}]
    lang = sum(x["tid"] == "for_lang" for x in sc) / len(sc)
    return {"for_lang_andel": lang, "for_kort_andel": sum(x["tid"] == "for_kort" for x in sc) / len(sc), "scener": len(sc), "repliker": sum(x["repliker"] for x in sc),
            "repliker_per_s": sum(x["repliker"] for x in sc) / max(TEK[i]["langd"], 1), "premiss_klar": s["premiss_klar"], "premiss_andel": s["premiss_klar"] / max(TEK[i]["langd"], 1),
            "svarighet": s["svarighet"], "manus_skrivet": float(s["manus"] == "skrivet"), "manus_inget": float(s["manus"] == "inget")}
SF = list(sv(ids[0]).keys()); S = np.array([[sv(i)[f] for f in SF] for i in ids], float)
print("Lager 2, semantisk-tekniskt (Flash), fördelning och mot utfall inom konto:")
for j, f in enumerate(SF):
    r, p = perm(S[:, j], 2000); print(f"  {f:16s} medel {S[:, j].mean():6.2f}  rho {r:+.3f}  p {p:.3f}{'  *' if p < 0.05 else ''}")
print("  (HE28b = for_lang_andel, negativt väntat; HE28c = premiss_klar, negativt väntat; HE28d = svarighet, tvåsidigt)")
Sz = (S - S.mean(0)) / (S.std(0) + 1e-9); mS, sS, pS = kors(Sz, lam=30); print(f"  lager 2 som helhet: rho {mS:+.3f} (±{sS:.3f})\n")

# Lager 3: semantiskt (N och fälten)
tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small"); mod = AutoModel.from_pretrained("intfloat/multilingual-e5-small").eval()
def badda(X):
    ut = []
    for k in range(0, len(X), 64):
        b = tok(["query: " + t for t in X[k:k + 64]], padding=True, truncation=True, max_length=256, return_tensors="pt")
        with torch.no_grad(): h = mod(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).float(); ut.append(torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1).numpy())
    return np.concatenate(ut)
N = badda([L("e26/lasning", i)["aterberattelse"] for i in ids]); mN, sN, pN = kors(N, n_ax=30)
FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
F = np.array([[float({**L("e20/lasning", i), **L("e21/lasning", i)}.get(k) == x) for k, xs in FALT.items() for x in xs] for i in ids])
mF, sF, pF = kors(F, lam=5)
print(f"Lager 3, semantiskt: återberättelse N rho {mN:+.3f} (±{sN:.3f}), sju fält rho {mF:+.3f} (±{sF:.3f})\n")
print("HE28e lagren tillsammans (rangsumma av korsvaliderade förutsägelser):")
for namn, delar in [("N", [pN]), ("N + fält", [pN, pF]), ("N + fält + tekniskt", [pN, pF, pT]), ("N + fält + semantisk-tekniskt", [pN, pF, pS]), ("alla fyra", [pN, pF, pT, pS])]:
    print(f"  {namn:32s} rho {sp(sum(rankdata(cen(p)) for p in delar), y):+.3f}")
mA, sA, pA = kors(np.hstack([N, F * 0.2, T * 0.05, Sz * 0.05]), n_ax=40)
print(f"  allt i en modell (40 axlar)      rho {mA:+.3f} (±{sA:.3f})")
