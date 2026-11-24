# E42: parvis läsning med ägarens två frågor. Förregistrering data/format/e42/forregistrering.json.
#   ../scen/.venv/Scripts/python.exe -u format/e42_analys.py
import json
from pathlib import Path
from collections import defaultdict, Counter
from scipy.stats import binomtest

F = Path(__file__).resolve().parents[2] / "data" / "format"; E = F / "e42"
las = defaultdict(dict)
for p in (E / "lasning").glob("*.json"):
    r = json.loads(p.read_text(encoding="utf-8")); las[r["namn"]][r["ordning"]] = r
def enig(namn, fraga):
    x = las.get(namn, {})
    if len(x) < 2: return None
    a, b = x["vh"][fraga], x["hv"][fraga]
    return a if a == b else "oenig"

# ägarens svar
kons = {x["nr"]: x for x in json.loads((F / "kontroll/kodning/k1-del1-konsensus.json").read_text(encoding="utf-8"))}
ag7 = json.loads((F / "harness/pass7/agare.json").read_text(encoding="utf-8"))["val"]
m = {"first": "v", "second": "h"}
B7 = {n: {p["pair"]: p for p in json.loads((F / f"kontroll/kodning/pass7-blind-{n}.json").read_text(encoding="utf-8"))["pairs"]} for n in ("pro", "flash")}
agare = {}
for n, x in kons.items(): agare[f"k1-{n}"] = {"bib": x["bib"], "smak": x["smak"]}
for n in range(1, 21):
    s = [m.get(B7[k][n]["content_preference"], "?") if n in B7[k] else "?" for k in B7]
    agare[f"p7-{n}"] = {"bib": ag7.get(str(n), "-"), "smak": s[0] if s[0] == s[1] and s[0] in "vh" else "?"}

pos = Counter(); oen = Counter(); n_l = 0
for namn, x in las.items():
    for o, r in x.items(): pos[r["viewer"]] += 1; n_l += 1
print(f"positionsbias: A valt som tittare {pos['A']}/{n_l}")

def jamfor(fraga, nyckel, grupp):
    tr = n = oe = 0
    for namn, a in agare.items():
        if not namn.startswith(grupp) or a[nyckel] not in ("v", "h"): continue
        e = enig(namn, fraga)
        if e is None: continue
        if e == "oenig": oe += 1; continue
        n += 1; tr += e == a[nyckel]
    return tr, n, oe
print("\n== ägarparen ==")
for fr, ny, h in (("tittare", "smak", "HE42a"), ("bibliotek", "bib", "HE42b")):
    tot = [0, 0, 0]
    for g in ("k1-", "p7-"):
        t, n, oe = jamfor(fr, ny, g); tot = [tot[0] + t, tot[1] + n, tot[2] + oe]; print(f"  {fr:9} mot ägarens {ny:4} {g}: {t}/{n} (oeniga över ordning {oe})")
    print(f"{h} {fr} = ägarens {ny}: {tot[0]}/{tot[1]} = {tot[0] / max(1, tot[1]):.0%}  {'HÅLLER' if tot[1] and tot[0] / tot[1] >= 0.65 else 'faller'}  (oeniga {tot[2]})")
# läsarens egna två val: skiljer de sig, och åt vilket håll mot ägaren
skil = [(n, enig(n, "tittare"), enig(n, "bibliotek")) for n in agare if enig(n, "tittare") in ("v", "h") and enig(n, "bibliotek") in ("v", "h")]
print(f"  läsaren skiljer tittare/bibliotek i {sum(a != b for _, a, b in skil)}/{len(skil)} ägarpar")

up = E / "urval-utfall.json"
if up.exists():
    U = {}
    for l in (F / "e15/motorer-flash.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(l); U[r["id"]] = r["u"]
    print("\n== utfallsparen ==")
    res = {}
    for fr in ("tittare", "bibliotek"):
        t = n = oe = 0
        for p in json.loads(up.read_text(encoding="utf-8")):
            e = enig(p["namn"], fr)
            if e is None: continue
            if e == "oenig": oe += 1; continue
            hogst = "v" if U[p["v"]] > U[p["h"]] else "h"; n += 1; t += e == hogst
        res[fr] = (t, n, oe)
        print(f"  {fr:9} träffar högst u: {t}/{n} = {t / max(1, n):.0%}, ensidigt p {binomtest(t, n, 0.5, alternative='greater').pvalue if n else float('nan'):.3f}  (oeniga {oe})")
    t, n, _ = res["tittare"]; print(f"HE42c {'HÅLLER' if n and binomtest(t, n, 0.5, alternative='greater').pvalue < 0.05 else 'faller'}")
    t, n, _ = res["bibliotek"]
    sk = [(enig(p["namn"], "tittare"), enig(p["namn"], "bibliotek")) for p in json.loads(up.read_text(encoding="utf-8"))]
    sk = [(a, b) for a, b in sk if a in ("v", "h") and b in ("v", "h")]
    andel = sum(a != b for a, b in sk) / max(1, len(sk))
    print(f"HE42d bibliotek {t}/{n} = {t / max(1, n):.0%}, skiljer sig från tittare i {andel:.0%}  {'HÅLLER' if n and t / n <= 0.55 and andel >= 0.20 else 'faller'}")
