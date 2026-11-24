# E30: tal (Silero VAD) mot utfall inom konto. HE30a–d enligt data/format/e30/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e30_analys.py
import json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
ROT = Path(__file__).resolve().parents[2] / "data" / "format"
rng = np.random.default_rng(30)
jl = lambda p: {json.loads(l)["id"]: json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}
R = jl(ROT / "e15" / "motorer-flash.jsonl"); TAL = jl(ROT / "e30" / "tal.jsonl"); TEK = jl(ROT / "e28" / "tek.jsonl")
nya = set(json.loads((ROT / "e19" / "ids.json").read_text()))
ids = [i for i in R if i in TAL and R[i].get("u") is not None and TAL[i]["langd"] >= 0.5]
konto = np.array([R[i]["konto"] for i in ids]); u = np.array([R[i]["u"] for i in ids], float)
def cen(x, m=None):
    x = np.asarray(x, float).copy()
    for k in set(konto): mm = konto == k; x[mm] -= x[mm].mean()
    return x
rk = lambda x: cen(rankdata(x))
def perm(x, mask, z=None, n=5000):
    # rangkorrelation inom konto, valfritt partiell mot z; permutation inom konto
    xs, ys = rk(x)[mask], rk(u)[mask]; ks = konto[mask]
    if z is not None:
        Z = np.column_stack([rk(c)[mask] for c in z]); xs = xs - Z @ np.linalg.lstsq(Z, xs, rcond=None)[0]; ys = ys - Z @ np.linalg.lstsq(Z, ys, rcond=None)[0]
    r0 = np.corrcoef(xs, ys)[0, 1]; c = 0
    for _ in range(n):
        yy = ys.copy()
        for k in set(ks): m = ks == k; yy[m] = rng.permutation(yy[m])
        c += abs(np.corrcoef(xs, yy)[0, 1]) >= abs(r0)
    return r0, (c + 1) / (n + 1)
f = lambda k: np.array([TAL[i][k] if TAL[i][k] is not None else TAL[i]["langd"] for i in ids], float)
seg, andel, pers, forsta = f("tal_segment"), f("tal_andel"), f("tal_per_s"), f("forsta_tal")
L = np.log1p([TAL[i]["langd"] for i in ids])
ny = np.array([i in nya for i in ids]); alla = np.ones(len(ids), bool)
print(f"{len(ids)} klipp ({ny.sum()} replikering, {(~ny).sum()} bibliotek), {len(set(konto))} konton")
print(f"tal_andel median {np.median(andel):.2f}; under 0,1: {np.mean(andel < 0.1):.0%}; tal_segment median {np.median(seg):.0f}\n")
print("                      alla               bibliotek          replikering")
for namn, x, z in [("HE30a tal_segment", seg, None), ("HE30b segment | längd", seg, [L]), ("tal_andel", andel, None), ("tal_per_s", pers, None), ("forsta_tal", forsta, None), ("längd", L, None), ("längd | segment", L, [seg])]:
    print(f"  {namn:22s}" + "".join(f"  rho {r:+.3f} p {p:.3f}" for r, p in (perm(x, m, z, 2000) for m in (alla, ~ny, ny))))
# HE30c: klipp utan tal mot övriga, medel av utfall inom konto
yc = cen(u); tyst = andel < 0.1
r, p = perm(tyst.astype(float), alla)
print(f"\nHE30c utan tal (n={tyst.sum()}): utfall inom konto {yc[tyst].mean():+.3f} mot {yc[~tyst].mean():+.3f} (×{np.exp(yc[tyst].mean() - yc[~tyst].mean()):.2f}), rho {r:+.3f} p {p:.4f}")
# HE30d: giltighet mot Flashs replikantal i E28
E28 = ROT / "e28" / "lasning"; har = [i for i in ids if (E28 / f"{i}.json").exists()]
if har:
    rep = np.array([sum(s["repliker"] for s in json.loads((E28 / f"{i}.json").read_text(encoding="utf-8"))["scener"]) for i in har])
    ix = [ids.index(i) for i in har]
    c = lambda a, b: np.corrcoef(rankdata(a), rankdata(b))[0, 1]
    print(f"HE30d giltighet (n={len(har)}): rho(tal_segment, repliker) {c(seg[ix], rep):+.3f}, rho(tal_andel, repliker) {c(andel[ix], rep):+.3f}")
    ing = np.array([json.loads((E28 / f"{i}.json").read_text(encoding="utf-8"))["manus"] == "inget" for i in har])
    print(f"  tal_andel när manus = inget {np.median(andel[ix][ing]):.2f}, annars {np.median(andel[ix][~ing]):.2f}")
# Lånat ljud (E21) mot VAD
E21 = ROT / "e21" / "lasning"; h21 = [i for i in ids if (E21 / f"{i}.json").exists()]
if h21:
    lan = np.array([json.loads((E21 / f"{i}.json").read_text(encoding="utf-8")).get("uttryck") == "lanat" for i in h21]); ix = [ids.index(i) for i in h21]
    print(f"Lånat ljud (E21, n={len(h21)}): tal_segment median {np.median(seg[ix][lan]):.0f} mot eget {np.median(seg[ix][~lan]):.0f}; tal_andel {np.median(andel[ix][lan]):.2f} mot {np.median(andel[ix][~lan]):.2f}")
