"""0027 punkt 3: handföremålets fäste räknat mot den kropp som används, ur var föremålet syns i genereringen (det är inbakat där).

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/r_sked.py <d_video-variant> [--ben r_wrist] [--ljus 228]
Allmänt för vilken kropp och vilket handföremål som helst, så länge föremålet skiljer sig från personen och den grå duken:
1. I varje ruta av genereringen: ett fönster kring handens leder (handled och långfingrets topp, projicerade ur läsningen). Föremålets
   pixlar = ljusa och omättade (V > --ljus, S < 45) inne i fönstret, största sammanhängande delen. Duken (200) och huden faller bort.
2. Föremålets tyngdpunkt lyfts till 3D på handledens djup. Fästet = R^T (P - p) i handledens ram (R = läsningens globala rotation för
   benet, p = benets läge), samma definition som kontrakt/handforemal.py.
3. Medianen över rutorna där föremålet syns blir offset_m (status 'matt ur genereringen'). Avstånd hand–föremål före och efter redovisas.
Ut: d_video/<variant>/sked.json.
"""
import json, sys
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; N = json.loads((ING / 'mhr_ledernamn.json').read_text())
PLAN = HIT / 'g_forvarld/dreamina_t/plan.json'


def main():
    v = sys.argv[1]; ben = sys.argv[sys.argv.index('--ben') + 1] if '--ben' in sys.argv else 'r_wrist'; ljus = int(sys.argv[sys.argv.index('--ljus') + 1]) if '--ljus' in sys.argv else 228
    d = HIT / 'd_video' / v; c = cv2.VideoCapture(str(d / 'isolerad.mp4')); j = 0; off, rad = [], []
    fot = 'r_middle3' if ben.startswith('r') else 'l_middle3'
    while True:
        ok, f = c.read()
        if not ok: break
        z = np.load(d / 'las/1' / f'{j:04d}.npz'); H, W = f.shape[:2]; k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); fl = float(z['focal_length'])
        pr = lambda n: np.array([fl * k[N.index(n), 0] / k[N.index(n), 2] + W / 2, fl * k[N.index(n), 1] / k[N.index(n), 2] + H / 2])
        a, b = pr(ben), pr(fot); r = max(25., 1.6 * np.linalg.norm(b - a)); m = (a + b) / 2
        x0, y0, x1, y1 = [int(t) for t in (max(0, m[0] - r), max(0, m[1] - r), min(W, m[0] + r), min(H, m[1] + r))]
        hsv = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2HSV); mk = ((hsv[..., 2] > ljus) & (hsv[..., 1] < 45)).astype(np.uint8)
        nn, lab, st, cen = cv2.connectedComponentsWithStats(mk)
        if nn > 1 and st[1:, cv2.CC_STAT_AREA].max() >= 12:
            i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); px = cen[i] + [x0, y0]
            p = k[N.index(ben)]; djup = p[2]; P = np.array([(px[0] - W / 2) * djup / fl, (px[1] - H / 2) * djup / fl, djup])
            R = z['pred_global_rots'][N.index(ben)].astype(float); off.append(R.T @ (P - p)); rad.append(dict(ruta=j, px=px.round(1).tolist(), yta_px=int(st[i, cv2.CC_STAT_AREA])))
        j += 1
    off = np.array(off); med = np.median(off, 0) if len(off) else None
    plan = json.loads(PLAN.read_text(encoding='utf-8')); gammal = np.array(next(h for h in plan['handforemal'] if h['scen'] == 's1')['offset_m'])
    res = dict(variant=v, ben=ben, rutor=j, syns_i=len(rad), offset_m=None if med is None else med.round(4).tolist(),
               spridning_m=None if med is None else round(float(np.median(np.linalg.norm(off - med, axis=1))), 3),
               gammalt_offset_m=gammal.tolist(), avstand_till_handled_m=dict(gammalt=round(float(np.linalg.norm(gammal)), 3), nytt=None if med is None else round(float(np.linalg.norm(med)), 3)),
               status='matt ur genereringen', prov=rad[::10])
    (d / 'sked.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps({k: res[k] for k in res if k != 'prov'}, ensure_ascii=False))


if __name__ == '__main__': main()
