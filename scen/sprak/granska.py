"""Granskar en Scenskrift-fil mot klippet och YOLO-spåren.

1. Kontaktark: en bildruta per sekund med Geminis interpolerade punkter (id, kroppsläge, händer) inritade.
2. Mätning: för varje waypoint, avstånd (0-1000) till närmaste YOLO-höftmitt vid samma tid,
   och om varje P-id hålls till samma YOLO-spår (identitet).
Användning: .venv/Scripts/python.exe sprak/granska.py data/c-sketch-tre/ss-gemini-3.8-flash-fps10.0.json klipp/c-sketch-tre.mp4
"""
import json, sys
from pathlib import Path
import numpy as np, cv2

fil, video = Path(sys.argv[1]), sys.argv[2]
d = json.load(open(fil, encoding="utf-8")); ss = d["ss"]
spar = json.load(open(fil.parent / "spar.json", encoding="utf-8"))
tick = ss["huvud"].get("tick", 0.1) or 0.1
FARG = [(230, 168, 106), (90, 122, 224), (127, 191, 95), (224, 139, 195), (74, 176, 224), (200, 200, 200)]
ids = sorted({b["av"] for b in ss["banor"]})
farg = {i: FARG[k % len(FARG)] for k, i in enumerate(ids)}


def lage(t):
    """interpolerad position per entitet vid tid t (sekunder)"""
    ut = {}
    for b in ss["banor"]:
        tg = next((x for x in ss["tagningar"] if x["id"] == b["tagning"]), None)
        if tg and not (tg["in"] * tick <= t < tg["ut"] * tick + 1e-6): continue
        wp = sorted(b["wp"], key=lambda w: w["t"])
        if not wp or t < wp[0]["t"] * tick - 0.05 or t > wp[-1]["t"] * tick + 0.05: continue
        a = max([w for w in wp if w["t"] * tick <= t + 1e-6], key=lambda w: w["t"], default=wp[0])
        c = min([w for w in wp if w["t"] * tick >= t - 1e-6], key=lambda w: w["t"], default=wp[-1])
        q = 0 if c["t"] == a["t"] else (t - a["t"] * tick) / ((c["t"] - a["t"]) * tick)
        p = [a["p"][i] + q * (c["p"][i] - a["p"][i]) for i in range(2)]
        ut[b["av"]] = {"p": p, "k": a.get("k", ""), "h": a.get("h", ""), "v": a.get("v", "")}
    return ut


cap = cv2.VideoCapture(video); fps = cap.get(cv2.CAP_PROP_FPS); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
bilder = []
for sek in np.arange(0, n / fps, 1.0):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(sek * fps)); ok, f = cap.read()
    if not ok: break
    H, W = f.shape[:2]
    tg = next((x for x in ss["tagningar"] if x["in"] * tick <= sek < x["ut"] * tick), None)
    for eid, l in lage(sek).items():
        y, x = int(l["p"][0] / 1000 * H), int(l["p"][1] / 1000 * W)
        cv2.circle(f, (x, y), 16, farg[eid], -1); cv2.circle(f, (x, y), 16, (0, 0, 0), 2)
        cv2.putText(f, f"{eid} {l['k']}/{l['h']}", (x - 40, y - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 5)
        cv2.putText(f, f"{eid} {l['k']}/{l['h']}", (x - 40, y - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    # YOLO höftmitt som små kryss
    b = min(spar["bilder"], key=lambda b: abs(b["t"] - sek))
    for p in b["p"]:
        kp = p["kp"]; hx = (kp[11][0] + kp[12][0]) / 2 * W; hy = (kp[11][1] + kp[12][1]) / 2 * H
        if kp[11][2] > .3: cv2.drawMarker(f, (int(hx), int(hy)), (0, 255, 255), cv2.MARKER_CROSS, 22, 3)
    cv2.rectangle(f, (0, 0), (W, 46), (0, 0, 0), -1)
    cv2.putText(f, f"{sek:.0f}s {tg['id'] + ' ' + tg['utsnitt'] + ' ' + tg['takt'] if tg else '-'}", (8, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    bilder.append(cv2.resize(f, (216, 384)))
while len(bilder) % 8: bilder.append(np.zeros_like(bilder[0]))
ark = np.vstack([np.hstack(bilder[i:i + 8]) for i in range(0, len(bilder), 8)])
ut_ark = fil.with_suffix(".jpg"); cv2.imwrite(str(ut_ark), ark, [cv2.IMWRITE_JPEG_QUALITY, 82])

# mätning mot YOLO
avst, koppling = [], {}
for bn in ss["banor"]:
    if not bn["av"].startswith("P"): continue
    for w in bn["wp"]:
        t = w["t"] * tick
        b = min(spar["bilder"], key=lambda b: abs(b["t"] - t))
        if abs(b["t"] - t) > 0.15: continue
        best = None
        for p in b["p"]:
            kp = p["kp"]
            if kp[11][2] < .3 and kp[12][2] < .3: continue
            hy = (kp[11][1] + kp[12][1]) / 2 * 1000; hx = (kp[11][0] + kp[12][0]) / 2 * 1000
            dd = float(np.hypot(hy - w["p"][0], hx - w["p"][1]))
            if best is None or dd < best[0]: best = (dd, p["id"])
        if best:
            avst.append(best[0]); koppling.setdefault(bn["av"], []).append(best[1])
ident = {k: {"spår": sorted(set(v), key=lambda x: (x is None, x)), "andel_största": round(max(v.count(x) for x in set(v)) / len(v), 2)} for k, v in koppling.items()}
res = {"waypoints_matchade": len(avst), "avstånd_median": round(float(np.median(avst)), 1) if avst else None,
       "andel_inom_80": round(float(np.mean([a < 80 for a in avst])), 2) if avst else None, "identitet": ident, "ark": str(ut_ark)}
print(json.dumps(res, ensure_ascii=False, indent=1))
