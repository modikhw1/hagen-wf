"""Poängsätter Luma-stillbilderna i utfall/bild mot originalen i indata/bild.
  steg 1:  python poang.py forbered   -> poang/par.mp4, poang/jobb.json, poang/index.json, poang/yolo.json
  (Modal) modal run ../../ingest/modal_sam3db.py --klipp poang/par.mp4 --jobb poang/jobb.json --ut poang/kropp --fokal 1024
  steg 2:  python poang.py analys     -> poang/poang.json + poang/panel.jpg
Mått som tål ändrad beskärning: pose jämförs efter Procrustes (2D: skala+flytt; 3D: rotation+flytt), så F2 och F7a går att jämföra."""
import json, sys
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; UT = HIT / 'poang'; UT.mkdir(exist_ok=True)
SCEN = HIT.parents[2]
W, H = 576, 1024

def lista():
    rad = [('original', s, HIT / 'indata' / 'bild' / f'{s}.png') for s in ('S1', 'S4')]
    for f in sorted((HIT / 'utfall' / 'bild').glob('*/*.png')):
        rad.append((f.parent.name, f.stem, f))
    return rad

def procrustes(A, B, skala):
    a, b = A - A.mean(0), B - B.mean(0)
    U, S, Vt = np.linalg.svd(a.T @ b); R = U @ Vt
    if np.linalg.det(R) < 0: U[:, -1] *= -1; R = U @ Vt
    s = S.sum() / (a ** 2).sum() if skala else 1.0
    return np.linalg.norm(s * a @ R - b, axis=1).mean()

if sys.argv[1] == 'forbered':
    from ultralytics import YOLO
    pose = YOLO(str(SCEN / 'py' / 'modeller' / 'yolo11n-pose.pt'))
    rad = lista(); vw = cv2.VideoWriter(str(UT / 'par.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 30, (W, H)); jobb, yolo, index = [], {}, []
    for k, (fmt, s, f) in enumerate(rad):
        im = cv2.resize(cv2.imread(str(f)), (W, H)); vw.write(im); cv2.imwrite(str(UT / f'{k:02d}.png'), im)
        index.append(dict(k=k, format=fmt, bild=s, fil=str(f.relative_to(HIT))))
        r = pose(im, verbose=False)[0]
        if len(r.boxes):
            xy = r.boxes.xyxy.cpu().numpy(); j = int(((xy[:, 2] - xy[:, 0]) * (xy[:, 3] - xy[:, 1])).argmax())
            yolo[k] = dict(antal=int(len(r.boxes)), konf=float(r.boxes.conf[j]), kpkonf=float(r.keypoints.conf[j].mean()))
            jobb.append([k, 'p', [float(v) for v in xy[j]]])
        else:
            yolo[k] = dict(antal=0)
    vw.release()
    json.dump(jobb, open(UT / 'jobb.json', 'w')); json.dump(yolo, open(UT / 'yolo.json', 'w')); json.dump(index, open(UT / 'index.json', 'w'), indent=1)
    from transformers import pipeline
    from PIL import Image
    dm = pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Small-hf', device='cpu')
    D = [cv2.resize(np.array(dm(Image.open(UT / f'{i["k"]:02d}.png').convert('RGB'))['predicted_depth'], np.float32), (W // 4, H // 4)) for i in index]
    np.save(UT / 'djup.npy', np.stack(D)); print('bilder', len(index), 'jobb', len(jobb))

else:
    from scipy.stats import spearmanr
    index = json.load(open(UT / 'index.json')); yolo = {int(k): v for k, v in json.load(open(UT / 'yolo.json')).items()}; D = np.load(UT / 'djup.npy')
    orig = {i['bild']: i['k'] for i in index if i['format'] == 'original'}
    def kropp(k):
        f = UT / 'kropp' / 'p' / f'{k:04d}.npz'; return np.load(f) if f.exists() else None
    res, panel = [], []
    for i in index:
        k, o = i['k'], orig[i['bild'].split('_')[0]]; r = dict(format=i['format'], bild=i['fil'].split('\\')[-1].split('/')[-1], personer=yolo[k].get('antal', 0))
        A, B = kropp(k), kropp(o)
        if A is not None and B is not None:
            r['pose2d_proc'] = round(float(procrustes(A['pred_keypoints_2d'][:21], B['pred_keypoints_2d'][:21], True) / (B['bbox'][3] - B['bbox'][1]) * 100), 1)
            r['pose3d_cm'] = round(float(procrustes(A['pred_keypoints_3d'][:21], B['pred_keypoints_3d'][:21], False) * 100), 1)
            r['langd_m'] = round(float(np.ptp(A['pred_vertices'][:, 1])), 3)
            kp = A['pred_keypoints_2d']; r['ben_i_bild'] = int(sum(0 <= x < W and 0 <= y < H for x, y in kp[13:17]))   # knän + vrister
        if i['format'] in ('F3',):   # Lumas djupbild: ljus = nära; DA-V2 ger större = nära
            g = cv2.resize(cv2.cvtColor(cv2.imread(str(UT / f'{k:02d}.png')), cv2.COLOR_BGR2GRAY).astype(np.float32), (W // 4, H // 4))
            r['djup_rho_mot_original'] = round(float(spearmanr(g.ravel(), D[o].ravel()).correlation), 3)
        elif i['format'] not in ('original', 'F2', 'F7a', 'F7b'):
            r['djup_rho_mot_original'] = round(float(spearmanr(D[k].ravel(), D[o].ravel()).correlation), 3)
        res.append(r)
        im = cv2.imread(str(UT / f'{k:02d}.png'))
        if A is not None:
            for x, y in A['pred_keypoints_2d'][:21]: cv2.circle(im, (int(x), int(y)), 7, (0, 0, 255), -1)
        cv2.putText(im, f"{i['format']} {r['bild']}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 3)
        panel.append(cv2.resize(im, (216, 384)))
    json.dump(res, open(UT / 'poang.json', 'w'), indent=1, ensure_ascii=False)
    rader = [np.hstack(panel[j:j + 9] + [np.zeros_like(panel[0])] * (9 - len(panel[j:j + 9]))) for j in range(0, len(panel), 9)]
    cv2.imwrite(str(UT / 'panel.jpg'), np.vstack(rader), [cv2.IMWRITE_JPEG_QUALITY, 80])
    for r in res: print(r)
