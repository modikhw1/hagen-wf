# E37: personer i bild (YOLOv8n, 6 rutor per klipp). data/format/e37/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e37_personer.py   (återupptas)
import json
from pathlib import Path
import cv2, numpy as np, torch
from ultralytics import YOLO
torch.set_num_threads(2)
E = Path(__file__).resolve().parents[2] / "data" / "format" / "e37"; UT = E / "personer.jsonl"
klar = {json.loads(l)["id"] for l in UT.read_text(encoding="utf-8").splitlines() if l.strip()} if UT.exists() else set()
DIR = Path.home() / "Downloads" / "letrend-e13"
ids = sorted(f.stem for f in DIR.glob("*.mp4") if f.stem.rsplit("-", 1)[-1].isdigit() and f.stem not in klar)
mod = YOLO(str(E / "yolov8n.pt"))
print(f"{len(ids)} klipp", flush=True)
with UT.open("a", encoding="utf-8") as ut:
    for n, i in enumerate(ids):
        try:
            cap = cv2.VideoCapture(str(DIR / f"{i}.mp4")); N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); rutor = []
            for t in np.linspace(0.05, 0.95, 6):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * max(N - 1, 0))); ok, f = cap.read()
                if ok: rutor.append(f)
            cap.release()
            ant = [int(sum(1 for b in r.boxes if int(b.cls) == 0 and float(b.conf) >= 0.4)) for r in mod(rutor, verbose=False, imgsz=320)] if rutor else []
            ut.write(json.dumps({"id": i, "antal": ant}) + "\n")
        except Exception as e:
            print("FEL", i, str(e)[:100], flush=True)
        if n % 200 == 0: ut.flush(); print(f"  {n}", flush=True)
print("klart", flush=True)
