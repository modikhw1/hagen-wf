"""Uppdrag 0014/0016: kompilera bas och varje meningsregi genom kontraktets snabbväg (kompilera(..., snabb=True)).
Cachen omdirigeras till <ut>/cache, inget skrivs under scen/.
Kör: scen/.venv/Scripts/python.exe forvarld/btilltal/kompilera.py [ut-mapp under forvarld/btilltal, standard ut] [kalla-filnamn, standard kalla.json]
  0014: ... kompilera.py                     0016: ... kompilera.py ut_0016 kalla_0016.json
"""
import sys
sys.dont_write_bytecode = True
import os, json, time, traceback
from pathlib import Path

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent.parent
OUT = DIR / (sys.argv[1] if len(sys.argv) > 1 else 'ut')
os.environ.update(PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', TAL_CACHE=str(OUT / 'tal_cache'))
sys.path.insert(0, str(ROOT / 'scen/3d/kontrakt'))
import datacache
datacache.CACHE = OUT / 'cache'
from kompilera import kompilera
from gemensamt import skriv

KALLA = ROOT / 'scen/3d/kontrakt/ut/b-tilltal-ravara_n06-hand' / (sys.argv[2] if len(sys.argv) > 2 else 'kalla.json')


def main():
    regier = sorted((OUT / 'regi').glob('m*.json'), key=lambda p: (len(p.stem), p.stem))
    K = json.loads(KALLA.read_text(encoding='utf-8'))
    bas = json.loads(regier[0].read_text(encoding='utf-8')); bas['edits'] = []; bas['kalla']['revision'] = K['revision']
    skriv(OUT / 'regi' / 'bas.json', bas)
    res = {}
    for r in [OUT / 'regi' / 'bas.json'] + regier:
        t = time.perf_counter(); rad = dict(regi=r.name)
        try:
            plan = kompilera(KALLA, r, snabb=True)
            skriv(OUT / 'plan' / r.name, plan)
            rad.update(kompilerad=True, tillampat=plan.get('tillampat'), ej_tillampat=plan.get('ej_tillampat'),
                       varningar=[v for v in plan.get('varningar', []) if 'Bildtrohet' not in v][:12],
                       scener=[s['id'] for s in plan.get('scener', [])], langd_rutor=len(plan.get('kallrutor', [])),
                       hallna_rutor=plan.get('hallna_rutor'))
        except Exception as e:
            rad.update(kompilerad=False, fel=f'{type(e).__name__}: {e}', spar=traceback.format_exc()[-1500:])
        rad['s'] = round(time.perf_counter() - t, 2)
        res[r.stem] = rad
        print(r.stem, rad.get('kompilerad'), rad.get('fel', ''), rad['s'], 's', flush=True)
    skriv(OUT / 'kompilering.json', res)


if __name__ == '__main__':
    main()
