"""FORSKNING (0039): MaskedMimic-utfall (SMPL-kroppar per steg) -> MHR-sekvens, plan för förvärlden, och mått.

  scen/.venv/Scripts/python.exe forvarld/kropp/forskning/mm/efter_mm.py <mm.npz> <ut-namn>
Ger forvarld/kropp/forskning/mm/ut/<ut-namn>.npz (sekvens), ut/plan/<ut-namn>.json (plan, licens: forskning) och ut/matt_<ut-namn>.json.
Mått (samma som 0034/0036) plus mjukhet: ryck (tredje derivatan, m/s³, median) i händer och bål, och fotglidning (cm per ruta när foten står).
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Ro
HIT = Path(__file__).resolve().parent; KR = HIT.parents[1]; ROOT = HIT.parents[3]
sys.path.insert(0, str(HIT)); sys.path.insert(0, str(KR))
import mhr_smpl as M
import prov_optimering as O
import bank_bygg as B

SEK = ROOT / 'scen/3d/gennedbrytning/g_forvarld/dreamina_t_rot/sekvens_1.npz'; VAR = ROOT / 'scen/3d/ingest/ut/kand-kennysgelato-tagningar/S1/varld.npz'
FPS = 29.97; ix = M.ix


def tillbaka(mm, z, V):
    u = M.till_smpl(z, V); d = dict(np.load(mm, allow_pickle=True)); n = len(z['pose'])
    pos, rot = d['pos'].astype(float), d['rot'].astype(float); k = len(pos)
    Gs = Ro.from_quat(rot.reshape(-1, 4)).as_matrix().reshape(k, -1, 3, 3)          # xyzw (w sist, som ProtoMotions)
    rs = pos[:, 0] - d['skift'][None]                                               # samma golv som referensen
    off = np.r_[(rs[0] - u['rot'][1])[:2], 0.]; rs = rs - off                       # miljöns förskjutning i xy (rapporteras)
    G = np.concatenate([u['G'][:1], Gs, np.repeat(Gs[-1:], n - 1 - k, 0)])[:n]; R = np.concatenate([u['rot'][:1], rs, np.repeat(rs[-1:], n - 1 - k, 0)])[:n]
    P, T = M.fran_smpl(G, R, u, z)
    Gr = M.gravitation(V['upp']); cam_t = np.array([V['kam_R'][f].T @ (Gr.T @ T[f] - V['kam_C'][f]) for f in range(n)])
    return P, cam_t, dict(steg=k, forskjutning_xy_m=off[:2].round(3).tolist())


def matt(z, V, P, cam_t):
    zz = {**z, 'pose': P, 'cam_t': cam_t}; pos, rot, _, _ = M.till_varld(zz, V); pos0, rot0, _, _ = M.till_varld(z, V)
    mal = z['pose'][:, ix('r_wrist'), :3].astype(float); D = B.D_led(z['rest']); vila = B.spegla(z['pose'].astype(float), D)[:, ix('r_wrist'), :3]
    w = np.array([O.vikt(f) for f in range(len(P))]); fon = dict(skopa=(28, 66), ge=(90, 146))
    def med(x, a, b): return round(float(np.median(x[a:b][w[a:b] == 1])), 1)
    dv = np.linalg.norm(P[:, ix('l_wrist'), :3] - mal, axis=1)
    bal = np.degrees([Ro.from_matrix(rot[f, ix('c_spine3')] @ rot0[f, ix('c_spine3')].T).magnitude() for f in range(len(P))])
    ab = np.array([O.armbage(P[f], O.LUP, O.LLOW, ix('l_wrist')) for f in range(len(P))])
    hv = np.linalg.norm(P[:, ix('r_wrist'), :3] - vila, axis=1)
    ryck = lambda j: round(float(np.median(np.linalg.norm(np.diff(pos[:, ix(j)], 3, axis=0), axis=1)) * FPS ** 3), 1)
    def glid(fot):
        p = pos[:, ix(fot)]; h = p[:, 2] - np.percentile(p[:, 2], 5); v = np.linalg.norm(np.diff(p[:, :2], axis=0), axis=1) * 100; st = h[1:] < 0.03
        return round(float(v[st].mean()), 2) if st.any() else None
    return dict(vanster_hand_till_mal_cm={k: med(dv, *v) for k, v in fon.items()}, bal_rotation_mot_original_grader={k: med(bal, *v) for k, v in fon.items()},
                vanster_armbage_grader={k: med(ab, *v) for k, v in fon.items()}, hoger_hand_mot_speglad_vila_cm={k: med(hv, *v) for k, v in fon.items()},
                ryck_m_per_s3=dict(vanster_handled=ryck('l_wrist'), hoger_handled=ryck('r_wrist'), bal=ryck('c_spine3')),
                fotglidning_cm_per_ruta=dict(vanster=glid('l_ball'), hoger=glid('r_ball')),
                rotens_forflyttning_cm=round(float(np.linalg.norm(pos[-1, ix('root'), :2] - pos[0, ix('root'), :2]) * 100), 1))


def main():
    z = dict(np.load(SEK)); V = np.load(VAR); namn = sys.argv[2]; ut = HIT / 'ut'
    if sys.argv[1] in ('original', '0034'):
        P = z['pose'].astype(float) if sys.argv[1] == 'original' else np.load(KR / 'ut/sekvens_andra_handen.npz')['pose'].astype(float); cam_t = z['cam_t']; info = {}
    else:
        P, cam_t, info = tillbaka(sys.argv[1], z, V)
        zz = dict(z); zz['pose'] = P.astype(z['pose'].dtype); zz['cam_t'] = cam_t.astype(z['cam_t'].dtype); np.savez(ut / f'sek_{namn}.npz', **zz)
        pl = json.loads((KR / 'ut/plan/efter.json').read_text(encoding='utf-8'))
        s = json.dumps(pl, ensure_ascii=False).replace(json.dumps(str(KR / 'ut/sekvens_andra_handen.npz'))[1:-1], json.dumps(str(ut / f'sek_{namn}.npz'))[1:-1]); pl = json.loads(s)
        pl['licens'] = 'forskning'; pl.setdefault('anteckningar', []).append('0039: FORSKNING. Kroppen ur MaskedMimic SMPL (ProtoMotions v3.0, AMASS-tränad, icke-kommersiell).')
        (ut / 'plan').mkdir(parents=True, exist_ok=True); (ut / 'plan' / f'{namn}.json').write_text(json.dumps(pl, ensure_ascii=False, indent=1), encoding='utf-8')
    m = dict(namn=namn, **info, **matt(z, V, P, cam_t)); print(json.dumps(m, ensure_ascii=False))
    (ut / f'matt_{namn}.json').write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__': main()
