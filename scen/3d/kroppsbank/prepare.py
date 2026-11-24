"""Small read-only input inventory. Run from workspace root, with -B."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
shots = []
for group, name, ident in [('notan-tagningar', 'S1', 'notan-S1'),
                            ('notan-tagningar', 'S4', 'notan-S4'),
                            ('b-tilltal-ravara-tagningar', 'S5', 'ravara-S5'),
                            ('b-tilltal-ravara-tagningar', 'S9', 'ravara-S9')]:
    folder = Path('scen/3d/ingest/ut') / group / name
    meta = json.loads((folder / 'meta.json').read_text(encoding='utf-8'))
    pids = [p.stem.split('_')[1] for p in sorted(folder.glob('sekvens_*.npz'))]
    first = next((folder / 'kropp' / pids[0]).glob('*.npz'))
    with np.load(first) as z:
        focal = float(z['focal_length'])
    w, h = meta['bredd'], meta['hojd']
    video = folder.parent / 'klipp' / f'{name}.mp4'
    sources = [video, folder / 'meta.json', folder / 'personer.json',
               folder / 'masker.npy', folder / 'tider.json', folder / 'varld.npz']
    sources += list(folder.glob('sekvens_*.npz'))
    sources += list((folder / 'kropp').glob('*/*.npz'))
    hashes = {str(p).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    shots.append({'id': ident, 'folder': folder.as_posix(), 'video': video.as_posix(),
                  'pids': pids, 'meta': meta, 'K': [[focal, 0, w/2], [0, focal, h/2], [0, 0, 1]],
                  'source_sha256': hashes})
(ROOT / 'manifest.json').write_text(json.dumps({'shots': shots}, ensure_ascii=False, indent=2), encoding='utf-8')
print([(s['id'], s['meta']['N'], s['pids'], s['K'][0][0]) for s in shots])
