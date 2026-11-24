# E38: publiceringstakt. data/format/e38/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e38_analys.py
import io, contextlib, json, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
with contextlib.redirect_stdout(io.StringIO()):
    import e32_analys as E
import numpy as np
from scipy.stats import rankdata
rng = np.random.default_rng(38); D = E.D

def bygg(listor, behall):
    out = []
    for k, L in listor.items():
        L = sorted([x for x in L if (x.get("visningar") or 0) > 0 and x.get("datum")], key=lambda x: x["datum"])
        if len(L) < 7: continue
        v = np.log([x["visningar"] for x in L]); U = E.utfall(L)
        d = [date.fromisoformat(x["datum"]) for x in L]
        for i, x in enumerate(L):
            if np.isnan(U[i]) or not behall(f"{k}-{x['id']}") or i == 0: continue
            nx = (d[i + 1] - d[i]).days if i + 1 < len(L) else np.nan
            out.append((k, U[i], (d[i] - d[i - 1]).days, nx, d[i].weekday()))
    return out

bank = {k: L for k, (h, L) in E.K.items()}
osedda = set(json.load(open(D / "format" / "e34" / "osedda.json")))
ny = {json.loads(f.read_text(encoding="utf-8"))["konto"]: json.loads(f.read_text(encoding="utf-8"))["klipp"] for f in (D / "format" / "e34" / "listor").glob("*.json")}
S = {"bank": bygg(bank, lambda i: True), "osedda": bygg(ny, lambda i: i in osedda)}

def prho(ka, x, y, n=4000):
    ok = ~np.isnan(x); ka, x, y = ka[ok], x[ok], y[ok]
    def cen(v):
        v = np.asarray(v, float).copy()
        for k in set(ka): m = ka == k; v[m] -= v[m].mean()
        return v
    xr, yr = cen(rankdata(x)), cen(rankdata(y)); r0 = np.corrcoef(xr, yr)[0, 1]; c = 0; g = [np.where(ka == k)[0] for k in set(ka)]
    for _ in range(n):
        yy = yr.copy()
        for gg in g: yy[gg] = rng.permutation(yy[gg])
        c += abs(np.corrcoef(xr, yy)[0, 1]) >= abs(r0)
    return r0, (c + 1) / (n + 1), ok.sum()

res = {}
for s, R in S.items():
    ka = np.array([r[0] for r in R]); u = np.array([r[1] for r in R]); g = np.array([r[2] for r in R], float); nx = np.array([r[3] for r in R], float); wd = np.array([r[4] for r in R])
    uc = u.copy()
    for k in set(ka): m = ka == k; uc[m] -= uc[m].mean()
    a = prho(ka, np.log1p(g), u); c_ = prho(ka, np.log1p(nx), u)
    m0 = g == 0; d0 = uc[m0].mean() - uc[~m0].mean()
    c = 0; grp = [np.where(ka == k)[0] for k in set(ka)]
    for _ in range(4000):
        mm = m0.copy()
        for gg in grp: mm[gg] = rng.permutation(mm[gg])
        c += abs(uc[mm].mean() - uc[~mm].mean()) >= abs(d0)
    res[s] = (a, (np.exp(d0), (c + 1) / 4001, m0.sum()), c_)
    print(f"{s}: {len(R)} klipp, {len(set(ka))} konton, median glapp {np.median(g):.0f} dagar")
    print(f"  HE38a log1p(glapp) mot u: rho {a[0]:+.3f} p {a[1]:.4f}")
    print(f"  HE38b samma dag (n {m0.sum()}): ×{np.exp(d0):.2f} p {(c + 1) / 4001:.4f}")
    print(f"  HE38c dagar till nästa: rho {c_[0]:+.3f} p {c_[1]:.4f}")
    kl = np.digitize(g, [1, 2, 4, 8]); print("  klasser 0/1/2–3/4–7/8+: " + "  ".join(f"×{np.exp(uc[kl == j].mean()):.2f} (n {(kl == j).sum()})" for j in range(5)))
    print("  veckodag mån–sön: " + "  ".join(f"×{np.exp(uc[wd == j].mean()):.2f}" for j in range(7)))
a1, a2 = res["bank"][0], res["osedda"][0]; b1, b2 = res["bank"][1], res["osedda"][1]; c1, c2 = res["bank"][2], res["osedda"][2]
print(f"\n=> HE38a {'HÅLLER' if a1[0] > 0 and a2[0] > 0 and a1[1] < .05 and a2[1] < .05 else 'FALLER'}   HE38b {'HÅLLER' if b1[0] < 1 and b2[0] < 1 and b1[1] < .05 and b2[1] < .05 else 'FALLER'}   HE38c {'HÅLLER' if abs(c1[0]) < .03 and abs(c2[0]) < .03 else 'FALLER'}")
