"""Diagnos köttbit: stämmer simulatorns rotationer med dess positioner? FK(Gs, rot) mot mm.npz-positionerna, per kropp (cm),
och samma för referensen (FK(ref G) mot ref S). Plus: tillbaka() med referensen i stället för simuleringen (ska ge ~0 i överkroppen).
  scen/.venv/Scripts/python.exe -X utf8 diagnos_kottbit/rotationer.py trofe2 ..."""
import sys, json
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HIT)); sys.dont_write_bytecode = True
import mhr_smpl as M, tagning as TG
from scipy.spatial.transform import Rotation as Ro
ix = M.SN.index
for namn in sys.argv[1:]:
    L = json.loads((HIT / 'ut' / f'mening_{namn}' / 'logg.json').read_text(encoding='utf-8'))
    t = TG.las(L['kalla'], L['liggare'], L['scen'], L['person']); ref = TG.referens(t)
    P, q, k, _ = TG.las_utfall(HIT / 'ut' / f'mening_{namn}' / 'mm.npz', ref['S'])
    for konv, Q in (('xyzw', q), ('wxyz', np.roll(q, -1, axis=-1))):
        Gs = Ro.from_quat(Q.reshape(-1, 4)).as_matrix().reshape(k, -1, 3, 3); Pf = M.fk_smpl(Gs, P[:, 0])
        d = {j: np.linalg.norm(Pf[:, ix(j)] - P[:, ix(j)], axis=1).mean() * 100 for j in ('Chest', 'Head', 'R_Hand', 'L_Hand', 'R_Ankle')}
        print(f'== {namn} kvat {konv}: FK(sim-rot) − sim-pos cm', {a: round(b, 1) for a, b in d.items()})
    Sr = M.fk_smpl(ref['G'], ref['rot']); print('   ref: FK − S cm', round(float(np.abs(Sr - ref['S']).max() * 100), 2))
    Gs = Ro.from_quat(q.reshape(-1, 4)).as_matrix().reshape(k, -1, 3, 3)
    print('   sim Pelvis-rot mot ref (grader, medel):', round(float(np.degrees((Ro.from_matrix(Gs[:, 0]) * Ro.from_matrix(ref['G'][1:k + 1, 0]).inv()).magnitude()).mean()), 1),
          ' Chest:', round(float(np.degrees((Ro.from_matrix(Gs[:, ix('Chest')]) * Ro.from_matrix(ref['G'][1:k + 1, ix('Chest')]).inv()).magnitude()).mean()), 1))
