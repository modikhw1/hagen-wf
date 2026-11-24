"""Uppdrag 0009: planen för exempelklippet `bar` (inget fokalvärde ändras) är byteidentisk före och efter, bortsett från kvalitet.kamerakalibrering.
Körs (från scen/): .venv/Scripts/python.exe -B 3d/kontrakt/ut/fore_fokal_0009/identitet.py [--fore]   (--fore: baslinjens kompilera.py ur kod/)
Skriver ingenting; skriver hash och det nya fältet till stdout."""
import copy, hashlib, importlib.util, json, os, sys
from unittest.mock import patch

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); KON = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, KON); sys.path.insert(1, os.path.join(os.path.dirname(KON), 'ingest'))
if '--fore' in sys.argv:
    spec = importlib.util.spec_from_file_location('kompilera', f'{HERE}/kod/kontrakt_kompilera.py'); mod = importlib.util.module_from_spec(spec)
    sys.modules['kompilera'] = mod; spec.loader.exec_module(mod)
import kompilera                                                                       # noqa: E402
assert ('fore_fokal_0009' in kompilera.__file__) == ('--fore' in sys.argv), kompilera.__file__
with patch('kroppmatt.matt_plan', return_value=[]):
    plan = kompilera.kompilera(f'{KON}/exempel/bar/kalla.json', f'{KON}/exempel/bar/regi.json')
kal = plan['kvalitet'].get('kamerakalibrering')
rest = copy.deepcopy(plan); rest['kvalitet'].pop('kamerakalibrering', None)
h = hashlib.sha256(json.dumps(rest, sort_keys=True, ensure_ascii=False, default=float).encode()).hexdigest()[:16]
print('kompilera:', 'baslinje' if '--fore' in sys.argv else 'ny', '| hash utan kamerakalibrering:', h, '| kamerakalibrering:', json.dumps(kal, ensure_ascii=False))
