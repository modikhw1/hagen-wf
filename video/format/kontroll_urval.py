# Kontroller med ägaren (18 nov 2026): urval av klipp till K1–K3, med reserver.
#   ../scen/.venv/Scripts/python.exe -u format/kontroll_urval.py
# Skriver data/format/kontroll/kandidater.json. Inget låses här; låsning sker i kontroll_las.py
# när klippen är nedladdade (reserver fyller i för borttagna klipp).
#
# K1  smak mot utfall: par där fältmodellen (publikens utfall) och biblioteket/nyttan (ägarnära) går isär.
# K2  serien och uppfattningen: per konto två mål (Argon E16: bärande resp. ihopkastat) i en remsa om sex.
# K3  fri sortering: 30 klipp brett över fältprofiler och hyllor, ett per konto.
import json, random, re
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROT = Path(__file__).resolve().parents[2]
F = ROT / "data" / "format"
UT = F / "kontroll"; UT.mkdir(exist_ok=True)
rng = random.Random(1118)

FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
B = np.load(F / "e21" / "faltvikter.npy")


def falt(i):
    a, b = F / "e20" / "lasning" / f"{i}.json", F / "e21" / "lasning" / f"{i}.json"
    if not (a.exists() and b.exists()): return None
    return {**json.loads(a.read_text(encoding="utf-8")), **json.loads(b.read_text(encoding="utf-8"))}


def fpoang(i):
    f = falt(i)
    return None if f is None else float(np.array([float(f.get(k) == x) for k, xs in FALT.items() for x in xs]) @ B)


# Klipp ägaren redan sett (pass 1–8, kalibrering, validering, E13-planen)
sett = set()
for k in json.loads((F / "e13" / "plan.json").read_text(encoding="utf-8")).values():
    sett |= {c["id"].rsplit("-", 1)[-1] for c in k["kandidater"]}   # historiken visades inte som klipp
for p in [ROT / "karta" / "videoforandring" / "miles", F / "kalib", F / "harness" / "pass6", F / "harness" / "pass7", F / "harness" / "pass8", F / "harness" / "validering"]:
    for fil in ([p] if p.is_file() else p.rglob("*")):
        if fil.is_file() and fil.suffix in (".json", ".md", ".txt"):
            sett |= set(re.findall(r"\d{19}", fil.read_text(encoding="utf-8", errors="ignore")))
nid = lambda i: i.rsplit("-", 1)[-1]
osett = lambda i: nid(i) not in sett

U = {}
for l in (F / "e15" / "motorer-flash.jsonl").read_text(encoding="utf-8").splitlines():
    if l.strip():
        r = json.loads(l)
        if r.get("u") is not None: U[r["id"]] = r["u"]

bib = json.loads((F / "harness" / "bibliotek-v6.json").read_text(encoding="utf-8"))
H = {k["id"]: k for k in sum(bib["hyllor"].values(), [])}
url = lambda i: H[i]["url"] if i in H and H[i].get("url") else f"https://www.tiktok.com/@{i.rsplit('-', 1)[0]}/video/{nid(i)}"
konto = lambda i: i.rsplit("-", 1)[0]

# ---------- K1 ----------
kand = [i for i in H if osett(i) and i in U and fpoang(i) is not None and H[i].get("nytta_v62") is not None]
fp = dict(zip(kand, rankdata([fpoang(i) for i in kand]) / len(kand)))
npz = dict(zip(kand, rankdata([H[i]["nytta_v62"] for i in kand]) / len(kand)))
rang = {"karna": 2, "mitten": 1, "situation": 1, "capcut_referens": 0, "ute": 0}

def parlista(A, Bl, typ, n):
    A, Bl = A[:], Bl[:]; rng.shuffle(A); rng.shuffle(Bl); ut, anv = [], {}
    ok = lambda x: anv.get(konto(x), 0) < 2 and x not in brukad
    for a in A:
        if not ok(a): continue
        for b in Bl:
            if konto(a) != konto(b) and ok(b):
                ut.append({"typ": typ, "bibliotek": a, "falt": b}); Bl.remove(b)
                for x in (a, b): anv[konto(x)] = anv.get(konto(x), 0) + 1; brukad.add(x)
                break
        if len(ut) >= n: break
    return ut

# a) E22-typen: kärna med låg fältpoäng mot ute/capcut med hög fältpoäng
brukad = set()
k_lag = [i for i in kand if rang[H[i]["hylla"]] == 2 and fp[i] < 0.2]
u_hog = [i for i in kand if rang[H[i]["hylla"]] == 0 and fp[i] > 0.8]
print("listor", len(k_lag), len(u_hog))
# b) mitten: samma hyllnivå, nyttan hög/fält låg mot nyttan låg/fält hög
m_ny = [i for i in kand if rang[H[i]["hylla"]] >= 1 and npz[i] > 0.6 and fp[i] < 0.35]
m_fa = [i for i in kand if rang[H[i]["hylla"]] >= 1 and npz[i] < 0.4 and fp[i] > 0.65]
print("mitten", len(m_ny), len(m_fa))
K1 = parlista(k_lag, u_hog, "hylla_mot_falt", 16) + parlista(m_ny, m_fa, "nytta_mot_falt_mitten", 16)

# ---------- K2 ----------
# Per konto: ett bärande och ett ihopkastat mål (osedda) + fyra grannar i kontots ordning = remsa om sex.
K2 = []
for fil in sorted((F / "e16" / "roller").glob("*.json")):
    r = json.loads(fil.read_text(encoding="utf-8")); ids = r["ids"]
    roll = {k["nr"]: k["roll"] for k in r["klipp"]}
    bar = [n for n in range(1, len(ids) + 1) if roll.get(n) == "barande" and osett(ids[n - 1])]
    ihop = [n for n in range(1, len(ids) + 1) if roll.get(n) == "ihopkastat" and osett(ids[n - 1])]
    if not bar or not ihop: continue
    nb, ni = rng.choice(bar), rng.choice(ihop)
    ovr = sorted((n for n in range(1, len(ids) + 1) if n not in (nb, ni) and osett(ids[n - 1])), key=lambda n: min(abs(n - nb), abs(n - ni)))[:4]
    remsa = sorted([nb, ni] + ovr)
    K2.append({"konto": r["konto"], "mal": {"barande": ids[nb - 1], "ihopkastat": ids[ni - 1]},
               "remsa": [{"nr": n, "id": ids[n - 1], "roll": roll.get(n)} for n in remsa]})
rng.shuffle(K2); K2 = K2[:6]   # fyra används, två reserver

# ---------- K3 ----------
pool = [i for i in set(U) | set(H) if osett(i) and falt(i) is not None]
def cell(i):
    f = falt(i); rel = f.get("relation") if f.get("relation") in FALT["relation"] else "ingen"
    return f"{rel}|{'friktion' if f.get('friktion') in ('mild', 'tydlig') else 'lugn'}"
celler = {}
for i in pool: celler.setdefault(cell(i), []).append(i)
for v in celler.values(): rng.shuffle(v)
K3, anv = [], set()
nycklar = sorted(celler)
while len(K3) < 40 and any(celler.values()):
    for c in nycklar:
        while celler[c]:
            i = celler[c].pop()
            if konto(i) not in anv: K3.append({"id": i, "cell": c, "hylla": H[i]["hylla"] if i in H else "replikering"}); anv.add(konto(i)); break

alla = {x for p in K1 for x in (p["bibliotek"], p["falt"])} | {x["id"] for k in K2 for x in k["remsa"]} | {x["id"] for x in K3}
(UT / "kandidater.json").write_text(json.dumps({"K1": K1, "K2": K2, "K3": K3, "url": {i: url(i) for i in sorted(alla)}, "antal_sett": len(sett)}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"sett {len(sett)} | K1 par {len(K1)} (a {sum(p['typ']=='hylla_mot_falt' for p in K1)}) | K2 konton {len(K2)} | K3 {len(K3)} | klipp att hämta {len(alla)}")
