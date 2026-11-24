"""Lokal uppföljning av jämn-passet. Skriver bara nya granskningsfiler."""
import json
import sys
from pathlib import Path
import numpy as np

H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H))
from trohet import KP, LED, F, ruta, projicera

for clip, run in [('b', 'tom3'), ('kenny', 'tom3'), ('a', 'tom3'), ('notan', 'jamn_tom')]:
    p = json.loads((H / 'ut' / clip / run / 'plan.json').read_text(encoding='utf-8'))
    print(clip, flush=True)
    for sc in p['scener']:
        for pm in sc['personer'][:1]:
            S = dict(np.load(pm['rorelse'])); V = dict(np.load(sc['varld']))
            folder = Path(pm['rorelse']).parent; pid = pm['ingest_id']; errs = [[], [], []]
            for u in range(*sc['ut']):
                f = sc['lokal_start'] + u - sc['ut'][0]; raw = folder / 'kropp' / pid / f'{f:04d}.npz'
                if not raw.exists(): continue
                with np.load(raw) as B:
                    target = B['pred_keypoints_2d'][KP]
                    xy = S['pose'][f, LED, :3] @ F / 100 + S.get('cam_t_fore_golv', S['cam_t'])[f]
                    uv = xy[:, :2] / xy[:, 2:3] * float(S['fokal']) + [p['kallbild_bredd']/2, p['utdata']['hojd']/2]
                    errs[0].extend(np.linalg.norm(uv-target, axis=1))
                    for std, arr in [(False, errs[1]), (True, errs[2])]:
                        uv = projicera(ruta(sc, pm, f, std, (S, V))[LED], p['matkamera']['nycklar'][u], p['kallbild_bredd'], p['utdata']['hojd'])
                        arr.extend(np.linalg.norm(uv-target, axis=1))
            print(sc['id'], pm['id'], 'före golv / plan utan stöd / byggd',
                  *[np.round(np.percentile(e, [50, 90]), 2).tolist() if e else [] for e in errs],
                  'cam_t delta', round(float(np.median(np.linalg.norm(S['cam_t']-S.get('cam_t_fore_golv', S['cam_t']), axis=1))), 4), flush=True)
