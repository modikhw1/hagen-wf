"""S?kerhetskopior och of?r?ndrade radslut f?r steg 10c."""
from pathlib import Path
import shutil
ROT = Path(__file__).resolve().parents[4]
BACKUP = ROT / 'scen/3d/kontrakt/ut/fore_steg10c'
def andra(rel, fn):
    p = ROT / rel
    b = p.read_bytes()
    dest = BACKUP / rel
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    nl = '\r\n' if b'\r\n' in b else '\n'
    s = fn(b.decode('utf-8').replace('\r\n', '\n'))
    p.write_bytes(s.replace('\r\n', '\n').replace('\n', nl).encode('utf-8'))
def logg(text):
    p = ROT / 'scen/3d/kontrakt/STEG10C-LOGG.md'
    andra(str(p.relative_to(ROT)), lambda s: s + '\n' + text + '\n')
