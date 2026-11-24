"""Diagnos köttbit: var sitter MHR-roten i förhållande till bäcken/rygg, och hur stor del av överkroppens förskjutning förklaras av
att rotens rotationsskillnad (sim Pelvis mot original) vrider hela offseten rot->c_spine0 (fran_smpl: posn[i] = posn[p] + ΔR_p (pos0_i - pos0_p)).
  scen/.venv/Scripts/python.exe -X utf8 diagnos_kottbit/rotled.py trofe2 ..."""
import sys, json
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HIT)); sys.dont_write_bytecode = True
import mhr_smpl as M, tagning as TG
from scipy.spatial.transform import Rotation as Ro
ix = M.ix; PAR = M.PAR
def kedja(j):
    k = [ix(j)]
    while PAR[k[-1]] >= 0: k.append(PAR[k[-1]])
    return [M.N[i] for i in k[::-1]]
print('kedja till c_spine3:', kedja('c_spine3')); print('kedja till r_wrist:', kedja('r_wrist'))
for namn in sys.argv[1:]:
    L = json.loads((HIT / 'ut' / f'mening_{namn}' / 'logg.json').read_text(encoding='utf-8'))
    t = TG.las(L['kalla'], L['liggare'], L['scen'], L['person']); z0 = t['z']; z1 = dict(np.load(HIT / 'ut' / f'mening_{namn}' / 'sekvens.npz'))
    p0, r0 = M.till_varld(z0, t['V'])[:2]; p1, r1 = M.till_varld(z1, t['V'])[:2]
    off = (p0[:, ix('c_spine0')] - p0[:, ix('root')]).mean(0) * 100
    print(f'== {namn}: rot->c_spine0 offset i världen (cm) {off.round(1)}, rot->l_upleg {((p0[:, ix("l_upleg")] - p0[:, ix("root")]).mean(0) * 100).round(1)}')
    dR = Ro.from_matrix(np.einsum('fab,fcb->fac', r1[:, ix('root')], r0[:, ix('root')]))
    e = dR.as_rotvec(); print(f'   rotens rotationsskillnad sekvens mot original: {np.degrees(np.linalg.norm(e, axis=1)).mean():.1f}° medel, axel (medel) {(e.mean(0) / np.linalg.norm(e.mean(0))).round(2)}')
    for j in ('c_spine0', 'c_spine3', 'c_head'):
        d = ((p1[:, ix(j)] - p1[:, ix('root')]) - (p0[:, ix(j)] - p0[:, ix('root')])).mean(0) * 100
        print(f'   {j:8s} rel. rot Δ {d.round(1)} cm')
