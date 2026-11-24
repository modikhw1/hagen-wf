"""Säkerhetskopiera och bevara radslut i återupptagningen av steg 10."""
import shutil
from pathlib import Path

ROT = Path(__file__).resolve().parents[4]
BACKUP = ROT / 'scen/3d/kontrakt/ut/fore_prop'


def andra(rel, fn):
    p = ROT / rel
    b = p.read_bytes()
    for dest in (BACKUP / rel, BACKUP / 'aterupptagning_20261110' / rel):
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
    nl = '\r\n' if b'\r\n' in b else '\n'
    text = fn(b.decode('utf-8').replace('\r\n', '\n'))
    p.write_bytes(text.replace('\r\n', '\n').replace('\n', nl).encode('utf-8'))
