"""Bygger scen-json v0 för ett klipp enligt en av tre metoder.

  2d        : scener + spår (spar.json), automatiskt utsnitt, händelser och motiv
  rum       : som 2d + bakgrund/ankare/golvbanor (rum.json), aktörer ur sammanslagna spår, händelser ur närhet
  semantisk : scener/händelser/avsikt ur handskriven semantik.json; motiv fylls i ur spar.json

Användning: .venv/Scripts/python.exe py/bygg_scen.py <namn> <metod>
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from motiv import normalisera, vektor, T

ROT = Path(__file__).resolve().parent.parent
namn, metod = sys.argv[1], sys.argv[2]
D = ROT / "data" / namn
spar = json.load(open(D / "spar.json", encoding="utf-8"))
bib = json.load(open(ROT / "data" / "bibliotek" / "motiv.json"))
ref = json.load(open(ROT / "data" / "bibliotek" / "referens.json"))
R = np.array(ref["X"]).reshape(-1, ref["dim"]); d90 = ref["d90"]
KX = np.array(ref["kontext"]); D90K = ref["d90_kontext"]
klass = lambda h: "nara" if h > 0.85 else ("halv" if h > 0.5 else "hel")
MV = np.array([vektor(np.array(m["pose"]), np.array(m["rel"])) for m in bib["motiv"]])


def poang(v, k=None):
    RR, dd = (R[KX == k], D90K[k]) if k else (R, d90)
    d = np.sqrt(((RR - v) ** 2).sum(1)).min(); return round(float(np.clip(100 * (1 - 0.2 * d / dd), 0, 100)), 1)


def narmaste_motiv(v):
    d = np.sqrt(((MV - v) ** 2).sum(1)); k = int(d.argmin()); return bib["motiv"][k]["id"], bib["motiv"][k]["namn"]


def utsnitt(bs):
    h = [max([p["box"][3] - p["box"][1] for p in b["p"]] or [0]) for b in bs]
    ansikte = [max([abs(p["kp"][1][0] - p["kp"][2][0]) for p in b["p"] if p["kp"][1][2] > .5 and p["kp"][2][2] > .5] or [0]) for b in bs]
    if np.median(h) < 0.05: return "detalj"
    if np.median(ansikte) > 0.06: return "närbild"
    if np.median(h) > 0.75: return "halvbild"
    return "total"


def kamerarorelse(bs):
    # ytlig: hur mycket alla boxar flyttar sig samtidigt mellan bildrutor (kameran rör sig, inte personen)
    if len(bs) < 3: return "statisk"
    v = []
    for a, b in zip(bs, bs[1:]):
        if a["p"] and b["p"]:
            ca = np.mean([[(p["box"][0] + p["box"][2]) / 2] for p in a["p"]]); cb = np.mean([[(p["box"][0] + p["box"][2]) / 2] for p in b["p"]])
            v.append(abs(ca - cb))
    return "handhållen" if v and np.median(v) > 0.008 else "statisk"


def figur_spar(bs, pid):
    """original: glesa bildrutor med 9 leder i bildkoordinater (för uppspelning)"""
    ut = []
    for b in bs:
        for p in b["p"]:
            if p["id"] == pid:
                ut.append({"t": b["t"], "kp": [p["kp"][i][:2] if p["kp"][i][2] > .3 else None for i in (0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)],
                           "box": p["box"]})
    return ut


def motivsegment(bs, pid):
    ut = []
    rad = [(b["t"], next(p for p in b["p"] if p["id"] == pid)) for b in bs if any(p["id"] == pid for p in b["p"])]
    for st in range(0, len(rad) - T + 1, T):
        w = rad[st:st + T]
        if w[-1][0] - w[0][0] > T * 0.15: continue  # glapp
        pose, rel, mask = normalisera([q[1]["kp"] for q in w])
        v = vektor(pose, rel); mid, mn = narmaste_motiv(v)
        k = klass(float(np.median([q[1]["box"][3] - q[1]["box"][1] for q in w])))
        ut.append({"start": w[0][0], "slut": round(w[-1][0] + 0.1, 2), "motiv": mid, "motiv_namn": mn, "kontext": k,
                   "narhet": poang(v, k), "narhet_fri": poang(v), "vek": np.round(v, 3).tolist()})
    return ut


def foremal(bs):
    f = {}
    for b in bs:
        for x in b.get("f", []):
            if x["c"] >= 0.3: f[x["k"]] = f.get(x["k"], 0) + 1
    return [{"klass": k, "andel": round(v / max(1, len(bs)), 2)} for k, v in sorted(f.items(), key=lambda z: -z[1]) if v / max(1, len(bs)) >= 0.2]


def auto_handelser(bs, ids):
    h = []
    for pid in ids:
        rad = [(b["t"], next(p for p in b["p"] if p["id"] == pid)) for b in bs if any(p["id"] == pid for p in b["p"])]
        if not rad: continue
        h.append({"t": rad[0][0], "aktor": f"s{pid}", "verb": "syns"})
        # talar till kameran: båda ögonen syns, näsan mitt emellan
        fr = [p for _, p in rad if p["kp"][1][2] > .6 and p["kp"][2][2] > .6 and abs(p["kp"][0][0] - (p["kp"][1][0] + p["kp"][2][0]) / 2) < abs(p["kp"][1][0] - p["kp"][2][0]) * 0.35]
        if len(fr) > 0.6 * len(rad): h.append({"t": rad[0][0], "aktor": f"s{pid}", "verb": "vänd_mot_kamera"})
        cx = [(p["box"][0] + p["box"][2]) / 2 for _, p in rad]
        if len(cx) > 5 and abs(cx[-1] - cx[0]) > 0.25: h.append({"t": rad[-1][0], "aktor": f"s{pid}", "verb": "förflyttar_sig", "riktning": "höger" if cx[-1] > cx[0] else "vänster"})
        hand = [max(p["box"][3] - p["kp"][9][1], p["box"][3] - p["kp"][10][1]) / max(1e-3, p["box"][3] - p["box"][1]) for _, p in rad if p["kp"][9][2] > .4 or p["kp"][10][2] > .4]
        if hand and max(hand) > 0.75: h.append({"t": rad[int(np.argmax(hand))][0], "aktor": f"s{pid}", "verb": "lyfter_hand"})
    return sorted(h, key=lambda x: x["t"])


ut = {"version": "scen-json v0", "metod": metod, "klipp": {"id": namn, "langd_s": spar["bilder"][-1]["t"] + spar["steg"] / spar["fps"], "w": spar["w"], "h": spar["h"]},
      "bakgrund": {}, "aktorer": [], "foremal": [], "scener": []}

if metod in ("2d", "rum"):
    rum = json.load(open(D / "rum.json")) if metod == "rum" else None
    for s in spar["scener"]:
        bs = [b for b in spar["bilder"] if s["start"] <= b["t"] < s["slut"]]
        cnt = {}
        for b in bs:
            for p in b["p"]:
                if p["id"] is not None: cnt[p["id"]] = cnt.get(p["id"], 0) + 1
        ids = [k for k, v in cnt.items() if v >= 5]
        sc = {"i": s["i"], "start": s["start"], "slut": s["slut"], "rum": f"r{s['i']}", "avsikt": None,
              "kamera": {"utsnitt": utsnitt(bs), "rorelse": kamerarorelse(bs)},
              "foremal": foremal(bs), "handelser": auto_handelser(bs, ids),
              "figurer": [{"aktor": f"s{pid}", "spar": figur_spar(bs, pid), "motiv": motivsegment(bs, pid)} for pid in ids]}
        ut["scener"].append(sc)
    ut["aktorer"] = [{"id": f["aktor"], "roll": None} for s in ut["scener"] for f in s["figurer"]]

if metod == "rum":
    # slå ihop spår till aktörer: ett spår som börjar efter att ett annat slutat, nära i bild -> samma aktör
    r = rum["rum"][0]
    spar_lista = []
    for pid, bana in r["banor"].items():
        if len(bana) < 5: continue
        spar_lista.append({"pid": pid, "start": bana[0]["t"], "slut": bana[-1]["t"], "forst": bana[0]["pos"], "sist": bana[-1]["pos"], "bana": bana})
    spar_lista.sort(key=lambda x: x["start"])
    akt = []
    for sp in spar_lista:
        best = None
        for a in akt:
            if a["slut"] <= sp["start"] + 0.3:
                d = np.linalg.norm(np.array(a["sist"])[[0, 2]] - np.array(sp["forst"])[[0, 2]])
                if d < 0.9 and (best is None or d < best[1]): best = (a, d)
        if best:
            a = best[0]; a["pid"].append(sp["pid"]); a["slut"] = sp["slut"]; a["sist"] = sp["sist"]; a["bana"] += sp["bana"]
        else:
            akt.append({"pid": [sp["pid"]], "start": sp["start"], "slut": sp["slut"], "forst": sp["forst"], "sist": sp["sist"], "bana": list(sp["bana"])})
    def jamna(b, n=7):  # glidande median mot djupbrus under fötterna
        x = np.array([q["pos"][0] for q in b]); z = np.array([q["pos"][2] for q in b]); h = n // 2
        for q, i in zip(b, range(len(b))):
            q["pos"] = [float(np.median(x[max(0, i - h):i + h + 1])), q["pos"][1], float(np.median(z[max(0, i - h):i + h + 1]))]
        return b
    for a in akt: a["bana"] = jamna(sorted(a["bana"], key=lambda q: q["t"]))
    ut["aktorer"] = [{"id": f"a{i}", "spar": a["pid"], "in": a["start"], "ut": a["slut"],
                      "bana": [{"t": q["t"], "x": q["pos"][0], "z": q["pos"][2]} for q in a["bana"][::2]]} for i, a in enumerate(akt)]
    ut["bakgrund"] = {"platta": r["platta"], "djup": r["djup"], "golv": r["golv"], "fov": rum["fov"],
                      "ankare": r["ankare"], "poser3d_antal": len(r["poser3d"])}
    # händelser ur närhet i rummet
    hand = []
    L = ut["klipp"]["langd_s"]
    for a in ut["aktorer"]:
        if a["in"] > 0.5: hand.append({"t": a["in"], "aktor": a["id"], "verb": "kommer_in"})
        if a["ut"] < L - 0.6: hand.append({"t": a["ut"], "aktor": a["id"], "verb": "går_ut"})
        for an in r["ankare"]:
            if an["namn"] != "table": continue
            nara = [q for q in a["bana"] if np.hypot(q["x"] - an["pos"][0], q["z"] - an["pos"][2]) < 0.7]
            if len(nara) >= 3: hand.append({"t": nara[0]["t"], "aktor": a["id"], "verb": "vid", "mal": f"bord@{an['u']},{an['v']}"})
    for i, a in enumerate(ut["aktorer"]):
        for b in ut["aktorer"][i + 1:]:
            ta = {round(q["t"], 1): q for q in a["bana"]}
            for q in b["bana"]:
                p = ta.get(round(q["t"], 1))
                if p and np.hypot(p["x"] - q["x"], p["z"] - q["z"]) < 0.6:
                    hand.append({"t": q["t"], "aktor": a["id"], "verb": "möter", "mal": b["id"]}); break
    ut["scener"][0]["handelser"] = sorted(hand, key=lambda x: x["t"])

if metod == "semantisk":
    sem = json.load(open(D / "semantik.json"))
    ut["aktorer"] = sem["aktorer"]; ut["foremal"] = sem["foremal"]; ut["bakgrund"] = {"rum": sem["rum"]}
    ut["premiss"] = sem["premiss"]; ut["ryggrad"] = sem["ryggrad"]
    synliga = [a["id"] for a in sem["aktorer"] if a["id"].startswith("p")]
    for i, s in enumerate(sem["scener"]):
        bs = [b for b in spar["bilder"] if s["start"] <= b["t"] < s["slut"]]
        cnt = {}
        for b in bs:
            for p in b["p"]:
                if p["id"] is not None: cnt[p["id"]] = cnt.get(p["id"], 0) + (p["box"][3] - p["box"][1])
        # huvudpersonen i scenen = störst summerad yta; mappas till den aktör som har flest händelser
        aktiv = [h["aktor"] for h in s["handelser"] if h["aktor"] in synliga]
        figurer = []
        if cnt and aktiv:
            pid = max(cnt, key=cnt.get)
            figurer.append({"aktor": max(set(aktiv), key=aktiv.count), "spar": figur_spar(bs, pid), "motiv": motivsegment(bs, pid)})
        ut["scener"].append({"i": i, **s, "figurer": figurer})

json.dump(ut, open(D / f"scen-{metod}.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
seg = [m for s in ut["scener"] for f in s["figurer"] for m in f["motiv"]]
print(namn, metod, "scener", len(ut["scener"]), "aktörer", len(ut["aktorer"]), "motivsegment", len(seg),
      "närhet median", np.median([m["narhet"] for m in seg]) if seg else None,
      "andel>=80", round(np.mean([m["narhet"] >= 80 for m in seg]), 2) if seg else None)
