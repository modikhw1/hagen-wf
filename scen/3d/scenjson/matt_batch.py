"""Mäter alla bilder i utfall/<variant>/<S1|S4>*.png i EN Modal-körning och analyserar med matt_andring.analysera.
Kör: scen/.venv/Scripts/python.exe matt_batch.py"""
import json, subprocess, os, importlib.util
from pathlib import Path
import cv2

HIT = Path(__file__).resolve().parent; SCEN = HIT.parents[1]; UT = HIT / 'matning' / 'batch'; UT.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('m', HIT / 'matt_andring.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from ultralytics import YOLO
pose = YOLO(str(SCEN / 'py' / 'modeller' / 'yolo11n-pose.pt'))
bilder = sorted(f for f in (HIT / 'utfall').glob('*/*.png'))
vw = cv2.VideoWriter(str(UT / 'bilder.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 30, (576, 1024)); jobb, idx = [], []
for k, f in enumerate(bilder):
    im = cv2.resize(cv2.imread(str(f)), (576, 1024)); vw.write(im)
    r = pose(im, verbose=False)[0]; idx.append(dict(k=k, fil=f'{f.parent.name}/{f.name}', key=f.stem[:2], personer=int(len(r.boxes))))
    if len(r.boxes):
        xy = r.boxes.xyxy.cpu().numpy(); j = int(((xy[:, 2] - xy[:, 0]) * (xy[:, 3] - xy[:, 1])).argmax())
        jobb.append([k, 'p', [float(v) for v in xy[j]]])
vw.release(); json.dump(jobb, open(UT / 'jobb.json', 'w'))
subprocess.run([str(SCEN / '.venv/Scripts/modal.exe'), 'run', str(SCEN / '3d/ingest/modal_sam3db.py'), '--klipp', str(UT / 'bilder.mp4'),
                '--jobb', str(UT / 'jobb.json'), '--ut', str(UT / 'sam'), '--fokal', '1024'], check=True,
               env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, capture_output=True)
res = []
for i in idx:
    r = m.analysera(UT / 'sam' / 'p' / f'{i["k"]:04d}.npz', i['key'], i['fil']); r['personer_yolo'] = i['personer']; res.append(r)
    print(i['fil'], {x: r.get(x) for x in ('uppmatt_avstandsforandring_m', 'beordrad_geometrisk_avstandsforandring_m', 'uppmatt_vridning_egen_hogra_grader',
                                          'posedrift_procrustes_cm', 'dom', 'fel')})
json.dump(res, open(UT / 'resultat.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
