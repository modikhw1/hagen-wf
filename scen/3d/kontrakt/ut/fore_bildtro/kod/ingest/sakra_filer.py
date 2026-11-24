"""Spara original före ändring; invalidation arkiverar och raderar aldrig data."""
import shutil
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]
BACKUP = ROT / 'scen/3d/kontrakt/ut/fore_regler'


def sakerhetskopiera(p):
    p = Path(p).resolve()
    if not p.exists(): return
    try: rel = p.relative_to(ROT)
    except ValueError: raise ValueError('Skrivning utanför projektet: ' + str(p))
    mal = BACKUP / rel
    if mal.exists(): return
    mal.parent.mkdir(parents=True, exist_ok=True)
    if p.is_dir(): shutil.copytree(p, mal)
    else: shutil.copy2(p, mal)


def arkivera(p):
    p = Path(p).resolve()
    if not p.exists(): return
    sakerhetskopiera(p)
    # Behåll även senare körningar. Inget raderas vid invalidation.
    mal = BACKUP / 'senare' / p.relative_to(ROT)
    mal.parent.mkdir(parents=True, exist_ok=True)
    nr = 1
    while mal.exists():
        mal = mal.with_name(p.name + '.' + str(nr)); nr += 1
    p.rename(mal)
