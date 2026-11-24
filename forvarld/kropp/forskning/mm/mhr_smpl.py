"""FORSKNING (0039): MHR <-> SMPL-humanoiden i ProtoMotions (MJCF), utan SMPL-modellfiler.

Kroppen är ProtoMotions smpl_humanoid.xml (24 kroppar, z upp, x framåt, y vänster, vila = T-pose, alla lokala rotationer = I).
MHR-sekvensen (modellrum, y upp, x vänster, z framåt, vila = A-pose) förs först till världen som mhr_rig.py gör
(Q3 = G·Rw·F, T = G·(C + Rw·cam_t)), sedan per SMPL-kropp j med MHR-led m(j):
    Δ_m(t) = R_värld_m(t) · (Am · R_vila_m)^T          (rotationen från MHR:s vila till nu, i världen)
    G_j(t) = Δ_m(t) · B_j                               (B_j = minsta rotation från MJCF-benets riktning till MHR-vilans, så T- och A-pose möts)
Rot: MHR-roten i världen, flyttad till golvet och skalad med s = SMPL-längd / MHR-längd.
Tillbaka: R_värld_m = G_j · B_j^T · Am · R_vila_m för mappade leder; omappade följer sin förälder; positioner med MHR:s egna benlängder.
"""
import json, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Ro

ROOT = Path(__file__).resolve().parents[4]
MJCF = Path(__file__).resolve().parents[1] / 'ProtoMotions/protomotions/data/assets/mjcf/smpl_humanoid.xml'
N = json.loads((ROOT / 'scen/3d/ingest/mhr_ledernamn.json').read_text()); ix = N.index
PAR = json.loads((ROOT / 'scen/3d/klipp2/sam3db/mhr_skelett.json').read_text())['parents']
F = np.diag([1., -1., -1.])
Am = np.array([[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]])        # MHR-modellrum -> MJCF-axlar
# SMPL-kropp -> (MHR-led för rotation, SMPL-barn, MHR-led för barnets riktning)
KARTA = {
    'Pelvis': ('root', None, None),
    'L_Hip': ('l_upleg', 'L_Knee', 'l_lowleg'), 'L_Knee': ('l_lowleg', 'L_Ankle', 'l_foot'), 'L_Ankle': ('l_foot', 'L_Toe', 'l_ball'), 'L_Toe': ('l_ball', None, None),
    'R_Hip': ('r_upleg', 'R_Knee', 'r_lowleg'), 'R_Knee': ('r_lowleg', 'R_Ankle', 'r_foot'), 'R_Ankle': ('r_foot', 'R_Toe', 'r_ball'), 'R_Toe': ('r_ball', None, None),
    # 17 nov: Spine styr bara c_spine1 (->c_spine2), Chest styr c_spine2 (->c_neck); c_spine3 ärver Chest. Förut bar Spine c_spine1..c_spine3 (30 cm mot SMPL:s 6),
    # så en ryggböj i simuleringen flyttade överkroppen 15-19 cm (diagnos_kottbit/). Före: mhr_smpl_fore_ryggfix.py.
    'Torso': ('c_spine0', 'Spine', 'c_spine1'), 'Spine': ('c_spine1', 'Chest', 'c_spine2'), 'Chest': ('c_spine2', 'Neck', 'c_neck'),
    'Neck': ('c_neck', 'Head', 'c_head'), 'Head': ('c_head', None, None),
    'L_Thorax': ('l_clavicle', 'L_Shoulder', 'l_uparm'), 'L_Shoulder': ('l_uparm', 'L_Elbow', 'l_lowarm'), 'L_Elbow': ('l_lowarm', 'L_Wrist', 'l_wrist'),
    'L_Wrist': ('l_wrist', 'L_Hand', 'l_middle1'), 'L_Hand': ('l_wrist', None, None),
    'R_Thorax': ('r_clavicle', 'R_Shoulder', 'r_uparm'), 'R_Shoulder': ('r_uparm', 'R_Elbow', 'r_lowarm'), 'R_Elbow': ('r_lowarm', 'R_Wrist', 'r_wrist'),
    'R_Wrist': ('r_wrist', 'R_Hand', 'r_middle1'), 'R_Hand': ('r_wrist', None, None),
}
ARV_B = {'L_Hand': 'L_Wrist', 'R_Hand': 'R_Wrist'}                   # löv som ärver förälderns B
TILLBAKA = [k for k in KARTA if k not in ('L_Hand', 'R_Hand')]     # SMPL-kroppar som bestämmer en MHR-led


def mjcf():
    namn, foralder, off = [], [], []
    def gå(e, p):
        for b in e.findall('body'):
            namn.append(b.get('name')); foralder.append(p); off.append([float(v) for v in b.get('pos').split()]); gå(b, len(namn) - 1)
    gå(ET.parse(MJCF).getroot().find('worldbody'), -1)
    return namn, np.array(foralder), np.array(off)


SN, SP, SO = mjcf()
def vila_mjcf():
    P = np.zeros((len(SN), 3))
    for i in range(len(SN)): P[i] = (P[SP[i]] if SP[i] >= 0 else 0) + SO[i]
    return P
SV = vila_mjcf()


def minrot(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b); v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-9: return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + vx + vx @ vx / (1 + c)


def gravitation(upp):
    u = upp / np.linalg.norm(upp); return minrot(u, np.array([0., 0., 1.]))


def B_matriser(rest):
    B = {}
    for j, (m, barn, mb) in KARTA.items():
        if barn is None: continue
        o = SO[SN.index(barn)]; d = Am @ (rest[ix(mb), :3] - rest[ix(m), :3]); B[j] = minrot(o, d)
    for j in KARTA:
        if j not in B: B[j] = B[ARV_B[j]] if j in ARV_B else np.eye(3)
    return B


def till_varld(z, V):
    """MHR-sekvens -> världen (meter, z upp): positioner (T,127,3) och rotationer (T,127,3,3), plus Q3, T per ruta."""
    G = gravitation(V['upp']); n = len(z['pose']); P = z['pose'].astype(float)
    Q3 = np.array([G @ V['kam_R'][f] @ F for f in range(n)]); T = np.array([G @ (V['kam_C'][f] + V['kam_R'][f] @ z['cam_t'][f]) for f in range(n)])
    pos = np.einsum('fab,fjb->fja', Q3, P[:, :, :3] / 100.) + T[:, None]
    rot = np.einsum('fab,fjbc->fjac', Q3, Ro.from_quat(P[:, :, 3:7].reshape(-1, 4)).as_matrix().reshape(n, -1, 3, 3))
    return pos, rot, Q3, T


def rensa(z):
    """Index per ruta: osynliga rutor (inom = falskt, utfyllnad före och efter tagningen) tar närmaste synliga ruta."""
    ok = np.nonzero(np.asarray(z['inom'], bool))[0]
    if len(ok) == 0: return np.arange(len(z['inom']))
    return np.array([ok[np.argmin(np.abs(ok - f))] for f in range(len(z['inom']))])


def golv_per_ruta(fotz):
    """Golvet under fötterna per ruta (lägsta fot, utjämnat): läsningens drift i höjd tas bort före modellen och läggs tillbaka efter."""
    from scipy.signal import savgol_filter
    g = fotz.min(1); g = savgol_filter(g, min(31, len(g) // 2 * 2 - 1), 2); return g - g[0]


def langd_mhr(rest): return (rest[ix('c_head'), 1] - min(rest[ix('l_ball'), 1], rest[ix('l_foot'), 1])) / 100.
def langd_smpl(): return SV[SN.index('Head'), 2] - min(SV[SN.index('L_Toe'), 2], SV[SN.index('L_Ankle'), 2])


def till_smpl(z, V):
    """Ger G (T,24,3,3) i MJCF-ordning, rotposition (T,3) i simvärlden, och avbildningen (s, o) för vägen tillbaka."""
    pos, rot, Q3, T = till_varld(z, V); rest = z['rest'].astype(float); Rv = Ro.from_quat(rest[:, 3:7]).as_matrix(); B = B_matriser(rest)
    ri = rensa(z); pos, rot = pos[ri], rot[ri]
    s = langd_smpl() / langd_mhr(rest); fot = np.concatenate([pos[:, ix('l_ball')], pos[:, ix('r_ball')], pos[:, ix('l_foot')], pos[:, ix('r_foot')]])
    o = np.array([pos[0, ix('root'), 0], pos[0, ix('root'), 1], np.percentile(fot[:, 2], 2)])
    n = len(pos); Gm = np.zeros((n, len(SN), 3, 3))
    for j, (m, _, _) in KARTA.items():
        D = rot[:, ix(m)] @ (Am @ Rv[ix(m)]).T; Gm[:, SN.index(j)] = D @ B[j]
    rotpos = s * (pos[:, ix('root')] - o)
    dz = golv_per_ruta(s * (np.stack([pos[:, ix(k), 2] for k in ('l_ball', 'r_ball', 'l_foot', 'r_foot')], 1) - o[2])); rotpos[:, 2] -= dz
    return dict(G=Gm, rot=rotpos, s=s, o=o, B=B, pos_mhr=pos, rotm_mhr=rot, Q3=Q3, T=T, dz=dz, ri=ri)


def fk_smpl(Gm, rotpos):
    """FK i MJCF: kroppspositioner (T,24,3) ur globala rotationer och rotens position."""
    n = len(Gm); P = np.zeros((n, len(SN), 3)); P[:, 0] = rotpos
    for i in range(1, len(SN)): P[:, i] = P[:, SP[i]] + np.einsum('fab,b->fa', Gm[:, SP[i]], SO[i])
    return P


def fran_smpl(Gs, rot_sim, ut, z):
    """Simulerade SMPL-kroppar (globala rotationer, rotposition i simvärlden) -> ny MHR-pose (modellrum) och T (modellorigo i världen).
    cam_t ur T: cam_t = Rw^T (G^T T - C)."""
    rest = z['rest'].astype(float); Rv = Ro.from_quat(rest[:, 3:7]).as_matrix(); B, s, o, Q3, T = ut['B'], ut['s'], ut['o'], ut['Q3'], ut['T']
    pos0, rot0 = ut['pos_mhr'], ut['rotm_mhr']; n = len(Gs)
    rotn = rot0.copy(); satt = np.zeros(len(N), bool)
    for j in TILLBAKA:
        m = KARTA[j][0]; rotn[:, ix(m)] = Gs[:, SN.index(j)] @ B[j].T @ Am @ Rv[ix(m)]; satt[ix(m)] = True
    rs = rot_sim.copy(); rs[:, 2] += ut.get('dz', 0)
    posn = pos0.copy(); posn[:, ix('root')] = rs / s + o
    for i in range(len(N)):
        p = PAR[i]
        if p < 0 or i == ix('root'): continue
        if not satt[i]: rotn[:, i] = rotn[:, p] @ np.transpose(rot0[:, p], (0, 2, 1)) @ rot0[:, i]
        if i != ix('root'): posn[:, i] = posn[:, p] + np.einsum('fab,fb->fa', rotn[:, p] @ np.transpose(rot0[:, p], (0, 2, 1)), pos0[:, i] - pos0[:, p])
    # tillbaka till modellrummet: roten bär cam_t, posen ligger runt roten
    Qt = np.transpose(Q3, (0, 2, 1)); Tn = T + (posn[:, ix('root')] - pos0[:, ix('root')])     # modellrummets origo flyttas med roten
    P = z['pose'].astype(float).copy()
    P[:, :, :3] = np.einsum('fab,fjb->fja', Qt, posn - Tn[:, None]) * 100.
    P[:, :, 3:7] = Ro.from_matrix(np.einsum('fab,fjbc->fjac', Qt, rotn).reshape(-1, 3, 3)).as_quat().reshape(n, -1, 4)
    return P, Tn
