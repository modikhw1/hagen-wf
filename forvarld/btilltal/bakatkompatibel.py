"""0016: visar att befintliga källor och regier (Notan, bar, guacamole) ger samma plan före och efter ändringen.

    scen/.venv/Scripts/python.exe forvarld/btilltal/bakatkompatibel.py bas|ny <ut.json>

bas = kompilera.py och gemensamt.py ur scen/3d/kontrakt/ut/fore_tillstand_0016/kod/ (övriga moduler och schemana som de är nu;
schemaändringarna är bara nya valfria fält). ny = koden som den är nu. Snabbvägen, egen cache per variant under forvarld/btilltal/ut_kompat/.
Varje variant körs i en egen process. Jämför sedan de två utfilerna (sha256 per plan).
"""
import sys
sys.dont_write_bytecode = True
import os, json, hashlib, shutil, tempfile, time, traceback
from pathlib import Path

DIR = Path(__file__).resolve().parent; ROOT = DIR.parent.parent; KON = ROOT / 'scen/3d/kontrakt'
variant, utfil = sys.argv[1], Path(sys.argv[2])
OUT = DIR / 'ut_kompat' / variant
os.environ.update(PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', TAL_CACHE=str(OUT / 'tal_cache'))
tmp = None
if variant == 'bas':
    tmp = Path(tempfile.mkdtemp(prefix='bas0016_'))
    shutil.copy(KON / 'ut/fore_tillstand_0016/kod/kompilera.py', tmp / 'kompilera.py')
    g = (KON / 'ut/fore_tillstand_0016/kod/gemensamt.py').read_text(encoding='utf-8')
    g = g.replace("HIT = Path(__file__).resolve().parent", f"HIT = Path(r'{KON}')", 1)
    (tmp / 'gemensamt.py').write_text(g, encoding='utf-8')
    sys.path.insert(0, str(KON)); sys.path.insert(0, str(tmp))
else:
    sys.path.insert(0, str(KON))
import datacache
datacache.CACHE = OUT / 'cache'
from kompilera import kompilera
import kompilera as km
assert (variant == 'bas') == (Path(km.__file__).parent == tmp), km.__file__

FALL = [('notan', KON / 'exempel/notan/kalla.json', KON / 'exempel/notan/regi.json'),
        ('notan_byt_lokal', KON / 'exempel/notan/kalla.json', KON / 'exempel/notan/regi_byt_lokal.json'),
        ('bar', KON / 'exempel/bar/kalla.json', KON / 'exempel/bar/regi.json'),
        ('guacamole_grupp_tom', KON / 'ut/e-dialog-guacamole_grupp/kalla.json', KON / 'ut/e-dialog-guacamole_grupp/tom/regi.json')]


def norm(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True)


res = {}
for namn, k, r in FALL:
    t = time.perf_counter()
    try:
        plan = kompilera(k, r, snabb=True)
        res[namn] = dict(sha256=hashlib.sha256(norm(plan).encode()).hexdigest(), tillampat=[x['id'] for x in plan['tillampat']],
                         ej=[(x['id'], x['orsak'][:80]) for x in plan['ej_tillampat']], rutor=len(plan['kallrutor']), s=round(time.perf_counter() - t, 1))
    except Exception as e:
        res[namn] = dict(fel=f'{type(e).__name__}: {e}'[:400], spar=traceback.format_exc()[-600:])
    print(variant, namn, res[namn].get('sha256', res[namn].get('fel'))[:16], flush=True)
utfil.parent.mkdir(parents=True, exist_ok=True); utfil.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
if tmp: shutil.rmtree(tmp, ignore_errors=True)
