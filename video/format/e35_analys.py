# E35: dialog mot monolog. data/format/e35/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e35_analys.py
import io, contextlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
with contextlib.redirect_stdout(io.StringIO()):
    import e32_analys as B
    import e34_analys as O
import numpy as np
from scipy.stats import rankdata
from scipy.cluster.hierarchy import linkage, fcluster
rng = np.random.default_rng(35); ROT = B.ROT

def matt(r, tau):
    seg, S = r["seg"], np.array(r["sim"]) if r["sim"] else None
    if S is None or len(seg) < 2: return 0, (1 if seg else 0), 0.0
    byten = int(sum(S[k, k + 1] < tau for k in range(len(seg) - 1)))
    lang = [k for k, s in enumerate(seg) if s[1] - s[0] >= 1.0]
    if len(lang) >= 2:
        d = 1 - S[np.ix_(lang, lang)]; iu = np.triu_indices(len(lang), 1)
        talare = int(fcluster(linkage(np.clip(d[iu], 0, 2), "average"), 1 - tau, "distance").max())
    else: talare = 1 if lang else 0
    snabb = sum(1 for k in range(len(seg) - 1) if S[k, k + 1] < tau and seg[k + 1][0] - seg[k][1] < 0.5)
    return byten, talare, snabb

T = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e35" / "talare.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
TAL = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e30" / "tal.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
TAL.update({json.loads(l)["id"]: json.loads(l) for l in (ROT / "e34" / "tal.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()})

# utfall och residualiserade takter per källa
rader = []
bank = [i for i in B.rad if not np.isnan(B.rad[i]["u"]) and i in T and i in TAL]
kb = np.array([B.rad[i]["konto"] for i in B.rad if not np.isnan(B.rad[i]["u"])]); allb = [i for i in B.rad if not np.isnan(B.rad[i]["u"])]
def cen(v, ka):
    v = np.asarray(v, float).copy()
    for k in set(ka): m = ka == k; v[m] -= np.nanmean(v[m])
    return v
ub = cen([B.rad[i]["u"] for i in allb], kb); Yb = {"u": ub}
for t in ["komm", "dela"]:
    v = cen([B.rad[i][t] for i in allb], kb); ok = ~np.isnan(v); v[ok] -= (v[ok] @ ub[ok]) / (ub[ok] @ ub[ok]) * ub[ok]; Yb[t] = v
ixb = {i: n for n, i in enumerate(allb)}
for i in bank:
    rader.append({"id": i, "grupp": "b:" + B.rad[i]["konto"], "set": "rep" if i in B.nya else "bib", **{t: Yb[t][ixb[i]] for t in Yb}})
for n, r in enumerate(O.rad):
    if r["id"] in T and r["id"] in TAL: rader.append({"id": r["id"], "grupp": "o:" + r["konto"], "set": "osedd", **{t: O.Y[t][n] for t in ["u", "komm", "dela"]}})
print(f"E35: {len(T)} klipp mätta; med utfall: " + ", ".join(f"{s} {sum(r['set'] == s for r in rader)}" for s in ["bib", "rep", "osedd"]))

def prho(sel, x, y, z=None, n=4000):
    R = [r for r in rader if r["set"] in sel]; ka = np.array([r["grupp"] for r in R]); xs = x(R); ys = np.array([r[y] for r in R])
    ok = ~np.isnan(ys); ka, xs, ys = ka[ok], xs[ok], ys[ok]
    xr, yr = cen(rankdata(xs), ka), cen(rankdata(ys), ka)
    if z is not None:
        zs = cen(rankdata(z(R)[ok]), ka); f = lambda a: a - zs * (a @ zs) / (zs @ zs); xr, yr = f(xr), f(yr)
    r0 = np.corrcoef(xr, yr)[0, 1]; c = 0; g = [np.where(ka == k)[0] for k in set(ka)]
    for _ in range(n):
        yy = yr.copy()
        for gg in g: yy[gg] = rng.permutation(yy[gg])
        if z is not None: yy = yy - zs * (yy @ zs) / (zs @ zs)
        c += abs(np.corrcoef(xr, yy)[0, 1]) >= abs(r0)
    return r0, (c + 1) / (n + 1), ok.sum()
def pbin(sel, m_, y, n=4000):
    R = [r for r in rader if r["set"] in sel]; ka = np.array([r["grupp"] for r in R]); m, ys = m_(R), np.array([r[y] for r in R])
    keep = (m != 0) & ~np.isnan(ys); ka, m, ys = ka[keep], m[keep] == 1, ys[keep]; ys = cen(ys, ka)
    d0 = ys[m].mean() - ys[~m].mean(); c = 0; g = [np.where(ka == k)[0] for k in set(ka)]
    for _ in range(n):
        mm = m.copy()
        for gg in g: mm[gg] = rng.permutation(mm[gg])
        c += abs(ys[mm].mean() - ys[~mm].mean()) >= abs(d0)
    return np.exp(d0), (c + 1) / (n + 1), int(m.sum()), int((~m).sum())

for tau in [0.86, 0.80, 0.90]:
    M = {i: matt(T[i], tau) for i in T}
    by = lambda R: np.array([np.log1p(M[r["id"]][0]) for r in R], float)
    ts = lambda R: np.array([np.log1p(TAL[r["id"]]["tal_segment"]) for r in R], float)
    # dialog = 1, monolog = -1, övrigt 0
    def dm(R):
        out = []
        for r in R:
            b, t, _ = M[r["id"]]; ns = len(T[r["id"]]["seg"])
            out.append(1 if t >= 2 and b >= 2 else (-1 if t == 1 and ns >= 3 else 0))
        return np.array(out)
    dm_mono = lambda R: -dm(R)  # monolog = 1
    print(f"\n--- tröskel {tau}{' (förregistrerad)' if tau == 0.86 else ' (känslighet)'}")
    alla_dm = dm(rader); print(f"  dialog {np.mean(alla_dm == 1):.0%}, monolog {np.mean(alla_dm == -1):.0%}, median byten {np.median([M[r['id']][0] for r in rader]):.0f}")
    for sel, namn in [(("rep", "osedd"), "repl+osedda"), (("rep",), "repl"), (("osedd",), "osedda"), (("bib",), "bibliotek")]:
        a = prho(sel, by, "u", ts, 2000 if tau == 0.86 else 500); a0 = prho(sel, by, "u", None, 500)
        bk = pbin(sel, dm_mono, "komm", 2000 if tau == 0.86 else 500); bd = pbin(sel, dm_mono, "dela", 2000 if tau == 0.86 else 500); d = pbin(sel, dm, "u", 2000 if tau == 0.86 else 500)
        print(f"  {namn:12s} byten→u {a0[0]:+.3f} | tal konstant {a[0]:+.3f} (p {a[1]:.3f}, n {a[2]})   monolog mot dialog: komm ×{bk[0]:.2f} (p {bk[1]:.3f}) dela ×{bd[0]:.2f} (p {bd[1]:.3f}) [n {bk[2]}/{bk[3]}]   dialog mot monolog u ×{d[0]:.2f} (p {d[1]:.3f})")
        if tau == 0.86 and namn == "repl+osedda":
            print(f"  => HE35a {'HÅLLER' if a[0] > 0 and a[1] < .05 else 'FALLER'}   HE35b {'HÅLLER' if (bk[0] > 1 and bk[1] < .05) or (bd[0] > 1 and bd[1] < .05) else 'FALLER'}   HE35d {'HÅLLER' if d[0] > 1 and d[1] < .05 else 'FALLER'}")
    if tau == 0.86:
        F = {i: B.las(i) for i in T if (ROT / "e20/lasning" / f"{i}.json").exists() and (ROT / "e21/lasning" / f"{i}.json").exists()}
        pos = [np.log1p(M[i][0]) for i, f in F.items() if f.get("relation") in ("gast_personal", "personal_personal")]
        neg = [np.log1p(M[i][0]) for i, f in F.items() if f.get("relation") not in ("gast_personal", "personal_personal")]
        rk = rankdata(pos + neg); auc = (rk[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
        print(f"  HE35c AUC byten för möte (n {len(pos)}) mot övrigt (n {len(neg)}): {auc:.3f}  => {'HÅLLER' if auc > 0.6 else 'FALLER'}")
        sn = lambda R: np.array([np.log1p(M[r["id"]][2]) for r in R], float)
        a = prho(("rep", "osedda"), sn, "u", ts, 1000); print(f"  utforskande: snabba växlingar (< 0,5 s) | tal konstant: {a[0]:+.3f} (p {a[1]:.3f})")
