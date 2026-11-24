# E41: två domar. Förregistrering data/format/e41/forregistrering.json.
#   ../scen/.venv/Scripts/python.exe -u format/e41_analys.py
# Del 1: utfall på replikeringen (HE41a–d). Del 2: K1 par 1–12 i provet (utforskande). Del 3: låser prognoser för par 13–20 (HE41e–g).
import json, hashlib, random
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from scipy.stats import spearmanr, mannwhitneyu

ROT = Path(__file__).resolve().parents[2]; F = ROT / "data" / "format"; E = F / "e41"
L = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (E / "lasning").glob("*.json")}
U = {}
for l in (F / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(l); U[r["id"]] = (r["konto"], r["u"])

FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
B = np.load(F / "e21" / "faltvikter.npy")
def fp(i, suf="-argon"):
    a, b = F / "e20" / f"lasning{suf}" / f"{i}.json", F / "e21" / f"lasning{suf}" / f"{i}.json"
    if not (a.exists() and b.exists()): return None
    f = {**json.loads(a.read_text(encoding="utf-8")), **json.loads(b.read_text(encoding="utf-8"))}
    return float(np.array([float(f.get(k) == x) for k, xs in FALT.items() for x in xs]) @ B)

def centrera(ids, v):
    g = defaultdict(list)
    for i in ids: g[U[i][0]].append(i)
    out = {}
    for k, xs in g.items():
        if len(xs) < 2: continue
        m = np.mean([v(i) for i in xs])
        for i in xs: out[i] = v(i) - m
    return out

def inom(ids, x, rng=random.Random(41), n=5000):
    """Spearman mellan inom-konto-centrerat x och u, p via permutation av x inom konto."""
    ids = [i for i in ids if x(i) is not None]
    cx, cu = centrera(ids, x), centrera(ids, lambda i: U[i][1]); ids = [i for i in ids if i in cx]
    obs = spearmanr([cx[i] for i in ids], [cu[i] for i in ids])[0]
    g = defaultdict(list)
    for i in ids: g[U[i][0]].append(i)
    cnt = 0
    for _ in range(n):
        perm = {}
        for k, xs in g.items():
            v = [cx[i] for i in xs]; rng.shuffle(v); perm.update(zip(xs, v))
        cnt += abs(spearmanr([perm[i] for i in ids], [cu[i] for i in ids])[0]) >= abs(obs)
    return obs, (cnt + 1) / (n + 1), len(ids), len(g)

def del1(namn, ids):
    ids = [i for i in ids if i in L and i in U and U[i][1] is not None]
    print(f"\n== {namn}: {len(ids)} klipp ==")
    r, p, n, k = inom(ids, lambda i: L[i]["transferable"]); print(f"HE41a överförbar mot u: rho {r:+.3f} p {p:.3f} (n {n}, {k} konton)  {'HÅLLER' if r <= 0.02 else 'faller'}")
    r, p, n, k = inom(ids, lambda i: L[i]["hold"]); print(f"HE41b hålla mot u:      rho {r:+.3f} p {p:.3f}  {'HÅLLER' if r > 0 and p < 0.05 else 'faller'}")
    r, p, n, k = inom(ids, lambda i: (L[i]["swipe_second"] if L[i]["swipe_second"] >= 0 else 99)); print(f"  (utforskande) svepsekund (ingen = 99) mot u: rho {r:+.3f} p {p:.3f}")
    cu = centrera(ids, lambda i: U[i][1])
    for b, c in Counter(L[i]["carrier"] for i in ids).most_common():
        v = [cu[i] for i in ids if i in cu and L[i]["carrier"] == b]; print(f"  bärare {b:12} n {c:3}  u inom konto ×{np.exp(np.mean(v)):.2f}" if v else f"  bärare {b} n {c}")
    pp = [cu[i] for i in ids if i in cu and L[i]["carrier"] in ("person", "production")]; pr = [cu[i] for i in ids if i in cu and L[i]["carrier"] == "premise"]
    p = mannwhitneyu(pp, pr, alternative="greater").pvalue
    print(f"HE41d person/produktion ×{np.exp(np.mean(pp)):.2f} (n {len(pp)}) mot premiss ×{np.exp(np.mean(pr)):.2f} (n {len(pr)}), p {p:.3f}  {'HÅLLER' if p < 0.10 else 'faller'}")
    print(f"  korrelation överförbar–hålla (rå): {spearmanr([L[i]['transferable'] for i in ids], [L[i]['hold'] for i in ids])[0]:+.2f}")
    return ids

arg = json.loads((F / "e19" / "argon-ids.json").read_text(encoding="utf-8"))
ids = del1("replikering, Argon-delen (240)", arg)

# HE41c: hålla utöver fälten, inom konto (OLS på centrerade värden, p via permutation av hålla inom konto)
ids_f = [i for i in ids if fp(i) is not None]
cf, ch, cu = centrera(ids_f, fp), centrera(ids_f, lambda i: L[i]["hold"]), centrera(ids_f, lambda i: U[i][1])
ids_f = [i for i in ids_f if i in cf]
X = np.c_[[cf[i] for i in ids_f], [ch[i] for i in ids_f]]; y = np.array([cu[i] for i in ids_f])
beta = np.linalg.lstsq(X, y, rcond=None)[0]
g = defaultdict(list)
for i in ids_f: g[U[i][0]].append(i)
rng = random.Random(4141); cnt = 0
for _ in range(5000):
    perm = {}
    for k, xs in g.items():
        v = [ch[i] for i in xs]; rng.shuffle(v); perm.update(zip(xs, v))
    Xp = np.c_[X[:, 0], [perm[i] for i in ids_f]]; cnt += np.linalg.lstsq(Xp, y, rcond=None)[0][1] >= beta[1]
print(f"HE41c hålla utöver Argon-fälten: koefficient {beta[1]:+.3f} (fält {beta[0]:+.3f}), ensidigt p {(cnt + 1) / 5001:.3f}, n {len(ids_f)}  {'HÅLLER' if beta[1] > 0 and (cnt + 1) / 5001 < 0.10 else 'faller'}")
print(f"  rå: fält mot u rho {spearmanr([cf[i] for i in ids_f], y)[0]:+.3f}; hålla mot fält rho {spearmanr([cf[i] for i in ids_f], [ch[i] for i in ids_f])[0]:+.3f}")

rest = [i for i in json.loads((F / "e19" / "ids.json").read_text(encoding="utf-8")) if i not in set(arg)]
if sum(i in L for i in rest) >= 100: del1(f"replikering, resten ({sum(i in L for i in rest)})", rest)

# ---------- Del 2: K1 par 1–12 (i provet) ----------
las = {p["nr"]: p for p in json.loads((F / "kontroll" / "las.json").read_text(encoding="utf-8"))["K1"]}
kons = {x["nr"]: x for x in json.loads((F / "kontroll" / "kodning" / "k1-del1-konsensus.json").read_text(encoding="utf-8"))}
print("\n== K1 par 1–12 (i provet) ==\npar  bib smak | överf v/h  hålla v/h | bärare v/h")
tr = {"bib": [0, 0], "smak": [0, 0]}
for n in range(1, 13):
    p = las[n]; v, h = L.get(p["vanster"]), L.get(p["hoger"]); k = kons[n]
    if not (v and h): print(n, "saknar läsning"); continue
    print(f"{n:3}  {k['bib']:5} {k['smak']:4} | {v['transferable']} / {h['transferable']}      {v['hold']} / {h['hold']}    | {v['carrier']} / {h['carrier']}")
    if k["bib"] in ("v", "h") and v["transferable"] != h["transferable"]:
        tr["bib"][1] += 1; tr["bib"][0] += (k["bib"] == "v") == (v["transferable"] > h["transferable"])
    if k["smak"] in ("v", "h") and v["hold"] != h["hold"]:
        tr["smak"][1] += 1; tr["smak"][0] += (k["smak"] == "v") == (v["hold"] > h["hold"])
print(f"bib = högst överförbar {tr['bib'][0]}/{tr['bib'][1]};  smak = högst hålla {tr['smak'][0]}/{tr['smak'][1]}")

# ---------- Del 3: låsta prognoser för par 13–20 ----------
prog = {}
for n in range(13, 21):
    p = las[n]; v, h = L.get(p["vanster"]), L.get(p["hoger"])
    if not (v and h): prog[n] = None; continue
    pick = lambda a, b: "v" if a > b else "h" if b > a else "lika"
    prog[n] = {"bib_overforbar": pick(v["transferable"], h["transferable"]), "smak_halla": pick(v["hold"], h["hold"])}
ut = E / "prognos-k1-13-20.json"
if not ut.exists():
    s = json.dumps(prog, indent=1); ut.write_text(s, encoding="utf-8")
    print(f"\nlåst {ut.name} sha256 {hashlib.sha256(s.encode()).hexdigest()[:16]}")
print("prognoser 13–20:", json.dumps(prog))
