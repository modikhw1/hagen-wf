"""Lokalt arbetsstöd: säkerhetskopia och bevarade radslut."""
import json
import shutil
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]
UT = Path(__file__).resolve().parent / 'ut/fore_text'


def backup(p):
    p = Path(p).resolve()
    if p.exists():
        target = UT / p.relative_to(ROT)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)


def spara(p, text):
    p = Path(p)
    backup(p)
    old = p.read_bytes() if p.exists() else b''
    newline = b'\r\n' if b'\r\n' in old else b'\n'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.replace('\r\n', '\n').replace('\n', newline.decode()).encode('utf-8'))


def jsonfil(p, data):
    spara(p, json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def byt(p, old, new):
    p = Path(p)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise ValueError(f'Söktext saknas i {p}: {old[:100]}')
    spara(p, text.replace(old, new))
