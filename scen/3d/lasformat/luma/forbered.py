"""Par-prov Luma mot original: bygger en 12-rutors video (0-5 Luma S1-S6, 6-11 originalrutor), personrutor, jobbfil för
SAM 3D Body, YOLO-pose och djup (Depth Anything V2 Small) per bild. Kör: scen/.venv/Scripts/python.exe forbered.py"""
import json, glob
from pathlib import Path
import cv2, numpy as np
from scipy.stats import spearmanr

HIT = Path(__file__).resolve().parent
SCEN = HIT.parents[2]
W, H = 576, 1024
RUTOR = {1: 36, 2: 110, 3: 167, 4: 213, 5: 277, 6: 308}   # NYCKEL i py/skikt25d.py (KF_*_Fnnn)

cap = cv2.VideoCapture(str(SCEN / 'klipp' / 'd-dialog-notan.mp4'))
def kallruta(i):
    cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, f = cap.read(); assert ok, i
    return cv2.resize(f, (W, H))

bilder = [cv2.resize(cv2.imread(str(SCEN / 'luma' / 'd-dialog-notan' / 'gemini_skikt' / f'S{n}.jpg')), (W, H)) for n in RUTOR]
bilder += [kallruta(i) for i in RUTOR.values()]
(HIT / 'bilder').mkdir(exist_ok=True)
for k, b in enumerate(bilder):
    cv2.imwrite(str(HIT / 'bilder' / f'{k:02d}.png'), b)
vw = cv2.VideoWriter(str(HIT / 'par.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 30, (W, H))
for b in bilder: vw.write(b)
vw.release()

from ultralytics import YOLO
pose = YOLO(str(SCEN / 'py' / 'modeller' / 'yolo11n-pose.pt'))
jobb, yolo = [], {}
for k, b in enumerate(bilder):
    r = pose(b, verbose=False)[0]
    if len(r.boxes) == 0:
        yolo[k] = None; continue
    xyxy = r.boxes.xyxy.cpu().numpy(); ytor = (xyxy[:, 2] - xyxy[:, 0]) * (xyxy[:, 3] - xyxy[:, 1]); j = int(ytor.argmax())
    yolo[k] = dict(ruta=xyxy[j].tolist(), kp=r.keypoints.xy[j].cpu().numpy().tolist(), konf=r.keypoints.conf[j].cpu().numpy().tolist(),
                   rutkonf=float(r.boxes.conf[j]), antal_personer=int(len(r.boxes)))
    jobb.append([k, 'p', [float(v) for v in xyxy[j]]])
json.dump(jobb, open(HIT / 'jobb.json', 'w'))
json.dump(yolo, open(HIT / 'yolo.json', 'w'))

from transformers import pipeline
from PIL import Image
djupm = pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Small-hf', device='cpu')
djup = [np.array(djupm(Image.fromarray(cv2.cvtColor(b, cv2.COLOR_BGR2RGB)))['predicted_depth'], dtype=np.float32) for b in bilder]
np.save(HIT / 'djup.npy', np.stack([cv2.resize(d, (W // 4, H // 4)) for d in djup]))
rho = {}
for n_i, n in enumerate(RUTOR):
    a, b = cv2.resize(djup[n_i], (W // 4, H // 4)).ravel(), cv2.resize(djup[n_i + 6], (W // 4, H // 4)).ravel()
    rho[f'S{n}'] = round(float(spearmanr(a, b).correlation), 3)
json.dump(rho, open(HIT / 'djup_rho.json', 'w'), indent=1)
fok = float(np.load(sorted(glob.glob(str(SCEN / '3d/ingest/ut/notan-tagningar/S4/kropp/4/*.npz')))[0])['focal_length'])
print('jobb', len(jobb), 'fokal', fok, 'djup rho', rho)
