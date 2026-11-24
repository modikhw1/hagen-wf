"""0018 punkt 3 / 0019 punkt 4: kroppsläsning av passade isolerade nyckelbilder med ingestens läsare (modal_sam3db.py, oförändrad).

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/las_stillbild.py <ut-mapp> <ruta>:<passad.png> [...]
Bilderna läggs som rutor i en kort mp4 (läsaren tar video), personrutan ur bildens personmask, samma fokal som ingesten (1920 px).
Mäts sedan mot dagens läsning av samma klippruta (ingestens kropp/1/<ruta+7>.npz): överkroppens leder i bild (promille av bildhöjden),
benlängder (lår, underben) och benlängd mot överkropp.
"""
import json, subprocess, sys
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; ROT = HIT.parents[2]; ING = HIT.parent / 'ingest'
N = json.loads((ING / 'mhr_ledernamn.json').read_text()); FOKAL = 1920.0; W, H = 1080, 1920
OVER = ['c_neck', 'c_head', 'l_clavicle', 'r_clavicle', 'l_uparm', 'r_uparm', 'l_lowarm', 'r_lowarm', 'l_wrist', 'r_wrist']


def leder(z):
    k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); fl = float(z['focal_length'])
    return {n: (fl * k[i, 0] / k[i, 2] + W / 2, fl * k[i, 1] / k[i, 2] + H / 2) for i, n in enumerate(N)}, z['pred_joint_coords'].astype(float)


def langd(j, a, b): return float(np.linalg.norm(j[N.index(a)] - j[N.index(b)]))


def matt(z, z0):
    p, j = leder(z); res = {}
    for s in ('l', 'r'):
        res[f'lar_{s}'] = round(langd(j, f'{s}_upleg', f'{s}_lowleg'), 3); res[f'underben_{s}'] = round(langd(j, f'{s}_lowleg', f'{s}_foot'), 3)
    res['overkropp'] = round(langd(j, 'root', 'c_neck'), 3)
    res['ben_mot_overkropp'] = round((res['lar_l'] + res['underben_l'] + res['lar_r'] + res['underben_r']) / 2 / res['overkropp'], 3)
    if z0 is not None:
        p0, _ = leder(z0); ov = [n for n in OVER if n in N]
        d = [np.hypot(p[n][0] - p0[n][0], p[n][1] - p0[n][1]) / H * 1000 for n in ov]
        res['overkropp_mot_original_promille'] = dict(median=round(float(np.median(d)), 1), max=round(float(np.max(d)), 1))
        res['original_ben_mot_overkropp'] = matt(z0, None)['ben_mot_overkropp']
    return res


def main():
    ut = Path(sys.argv[1]); ut.mkdir(parents=True, exist_ok=True); par = [(int(a.split(':', 1)[0]), a.split(':', 1)[1]) for a in sys.argv[2:]]
    vid = ut / 'stillbilder.mp4'; jobb = []
    if not (ut / 'las' / '1').exists() or len(list((ut / 'las' / '1').glob('*.npz'))) < len(par):
        v = cv2.VideoWriter(str(vid), cv2.VideoWriter_fourcc(*'mp4v'), 1, (W, H))
        for i, (r, f) in enumerate(par):
            im = cv2.imread(f); v.write(im)
            m = cv2.imread(f.replace('.png', '_mask.png'), 0); ys, xs = np.nonzero(m > 0)
            jobb.append([i, '1', [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]])
        v.release(); (ut / 'jobb.json').write_text(json.dumps(jobb), encoding='utf-8')
        subprocess.run([str(ROT / 'scen/.venv/Scripts/modal.exe'), 'run', str(ING / 'modal_sam3db.py'), '--klipp', str(vid), '--jobb', str(ut / 'jobb.json'),
                        '--ut', str(ut / 'las'), '--fokal', str(FOKAL)], check=True, cwd=ROT)
    res = {}
    for i, (r, f) in enumerate(par):
        z = np.load(ut / 'las' / '1' / f'{i:04d}.npz'); o = ING / f'ut/kand-kennysgelato-tagningar/S1/kropp/1/{r + 7:04d}.npz'
        res[f'{r}:{Path(f).stem}'] = matt(z, np.load(o) if o.exists() else None)
    (ut / 'matt.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__': main()
