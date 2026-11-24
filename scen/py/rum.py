"""Metod 2, rum i 2,5D/3D: bakgrundsplatta per scen (median), djup (Depth Anything V2 Small),
ankare (bord/stol/disk ur YOLO-World i spar.json) och personernas fötter på golvet.
MediaPipe PoseLandmarker ger 3D-pose i meter per person.

Användning: .venv/Scripts/python.exe py/rum.py klipp/c-sketch-tre.mp4
Läser data/<namn>/spar.json och skriver data/<namn>/rum.json, plattor och djup i data/<namn>/rum/.
"""
import json, sys, time
from pathlib import Path
import numpy as np, cv2
from PIL import Image

ROT = Path(__file__).resolve().parent.parent
video = Path(sys.argv[1]); namn = video.stem
D = ROT / "data" / namn; (D / "rum").mkdir(parents=True, exist_ok=True)
spar = json.load(open(D / "spar.json"))
W, H, fps = spar["w"], spar["h"], spar["fps"]

t0 = time.time()
cap = cv2.VideoCapture(str(video))
alla = []
while True:
    ok, f = cap.read()
    if not ok: break
    alla.append(f)
cap.release()
n = len(alla)

from transformers import pipeline
djupm = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device="cpu")

import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
lm = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=str(ROT / "py" / "modeller" / "pose_landmarker_full.task")),
    running_mode=vision.RunningMode.IMAGE, num_poses=4))

FOV = 60.0  # antagen vertikal synvinkel; telefonens huvudkamera i stående läge ligger nära
fy = (H / 2) / np.tan(np.radians(FOV / 2)); fx = fy

def till3d(u, v, z):
    """bildkoordinat (0..1) + relativt djup -> kamerakoordinater (x höger, y upp, z framåt)"""
    x = (u * W - W / 2) / fx * z; y = -(v * H - H / 2) / fy * z
    return [round(float(x), 3), round(float(y), 3), round(float(z), 3)]

rum = []
for s in spar["scener"]:
    a, b = int(s["start"] * fps), max(int(s["start"] * fps) + 1, int(s["slut"] * fps))
    idx = np.linspace(a, min(b, n) - 1, num=min(25, max(1, b - a))).astype(int)
    platta = np.median(np.stack([alla[i] for i in idx]), axis=0).astype(np.uint8)  # personer som rör sig försvinner
    cv2.imwrite(str(D / "rum" / f"platta-{s['i']}.jpg"), platta, [cv2.IMWRITE_JPEG_QUALITY, 80])
    dj = djupm(Image.fromarray(cv2.cvtColor(platta, cv2.COLOR_BGR2RGB)))["predicted_depth"]
    dj = dj.squeeze().numpy(); dj = cv2.resize(dj, (W, H))
    # Depth Anything ger omvänt relativt djup (stort = nära). Gör om till pseudo-meter: z = k / (d + e)
    dn = (dj - dj.min()) / (dj.max() - dj.min() + 1e-6)
    z = 1.0 / (0.15 + dn) * 0.9           # nära ~0,8 m, långt ~6 m
    cv2.imwrite(str(D / "rum" / f"djup-{s['i']}.png"), (dn * 255).astype(np.uint8))

    def z_vid(u, v):
        x = int(np.clip(u * W, 0, W - 1)); y = int(np.clip(v * H, 0, H - 1))
        return float(np.median(z[max(0, y - 4):y + 5, max(0, x - 4):x + 5]))

    # golvet: nedersta femtedelen, anpassa plan y = a*z + b i kamerakoordinater
    vs, us = np.mgrid[int(H * 0.8):H:8, 0:W:8]
    P = np.array([till3d(u / W, v / H, z[v, u]) for u, v in zip(us.ravel(), vs.ravel())])
    A = np.c_[P[:, 2], np.ones(len(P))]; golv, *_ = np.linalg.lstsq(A, P[:, 1], rcond=None)

    bs = [bb for bb in spar["bilder"] if s["start"] <= bb["t"] < s["slut"]]
    # ankare: fasta föremål (median per klass) i 3D
    ank = {}
    for bb in bs:
        for f in bb.get("f", []):
            if f["k"] in ("table", "chair", "counter", "scale", "box", "tray") and f["c"] > 0.25:
                u = (f["box"][0] + f["box"][2]) / 2; v = (f["box"][1] + f["box"][3]) / 2
                ank.setdefault(f["k"], []).append((round(u, 2), round(v, 2)))
    ankare = []
    for k, pts in ank.items():
        # gruppera på position (avrundade rutor) och behåll stabila
        cnt = {}
        for p in pts: cnt[(round(p[0] * 5) / 5, round(p[1] * 5) / 5)] = cnt.get((round(p[0] * 5) / 5, round(p[1] * 5) / 5), 0) + 1
        for (u, v), c in sorted(cnt.items(), key=lambda x: -x[1])[:3]:
            if c >= max(3, len(bs) * 0.15):
                ankare.append({"namn": k, "u": u, "v": v, "pos": till3d(u, v, z_vid(u, v)), "stabil": round(c / len(bs), 2)})

    # personer: fötter -> golvpunkt per tidpunkt (spår-id från YOLO)
    banor = {}
    for bb in bs:
        for p in bb["p"]:
            kp = p["kp"]; fot = [kp[i] for i in (15, 16) if kp[i][2] > 0.4]
            if fot:
                u = sum(q[0] for q in fot) / len(fot); v = sum(q[1] for q in fot) / len(fot); syns = "fot"
            else:  # fötter utanför bild: höft + antagen höjd
                h = [kp[i] for i in (11, 12) if kp[i][2] > 0.4]
                if not h: continue
                u = sum(q[0] for q in h) / len(h); v = sum(q[1] for q in h) / len(h); syns = "hoft"
            banor.setdefault(str(p["id"]), []).append({"t": bb["t"], "pos": till3d(u, v, z_vid(u, v)), "via": syns})

    # 3D-pose (MediaPipe) på ett glest urval av bildrutor
    poser3d = []
    for i in idx[:: max(1, len(idx) // 8)]:
        im = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(alla[i], cv2.COLOR_BGR2RGB))
        r = lm.detect(im)
        for j, wl in enumerate(r.pose_world_landmarks):
            nl = r.pose_landmarks[j]
            poser3d.append({"t": round(i / fps, 3), "hoft_uv": [round((nl[23].x + nl[24].x) / 2, 3), round((nl[23].y + nl[24].y) / 2, 3)],
                            "varld": [[round(q.x, 3), round(-q.y, 3), round(-q.z, 3)] for q in wl]})
    rum.append({"scen": s["i"], "platta": f"rum/platta-{s['i']}.jpg", "djup": f"rum/djup-{s['i']}.png",
                "golv": {"y_ur_z": [round(float(golv[0]), 3), round(float(golv[1]), 3)]},
                "ankare": ankare, "banor": banor, "poser3d": poser3d})

json.dump({"klipp": namn, "fov": FOV, "w": W, "h": H, "rum": rum, "tid_s": round(time.time() - t0, 1)},
          open(D / "rum.json", "w"), separators=(",", ":"))
print(namn, "scener", len(rum), "ankare", sum(len(r["ankare"]) for r in rum), "banor", sum(len(r["banor"]) for r in rum),
      "poser3d", sum(len(r["poser3d"]) for r in rum), "tid", round(time.time() - t0, 1))
