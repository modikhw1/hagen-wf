"""Tydlig varning när en lokal ingestomkörning lämnar källmanifest inaktuella."""
import hashlib
import json
import sys
from pathlib import Path


def inaktuella(kallfil, ut, cache=None):
    cache = {} if cache is None else cache
    path = Path(kallfil).resolve(); ut = Path(ut).resolve()
    k = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(k, dict) or k.get('schema_version') != 'kalla/1': return []
    changed = []
    def visit(x):
        if isinstance(x, dict):
            if 'sokvag' in x and 'sha256' in x:
                p = (path.parent/x['sokvag']).resolve()
                if p.is_relative_to(ut) and p.is_file():
                    if p not in cache: cache[p] = hashlib.sha256(p.read_bytes()).hexdigest()
                    if cache[p] != x['sha256']: changed.append(x['sokvag'])
            for v in x.values(): visit(v)
        elif isinstance(x, list):
            for v in x: visit(v)
    visit(k['matning'])
    return changed


def varna(ut, manifest=None):
    h = Path(__file__).resolve().parents[1]/'kontrakt'
    candidates = list(manifest) if manifest is not None else [*h.glob('exempel/*/kalla*.json'), *h.glob('ut/*/kalla*.json')]
    cache, result = {}, []
    for path in candidates:
        changed = inaktuella(path, ut, cache)
        if not changed: continue
        result.append(str(path))
        print(f'INAKTUELL KÄLLA: {path}: {len(changed)} ändrade mätpekare. Kontroll/kompilering vägrar använda den.', file=sys.stderr)
        print(f'Granska och kör: scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_omhasha.py "{Path(path).resolve()}" --uppdatera', file=sys.stderr)
        if 'handelser' in json.loads(Path(path).read_text(encoding='utf-8'))['semantik']:
            print('Har händelser: mät om med kalla_handelser.py från aktuell kalla_prop.json; omhashning av gamla händelser avvisas.', file=sys.stderr)
    return result
