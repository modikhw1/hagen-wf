"""Named body-data boundary. All consumers use the same plan/raw snapshot.

This module never imports or runs the ingest/contract pipeline. A fresh full
export must receive a matching finished plan.json + scen.blend from that pipeline.
"""
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PACKAGE = OUT / 'paket/notan'
BODY_PLAN = ROOT / 'scen/3d/kontrakt/ut/notan/jamn_tom/plan.json'
BODY_BLEND = BODY_PLAN.with_name('scen.blend')
BODY_RIG = ROOT / 'scen/3d/kontrakt/tro_rigg.json'

def body_rig_names():
    return json.loads(BODY_RIG.read_text(encoding='utf-8'))['namn'][1:]

def load_body_source(reuse_raw=True):
    """Read frozen package plan, or the finished upstream plan for full export."""
    path = PACKAGE / 'plan.json' if reuse_raw else BODY_PLAN
    return json.loads(path.read_text(encoding='utf-8'))

def read_body_raw(stem):
    """Only entry point for the Blender-extracted body arrays."""
    path = PACKAGE / f'{stem}-raw.npz'
    if not path.exists():
        path = OUT / 'intermediat' / f'{stem}-raw.npz'
    with np.load(path) as raw:
        return {name: raw[name] for name in raw.files}

def body_dependencies(plan):
    """Explicit upstream files referenced by this plan, for rebuild auditing."""
    files = {str(BODY_PLAN), str(BODY_BLEND), str(BODY_RIG)}
    for scene in plan['scener']:
        files.add(scene['varld'])
        folder = Path(scene['varld']).parent
        files.update(str(folder / name) for name in ('masker.npy', 'personer.json'))
        files.update(person['rorelse'] for person in scene['personer'])
    return sorted(files)
