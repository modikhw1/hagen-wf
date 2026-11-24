"""Diagnos köttbit: MHR-sekvensen (sekvens.npz, före riggen) mot originalets, i världen (till_varld): leder relativt roten, cm, medel över tagningen.
Visar om förskjutningen redan finns i sekvensen eller uppstår i riggen. Även samma sak för simulatorns SMPL-kroppar (mm.npz) relativt Pelvis.
  scen/.venv/Scripts/python.exe -X utf8 diagnos_kottbit/sekvens_jamfor.py trofe2 ..."""
import sys, json
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HIT)); sys.dont_write_bytecode = True
import mhr_smpl as M, tagning as TG
ix = M.ix
for namn in sys.argv[1:]:
    L = json.loads((HIT / 'ut' / f'mening_{namn}' / 'logg.json').read_text(encoding='utf-8'))
    t = TG.las(L['kalla'], L['liggare'], L['scen'], L['person']); z0 = t['z']; z1 = dict(np.load(HIT / 'ut' / f'mening_{namn}' / 'sekvens.npz'))
    p0 = M.till_varld(z0, t['V'])[0]; p1 = M.till_varld(z1, t['V'])[0]; ok = np.asarray(z0['inom'], bool)
    print(f'== {namn} ({ok.sum()} synliga rutor av {len(ok)})')
    for j in ('c_spine3', 'c_head', 'r_lowarm', 'r_wrist', 'l_wrist'):
        d = ((p1[:, ix(j)] - p1[:, ix('root')]) - (p0[:, ix(j)] - p0[:, ix('root')]))[ok] * 100
        print(f'  {j:9s} sekvens−original rel. rot (x,y,z cm) {d.mean(0).round(1)}   |Δ| max {np.linalg.norm(d, axis=1).max():.1f}')
    u = M.till_smpl(z0, t['V']); print(f"  skala s = {u['s']:.3f}")
