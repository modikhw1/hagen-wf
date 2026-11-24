"""Baka in Scenskrift (Gemini) i YOLO-spåren: Gemini äger identitet och mening, YOLO äger exakt position och skelett.

1. Varje YOLO-spår (ofta avbrutet, 9 st i klipp C) tilldelas den P-id vars interpolerade Gemini-bana ligger närmast
   i snitt under spårets livstid. Spår som överlappar i tid får inte dela P-id (det närmaste vinner).
2. Föremål (O-id) knyts till YOLO-World-fynd ('plate', 'food' …) nära Geminis O-punkt, och följer bärarens hand
   när Gemini säger att någon håller/tar det.
3. Utdata: data/<klipp>/enhet.json (en tät bana per P med skelett, kroppsläge, händer, handlingar) och
   enhet.mp4 (sida vid sida: original med enhetliga figurer | bara figurerna på bakgrundsplattan).
Användning: .venv/Scripts/python.exe sprak/fusera.py data/c-sketch-tre/ss-gemini-3.8-flash-fps5.json klipp/c-sketch-tre.mp4
"""
import json, sys
from pathlib import Path
import numpy as np, cv2

fil, video = Path(sys.argv[1]), sys.argv[2]
ss = json.load(open(fil, encoding="utf-8"))["ss"]
D = fil.parent
spar = json.load(open(D / "spar.json", encoding="utf-8"))
tick = ss["huvud"].get("tick", 0.1) or 0.1
TROSKEL = 300  # max snittavstånd (0-1000) för att ett spår ska få ett P-id

def bana(eid):
    wp = sorted([w for b in ss["banor"] if b["av"] == eid for w in b["wp"]], key=lambda w: w["t"])
    return wp

def vid(wp, t):
    if not wp or t < wp[0]["t"] * tick - 0.3 or t > wp[-1]["t"] * tick + 0.3: return None
    a = max([w for w in wp if w["t"] * tick <= t], key=lambda w: w["t"], default=wp[0])
    c = min([w for w in wp if w["t"] * tick >= t], key=lambda w: w["t"], default=wp[-1])
    q = 0 if c["t"] == a["t"] else (t - a["t"] * tick) / ((c["t"] - a["t"]) * tick)
    return {"p": [a["p"][i] + q * (c["p"][i] - a["p"][i]) for i in range(2)], "k": a.get("k"), "h": a.get("h"), "v": a.get("v")}

P = [r["id"] for r in ss["roller"]]
O = [o["id"] for o in ss["foremal"]]
BANOR = {e: bana(e) for e in P + O}

def kropp(p):
    """YOLO: kroppspunkt i 0-1000 [y, x]; höftmitt om synlig annars axelmitt nedflyttad"""
    k = p["kp"]
    if k[11][2] > .3 or k[12][2] > .3:
        pts = [k[i] for i in (11, 12) if k[i][2] > .3]
    else:
        pts = [[k[i][0], k[i][1] + 0.12] for i in (5, 6) if k[i][2] > .3] or [[(p["box"][0] + p["box"][2]) / 2, (p["box"][1] + p["box"][3]) / 2]]
    return [np.mean([q[1] for q in pts]) * 1000, np.mean([q[0] for q in pts]) * 1000]

# --- 1. spår -> P-id
spar_pts = {}
for b in spar["bilder"]:
    for p in b["p"]:
        if p["id"] is None: continue
        spar_pts.setdefault(p["id"], []).append((b["t"], kropp(p), p))
def sitter(p):
    """YOLO: knän nästan i höjd med höfter -> sitter (None om benen inte syns)"""
    k = p["kp"]
    if min(k[11][2], k[12][2]) < .3 or max(k[13][2], k[14][2]) < .3: return None
    torso = abs((k[11][1] + k[12][1]) / 2 - (k[5][1] + k[6][1]) / 2) + 1e-3
    kna = np.mean([k[i][1] for i in (13, 14) if k[i][2] > .3])
    return (kna - (k[11][1] + k[12][1]) / 2) < 0.45 * torso

kost = {}
for sid, pts in spar_pts.items():
    if len(pts) < 4: continue
    for e in P:
        dd, miss = [], []
        for t, kp_, p in pts:
            g = vid(BANOR[e], t)
            if not g: continue
            dd.append(np.hypot(*(np.array(kp_) - g["p"])))
            s = sitter(p)
            if s is not None and g.get("k"): miss.append(s != (g["k"] == "sitter"))
        if len(dd) >= max(3, 0.5 * len(pts)):
            kost[(sid, e)] = float(np.median(dd)) + (150 * float(np.mean(miss)) if miss else 0)
tilldelning = {}
for sid in sorted(spar_pts, key=lambda s: -len(spar_pts[s])):          # långa spår väljer först
    t0, t1 = spar_pts[sid][0][0], spar_pts[sid][-1][0]
    for e in sorted(P, key=lambda e: kost.get((sid, e), 1e9)):
        c = kost.get((sid, e), 1e9)
        if c > TROSKEL: break
        krock = [s for s, ee in tilldelning.items() if ee == e and not (spar_pts[s][-1][0] < t0 or spar_pts[s][0][0] > t1)]
        if not krock:
            tilldelning[sid] = e; break
print("spår → P:", {int(k): v for k, v in sorted(tilldelning.items())})
print("utan P:", sorted(int(s) for s in spar_pts if s not in tilldelning), "| kostnad:", {f"{int(s)}>{e}": round(c) for (s, e), c in sorted(kost.items()) if c < 400})

# --- 2. per bildruta: enhetliga figurer + föremål
handl = sorted(ss["handlingar"], key=lambda h: h["t"])
enhet = {"klipp": ss.get("huvud"), "roller": ss["roller"], "foremal": ss["foremal"], "tilldelning": {str(int(k)): v for k, v in tilldelning.items()}, "bilder": []}
for b in spar["bilder"]:
    t = b["t"]; rad = {"t": t, "P": {}, "O": {}}
    for p in b["p"]:
        e = tilldelning.get(p["id"])
        if not e: continue
        g = vid(BANOR[e], t) or {}
        rad["P"][e] = {"kp": p["kp"], "box": p["box"], "k": g.get("k"), "h": g.get("h"), "v": g.get("v"), "spar": p["id"]}
    for e in O:
        g = vid(BANOR[e], t)
        if not g: continue
        fynd = [f for f in b.get("f", []) if f["k"] in ("plate", "food", "pizza", "sandwich", "tray", "bowl") and f["c"] > 0.2]
        nara = min(fynd, key=lambda f: np.hypot((f["box"][1] + f["box"][3]) / 2 * 1000 - g["p"][0], (f["box"][0] + f["box"][2]) / 2 * 1000 - g["p"][1]), default=None)
        if nara and np.hypot((nara["box"][1] + nara["box"][3]) / 2 * 1000 - g["p"][0], (nara["box"][0] + nara["box"][2]) / 2 * 1000 - g["p"][1]) < 250:
            rad["O"][e] = {"box": nara["box"], "kalla": "yolo"}
        else:
            rad["O"][e] = {"p": g["p"], "kalla": "gemini"}
    rad["handling"] = [h for h in handl if h["t"] * tick <= t < (h["t"] + max(h.get("dur", 10), 10)) * tick]
    enhet["bilder"].append(rad)
json.dump(enhet, open(D / "enhet.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# --- 3. rendering
FARG = {e: c for e, c in zip(P, [(230, 168, 106), (90, 122, 224), (127, 191, 95), (224, 139, 195), (74, 176, 224)])}
BEN = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]
platta = cv2.imread(str(D / "rum" / "platta-0.jpg"))
cap = cv2.VideoCapture(video); fps = cap.get(cv2.CAP_PROP_FPS); W = int(cap.get(3)); H = int(cap.get(4))
ut = cv2.VideoWriter(str(D / "enhet.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W * 2, H))
platta = cv2.resize(platta, (W, H)) if platta is not None else np.zeros((H, W, 3), np.uint8)
idx = 0; ark = []
def rita(img, rad, tunn):
    for e, f in rad["P"].items():
        kp = f["kp"]; c = FARG.get(e, (200, 200, 200))
        for a, bb in BEN:
            if kp[a][2] > .3 and kp[bb][2] > .3:
                cv2.line(img, (int(kp[a][0] * W), int(kp[a][1] * H)), (int(kp[bb][0] * W), int(kp[bb][1] * H)), c, 6 if tunn else 10, cv2.LINE_AA)
        if kp[0][2] > .3: cv2.circle(img, (int(kp[0][0] * W), int(kp[0][1] * H)), 14 if tunn else 26, c, -1)
        x, y = int(f["box"][0] * W), int(f["box"][1] * H) + 30
        lbl = f"{e} {f['k'] or ''}/{f['h'] or ''}"
        cv2.putText(img, lbl, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 6); cv2.putText(img, lbl, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, c, 2)
    for e, o in rad["O"].items():
        if "box" in o:
            x0, y0, x1, y1 = [int(v) for v in (o["box"][0] * W, o["box"][1] * H, o["box"][2] * W, o["box"][3] * H)]
            cv2.rectangle(img, (x0, y0), (x1, y1), (0, 220, 255), 3)
        else:
            x0, y0 = int(o["p"][1] / 1000 * W), int(o["p"][0] / 1000 * H); cv2.circle(img, (x0, y0), 14, (0, 220, 255), 3)
        cv2.putText(img, e, (x0, y0 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 255), 2)
    for k, h in enumerate(rad["handling"][:3]):
        s = f"{h['vem']} {h['verb']} {h.get('obj') or ''}"
        cv2.putText(img, s, (12, H - 30 - 36 * k), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 6); cv2.putText(img, s, (12, H - 30 - 36 * k), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
while True:
    ok, fr = cap.read()
    if not ok: break
    t = idx / fps
    rad = min(enhet["bilder"], key=lambda r: abs(r["t"] - t))
    a = fr.copy(); rita(a, rad, True)
    bgr = (platta * 0.45).astype(np.uint8); rita(bgr, rad, False)
    rum = np.hstack([a, bgr]); cv2.putText(rum, f"{t:4.1f}s", (12, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    ut.write(rum)
    if idx % int(fps) == 0: ark.append(cv2.resize(rum, (432, 384)))
    idx += 1
ut.release()
while len(ark) % 4: ark.append(np.zeros_like(ark[0]))
cv2.imwrite(str(D / "enhet.jpg"), np.vstack([np.hstack(ark[i:i + 4]) for i in range(0, len(ark), 4)]), [cv2.IMWRITE_JPEG_QUALITY, 80])
tackt = sum(1 for r in enhet["bilder"] for _ in r["P"]); alla = sum(len(b["p"]) for b in spar["bilder"])
print(f"YOLO-detektioner med P-id: {tackt}/{alla} ({tackt / max(1, alla):.0%}); föremål från yolo/gemini:",
      sum(1 for r in enhet["bilder"] for o in r["O"].values() if o["kalla"] == "yolo"), "/", sum(1 for r in enhet["bilder"] for o in r["O"].values() if o["kalla"] == "gemini"))
