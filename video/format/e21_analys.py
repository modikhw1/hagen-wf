# E21 (och E20 på replikeringen): fälten mot utfall inom konto, och HE21d (sju fält frusna, motorns rest).
#   ../scen/.venv/Scripts/python.exe -u format/e21_analys.py
# Underlag: e15/motorer-flash.jsonl (+ vek-motorer-flash-hel.npy), e20/lasning, e21/lasning, e19/ids.json, e17/modell.npz
import json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROT = Path(__file__).resolve().parents[2] / "data" / "format"
R = [json.loads(l) for l in (ROT / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
V = np.load(ROT / "e15" / "vek-motorer-flash-hel.npy"); nya = set(json.loads((ROT / "e19" / "ids.json").read_text()))
rng = np.random.default_rng(21); sp = lambda a, b: float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
rad = []
for i, r in enumerate(R):
    a, b = ROT / "e20" / "lasning" / f"{r['id']}.json", ROT / "e21" / "lasning" / f"{r['id']}.json"
    if r.get("u") is None or not a.exists(): continue
    d = {**json.loads(a.read_text(encoding="utf-8")), **(json.loads(b.read_text(encoding="utf-8")) if b.exists() else {})}
    rad.append((i, r["konto"], r["u"], r["id"] in nya, d))
I = np.array([x[0] for x in rad]); konto = np.array([x[1] for x in rad]); u = np.array([x[2] for x in rad]); ny = np.array([x[3] for x in rad]); F = [x[4] for x in rad]
har21 = np.array(["uttryck" in f for f in F])
print(f"{len(rad)} klipp med E20-fält och utfall, varav {har21.sum()} även med E21-fält; replikering {ny.sum()}, bibliotek {(~ny).sum()}\n")


def cen(x, mask):
    x = np.asarray(x, float).copy()
    for k in set(konto[mask]):
        m = mask & (konto == k); x[m] -= x[m].mean(0)
    return x


def prov(namn, mask, a, b, N=5000):
    y = cen(u, mask); m = mask & (a | b); A = a[m]; yy = y[m]; kon = konto[m]
    if A.sum() < 8 or (~A).sum() < 8: print(f"  {namn:50s} för få ({A.sum()} mot {(~A).sum()})"); return
    d0 = yy[A].mean() - yy[~A].mean(); f = 0; grupper = [np.where(kon == k)[0] for k in set(kon)]
    for _ in range(N):
        z = A.copy()
        for g in grupper: z[g] = rng.permutation(z[g])
        f += (yy[z].mean() - yy[~z].mean()) >= d0
    print(f"  {namn:50s} n {A.sum():4d} mot {(~A).sum():4d}  ×{np.exp(d0):.2f}  p {(f + 1) / (N + 1):.4f}")


v = lambda falt, *varden: np.array([f.get(falt) in varden for f in F])
for titel, mask in [("REPLIKERING (osedda klipp) – provet", ny), ("Biblioteket och E13-klippen – inget prov", ~ny)]:
    print(f"{titel}: {mask.sum()} klipp, {len(set(konto[mask]))} konton"); y = cen(u, mask)
    for falt in ["relation", "friktion", "insats", "sida", "uttryck", "utgang", "handling"]:
        g = {}
        for j in np.where(mask)[0]:
            if F[j].get(falt): g.setdefault(F[j][falt], []).append(y[j])
        print(f"  {falt}: " + "  ".join(f"{k} {np.mean(x):+.2f} (n {len(x)})" for k, x in sorted(g.items(), key=lambda t: -np.mean(t[1]))))
    gp = v("relation", "gast_personal")
    prov("HE20a gäst–personal mot tilltal/ingen", mask, gp, v("relation", "avsandare_publik", "ingen"))
    prov("HE20a utan klipp där insatsen är pengar", mask & ~v("insats", "pengar"), gp, v("relation", "avsandare_publik", "ingen"))
    prov("HE20b tydlig friktion mot ingen", mask, v("friktion", "tydlig"), v("friktion", "ingen"))
    prov("HE20c gäst–personal mot personal–personal", mask, gp, v("relation", "personal_personal"))
    prov("HE20d gästens/personalens sida mot verksamhetens", mask, v("sida", "gastens", "personalens"), v("sida", "verksamhetens"))
    prov("     friktion inom tilltal", mask & v("relation", "avsandare_publik"), v("friktion", "mild", "tydlig"), v("friktion", "ingen"))
    prov("HE21a eget uttryck mot lånat", mask & har21, v("uttryck", "eget"), v("uttryck", "lanat"))
    prov("HE21b oviss utgång mot ingen", mask & har21, v("utgang", "oviss"), v("utgang", "ingen"))
    prov("     oviss utgång mot spelad", mask & har21, v("utgang", "oviss"), v("utgang", "spelad"))
    prov("HE21c handling sker mot visas", mask & har21, v("handling", "sker"), v("handling", "visas"))
    print()

# HE21d: sju fält, frusen på biblioteket, prövad på replikeringen; motorns rest
FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
D = np.array([[float(f.get(k) == x) for k, xs in FALT.items() for x in xs] for f in F])
tr, te = ~ny & har21, ny & har21
if tr.sum() > 100 and te.sum() > 100:
    Dtr, Dte, ytr, yte = cen(D, tr)[tr], cen(D, te)[te], cen(u, tr)[tr], cen(u, te)[te]
    b = np.linalg.solve(Dtr.T @ Dtr + 5 * np.eye(D.shape[1]), Dtr.T @ ytr); pf = Dte @ b
    M = np.load(ROT / "e17" / "modell.npz"); C = cen(V[I], te)[te]; pm = C @ M["W_hel"].T @ M["b_hel"]
    kon = konto[te]
    def inom(x):
        x = x.copy()
        for k in set(kon): m = kon == k; x[m] -= x[m].mean()
        return x
    pf, pm = inom(pf), inom(pm); rest = pm - np.polyval(np.polyfit(pf, pm, 1), pf)
    print(f"HE21d på replikeringen ({te.sum()} klipp), modeller frusna på biblioteket ({tr.sum()} klipp):")
    print(f"  sju fält:                 rho {sp(pf, yte):+.3f}  (tröskel 0,10)")
    print(f"  motorrummet:              rho {sp(pm, yte):+.3f}")
    print(f"  motorn rensad från fälten: rho {sp(rest, yte):+.3f}  (tröskel 0,05; samband motor–fält {sp(pm, pf):+.2f})")
    print(f"  fälten + motorn (summa av rang): rho {sp(rankdata(pf) + rankdata(pm), yte):+.3f}")
    namn = [f"{k}={x}" for k, xs in FALT.items() for x in xs]
    print("  vikter (bibliotek): " + "  ".join(f"{n} {w:+.2f}" for n, w in sorted(zip(namn, b), key=lambda t: -t[1])))
