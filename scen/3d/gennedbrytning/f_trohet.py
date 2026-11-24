"""0021 punkt 4: trohet i originalets ram, och hela kroppen i bild.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/f_trohet.py <variant> [--kamerafri]
Synliga överkroppsleder ur den nya läsningen, i videons pixlar skalade till 1080x1920, förs tillbaka till originalets rutor genom
inversen av avbildningen (kamerafri/avbildning.json) när källan var kamerafri, och jämförs med dagens läsning (promille av bildhöjden).
Hela kroppen i bild: båda fotlederna (pred_keypoints_2d 13:15) och huvudet inom bilden.
"""
import json, sys
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; DAG = ING / 'ut/kand-kennysgelato-tagningar/S1/kropp/1'
N = json.loads((ING / 'mhr_ledernamn.json').read_text())
OVER = ['c_neck', 'c_head', 'l_clavicle', 'r_clavicle', 'l_uparm', 'r_uparm', 'l_lowarm', 'r_lowarm', 'l_wrist', 'r_wrist']


def proj(z, W, H):
    k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); fl = float(z['focal_length'])
    return np.array([[fl * k[N.index(n), 0] / k[N.index(n), 2] + W / 2, fl * k[N.index(n), 1] / k[N.index(n), 2] + H / 2] for n in OVER])


def main():
    v = sys.argv[1]; kf = '--kamerafri' in sys.argv; d = HIT / 'd_video' / v
    c = cv2.VideoCapture(str(d / 'isolerad.mp4')); W, H, n = int(c.get(3)), int(c.get(4)), int(c.get(7)); s = 1080 / W
    avb = json.loads((HIT / 'kamerafri/avbildning.json').read_text(encoding='utf-8'))['rutor'] if kf else None
    dist, hel = [], 0
    for i in range(n):
        f = d / 'las/1' / f'{i:04d}.npz'
        if not f.exists(): continue
        z = np.load(f); kp = z['pred_keypoints_2d']
        if all(0 <= x < W and 0 <= y < H for x, y in kp[13:15]) and 0 <= kp[0][1] < H: hel += 1
        o = DAG / f'{i + 7:04d}.npz'
        if not o.exists(): continue
        p = proj(z, W, H) * s
        if kf: Ai = np.array(avb[i]['invers']); p = np.c_[p, np.ones(len(p))] @ Ai.T
        q = proj(np.load(o), 1080, 1920)
        dist += list(np.linalg.norm(p - q, axis=1) / 1920 * 1000)
    r = dict(variant=v, kamerafri=kf, hela_kroppen_i_bild_rutor=hel, av=n, overkropp_i_originalets_ram_promille=dict(median=round(float(np.median(dist)), 1), p90=round(float(np.percentile(dist, 90)), 1)))
    (d / 'trohet.json').write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__': main()
