"""Hypotes: den systematiska kamerakorrigeringen (−3° lutning, −6 cm) beror på fel bordshöjd relativt A:s kropp.
Test: kamerorna LÅSTA (fas 1b + kalibrering), fri gemensam höjd för A-bordets yta (alla A-föremål flyttas med), fria x,z per föremål.
Jämför föremålsresidual mot låst 0,75 m. Skriver inget, bara mäter. Kör från versionen före kameraförfining.
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kalibrera_rekvisita_lib import kamera_fran, ruta2d, källruta

ROOT = Path(__file__).resolve().parent
spec = json.load(open(ROOT / 'scen3d.fore-kameraforfining.json', encoding='utf-8'))
shots = {s['id']: s for s in spec['shots']}; props = {p['id']: p for p in spec['props']}
SAMPLES = ['S1', 'S3', 'S6']
källor = {sid: {s['etikett']: källruta(s['box_2d']) for s in json.load(open(ROOT / f'data/props-source-{sid}-3.json', encoding='utf-8'))['saker']} for sid in SAMPLES}
PÅLITLIGA = {'A:can': SAMPLES, 'A:cup': SAMPLES, 'A:burger_wrap': SAMPLES, 'A:rear_wrap': SAMPLES, 'A:sauce': ['S1', 'S3']}
pids = list(PÅLITLIGA); kams = {sid: kamera_fran(shots[sid]['camera']['keyframes'][0]) for sid in SAMPLES}
bas_y = {pid: props[pid]['transform']['position'][1] for pid in pids}

def res(x, fri_höjd):
    dy = x[-1] if fri_höjd else 0.0; xz = x[:2 * len(pids)].reshape(-1, 2); r = []
    for j, pid in enumerate(pids):
        p = props[pid]; pos = [xz[j, 0], bas_y[pid] + dy, xz[j, 1]]
        for sid in PÅLITLIGA[pid]:
            if pid in källor[sid]: r += list(ruta2d(pos, p['dims'], p['transform'].get('yaw', 0), kams[sid]) - källor[sid][pid])
    return np.array(r) / 10

x0 = np.array([[props[p]['transform']['position'][0], props[p]['transform']['position'][2]] for p in pids]).ravel()
låst = least_squares(lambda x: res(x, False), x0)
fri = least_squares(lambda x: res(x, True), np.r_[x0, 0.0], bounds=(np.r_[x0 - .4, -.15], np.r_[x0 + .4, .15]))
for namn, s, fh in [('låst bordshöjd 0,75 m', låst, False), ('fri bordshöjd', fri, True)]:
    e = np.abs(res(s.x, fh) * 10)
    print(f'{namn:<24} föremålsfel median {np.median(e):.1f} px, p90 {np.percentile(e, 90):.1f} px' + (f',  bordsyta {0.75 + s.x[-1]:.3f} m' if fh else ''))
# per tagning: systematisk vertikal förskjutning (modell - källa, mittpunkt y) med låst höjd
xz = låst.x.reshape(-1, 2)
for sid in SAMPLES:
    dy = []
    for j, pid in enumerate(pids):
        if sid in PÅLITLIGA[pid] and pid in källor[sid]:
            b = ruta2d([xz[j, 0], bas_y[pid], xz[j, 1]], props[pid]['dims'], 0, kams[sid]); s = källor[sid][pid]
            dy.append(((b[1] + b[3]) - (s[1] + s[3])) / 2)
    print(f'{sid}: modellens mitt ligger i snitt {np.mean(dy):+.1f} px {"under" if np.mean(dy) > 0 else "över"} källans (låst höjd)')
