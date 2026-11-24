"""Rummet v0: en rad per formatkort med styrande fingrar, kategorier, läsning och säkerhet.

Skillnad mot första versionen:
  - Alla 1 480 kort är med. Kort utan ytlager (L3) får ord, produkt och ensemble ur kortet (L4),
    där ersättaren följer L3 tillräckligt väl på de 736 kort som har båda (rho 0,54-0,74).
  - Kort där de två läsarna säger emot varandra på ett styrande finger märks 'oenig' och får inte bli hållpunkt.
  - Relation och insats (Fables läsning av kärnan) är egna fingrar för sketchkorten.
  - Text styr inte längre: två läsare är överens med kappa 0,21 och ersättaren når rho 0,23.

Skriver ut/rum.jsonl. Kör efter samla.py, tema.py och lasning.py.
"""
import json
from pathlib import Path

from fingrar import KATEGORIER, las

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'
HYLLA = {'karna': 3, 'mitten': 2, 'situation': 1}
NOTANS_TVILLING = 'chickiiburger-7576259590170348822'
TOLERANS = {'ensemble': 0.34, 'ord': 0.5, 'produkt': 0.5}


def ersattare(l4):
    k = l4.get('krav') or {}
    b = l4.get('beats') or []
    return {
        'ensemble': min(k.get('personer_min', 1), 3) / 3,
        'ord': {'eget_tal': 1.0, 'voiceover': 0.5}.get(k.get('ljud'), 0.0),
        'produkt': ((k.get('produkt') in ('mat', 'dryck', 'specifik'))
                    + sum(x.get('bunden') == 'produkt' for x in b) / max(1, len(b))) / 2,
    }


def rad(r, lasning):
    l4 = r['l4']
    f = las(r)
    e = ersattare(l4)
    ut = {'id': r['id'], 'url': l4.get('url'), 'karna': l4.get('karna'), 'handling': l4.get('handling'),
          'mall': l4.get('mall'), 'kalla': {}, 'oenig': []}
    v = {}
    for k in ('ensemble', 'ord', 'produkt'):
        if f.get(k) is not None:
            v[k] = f[k]
            ut['kalla'][k] = 'l3'
            if abs(f[k] - e[k]) > TOLERANS[k]:
                ut['oenig'].append(k)
        else:
            v[k] = round(e[k], 3)
            ut['kalla'][k] = 'l4'
    for k in ('poang_i_ord', 'poang_i_sak', 'poang_i_klipp', 'poang_i_person', 'vandning'):
        v[k] = f.get(k)
    for k in ('text', 'klippning', 'rum', 'samspel', 'ansikte', 'lanat_ljud'):
        v[k] = f.get(k)  # fria, bara för redovisning
    ut['f'] = v
    ut['plats'] = list(KATEGORIER['plats'](r))
    ut['strategi'] = KATEGORIER['strategi'](r)
    ut['tilltal'] = KATEGORIER['tilltal'](r)
    ut['lasning'] = lasning.get(r['id'])
    g = l4.get('grundvarde') or {}
    ut['hylla'] = g.get('hylla')
    ut['rekonbar'] = (r.get('l2') or {}).get('rekonbar')
    ut['kvalitet'] = 2 * HYLLA.get(g.get('hylla'), 0) + ((r.get('l3') or {}).get('fristaende_ide')
                                                          or {'stark': 4, 'medel': 3, 'svag': 2}.get(g.get('premiss'), 1)) \
        + (ut['rekonbar'] or 3) / 2
    ut['roller'] = (l4.get('krav') or {}).get('roller')
    ut['beats'] = l4.get('beats')
    return ut


def main():
    lasning = json.loads((UT / 'lasning.json').read_text(encoding='utf-8'))
    n = oen = 0
    tvillingrad = None
    with open(UT / 'rum.jsonl', 'w', encoding='utf-8') as ut:
        for line in open(UT / 'klipp.jsonl', encoding='utf-8'):
            r = json.loads(line)
            if 'l4' not in r:
                continue
            x = rad(r, lasning)
            if x['id'] == NOTANS_TVILLING:
                tvillingrad = x
            n += 1
            oen += bool(x['oenig'])
            ut.write(json.dumps(x, ensure_ascii=False) + '\n')
        notan = json.loads((HERE / 'notan_kort.json').read_text(encoding='utf-8'))
        x = rad(notan, lasning)
        x['handkodad'] = True
        # Notans tvilling i banken (samma mall, läst av samma modell som alla andra kort) får avgöra
        # meningsfingrarna, så att notan mäts med samma läsare som resten.
        tv = tvillingrad
        x['tvilling'] = tv['id']
        for k in ('poang_i_ord', 'poang_i_sak', 'poang_i_klipp', 'poang_i_person', 'vandning'):
            if tv['f'][k] is not None and abs((x['f'][k] or 0) - tv['f'][k]) > 0.3:
                x['kalla'][k] = f"tvilling (handkodat {x['f'][k]})"
                x['f'][k] = tv['f'][k]
        ut.write(json.dumps(x, ensure_ascii=False) + '\n')
    print('kort', n, 'oeniga', oen, 'med läsning', len(lasning))


if __name__ == '__main__':
    main()
