"""Skriv en kopia av en kalla.json där alla filpekares sha256 räknas om mot filerna som de pekar på nu.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_omhasha.py <in kalla.json> <ut kalla.json>

Behövs efter att ingest-filer (sekvens, varld) skrivits om med ny utjämning (10 nov, jämn-passet). Utfilen måste ligga i samma mapp som infilen,
eftersom sökvägarna är relativa. Inget annat ändras; en befintlig utfil skrivs aldrig över. Hashen för en pekare vars fil saknas lämnas orörd och skrivs ut.
"""
import hashlib
import json
import sys
from pathlib import Path


def omhasha(o, bas, ändrade, saknade):
    if isinstance(o, dict):
        if 'sokvag' in o and 'sha256' in o and isinstance(o['sokvag'], str):
            p = (bas / o['sokvag']).resolve()
            if p.is_file():
                h = hashlib.sha256(p.read_bytes()).hexdigest()
                if h != o['sha256']: ändrade.append(o['sokvag']); o['sha256'] = h
            else: saknade.append(o['sokvag'])
        for v in o.values(): omhasha(v, bas, ändrade, saknade)
    elif isinstance(o, list):
        for v in o: omhasha(v, bas, ändrade, saknade)


def main(inf, utf):
    inf, utf = Path(inf).resolve(), Path(utf).resolve()
    if utf.exists(): raise FileExistsError(utf)
    if inf.parent != utf.parent: raise ValueError('Utfilen måste ligga i samma mapp som infilen.')
    k = json.loads(inf.read_text(encoding='utf-8')); ändrade, saknade = [], []
    omhasha(k, inf.parent, ändrade, saknade)
    utf.write_text(json.dumps(k, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return ändrade, saknade


if __name__ == '__main__':
    a, s = main(sys.argv[1], sys.argv[2]); print(len(a), 'hashar ändrade,', len(s), 'pekare saknar fil'); [print('  saknas:', x) for x in s]
