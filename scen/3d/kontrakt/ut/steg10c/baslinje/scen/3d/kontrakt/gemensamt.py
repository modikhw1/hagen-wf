"""Lokal JSON-I/O och import av den befintliga kontraktskontrollen."""
import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

HIT = Path(__file__).resolve().parent


def ladda(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def skriv(p, data):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def kontrollmodul():
    # kontrollera.py saknar main-vakt. Importera oförändrad, fånga bara dess
    # CLI-avslut och kasta CLI-resultaten; anropa sedan funktionerna för våra indata.
    spec = importlib.util.spec_from_file_location('kontrollera', HIT / 'kontrollera.py')
    mod = importlib.util.module_from_spec(spec)
    argv = sys.argv
    try:
        sys.argv = [str(HIT / 'kontrollera.py')]
        with contextlib.redirect_stdout(io.StringIO()):
            try: spec.loader.exec_module(mod)
            except SystemExit: pass
    finally:
        sys.argv = argv
    mod.fel_lista.clear(); mod.varningar.clear()
    return mod


def kontrollera(k, r, mapp, kallfil=None):
    mod = kontrollmodul()
    for namn, data in (('kalla', k), ('regi', r)):
        schema = ladda(HIT / (namn + '.schema.json'))
        mod.lint(schema, namn)
        mod.fel_lista.extend(mod.validera(data, schema, namn, schema))
    if not mod.fel_lista:
        mod.referenser(k, r); mod.hashar(k, Path(mapp), kallfil)
        if k['revision'] != r['kalla']['revision']:
            mod.fel_lista.append('Regins revision stämmer inte med källan.')
    if mod.fel_lista: raise ValueError('\n'.join(mod.fel_lista))
    return mod.varningar
