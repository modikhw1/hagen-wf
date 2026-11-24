"""FORSKNING/0040: SMPL-G (ProtoMotions MJCF, 24 kroppar) <-> Kimodo SOMA77.

Konventioner, kontrollerade mot källkoden och ut/neutral.npz (17 nov):
- Kimodos modell, dess utfall (local_rot_mats) och villkorsfilens 'local_joints_rot' ligger i STANDARD-T-posen:
  lokal = I för alla leder ger neutral_joints, en T-pose. skeleton.fk(local, root) återger posed_joints exakt (2e-7).
  from_standard_tpose behövs bara för BVH i BONES-SEED-vilan. Den används alltså inte här.
- Kimodos värld: x vänster, y upp, z framåt (tårna pekar +z i T-posen), meter, 30 fps. MJCF: x framåt, y vänster, z upp.
  v_mjcf = A v_kimodo. A härleds ur T-posens leder i axelbyte() och kontrolleras vid laddning.
- SMPL-G: globala rotationer från MJCF-vilan (T-pose, alla I) till nu. SOMA-rotationen i MJCF-ram: R = G B^T, och G = R B.
  B = minsta rotation från SMPL-benets riktning till SOMA-benets riktning i vilan. Den används bara för långa lemben
  (höft, knä, fotled, överarm, underarm, handled). Bål, nacke, huvud, nyckelben och tår har B = I, eftersom skillnaden
  där är var lederna sitter anatomiskt och inte hur personen står (SMPL:s nacke lutar 38° framåt i vilan, SOMA:s 17°).
- Rot: höftledernas mitt (SMPL L_Hip/R_Hip <-> SOMA LeftLeg/RightLeg) följs i sidled, skalad med benlängdskvoten s.
  Höjden sätts så att SOMA:s sula står lika högt (gånger s) som SMPL:s sula varje ruta. Sulan är den lägsta av fotled
  och tå minus ledens höjd över sulan i vilan (SMPL: fotlådornas underkant i MJCF; SOMA: LeftToeEnd = golvet).
  golv=True flyttar dessutom hela sekvensen så att sulans 2:a percentil hamnar på y = 0 (skiftet returneras).
- Leder utan motsvarighet: fingrar får Kimodos avslappnade handvila (relaxed_hands_rest_pose, samma som modellen sätter
  när SOMA30 fylls ut till 77), övriga (Neck2, Jaw, ögon, ändleder) lokal I, dvs följer föräldern.
  SMPL L_Hand/R_Hand får handledens G på vägen tillbaka.

Körs i Modal-containern (kimodo installerat) eller lokalt om paketet kimodo.skeleton går att importera.
  smpl_till_soma(G (T,24,3,3), rot (T,3)) -> dict(local_joints_rot (T,77,3) axis-angle, local_rot_mats, root_positions (T,3), s, golv_skift)
  soma_till_smpl(local_rot_mats (T,77,3,3), root_positions (T,3), s=None, golv_skift=0) -> (G (T,24,3,3), rot (T,3))
"""
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Ro

HIT = Path(__file__).resolve().parent
_MJCF = [HIT / 'smpl_humanoid.xml', HIT.parent / 'ProtoMotions/protomotions/data/assets/mjcf/smpl_humanoid.xml']

KARTA = {  # SMPL-kropp -> SOMA77-led
    'Pelvis': 'Hips', 'Torso': 'Spine1', 'Spine': 'Spine2', 'Chest': 'Chest', 'Neck': 'Neck1', 'Head': 'Head',
    'L_Hip': 'LeftLeg', 'L_Knee': 'LeftShin', 'L_Ankle': 'LeftFoot', 'L_Toe': 'LeftToeBase',
    'R_Hip': 'RightLeg', 'R_Knee': 'RightShin', 'R_Ankle': 'RightFoot', 'R_Toe': 'RightToeBase',
    'L_Thorax': 'LeftShoulder', 'L_Shoulder': 'LeftArm', 'L_Elbow': 'LeftForeArm', 'L_Wrist': 'LeftHand',
    'R_Thorax': 'RightShoulder', 'R_Shoulder': 'RightArm', 'R_Elbow': 'RightForeArm', 'R_Wrist': 'RightHand',
}
ARV = {'L_Hand': 'L_Wrist', 'R_Hand': 'R_Wrist'}            # SMPL-kroppar utan SOMA-led: förälderns G
# Lemben där vilornas benriktning rättas med B: SMPL-kropp -> (SMPL-barn, SOMA-barn)
LEMBEN = {'L_Hip': ('L_Knee', 'LeftShin'), 'L_Knee': ('L_Ankle', 'LeftFoot'), 'L_Ankle': ('L_Toe', 'LeftToeBase'),
          'R_Hip': ('R_Knee', 'RightShin'), 'R_Knee': ('R_Ankle', 'RightFoot'), 'R_Ankle': ('R_Toe', 'RightToeBase'),
          'L_Shoulder': ('L_Elbow', 'LeftForeArm'), 'L_Elbow': ('L_Wrist', 'LeftHand'), 'L_Wrist': ('L_Hand', 'LeftHandMiddle1'),
          'R_Shoulder': ('R_Elbow', 'RightForeArm'), 'R_Elbow': ('R_Wrist', 'RightHand'), 'R_Wrist': ('R_Hand', 'RightHandMiddle1')}
SOMA_SULA = {'L': ('LeftFoot', 'LeftToeBase', 'LeftToeEnd'), 'R': ('RightFoot', 'RightToeBase', 'RightToeEnd')}
SMPL_SULA = {'L': ('L_Ankle', 'L_Toe'), 'R': ('R_Ankle', 'R_Toe')}


# ---------- SMPL (MJCF) ----------
@lru_cache(None)
def smpl():
    f = next(p for p in _MJCF if p.exists()); namn, far, off, botten = [], [], [], {}
    def ga(e, p):
        for b in e.findall('body'):
            namn.append(b.get('name')); far.append(p); off.append([float(v) for v in b.get('pos').split()])
            for g in b.findall('geom'):
                if g.get('type') == 'box':
                    botten[b.get('name')] = float(g.get('pos').split()[2]) - float(g.get('size').split()[2])   # lådans underkant under leden
            ga(b, len(namn) - 1)
    ga(ET.parse(f).getroot().find('worldbody'), -1)
    far, off = np.array(far), np.array(off); V = np.zeros((len(namn), 3))
    for i in range(len(namn)): V[i] = (V[far[i]] if far[i] >= 0 else 0) + off[i]
    sula0 = min(V[namn.index(k), 2] + botten[k] for k in ('L_Ankle', 'L_Toe', 'R_Ankle', 'R_Toe'))
    h = {k: V[namn.index(k), 2] - sula0 for k in ('L_Ankle', 'L_Toe', 'R_Ankle', 'R_Toe')}       # ledens höjd över sulan i vilan
    return dict(namn=namn, far=far, off=off, vila=V, hojd=h, ben=V[namn.index('L_Hip'), 2] - sula0)


def fk_smpl(G, rot):
    S = smpl(); n = len(G); P = np.zeros((n, len(S['namn']), 3)); P[:, 0] = rot
    for i in range(1, len(S['namn'])): P[:, i] = P[:, S['far'][i]] + np.einsum('fab,b->fa', G[:, S['far'][i]], S['off'][i])
    return P


def sula_smpl(P):
    S = smpl(); ix = S['namn'].index
    return np.min(np.stack([P[:, ix(k), 2] - S['hojd'][k] for s in 'LR' for k in SMPL_SULA[s]], 1), 1)


# ---------- SOMA77 ----------
def axelbyte(nj, ix):
    """A (v_mjcf = A v_kimodo) ur T-posen: vänster = LeftArm - RightArm, upp = HeadEnd - Hips, framåt = LeftToeEnd - LeftFoot."""
    vanster = nj[ix['LeftArm']] - nj[ix['RightArm']]; upp = nj[ix['HeadEnd']] - nj[ix['Hips']]; fram = nj[ix['LeftToeEnd']] - nj[ix['LeftFoot']]
    upp = upp / np.linalg.norm(upp); fram = fram - upp * (fram @ upp); fram /= np.linalg.norm(fram); vanster = np.cross(upp, fram)
    assert np.dot(vanster, nj[ix['LeftArm']] - nj[ix['RightArm']]) > 0, 'vänster/höger stämmer inte med högerhänt system'
    A = np.stack([fram, vanster, upp])            # rad i: MJCF-axel i (x fram, y vänster, z upp) uttryckt i Kimodo-koordinater
    Ar = np.round(A); assert np.abs(A - Ar).max() < 0.1 and abs(np.linalg.det(Ar) - 1) < 1e-6, f'T-posen ligger inte längs axlarna: {A.round(3)}'
    return Ar


@lru_cache(None)
def soma():
    from kimodo.skeleton import SOMASkeleton77
    s = SOMASkeleton77(); nj = s.neutral_joints.double().cpu().numpy(); namn = list(s.bone_order_names); ix = s.bone_index
    far = s.joint_parents.cpu().numpy().astype(int); A = axelbyte(nj, ix)
    relax = s.relaxed_hands_rest_pose.double().cpu().numpy()
    fast = np.repeat(np.eye(3)[None], len(namn), 0)
    for i, n in enumerate(namn):
        if 'Hand' in n and n not in ('LeftHand', 'RightHand'): fast[i] = relax[i]          # fingrar: Kimodos avslappnade hand
    sula0 = min(nj[ix[k], 1] for k in ('LeftToeEnd', 'RightToeEnd'))
    h = {k: nj[ix[k], 1] - sula0 for s_ in 'LR' for k in SOMA_SULA[s_]}
    # B per SMPL-kropp
    S = smpl(); B = {}
    for j in S['namn']:
        if j in LEMBEN:
            sb, kb = LEMBEN[j]; o = S['off'][S['namn'].index(sb)]; d = A @ (nj[ix[kb]] - nj[ix[KARTA[j]]]); B[j] = minrot(o, d)
        else: B[j] = np.eye(3)
    B['L_Hand'], B['R_Hand'] = B['L_Wrist'], B['R_Wrist']
    ben = nj[ix['LeftLeg'], 1] - sula0
    return dict(namn=namn, ix=ix, far=far, nj=nj, A=A, fast=fast, hojd=h, B=B, ben=ben, s=ben / S['ben'], mappad={v: k for k, v in KARTA.items()})


def minrot(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b); v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-9: return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + vx + vx @ vx / (1 + c)


def fk_soma(L, rot):
    """Numpy-FK som kimodo.skeleton.fk: L (T,77,3,3) lokala i standard-T-posen, rot (T,3) = Hips. Ger (G, P)."""
    K = soma(); n = len(L); G = np.zeros_like(L); P = np.zeros((n, len(K['namn']), 3)); nj = K['nj']
    for i, p in enumerate(K['far']):
        if p < 0: G[:, i] = L[:, i]; P[:, i] = rot
        else: G[:, i] = G[:, p] @ L[:, i]; P[:, i] = P[:, p] + np.einsum('fab,b->fa', G[:, p], nj[i] - nj[p])
    return G, P


def sula_soma(P):
    K = soma(); ix = K['ix']
    return np.min(np.stack([P[:, ix[k], 1] - K['hojd'][k] for s in 'LR' for k in SOMA_SULA[s]], 1), 1)


def _mitt_soma(P): K = soma(); return (P[:, K['ix']['LeftLeg']] + P[:, K['ix']['RightLeg']]) / 2
def _mitt_smpl(P): ix = smpl()['namn'].index; return (P[:, ix('L_Hip')] + P[:, ix('R_Hip')]) / 2


# ---------- vägarna ----------
def smpl_till_soma(G_smpl, rot_smpl, golv=True, s=None):
    K, S = soma(), smpl(); A = K['A']; G_smpl = np.asarray(G_smpl, float); rot_smpl = np.asarray(rot_smpl, float); n = len(G_smpl)
    s = K['s'] if s is None else s; Gk = np.zeros((n, len(K['namn']), 3, 3)); L = np.zeros_like(Gk)
    for i, p in enumerate(K['far']):
        j = K['mappad'].get(K['namn'][i])
        if j is not None:
            R = G_smpl[:, S['namn'].index(j)] @ K['B'][j].T; Gk[:, i] = A.T @ R @ A
            L[:, i] = Gk[:, i] if p < 0 else np.transpose(Gk[:, p], (0, 2, 1)) @ Gk[:, i]
        else:
            L[:, i] = K['fast'][i]; Gk[:, i] = Gk[:, p] @ L[:, i]
    # rot: höftmitten i sidled (skalad), sulan i höjdled (skalad)
    Ps = fk_smpl(G_smpl, rot_smpl); _, P0 = fk_soma(L, np.zeros((n, 3)))
    mitt = (A.T @ (s * _mitt_smpl(Ps)).T).T; rot = mitt - _mitt_soma(P0)
    rot[:, 1] = s * sula_smpl(Ps) - sula_soma(P0)
    g = float(np.percentile(s * sula_smpl(Ps), 2)) if golv else 0.0; rot[:, 1] -= g
    aa = Ro.from_matrix(L.reshape(-1, 3, 3)).as_rotvec().reshape(n, -1, 3)
    return dict(local_joints_rot=aa, local_rot_mats=L, root_positions=rot, s=s, golv_skift=g)


def soma_till_smpl(local_rot_mats, root_positions, s=None, golv_skift=0.0):
    K, S = soma(), smpl(); A = K['A']; L = np.asarray(local_rot_mats, float); root = np.asarray(root_positions, float); n = len(L)
    s = K['s'] if s is None else s; Gk, Pk = fk_soma(L, root); G = np.zeros((n, len(S['namn']), 3, 3))
    for j in S['namn']:
        if j in KARTA: G[:, S['namn'].index(j)] = A @ Gk[:, K['ix'][KARTA[j]]] @ A.T @ K['B'][j]
    for j, f in ARV.items(): G[:, S['namn'].index(j)] = G[:, S['namn'].index(f)]
    P0 = fk_smpl(G, np.zeros((n, 3))); mitt = (A @ _mitt_soma(Pk).T).T / s; rot = mitt - _mitt_smpl(P0)
    rot[:, 2] = (sula_soma(Pk) + golv_skift) / s - sula_smpl(P0)
    return G, rot


def skriv_mm(G, rot, ut, dt=1 / 30):
    """mm.npz som TG.tillbaka läser: pos (k,24,3) via fk_smpl, rot (k,24,4) kvaternioner xyzw globala, skift 0, dt."""
    G = np.asarray(G, float); k = len(G); q = Ro.from_matrix(G.reshape(-1, 3, 3)).as_quat().reshape(k, -1, 4)
    np.savez(ut, pos=fk_smpl(G, rot).astype(np.float32), rot=q.astype(np.float32), skift=np.zeros(3, np.float32), dt=np.float32(dt))
    return ut


def vinkel(R1, R2):
    """Vinkel i grader mellan två rotationsfält (..., 3, 3)."""
    c = (np.einsum('...ij,...ij->...', R1, R2) - 1) / 2; return np.degrees(np.arccos(np.clip(c, -1, 1)))
