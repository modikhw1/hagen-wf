"""2D-led ur originalet (yolo11n-pose, lokalt CPU). Oberoende bildobservation för reprojektionsfel."""
from __future__ import annotations
import json, time
from pathlib import Path
import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[3]
VIDEO = ROOT / 'data/format/kontroll/klipp/duepiani-7650849186912406806.mp4'
OUT = Path(__file__).resolve().parent / 'ut'

def main():
    t0 = time.perf_counter(); m = YOLO(str(ROOT / 'scen/py/modeller/yolo11n-pose.pt'))
    cap = cv2.VideoCapture(str(VIDEO)); rows = []; n = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        r = m.predict(f, conf=0.25, verbose=False)[0]
        pers = []
        if r.keypoints is not None and len(r.boxes):
            for b, kp, kc in zip(r.boxes.xyxy.numpy(), r.keypoints.xy.numpy(), r.keypoints.conf.numpy()):
                pers.append({'box': [round(float(v), 1) for v in b], 'kp': [[round(float(x), 1), round(float(y), 1), round(float(c), 3)] for (x, y), c in zip(kp, kc)]})
        rows.append({'ruta': n, 'personer': pers}); n += 1
    OUT.mkdir(exist_ok=True)
    (OUT / 'pose2d.json').write_text(json.dumps({'modell': 'yolo11n-pose', 'bild_px': [540, 960], 'rutor': rows, 'sek': round(time.perf_counter() - t0, 1)}), encoding='utf-8')
    print('rutor', n, 'sek', round(time.perf_counter() - t0, 1))

if __name__ == '__main__':
    main()
