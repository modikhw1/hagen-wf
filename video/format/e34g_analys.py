# E34/HE34g: talsegment mot utfall på osedda klipp. data/format/e34/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e34g_analys.py
import io, contextlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
with contextlib.redirect_stdout(io.StringIO()):
    import e34_analys as E
import numpy as np
from scipy.stats import rankdata
rng = np.random.default_rng(341)
TAL = {json.loads(l)["id"]: json.loads(l) for l in (E.D / "format" / "e34" / "tal.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
ix = [n for n, r in enumerate(E.rad) if r["id"] in TAL and TAL[r["id"]]["langd"] >= 0.5]
ka = E.ka[ix]; Y = {t: E.Y[t][ix] for t in E.Y}
seg = np.array([np.log1p(TAL[E.rad[n]["id"]]["tal_segment"]) for n in ix]); andel = np.array([TAL[E.rad[n]["id"]]["tal_andel"] for n in ix])
L = np.array([TAL[E.rad[n]["id"]]["langd"] for n in ix])
def cen(v):
    v = np.asarray(v, float).copy()
    for k in set(ka): m = ka == k; v[m] -= v[m].mean()
    return v
def prho(x, y, n=5000):
    xr, yr = cen(rankdata(x)), cen(rankdata(y)); r0 = np.corrcoef(xr, yr)[0, 1]; c = 0; g = [np.where(ka == k)[0] for k in set(ka)]
    for _ in range(n):
        yy = yr.copy()
        for gg in g: yy[gg] = rng.permutation(yy[gg])
        c += abs(np.corrcoef(xr, yy)[0, 1]) >= abs(r0)
    return r0, (c + 1) / (n + 1)
print(f"{len(ix)} osedda klipp med tal, {len(set(ka))} konton (E30: talsegment +0,15, bibliotek +0,17, replikering +0,11)")
r, p = prho(seg, Y["u"]); print(f"  HE34g talsegment mot u: rho {r:+.3f} p {p:.4f}  => {'HÅLLER' if r > 0 and p < 0.05 else 'FALLER'}")
# utforskande
kn = sorted(set(ka)); bs = []
for _ in range(1000):
    v = rng.choice(kn, len(kn)); jj = np.concatenate([np.where(ka == k)[0] for k in v])
    bs.append(np.corrcoef(rankdata(seg[jj]), rankdata(Y["u"][jj]))[0, 1])
print(f"  95 % över konton (rå rang, utan centrering i bootstrap): {np.percentile(bs, 2.5):+.3f} till {np.percentile(bs, 97.5):+.3f}")
for t in ["gill", "komm", "dela"]: print(f"  talsegment mot {t} (u konstant): rho {prho(seg, Y[t], 1000)[0]:+.3f}")
print(f"  tal_andel mot u: rho {prho(andel, Y['u'], 1000)[0]:+.3f};  längd mot u: rho {prho(np.log(L), Y['u'], 1000)[0]:+.3f}")
# längd konstant
lc, sc, uc = cen(rankdata(np.log(L))), cen(rankdata(seg)), cen(rankdata(Y["u"]))
res = lambda a, b: a - b * (a @ b) / (b @ b)
print(f"  talsegment | längd: {np.corrcoef(res(sc, lc), res(uc, lc))[0, 1]:+.3f};  längd | talsegment: {np.corrcoef(res(lc, sc), res(uc, sc))[0, 1]:+.3f}")
ut = np.array([TAL[E.rad[n]["id"]]["tal_segment"] == 0 for n in ix])
yc = Y["u"]; print(f"  klipp utan tal: {ut.mean():.0%}, ×{np.exp(yc[ut].mean() - yc[~ut].mean()):.2f} (E30: 31 %, ×0,81)")
for typ in ["aldre", "nyare"]:
    s = np.array([E.rad[n]["typ"] == typ for n in ix])
    if s.sum() > 30: print(f"  bara {typ} (n {s.sum()}): rho {np.corrcoef(rankdata(seg[s]), rankdata(yc[s]))[0, 1]:+.3f}")
