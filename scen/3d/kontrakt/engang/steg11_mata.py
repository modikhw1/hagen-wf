"""Steg 11: mäter snabbvägen i en och samma långlivade process (som kompilator_demon.py).

Kör från projektroten:
  scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg11_mata.py <etikett> [--cache MAPP] [--hoppa-replik]
Skriver ut/steg11/<etikett>/NN_namn.json (hela planen) och ut/steg11/<etikett>/tider.json.
Cachen är en tom tillfällig mapp om inte --cache anges (kall start).
"""
import json, os, sys, time, tempfile, argparse, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
KONTRAKT = ROOT / 'scen/3d/kontrakt'
sys.dont_write_bytecode = True
sys.path.insert(0, str(KONTRAKT)); os.chdir(ROOT)
ap = argparse.ArgumentParser(); ap.add_argument('etikett'); ap.add_argument('--cache'); ap.add_argument('--hoppa-replik', action='store_true'); ap.add_argument('--forvarm', action='store_true')
a = ap.parse_args()
cache = Path(a.cache) if a.cache else Path(tempfile.mkdtemp(prefix='steg11-cache-'))
os.environ['TAL_CACHE'] = str(cache.parent / (cache.name + '_tal'))
t_imp = time.perf_counter()
import datacache; datacache.CACHE = cache
import kompilera as K
from gemensamt import skriv
imp = time.perf_counter() - t_imp
KALLA = ROOT / 'forvarld/varld/pipeline/kalla.json'
base = json.loads((ROOT / 'forvarld/varld/pipeline/base-regi.json').read_text(encoding='utf-8'))
c = lambda **x: dict(ursprung={'typ': 'cm'}, **x)
trim = lambda i, s, **kw: c(id=i, op='trimma_scen', scen=s, lage='klipp_slut', **kw)
FALL = [
    ('bas', []),
    ('trim_s3_545', [trim('t1', 's3', slut_s=5.45)]),
    ('trim_s3_545_igen', [trim('t1', 's3', slut_s=5.45)]),
    ('trim_s3_535', [trim('t1', 's3', slut_s=5.35)]),
    ('trim_s3_525', [trim('t1', 's3', slut_s=5.25)]),
    ('trim_s3_start_40', [trim('t1', 's3', start_s=4.0)]),
    ('trim_s4_slut_80', [trim('t1', 's4', slut_s=8.0)]),
    ('trim_s2_slut_36', [trim('t1', 's2', slut_s=3.6)]),
    ('ta_bort_s4', [c(id='d1', op='ta_bort_scen', scen='s4')]),
    ('ta_bort_s3', [c(id='d1', op='ta_bort_scen', scen='s3')]),
    ('flytta_s5_efter_s6', [c(id='f1', op='flytta_scen', scen='s5', efter='s6')]),
    ('duplicera_s1', [c(id='u1', op='duplicera_scen', scen='s1', ny_id='s1_copy', efter='s1', med_ljud=False)]),
    ('text_s4', [c(id='x1', op='skarmtext', scen='s4', skarmtext_id='st4', atgard='byt', text='Ny text i fyran')]),
]
if not a.hoppa_replik:
    FALL.append(('byt_replik', [c(id='r9', op='byt_replik', replik='r1', text='Hej igen.', sprak='sv', rost={'motor': None, 'rost_id': None, 'stil': None}, tidspolicy='samma_lucka', max_talfaktor=None)]))
ut = KONTRAKT / 'ut/steg11' / a.etikett; ut.mkdir(parents=True, exist_ok=True)
tider = {'import_s': round(imp, 3), 'cache': str(cache), 'fall': {}}
rf = ut / 'regi.json'
for i, (namn, edits) in enumerate(FALL):
    regi = dict(base, edits=edits); rf.write_text(json.dumps(regi, ensure_ascii=False), encoding='utf-8')
    t = time.perf_counter()
    try:
        plan = K.kompilera(str(KALLA), str(rf), snabb=True)
    except Exception as e:
        tider['fall'][namn] = dict(s=round(time.perf_counter() - t, 3), fel=f'{type(e).__name__}: {e}'[:300]); print(namn, tider['fall'][namn], flush=True); continue
    s = time.perf_counter() - t
    skriv(ut / f'{i:02d}_{namn}.json', plan)
    if a.forvarm and namn == 'bas':
        import skymning; t = time.perf_counter(); n = skymning.forvarm(plan); tider['forvarm_s'] = round(time.perf_counter() - t, 3); print(f'forvarm {n} rutor {tider["forvarm_s"]} s', flush=True)
    tider['fall'][namn] = dict(s=round(s, 3), ej=[(e['id'], e['orsak'][:80]) for e in plan['ej_tillampat']])
    print(f'{namn:24s} {s:7.2f} s', flush=True)
(ut / 'tider.json').write_text(json.dumps(tider, indent=1, ensure_ascii=False), encoding='utf-8')
if not a.cache: shutil.rmtree(cache, ignore_errors=True); shutil.rmtree(str(cache) + '_tal', ignore_errors=True)
