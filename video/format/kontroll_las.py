# Kontroller med ägaren: låser urval, ordning och prognoser innan ägaren ser något.
#   ../scen/.venv/Scripts/python.exe -u format/kontroll_las.py
# Läser kandidater.json + hämtade klipp. Skriver forregistrering.json (prognoser, hypoteser, sha256 per låst fil),
# las.json (allt som analysen behöver: fält, hylla, nytta, roller, utfall) och spelare/data.js (bara det spelaren visar).
import json, random, hashlib
from pathlib import Path
import numpy as np
from scipy.stats import binom

ROT = Path(__file__).resolve().parents[2]
F = ROT / "data" / "format"; K = F / "kontroll"; KL = K / "klipp"
if (K / "forregistrering.json").exists(): raise SystemExit("Redan låst. Ta bort forregistrering.json bara om ägaren inte sett något.")
rng = random.Random(20261118)
kand = json.loads((K / "kandidater.json").read_text(encoding="utf-8"))
har = lambda i: (KL / f"{i}.mp4").exists()
konto = lambda i: i.rsplit("-", 1)[0]
nid = lambda i: i.rsplit("-", 1)[-1]

FALT = {"relation": ["gast_personal", "personal_personal", "avsandare_publik"], "friktion": ["mild", "tydlig"], "insats": ["pengar", "tid_arbete", "status", "smak"], "sida": ["gastens", "personalens"], "uttryck": ["eget", "lanat"], "utgang": ["oviss", "spelad"], "handling": ["sker", "berattas"]}
B = np.load(F / "e21" / "faltvikter.npy")
def falt(i):
    a, b = F / "e20" / "lasning" / f"{i}.json", F / "e21" / "lasning" / f"{i}.json"
    return {**json.loads(a.read_text(encoding="utf-8")), **json.loads(b.read_text(encoding="utf-8"))} if a.exists() and b.exists() else None
fp = lambda i: None if falt(i) is None else round(float(np.array([float(falt(i).get(k) == x) for k, xs in FALT.items() for x in xs]) @ B), 3)
bib = json.loads((F / "harness" / "bibliotek-v6.json").read_text(encoding="utf-8"))
H = {k["id"]: k for k in sum(bib["hyllor"].values(), [])}

# Publiksiffror ur bankens listor: visningar mot medianen av ±10 grannar i tid inom kontot (samma definition som u)
LISTA = {}
def siffror(i):
    k = konto(i)
    if k not in LISTA:
        p = ROT / "data" / "bank" / k / "lista.json"
        LISTA[k] = json.loads(p.read_text(encoding="utf-8"))["klipp"] if p.exists() else []
    L = sorted([x for x in LISTA[k] if x.get("visningar")], key=lambda x: x.get("datum") or "")
    for j, x in enumerate(L):
        if x["id"] == nid(i):
            gr = [y["visningar"] for y in L[max(0, j - 10):j] + L[j + 1:j + 11]]
            med = float(np.median(gr)) if gr else None
            return {"visningar": x["visningar"], "gillanden": x.get("gillanden"), "kommentarer": x.get("kommentarer"), "delningar": x.get("delningar"),
                    "datum": x.get("datum"), "mot_kontot": round(x["visningar"] / med, 2) if med else None}
    return None

# ---------- K1: 20 par, 6–8 av typ a ----------
par = [p for p in kand["K1"] if har(p["bibliotek"]) and har(p["falt"]) and siffror(p["bibliotek"]) and siffror(p["falt"])]
a = [p for p in par if p["typ"] == "hylla_mot_falt"]; b = [p for p in par if p["typ"] != "hylla_mot_falt"]
K1 = a[:8] + b[:20 - len(a[:8])]
rng.shuffle(K1)
k1 = []
for n, p in enumerate(K1, 1):
    vanster_bib = rng.random() < 0.5
    v, h = (p["bibliotek"], p["falt"]) if vanster_bib else (p["falt"], p["bibliotek"])
    sv, sh = siffror(v), siffror(h)
    k1.append({"nr": n, "typ": p["typ"], "vanster": v, "hoger": h,
               "prognos_nytta": "v" if vanster_bib else "h", "prognos_falt": "h" if vanster_bib else "v",
               "prognos_utfall": "v" if sv["mot_kontot"] >= sh["mot_kontot"] else "h",
               "las": {x: {"hylla": H[x]["hylla"], "nytta_v62": H[x].get("nytta_v62"), "letrend_varde": H[x].get("letrend_varde"), "faltpoang": fp(x), "falt": falt(x), "karna": H[x].get("karna"), "siffror": siffror(x)} for x in (v, h)}})

# ---------- K2: fyra konton ----------
k2 = []
for k in kand["K2"]:
    if len(k2) == 4: break
    if not all(har(x["id"]) for x in k["remsa"]): continue
    k2.append(k)
mal = [(k["konto"], r, i) for k in k2 for r, i in k["mal"].items()]
rng.shuffle(mal)
for k in k2:
    for j, x in enumerate(k["remsa"]): x["bokstav"] = "ABCDEF"[j]
andel_bar = float(np.mean([sum(x["roll"] == "barande" for x in k["remsa"]) / len(k["remsa"]) for k in k2]))
andel_ihop = float(np.mean([sum(x["roll"] == "ihopkastat" for x in k["remsa"]) / len(k["remsa"]) for k in k2]))

# ---------- K3: 30 klipp med utfall, ett per konto, bred spridning ----------
k3 = [x for x in kand["K3"] if har(x["id"]) and siffror(x["id"])][:30]
rng.shuffle(k3)
for j, x in enumerate(k3, 1):
    x["nr"] = j; x["faltpoang"] = fp(x["id"]); x["falt"] = falt(x["id"]); x["siffror"] = siffror(x["id"])
    x["nytta_v62"] = H.get(x["id"], {}).get("nytta_v62")

las = {"K1": k1, "K2": {"konton": k2, "isolerat_ordning": [{"nr": j, "konto": k, "roll": r, "id": i} for j, (k, r, i) in enumerate(mal, 1)]}, "K3": k3}
(K / "las.json").write_text(json.dumps(las, ensure_ascii=False, indent=1), encoding="utf-8")

# Spelaren får bara id, nummer och (i K1, efter valet) publiksiffrorna
spel = {"K1": [{"nr": p["nr"], "vanster": p["vanster"], "hoger": p["hoger"], "siffror": {"v": p["las"][p["vanster"]]["siffror"], "h": p["las"][p["hoger"]]["siffror"]}} for p in k1],
        "K2": {"isolerat": [{"nr": m["nr"], "id": m["id"]} for m in las["K2"]["isolerat_ordning"]],
               "remsor": [{"nr": j, "remsa": [{"bokstav": x["bokstav"], "id": x["id"]} for x in k["remsa"]],
                           "mal": [next(x["bokstav"] for x in k["remsa"] if x["id"] == i) for i in (k["mal"]["barande"], k["mal"]["ihopkastat"])]} for j, k in enumerate(k2, 1)]},
        "K3": [{"nr": x["nr"], "id": x["id"]} for x in k3]}
# målen i remsan visas i bokstavsordning, inte i rollordning
for r in spel["K2"]["remsor"]: r["mal"].sort()
(K / "spelare").mkdir(exist_ok=True)
(K / "spelare" / "data.js").write_text("window.KONTROLL = " + json.dumps(spel, ensure_ascii=False) + ";\n", encoding="utf-8")

n1 = len(k1); kr = int(binom.ppf(0.95, n1, 0.5)) + 1
na = sum(p["typ"] == "hylla_mot_falt" for p in k1)
fr = {
 "namn": "Kontroller med ägaren K1–K4", "datum": "2026-11-17", "las_tid": "före ägarens första sittning",
 "princip": "Ägarens svar är avläsning. Inga skalor eller prompter skrivs om efter svaren. Skälen ägaren ger används bara som källa till nya abstrakta hypoteser, som sedan prövas mot utfall och undanhållna konton i andra experiment.",
 "skyddsregler": ["Klippen spelas lokalt utan publiksiffror (spelare/index.html).", "Miles läser aldrig upp modellens bedömning, kategorier eller hyllor.", "Ägaren har inte sett något av klippen i pass 1–8 (kontrollerat mot id i miles/, kalib/, harness/pass6–8, validering/, E13-kandidater).", "Vänster/höger och ordning slumpade med fröt 20261118."],
 "K1": {"fraga": "Vilket av de två klippen vill du hellre ha i LeTrends bibliotek?", "n_par": n1, "n_typ_a": na,
        "design": "Typ a: bibliotekets kärna med låg fältpoäng mot hyllan ute/capcut med hög fältpoäng. Typ b: samma hyllnivå (mitten/situation/kärna), nyttan v6.2 hög och fältpoängen låg mot tvärtom. Nyttan och fälten pekar alltså alltid åt olika håll. Efter valet visas publiksiffrorna (visningar mot kontots grannar, gillanden, kommentarer, delningar) och ägaren får ändra.",
        "hypoteser": {
          "HK1a": f"Ägaren väljer nyttans/bibliotekets klipp i minst {kr} av {n1} par (binomial p < 0,05). Grund: pass 7 (nytta 16/19, fält 11/19).",
          "HK1b": f"Ägaren väljer fältens klipp i minst {kr} av {n1} par. Konkurrerande hypotes; om ingen av HK1a/HK1b håller är smaken blandad och skälen är huvuddatan.",
          "HK1c": f"I typ a väljer ägaren kärnklippet i minst {max(1, round(na * 0.75))} av {na}.",
          "HK1d": "När siffrorna visas ändrar ägaren sig i högst 2 av 20 par. Fler än 3 ändringar räknas som att publiksiffrorna styr smaken; riktningen (mot det klipp som gått bäst mot kontot) redovisas.",
          "HK1e": "Det klipp som gått bäst mot kontot (prognos_utfall) väljs i högst 12 av 20 före siffrorna, alltså inget samband mellan ägarens smak och publikens utfall (replikerar E32)."},
        "utforskande": "Skälen kodas fritt, utan förbestämda kategorier, och jämförs med de sju fälten: vilka skäl har inget fält."},
 "K2": {"fraga": "Hur starkt är klippet, 1–5? Först ensamt, sedan i kontots remsa om sex klipp. Därefter: vilket klipp i remsan bär kontot, och vilket är utfyllnad?",
        "design": "Fyra konton ur E16. Per konto ett klipp som Argon kallade bärande och ett som Argon kallade ihopkastat, båda osedda, plus fyra grannar i tid. Alla åtta mål bedöms först ensamma i slumpad ordning, sedan i remsorna.",
        "hypoteser": {
          "HK2a": "Medelförändringen (remsa minus ensamt) är högre för bärande mål än för ihopkastade, och åt det hållet i minst 3 av 4 konton.",
          "HK2b": f"Klippet ägaren säger bär kontot är Argons bärande klipp (vilket som helst av dem i remsan) i minst 3 av 4 konton. Basnivå: {andel_bar:.2f} av remsan är bärande.",
          "HK2c": f"Klippet ägaren kallar utfyllnad är Argons ihopkastade i minst 2 av 4 konton. Basnivå: {andel_ihop:.2f} av remsan är ihopkastad.",
          "HK2d": "Ensamt bedömt får bärande mål högre medel än ihopkastade (Argons roller syns även utan serien)."},
        "obs": "Omtittning är en störning som gäller alla mål lika; HK2a jämför skillnaden mellan rollerna, inte förändringen i sig."},
 "K3": {"fraga": "Lägg klippen i högar efter vad du tycker hör ihop. Så många högar du vill. Namnge dem efteråt och markera den hög som är mest LeTrend.",
        "design": "30 klipp, ett per konto, spridda över relation × friktion i fälten och över hyllor och replikering. Inga kategorier ges.",
        "hypoteser": {
          "HK3a": "Ägarens högar stämmer med fältcellen (relation × friktion) bättre än slumpen: justerat Rand-index över 95:e percentilen av 5 000 permutationer.",
          "HK3b": "Högen ägaren markerar som mest LeTrend har högre medel-fältpoäng än övriga klipp (rangsumma, p < 0,10).",
          "HK3c": "Högen ägaren markerar som mest LeTrend har INTE högre utfall mot kontot än övriga (p > 0,10), i linje med att ägarens val och publikens utfall är olika saker (E22, E32)."},
        "utforskande": "Högarnas namn jämförs med E17-axlarna och med orden i E18; nya ord som saknas i båda listas som kandidater till abstrakta hypoteser."},
 "K4": {"fraga": "Pass 8b (klient B–F), oförändrat. Underlag och låst ordning i karta/videoforandring/miles/pass-8b*. Låst sedan 6 nov."},
}
fr["sha256"] = {f: hashlib.sha256((K / f).read_bytes()).hexdigest() for f in ["las.json", "spelare/data.js", "kandidater.json"]}
(K / "forregistrering.json").write_text(json.dumps(fr, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"K1 {n1} par (typ a {na}), tröskel {kr} | K2 {len(k2)} konton, bärande-andel {andel_bar:.2f}, ihop {andel_ihop:.2f} | K3 {len(k3)} klipp")
print("prognos utfall = nytta i", sum(p['prognos_utfall'] == p['prognos_nytta'] for p in k1), "av", n1)
