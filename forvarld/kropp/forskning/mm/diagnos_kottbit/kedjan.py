"""Diagnos köttbit: var uppstår framåtlutningen/handförflyttningen? Jämför i SMPL-rummet (z upp)
  (a) rundresa till_smpl -> fran_smpl utan simulering (ska vara identitet),
  (b) referensen efter grinden (ref_bas) mot originalets läsning, (c) simulatorns utfall (mm.npz) mot referensen.
  scen/.venv/Scripts/python.exe -X utf8 diagnos_kottbit/kedjan.py trofe2 bord_225429 uttrakad_vrid"""
import sys, json
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HIT)); sys.dont_write_bytecode = True
import mhr_smpl as M, tagning as TG
from scipy.spatial.transform import Rotation as Ro
ix = M.SN.index
def rel(P, j): return P[:, ix(j)] - P[:, ix('Pelvis')]
for namn in sys.argv[1:]:
    L = json.loads((HIT / 'ut' / f'mening_{namn}' / 'logg.json').read_text(encoding='utf-8'))
    t = TG.las(L['kalla'], L['liggare'], L['scen'], L['person']); z = t['z']; u0 = M.till_smpl(z, t['V'])
    S0 = M.fk_smpl(u0['G'], u0['rot'])                      # läst kropp, före grinden
    ref = TG.referens(t); Sr = ref['S']                       # efter grinden (raka ben, rot står)
    Pm, Tn = M.fran_smpl(u0['G'], u0['rot'], u0, z)            # (a) rundresa
    fel_pos = np.abs(Pm[:, :, :3] - z['pose'][:, :, :3]).max(); fel_T = np.abs(Tn - u0['T']).max()
    P, q, k, _ = TG.las_utfall(HIT / 'ut' / f'mening_{namn}' / 'mm.npz', ref['S'])
    print(f'== {namn}: rundresa max|Δpose| {fel_pos:.3f} cm, max|ΔT| {fel_T*100:.2f} cm')
    for j in ('Chest', 'Head', 'R_Hand', 'L_Hand'):
        a = (rel(Sr, j) - rel(S0, j))[1:k + 1].mean(0) * 100; b = (P[:, ix(j)] - P[:, :1].squeeze(1) - rel(Sr, j)[1:k + 1]).mean(0) * 100
        print(f'  {j:7s} grinden (ref−läst) x,y,z cm {a.round(1)}   simulatorn (mm−ref) {b.round(1)}')
    # bäckenets lutning (Pelvis-kroppens upp-axel mot z) i läst, ref och sim
    up = lambda R: np.degrees(np.arccos(np.clip(R[:, :, 2] @ np.array([0, 0, 1.]), -1, 1)))
    Gm = Ro.from_quat(q[:, 0]).as_matrix()
    gT = lambda G: np.degrees(np.arccos(np.clip(G[:, 2, 2], -1, 1)))
    print(f"  lutning Pelvis (grader från lodrätt): läst {gT(u0['G'][:, 0]).mean():.0f}, ref {gT(ref['G'][:, 0]).mean():.0f}, sim {gT(Gm).mean():.0f};"
          f" Chest: läst {gT(u0['G'][:, ix('Chest')]).mean():.0f}, ref {gT(ref['G'][:, ix('Chest')]).mean():.0f}, sim {gT(Ro.from_quat(q[:, ix('Chest')]).as_matrix()).mean():.0f}")
    print(f"  bäckenhöjd m: läst {S0[:,0,2].mean():.2f}, ref {Sr[:,0,2].mean():.2f}, sim {P[:,0,2].mean():.2f}")
