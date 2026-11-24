"""Diagnos köttbit: uppskattning (ändrar inget) av c_spine3:s förskjutning om Chest i stället styr c_spine2 (c_spine3 ärver), mot dagens KARTA där Spine-ΔR
gäller över c_spine1->c_spine2->c_spine3. ΔR = Gs·G0ᵀ är oberoende av B, så uppskattningen kräver ingen omkörning av simulatorn.
Jämförs med simulatorns egen SMPL-förskjutning av Chest+Neck-roten (det MHR borde återge)."""
import sys, json
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HIT)); sys.dont_write_bytecode = True
import mhr_smpl as M, tagning as TG
from scipy.spatial.transform import Rotation as Ro
ix = M.ix; SN = M.SN
for namn in sys.argv[1:]:
    L = json.loads((HIT / 'ut' / f'mening_{namn}' / 'logg.json').read_text(encoding='utf-8')); t = TG.las(L['kalla'], L['liggare'], L['scen'], L['person'])
    ref = TG.referens(t); u = ref['u']; P, q, k, _ = TG.las_utfall(HIT / 'ut' / f'mening_{namn}' / 'mm.npz', ref['S'])
    Gs = Ro.from_quat(q.reshape(-1, 4)).as_matrix().reshape(k, -1, 3, 3); G0 = u['G'][1:k + 1]; p0 = u['pos_mhr'][1:k + 1]
    dR = lambda j: np.einsum('fab,fcb->fac', Gs[:, SN.index(j)], G0[:, SN.index(j)])
    off = lambda a, b: p0[:, ix(b)] - p0[:, ix(a)]; rot = lambda R, v: np.einsum('fab,fb->fa', R, v) - v
    idag = rot(dR('Torso'), off('c_spine0', 'c_spine1')) + rot(dR('Spine'), off('c_spine1', 'c_spine2')) + rot(dR('Spine'), off('c_spine2', 'c_spine3'))
    ny = rot(dR('Torso'), off('c_spine0', 'c_spine1')) + rot(dR('Spine'), off('c_spine1', 'c_spine2')) + rot(dR('Chest'), off('c_spine2', 'c_spine3'))
    S0 = M.fk_smpl(G0, ref['rot'][1:k + 1]); Ss = M.fk_smpl(Gs, ref['rot'][1:k + 1]); sm = ((Ss[:, SN.index('Neck')] - Ss[:, 0]) - (S0[:, SN.index('Neck')] - S0[:, 0]))
    print(f'{namn}: c_spine3 Δ (cm) idag {(idag.mean(0) * 100).round(1)}  med Chest->c_spine2 {(ny.mean(0) * 100).round(1)}  sim SMPL Neck {(sm.mean(0) * 100).round(1)}')
