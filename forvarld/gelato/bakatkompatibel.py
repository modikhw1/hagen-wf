"""0029: befintliga källor och regier ger samma plan före och efter ändringen (sha256 per plan), med tom cache per variant.

    scen/.venv/Scripts/python.exe forvarld/gelato/bakatkompatibel.py bas|ny <ut.json>

bas = kompilera.py, gemensamt.py, kontrollera.py och båda schemana ur scen/3d/kontrakt/ut/fore_0029/kod/ (övriga moduler som de är;
0029 ändrar inga andra). ny = koden som den är nu. Snabbvägen, egen tom cache per variant under forvarld/gelato/ut_kompat/<variant>/.
Varje variant körs i en egen process. Fall: Notan, Notan med lokalbyte, bar, guacamole (tom regi), b-tilltal (kalla_0016, tom regi)
och gelato med sin gamla källa (kalla.json, tom regi).
"""
import sys
sys.dont_write_bytecode = True
import os, json, hashlib, shutil, tempfile, time, traceback
from pathlib import Path

DIR = Path(__file__).resolve().parent; ROOT = DIR.parent.parent; KON = ROOT / 'scen/3d/kontrakt'; FORE = KON / 'ut/fore_0029/kod'
variant, utfil = sys.argv[1], Path(sys.argv[2]).resolve()
OUT = DIR / 'ut_kompat' / variant
if OUT.exists(): shutil.rmtree(OUT)
os.environ.update(PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', TAL_CACHE=str(OUT / 'tal_cache'))
tmp = None
if variant == 'bas':
    tmp = Path(tempfile.mkdtemp(prefix='bas0029_'))
    for f in ('kompilera.py', 'kontrollera.py', 'kalla.schema.json', 'regi.schema.json'): shutil.copy(FORE / f, tmp / f)
    k = (tmp / 'kontrollera.py').read_text(encoding='utf-8'); assert "HIT = Path(__file__).resolve().parent" in k
    (tmp / 'kontrollera.py').write_text(k.replace("HIT = Path(__file__).resolve().parent", f"HIT = Path(r'{KON}')", 1), encoding='utf-8')   # exempel/ och schemana via KON i CLI-delen
    g = (FORE / 'gemensamt.py').read_text(encoding='utf-8')
    g = g.replace("HIT = Path(__file__).resolve().parent", f"HIT = Path(r'{KON}')", 1)
    g = g.replace("fil = HIT / 'kontrollera.py'", f"fil = Path(r'{tmp}') / 'kontrollera.py'", 1)
    g = g.replace("fil = HIT / (namn + '.schema.json')", f"fil = Path(r'{tmp}') / (namn + '.schema.json')", 1)
    assert g.count(str(tmp)) == 2, 'gemensamt.py har ändrats; patchen träffar inte'
    (tmp / 'gemensamt.py').write_text(g, encoding='utf-8')
    sys.path.insert(0, str(KON)); sys.path.insert(0, str(tmp))
else:
    sys.path.insert(0, str(KON))
import datacache
datacache.CACHE = OUT / 'cache'
from kompilera import kompilera
import kompilera as km, gemensamt as gm
assert (variant == 'bas') == (Path(km.__file__).parent == tmp) == (Path(gm.__file__).parent == tmp), km.__file__

BT = KON / 'ut/b-tilltal-ravara_n06-hand'; GE = KON / 'ut/kand-kennysgelato_n06-hand'
FALL = [('notan', KON / 'exempel/notan/kalla.json', KON / 'exempel/notan/regi.json'),
        ('notan_byt_lokal', KON / 'exempel/notan/kalla.json', KON / 'exempel/notan/regi_byt_lokal.json'),
        ('bar', KON / 'exempel/bar/kalla.json', KON / 'exempel/bar/regi.json'),
        ('guacamole_grupp_tom', KON / 'ut/e-dialog-guacamole_grupp/kalla.json', KON / 'ut/e-dialog-guacamole_grupp/tom/regi.json'),
        ('b_tilltal_0016_tom', BT / 'kalla_0016.json', ROOT / 'forvarld/btilltal/ut_0016/regi/bas.json'),
        ('gelato_gammal_tom', GE / 'kalla.json', GE / 'tom/regi.json')]


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
