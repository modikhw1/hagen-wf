# E39: lokal ingestpoäng med två axlar, fryst på banken, prövad på osedda. data/format/e39/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e39_analys.py
import io, contextlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
with contextlib.redirect_stdout(io.StringIO()):
    import e32_analys as B
    import e34_analys as O
import numpy as np
from scipy.stats import rankdata
ROT = B.ROT
jl = lambda p: {json.loads(l)["id"]: json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}
TB, TO = jl(ROT / "e30" / "tal.jsonl"), jl(ROT / "e34" / "tal.jsonl")
KOM = r"kommentera|\bskriv|\bvem\b|vilken|vilket|vad tycker|comment|tell us|\bwhich\b"; TAG = r"tagga|\btag\b|skicka|\bsend\b|\bdela\b"; TAV = r"\bvinn|tävling|giveaway|vinnare|\bwin\b"

def samdag(listor):
    s = {}
    for k, L in listor.items():
        L = sorted([x for x in L if x.get("datum")], key=lambda x: x["datum"])
        for i, x in enumerate(L):
            s[f"{k}-{x['id']}"] = float((i > 0 and L[i - 1]["datum"] == x["datum"]) or (i + 1 < len(L) and L[i + 1]["datum"] == x["datum"]))
    return s
SB = samdag({k: L for k, (h, L) in B.K.items()})
SO = samdag({json.loads(f.read_text(encoding="utf-8"))["konto"]: json.loads(f.read_text(encoding="utf-8"))["klipp"] for f in (ROT / "e34" / "listor").glob("*.json")})
def sardrag(i, tal, text, sd):
    t = tal[i]; tx = text.lower()
    return [np.log1p(t["tal_segment"]), t["tal_andel"], float(t["tal_segment"] == 0), np.log(max(t["langd"], 1)), sd.get(i, 0.0), float(bool(re.search(KOM, tx))), float(bool(re.search(TAG, tx))), float(bool(re.search(TAV, tx)))]
NAMN = ["talsegment", "tal_andel", "inget tal", "längd", "samma dag", "uppmaning", "tagga/skicka", "tävling"]

def mangd(rows):  # rows: (id, konto, text, u, komm, dela, tal, sd)
    ka = np.array([r[1] for r in rows]); X = np.array([sardrag(r[0], r[6], r[2], r[7]) for r in rows])
    def cen(v):
        v = np.asarray(v, float).copy()
        for k in set(ka): m = ka == k; v[m] -= np.nanmean(v[m], 0)
        return v
    u = cen([r[3] for r in rows]); resp = []
    for j in (4, 5):
        v = cen([r[j] for r in rows]); ok = ~np.isnan(v); v[ok] -= (v[ok] @ u[ok]) / (u[ok] @ u[ok]) * u[ok]; resp.append(v)
    return ka, cen(X), u, np.nanmean(np.vstack(resp), 0)
rb = [(i, B.rad[i]["konto"], B.rad[i]["text"], B.rad[i]["u"], B.rad[i]["komm"], B.rad[i]["dela"], TB, SB) for i in B.rad if i in TB and TB[i]["langd"] >= 0.5 and not np.isnan(B.rad[i]["u"])]
ro = [(r["id"], r["konto"], r["text"], r["u"], r["komm"], r["dela"], TO, SO) for r in O.rad if r["id"] in TO and TO[r["id"]]["langd"] >= 0.5]
kb, Xb, ub, rpb = mangd(rb); ko, Xo, uo, rpo = mangd(ro)
s = Xb.std(0) + 1e-9; Xb, Xo = Xb / s, Xo / s
fit = lambda X, y: np.linalg.solve(X.T @ X + 5 * np.eye(X.shape[1]), X.T @ y)
ok = ~np.isnan(rpb); wu, wr = fit(Xb, ub), fit(Xb[ok], rpb[ok])
print(f"E39: anpassad på {len(rb)} bankklipp, prövad på {len(ro)} osedda")
print("  vikter räckvidd: " + "  ".join(f"{n} {w:+.2f}" for n, w in zip(NAMN, wu)))
print("  vikter respons:  " + "  ".join(f"{n} {w:+.2f}" for n, w in zip(NAMN, wr)))
def rho(ka, a, b):
    ok = ~np.isnan(b); ka, a, b = ka[ok], a[ok], b[ok]
    def c(v):
        v = v.astype(float).copy()
        for k in set(ka): m = ka == k; v[m] -= v[m].mean()
        return v
    return np.corrcoef(c(rankdata(a)), c(rankdata(b)))[0, 1]
pu, pr = Xo @ wu, Xo @ wr
a, b, c = rho(ko, pu, uo), rho(ko, pr, rpo), rho(ko, pu, pr)
rng = np.random.default_rng(39); kn = sorted(set(ko)); bs = []
for _ in range(1000):
    v = rng.choice(kn, len(kn)); jj = np.concatenate([np.where(ko == k)[0] for k in v]); bs.append((rho(ko[jj], pu[jj], uo[jj]), rho(ko[jj], pr[jj], rpo[jj])))
bs = np.array(bs)
print(f"  bank (i urval): räckvidd {rho(kb, Xb @ wu, ub):+.3f}, respons {rho(kb, Xb @ wr, rpb):+.3f}")
print(f"  HE39a räckviddspoäng mot u, osedda: {a:+.3f} (95 % över konton {np.percentile(bs[:, 0], 2.5):+.3f} till {np.percentile(bs[:, 0], 97.5):+.3f})  => {'HÅLLER' if a >= 0.12 else 'FALLER'}")
print(f"  HE39b responspoäng mot respons, osedda: {b:+.3f} (95 % {np.percentile(bs[:, 1], 2.5):+.3f} till {np.percentile(bs[:, 1], 97.5):+.3f})  => {'HÅLLER' if b >= 0.08 else 'FALLER'}")
print(f"  HE39c räckvidd mot respons, osedda: {c:+.3f}  => {'HÅLLER' if abs(c) < 0.3 else 'FALLER'}")
print(f"  korsat: räckviddspoäng mot respons {rho(ko, pu, rpo):+.3f}, responspoäng mot u {rho(ko, pr, uo):+.3f}")
