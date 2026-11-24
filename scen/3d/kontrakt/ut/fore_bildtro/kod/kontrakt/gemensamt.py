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


_MODUL = [None, None]   # [modul, filstämpel]; laddas en gång per process och om kontrollera.py ändras
_SCHEMA = {}            # namn -> (filstämpel, schema); lintad en gång per filstämpel


def _stampel(p):
    st = Path(p).stat()
    return (st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def kontrollmodul():
    # kontrollera.py saknar main-vakt. Importera oförändrad, fånga bara dess
    # CLI-avslut och kasta CLI-resultaten; anropa sedan funktionerna för våra indata.
    # Modulen laddas bara en gång per process (den kör annars sin CLI-körning mot exempel/bar vid varje import);
    # dess hashminne gör att en långlivad process hashar en fil om först när filstämpeln ändrats.
    fil = HIT / 'kontrollera.py'
    if _MODUL[0] is None or _MODUL[1] != _stampel(fil):
        spec = importlib.util.spec_from_file_location('kontrollera', fil)
        mod = importlib.util.module_from_spec(spec)
        argv = sys.argv
        try:
            sys.argv = [str(fil)]
            with contextlib.redirect_stdout(io.StringIO()):
                try: spec.loader.exec_module(mod)
                except SystemExit: pass
        finally:
            sys.argv = argv
        _MODUL[0], _MODUL[1] = mod, _stampel(fil)
        _SCHEMA.clear()
    mod = _MODUL[0]
    mod.fel_lista.clear(); mod.varningar.clear()
    return mod


def kontrollera(k, r, mapp, kallfil=None, avvisade=None):
    """Kontrollerar kalla och regi. Utan avvisade: varje fel avvisar hela regin (ValueError).

    Med avvisade (en lista) avvisas en edit som bryter regi-schemat ensam: den tas bort ur r på plats och läggs i listan som
    dict(index, id, op, orsak); övriga edits och kontrollerna av kalla, regins huvud och referenser gäller som förut."""
    mod = kontrollmodul()
    for namn, data in (('kalla', k), ('regi', r)):
        fil = HIT / (namn + '.schema.json'); st = _stampel(fil)
        if namn not in _SCHEMA or _SCHEMA[namn][0] != st:
            schema = ladda(fil); mod.lint(schema, namn)
            _SCHEMA[namn] = (st, schema, list(mod.fel_lista)); mod.fel_lista.clear()
        schema = _SCHEMA[namn][1]
        mod.fel_lista.extend(_SCHEMA[namn][2])
        if namn == 'regi' and avvisade is not None and isinstance(data, dict) and isinstance(data.get('edits'), list):
            sched = schema['properties']['edits']['items']; kvar = []
            for i, e in enumerate(data['edits']):
                fel = mod.validera(e, sched, f'edits[{i}]', schema)
                if not fel: kvar.append(e); continue
                avvisade.append(dict(index=i, id=e['id'] if isinstance(e, dict) and isinstance(e.get('id'), str) and e['id'] else f'edit[{i}]',
                                     op=e.get('op') if isinstance(e, dict) and isinstance(e.get('op'), str) else '?',
                                     orsak='Editen följer inte regi-schemat och avvisades ensam; resten av regin gäller. ' + '; '.join(fel[:4])))
            mod.fel_lista.extend(mod.validera(dict(data, edits=[]), schema, namn, schema)); data['edits'] = kvar
        else: mod.fel_lista.extend(mod.validera(data, schema, namn, schema))
    if not mod.fel_lista:
        mod.referenser(k, r); mod.hashar(k, Path(mapp), kallfil)
        if k['revision'] != r['kalla']['revision']:
            mod.fel_lista.append('Regins revision stämmer inte med källan.')
    if mod.fel_lista: raise ValueError(chr(10).join(mod.fel_lista))
    return mod.varningar
