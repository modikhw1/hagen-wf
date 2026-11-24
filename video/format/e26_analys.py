# E26: huvudrum mellan återberättelse och säljtext. HE26a–e.
#   HF_HUB_OFFLINE=1 ../scen/.venv/Scripts/python.exe -u format/e26_analys.py
import json, re
from pathlib import Path
import numpy as np, torch
from scipy.stats import rankdata, mannwhitneyu
from transformers import AutoTokenizer, AutoModel

ROT = Path(__file__).resolve().parents[2] / "data" / "format"; E = ROT / "e26"
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1]); rng = np.random.default_rng(26)
U = json.loads((E / "urval.json").read_text())
L = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (E / "lasning").glob("*.json")}
R = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
COPY = set(json.loads((ROT / "e23" / "copyord.json").read_text(encoding="utf-8")))
ord_ = lambda t: re.findall(r"[a-zåäöé]+", t.lower())
def upp(t):
    w = ord_(t); s = " ".join(w); return 100 * (sum(x in COPY for x in w) + s.count("visa upp") + s.count("visar upp")) / max(len(w), 1)
tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small"); mod = AutoModel.from_pretrained("intfloat/multilingual-e5-small").eval()
def badda(T):
    ut = []
    for k in range(0, len(T), 64):
        b = tok(["query: " + t for t in T[k:k + 64]], padding=True, truncation=True, max_length=256, return_tensors="pt")
        with torch.no_grad(): h = mod(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).float(); ut.append(torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1).numpy())
    return np.concatenate(ut)
ids = [i for i in L]
N, S = badda([L[i]["aterberattelse"] for i in ids]), badda([L[i]["saljtext"] for i in ids])
AV = {i: float(1 - N[j] @ S[j]) for j, i in enumerate(ids)}; TA = {i: L[i]["tackning"] for i in ids}
print(f"{len(ids)} klipp lästa. Täckning: medel {np.mean(list(TA.values())):.0f}, spridning {np.std(list(TA.values())):.1f}, min {min(TA.values())}, max {max(TA.values())}")
print(f"Avstånd återberättelse–säljtext: medel {np.mean(list(AV.values())):.3f}, spridning {np.std(list(AV.values())):.3f};  samband täckning–avstånd rho {sp(list(TA.values()), list(AV.values())):+.2f}\n")

rep = [i for i in U["replikering"] if i in L and R.get(i, {}).get("u") is not None]
kon = np.array([R[i]["konto"] for i in rep]); u = np.array([R[i]["u"] for i in rep])
def cen(x):
    x = np.asarray(x, float).copy()
    for k in set(kon): m = kon == k; x[m] -= x[m].mean()
    return x
def perm(x, n=5000):
    y = cen(u); x = cen(x); r0 = sp(x, y); c = 0
    for _ in range(n):
        z = y.copy()
        for k in set(kon): m = kon == k; z[m] = rng.permutation(z[m])
        c += abs(sp(x, z)) >= abs(r0)
    return r0, (c + 1) / (n + 1)
print(f"Replikeringen: {len(rep)} klipp med utfall, {len(set(kon))} konton")
r, p = perm([TA[i] for i in rep]); print(f"  HE26a täckning mot utfall inom konto:  rho {r:+.3f}  p {p:.4f}")
r, p = perm([AV[i] for i in rep]); print(f"  HE26b avstånd mot utfall inom konto:   rho {r:+.3f}  p {p:.4f}")
b = np.load(ROT / "e21" / "faltvikter.npy")
FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
def falt(i):
    a, c = ROT / "e20" / "lasning" / f"{i}.json", ROT / "e21" / "lasning" / f"{i}.json"
    f = {**json.loads(a.read_text(encoding="utf-8")), **json.loads(c.read_text(encoding="utf-8"))}
    return np.array([float(f.get(k) == x) for k, xs in FALT.items() for x in xs]) @ b
pf = cen([falt(i) for i in rep]); t = cen([TA[i] for i in rep]); rest = t - np.polyval(np.polyfit(pf, t, 1), pf)
r, p = perm(rest); print(f"  HE26d täckning efter de sju fälten:    rho {r:+.3f}  p {p:.4f}   (fälten själva {sp(pf, cen(u)):+.3f})")
print("\nBiblioteket:")
for n, M in [("täckning", TA), ("avstånd", AV)]:
    k, o = [M[i] for i in U["karna"] if i in M], [M[i] for i in U["ute"] if i in M]
    print(f"  {n:9s} kärna {np.mean(k):.3f} (n {len(k)})  ute {np.mean(o):.3f} (n {len(o)})  Mann–Whitney p {mannwhitneyu(k, o).pvalue:.4f}" + ("   ← HE26c" if n == "täckning" else ""))
A = [R[i]["hel"] for i in ids if i in R]; Ni = [L[i]["aterberattelse"] for i in ids if i in R]; Si = [L[i]["saljtext"] for i in ids if i in R]
cv = lambda x: np.std(x) / np.mean(x)
ua, un, us = [upp(t) for t in A], [upp(t) for t in Ni], [upp(t) for t in Si]
print(f"\nHE26e copyindex (medel / variationskoefficient):  motor A {np.mean(ua):.1f} / {cv(ua):.2f}   återberättelse {np.mean(un):.1f} / {cv(un):.2f}   säljtext {np.mean(us):.1f} / {cv(us):.2f}")
print("\nStörst och minst huvudrum (avstånd) i replikeringen, med utfall inom konto:")
y = cen(u); o = np.argsort([AV[i] for i in rep])
for t_, J in [("minst", o[:5]), ("störst", o[-5:])]:
    for j in J: print(f"  {t_} {AV[rep[j]]:.3f} täckning {TA[rep[j]]} utfall {y[j]:+.2f}: {L[rep[j]]['aterberattelse'][:150]}")
