"""T3: kort, lokal känslighetskontroll; skriver endast bredvid denna fil.

Återanvänder T2:s inläsning och typtest, men kör aldrig dess skrivande slutdel.
Ingen video avkodas och inga modeller eller nätverk anropas.
"""
import json
import time
from pathlib import Path
import numpy as np

start = time.monotonic()
here = Path(__file__).resolve().parent
source = here.parent / 'T2-tolkning' / 'diagnos_modellfri.py'
prefix = source.read_text(encoding='utf-8').split('\nres = ', 1)[0]
assert 'write_text' not in prefix
ns = {'__file__': str(source)}
exec(compile(prefix, str(source), 'exec'), ns)
X, keep, groups = ns['X'], ns['behall'], ns['G']
y, g = ns['Y'][keep], groups[keep]

def rank_average(A):
    R = np.empty_like(A, dtype=float)
    for j in range(A.shape[1]):
        _, inv, count = np.unique(A[:, j], return_inverse=True, return_counts=True)
        end = np.cumsum(count)
        R[:, j] = (end - (count + 1) / 2)[inv]
    return (R - R.mean(0)) / (R.std(0) + 1e-9)

def metrics(F):
    D = ((F[:, None, :] - F[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(D, np.inf)
    account = float((g[D.argmin(1)] == g).mean())
    return {'konto': account, 'typ': ns['knn_konto_ut'](F, y, g)}

original = metrics(ns['Xz'][keep])
average = metrics(rank_average(X)[keep])
tie_info = []
for j, name in enumerate(ns['NAMN_MF']):
    _, counts = np.unique(X[:, j], return_counts=True)
    tie_info.append({'matt': name, 'unika': len(counts),
                     'andel_i_lika_grupper': float(counts[counts > 1].sum() / len(X)),
                     'storsta_grupp': int(counts.max())})

rng = np.random.default_rng(20261121)
shuffles = []
for trial in range(10):
    if time.monotonic() - start > 90:
        break
    order = rng.permutation(len(X))
    F = np.empty_like(X, dtype=float)
    F[order] = ns['rangz'](X[order])
    shuffles.append(metrics(F[keep]))

result = {
    'n_fore_typfilter': len(X), 'n_efter_typfilter': int(keep.sum()),
    'ursprunglig': original, 'medelrang_vid_lika_varden': average,
    'endast_omordnade_rader': shuffles,
    'radgrannar_samma_konto': float((groups[1:] == groups[:-1]).mean()),
    'lika_varden': tie_info,
    'sekunder': round(time.monotonic() - start, 3),
    'begransning': 'Känslighetskontroll, inte oberoende testdata eller kausal förklaring.'
}
(here / 'robusthet.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'lika_varden'}, ensure_ascii=False, indent=2))
