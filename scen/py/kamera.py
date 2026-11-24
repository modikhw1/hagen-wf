"""Kameralagret v2: kamerans rörelse skild från personernas, och klipp där kameran inte kan följas.

Hela klippet, bildruta för bildruta:
  1. Bakgrundspunkter (Shi-Tomasi) utanför personrutor (YOLO, utvidgade) följs med optiskt flöde (Lucas-Kanade).
  2. Likformighetstransform (förskjutning, rotation, skala) skattas robust (RANSAC) och kedjas inom ett kamerasegment.
  3. Klipp: när registreringen brister (för få inliers, orimligt skalsprång eller förskjutning, stort bildbyte)
     börjar ett nytt segment. Segmenten är alltså tagningar sedda från kamerans håll.
  4. Scenkoordinater: varje segment uttrycks i sin vidaste vy (minst zoom), så enheterna är jämförbara.
Mått per spår: spann (95:e - 5:e percentil) i bild- mot scenkoordinater; stillasittande ska krympa när kameran rör sig.
Skriver data/<klipp>/kamera.json och data/<klipp>/kamera-mosaik-<segment>.jpg.

Användning: .venv/Scripts/python.exe py/kamera.py c-sketch-tre
"""
import json, sys
from pathlib import Path
import numpy as np, cv2

ROT = Path(__file__).resolve().parent.parent
namn = sys.argv[1]
D = ROT / "data" / namn
spar = json.load(open(D / "spar.json", encoding="utf-8"))
SKALA = 0.5

cap = cv2.VideoCapture(str(ROT / "klipp" / f"{namn}.mp4")); fps = cap.get(cv2.CAP_PROP_FPS)
W, H = int(cap.get(3)), int(cap.get(4))
rutor = []
while True:
    ok, f = cap.read()
    if not ok: break
    rutor.append(f)
N = len(rutor)
gra = [cv2.cvtColor(cv2.resize(f, None, fx=SKALA, fy=SKALA), cv2.COLOR_BGR2GRAY) for f in rutor]
yolo_t = np.array([b["t"] for b in spar["bilder"]])

def mask(i):
    m = np.full(gra[0].shape, 255, np.uint8)
    b = spar["bilder"][int(np.abs(yolo_t - i / fps).argmin())]
    for p in b["p"]:
        x0, y0, x1, y1 = p["box"]; dx, dy = (x1 - x0) * 0.15, (y1 - y0) * 0.08
        cv2.rectangle(m, (int((x0 - dx) * W * SKALA), int((y0 - dy) * H * SKALA)), (int((x1 + dx) * W * SKALA), int((y1 + dy) * H * SKALA)), 0, -1)
    return m

# --- 1-3: kedja per bildruta, bryt vid klipp
def reg(a, b, strang=True):
    """registrera bildruta a mot b. -> (ok, steg 3x3 i full upplösning, inliers)"""
    p0 = cv2.goodFeaturesToTrack(gra[a], 500, 0.01, 7, mask=mask(a))
    diff = float(np.mean(cv2.absdiff(cv2.resize(gra[a], (64, 112)), cv2.resize(gra[b], (64, 112)))))
    if p0 is None or len(p0) < 15:
        return (diff <= 25), np.eye(3), 0
    p1, st, _ = cv2.calcOpticalFlowPyrLK(gra[a], gra[b], p0, None, winSize=(21, 21), maxLevel=3)
    ok = st.ravel() == 1
    if ok.sum() < 10: return False, np.eye(3), 0
    A, inm = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.5)
    if A is None: return False, np.eye(3), 0
    inl = int(inm.sum()); andel = inl / max(1, ok.sum())
    sk = float(np.sqrt(abs(np.linalg.det(A[:, :2])))); tr = float(np.hypot(*A[:, 2])) / (W * SKALA)
    lim = (0.08, 0.12) if strang else (0.2, 0.3)  # över flera bildrutor får kameran ha rört sig mer
    if (andel < 0.35 and diff > 12) or abs(np.log(sk)) > lim[0] or tr > lim[1] or diff > 40:
        return False, np.eye(3), inl
    A[:, 2] /= SKALA
    return True, np.vstack([A, [0, 0, 1]]), inl

M = np.eye(3); seg = 0; logg = [{"i": 0, "seg": 0, "M": M.copy(), "inl": None}]
i = 1; storning = 0
while i < N:
    ok, steg, inl = reg(i - 1, i)
    if ok:
        M = steg @ M; logg.append({"i": i, "seg": seg, "M": M.copy(), "inl": inl}); i += 1; continue
    # kandidat: bekräfta genom att registrera förbi störningen (text som tänds, föremål mot kameran, rörelseoskärpa)
    brygga = None
    for k in (3, 6, 10):
        if i - 1 + k < N:
            ok2, steg2, inl2 = reg(i - 1, i - 1 + k, strang=False)
            if ok2: brygga = (k, steg2); break
    if brygga:
        k, steg2 = brygga
        for j in range(1, k):  # interpolera inte: håll kameran under störningen
            logg.append({"i": i - 1 + j, "seg": seg, "M": M.copy(), "inl": 0, "storning": True})
        M = steg2 @ M; logg.append({"i": i - 1 + k, "seg": seg, "M": M.copy(), "inl": None}); storning += 1
        i = i - 1 + k + 1
    else:
        seg += 1; M = np.eye(3); logg.append({"i": i, "seg": seg, "M": M.copy(), "inl": None, "klipp": True}); i += 1
# segment kortare än 0,25 s är övergångar: slå ihop med nästa
for q in logg: q.setdefault("seg", 0)
langd = {}
for q in logg: langd[q["seg"]] = langd.get(q["seg"], 0) + 1
ny, karta = 0, {}
for s in sorted(langd):
    karta[s] = ny
    if langd[s] >= int(0.25 * fps): ny += 1
for q in logg:
    s2 = karta[q["seg"]]
    if langd[q["seg"]] < int(0.25 * fps): q["overgang"] = True
    q["seg"] = s2
logg = [q for q in logg if not q.get("overgang")]
seg = max(q["seg"] for q in logg)
# kedjan börjar om i varje segment
for s in range(seg + 1):
    rad = [q for q in logg if q["seg"] == s]
    if rad:
        M0inv = np.linalg.inv(rad[0]["M"])
        for q in rad: q["M"] = q["M"] @ M0inv
print("störningar överbryggade:", storning)

segment = []
for s in range(seg + 1):
    rad = [q for q in logg if q["seg"] == s]
    segment.append({"seg": s, "in": round(rad[0]["i"] / fps, 3), "ut": round((rad[-1]["i"] + 1) / fps, 3), "rad": rad})

def kropp(p):
    k = p["kp"]
    pts = [k[i] for i in (11, 12) if k[i][2] > .3] or [[k[i][0], k[i][1] + 0.12, 1] for i in (5, 6) if k[i][2] > .3]
    if not pts: return None
    return np.array([np.mean([q[0] for q in pts]) * W, np.mean([q[1] for q in pts]) * H])

ut = {"klipp": namn, "w": W, "h": H, "fps": fps, "klipp_tider": [s["in"] for s in segment[1:]], "segment": []}
FARG = [(230, 168, 106), (90, 122, 224), (127, 191, 95), (224, 139, 195), (74, 176, 224), (200, 200, 90)]
for s in segment:
    rad = s["rad"]
    if len(rad) < 6:
        ut["segment"].append({"seg": s["seg"], "in": s["in"], "ut": s["ut"], "kort": True}); continue
    zoom = [float(np.sqrt(abs(np.linalg.det(q["M"][:2, :2])))) for q in rad]
    w = rad[int(np.argmin(zoom))]["M"]  # vidaste vyn blir scenens referens
    bana = []
    for q in rad[::3]:
        Ms = w @ np.linalg.inv(q["M"])          # bildruta -> scen
        c = np.linalg.inv(Ms) @ np.array([W / 2, H / 2, 1])  # var scenens mitt syns i bild ... omvänt: kamerans mitt i scen:
        kc = Ms @ np.array([W / 2, H / 2, 1])
        bana.append({"t": round(q["i"] / fps, 3), "mitt": [round(kc[0] / W, 4), round(kc[1] / H, 4)],
                     "zoom": round(float(1 / np.sqrt(abs(np.linalg.det(Ms[:2, :2])))), 4), "roll": round(float(np.degrees(np.arctan2(Ms[1, 0], Ms[0, 0]))), 2)})
    per = {}
    for q in rad:
        t = q["i"] / fps; j = int(np.abs(yolo_t - t).argmin())
        if abs(yolo_t[j] - t) > 0.017: continue
        Ms = w @ np.linalg.inv(q["M"])
        for p in spar["bilder"][j]["p"]:
            if p["id"] is None: continue
            k = kropp(p)
            if k is None: continue
            sc = Ms @ np.array([k[0], k[1], 1])
            per.setdefault(int(p["id"]), []).append({"t": round(t, 3), "bild": [round(k[0] / W, 4), round(k[1] / H, 4)], "scen": [round(sc[0] / W, 4), round(sc[1] / H, 4)]})
    matt = {}
    for pid, lst in per.items():
        if len(lst) < 8: continue
        bi = np.array([x["bild"] for x in lst]); sc = np.array([x["scen"] for x in lst])
        spann = lambda a: float(np.linalg.norm(np.percentile(a, 95, axis=0) - np.percentile(a, 5, axis=0)))
        matt[pid] = {"n": len(lst), "spann_bild": round(spann(bi), 3), "spann_scen": round(spann(sc), 3)}
    kamspann = float(np.linalg.norm(np.percentile([b["mitt"] for b in bana], 95, axis=0) - np.percentile([b["mitt"] for b in bana], 5, axis=0)))
    ut["segment"].append({"seg": s["seg"], "in": s["in"], "ut": s["ut"], "kamera_spann": round(kamspann, 3),
                          "zoom_spann": [round(min(b["zoom"] for b in bana), 3), round(max(b["zoom"] for b in bana), 3)],
                          "bana": bana, "personer": per, "matt": matt})
    # mosaik i scenens plan
    urval = rad[:: max(1, len(rad) // 14)]
    hörn = []
    for q in urval:
        Ms = w @ np.linalg.inv(q["M"]); h_ = np.array([[0, 0, 1], [W, 0, 1], [W, H, 1], [0, H, 1]]) @ Ms.T; hörn.append(h_[:, :2] / h_[:, 2:])
    allt = np.vstack(hörn); x0, y0 = allt.min(0); x1, y1 = allt.max(0)
    Wm, Hm = int(min(3 * W, x1 - x0)) + 1, int(min(3 * H, y1 - y0)) + 1
    T = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]])
    mos = np.zeros((Hm, Wm, 3), np.uint8)
    for q in urval:
        wr = cv2.warpPerspective(rutor[q["i"]], T @ w @ np.linalg.inv(q["M"]), (Wm, Hm))
        mos = np.where(wr.sum(2, keepdims=True) > 0, wr, mos)
    for j, (pid, lst) in enumerate(sorted(per.items(), key=lambda x: -len(x[1]))[:6]):
        if len(lst) < 8: continue
        sp = (np.array([x["scen"] for x in lst]) * [W, H] - [x0, y0]).astype(int)
        cv2.polylines(mos, [sp.reshape(-1, 1, 2)], False, FARG[j], 6); cv2.putText(mos, str(pid), tuple(int(v) for v in sp[0]), cv2.FONT_HERSHEY_SIMPLEX, 1.4, FARG[j], 4)
    kb = (np.array([b["mitt"] for b in bana]) * [W, H] - [x0, y0]).astype(int)
    cv2.polylines(mos, [kb.reshape(-1, 1, 2)], False, (255, 255, 255), 3)
    cv2.imwrite(str(D / f"kamera-mosaik-{s['seg']}.jpg"), cv2.resize(mos, None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 80])

for old in D.glob("kamera-mosaik-*.jpg"):
    if int(old.stem.split("-")[-1]) > seg: old.unlink()
json.dump(ut, open(D / "kamera.json", "w", encoding="utf-8"), separators=(",", ":"))
print(namn, "klipp vid", ut["klipp_tider"])
for s in ut["segment"]:
    if s.get("kort"): print(f"  seg {s['seg']} {s['in']:.2f}-{s['ut']:.2f} (kort)"); continue
    print(f"  seg {s['seg']} {s['in']:.2f}-{s['ut']:.2f}s  kamerans rörelse (spann) {s['kamera_spann']:.3f}  zoom {s['zoom_spann']}")
    for pid, m in sorted(s["matt"].items(), key=lambda x: -x[1]["n"])[:4]:
        print(f"     spår {pid:>3} n{m['n']:>3}  spann bild {m['spann_bild']:.3f} -> scen {m['spann_scen']:.3f}")
