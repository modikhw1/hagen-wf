"""0040: Kimodo-utfall (somaskel30, lokala rotationer och rot i Kimodos värld) -> MHR-sekvens, plan för förvärlden och mått (som 0039).

  scen/.venv/Scripts/python.exe forvarld/kropp/kimodo/efter_kimodo.py <raw.npz> <variant> <frö> <ut-namn>
"""
import json, sys
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parent; KR = HIT.parent; ROOT = HIT.parents[2]
sys.path.insert(0, str(HIT)); sys.path.insert(0, str(KR / 'forskning/mm'))
import mhr_soma as K
import mhr_smpl as MS
import efter_mm as E


def main():
    raw, var, fro, namn = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    z = dict(np.load(E.SEK)); V = np.load(E.VAR); d = np.load(raw); u = K.till_soma(z, V)
    lok = d[f'{var}__{fro}__lok'].astype(float); rot = d[f'{var}__{fro}__rot'].astype(float); n = len(lok)
    G = lok.copy()
    for i in range(1, len(K.SN)): G[:, i] = G[:, K.SP[i]] @ lok[:, i]
    P, T = K.fran_soma(G, rot, u, z)
    Gr = MS.gravitation(V['upp']); cam_t = np.array([V['kam_R'][f].T @ (Gr.T @ T[f] - V['kam_C'][f]) for f in range(n)])
    ut = HIT / 'ut'; zz = dict(z); zz['pose'] = P.astype(z['pose'].dtype); zz['cam_t'] = cam_t.astype(z['cam_t'].dtype); np.savez(ut / f'sek_{namn}.npz', **zz)
    pl = json.loads((KR / 'ut/plan/efter.json').read_text(encoding='utf-8'))
    s = json.dumps(pl, ensure_ascii=False).replace(json.dumps(str(KR / 'ut/sekvens_andra_handen.npz'))[1:-1], json.dumps(str(ut / f'sek_{namn}.npz'))[1:-1]); pl = json.loads(s)
    pl['licens'] = 'nvidia-open-model-license'; pl.setdefault('anteckningar', []).append(f'0040: kroppen ur Kimodo-SOMA-RP-v1.1 ({var}, frö {fro}); vikter NVIDIA Open Model License.')
    (ut / 'plan').mkdir(parents=True, exist_ok=True); (ut / 'plan' / f'{namn}.json').write_text(json.dumps(pl, ensure_ascii=False, indent=1), encoding='utf-8')
    m = dict(namn=namn, variant=var, fro=int(fro), generering_s=float(d[f'{var}__sekunder']), **E.matt(z, V, P, cam_t)); print(json.dumps(m, ensure_ascii=False))
    (ut / f'matt_{namn}.json').write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__': main()
