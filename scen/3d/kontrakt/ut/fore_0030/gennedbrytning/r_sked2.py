"""0027 punkt 3: handföremålets fäste mot den kropp som faktiskt byggs, ur var föremålet syns i genereringen.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/r_sked2.py <d_video-variant> <scen-mapp> <samspel med sked_R> [--avbildning kamerafri/avbildning.json]
Allmänt för vilken kropp och vilket handföremål som helst:
1. Föremålets pixlar i genereringen (d_video/<v>/sked.json från r_sked.py: tyngdpunkt per genereringsruta).
2. Genereringsruta -> källruta (tid.json), genereringens pixel -> den kamerafria ramen (skala) -> originalets bild (inversen i avbildningen).
3. Strålen genom planens renderkamera för planrutan (källruta + 7), på handledens djup: föremålets punkt P i världen.
4. Fästets ram i den byggda scenen = föremålsobjektets egen världsrotation A (Child Of: sekvensens handledsrotation utan kalibrering),
   och fästets origo O = objektets läge minus A·offset_nu. Nytt offset = A^T (P - O), median över rutorna.
   Det ersätter fästet ur gårdagens kropp (kontrakt/handforemal.py mäter på samma sätt, men mot den kropp som fanns då).
Ut: <scen-mapp>/sked_fäste.json.
"""
import json, sys
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent; OFFS = 7


def main():
    v, scen, spf = sys.argv[1], HIT / sys.argv[2], HIT / sys.argv[3]
    avb = json.loads((HIT / (sys.argv[sys.argv.index('--avbildning') + 1] if '--avbildning' in sys.argv else 'kamerafri/avbildning.json')).read_text(encoding='utf-8'))['rutor']
    sk = json.loads((HIT / 'd_video' / v / 'sked.json').read_text(encoding='utf-8')); w = json.loads((HIT / 'd_video' / v / 'tid.json').read_text(encoding='utf-8'))['avbildning']
    plan = json.loads((scen / 'plan.json').read_text(encoding='utf-8')); h = next(x for x in plan['handforemal'] if x['scen'] == 's1'); off0 = np.array(h['offset_m'])
    sp = {r['ruta']: r for r in json.loads(spf.read_text())['rutor']}; nk = plan['renderkamera']['nycklar']
    # alla genereringsrutor med föremålet (sked.json sparar bara var tionde i 'prov'; räkna om alla här)
    import cv2
    from r_sked import N
    c = cv2.VideoCapture(str(HIT / 'd_video' / v / 'isolerad.mp4')); j = 0; px = {}
    while True:
        ok, f = c.read()
        if not ok: break
        z = np.load(HIT / 'd_video' / v / 'las/1' / f'{j:04d}.npz'); H, W = f.shape[:2]; k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); fl = float(z['focal_length'])
        pr = lambda n: np.array([fl * k[N.index(n), 0] / k[N.index(n), 2] + W / 2, fl * k[N.index(n), 1] / k[N.index(n), 2] + H / 2])
        a, b = pr('r_wrist'), pr('r_middle3'); r = max(25., 1.6 * np.linalg.norm(b - a)); m = (a + b) / 2
        x0, y0, x1, y1 = [int(t) for t in (max(0, m[0] - r), max(0, m[1] - r), min(W, m[0] + r), min(H, m[1] + r))]
        hsv = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2HSV); mk = ((hsv[..., 2] > 228) & (hsv[..., 1] < 45)).astype(np.uint8)
        nn, lab, st, cen = cv2.connectedComponentsWithStats(mk)
        if nn > 1 and st[1:, cv2.CC_STAT_AREA].max() >= 12: i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); px[j] = (cen[i] + [x0, y0]) * (1080 / W)
        j += 1
    nya, fore, efter = [], [], []
    for i, gj in enumerate(w):
        u = i + OFFS
        if gj not in px or u not in sp or not sp[u].get('sked_R'): continue
        q = np.array(avb[i]['invers']) @ np.r_[px[gj], 1]                 # originalets pixel
        K = np.array(nk[u]['matris']); R, C = K[:3, :3], K[:3, 3]; fpx = nk[u]['lins_mm'] / 36 * 1080
        d = R @ np.array([(q[0] - 540) / fpx, -(q[1] - 960) / fpx, -1.]); d /= np.linalg.norm(d)
        pw = np.array(sp[u]['leder']['r_wrist']['huvud']); djup = (pw - C) @ d; P = C + d * djup
        A = np.array(sp[u]['sked_R']); S = np.array(sp[u]['sked']); O = S - A @ off0
        nya.append(A.T @ (P - O)); fore.append(float(np.linalg.norm(S - P)))
    off = np.median(np.array(nya), 0)
    for i, gj in enumerate(w):
        u = i + OFFS
        if gj not in px or u not in sp or not sp[u].get('sked_R'): continue
        A = np.array(sp[u]['sked_R']); O = np.array(sp[u]['sked']) - A @ off0
        q = np.array(avb[i]['invers']) @ np.r_[px[gj], 1]; K = np.array(nk[u]['matris']); R, C = K[:3, :3], K[:3, 3]; fpx = nk[u]['lins_mm'] / 36 * 1080
        d = R @ np.array([(q[0] - 540) / fpx, -(q[1] - 960) / fpx, -1.]); d /= np.linalg.norm(d); pw = np.array(sp[u]['leder']['r_wrist']['huvud']); P = C + d * ((pw - C) @ d)
        efter.append(float(np.linalg.norm(O + A @ off - P)))
    res = dict(variant=v, rutor_med_foremal=len(nya), offset_m=off.round(4).tolist(), offset_fore=off0.tolist(), status='matt ur genereringen, mot den byggda kroppen',
               avstand_till_foremalet_i_genereringen_m=dict(fore_median=round(float(np.median(fore)), 3), efter_median=round(float(np.median(efter)), 3)))
    (scen / 'sked_faste.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__': main()
