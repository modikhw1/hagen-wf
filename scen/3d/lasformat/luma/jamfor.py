"""Jämför SAM 3D Body på Luma-bild (0-5) mot originalruta (6-11), plus YOLO-pose. Skriver matt.json och en bildpanel."""
import json
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent
Y = json.load(open(HIT / 'yolo.json'))
ut, rader = {}, []
for n in range(6):
    a, b = HIT / 'kropp/p' / f'{n:04d}.npz', HIT / 'kropp/p' / f'{n + 6:04d}.npz'
    r = {}
    ya, yb = Y[str(n)], Y[str(n + 6)]
    if ya and yb:
        ka, kb, ca, cb = map(np.array, (ya['kp'], yb['kp'], ya['konf'], yb['konf']))
        h = yb['ruta'][3] - yb['ruta'][1]; m = (ca > .5) & (cb > .5)
        r['yolo_2d_avvik_proc_av_kroppshojd'] = round(float(np.linalg.norm(ka[m] - kb[m], axis=1).mean() / h * 100), 1) if m.any() else None
    if a.exists() and b.exists():
        A, B = np.load(a), np.load(b)
        h = B['bbox'][3] - B['bbox'][1]
        r['sam_2d_avvik_proc_av_kroppshojd'] = round(float(np.linalg.norm(A['pred_keypoints_2d'][:21] - B['pred_keypoints_2d'][:21], axis=1).mean() / h * 100), 1)
        rel = lambda D: D['pred_keypoints_3d'][:21] - D['pred_keypoints_3d'][[9, 10]].mean(0)   # MHR70 9/10 = höfter
        r['sam_3d_pose_avvik_cm'] = round(float(np.linalg.norm(rel(A) - rel(B), axis=1).mean() * 100), 1)
        hojd = lambda D: float(np.ptp(D['pred_vertices'][:, 1]))
        r['langd_m_luma_orig'] = [round(hojd(A), 3), round(hojd(B), 3)]
        r['avstand_m_luma_orig'] = [round(float(A['pred_cam_t'][2]), 2), round(float(B['pred_cam_t'][2]), 2)]
        r['form_avvik_shape_l2'] = round(float(np.linalg.norm(A['shape_params'] - B['shape_params'])), 2)
        for k, D in ((n, A), (n + 6, B)):
            im = cv2.imread(str(HIT / 'bilder' / f'{k:02d}.png'))
            for x, y in D['pred_keypoints_2d'][:21]:
                cv2.circle(im, (int(x), int(y)), 6, (0, 0, 255) if k < 6 else (0, 160, 0), -1)
            rader.append(cv2.resize(im, (288, 512)))
    ut[f'S{n + 1}'] = r
json.dump(ut, open(HIT / 'matt.json', 'w'), indent=1, ensure_ascii=False)
if rader:
    par = [np.hstack(rader[i:i + 2]) for i in range(0, len(rader), 2)]
    cv2.imwrite(str(HIT / 'panel.jpg'), np.hstack(par), [cv2.IMWRITE_JPEG_QUALITY, 80])
for k, v in ut.items(): print(k, v)
