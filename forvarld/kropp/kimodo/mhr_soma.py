"""0040: MHR <-> SOMA (somaskel30, Kimodo) i samma form som forskning/mm/mhr_smpl.py.

SOMA-vilan (kimodo/assets/skeletons/somaskel30/joints.p, T-pose) har samma axlar som MHR:s modellrum: y upp, x vänster, z framåt; Am = I.
Kimodos värld: y upp, golvet y = 0, roten i XZ-origo i ruta 0 (kanonisering). Världen ur mhr_rig.py är z upp: Kimodo = Rk · (världen - o) · s.
Per SOMA-led j med MHR-led m(j): G_j = Rk · Δ_m · B_j, Δ_m = R_värld_m · R_vila_m^T, B_j = minsta rotation från SOMA-benets riktning till
MHR-vilans (T- mot A-pose). Tillbaka: R_värld_m = Rk^T · G_j · B_j^T · R_vila_m; omappade leder följer sin förälder; MHR:s egna benlängder.
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Ro
HIT = Path(__file__).resolve().parent; sys.path.insert(0, str(HIT.parent / 'forskning/mm'))
import mhr_smpl as MS          # till_varld, minrot, gravitation, MHR-namn och föräldrar (ingen licensbunden kod; bara geometri)

ix, N, PAR = MS.ix, MS.N, MS.PAR
SN = ['Hips', 'Spine1', 'Spine2', 'Chest', 'Neck1', 'Neck2', 'Head', 'Jaw', 'LeftEye', 'RightEye', 'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand',
      'LeftHandThumbEnd', 'LeftHandMiddleEnd', 'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand', 'RightHandThumbEnd', 'RightHandMiddleEnd',
      'LeftLeg', 'LeftShin', 'LeftFoot', 'LeftToeBase', 'RightLeg', 'RightShin', 'RightFoot', 'RightToeBase']
FOR = {'Hips': None, 'Spine1': 'Hips', 'Spine2': 'Spine1', 'Chest': 'Spine2', 'Neck1': 'Chest', 'Neck2': 'Neck1', 'Head': 'Neck2', 'Jaw': 'Head', 'LeftEye': 'Head',
       'RightEye': 'Head', 'LeftShoulder': 'Chest', 'LeftArm': 'LeftShoulder', 'LeftForeArm': 'LeftArm', 'LeftHand': 'LeftForeArm', 'LeftHandThumbEnd': 'LeftHand',
       'LeftHandMiddleEnd': 'LeftHand', 'RightShoulder': 'Chest', 'RightArm': 'RightShoulder', 'RightForeArm': 'RightArm', 'RightHand': 'RightForeArm',
       'RightHandThumbEnd': 'RightHand', 'RightHandMiddleEnd': 'RightHand', 'LeftLeg': 'Hips', 'LeftShin': 'LeftLeg', 'LeftFoot': 'LeftShin', 'LeftToeBase': 'LeftFoot',
       'RightLeg': 'Hips', 'RightShin': 'RightLeg', 'RightFoot': 'RightShin', 'RightToeBase': 'RightFoot'}
SP = np.array([SN.index(FOR[n]) if FOR[n] else -1 for n in SN])
SV = np.load(HIT / 'soma30_vila.npy'); SO = np.array([SV[i] - (SV[SP[i]] if SP[i] >= 0 else 0) for i in range(len(SN))])
KARTA = {   # SOMA-led -> (MHR-led för rotation, SOMA-barn, MHR-led för barnets riktning)
    'Hips': ('root', None, None), 'Spine1': ('c_spine0', 'Spine2', 'c_spine1'), 'Spine2': ('c_spine1', 'Chest', 'c_spine3'), 'Chest': ('c_spine3', None, None),
    'Neck1': ('c_neck', 'Head', 'c_head'), 'Neck2': ('c_neck', 'Head', 'c_head'), 'Head': ('c_head', None, None),
    'Jaw': ('c_head', None, None), 'LeftEye': ('c_head', None, None), 'RightEye': ('c_head', None, None),
    'LeftShoulder': ('l_clavicle', 'LeftArm', 'l_uparm'), 'LeftArm': ('l_uparm', 'LeftForeArm', 'l_lowarm'), 'LeftForeArm': ('l_lowarm', 'LeftHand', 'l_wrist'),
    'LeftHand': ('l_wrist', 'LeftHandMiddleEnd', 'l_middle1'), 'LeftHandThumbEnd': ('l_wrist', None, None), 'LeftHandMiddleEnd': ('l_wrist', None, None),
    'RightShoulder': ('r_clavicle', 'RightArm', 'r_uparm'), 'RightArm': ('r_uparm', 'RightForeArm', 'r_lowarm'), 'RightForeArm': ('r_lowarm', 'RightHand', 'r_wrist'),
    'RightHand': ('r_wrist', 'RightHandMiddleEnd', 'r_middle1'), 'RightHandThumbEnd': ('r_wrist', None, None), 'RightHandMiddleEnd': ('r_wrist', None, None),
    'LeftLeg': ('l_upleg', 'LeftShin', 'l_lowleg'), 'LeftShin': ('l_lowleg', 'LeftFoot', 'l_foot'), 'LeftFoot': ('l_foot', 'LeftToeBase', 'l_ball'), 'LeftToeBase': ('l_ball', None, None),
    'RightLeg': ('r_upleg', 'RightShin', 'r_lowleg'), 'RightShin': ('r_lowleg', 'RightFoot', 'r_foot'), 'RightFoot': ('r_foot', 'RightToeBase', 'r_ball'), 'RightToeBase': ('r_ball', None, None),
}
ARV = {'LeftHandThumbEnd': 'LeftHand', 'LeftHandMiddleEnd': 'LeftHand', 'RightHandThumbEnd': 'RightHand', 'RightHandMiddleEnd': 'RightHand',
       'Jaw': 'Head', 'LeftEye': 'Head', 'RightEye': 'Head'}
TILLBAKA = ['Hips', 'Spine1', 'Spine2', 'Chest', 'Neck1', 'Head', 'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand', 'RightShoulder', 'RightArm', 'RightForeArm',
            'RightHand', 'LeftLeg', 'LeftShin', 'LeftFoot', 'LeftToeBase', 'RightLeg', 'RightShin', 'RightFoot', 'RightToeBase']
Rk = np.array([[1., 0., 0.], [0., 0., 1.], [0., -1., 0.]])     # världen (z upp) -> Kimodo (y upp): (x, y, z) -> (x, z, -y)


def B_matriser(rest):
    B = {}
    for j, (m, barn, mb) in KARTA.items():
        if barn is None: continue
        B[j] = MS.minrot(SO[SN.index(barn)], rest[ix(mb), :3] - rest[ix(m), :3])
    for j in KARTA:
        if j not in B: B[j] = B[ARV[j]] if j in ARV else np.eye(3)
    return B


def langd_soma(): return SV[SN.index('Head'), 1] - min(SV[SN.index('LeftToeBase'), 1], SV[SN.index('LeftFoot'), 1])


def till_soma(z, V):
    pos, rot, Q3, T = MS.till_varld(z, V); rest = z['rest'].astype(float); Rv = Ro.from_quat(rest[:, 3:7]).as_matrix(); B = B_matriser(rest)
    ri = MS.rensa(z); pos, rot = pos[ri], rot[ri]
    s = langd_soma() / MS.langd_mhr(rest); fot = np.concatenate([pos[:, ix(k)] for k in ('l_ball', 'r_ball', 'l_foot', 'r_foot')])
    o = np.array([pos[0, ix('root'), 0], pos[0, ix('root'), 1], np.percentile(fot[:, 2], 2)])
    n = len(pos); G = np.zeros((n, len(SN), 3, 3))
    for j, (m, _, _) in KARTA.items(): G[:, SN.index(j)] = Rk @ rot[:, ix(m)] @ Rv[ix(m)].T @ B[j]
    rotpos = s * (pos[:, ix('root')] - o) @ Rk.T
    dy = MS.golv_per_ruta(s * (np.stack([pos[:, ix(k), 2] for k in ('l_ball', 'r_ball', 'l_foot', 'r_foot')], 1) - o[2])); rotpos[:, 1] -= dy
    lok = G.copy()
    for i in range(1, len(SN)): lok[:, i] = np.transpose(G[:, SP[i]], (0, 2, 1)) @ G[:, i]
    return dict(G=G, lok=lok, rot=rotpos, s=s, o=o, B=B, pos_mhr=pos, rotm_mhr=rot, Q3=Q3, T=T, dy=dy, ri=ri)


def fk_soma(G, rotpos):
    n = len(G); P = np.zeros((n, len(SN), 3)); P[:, 0] = rotpos
    for i in range(1, len(SN)): P[:, i] = P[:, SP[i]] + np.einsum('fab,b->fa', G[:, SP[i]], SO[i])
    return P


def fran_soma(G, rotpos, ut, z):
    rest = z['rest'].astype(float); Rv = Ro.from_quat(rest[:, 3:7]).as_matrix(); B, s, o, Q3, T = ut['B'], ut['s'], ut['o'], ut['Q3'], ut['T']
    pos0, rot0 = ut['pos_mhr'], ut['rotm_mhr']; n = len(G); rotn = rot0.copy(); satt = np.zeros(len(N), bool)
    for j in TILLBAKA:
        m = KARTA[j][0]; rotn[:, ix(m)] = Rk.T @ G[:, SN.index(j)] @ B[j].T @ Rv[ix(m)]; satt[ix(m)] = True
    rp = rotpos.copy(); rp[:, 1] += ut.get('dy', 0)
    posn = pos0.copy(); posn[:, ix('root')] = (rp @ Rk) / s + o
    for i in range(len(N)):
        p = PAR[i]
        if p < 0 or i == ix('root'): continue
        if not satt[i]: rotn[:, i] = rotn[:, p] @ np.transpose(rot0[:, p], (0, 2, 1)) @ rot0[:, i]
        posn[:, i] = posn[:, p] + np.einsum('fab,fb->fa', rotn[:, p] @ np.transpose(rot0[:, p], (0, 2, 1)), pos0[:, i] - pos0[:, p])
    Qt = np.transpose(Q3, (0, 2, 1)); Tn = T + (posn[:, ix('root')] - pos0[:, ix('root')])
    P = z['pose'].astype(float).copy()
    P[:, :, :3] = np.einsum('fab,fjb->fja', Qt, posn - Tn[:, None]) * 100.
    P[:, :, 3:7] = Ro.from_matrix(np.einsum('fab,fjbc->fjac', Qt, rotn).reshape(-1, 3, 3)).as_quat().reshape(n, -1, 4)
    return P, Tn
