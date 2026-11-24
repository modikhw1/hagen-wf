"""Fas 3: gemensam förfining av A-bordets föremål och kamerorna i S3/S6 (S1 är ankare).

Kamerorna löstes i fas 1b enbart ur kroppen (PnP). Med kalibrerade föremål syns en systematisk förskjutning i S6 (och delvis S3).
Här löses föremålens (x, z) och små kamerakorrigeringar (±3°, ±6 cm) för S3 och S6 samtidigt, mot källrutorna för de föremål
som är pålitligt mätta (inte delvis skymda): burk, mugg, hamburgerlåda, inslaget föremål, såskopp (ej S6: flyttad mellan tagningar).
Efteråt måste kroppsfelet kontrolleras med verifiera.py --quick; om det blir sämre än 0,04 H återställs kamerorna (--aterstall).

Användning: scen/.venv/Scripts/python.exe -B scen/3d/forfina_kameror.py [--aterstall]
"""
import json, math, sys, shutil
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kalibrera_rekvisita_lib import kamera_fran, ruta2d, källruta, W, H

ROOT = Path(__file__).resolve().parent
FIL = ROOT / 'scen3d.json'; KOPIA = ROOT / 'scen3d.fore-kameraforfining.json'
if '--aterstall' in sys.argv:
    shutil.copy(KOPIA, FIL); print('återställde kamerorna från', KOPIA.name); sys.exit()
if '--fran-kopia' in sys.argv and KOPIA.exists(): shutil.copy(KOPIA, FIL)   # kör om från läget före förfiningen
spec = json.load(open(FIL, encoding='utf-8')); shutil.copy(FIL, KOPIA)
# kroppen: MediaPipes världspunkter -> rummet via layoutens raw_pose_to_world; synliga leder (ej händer/fingrar)
layout = json.load(open(ROOT / 'data/layout.json', encoding='utf-8')); motion = json.load(open(ROOT / 'data/sparning.json', encoding='utf-8'))['frames']
T_A = np.array(layout['actors']['A']['raw_pose_to_world'] if isinstance(layout['actors'], dict) else next(a for a in layout['actors'] if a['id'] == 'A')['raw_pose_to_world'])
KROPP = [0, 2, 5, 7, 8, 9, 10, 11, 12, 13, 14]   # näsa, ögon, öron, mun, axlar, armbågar
def kropp_obs(sid):
    c = layout['cameras'][sid]; ut = []
    for f in motion[c['start_frame']:c['end_frame_exclusive']:3]:
        if f['actor'] != 'A': continue
        w = np.array(f['pose']['world']); im = np.array(f['pose']['image'])
        for j in KROPP:
            if w[j, 3] > .7 and im[j, 3] > .7: ut.append(((T_A @ np.r_[w[j, :3], 1])[:3], np.array([im[j, 0] * W, im[j, 1] * H])))
    return ut
KROPPSOBS = {sid: kropp_obs(sid) for sid in ['S1', 'S3', 'S6']}
shots = {s['id']: s for s in spec['shots']}; props = {p['id']: p for p in spec['props']}
SAMPLES = {'S1': 36, 'S3': 141, 'S6': 309}
källor = {sid: {s['etikett']: källruta(s['box_2d']) for s in json.load(open(ROOT / f'data/props-source-{sid}-3.json', encoding='utf-8'))['saker']} for sid in SAMPLES}
PÅLITLIGA = {'A:can': ['S1', 'S3', 'S6'], 'A:cup': ['S1', 'S3', 'S6'], 'A:burger_wrap': ['S1', 'S3', 'S6'], 'A:rear_wrap': ['S1', 'S3', 'S6'], 'A:sauce': ['S1', 'S3']}
RÖRLIGA = ['S1', 'S3', 'S6'] if '--alla' in sys.argv else ['S3', 'S6']; pids = list(PÅLITLIGA)

def kamera_korr(shot, d):
    k = shot['camera']['keyframes'][0]; pos = np.array(k['pos']); tgt = np.array(k['target']); up = np.array(k.get('up', [0, 1, 0]))
    R = Rotation.from_euler('xyz', np.radians(d[:3])).as_matrix(); t = np.array(d[3:])
    return {**k, 'pos': (pos + t).tolist(), 'target': (pos + t + R @ (tgt - pos)).tolist(), 'up': (R @ up).tolist()}

def residual(x, med_reg=True):
    r = []
    xz = x[:2 * len(pids)].reshape(-1, 2); dk = x[2 * len(pids):].reshape(-1, 6)
    kams = {sid: kamera_fran(shots[sid]['camera']['keyframes'][0]) for sid in ['S1', 'S3', 'S6']}
    for i, sid in enumerate(RÖRLIGA): kams[sid] = kamera_fran(kamera_korr(shots[sid], dk[i]))
    for j, pid in enumerate(pids):
        p = props[pid]; pos = [xz[j, 0], p['transform']['position'][1], xz[j, 1]]
        for sid in PÅLITLIGA[pid]:
            if pid in källor[sid]: r += list((ruta2d(pos, p['dims'], p['transform'].get('yaw', 0), kams[sid]) - källor[sid][pid]) / 10.0)
    for i, sid in enumerate(RÖRLIGA):
        obs = KROPPSOBS[sid]; vikt = math.sqrt(40.0 / max(1, len(obs)))     # kroppen som helhet väger ungefär som ~10 föremålsrutor
        P = np.array([o[0] for o in obs]); Q = np.array([o[1] for o in obs])
        from kalibrera_rekvisita_lib import projicera
        r += list(((projicera(P, kams[sid]) - Q) / 10.0 * vikt).ravel())
    if med_reg:
        for i in range(len(RÖRLIGA)): r += list(dk[i, :3] / 1.0) + list(dk[i, 3:] / 0.02)   # 1° och 2 cm som "kostnad 1"
    return np.array(r)

from kalibrera_rekvisita_lib import projicera
def föremål_res(x):
    xz = x[:2 * len(pids)].reshape(-1, 2); dk = x[2 * len(pids):].reshape(-1, 6); r = []
    kams = {sid: kamera_fran(shots[sid]['camera']['keyframes'][0]) for sid in ['S1', 'S3', 'S6']}
    for i, sid in enumerate(RÖRLIGA): kams[sid] = kamera_fran(kamera_korr(shots[sid], dk[i]))
    for j, pid in enumerate(pids):
        p = props[pid]; pos = [xz[j, 0], p['transform']['position'][1], xz[j, 1]]
        for sid in PÅLITLIGA[pid]:
            if pid in källor[sid]: r += list(ruta2d(pos, p['dims'], p['transform'].get('yaw', 0), kams[sid]) - källor[sid][pid])
    return np.abs(np.array(r))
def kroppfel(x):
    dk = x[2 * len(pids):].reshape(-1, 6); ut = {}
    for i, sid in enumerate(RÖRLIGA):
        kam = kamera_fran(kamera_korr(shots[sid], dk[i])); P = np.array([o[0] for o in KROPPSOBS[sid]]); Q = np.array([o[1] for o in KROPPSOBS[sid]])
        ut[sid] = round(float(np.median(np.linalg.norm(projicera(P, kam) - Q, axis=1))), 1)
    return ut
x0 = np.concatenate([np.array([[props[p]['transform']['position'][0], props[p]['transform']['position'][2]] for p in pids]).ravel(), np.zeros(6 * len(RÖRLIGA))])
lo = np.concatenate([x0[:2 * len(pids)] - .3, np.tile([-3, -3, -3, -.06, -.06, -.06], len(RÖRLIGA))])
hi = np.concatenate([x0[:2 * len(pids)] + .3, np.tile([3, 3, 3, .06, .06, .06], len(RÖRLIGA))])
f_före, k_före = föremål_res(x0), kroppfel(x0)
sol = least_squares(residual, x0, bounds=(lo, hi))
f_efter, k_efter = föremål_res(sol.x), kroppfel(sol.x)
xz = sol.x[:2 * len(pids)].reshape(-1, 2); dk = sol.x[2 * len(pids):].reshape(-1, 6)
for j, pid in enumerate(pids): props[pid]['transform']['position'][0] = round(float(xz[j, 0]), 4); props[pid]['transform']['position'][2] = round(float(xz[j, 1]), 4)
props['A:burger']['transform']['position'][0] = props['A:burger_wrap']['transform']['position'][0]; props['A:burger']['transform']['position'][2] = props['A:burger_wrap']['transform']['position'][2]
for i, sid in enumerate(RÖRLIGA):
    shots[sid]['camera']['keyframes'] = [kamera_korr(shots[sid], dk[i])]
    shots[sid]['camera']['refinement'] = {'degrees_xyz': np.round(dk[i, :3], 3).tolist(), 'translation_m': np.round(dk[i, 3:], 4).tolist(), 'by': 'forfina_kameror.py (fas 3, föremål + kropp)'}
spec['editLog'].append({'phase': 3, 'action': 'S3/S6-kameror förfinade gemensamt mot pålitliga föremål och kroppens leder (S1 ankare); föremålens x,z omlösta.',
                        **{sid: np.round(dk[i], 3).tolist() for i, sid in enumerate(RÖRLIGA)}})
json.dump(spec, open(FIL, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'föremålsrutor (px per kant): median {np.median(f_före):.1f} -> {np.median(f_efter):.1f}, p90 {np.percentile(f_före, 90):.1f} -> {np.percentile(f_efter, 90):.1f}')
print('kroppens ledfel (proxy, median px):', k_före, '->', k_efter)
for i, sid in enumerate(RÖRLIGA): print(f'{sid}: rotation {np.round(dk[i, :3], 2).tolist()}°  förflyttning {np.round(dk[i, 3:] * 100, 1).tolist()} cm')
