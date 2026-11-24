"""2D-led ur originalet (yolo11n-pose, CPU). Körs med scen/.venv. python pose2d.py <klipp> [--nyckel]"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import cv2
from ultralytics import YOLO
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('klipp'); ap.add_argument('--nyckel'); a = ap.parse_args()
    nyckel = a.nyckel or a.klipp.split('-')[0]; out = HERE / 'ut' / nyckel; out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter(); m = YOLO(str(ROOT / 'scen/py/modeller/yolo11n-pose.pt'))
    cap = cv2.VideoCapture(str(ROOT / 'data/format/kontroll/klipp' / (a.klipp + '.mp4'))); rows = []; n = 0; W = H = None
    while True:
        ok, f = cap.read()
        if not ok: break
        H, W = f.shape[:2]; r = m.predict(f, conf=0.25, verbose=False)[0]; pers = []
        if r.keypoints is not None and len(r.boxes):
            for b, kp, kc in zip(r.boxes.xyxy.numpy(), r.keypoints.xy.numpy(), r.keypoints.conf.numpy()):
                pers.append({'box': [round(float(v), 1) for v in b], 'kp': [[round(float(x), 1), round(float(y), 1), round(float(c), 3)] for (x, y), c in zip(kp, kc)]})
        rows.append({'ruta': n, 'personer': pers}); n += 1
    (out / 'pose2d.json').write_text(json.dumps({'modell': 'yolo11n-pose', 'bild_px': [W, H], 'rutor': rows, 'sek': round(time.perf_counter() - t0, 1)}), encoding='utf-8')
    print(nyckel, 'rutor', n, 'sek', round(time.perf_counter() - t0, 1))

if __name__ == '__main__':
    main()
