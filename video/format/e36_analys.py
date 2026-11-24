# E36: kommer publiken tillbaka? Efterverkan på kontots följande klipp. data/format/e36/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e36_analys.py
import io, contextlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
with contextlib.redirect_stdout(io.StringIO()):
    import e32_analys as E
import numpy as np
from scipy.stats import rankdata
rad, K = E.rad, E.K; rng = np.random.default_rng(36)

def efter(w):
    for k, (h, L) in K.items():
        v = np.log([x["visningar"] for x in L])
        for i, x in enumerate(L):
            r = rad[f"{k}-{x['id']}"]
            r[f"e{w}"] = np.median(v[i + 1:i + 1 + w]) - np.median(v[i - w:i]) if i >= w and i + w < len(v) else np.nan
for w in (3, 5, 10): efter(w)

def analys(ids, x, namn, w=5, n=4000, ytter=None):
    ka = np.array([rad[i]["konto"] for i in ids]); e = np.array([rad[i][f"e{w}"] for i in ids]); u = np.array([rad[i]["u"] for i in ids])
    ok = ~np.isnan(e) & ~np.isnan(u) & ~np.isnan(x); ka, e, u, x = ka[ok], e[ok], u[ok], x[ok]
    def cen(v):
        v = np.asarray(v, float).copy()
        for k in set(ka): m = ka == k; v[m] -= v[m].mean()
        return v
    res = lambda a, b: a - b * (a @ b) / (b @ b)
    uc = cen(rankdata(u)); xr = res(cen(rankdata(x)), uc) if ytter is None else cen(rankdata(x)); er = res(cen(rankdata(e)), uc) if ytter is None else cen(rankdata(e))
    r0 = np.corrcoef(xr, er)[0, 1]; c = 0; g = [np.where(ka == k)[0] for k in set(ka)]
    for _ in range(n):
        yy = er.copy()
        for gg in g: yy[gg] = rng.permutation(yy[gg])
        c += abs(np.corrcoef(xr, yy)[0, 1]) >= abs(r0)
    print(f"  {namn:42s} n {ok.sum():5d}  rho {r0:+.3f}  p {(c + 1) / (n + 1):.4f}")
    return r0, (c + 1) / (n + 1)

alla = [i for i in rad if not np.isnan(rad[i]["u"])]
print("E36 efterverkan (5 följande mot 5 föregående), inom konto")
r, p = analys(alla, np.array([rad[i]["u"] for i in alla]), "HE36a eget u (utan u konstant)", ytter=True)
print(f"    => HE36a {'HÅLLER' if r > 0 and p < 0.05 else 'FALLER'}")
ids = E.ids; pF = dict(zip(ids, E.pF)); ny = E.nya
r, p = analys(ids, np.array([pF[i] for i in ids]), "HE36b fältpoäng | u (alla med fält)"); print(f"    => HE36b {'HÅLLER' if r > 0 and p < 0.05 else 'FALLER'}")
analys([i for i in ids if i not in ny], np.array([pF[i] for i in ids if i not in ny]), "  bibliotek", n=1000)
analys([i for i in ids if i in ny], np.array([pF[i] for i in ids if i in ny]), "  replikering", n=1000)
TAL = {json.loads(l)["id"]: json.loads(l) for l in (E.ROT / "e30" / "tal.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
ti = [i for i in alla if i in TAL and TAL[i]["langd"] >= 0.5]
r, p = analys(ti, np.array([np.log1p(TAL[i]["tal_segment"]) for i in ti]), "HE36c talsegment | u"); print(f"    => HE36c {'HÅLLER' if r > 0 and p < 0.05 else 'FALLER'}")
# takter residualiserade på u inom konto (som E33)
ka = np.array([rad[i]["konto"] for i in alla])
def cen(v):
    v = np.asarray(v, float).copy()
    for k in set(ka): m = ka == k; v[m] -= np.nanmean(v[m])
    return v
uc = cen([rad[i]["u"] for i in alla])
for h, t in [("HE36d", "dela"), ("HE36e", "komm")]:
    v = cen([rad[i][t] for i in alla]); okk = ~np.isnan(v); v[okk] -= (v[okk] @ uc[okk]) / (uc[okk] @ uc[okk]) * uc[okk]
    r, p = analys(alla, v, f"{h} {t}-takt | u"); print(f"    => {h} {'HÅLLER' if r > 0 and p < 0.05 else 'FALLER'}")
v = cen([rad[i]["gill"] for i in alla]); okk = ~np.isnan(v); v[okk] -= (v[okk] @ uc[okk]) / (uc[okk] @ uc[okk]) * uc[okk]
analys(alla, v, "  (utforskande) gill-takt | u", n=1000)

print("\nUtforskande: fönster 3 och 10")
for w in (3, 10):
    analys(ids, np.array([pF[i] for i in ids]), f"  fältpoäng | u, fönster {w}", w=w, n=1000)
    analys(ti, np.array([np.log1p(TAL[i]["tal_segment"]) for i in ti]), f"  talsegment | u, fönster {w}", w=w, n=1000)
print("\nUtforskande: drar ett bra mötesklipp med sig mer? e | u per hälft av fältpoängen bland klipp med u > 0,5")
for namn, sel in [("hög fältpoäng", lambda i: pF[i] > np.median(E.pF)), ("låg fältpoäng", lambda i: pF[i] <= np.median(E.pF))]:
    s = [i for i in ids if sel(i) and rad[i]["u"] > 0.5 and not np.isnan(rad[i]["e5"])]
    print(f"  {namn}: n {len(s)}, medel e {np.mean([rad[i]['e5'] for i in s]):+.3f}, medel u {np.mean([rad[i]['u'] for i in s]):+.2f}")
