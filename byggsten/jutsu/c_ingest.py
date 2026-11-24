"""Resume C's cached ingest with the sparse-sampling sequence adapter only."""
import subprocess
import sys
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scen/3d/ingest'))
import ingest_klipp as ingest


def knee_visibility(out, meta, pid):
    tracks = json.loads((out / 'personer.json').read_text())
    mask = np.load(out / 'masker.npy')
    scale = meta['bredd'] / mask.shape[2]
    result = {}
    for path in (out / 'kropp' / pid).glob('*.npz'):
        frame = int(path.stem)
        box = tracks[pid].get(str(frame))
        knees = np.load(path)['pred_keypoints_2d'][11:13]
        result[str(frame)] = bool(box is not None and any(
            0 <= x < meta['bredd'] and 0 <= y < meta['hojd']
            and box[0] <= x <= box[2] and box[1] <= y <= box[3]
            and mask[frame, int(y / scale), int(x / scale)] for x, y in knees))
    return result


def main():
    rebuild = '--rebuild-sequences' in sys.argv
    out = HERE / 'ut/c-sketch-tre/ingest'
    if not (out / 'kropp/timing.json').exists():
        raise SystemExit('Cached body results required; this adapter must not launch a GPU job.')
    original_run = subprocess.run
    original_reliability = ingest.palitlighet

    def reliability(out, meta, pid):
        values = original_reliability(out, meta, pid)
        if pid == '2':
            for frame in (411, 414, 417):
                values[str(frame)] = False
        return values

    def run(command, *args, **kwargs):
        if isinstance(command, list) and len(command) > 1 and Path(command[1]).resolve() == (ingest.HIT / 'sekvens_stabil.py').resolve():
            command = list(command)
            command[1] = str(HERE / 'c_sekvens.py')
        return original_run(command, *args, **kwargs)

    sys.argv = [str(ingest.HIT / 'ingest_klipp.py'), str(ROOT / 'scen/klipp/c-sketch-tre.mp4'), str(out), '--personer', '3', '--steg', '3', '--till', 'golv']
    if rebuild:
        sys.argv += ['--om', 'sekvens']
    with patch.object(ingest.subprocess, 'run', run), patch.object(ingest, 'synlighet', knee_visibility), patch.object(ingest, 'palitlighet', reliability):
        ingest.main()


if __name__ == '__main__':
    main()
