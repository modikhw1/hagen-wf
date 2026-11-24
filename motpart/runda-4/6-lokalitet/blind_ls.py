"""Blint parvis prov Lt (skärvor) mot Ls (struktur): samma vyer under slumpade namn X/Y per tagning.
Nyckeln skrivs utanför arbetsmappen (argument 1) så att domaren inte kan läsa den. usage: python blind_ls.py <nyckelfil> <klipp...>"""
from __future__ import annotations
import json, random, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(nyckelfil, klipp):
    ut = HERE / 'ut' / 'blind_ls'; shutil.rmtree(ut, ignore_errors=True); ut.mkdir(parents=True)
    rng = random.Random(int(__import__("os").environ.get("FRO", "20261121"))); nyckel = {}; lista = []
    for k in klipp:
        plan = json.loads((HERE / 'ut' / 'rumshjarna' / k / 'plan.json').read_text(encoding='utf-8'))['tagningar']
        for sid, t in sorted(plan.items(), key=lambda x: int(x[0][1:])):
            f = t['ruta']; qa = HERE / 'ut' / k / 'qa'
            if not all((qa / f'orbit-{v}-{f}-{a}.png').is_file() for v in ('Lt', 'Ls') for a in ('0', '35', '50h')):
                continue
            x_ar = rng.choice(['Lt', 'Ls']); y_ar = 'Ls' if x_ar == 'Lt' else 'Lt'; nyckel[f'{k}/{sid}'] = {'X': x_ar, 'Y': y_ar}
            for namn, v in (('X', x_ar), ('Y', y_ar)):
                for a in ('0', '35', '50h'):
                    shutil.copy(qa / f'orbit-{v}-{f}-{a}.png', ut / f'{k}_{sid}_{namn}_{a}.png')
            shutil.copy(HERE / 'ut' / 'rumshjarna' / k / f'{sid}_orig.png', ut / f'{k}_{sid}_orig.png'); lista.append(f'{k}/{sid}')
    Path(nyckelfil).write_text(json.dumps(nyckel, indent=1), encoding='utf-8')
    (ut / 'lista.json').write_text(json.dumps(lista, indent=1), encoding='utf-8'); print(len(lista), 'tagningar')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
