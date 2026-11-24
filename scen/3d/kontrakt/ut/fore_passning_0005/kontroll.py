"""Uppdrag 0007/0005: kontroll på minneskopior (inga filer ändras, ingen kompilering).
  python -B -I kontroll.py --kod <mapp med boxpassning.py, mobellyft.py, foremallyft.py> fler
  python -B -I kontroll.py --kod <mapp> identitet     (notan och guacamole: planen ska vara oförändrad)
Körs en gång mot baslinjen (kod/) och en gång mot den ändrade koden (kontrakt/) och jämförs."""
import copy, hashlib, json, os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
args = sys.argv[1:]
kod = os.path.abspath(args[args.index('--kod') + 1]); mode = args[-1]
sys.path.insert(0, kod); sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import mobellyft as ml, foremallyft as fl  # noqa: E402
assert os.path.dirname(os.path.abspath(ml.__file__)) == kod, ml.__file__
UT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def las(p): return json.load(open(p, encoding='utf8'))


def hash_(o): return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=float).encode()).hexdigest()[:16]


if mode == 'fler':
    plan = las(f'{UT}/b-tilltal-ravara_n06-fler/narvaro/plan.json'); kopia = copy.deepcopy(plan)
    mr = ml.los(kopia); fr = fl.los(kopia)
    dc = next(r for r in mr if r['mobel'] == 'disk_C')
    med = np.median([[2.17, .98], [2.01, .78], [2.16, 1.11], [2.31, 1.23]], axis=0)         # lyft ur S7, S8, S9, S11 (0001, tabell 2)
    print('kod', kod)
    print('disk_C status', dc['status'], 'slut', [round(v, 3) for v in dc.get('slutlig_pos_m', [])[:2]], 'ordningsniva', dc.get('ordningsniva'),
          'granskonflikt', dc.get('granskonflikt'))
    if 'slutlig_pos_m' in dc:
        print('avstånd till medianen utan S6 (m):', round(float(np.hypot(*(np.array(dc['slutlig_pos_m'][:2]) - med))), 3), '(före: 0,33)')
    print('avvikande boxar:', dc.get('startlage', {}).get('avvikande_boxar'), 'uteslutna:', dc.get('uteslutna_boxar'), 'hoppade:', dc.get('hoppade_boxar'))
    print('orsak_granskonflikt:', dc.get('orsak_granskonflikt'))
    for k in dc.get('klamningar', []):
        print(f"  {k['tagning']}: kameramarginal {k['uppnadd_kameramarginal_m']:+.3f} person {k['uppnadd_personmarginal_m']:+.3f}")
    print('lyckad', dc.get('lyckad'), 'lyckad_slutlage', dc.get('lyckad_slutlage'), 'villkor_uppfyllda', dc.get('villkor_uppfyllda'))
    for p in dc.get('per_tagning', []):
        print(f"  per_tagning {p['tagning']}: i_passning {p.get('i_passning')} rms_efter {p['efter_rms_px']} {p.get('uteslutningsorsak', '')}{p.get('hoppad_orsak', '')}")
    for r in fr:
        print('föremål', r['foremal'], r['status'], r.get('orsak', ''), r.get('stod_ersatt', ''), [round(v, 3) for v in r.get('slutlig_pos_m', [])[:2]])
    print('hash', hash_([mr, fr]))
else:
    planer = {'notan': ['notan/golv_bar', 'notan/golv_tom', 'notan/jamn_tom', 'notan/fore_mall/kundprov'],
              'guacamole': ['e-dialog-guacamole/narvaro', 'e-dialog-guacamole/bildtro_data', 'e-dialog-guacamole/redigerad', 'e-dialog-guacamole/skymning']}
    for klipp, lista in planer.items():
        for d in lista:
            p = f'{UT}/{d}/plan.json'
            if not os.path.exists(p): print(klipp, d, 'saknas'); continue
            plan = las(p); kopia = copy.deepcopy(plan)
            mr = ml.los(kopia); fr = fl.los(kopia)
            print(klipp, d, 'mobellyft', mr, 'foremallyft', fr, 'planen oförändrad', hash_(plan) == hash_(kopia), hash_(kopia))
