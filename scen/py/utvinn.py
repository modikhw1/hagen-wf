"""Metod 1, 2D-spår: scener (PySceneDetect) + poser och spårning (YOLO11-pose) + föremål (YOLO-World, öppet ordförråd).

Användning: .venv/Scripts/python.exe py/utvinn.py klipp/a-sketch-servering.mp4 [--steg 3]
Skriver data/<namn>/spar.json.
"""
import json, sys, time, argparse
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--steg", type=int, default=3, help="var n:te bildruta (30 fps / 3 = 10 fps)")
ap.add_argument("--ut", default=None)
ap.add_argument("--utan-foremal", action="store_true")
a = ap.parse_args()

ROT = Path(__file__).resolve().parent.parent
video = Path(a.video)
namn = video.stem
ut = Path(a.ut) if a.ut else ROT / "data" / namn
ut.mkdir(parents=True, exist_ok=True)

t0 = time.time()
# --- scener
from scenedetect import detect, ContentDetector, AdaptiveDetector
scener = detect(str(video), AdaptiveDetector(min_scene_len=8))
if not scener:
    import cv2
    cap = cv2.VideoCapture(str(video)); n = cap.get(cv2.CAP_PROP_FRAME_COUNT); fps = cap.get(cv2.CAP_PROP_FPS)
    sc = [{"i": 0, "start": 0.0, "slut": round(n / fps, 3)}]
else:
    sc = [{"i": i, "start": round(s.get_seconds(), 3), "slut": round(e.get_seconds(), 3)} for i, (s, e) in enumerate(scener)]
t_scen = time.time() - t0

# --- poser med spårning
from ultralytics import YOLO
import cv2
cap = cv2.VideoCapture(str(video))
fps = cap.get(cv2.CAP_PROP_FPS); W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
cap.release()

pose = YOLO(str(ROT / "py" / "modeller" / "yolo11n-pose.pt"))
FOREMAL = ["plate", "pizza", "kebab meat", "raw meat", "food", "sandwich", "cup", "phone", "bag", "tray", "scale", "knife", "bowl", "bottle", "table", "chair", "counter", "box"]
if not a.utan_foremal:
    vark = YOLO(str(ROT / "py" / "modeller" / "yolov8s-worldv2.pt"))
    vark.set_classes(FOREMAL)

bilder = []
t1 = time.time()
res = pose.track(source=str(video), stream=True, vid_stride=a.steg, persist=True, verbose=False, tracker="bytetrack.yaml", imgsz=640)
for k, r in enumerate(res):
    t = round(k * a.steg / fps, 3)
    pers = []
    if r.boxes is not None and len(r.boxes):
        ids = r.boxes.id.int().tolist() if r.boxes.id is not None else [None] * len(r.boxes)
        for j in range(len(r.boxes)):
            b = r.boxes.xyxyn[j].tolist(); c = float(r.boxes.conf[j])
            kp = r.keypoints.xyn[j].tolist(); kc = r.keypoints.conf[j].tolist() if r.keypoints.conf is not None else [1] * 17
            pers.append({"id": ids[j], "c": round(c, 2), "box": [round(v, 4) for v in b],
                         "kp": [[round(x, 4), round(y, 4), round(q, 2)] for (x, y), q in zip(kp, kc)]})
    bilder.append({"t": t, "p": pers, "_img": r.orig_img if not a.utan_foremal else None})
t_pose = time.time() - t1

t2 = time.time()
if not a.utan_foremal:
    for b in bilder:
        rr = vark.predict(b["_img"], verbose=False, conf=0.15, imgsz=640)[0]
        b["f"] = [{"k": FOREMAL[int(c)], "c": round(float(q), 2), "box": [round(v, 4) for v in bx]}
                  for bx, c, q in zip(rr.boxes.xyxyn.tolist(), rr.boxes.cls.tolist(), rr.boxes.conf.tolist())]
for b in bilder:
    b.pop("_img", None)
t_for = time.time() - t2

json.dump({"klipp": namn, "w": W, "h": H, "fps": fps, "steg": a.steg, "scener": sc, "bilder": bilder,
           "tid_s": {"scener": round(t_scen, 1), "poser": round(t_pose, 1), "foremal": round(t_for, 1)}},
          open(ut / "spar.json", "w"), separators=(",", ":"))
print(namn, "scener", len(sc), "bilder", len(bilder), "tid", round(t_scen, 1), round(t_pose, 1), round(t_for, 1))
