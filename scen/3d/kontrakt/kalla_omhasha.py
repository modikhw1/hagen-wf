"""Skriv en kopia av en kalla.json där alla filpekares sha256 räknas om mot filerna som de pekar på nu.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_omhasha.py <in kalla.json> <ut kalla.json>

Behövs efter att ingest-filer (sekvens, varld) skrivits om med ny utjämning (10 nov, jämn-passet). Utfilen måste ligga i samma mapp som infilen,
eftersom sökvägarna är relativa. Inget annat ändras; en befintlig utfil skrivs aldrig över. Hashen för en pekare vars fil saknas lämnas orörd och skrivs ut.
"""
import argparse
import datetime
import hashlib
import json
import shutil
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
    skydda_handelser(k, ändrade)
    utf.write_text(json.dumps(k, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return ändrade, saknade


def skydda_handelser(k, ändrade):
    if any(p['sokvag'] in ändrade for p in k['matning'].get('handelsekallor', [])):
        raise ValueError('Händelseunderlaget har ändrats. Kör kalla_handelser.py igen från en aktuell kalla_prop.json; gamla händelser får inte bara hashas om.')


def uppdatera(inf):
    """Uttrycklig manifestuppdatering, med original och revisionslogg bevarade.

    Semantiken ändras inte, därför behålls dess revision och regins bindning.
    Ny semantik eller ändrad tidsbas ska byggas om, inte omhashas.
    """
    inf = Path(inf).resolve()
    root = Path(__file__).resolve().parents[3]
    rel = inf.relative_to(root)
    original = inf.read_bytes()
    k = json.loads(original.decode('utf-8'))
    ändrade, saknade = [], []
    omhasha(k, inf.parent, ändrade, saknade)
    skydda_handelser(k, ändrade)
    if saknade:
        raise FileNotFoundError('Mätfiler saknas: ' + ', '.join(saknade))
    if not ändrade:
        return [], []
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup = Path(__file__).resolve().parent / 'ut/fore_prop' / ('omhashning_' + stamp) / rel
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(inf, backup)
    nl = '\r\n' if b'\r\n' in original else '\n'
    data = (json.dumps(k, ensure_ascii=False, indent=2) + '\n').replace('\n', nl).encode('utf-8')
    log = inf.with_name(inf.name + '.omhashning.json')
    records = json.loads(log.read_text(encoding='utf-8')) if log.exists() else []
    records.append(dict(tid=stamp, före_sha256=hashlib.sha256(original).hexdigest(),
                        efter_sha256=hashlib.sha256(data).hexdigest(), backup=str(backup),
                        ändrade=ändrade, revision=k['revision'],
                        skäl='Uttrycklig uppdatering efter lokal ingest; semantik och video oförändrade.'))
    if log.exists():
        shutil.copy2(log, backup.with_name(log.name))
    temp = inf.with_name(inf.name + '.omhashning.tmp')
    if temp.exists():
        raise FileExistsError(temp)
    temp.write_bytes(data)
    temp.replace(inf)
    log.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return ändrade, saknade


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kalla'); p.add_argument('ut', nargs='?')
    p.add_argument('--uppdatera', action='store_true', help='Uppdatera indata uttryckligen, med säkerhetskopia och logg.')
    args = p.parse_args()
    if args.uppdatera and args.ut: p.error('Ange inte utfil med --uppdatera.')
    if not args.uppdatera and not args.ut: p.error('Ange utfil eller --uppdatera.')
    a, s = uppdatera(args.kalla) if args.uppdatera else main(args.kalla, args.ut)
    print(len(a), 'hashar ändrade,', len(s), 'pekare saknar fil')
    for x in s: print('  saknas:', x)
