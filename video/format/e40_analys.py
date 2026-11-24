# E40: tal + personer i bild, fryst på banken, prövad på osedda. data/format/e40/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e40_analys.py
import io, contextlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
with contextlib.redirect_stdout(io.StringIO()):
    import e32_analys as B
    import e34_analys as O
import numpy as np
from scipy.stats import rankdata
ROT = B.ROT; rng = np.random.default_rng(40)
jl = lambda p: {json.loads(l)["id"]: json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}
TB, TO, PB, PO = jl(ROT / "e30" / "tal.jsonl"), jl(ROT / "e34" / "tal.jsonl"), jl(ROT / "e37" / "personer.jsonl"), jl(ROT / "e40" / "personer.jsonl")
def X(i, T, P):
    a = P[i]["antal"]; return [np.log1p(T[i]["tal_segment"]), np.mean([x >= 1 for x in a]), np.mean([x >= 2 for x in a])]
rb = [(i, B.rad[i]["konto"], B.rad[i]["u"]) for i in B.rad if i in TB and i in PB and PB[i]["antal"] and TB[i]["langd"] >= 0.5 and not np.isnan(B.rad[i]["u"])]
ro = [(r["id"], r["konto"], r["u"]) for r in O.rad if r["id"] in TO and r["id"] in PO and PO[r["id"]]["antal"] and TO[r["id"]]["langd"] >= 0.5]
def mangd(rows, T, P):
    ka = np.array([r[1] for r in rows]); M = np.array([X(r[0], T, P) for r in rows]); u = np.array([r[2] for r in rows], float)
    for k in set(ka): m = ka == k; M[m] -= M[m].mean(0); u[m] -= u[m].mean()
    return ka, M, u
kb, Xb, ub = mangd(rb, TB, PB); ko, Xo, uo = mangd(ro, TO, PO)
s = Xb.std(0); Xb, Xo = Xb / s, Xo / s
w = np.linalg.solve(Xb.T @ Xb + 5 * np.eye(3), Xb.T @ ub)
def c(v, ka):
    v = v.astype(float).copy()
    for k in set(ka): m = ka == k; v[m] -= v[m].mean()
    return v
rho = lambda ka, a, b: np.corrcoef(c(rankdata(a), ka), c(rankdata(b), ka))[0, 1]
def perm(ka, x, y, z=None, n=4000):
    xr, yr = c(rankdata(x), ka), c(rankdata(y), ka)
    if z is not None:
        zs = c(rankdata(z), ka); f = lambda a: a - zs * (a @ zs) / (zs @ zs); xr, yr = f(xr), f(yr)
    r0 = np.corrcoef(xr, yr)[0, 1]; cnt = 0; g = [np.where(ka == k)[0] for k in set(ka)]
    for _ in range(n):
        yy = yr.copy()
        for gg in g: yy[gg] = rng.permutation(yy[gg])
        if z is not None: yy = yy - zs * (yy @ zs) / (zs @ zs)
        cnt += abs(np.corrcoef(xr, yy)[0, 1]) >= abs(r0)
    return r0, (cnt + 1) / (n + 1)
print(f"E40: anpassad på {len(rb)} bankklipp, prövad på {len(ro)} osedda ({len(set(ko))} konton)")
print(f"  vikter: talsegment {w[0]:+.3f}, andel ≥1 {w[1]:+.3f}, andel ≥2 {w[2]:+.3f}")
komb, tal = rho(ko, Xo @ w, uo), rho(ko, Xo[:, 0], uo)
kn = sorted(set(ko)); bs = []
for _ in range(1000):
    v = rng.choice(kn, len(kn)); jj = np.concatenate([np.where(ko == k)[0] for k in v]); bs.append(rho(ko[jj], (Xo @ w)[jj], uo[jj]) - rho(ko[jj], Xo[jj, 0], uo[jj]))
print(f"  HE40a kombinerad {komb:+.3f} mot tal ensamt {tal:+.3f}: skillnad {komb - tal:+.3f} (95 % över konton {np.percentile(bs, 2.5):+.3f} till {np.percentile(bs, 97.5):+.3f})  => {'HÅLLER' if komb - tal >= 0.02 else 'FALLER'}")
a = perm(ko, Xo[:, 2], uo, Xo[:, 0]); print(f"  HE40b andel ≥2 | tal: {a[0]:+.3f} p {a[1]:.4f}  => {'HÅLLER' if a[0] > 0 and a[1] < .05 else 'FALLER'}")
a = perm(ko, Xo[:, 1], uo); print(f"  HE40c andel ≥1: {a[0]:+.3f} p {a[1]:.4f}  => {'HÅLLER' if a[0] > 0 and a[1] < .05 else 'FALLER'}")
a = perm(ko, Xo[:, 2], uo, n=1000); print(f"  (utforskande) andel ≥2 ensam: {a[0]:+.3f};  ingen person i någon ruta: {np.mean([max(PO[r[0]]['antal']) == 0 for r in ro]):.0%}")
