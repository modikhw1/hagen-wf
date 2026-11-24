"""FORSKNING: jämför råfiler mot en referens. python jamfor.py <ref.npz> <raw_namn> [...]  (namn utan raw_ och .npz, i ut/)"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import mhr_smpl as M
U = Path(__file__).resolve().parent / 'ut'; ix = M.SN.index
r = dict(np.load(sys.argv[1], allow_pickle=True)); S = M.fk_smpl(r['G'].astype(float), r['rot'].astype(float))
print(f"{'namn':14s} rot  alla  bäck huvud hHand vHand | hHand skopa ge | huvud skopa | fotväg | ryck hHand bäcken")
for n in sys.argv[2:]:
    d = dict(np.load(U / f'raw_{n}.npz', allow_pickle=True)); P = d['pos'].astype(float) - d['skift'][None, None]; k = min(len(P), len(S) - 1); P = P[:k]; R = S[1:1 + k]; P = P - np.r_[(P[0, 0] - R[0, 0])[:2], 0.]
    e = lambda b, a=0, c=None: float(np.median(np.linalg.norm(P[a:c, ix(b)] - R[a:c, ix(b)], axis=1))) * 100
    ry = lambda b: float(np.median(np.linalg.norm(np.diff(P[:, ix(b)], 3, axis=0), axis=1))) * 30 ** 3
    fv = sum(float(np.linalg.norm(np.diff(P[:, ix(f), :2], axis=0), axis=1).sum()) for f in ('L_Ankle', 'R_Ankle')) * 50
    print(f"{n:14s} {P[:, 0, 2].min():.2f} {np.linalg.norm(P - R, axis=-1).mean() * 100:5.1f} {e('Pelvis'):5.1f} {e('Head'):5.1f} {e('R_Hand'):5.1f} {e('L_Hand'):5.1f} | {e('R_Hand', 28, 66):10.1f} {e('R_Hand', 90, 146):5.1f} | {e('Head', 28, 66):8.1f} | {fv:6.0f} | {ry('R_Hand'):6.0f} {ry('Pelvis'):6.0f}")
