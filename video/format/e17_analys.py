# E17: motorgeometri. M1 ytan borta, M2 värdet kvar, M3 röd tråd, M4 ägarens biblioteksval, M5 axlarna utlästa.
#   ../scen/.venv/Scripts/python.exe -u format/e17_analys.py [motorer | motorer-flash]
# Kräver vek-<kalla>-hel.npy, -yta.npy och -svag.npy från e15_badda.py.
import json, sys
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROT = Path(__file__).resolve().parents[2] / "data"
E = ROT / "format" / "e15"
kalla = sys.argv[1] if len(sys.argv) > 1 else "motorer"
R = [json.loads(l) for l in (E / f"{kalla}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
RUM = {n: np.load(E / f"vek-{kalla}-{n}.npy") for n in ["hel", "yta", "svag"] if (E / f"vek-{kalla}-{n}.npy").exists()}
NAMN = {"hel": "motor", "yta": "yta", "svag": "svag text"}
konto = np.array([r["konto"] for r in R]); ix = {r["id"]: i for i, r in enumerate(R)}
rng = np.random.default_rng(7)
sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
print(f"{kalla}: {len(R)} klipp, {len(set(konto))} konton\n")


def centrera(V):
    C = V.copy()
    for k in set(konto):
        m = konto == k
        if m.sum() > 1: C[m] -= C[m].mean(0)
    return C


# M1: går kontot att gissa? Närmaste granne (ej klippet självt), bara konton med minst 5 klipp.
stora = np.array([np.sum(konto == k) >= 5 for k in konto])
print("M1: träffandel på konto för närmaste granne (lägre = mindre yta kvar)")
for n, V in RUM.items():
    S = V @ V.T; np.fill_diagonal(S, -9)
    print(f"  {NAMN[n]:10s} {np.mean(konto[S.argmax(1)][stora] == konto[stora]):.2f}")
print(f"  slump      {np.mean([np.mean(konto[stora] == k) for k in konto[stora]]):.2f}\n")

# M2: utfall inom konto ur de 30 första axlarna, hela konton undanhållna (5 veck × 5 omgångar)
u = np.array([r["u"] if r.get("u") is not None else np.nan for r in R]); ok = ~np.isnan(u)
kk = np.array(sorted(set(konto[ok])))


def kors(V, n_ax=30, lam=10.0):
    C = centrera(V); rs = []
    for _ in range(5):
        rng.shuffle(kk); veck = np.array_split(kk, 5); pred = np.full(len(R), np.nan)
        for v in veck:
            te = ok & np.isin(konto, v); tr = ok & ~np.isin(konto, v)
            _, _, W = np.linalg.svd(C[tr], full_matrices=False); W = W[:n_ax]
            X = C[tr] @ W.T; y = u[tr] - u[tr].mean()
            b = np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]) * X.var() * len(X) / 100, X.T @ y)
            pred[te] = C[te] @ W.T @ b
        # inom konto: centrera förutsägelse och utfall per konto
        p, y = pred[ok].copy(), u[ok].copy(); kon = konto[ok]
        for k in set(kon):
            m = kon == k; p[m] -= p[m].mean(); y[m] -= y[m].mean()
        rs.append(sp(p, y))
    return float(np.mean(rs)), float(np.std(rs))


print(f"M2: utfall inom konto ur 30 axlar, konton undanhållna ({ok.sum()} klipp med utfall, {len(kk)} konton)")
for n, V in RUM.items():
    m, s = kors(V); print(f"  {NAMN[n]:10s} rho {m:+.3f} (±{s:.3f} mellan omgångar)")
print()

# M3: röd tråd
if "hel" in RUM:
    C = centrera(RUM["hel"]); ka = np.array(sorted(set(konto))); kv = []
    for _ in range(20):
        rng.shuffle(ka); A = np.isin(konto, ka[: len(ka) // 2])
        _, _, Wa = np.linalg.svd(C[A], full_matrices=False); _, sb, _ = np.linalg.svd(C[~A], full_matrices=False)
        kv.append(float(((C[~A] @ Wa[:20].T) ** 2).sum() / (sb[:20] ** 2).sum()))
    _, s, W = np.linalg.svd(C, full_matrices=False)
    print(f"M3: motoraxlar från halva kontona förklarar {np.mean(kv):.2f} (min {np.min(kv):.2f}) av andra halvans egna; 20 axlar bär {float((s[:20] ** 2).sum() / (s ** 2).sum()):.2f} av variansen inom konto\n")

    # M4: ägarens biblioteksval i pass 7
    p7 = ROT / "format" / "harness" / "pass7"
    try:
        val = json.loads((p7 / "agare.json").read_text(encoding="utf-8"))["val"]
        parfil = next(f for f in p7.glob("*.json") if "par" in json.loads(f.read_text(encoding="utf-8")) or f.name.startswith("forreg"))
        par = json.loads(parfil.read_text(encoding="utf-8")); par = par.get("par", par)
        X = C[ok] @ W[:30].T; y = u[ok] - u[ok].mean(); b = np.linalg.solve(X.T @ X + 10 * np.eye(30) * X.var() * len(X) / 100, X.T @ y)
        ratt = fel = sakn = 0
        for nr, v in val.items():
            p = par[int(nr) - 1] if isinstance(par, list) else par.get(nr)
            ids = [p.get("v", p.get("vanster")), p.get("h", p.get("hoger"))] if isinstance(p, dict) else p
            ids = [x["id"] if isinstance(x, dict) else x for x in ids]
            if not all(i in ix for i in ids): sakn += 1; continue
            d = (C[ix[ids[0]]] - C[ix[ids[1]]]) @ W[:30].T @ b
            if (d > 0) == (v == "v"): ratt += 1
            else: fel += 1
        print(f"M4: ägarens biblioteksval i pass 7: {ratt} rätt, {fel} fel, {sakn} par saknar motor\n")
    except Exception as e:
        print(f"M4: kunde inte läsas ({type(e).__name__}: {e})\n")

    # M5: axlarna utlästa genom ytterklipp, med utfall och bibliotekets hylla
    print("M5: de gemensamma motoraxlarna, utlästa genom sina ytterklipp")
    P = C @ W[:12].T; uu = np.where(ok, u, np.nan)
    for a in range(12):
        m = ok; r = sp(P[m, a], uu[m]); hog = np.argsort(P[:, a])[-4:][::-1]; lag = np.argsort(P[:, a])[:4]
        print(f"\n  axel {a + 1} ({float(s[a] ** 2 / (s ** 2).sum()):.3f} av variansen), mot utfall inom konto rho {r:+.2f}")
        for t, I in [("+", hog), ("−", lag)]:
            for i in I: print(f"    {t} {R[i]['motor'][:150]}")
    np.save(E / f"axlar-{kalla}.npy", W[:50].astype("float32"))

# M6: flyttbarhet = närhet till de tio närmaste klippen från andra konton i motorrummet
if "hel" in RUM:
    V = RUM["hel"]; S = V @ V.T
    S[konto[:, None] == konto[None, :]] = -9
    fl = np.sort(S, axis=1)[:, -10:].mean(1)
    print("\nM6: flyttbarhet (närhet till tio närmaste klipp hos andra konton)")
    for falt in ["hantverk", "hylla", "slitage", "utsatthet"]:
        g = {}
        for r, f in zip(R, fl):
            if r.get(falt): g.setdefault(r[falt], []).append(f)
        print(f"  {falt}: " + "  ".join(f"{k} {np.mean(v):.3f} (n {len(v)})" for k, v in sorted(g.items(), key=lambda x: -np.mean(x[1])) if len(v) >= 5))
    y, f = u[ok].copy(), fl[ok].copy(); kon = konto[ok]
    for k in set(kon):
        m = kon == k; y[m] -= y[m].mean(); f[m] -= f[m].mean()
    print(f"  mot utfall inom konto: rho {sp(f, y):+.3f} (n {ok.sum()})")

    # M7: utfallsmodellen tränad bara på klipp där värdet sitter i idén eller personen
    bar = np.array([r.get("hantverk") in ("i_iden", "i_personen") for r in R])
    C = centrera(V); rs_alla, rs_bar = [], []
    for _ in range(5):
        rng.shuffle(kk); pa = np.full(len(R), np.nan); pb = np.full(len(R), np.nan)
        for v in np.array_split(kk, 5):
            te = ok & np.isin(konto, v)
            for tr, pred in [(ok & ~np.isin(konto, v), pa), (ok & ~np.isin(konto, v) & bar, pb)]:
                _, _, W2 = np.linalg.svd(C[tr], full_matrices=False); W2 = W2[:30]
                X = C[tr] @ W2.T; yy = u[tr] - u[tr].mean()
                b2 = np.linalg.solve(X.T @ X + 10 * np.eye(X.shape[1]) * X.var() * len(X) / 100, X.T @ yy)
                pred[te] = C[te] @ W2.T @ b2
        for pred, rs in [(pa, rs_alla), (pb, rs_bar)]:
            p, y2 = pred[ok].copy(), u[ok].copy()
            for k in set(kon):
                m = kon == k; p[m] -= p[m].mean(); y2[m] -= y2[m].mean()
            rs.append(sp(p, y2))
    print(f"\nM7: utfall på undanhållna konton, tränad på alla ({ok.sum()}) rho {np.mean(rs_alla):+.3f}; bara idé/person ({(ok & bar).sum()}) rho {np.mean(rs_bar):+.3f}")
