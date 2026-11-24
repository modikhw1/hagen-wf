# E33: vad driver kommentarer och delningar med visningarna konstanta. data/format/e33/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e33_analys.py
import io, contextlib, sys, re, json
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
with contextlib.redirect_stdout(io.StringIO()):
    import e32_analys as E
import numpy as np
from scipy.stats import rankdata
rad, cen, ROT = E.rad, E.cen, E.ROT; rng = np.random.default_rng(33)

alla = [i for i in rad if not np.isnan(rad[i]["u"]) and not np.isnan(rad[i]["komm"])]
ka = np.array([rad[i]["konto"] for i in alla]); tx = [rad[i]["text"].lower() for i in alla]
uc = cen(np.array([rad[i]["u"] for i in alla]), ka)
def res(t):
    v = cen(np.array([rad[i][t] for i in alla]), ka); b = (v @ uc) / (uc @ uc); return v - b * uc, b
Y = {}
for t in ["gill", "komm", "dela"]:
    Y[t], b = res(t); print(f"{t}: lutning mot u {b:+.2f}")
Y["u"] = uc
grp = {k: np.where(ka == k)[0] for k in set(ka)}

def pb(m, yv, n=4000, sub=None):
    ix = np.arange(len(yv)) if sub is None else np.where(sub)[0]
    m, yv = m[ix], yv[ix]; kk = ka[ix]; d0 = yv[m].mean() - yv[~m].mean(); c = 0; g = [np.where(kk == k)[0] for k in set(kk)]
    for _ in range(n):
        mm = m.copy()
        for gg in g: mm[gg] = rng.permutation(mm[gg])
        c += abs(yv[mm].mean() - yv[~mm].mean()) >= abs(d0)
    return np.exp(d0), (c + 1) / (n + 1)

has = lambda p: np.array([bool(re.search(p, t)) for t in tx])
H = [("HE33a", "fråga '?'", np.array(["?" in t for t in tx]), "komm", lambda f: f > 1),
     ("HE33b", "uppmaning kommentera", has(r"kommentera|\bskriv|\bvem\b|vilken|vilket|vad tycker|comment|tell us|\bwhich\b"), "komm", lambda f: f > 1),
     ("HE33c", "tagga/skicka", has(r"tagga|\btag\b|skicka|\bsend\b|\bdela\b"), "dela", lambda f: f > 1),
     ("HE33d", "pris", has(r"\d\s*kr\b|\d\s*%|gratis"), "komm", lambda f: f > 1),
     ("HE33f", "tävling", has(r"\bvinn|tävling|giveaway|vinnare|\bwin\b"), "komm", lambda f: f > 2)]
print(f"\n{len(alla)} klipp, {len(set(ka))} konton. Faktor per visning, u konstant (u-kolumnen = visningar)")
for h, n, m, mal, ok in H:
    rr = {t: pb(m, Y[t]) for t in ["u", "gill", "komm", "dela"]}
    f, p = rr[mal]
    print(f"  {h} {n:22s} n {m.sum():5d}  " + "  ".join(f"{t} ×{rr[t][0]:.2f} (p {rr[t][1]:.3f})" for t in rr) + f"  => {'HÅLLER' if ok(f) and p < 0.05 else 'FALLER'}")

# HE33e tal
TAL = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e30" / "tal.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
sub = np.array([i in TAL and TAL[i]["langd"] >= 0.5 for i in alla])
x = np.array([np.log1p(TAL[i]["tal_segment"]) if s else 0 for i, s in zip(alla, sub)])
def prho(x, yv, sub, n=4000):
    ix = np.where(sub)[0]; kk = ka[ix]; xr = cen(rankdata(x[ix]), kk); yr = cen(rankdata(yv[ix]), kk); r0 = np.corrcoef(xr, yr)[0, 1]; c = 0
    g = [np.where(kk == k)[0] for k in set(kk)]
    for _ in range(n):
        yy = yr.copy()
        for gg in g: yy[gg] = rng.permutation(yy[gg])
        c += abs(np.corrcoef(xr, yy)[0, 1]) >= abs(r0)
    return r0, (c + 1) / (n + 1)
rr = {t: prho(x, Y[t], sub) for t in ["u", "gill", "komm", "dela"]}
print(f"  HE33e talsegment (n {sub.sum()})  " + "  ".join(f"{t} rho {rr[t][0]:+.3f} (p {rr[t][1]:.3f})" for t in rr) + f"  => {'HÅLLER' if rr['komm'][0] < 0 and rr['komm'][1] < 0.05 else 'FALLER'}")

# utforskande: fält och längd
FV = {i: E.las(i) for i in alla if i in E.FV}; sf = np.array([i in FV for i in alla])
print("\nUtforskande: fält (andel = värdet mot övriga, inom konto)")
for k, xs in E.FALT.items():
    for v in xs:
        m = np.array([FV.get(i, {}).get(k) == v for i in alla])
        if m.sum() >= 40: print(f"  {k}={v:18s} n {m.sum():4d}  " + "  ".join(f"{t} ×{np.exp(Y[t][m].mean() - Y[t][sf & ~m].mean()):.2f}" for t in ["u", "gill", "komm", "dela"]))
L = np.array([E.K[rad[i]["konto"]][1][rad[i]["pos"]].get("langd") or np.nan for i in alla], float); sl = ~np.isnan(L)
print("  längd (log) rho: " + "  ".join(f"{t} {prho(np.log(np.where(sl, L, 1)), Y[t], sl, 500)[0]:+.3f}" for t in ["u", "gill", "komm", "dela"]))

# utforskande: ord, upptäckt i halva kontona, prövat i andra
kon = sorted(set(ka)); A_ = set(kon[0::2]); hA = np.array([k in A_ for k in ka])
tok = [set(re.findall(r"#?[a-zåäöæø]{3,}|\d+\s*kr|\?", t)) for t in tx]
cnt = Counter(w for s in tok for w in s); ord_ = [w for w, c in cnt.items() if c >= 40]
for t in ["komm", "dela"]:
    eff = []
    for w in ord_:
        m = np.array([w in s for s in tok])
        if m[hA].sum() >= 15 and m[~hA].sum() >= 15:
            eA = Y[t][hA & m].mean() - Y[t][hA & ~m].mean(); eB = Y[t][~hA & m].mean() - Y[t][~hA & ~m].mean(); eff.append((eA, eB, w, m.sum()))
    eff.sort()
    top = eff[:10] + eff[-10:]; agree = sum(np.sign(a) == np.sign(b) for a, b, *_ in top)
    print(f"\nOrd mot {t} (upptäckt i halva A, prövat i B): {agree} av {len(top)} samma tecken; rho A mot B över alla {len(eff)} ord {np.corrcoef(rankdata([e[0] for e in eff]), rankdata([e[1] for e in eff]))[0, 1]:+.2f}")
    print("  lägst: " + ", ".join(f"{w} ×{np.exp(a):.2f}/×{np.exp(b):.2f}" for a, b, w, n in eff[:10]))
    print("  högst: " + ", ".join(f"{w} ×{np.exp(a):.2f}/×{np.exp(b):.2f}" for a, b, w, n in eff[-10:][::-1]))
