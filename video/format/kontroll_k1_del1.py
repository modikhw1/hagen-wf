# K1 del 1 (par 1–12): ägarens val och smak ur transkriptet mot de låsta prognoserna.
#   ../scen/.venv/Scripts/python.exe -u format/kontroll_k1_del1.py
# Valen kommer ur kodningen (Claude + två blinda kodare), eftersom spelarens svarsfil saknas.
# Konsensus = minst två av tre kodare; "?" när ingen majoritet.
import json
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.stats import binomtest

K = Path(__file__).resolve().parents[2] / "data" / "format" / "kontroll"
las = {p["nr"]: p for p in json.loads((K / "las.json").read_text(encoding="utf-8"))["K1"]}
kd = K / "kodning"
c = json.loads((kd / "k1-del1-claude.json").read_text(encoding="utf-8"))["par"]
m = {"first": "v", "second": "h", "neither": "ingen", "both": "båda", "unclear": "?"}
bl = {n: {p["pair"]: p for p in json.loads((kd / f"k1-del1-blind-{n}.json").read_text(encoding="utf-8"))["pairs"]} for n in ("pro", "argon")}

def kons(xs):
    x, n = Counter(xs).most_common(1)[0]
    return x if n >= 2 and x in ("v", "h", "ingen") else "?"

rad = []
for i in range(1, 13):
    p = las[i]
    bib = kons([c[str(i)]["bib"]] + [m[bl[n][i]["library_choice"]] for n in bl])
    sm = kons([c[str(i)]["smak"].replace("oklar", "?")] + [m[bl[n][i]["content_preference"]] for n in bl])
    sv, sh = p["las"][p["vanster"]]["siffror"]["mot_kontot"], p["las"][p["hoger"]]["siffror"]["mot_kontot"]
    rad.append(dict(nr=i, typ=p["typ"], bib=bib, smak=sm, nytta=p["prognos_nytta"], falt=p["prognos_falt"], utfall=p["prognos_utfall"],
                    lr=float(np.log(sv / sh))))  # log(v/h) i utfall mot kontot

def rakna(nyckel, mot):
    r = [x for x in rad if x[nyckel] in ("v", "h")]
    k = sum(x[nyckel] == x[mot] for x in r)
    return k, len(r), binomtest(k, len(r), 0.5).pvalue if r else float("nan")

print("par typ          bib smak nytta fält utfall  log(v/h)")
for x in rad: print(f"{x['nr']:3} {x['typ'][:12]:12} {x['bib']:5} {x['smak']:4} {x['nytta']:5} {x['falt']:4} {x['utfall']:6} {x['lr']:+.2f}")
print()
for nyckel in ("bib", "smak"):
    for mot in ("nytta", "falt", "utfall"):
        k, n, p = rakna(nyckel, mot); print(f"{nyckel:4} = {mot:6}: {k}/{n}  (tvåsidigt p {p:.3f})")
    print()
# utfallsavstånd: hur mycket bättre (log) gick det valda klippet än det andra
for nyckel in ("bib", "smak"):
    d = [x["lr"] if x[nyckel] == "v" else -x["lr"] for x in rad if x[nyckel] in ("v", "h")]
    print(f"{nyckel}: medel log(valt/annat) {np.mean(d):+.2f}  (×{np.exp(np.mean(d)):.2f}), n {len(d)}")
delade = [x for x in rad if x["bib"] in ("v", "h") and x["smak"] in ("v", "h") and x["bib"] != x["smak"]]
print(f"\npar där biblioteket och smaken skiljer sig: {[x['nr'] for x in delade]}")
for x in delade: print(f"  par {x['nr']}: bib={x['bib']} (nytta {x['nytta']}), smak={x['smak']}, utfall={x['utfall']}")
(kd / "k1-del1-konsensus.json").write_text(json.dumps(rad, ensure_ascii=False, indent=1), encoding="utf-8")
