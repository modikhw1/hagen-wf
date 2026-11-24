"""Diagnos köttbit: ryggsegmentens längder i SMPL (MJCF) mot MHR (vila, cm), och vad sim-Spine-ΔR (≈30° framåt) gör med MHR:s c_spine1->c_spine3."""
import sys, json
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HIT)); sys.dont_write_bytecode = True
import mhr_smpl as M, tagning as TG
from scipy.spatial.transform import Rotation as Ro
ix = M.ix; SO, SN = M.SO, M.SN
print('SMPL offset (cm): Pelvis->Torso', round(np.linalg.norm(SO[SN.index('Torso')]) * 100, 1), 'Torso->Spine', round(np.linalg.norm(SO[SN.index('Spine')]) * 100, 1),
      'Spine->Chest', round(np.linalg.norm(SO[SN.index('Chest')]) * 100, 1), 'Chest->Neck', round(np.linalg.norm(SO[SN.index('Neck')]) * 100, 1))
namn = sys.argv[1] if len(sys.argv) > 1 else 'trofe2'
L = json.loads((HIT / 'ut' / f'mening_{namn}' / 'logg.json').read_text(encoding='utf-8')); t = TG.las(L['kalla'], L['liggare'], L['scen'], L['person'])
r = t['z']['rest'][:, :3].astype(float)
for a, b in (('root', 'c_spine0'), ('c_spine0', 'c_spine1'), ('c_spine1', 'c_spine2'), ('c_spine2', 'c_spine3'), ('c_spine3', 'c_neck')):
    print(f'MHR {a}->{b}: {np.linalg.norm(r[ix(b)] - r[ix(a)]):.1f} cm')
ref = TG.referens(t); u = ref['u']; P, q, k, _ = TG.las_utfall(HIT / 'ut' / f'mening_{namn}' / 'mm.npz', ref['S'])
Gs = Ro.from_quat(q.reshape(-1, 4)).as_matrix().reshape(k, -1, 3, 3); G0 = u['G'][1:k + 1]; p0 = u['pos_mhr'][1:k + 1]
dR = np.einsum('fab,fcb->fac', Gs[:, SN.index('Spine')], G0[:, SN.index('Spine')]); off = p0[:, ix('c_spine3')] - p0[:, ix('c_spine1')]
print(f'{namn}: förskjutning av c_spine3 av enbart Spine-ΔR över c_spine1->c_spine3 (cm, världen):', ((np.einsum('fab,fb->fa', dR, off) - off).mean(0) * 100).round(1))
offS = np.einsum('fab,b->fa', G0[:, SN.index('Spine')], SO[SN.index('Chest')]); print('   samma ΔR över SMPL Spine->Chest:', ((np.einsum('fab,fb->fa', dR, offS) - offS).mean(0) * 100).round(1))
