"""Diagnos köttbit: rotationsskillnad sim mot original per ryggkropp (ΔR = Gs·G0ᵀ, i världen; samma ΔR som fran_smpl ger MHR-leden),
och vad samma ΔR gör med SMPL- resp. MHR-offseten (framåt = −y i världen här, kameran tittar längs +y).
  scen/.venv/Scripts/python.exe -X utf8 diagnos_kottbit/ryggdelta.py trofe2 ..."""
import sys, json
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HIT)); sys.dont_write_bytecode = True
import mhr_smpl as M, tagning as TG
from scipy.spatial.transform import Rotation as Ro
ix = M.SN.index
for namn in sys.argv[1:]:
    L = json.loads((HIT / 'ut' / f'mening_{namn}' / 'logg.json').read_text(encoding='utf-8'))
    t = TG.las(L['kalla'], L['liggare'], L['scen'], L['person']); ref = TG.referens(t); u = ref['u']
    P, q, k, _ = TG.las_utfall(HIT / 'ut' / f'mening_{namn}' / 'mm.npz', ref['S']); Gs = Ro.from_quat(q.reshape(-1, 4)).as_matrix().reshape(k, -1, 3, 3)
    G0 = u['G'][1:k + 1]; S0 = M.fk_smpl(G0, ref['rot'][1:k + 1]); Ss = M.fk_smpl(Gs, ref['rot'][1:k + 1])   # samma rotposition: bara rotationernas verkan
    print(f'== {namn}')
    for j in ('Pelvis', 'Torso', 'Spine', 'Chest', 'Neck', 'R_Thorax', 'R_Shoulder'):
        e = Ro.from_matrix(np.einsum('fab,fcb->fac', Gs[:, ix(j)], G0[:, ix(j)])).as_rotvec(); m = np.degrees(e.mean(0))
        print(f'  {j:10s} ΔR medel-rotvektor (grader kring x,y,z) {m.round(1)}  |ΔR| medel {np.degrees(np.linalg.norm(e, axis=1)).mean():.1f}')
    for j in ('Chest', 'Neck', 'Head', 'R_Shoulder', 'R_Wrist'):
        d = ((Ss[:, ix(j)] - Ss[:, 0]) - (S0[:, ix(j)] - S0[:, 0])).mean(0) * 100; print(f'  SMPL {j:10s} Δ rel. Pelvis (FK, samma rot) cm {d.round(1)}')
