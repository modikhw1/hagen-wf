# E32b: kontroller av E32-fynd (utforskande, efter körningen). Importerar e32_analys tyst.
#   ../scen/.venv/Scripts/python.exe -u format/e32b_kontroll.py
import io, contextlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
with contextlib.redirect_stdout(io.StringIO()):
    import e32_analys as E
import numpy as np
rad, ids, FV, konto, y, ny, pF, R = E.rad, E.ids, E.FV, E.konto, E.y, E.ny, E.pF, E.R
sp, cen, rng = E.sp, E.cen, np.random.default_rng(321)

# 1. lagrat mot återskapat u
a = np.array([(R[i]["u"], rad[i]["u"]) for i in ids]); d = np.abs(a[:, 0] - a[:, 1])
print(f"1. lagrat mot återskapat u: r {np.corrcoef(a.T)[0, 1]:.3f}, {np.mean(d < 1e-6):.0%} exakt lika, {np.mean(d > 0.1):.1%} avviker > 0,1")
bad = [i for i, x in zip(ids, d) if x > 0.1]; print(f"   avvikande per konto: {sorted({rad[i]['konto'] for i in bad})[:8]} ...")
print(f"   fältpoäng mot lagrat u (replikering): {sp(pF[ny], cen(a[:, 0], konto)[ny]):+.3f}")

# 2. engagemang med u hållet konstant (takten residualiseras på u inom konto)
print("\n2. engagemangstakt med u konstant (partiell, inom konto)")
uu = cen(np.array([rad[i]["u"] for i in ids]), konto)
def resid(t):
    v = np.array([rad[i][t] for i in ids]); ok = ~np.isnan(v); vc = cen(v, konto); bb = (vc[ok] @ uu[ok]) / (uu[ok] @ uu[ok]); vc[ok] -= bb * uu[ok]; return vc, ok, bb
J = lambda k, x: np.array([FV[i].get(k) == x for i in ids])
for t in ["gill", "komm", "dela"]:
    vc, ok, bb = resid(t)
    s = []
    for namn, m, bas in [("friktion", J("friktion", "tydlig"), ~J("friktion", "mild")), ("gäst–personal", J("relation", "gast_personal"), ~J("relation", "personal_personal"))]:
        mm, oo = m & bas & ok, ~m & bas & ok
        d0 = vc[mm].mean() - vc[oo].mean(); idx = np.where(bas & ok)[0]; c = 0
        for _ in range(2000):
            p = vc[idx].copy()
            for k in set(konto[idx]): g = konto[idx] == k; p[g] = rng.permutation(p[g])
            c += abs(p[m[idx]].mean() - p[~m[idx]].mean()) >= abs(d0)
        s.append(f"{namn} ×{np.exp(d0):.2f} (p {(c + 1) / 2001:.3f})")
    print(f"   {t:5s} lutning mot u {bb:+.2f}:  " + "   ".join(s) + f"   fältpoäng rho {sp(pF[ok & ny], vc[ok & ny]):+.3f} (repl.)")

# 3. upprepning med u mot hela kontot (ingen grannmekanik) och fler mått
print("\n3. upprepning: mötesklipp efter möte mot efter annat")
pos_ = {(rad[i]["konto"], rad[i]["pos"]): i for i in ids}
for t in ["u", "uhel", "u20"]:
    yt = cen(np.array([rad[i][t] for i in ids]), konto); ix = {i: n for n, i in enumerate(ids)}
    ef, ei, kf = [], [], []
    for i in ids:
        if FV[i].get("relation") != "gast_personal": continue
        f = pos_.get((rad[i]["konto"], rad[i]["pos"] - 1))
        if f: (ef if FV[f].get("relation") == "gast_personal" else ei).append(yt[ix[i]]); kf.append(rad[i]["konto"])
    print(f"   {t:5s} efter möte n {len(ef)} ×{np.exp(np.mean(ef)):.2f}   efter annat n {len(ei)} ×{np.exp(np.mean(ei)):.2f}   skillnad ×{np.exp(np.mean(ei) - np.mean(ef)):.2f}")

# 3b. med alla fält: klippets poäng mot föregående klipps poäng (bara där båda lästa)
ix = {i: n for n, i in enumerate(ids)}; o, f_, yy, kk = [], [], [], []
yh = cen(np.array([rad[i]["uhel"] for i in ids]), konto)
for i in ids:
    f = pos_.get((rad[i]["konto"], rad[i]["pos"] - 1))
    if f: o.append(pF[ix[i]]); f_.append(pF[ix[f]]); yy.append(yh[ix[i]]); kk.append(rad[i]["konto"])
o, f_, yy = map(np.array, (o, f_, yy)); X = np.column_stack([o, f_, o * f_]); X = (X - X.mean(0)) / X.std(0)
bb = np.linalg.lstsq(np.column_stack([np.ones(len(yy)), X]), yy, rcond=None)[0]
print(f"   par med båda lästa n {len(yy)}: uhel ~ egen {bb[1]:+.3f}, föregående {bb[2]:+.3f}, egen×föregående {bb[3]:+.3f} (log per sd)")
c = 0
for _ in range(2000):
    pp = f_.copy()
    for k in set(kk): g = np.array(kk) == k; pp[g] = rng.permutation(pp[g])
    Xp = np.column_stack([o, pp, o * pp]); Xp = (Xp - Xp.mean(0)) / Xp.std(0)
    c += abs(np.linalg.lstsq(np.column_stack([np.ones(len(yy)), Xp]), yy, rcond=None)[0][3]) >= abs(bb[3])
print(f"   interaktion p {(c + 1) / 2001:.3f}")

# 4. erbjudandeord: vad är det?
import re
alla = [i for i in rad if not np.isnan(rad[i]["u"])]
print("\n4. erbjudandeord per ord (alla bankklipp, inom konto, faktor)")
ka = np.array([rad[i]["konto"] for i in alla]); ua = cen(np.array([rad[i]["u"] for i in alla]), ka); tx = [rad[i]["text"].lower() for i in alla]
for w in [r"\d\s*kr\b", r"\d\s*%", "erbjudande", "rabatt", "öppet", "öppnar", "meny", "nyhet", "boka", "gratis"]:
    m = np.array([bool(re.search(w, t)) for t in tx])
    if m.sum() >= 15: print(f"   {w:12s} n {m.sum():4d} ×{np.exp(ua[m].mean() - ua[~m].mean()):.2f}")
m = np.array([bool(re.search(r"\d\s*kr\b", t)) for t in tx])
fk = [i for i, mm in zip(alla, m) if mm and i in FV]
if fk: print(f"   'kr'-klipp med fält: n {len(fk)}, insats=pengar {np.mean([FV[i].get('insats') == 'pengar' for i in fk]):.0%} (alla {np.mean([FV[i].get('insats') == 'pengar' for i in ids]):.0%}), gäst–personal {np.mean([FV[i].get('relation') == 'gast_personal' for i in fk]):.0%} (alla {np.mean([FV[i].get('relation') == 'gast_personal' for i in ids]):.0%})")
for i in [i for i, mm in zip(alla, m) if mm][:0]: pass
top = sorted([(ua[n], rad[i]["text"][:90]) for n, (i, mm) in enumerate(zip(alla, m)) if mm], reverse=True)
print("   högst:", *[f"\n     ×{np.exp(v):.1f} {t}" for v, t in top[:6]])

# 5. ägarens pass 7: samma 11 överallt?
print("\n5. pass 7 par för par (v=vänster vald): u-skillnad, komm-skillnad")
P, A = E.P, E.A
for p in P:
    val = A.get(str(p["nr"])); v, h = E.hitta(p["vanster"]), E.hitta(p["hoger"])
    if val and v and h:
        dv = lambda t: rad[v][t] - rad[h][t]
        print(f"   {p['nr']:>2} {val} u {dv('u'):+.2f} gill {dv('gill'):+.2f} komm {dv('komm'):+.2f} dela {dv('dela'):+.2f}")
