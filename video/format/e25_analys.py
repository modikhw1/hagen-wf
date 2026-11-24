# E25: negativ input. HE25a copy per villkor och grupp, HE25b fyllnad i tomma poster, HE25c distinktion, HE25d likhet med B.
#   HF_HUB_OFFLINE=1 ../scen/.venv/Scripts/python.exe -u format/e25_analys.py
import json, re
from pathlib import Path
import numpy as np, torch
from transformers import AutoTokenizer, AutoModel

ROT = Path(__file__).resolve().parents[2] / "data" / "format"; E = ROT / "e25"
U = json.loads((E / "urval.json").read_text()); grupp = {i: "lag" for i in U["lag"]} | {i: "hog" for i in U["hog"]}
COPY = set(json.loads((ROT / "e23" / "copyord.json").read_text(encoding="utf-8")))
R = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
V = ["p0", "p40", "p60", "p70"]
L = {v: {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (E / v).glob("*.json")} for v in V}
ids = [i for i in grupp if all(i in L[v] for v in V)]
print(f"{len(ids)} klipp med alla fyra villkor ({sum(grupp[i] == 'lag' for i in ids)} lite innehåll, {sum(grupp[i] == 'hog' for i in ids)} idé/person)\n")
ord_ = lambda t: re.findall(r"[a-zåäöé]+", t.lower())
def upp(t):
    w = ord_(t); s = " ".join(w); return 100 * (sum(x in COPY for x in w) + s.count("visa upp") + s.count("visar upp")) / max(len(w), 1)
verklig = lambda v, i: " ".join(p["vad"] for p in L[v][i]["poster"] if p["post"] in L[v][i]["verkliga"])
tomma = lambda v, i: [p["vad"] for p in L[v][i]["poster"] if p["post"] not in L[v][i]["verkliga"]]
TOM = re.compile(r"svart|tom|ingenting|inget innehåll|inget att se|ingen bild|blank|mörk", re.I)

TEXT = {"A (motor)": [R[i]["hel"] for i in ids]} | {v: [verklig(v, i) for i in ids] for v in V}
Bp = ROT / "e23" / "B"; harB = [i for i in ids if (Bp / f"{i}.json").exists()]
print("HE25a copy (copyord per 100 ord) i de verkliga posternas text")
for n, T in TEXT.items():
    x = np.array([upp(t) for t in T]); g = np.array([grupp[i] for i in ids])
    print(f"  {n:10s} alla {x.mean():.1f}   lite innehåll {x[g == 'lag'].mean():.1f}   idé/person {x[g == 'hog'].mean():.1f}   ord {np.mean([len(ord_(t)) for t in T]):.0f}")
print("\nHE25b tomma poster som beskrivs med innehåll (andel), per villkor och grupp")
for v in V[1:]:
    for g in ["lag", "hog"]:
        t = [x for i in ids if grupp[i] == g for x in tomma(v, i)]
        print(f"  {v:4s} {g}: {np.mean([not TOM.search(x) for x in t]):.3f} av {len(t)}", end="   ")
    print()
fyll = [x for v in V[1:] for i in ids for x in tomma(v, i) if not TOM.search(x)]
if fyll: print("  exempel på fyllnad: " + " | ".join(fyll[:6]))

tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small"); mod = AutoModel.from_pretrained("intfloat/multilingual-e5-small").eval()
def badda(T):
    ut = []
    for k in range(0, len(T), 64):
        b = tok(["query: " + t for t in T[k:k + 64]], padding=True, truncation=True, max_length=256, return_tensors="pt")
        with torch.no_grad(): h = mod(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).float(); ut.append(torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1).numpy())
    return np.concatenate(ut)
VEK = {n: badda(T) for n, T in TEXT.items()}
y = np.array([grupp[i] == "hog" for i in ids])
def auc_knn(X, k=7):
    S = X @ X.T; np.fill_diagonal(S, -9); s = np.array([y[np.argsort(S[j])[-k:]].mean() for j in range(len(y))])
    a, b = s[y], s[~y]; return np.mean([(p > q) + 0.5 * (p == q) for p in a for q in b])
print("\nHE25c hur väl texten skiljer lite innehåll från idé/person (närmaste grannar, AUC):")
for n in VEK: print(f"  {n:10s} {auc_knn(VEK[n]):.3f}")
if harB:
    ix = [ids.index(i) for i in harB]
    B = badda([f"{json.loads((Bp / f'{i}.json').read_text(encoding='utf-8'))['vad']}" for i in harB])
    print(f"\nHE25d likhet med den bokstavliga läsningen B ({len(harB)} klipp):  " + "  ".join(f"{n} {np.mean(np.sum(VEK[n][ix] * B, 1)):.3f}" for n in VEK))
print("\nExempel:")
for i in [ids[0], ids[-1]]:
    print(f"  [{grupp[i]}] {i}")
    for n, T in TEXT.items(): print(f"    {n:10s} {T[ids.index(i)][:230]}")
