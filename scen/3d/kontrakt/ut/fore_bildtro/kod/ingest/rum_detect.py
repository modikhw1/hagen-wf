"""Cached open-vocabulary furniture detections, in source pixel coordinates."""
import json
from pathlib import Path

LABELS = ['bar counter', 'pool table', 'table', 'chair', 'sofa', 'cabinet', 'shelf', 'card payment terminal']


def detect(clip, ut, step=6):
    import cv2
    from ultralytics import YOLOWorld
    target = Path(ut) / 'rum' / 'detections.json'
    if target.exists(): return json.loads(target.read_text())
    model = YOLOWorld(str(Path(__file__).resolve().parents[2] / 'py/modeller/yolov8s-worldv2.pt'))
    model.set_classes(LABELS)
    cap = cv2.VideoCapture(str(clip)); result = []
    for i in range(int(cap.get(7))):
        ok, f = cap.read()
        if not ok: raise RuntimeError(f'Could not decode frame {i}')
        if i % step: continue
        pred = model.predict(f, imgsz=960, conf=.12, iou=.45, verbose=False)[0]
        for b, c, score in zip(pred.boxes.xyxy.tolist(), pred.boxes.cls.tolist(), pred.boxes.conf.tolist()):
            result.append(dict(frame=i, label=LABELS[int(c)], box=b, confidence=score))
    cap.release(); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=1))
    return result


if __name__ == '__main__':
    import sys
    d = detect(sys.argv[1], sys.argv[2])
    from collections import Counter
    print(Counter(o['label'] for o in d))
