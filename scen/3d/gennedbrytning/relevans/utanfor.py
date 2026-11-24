"""0025 del C: när lämnar en bärande post bilden? Ur ingestens personmasker (masker.npy per tagning, alla personer i en mask).

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/relevans/utanfor.py
Per ruta: 'borta' (ingen mask), 'delvis' (masken når bildkanten med mer än 2 % av kantlängden), annars 'i_bild'. Sträckor slås ihop.
Ut: relevans/utanfor.json.
"""
import json
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent; ING = HIT.parents[1] / 'ingest/ut'
KLIPP = ['kand-kennysgelato-tagningar', 'e-dialog-guacamole-tagningar', 'b-tilltal-ravara-tagningar']


def main():
    ut = {}
    for k in KLIPP:
        T = json.loads((ING / k / 'tagningar.json').read_bytes().decode('utf-8', errors='replace')); ut[k] = {}
        for t in T['tagningar']:
            f = ING / k / t['id'] / 'masker.npy'
            if not f.exists(): ut[k][t['id']] = 'masker saknas'; continue
            M = np.load(f); lage = []
            for m in M:
                if not m.any(): lage.append('borta'); continue
                kanter = dict(topp=m[0].mean(), botten=m[-1].mean(), vanster=m[:, 0].mean(), hoger=m[:, -1].mean())
                k2 = [n for n, v in kanter.items() if v > .02]
                lage.append('delvis:' + '+'.join(k2) if k2 else 'i_bild')
            seg = []
            for i, l in enumerate(lage):
                if seg and seg[-1][0] == l: seg[-1][2] = i
                else: seg.append([l, i, i])
            ut[k][t['id']] = dict(rutor=len(lage), forsta_globala=t['start'], strackor=[dict(lage=l, rutor=[a, b]) for l, a, b in seg if b - a >= 2 or l == 'borta'],
                                  andel=dict((x, round(sum(1 for l in lage if l.split(':')[0] == x) / len(lage), 2)) for x in ('i_bild', 'delvis', 'borta')))
    (HIT / 'utanfor.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
    for k, v in ut.items():
        for t, x in v.items():
            print(k[:12], t, x if isinstance(x, str) else (x['andel'], [(s['lage'], s['rutor']) for s in x['strackor']][:8]))


if __name__ == '__main__': main()
