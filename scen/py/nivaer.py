"""Nivåmodellen v0: Klipp > Scen > Handlingsenhet, där mening (Gemini) och rörelse (YOLO, kamerakompenserad) binds i samma objekt.

Källor: kamera.json (segment = scener, kamerabana, personer i scenkoordinater), spar.json (YOLO-skelett och föremål),
ss-gemini-3.8-flash-fps5.json (roller, föremål, handlingar, takt, avsikt).

  Scen            = kamerasegment. kamera.typ ur banan (statisk/panorering/zoom/handhållen), kamera.osaker om bakgrunden är för liten.
  Identitet       = YOLO-spår inom scenen knyts till Geminis P-id (avstånd till interpolerad Gemini-bana + kroppsläge).
  Handlingsenhet  = en Gemini-handling (vem, verb, obj, mot, tid) + rörelsen hos 'vem' under samma tid i scenkoordinater:
                    förflyttning, riktning, fart, kroppsläge, händernas läge. Tider utan handling blir enheten 'närvaro'.
  Kärnföremål     = föremål som händerna rör (handled nära föremålsruta) och/eller som handlingarna nämner; resten är bakgrund.
Skriver data/<klipp>/klipp.json och skriver ut en läsbar sammanfattning.
Användning: .venv/Scripts/python.exe py/nivaer.py c-sketch-tre
"""
import json, sys
from pathlib import Path
import numpy as np

ROT = Path(__file__).resolve().parent.parent
namn = sys.argv[1]
D = ROT / "data" / namn
kam = json.load(open(D / "kamera.json", encoding="utf-8"))
spar = json.load(open(D / "spar.json", encoding="utf-8"))
gfil = sorted(D.glob("ss-gemini-3.8-flash-fps5*.json"))
ss = json.load(open(gfil[0], encoding="utf-8"))["ss"] if gfil else None
TICK = (ss["huvud"].get("tick") or 0.1) if ss else 0.1
W, H = kam["w"], kam["h"]
yolo_t = np.array([b["t"] for b in spar["bilder"]])

# ---------- Gemini-hjälp
def gbana(e):
    return sorted([w for b in ss["banor"] if b["av"] == e for w in b["wp"]], key=lambda w: w["t"]) if ss else []
GB = {r["id"]: gbana(r["id"]) for r in (ss["roller"] if ss else [])}
def gvid(e, t):
    wp = GB.get(e) or []
    if not wp or t < wp[0]["t"] * TICK - 0.3 or t > wp[-1]["t"] * TICK + 0.3: return None
    a = max([w for w in wp if w["t"] * TICK <= t], key=lambda w: w["t"], default=wp[0])
    c = min([w for w in wp if w["t"] * TICK >= t], key=lambda w: w["t"], default=wp[-1])
    q = 0 if c["t"] == a["t"] else (t - a["t"] * TICK) / ((c["t"] - a["t"]) * TICK)
    return {"p": [a["p"][i] + q * (c["p"][i] - a["p"][i]) for i in range(2)], "k": a.get("k"), "h": a.get("h")}

def yolo_vid(t):
    return spar["bilder"][int(np.abs(yolo_t - t).argmin())]

def sitter(p):
    k = p["kp"]
    if min(k[11][2], k[12][2]) < .3 or max(k[13][2], k[14][2]) < .3: return None
    torso = abs((k[11][1] + k[12][1]) / 2 - (k[5][1] + k[6][1]) / 2) + 1e-3
    return (np.mean([k[i][1] for i in (13, 14) if k[i][2] > .3]) - (k[11][1] + k[12][1]) / 2) < 0.45 * torso

def kameratyp(bana):
    m = np.array([b["mitt"] for b in bana]); z = np.array([b["zoom"] for b in bana])
    if len(m) < 4: return "okänd"
    spann = float(np.linalg.norm(np.percentile(m, 95, 0) - np.percentile(m, 5, 0)))
    jit = float(np.median(np.linalg.norm(np.diff(m, 2, axis=0), axis=1))) if len(m) > 3 else 0
    zr = float(z.max() / max(1e-3, z.min()))
    if zr > 1.15: return "zoom/åkning"
    if spann < 0.03: return "statisk"
    if jit > 0.004: return "handhållen"
    return "panorering"

def kp_(p):
    k = p["kp"]; pts = [k[i] for i in (11, 12) if k[i][2] > .3] or [[k[i][0], k[i][1] + 0.12, 1] for i in (5, 6) if k[i][2] > .3] or [[0, 0, 0]]
    return [np.mean([q[0] for q in pts]), np.mean([q[1] for q in pts])]

# ---------- per scen
scener = []
foremal_hand = {}  # (scen, klass) -> antal gånger en hand är nära
for s in kam["segment"]:
    if s.get("kort"): continue
    a, b = s["in"], s["ut"]
    # bakgrundsandel: hur mycket av bilden som inte är person (avgör om kamerabanan går att lita på)
    bg = []
    for bb in spar["bilder"]:
        if a <= bb["t"] < b:
            yta = sum((p["box"][2] - p["box"][0]) * (p["box"][3] - p["box"][1]) for p in bb["p"])
            bg.append(1 - min(1, yta))
    bgandel = float(np.median(bg)) if bg else 1.0
    kamera = {"typ": kameratyp(s["bana"]), "spann": s["kamera_spann"], "zoom": s["zoom_spann"],
              "bakgrund_andel": round(bgandel, 2), "osaker": bgandel < 0.35,
              "bana": [{"t": q["t"], "x": q["mitt"][0], "y": q["mitt"][1], "z": q["zoom"]} for q in s["bana"][::2]]}
    # identitet: spår -> P
    tilld = {}
    if ss:
        kost = {}
        for pid, lst in s["personer"].items():
            if len(lst) < 4: continue
            for e in GB:
                dd, miss = [], []
                for x in lst:
                    g = gvid(e, x["t"])
                    if not g: continue
                    dd.append(np.hypot(x["bild"][1] * 1000 - g["p"][0], x["bild"][0] * 1000 - g["p"][1]))
                    yp = next((p for p in yolo_vid(x["t"])["p"] if p["id"] == int(pid)), None)
                    st = sitter(yp) if yp else None
                    if st is not None and g.get("k"): miss.append(st != (g["k"] == "sitter"))
                if len(dd) >= max(3, 0.5 * len(lst)): kost[(pid, e)] = float(np.median(dd)) + (150 * float(np.mean(miss)) if miss else 0)
        for pid in sorted(s["personer"], key=lambda p: -len(s["personer"][p])):
            lst = s["personer"][pid]; t0, t1 = lst[0]["t"], lst[-1]["t"]
            for e in sorted(GB, key=lambda e: kost.get((pid, e), 1e9)):
                if kost.get((pid, e), 1e9) > 300: break
                if not any(ee == e and not (s["personer"][q][-1]["t"] < t0 or s["personer"][q][0]["t"] > t1) for q, ee in tilld.items()):
                    tilld[pid] = e; break
        # reserv: om bara en synlig person är aktiv hos Gemini under avsnittet får det längsta otilldelade spåret den personen
        aktiva = {h["vem"] for h in ss["handlingar"] if h["vem"] != "K" and h["t"] * TICK < b and (h["t"] + max(h.get("dur", 10), 10)) * TICK > a} | \
                 {bn["av"] for bn in ss["banor"] if bn["av"].startswith("P") and any(a - 0.3 <= w["t"] * TICK <= b + 0.3 for w in bn["wp"])}
        lediga = [e for e in aktiva if e not in tilld.values()]
        otill = sorted([p for p in s["personer"] if p not in tilld and len(s["personer"][p]) >= 6], key=lambda p: -len(s["personer"][p]))
        if len(aktiva) == 1 and lediga and otill:
            tilld[otill[0]] = lediga[0]; reserv = True
        else:
            reserv = False
    banor = {}
    for pid, e in tilld.items():
        banor.setdefault(e, []).extend(s["personer"][pid])
    for e in banor: banor[e].sort(key=lambda x: x["t"])
    # kärnföremål: händer nära föremål (YOLO-World) inom scenen
    for bb in spar["bilder"]:
        if not (a <= bb["t"] < b): continue
        for f in bb.get("f", []):
            if f["c"] < 0.25: continue
            x0, y0, x1, y1 = f["box"]
            for p in bb["p"]:
                for w in (9, 10):
                    k = p["kp"][w]
                    if k[2] > .4 and x0 - 0.04 <= k[0] <= x1 + 0.04 and y0 - 0.04 <= k[1] <= y1 + 0.04:
                        foremal_hand[(len(scener), f["k"])] = foremal_hand.get((len(scener), f["k"]), 0) + 1
    # handlingsenheter
    enheter = []
    if ss:
        for h in ss["handlingar"]:
            t0 = h["t"] * TICK; t1 = t0 + max(h.get("dur", 10), 10) * TICK
            if not (a <= t0 < b): continue
            enheter.append({"vem": h["vem"], "verb": h["verb"], "obj": h.get("obj"), "mot": h.get("mot"), "in": round(t0, 2), "ut": round(min(t1, b), 2), "kalla": "gemini"})
    # närvaro-enheter där en person syns utan handling
    for e, lst in banor.items():
        tider = [x["t"] for x in lst]
        upptaget = [(u["in"], u["ut"]) for u in enheter if u["vem"] == e]
        start = None
        for t in tider + [None]:
            fri = t is not None and not any(i0 - 0.05 <= t <= i1 + 0.05 for i0, i1 in upptaget)
            if fri and start is None: start = t
            if (not fri or t is None) and start is not None:
                slut = prev
                if slut - start >= 0.8: enheter.append({"vem": e, "verb": "närvaro", "in": round(start, 2), "ut": round(slut, 2), "kalla": "yolo"})
                start = None
            prev = t if t is not None else prev
    # rörelse per enhet, i scenkoordinater
    for u in enheter:
        lst = [x for x in banor.get(u["vem"], []) if u["in"] - 0.05 <= x["t"] <= u["ut"] + 0.05]
        if len(lst) < 3:
            u["rorelse"] = None; continue
        sc = np.array([x["scen"] for x in lst]); bi = np.array([x["bild"] for x in lst])
        # utjämna (median 5) mot skelettbrus
        sm = np.array([np.median(sc[max(0, i - 2):i + 3], axis=0) for i in range(len(sc))])
        d = sm[-1] - sm[0]; dur = lst[-1]["t"] - lst[0]["t"] + 1e-3
        kl = [sitter(next((p for p in yolo_vid(x["t"])["p"] if np.hypot(*(np.array(kp_(p)) - np.array(x["bild"]))) < 0.05), None) or {"kp": [[0, 0, 0]] * 17}) for x in lst[::3]]
        u["rorelse"] = {"forflyttning": round(float(np.linalg.norm(d)), 3), "riktning": ("höger" if d[0] > 0 else "vänster") if abs(d[0]) > abs(d[1]) else ("mot kameran" if d[1] > 0 else "bort"),
                        "fart": round(float(np.linalg.norm(d) / dur), 3), "sitter_andel": round(float(np.mean([k for k in kl if k is not None])), 2) if any(k is not None for k in kl) else None,
                        "skenbar_i_bild": round(float(np.linalg.norm(bi[-1] - bi[0])), 3),
                        "bana": [[x["t"], round(v[0], 3), round(v[1], 3)] for x, v in zip(lst[::2], sm[::2])]}
    # Geminis tagning med störst överlapp ger takt och avsikt
    tg = None
    if ss:
        tg = max(ss["tagningar"], key=lambda x: max(0, min(b, x["ut"] * TICK) - max(a, x["in"] * TICK)))
    scener.append({"id": f"S{len(scener) + 1}", "in": a, "ut": b, "kamera": kamera, "narvarande": sorted(banor),
                   "identitet": {str(k): v for k, v in tilld.items()}, "takt": tg and tg["takt"], "avsikt": tg and tg["avsikt"],
                   "utsnitt": tg and tg["utsnitt"], "enheter": sorted(enheter, key=lambda u: u["in"])})

# kärnföremål per scen: Gemini-föremål som handlingarna nämner + YOLO-klasser som händerna rör minst 3 gånger
gfor = {o["id"]: o for o in (ss["foremal"] if ss else [])}
for i, sc in enumerate(scener):
    namnda = sorted({u.get("obj") for u in sc["enheter"] if u.get("obj")} | {u.get("mot") for u in sc["enheter"] if u.get("mot") and str(u.get("mot")).startswith("O")})
    INREDNING = {"table", "chair", "counter"}
    rorda = sorted([(k, n) for (j, k), n in foremal_hand.items() if j == i and n >= 3 and k not in INREDNING], key=lambda x: -x[1])
    sc["inredning"] = sorted({k for (j, k), n in foremal_hand.items() if j == i and k in INREDNING})
    sc["karnforemal"] = [{"id": o, "typ": gfor.get(o, {}).get("typ"), "kalla": "handling"} for o in namnda if o in gfor] + \
                        [{"klass": k, "handkontakt": n, "kalla": "händer"} for k, n in rorda[:4]]

# --- scener = Geminis tagningar (meningsenheter); kamerans segment blir underavsnitt
avsnitt = scener
if ss:
    scener = []
    for tg in ss["tagningar"]:
        t0, t1 = tg["in"] * TICK, tg["ut"] * TICK
        mina = [av for av in avsnitt if (min(t1, av["ut"]) - max(t0, av["in"])) > 0.5 * (av["ut"] - av["in"])]
        enh = sorted([u for av in mina for u in av["enheter"]], key=lambda u: u["in"])
        scener.append({"id": tg["id"], "in": t0, "ut": t1, "takt": tg["takt"], "avsikt": tg["avsikt"], "utsnitt": tg["utsnitt"],
                       "kamera_gemini": tg["kamera"], "narvarande": sorted({p for av in mina for p in av["narvarande"]}),
                       "karnforemal": [f for av in mina for f in av["karnforemal"]],
                       "kameraavsnitt": [{"in": av["in"], "ut": av["ut"], **{k: av["kamera"][k] for k in ("typ", "spann", "zoom", "osaker")}} for av in mina],
                       "enheter": enh})
        # dubbletter av kärnföremål bort
        sett = set(); sc_ = scener[-1]; sc_["karnforemal"] = [f for f in sc_["karnforemal"] if not ((f.get("id") or f.get("klass")) in sett or sett.add(f.get("id") or f.get("klass")))]

ut = {"version": "nivåmodell v0", "klipp": namn, "langd": kam["segment"][-1]["ut"], "roller": ss["roller"] if ss else [],
      "foremal": ss["foremal"] if ss else [], "scener": scener, "kameraavsnitt_alla": len(avsnitt)}
json.dump(ut, open(D / "klipp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"## {namn}: {len(scener)} scener ({len(avsnitt)} kameraavsnitt), roller {[r['id'] + '=' + r['roll'] for r in ut['roller']]}")
for sc in scener:
    kv = " | ".join(f"{k['in']:.1f}-{k['ut']:.1f} {k['typ']}{'?' if k['osaker'] else ''}" for k in sc.get("kameraavsnitt", []))
    print(f"{sc['id']} {sc['in']:.1f}-{sc['ut']:.1f}s  {sc['takt']}  närvarande {sc['narvarande']}  kärna {[f.get('id') or f.get('klass') for f in sc['karnforemal']]}\n    kamera: {kv}\n    avsikt: {sc['avsikt']}")
    for u in sc["enheter"]:
        r = u.get("rorelse")
        rs = f"förfl {r['forflyttning']:.2f} {r['riktning']} (i bild {r['skenbar_i_bild']:.2f}) sitter {r['sitter_andel']}" if r else "ingen rörelsedata"
        print(f"    {u['in']:5.1f}-{u['ut']:5.1f} {u['vem']:>3} {u['verb']:<14} {u.get('obj') or '':<3} {u.get('mot') or '':<3} | {rs}")
