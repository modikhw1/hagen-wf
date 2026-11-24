"""Jutsu adapter: estimate noise from measured samples at their actual cadence."""
import math
import runpy
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
INGEST = ROOT / 'scen/3d/ingest'
sys.path.insert(0, str(INGEST))
import sekvens_jamn as J


def brus_sigma(Y, w, d=3):
    Y = np.asarray(Y, float)
    valid = np.flatnonzero(np.asarray(w) > 0)
    if len(valid) < d + 3:
        return np.full(Y.shape[1], np.nan)
    gaps, counts = np.unique(np.diff(valid), return_counts=True)
    stride = int(gaps[np.argmax(counts)])
    starts = np.arange(max(0, len(Y) - d * stride))
    groups = starts[:, None] + stride * np.arange(d + 1)
    groups = groups[np.all(np.asarray(w)[groups] > 0, axis=1)]
    if len(groups) < 3:
        return np.full(Y.shape[1], np.nan)
    residual = np.diff(Y[groups], n=d, axis=1)[:, 0, :]
    return 1.4826 * np.median(np.abs(residual - np.median(residual, axis=0)), axis=0) / math.sqrt(math.comb(2*d, d))


if __name__ == '__main__':
    J.brus_sigma = brus_sigma
    runpy.run_path(str(INGEST / 'sekvens_stabil.py'), run_name='__main__')
