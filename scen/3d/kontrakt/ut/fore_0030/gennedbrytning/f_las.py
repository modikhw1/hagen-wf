"""0017 del E–F: läs kroppen ur den isolerade videon med ingestens läsare (modal_sam3db.py, oförändrad) och mät mot dagens läsning ur originalet.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/f_las.py <variant>
Personruta per ruta ur hennes mask i den isolerade videon (allt som inte är jämnt grått, största sammanhängande; kundens hand utesluts).
Fokal: ingestens 1920 px för 1080 bredd, skalad till videons bredd. Dagens läsning: ingest kropp/1/<ruta+7>.npz.
Mått: vridning (bål och höft kring lodaxeln, i kamerans ram) ruta för ruta, hopp > 15°, största hopp; rotens hopp i m/ruta;
synliga överkroppsleder projicerade i bild mot originalets läsning (promille av bildhöjden); benlängder (spridning); maskens överlapp mot ingestens mask.
"""
import json, subprocess, sys
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; ROT = HIT.parents[2]; ING = HIT.parent / 'ingest'
N = json.loads((ING / 'mhr_ledernamn.json').read_text()); DAG = ING / 'ut/kand-kennysgelato-tagningar/S1/kropp/1'
OVER = ['c_neck', 'c_head', 'l_clavicle', 'r_clavicle', 'l_uparm', 'r_uparm', 'l_lowarm', 'r_lowarm', 'l_wrist', 'r_wrist']


def personmask(f):
    g = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); bak = (g[..., 1] < 30) & (g[..., 2] > 140)
    pm = (~bak).astype(np.uint8); pm = cv2.morphologyEx(pm, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(pm)
    return (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8) if n > 1 else pm


def vridning(z):
    R = z['pred_global_rots'].astype(float)
    def yaw(i):   # benets/bålens framåtriktning i kamerans x-z-plan
        f = R[i][:, 2]; return np.degrees(np.arctan2(f[0], f[2]))
    return yaw(N.index('c_spine2')), yaw(N.index('root'))


def serie(filer):
    out = []
    for f in filer:
        if not f.exists(): out.append(None); continue
        z = np.load(f); k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); fl = float(z['focal_length'])
        j = z['pred_joint_coords'].astype(float); bal, hoft = vridning(z)
        out.append(dict(k=k, fl=fl, bal=bal, hoft=hoft, rot=k[N.index('root')],
                        ben=[np.linalg.norm(j[N.index(f'{s}_upleg')] - j[N.index(f'{s}_lowleg')]) + np.linalg.norm(j[N.index(f'{s}_lowleg')] - j[N.index(f'{s}_foot')]) for s in 'lr']))
    return out


def stat(S, H):
    v = [s for s in S if s]; idx = [i for i, s in enumerate(S) if s]
    def hopp(nyckel):
        a = np.unwrap(np.radians([s[nyckel] for s in v])); d = np.degrees(np.abs(np.diff(a)))
        return dict(hopp_over_15=int((d > 15).sum()), storsta_hopp_grader=round(float(d.max()), 1), median_grader=round(float(np.median(d)), 2))
    r = np.array([s['rot'] for s in v]); dr = np.linalg.norm(np.diff(r, axis=0), axis=1)
    ben = np.array([s['ben'] for s in v])
    return dict(lasta_rutor=len(v), bal=hopp('bal'), hoft=hopp('hoft'), rot_hopp_m=dict(median=round(float(np.median(dr)), 3), max=round(float(dr.max()), 3), over_10cm=int((dr > .1).sum())),
                benlangd_m=dict(median=round(float(np.median(ben)), 3), spridning_cv=round(float(ben.std() / ben.mean()), 3)))


def main():
    v = sys.argv[1]; d = HIT / 'd_video' / v; vid = d / 'isolerad.mp4'
    c = cv2.VideoCapture(str(vid)); W, H = int(c.get(3)), int(c.get(4)); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    las = d / 'las'
    if not (las / '1').exists():
        jobb = []
        for i, f in enumerate(F):
            m = personmask(f); ys, xs = np.nonzero(m)
            if len(xs): jobb.append([i, '1', [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]])
        (d / 'jobb.json').write_text(json.dumps(jobb), encoding='utf-8')
        subprocess.run([str(ROT / 'scen/.venv/Scripts/modal.exe'), 'run', str(ING / 'modal_sam3db.py'), '--klipp', str(vid), '--jobb', str(d / 'jobb.json'),
                        '--ut', str(las), '--fokal', str(1920.0 * W / 1080)], check=True, cwd=ROT)
    ny = serie([las / '1' / f'{i:04d}.npz' for i in range(len(F))]); dag = serie([DAG / f'{i + 7:04d}.npz' for i in range(len(F))])
    # synliga överkroppsleder: den nya läsningen i den isolerade bildens pixlar, skalad till originalets 1080x1920, mot dagens läsning i originalet
    M = np.load(ING / 'ut/kand-kennysgelato-tagningar/S1/masker.npy'); s = 1080 / W; d_pm, ov = [], []
    for i in range(len(F)):
        a, b = ny[i], dag[i]
        if a and b:
            for n in OVER:
                pa = a['k'][N.index(n)]; pb = b['k'][N.index(n)]
                ua = np.array([a['fl'] * pa[0] / pa[2] + W / 2, a['fl'] * pa[1] / pa[2] + H / 2]) * s
                ub = np.array([b['fl'] * pb[0] / pb[2] + 540, b['fl'] * pb[1] / pb[2] + 960])
                d_pm.append(np.linalg.norm(ua - ub) / 1920 * 1000)
        if i + 7 < len(M):
            om = cv2.resize(M[i + 7].astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0; pm = personmask(F[i]) > 0
            if om.sum(): ov.append(float((pm & om).sum() / om.sum()))
    res = dict(variant=v, rutor_video=len(F), video_px=[W, H], ny=stat(ny, H), dag=stat(dag, 1920),
               overkropp_mot_dagens_lasning_promille=dict(median=round(float(np.median(d_pm)), 1), p90=round(float(np.percentile(d_pm, 90)), 1)),
               mask_overlapp_mot_originalets=dict(median=round(float(np.median(ov)), 3), min=round(float(np.min(ov)), 3)))
    (d / 'matt.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__': main()
