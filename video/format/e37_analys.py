# E37: personer i bild mot utfall. data/format/e37/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e37_analys.py
import io, contextlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
with contextlib.redirect_stdout(io.StringIO()):
    import e32_analys as B
import numpy as np
from scipy.stats import rankdata
rng = np.random.default_rng(37); ROT = B.ROT
P = {json.loads(l)["id"]: json.loads(l)["antal"] for l in (ROT / "e37" / "personer.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
TAL = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e30" / "tal.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
ids = [i for i in P if P[i] and i in B.rad and not np.isnan(B.rad[i]["u"])]
ka = np.array([B.rad[i]["konto"] for i in ids]); ny = np.array([i in B.nya for i in ids])
def cen(v, m=None):
    v = np.asarray(v, float).copy()
    for k in set(ka): s = ka == k; v[s] -= v[s].mean()
    return v
u = cen([B.rad[i]["u"] for i in ids])
tva = np.array([np.mean([a >= 2 for a in P[i]]) for i in ids]); en = np.array([np.mean([a >= 1 for a in P[i]]) for i in ids]); mx = np.array([max(P[i]) for i in ids])
ingen = mx == 0
def prho(sel, x, z=None, n=4000):
    kk = ka[sel]; xr = rankdata(x[sel]); yr = rankdata(u[sel])
    def c(v):
        v = v.astype(float).copy()
        for k in set(kk): s = kk == k; v[s] -= v[s].mean()
        return v
    xr, yr = c(xr), c(yr)
    if z is not None:
        zs = c(rankdata(z[sel])); f = lambda a: a - zs * (a @ zs) / (zs @ zs); xr, yr = f(xr), f(yr)
    r0 = np.corrcoef(xr, yr)[0, 1]; cnt = 0; g = [np.where(kk == k)[0] for k in set(kk)]
    for _ in range(n):
        yy = yr.copy()
        for gg in g: yy[gg] = rng.permutation(yy[gg])
        if z is not None: yy = yy - zs * (yy @ zs) / (zs @ zs)
        cnt += abs(np.corrcoef(xr, yy)[0, 1]) >= abs(r0)
    return r0, (cnt + 1) / (n + 1)
def pbin(sel, m, n=4000):
    kk, mm0, yy = ka[sel], m[sel], u[sel]; d0 = yy[mm0].mean() - yy[~mm0].mean(); c = 0; g = [np.where(kk == k)[0] for k in set(kk)]
    for _ in range(n):
        mm = mm0.copy()
        for gg in g: mm[gg] = rng.permutation(mm[gg])
        c += abs(yy[mm].mean() - yy[~mm].mean()) >= abs(d0)
    return np.exp(d0), (c + 1) / (n + 1), int(mm0.sum())
print(f"E37: {len(ids)} klipp ({ny.sum()} replikering). Andel klipp: ingen person {ingen.mean():.0%}, minst två i någon ruta {np.mean(mx >= 2):.0%}")
for namn, sel in [("replikering", ny), ("bibliotek", ~ny)]:
    a = prho(sel, tva); b = pbin(sel, ingen); e1 = prho(sel, en, n=1000); m_ = prho(sel, mx.astype(float), n=1000)
    print(f"  {namn:12s} andel ≥2 rho {a[0]:+.3f} (p {a[1]:.4f})   ingen person ×{b[0]:.2f} (p {b[1]:.4f}, n {b[2]})   andel ≥1 {e1[0]:+.3f}   max antal {m_[0]:+.3f}")
    if namn == "replikering": print(f"  => HE37a {'HÅLLER' if a[0] > 0 and a[1] < .05 else 'FALLER'}   HE37b {'HÅLLER' if b[0] < 1 and b[1] < .05 else 'FALLER'}")
F = {i: B.las(i) for i in ids if (ROT / "e20/lasning" / f"{i}.json").exists() and (ROT / "e21/lasning" / f"{i}.json").exists()}
ix = {i: n for n, i in enumerate(ids)}
pos = [tva[ix[i]] for i, f in F.items() if f.get("relation") in ("gast_personal", "personal_personal")]
neg = [tva[ix[i]] for i, f in F.items() if f.get("relation") not in ("gast_personal", "personal_personal")]
rk = rankdata(pos + neg); auc = (rk[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
print(f"  HE37c AUC andel ≥2 för möte (n {len(pos)}) mot övrigt (n {len(neg)}): {auc:.3f}  => {'HÅLLER' if auc > 0.6 else 'FALLER'}")
st = np.array([i in TAL and TAL[i]["langd"] >= 0.5 for i in ids]); ts = np.array([np.log1p(TAL[i]["tal_segment"]) if s else 0 for i, s in zip(ids, st)])
a = prho(ny & st, tva, ts); print(f"  HE37d andel ≥2 | talsegment (replikering, n {(ny & st).sum()}): rho {a[0]:+.3f} p {a[1]:.4f}  => {'HÅLLER' if a[0] > 0 and a[1] < .05 else 'FALLER'}")
a = prho(~ny & st, tva, ts, 1000); print(f"    bibliotek: {a[0]:+.3f}")
