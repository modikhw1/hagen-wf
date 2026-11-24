"""Säkerhetskopiering för GOLV2. Körs från projektroten."""
from pathlib import Path
import shutil
ROOT = Path(__file__).resolve().parents[4]
BACK = ROOT / 'scen/3d/kontrakt/ut/fore_golv2'
def backup(file):
    p = Path(file).resolve()
    dest = BACK / p.relative_to(ROOT)
    if p.exists() and not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    return p
def write(file, text):
    p = backup(file)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')
