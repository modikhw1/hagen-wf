"""Reprojektionsfel per kroppsspår och tagning mot oberoende 2D-pose (yolo11n-pose)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from geom import nyckel_pose, f_px, project, led_rutor

ROOT = Path(__file__).resolve().parents[3]
COCO = {5: 'l_uparm', 6: 'r_uparm', 7: 'l_lowarm', 8: 'r_lowarm', 9: 'l_wrist', 10: 'r_wrist',
        11: 'l_upleg', 12: 'r_upleg', 13: 'l_lowleg', 14: 'r_lowleg', 15: 'l_foot', 16: 'r_foot'}

def kamera_vid(t, u):
    ks = t['kamera']['nycklar']
    if len(ks) == 1: return nyckel_pose(ks[0])
    for k0, k1 in zip(ks, ks[1:]):
        if k0[0] <= u <= k1[0]:
            a = (u - k0[0]) / max(1, k1[0] - k0[0]); C0, R0, l0 = nyckel_pose(k0); C1, R1, l1 = nyckel_pose(k1)
            return C0 + (C1 - C0) * a, R0 if a < .5 else R1, l0 + (l1 - l0) * a
    return nyckel_pose(ks[-1])

def fel_per_spar(paket, pose, tagning):
    ix = {n: i for i, n in enumerate(paket['leder'])}; W, H = paket['bild']['bredd'], paket['bild']['hojd']
    sk = 540.0 / W; t = next(x for x in paket['tagningar'] if x['id'] == tagning); res = {}
    for pid in [p['id'] for p in t['personer']]:
        fr, X = led_rutor(paket, pid, tagning)
        if X is None: continue
        errs = []
        for u, J in zip(fr, X):
            C, R, lens = kamera_vid(t, u)
            uv, z = project(J, C, R, f_px(lens, W), W, H); uv = uv * sk
            pp = pose['rutor'][u]['personer']
            if not pp: continue
            best = None
            for p in pp:
                kp = np.array(p['kp'])
                e = [np.linalg.norm(uv[ix[j]] - kp[c, :2]) for c, j in COCO.items() if kp[c, 2] > .5 and z[ix[j]] > 0]
                if len(e) >= 3:
                    m = float(np.median(e))
                    best = m if best is None else min(best, m)
            if best is not None: errs.append(best)
        res[pid] = {'rutor_med_2d': len(errs), 'av_rutor': len(fr), 'median_px': round(float(np.median(errs)), 1) if errs else None}
    return res

if __name__ == '__main__':
    A = json.loads((ROOT / 'arbetsbord/data/ingest_v2/duepiani/paket.json').read_text(encoding='utf-8'))
    pose = json.loads((Path(__file__).resolve().parent / 'ut/pose2d.json').read_text(encoding='utf-8'))
    for t in A['tagningar']:
        print(t['id'], fel_per_spar(A, pose, t['id']))
