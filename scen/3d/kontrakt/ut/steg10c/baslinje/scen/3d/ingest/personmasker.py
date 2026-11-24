"""Per-person-masker till SAM 3D Bodys maskprompt (SAM-Body4D:s kärnidé utan SAM 3, som är gated, och utan Depth-Anything-V2-Large,
som är CC-BY-NC). YOLO11-seg körs om per bildruta, och varje detektering matchas mot personer.json (IoU >= 0,5), så att
person-ID:n från spårningen inte ändras och kropp-cachen förblir giltig. Masken skrivs som PNG i halv upplösning.

Kör: scen/.venv/Scripts/python.exe scen/3d/ingest/personmasker.py <klipp.mp4> <utmapp>
Ut:  <utmapp>/personmasker/<pid>/<ruta:04d>.png
"""
import sys, json
from pathlib import Path
import numpy as np, cv2

HIT = Path(__file__).resolve().parent; YOLO = HIT.parent.parent / 'py/modeller/yolo11n-seg.pt'


def iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]); i = max(0, x1 - x0) * max(0, y1 - y0)
    return i / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i + 1e-9)


def main(klipp, ut):
    from ultralytics import YOLO as Y
    ut = Path(ut); P = json.loads((ut / 'personer.json').read_text()); mod = Y(str(YOLO)); n_ok = n_tot = 0
    for i, r in enumerate(mod.predict(str(klipp), classes=[0], conf=.2, retina_masks=True, stream=True, verbose=False)):
        b = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else np.zeros((0, 4)); m = r.masks.data.cpu().numpy() if r.masks is not None else None
        for pid, d in P.items():
            if str(i) not in d: continue
            n_tot += 1; ruta = d[str(i)]
            if m is None or not len(b): continue
            s = [iou(ruta, bb) for bb in b]; k = int(np.argmax(s))
            if s[k] < .5: continue
            mk = (m[k] > .5).astype(np.uint8) * 255; mk = cv2.resize(mk, (mk.shape[1] // 2, mk.shape[0] // 2), interpolation=cv2.INTER_NEAREST)
            (ut / 'personmasker' / pid).mkdir(parents=True, exist_ok=True); cv2.imwrite(str(ut / 'personmasker' / pid / f'{i:04d}.png'), mk); n_ok += 1
    print(json.dumps(dict(masker=n_ok, av=n_tot)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
