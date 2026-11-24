# Kontroller med ägaren: analys enligt data/format/kontroll/forregistrering.json. Skrivs före ägarens svar och ändras inte efteråt.
#   ../scen/.venv/Scripts/python.exe -u format/kontroll_analys.py [svarsfil.json]
# Utan argument används den senaste filen i data/format/kontroll/svar/. Skälen i transkripten kodas separat.
import json, sys, hashlib, random
from pathlib import Path
from collections import Counter
from math import comb
import numpy as np
from scipy.stats import binomtest, mannwhitneyu

K = Path(__file__).resolve().parents[2] / "data" / "format" / "kontroll"
fr = json.loads((K / "forregistrering.json").read_text(encoding="utf-8"))
for f, h in fr["sha256"].items():
    if hashlib.sha256((K / f).read_bytes()).hexdigest() != h: print(f"VARNING: {f} har ändrats efter låsningen")
las = json.loads((K / "las.json").read_text(encoding="utf-8"))
fil = Path(sys.argv[1]) if len(sys.argv) > 1 else max((K / "svar").glob("*.json"), key=lambda p: p.stat().st_mtime)
S = json.loads(fil.read_text(encoding="utf-8")); print(f"svar: {fil.name}\n")

# ---------- K1 ----------
sv = S["K1"]["svar"]; rad = [(p, sv.get(str(p["nr"]))) for p in las["K1"]]; rad = [(p, s) for p, s in rad if s and s.get("val") in ("v", "h")]
if rad:
    n = len(rad); ny = sum(s["val"] == p["prognos_nytta"] for p, s in rad); fa = n - ny
    ut = sum(s["val"] == p["prognos_utfall"] for p, s in rad)
    a = [(p, s) for p, s in rad if p["typ"] == "hylla_mot_falt"]; ka = sum(s["val"] == p["prognos_nytta"] for p, s in a)
    ok = lambda t: "HÅLLER" if t else "faller"
    print(f"K1 ({n} par med val, {len(las['K1']) - n} utan/båda/inget)")
    print(f"  HK1a nyttans klipp {ny}/{n}  p {binomtest(ny, n, 0.5, alternative='greater').pvalue:.3f}  {ok(binomtest(ny, n, 0.5, alternative='greater').pvalue < 0.05)}")
    print(f"  HK1b fältens klipp {fa}/{n}  p {binomtest(fa, n, 0.5, alternative='greater').pvalue:.3f}  {ok(binomtest(fa, n, 0.5, alternative='greater').pvalue < 0.05)}")
    print(f"  HK1c kärnan i typ a {ka}/{len(a)}  {ok(len(a) and ka >= max(1, round(len(a) * 0.75)))}")
    byt = [(p, s) for p, s in rad if s.get("efter") in ("v", "h") and s["efter"] != s["val"]]
    mot_utfall = sum(s["efter"] == p["prognos_utfall"] for p, s in byt)
    print(f"  HK1d byten efter siffrorna {len(byt)} (mot klippet som gått bäst: {mot_utfall}); osäker {sum(s.get('efter') == 'osaker' for p, s in rad)}  {ok(len(byt) <= 2)}")
    print(f"  HK1e bästa utfallet valt före siffrorna {ut}/{n}  {ok(ut <= 12)}")
    print(f"  per typ: a nytta {ka}/{len(a)}, b nytta {ny - ka}/{n - len(a)}\n")

# ---------- K2 ----------
iso = {m["nr"]: m for m in las["K2"]["isolerat_ordning"]}; E = S["K2"]["ensam"]; R = S["K2"]["remsa"]
d = {"barande": [], "ihopkastat": []}; ensam = {"barande": [], "ihopkastat": []}; per_konto = []; bar_ok = fyll_ok = n_k = 0
for j, k in enumerate(las["K2"]["konton"], 1):
    r = R.get(str(j)); bok = {x["id"]: x["bokstav"] for x in k["remsa"]}; roll = {x["bokstav"]: x["roll"] for x in k["remsa"]}
    if not r: continue
    n_k += 1; dk = {}
    for rl, i in k["mal"].items():
        e = next((E.get(str(nr), {}).get("b") for nr, m in iso.items() if m["id"] == i), None); o = r.get("om", {}).get(bok[i])
        if e is not None: ensam[rl].append(e)
        if e is not None and o is not None: d[rl].append(o - e); dk[rl] = o - e
    if len(dk) == 2: per_konto.append(dk["barande"] - dk["ihopkastat"])
    bar_ok += roll.get(r.get("bar")) == "barande"; fyll_ok += roll.get(r.get("fyll")) == "ihopkastat"
if n_k:
    m = lambda x: float(np.mean(x)) if x else float("nan")
    print(f"K2 ({n_k} konton)")
    print(f"  HK2a förändring bärande {m(d['barande']):+.2f} mot ihopkastat {m(d['ihopkastat']):+.2f}; rätt håll i {sum(x > 0 for x in per_konto)}/{len(per_konto)} konton  {'HÅLLER' if m(d['barande']) > m(d['ihopkastat']) and sum(x > 0 for x in per_konto) >= 3 else 'faller'}")
    print(f"  HK2b bär-valet är bärande i {bar_ok}/{n_k}  {'HÅLLER' if bar_ok >= 3 else 'faller'}  (basnivå hög, se förregistreringen)")
    print(f"  HK2c utfyllnad är ihopkastat i {fyll_ok}/{n_k}  {'HÅLLER' if fyll_ok >= 2 else 'faller'}")
    print(f"  HK2d ensamt: bärande {m(ensam['barande']):.2f} mot ihopkastat {m(ensam['ihopkastat']):.2f}  {'HÅLLER' if m(ensam['barande']) > m(ensam['ihopkastat']) else 'faller'}\n")

# ---------- K3 ----------
def ari(a, b):
    n = len(a); c = Counter(zip(a, b)); s = lambda x: sum(comb(v, 2) for v in x)
    sij, sa, sb = s(c.values()), s(Counter(a).values()), s(Counter(b).values()); e = sa * sb / comb(n, 2); mx = (sa + sb) / 2
    return (sij - e) / (mx - e) if mx != e else 0.0
H3 = S["K3"]; hog_av = {nr: h["id"] for h in H3["hogar"] for nr in h["kort"]}
k3 = [x for x in las["K3"] if x["nr"] in hog_av]
if len(k3) >= 10:
    a = [hog_av[x["nr"]] for x in k3]; b = [x["cell"] for x in k3]; obs = ari(a, b); rng = random.Random(1)
    perm = [ari(a, rng.sample(b, len(b))) for _ in range(5000)]; p95 = float(np.percentile(perm, 95))
    print(f"K3 ({len(k3)} av {len(las['K3'])} sorterade, {len(set(a))} högar)")
    print(f"  HK3a ARI mot fältcellen {obs:.3f}, 95:e percentil {p95:.3f}  {'HÅLLER' if obs > p95 else 'faller'}")
    if H3.get("mest") is not None:
        inne = [x for x in k3 if hog_av[x["nr"]] == H3["mest"]]; ute = [x for x in k3 if hog_av[x["nr"]] != H3["mest"]]
        fi, fu = [x["faltpoang"] for x in inne], [x["faltpoang"] for x in ute]
        ui, uu = [np.log(x["siffror"]["mot_kontot"]) for x in inne if x["siffror"]["mot_kontot"]], [np.log(x["siffror"]["mot_kontot"]) for x in ute if x["siffror"]["mot_kontot"]]
        pf = mannwhitneyu(fi, fu, alternative="greater").pvalue if fi and fu else float("nan")
        pu = mannwhitneyu(ui, uu, alternative="greater").pvalue if ui and uu else float("nan")
        print(f"  HK3b fältpoäng mest LeTrend {np.mean(fi):+.2f} mot övriga {np.mean(fu):+.2f}, p {pf:.3f}  {'HÅLLER' if pf < 0.10 else 'faller'}")
        print(f"  HK3c utfall mest LeTrend ×{np.exp(np.mean(ui)):.2f} mot övriga ×{np.exp(np.mean(uu)):.2f}, p {pu:.3f}  {'HÅLLER' if pu > 0.10 else 'faller'}")
    for h in H3["hogar"]:
        x = [y for y in k3 if hog_av[y["nr"]] == h["id"]]
        if x: print(f"    hög {h['id']} '{h['namn']}' n {len(x)}: celler {dict(Counter(y['cell'] for y in x))}")
