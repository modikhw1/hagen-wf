# E32: fälla tjänstemötet + oanvänd data (engagemang, bildtext, tid). Inga modellanrop. data/format/e32/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e32_analys.py
import json, re
from datetime import date
from pathlib import Path
import numpy as np
from scipy.stats import rankdata, binomtest

D = Path(__file__).resolve().parents[2] / "data"; ROT = D / "format"; rng = np.random.default_rng(32)
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])

# ---- bankdata, utfall återskapat som i e16-analys.mjs
K = {}
for f in (D / "bank").glob("*/lista.json"):
    j = json.loads(f.read_text(encoding="utf-8")); L = [x for x in j["klipp"] if (x.get("visningar") or 0) > 0]
    L.sort(key=lambda x: x.get("datum") or ""); K[j["konto"]] = (j.get("hamtad", "")[:10], L)

def utfall(L, w=10, agg=np.median, helt=False):
    v = np.log([x["visningar"] for x in L]); ut = np.full(len(L), np.nan)
    for i in range(len(L)):
        g = np.delete(v, i) if helt else np.concatenate([v[max(0, i - w):i], v[i + 1:i + w + 1]])
        if len(g) >= 6: ut[i] = v[i] - agg(g)
    return ut

def takt(L, falt, w=10):
    v = np.array([np.log((x.get(falt) or 0) + 1) - np.log(x["visningar"]) for x in L]); ut = np.full(len(L), np.nan)
    for i in range(len(L)):
        g = np.concatenate([v[max(0, i - w):i], v[i + 1:i + w + 1]])
        if len(g) >= 6: ut[i] = v[i] - np.median(g)
    return ut

rad = {}
for k, (h, L) in K.items():
    var = {"u": utfall(L), "u5": utfall(L, 5), "u20": utfall(L, 20), "umedel": utfall(L, agg=np.mean), "uhel": utfall(L, helt=True),
           "gill": takt(L, "gillanden"), "komm": takt(L, "kommentarer"), "dela": takt(L, "delningar")}
    for i, x in enumerate(L):
        nid = f"{k}-{x['id']}"
        try: alder = (date.fromisoformat(h) - date.fromisoformat(x["datum"])).days if h and x.get("datum") else 999
        except ValueError: alder = 999
        rad[nid] = {"konto": k, "pos": i, "text": x.get("text") or "", "alder": alder, **{n: a[i] for n, a in var.items()}}

# kontroll mot lagrat u
R = {json.loads(l)["id"]: json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
par = [(R[i]["u"], rad[i]["u"]) for i in R if R[i].get("u") is not None and i in rad and not np.isnan(rad[i]["u"])]
a = np.array(par); print(f"Kontroll: {len(a)} klipp, lagrat u mot återskapat: max avvikelse {np.abs(a[:, 0] - a[:, 1]).max():.4f}")

# ---- fält
FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
def las(i):
    a, b = ROT / "e20/lasning" / f"{i}.json", ROT / "e21/lasning" / f"{i}.json"
    return {**json.loads(a.read_text(encoding="utf-8")), **json.loads(b.read_text(encoding="utf-8"))} if a.exists() and b.exists() else None
nya = set(json.loads((ROT / "e19" / "ids.json").read_text()))
ids = [i for i in R if i in rad and not np.isnan(rad[i]["u"]) and las(i)]
FV = {i: las(i) for i in ids}
konto = np.array([rad[i]["konto"] for i in ids]); ny = np.array([i in nya for i in ids])
F = np.array([[float(FV[i].get(k) == x) for k, xs in FALT.items() for x in xs] for i in ids])

def cen(X, kk):
    X = np.asarray(X, float).copy()
    for k in set(kk): m = kk == k; X[m] -= np.nanmean(X[m], 0)
    return X
y = cen(np.array([rad[i]["u"] for i in ids]), konto)
C = cen(F, konto); s = C[~ny].std(0) + 1e-9; C = C / s
b = np.linalg.solve(C[~ny].T @ C[~ny] + 5 * np.eye(C.shape[1]), C[~ny].T @ y[~ny]); pF = C @ b
print(f"\n{len(ids)} klipp med fält ({ny.sum()} replikering). Fältpoäng fryst på biblioteket: replikering rho {sp(pF[ny], y[ny]):+.3f}")

def perm_rho(x, yv, kk, n=4000):
    ok = ~np.isnan(yv); x, yv, kk = rankdata(x[ok]), yv[ok], kk[ok]; yv = cen(rankdata(yv), kk); x = cen(x, kk)
    r0 = np.corrcoef(x, yv)[0, 1]; c = 0; grp = [np.where(kk == k)[0] for k in set(kk)]
    for _ in range(n):
        yy = yv.copy()
        for g in grp: yy[g] = rng.permutation(yy[g])
        c += abs(np.corrcoef(x, yy)[0, 1]) >= abs(r0)
    return r0, (c + 1) / (n + 1), ok.sum()

def perm_bin(m, yv, kk, n=4000):
    ok = ~np.isnan(yv); m, yv, kk = m[ok], yv[ok], kk[ok]; yc = cen(yv, kk)
    d0 = yc[m].mean() - yc[~m].mean(); c = 0; grp = [np.where(kk == k)[0] for k in set(kk)]
    for _ in range(n):
        mm = m.copy()
        for g in grp: mm[g] = rng.permutation(mm[g])
        c += abs(yc[mm].mean() - yc[~mm].mean()) >= abs(d0)
    return np.exp(d0), (c + 1) / (n + 1), int(m.sum())

# ---- HE32a
print("\nHE32a robusthet över konton (replikering)")
kr = konto[ny]; pr, yr = pF[ny], y[ny]
per = {k: sp(pr[kr == k], yr[kr == k]) for k in set(kr) if (kr == k).sum() >= 8}
pos = sum(r > 0 for r in per.values()); bt = binomtest(pos, len(per), 0.5, alternative="greater").pvalue
loo = {k: sp(pr[kr != k], yr[kr != k]) for k in set(kr)}
kmin = min(loo, key=loo.get)
print(f"  {pos} av {len(per)} konton positiva ({pos / len(per):.0%}), teckentest p {bt:.4f}; median rho per konto {np.median(list(per.values())):+.2f}")
print(f"  ett konto bort: lägst {loo[kmin]:+.3f} (utan {kmin}, n {(kr == kmin).sum()}), högst {max(loo.values()):+.3f}")
print(f"  => HE32a {'HÅLLER' if pos / len(per) >= 0.6 and bt < 0.05 and loo[kmin] >= 0.15 else 'FALLER'}")

# ---- HE32b
print("\nHE32b utfallets definition (replikering, fryst poäng)")
ok32b = True
for n in ["u", "u5", "u20", "umedel", "uhel", "u_ung"]:
    if n == "u_ung":
        yy = np.array([rad[i]["u"] if rad[i]["alder"] >= 21 else np.nan for i in ids])
    else:
        yy = np.array([rad[i][n] for i in ids])
    m = ny & ~np.isnan(yy); yc = cen(yy, konto); r = sp(pF[m], yc[m]); ok32b &= r >= 0.12 or n == "u"
    print(f"  {n:7s} n {m.sum():4d}  rho {r:+.3f}")
print(f"  => HE32b {'HÅLLER' if ok32b else 'FALLER'}")

# ---- dos
print("\nDos (replikering): medel u inom konto per femtedel av fältpoängen, som faktor")
q = np.quantile(pr, [.2, .4, .6, .8]); fe = np.digitize(pr, q)
print("  " + "  ".join(f"F{j + 1} ×{np.exp(yr[fe == j].mean()):.2f}" for j in range(5)))

# ---- HE32c/d engagemang
J = lambda k, x: np.array([FV[i].get(k) == x for i in ids])
print("\nEngagemang (alla klipp med fält, inom konto, som faktor på takten)")
for namn, m in [("friktion=tydlig mot ingen", J("friktion", "tydlig")), ("gäst–personal mot tilltal/ingen", J("relation", "gast_personal"))]:
    bas = m | ~(J("friktion", "mild") if "friktion" in namn else J("relation", "personal_personal"))
    rr = []
    for t in ["u", "gill", "komm", "dela"]:
        yy = np.array([rad[i][t] for i in ids]); f, p, nm = perm_bin(m[bas], yy[bas], konto[bas]); rr.append(f"{t} ×{f:.2f} (p {p:.3f})")
    print(f"  {namn:32s} n {m.sum():4d}: " + "  ".join(rr))
print("  fältpoäng (fryst) mot takter, replikering: " + "  ".join(f"{t} {sp(pF[ny & ~np.isnan(yy)], cen(yy, konto)[ny & ~np.isnan(yy)]):+.3f}" for t in ["gill", "komm", "dela"] for yy in [np.array([rad[i][t] for i in ids])]))

# ---- bildtext, alla bankklipp med utfall
alla = [i for i in rad if not np.isnan(rad[i]["u"])]
ka = np.array([rad[i]["konto"] for i in alla]); ua = np.array([rad[i]["u"] for i in alla]); tx = [rad[i]["text"].lower() for i in alla]
hashtags = np.array([len(re.findall(r"#\w", t)) for t in tx], float)
serie = np.array([bool(re.search(r"\b(del|part|pt)\.?\s*\d", t)) for t in tx])
erbj = np.array([bool(re.search(r"\d\s*kr\b|\d\s*%|erbjudande|rabatt|öppet|öppnar|meny|nyhet|boka|gratis", t)) for t in tx])
prem = np.array([("?" in t) or bool(re.match(r"\s*(när|pov|den dagen|when)\b", t)) for t in tx])
fraga = np.array(["?" in t for t in tx]); start = np.array([bool(re.match(r"\s*(när|pov|den dagen|when)\b", t)) for t in tx])
print(f"\nBildtext: {len(alla)} bankklipp med utfall, {len(set(ka))} konton")
r, p, n = perm_rho(hashtags, ua, ka); print(f"  HE32e hashtags rho {r:+.3f} p {p:.4f}  => {'HÅLLER' if r < 0 and p < 0.05 else 'FALLER'}")
for h, namn, m, tecken in [("HE32f", "seriemarkör", serie, 1), ("HE32g", "erbjudandeord", erbj, -1), ("HE32h", "fråga/premiss", prem, 1), ("  (del)", "bara fråga", fraga, 1), ("  (del)", "bara premisstart", start, 1)]:
    f, p, n = perm_bin(m, ua, ka); ok = (np.log(f) * tecken > 0) and p < 0.05
    print(f"  {h} {namn:16s} n {n:5d}  ×{f:.2f}  p {p:.4f}" + (f"  => {'HÅLLER' if ok else 'FALLER'}" if h.startswith("HE") else ""))

# bildtext + fält på replikeringen
T = lambda i: [len(re.findall(r"#\w", rad[i]["text"].lower())), "?" in rad[i]["text"], bool(re.search(r"\b(del|part|pt)\.?\s*\d", rad[i]["text"].lower())), bool(re.search(r"\d\s*kr\b|\d\s*%|erbjudande|rabatt|öppet|öppnar|meny|nyhet|boka|gratis", rad[i]["text"].lower()))]
B = np.array([T(i) for i in ids], float); CB = cen(B, konto); CB /= CB[~ny].std(0) + 1e-9
CC = np.hstack([C, CB]); b2 = np.linalg.solve(CC[~ny].T @ CC[~ny] + 5 * np.eye(CC.shape[1]), CC[~ny].T @ y[~ny])
bb = np.linalg.solve(CB[~ny].T @ CB[~ny] + 5 * np.eye(CB.shape[1]), CB[~ny].T @ y[~ny])
print(f"  utforskande, replikering: bildtext {sp((CB @ bb)[ny], y[ny]):+.3f}, fält {sp(pF[ny], y[ny]):+.3f}, fält + bildtext {sp((CC @ b2)[ny], y[ny]):+.3f}")

# ---- upprepning
print("\nUpprepning (utforskande): mötesklipp (gäst–personal) efter möte mot efter icke-möte")
pos_ = {(rad[i]["konto"], rad[i]["pos"]): i for i in ids}; ef, ei = [], []
for i in ids:
    if FV[i].get("relation") != "gast_personal": continue
    f = pos_.get((rad[i]["konto"], rad[i]["pos"] - 1))
    if f: (ef if FV[f].get("relation") == "gast_personal" else ei).append(y[ids.index(i)])
print(f"  efter möte n {len(ef)} ×{np.exp(np.mean(ef)):.2f}   efter annat n {len(ei)} ×{np.exp(np.mean(ei)):.2f}")

# ---- brustak
print("\nBrustak (utforskande): u mot nästa klipps u inom konto")
x1, x2 = [], []
for k, (h, L) in K.items():
    uu = [rad[f"{k}-{x['id']}"]["u"] for x in L]
    for a_, b_ in zip(uu, uu[1:]):
        if not (np.isnan(a_) or np.isnan(b_)): x1.append(a_); x2.append(b_)
print(f"  lag 1: rho {sp(x1, x2):+.3f} (n {len(x1)}), sd u {np.std(ua):.2f} (log), dvs ×{np.exp(np.std(ua)):.1f} per sd")

# ---- ägarens val pass 7
print("\nÄgarens val, pass 7 (utforskande): andel där valt klipp har högre värde")
P = json.loads((ROT / "harness" / "pass7" / "forregistrering.json").read_text(encoding="utf-8"))["par"]
A = json.loads((ROT / "harness" / "pass7" / "agare.json").read_text(encoding="utf-8"))["val"]
def hitta(p):
    i = p["id"]; return i if i in rad else next((k for k in rad if k.endswith("-" + i)), None)
for t in ["u", "gill", "komm", "dela"]:
    r_ = f_ = 0
    for p in P:
        val = A.get(str(p["nr"]))
        if not val: continue
        v, h = hitta(p["vanster"]), hitta(p["hoger"])
        if not v or not h or np.isnan(rad[v][t]) or np.isnan(rad[h][t]): continue
        if (rad[v][t] > rad[h][t]) == (val == "v"): r_ += 1
        else: f_ += 1
    print(f"  {t:5s} {r_} av {r_ + f_}")
