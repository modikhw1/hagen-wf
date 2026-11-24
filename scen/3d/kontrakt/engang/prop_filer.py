"""Säkerhetskopiering för det lokala prop-arbetet, med bevarade radslut."""
import shutil
from pathlib import Path

ROT = Path(__file__).resolve().parents[4]
BACKUP = ROT / 'scen/3d/kontrakt/ut/fore_prop'

def andra(rel, fn):
    p = ROT / rel
    b = p.read_bytes()
    mal = BACKUP / rel
    if not mal.exists():
        mal.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, mal)
    nl = '\r\n' if b'\r\n' in b else '\n'
    s = b.decode('utf-8').replace('\r\n', '\n')
    p.write_bytes(fn(s).replace('\r\n', '\n').replace('\n', nl).encode('utf-8'))
