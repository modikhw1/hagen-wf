"""Slår ihop bankens fem metadatalager till en rad per klipp.

Läser bara under data/. Skriver bara under byggsten/hand/ut/.
Inga modellanrop. Kör: scen/.venv/Scripts/python.exe -I -X utf8 byggsten/hand/samla.py
"""
import glob
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / 'data'
UT = HERE / 'ut'

KORTMAPPAR = ['format/harness/v5', 'format/e6/kort', 'format/e6r/kort',
              'format/bank2/kort', 'format/bank3/kort']


def las(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def main():
    UT.mkdir(exist_ok=True)
    klipp = {}

    def rad(i):
        return klipp.setdefault(i, {'id': i, 'lager': []})

    # L1: listorna per konto (längd, räckvidd, bildtext)
    for f in glob.glob(str(DATA / 'bank/*/lista.json')):
        d = las(f)
        for k in d.get('klipp', []):
            r = rad(f"{d['konto']}-{k['id']}")
            r['konto'] = d['konto']
            r['l1'] = {x: k.get(x) for x in
                       ('langd', 'visningar', 'gillanden', 'kommentarer', 'delningar', 'datum', 'text')}
            r['lager'].append('l1')

    # L2: sållningen (typ, personer, montage, rekonbar)
    for f in glob.glob(str(DATA / 'bank/sallning/*.json')):
        d = las(f)
        r = rad(d['id'])
        r.setdefault('konto', d.get('konto'))
        r['l2'] = {x: d.get(x) for x in d if x not in ('id', 'konto', 'modell', 'video', 'ore')}
        r['lager'].append('l2')

    # L3: de 43 ytlagren (e4)
    for f in glob.glob(str(DATA / 'format/e4/lager-gemini-3.1-flash-lite/*.json')):
        d = las(f)
        r = rad(d['id'])
        r.setdefault('konto', d.get('konto'))
        r['l3'] = {x: d.get(x) for x in d if x not in ('id', 'konto', 'modell', 'tokens')}
        r['lager'].append('l3')

    # L4: formatkorten (v5-schemat; senare mapp vinner inte, första träffen gäller)
    for m in KORTMAPPAR:
        for f in glob.glob(str(DATA / m / '*.json')):
            d = las(f)
            i = d.get('id') or os.path.basename(f)[:-5]
            r = rad(i)
            if 'l4' in r:
                continue
            r.setdefault('konto', d.get('konto'))
            r['l4'] = {x: d.get(x) for x in d if x not in ('tokens', 'ms', 'modell', 'neutral')}
            r['l4']['kortmapp'] = m
            r['lager'].append('l4')

    # L5: mätt tempo (klippbyten, tystnad) och transkript
    with open(DATA / 'format/tempo/matt.jsonl', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                r = rad(d['id'])
                r['l5'] = {x: d.get(x) for x in ('langd', 'byten', 'tyst', 'takt')}
                r['lager'].append('l5')
    for f in glob.glob(str(DATA / 'format/tal/*.json')):
        d = las(f)
        if 'id' not in d:  # forregistrering.json
            continue
        r = rad(d['id'])
        r['tal'] = {'sprak': d.get('sprak'),
                    'ord': sum(len(s.get('text', '').split()) for s in d.get('segment', [])),
                    'segment': len(d.get('segment', []))}
        r['lager'].append('tal')

    with open(UT / 'klipp.jsonl', 'w', encoding='utf-8') as f:
        for r in klipp.values():
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    from collections import Counter
    komb = Counter('+'.join(sorted(set(r['lager']))) for r in klipp.values())
    per = Counter(x for r in klipp.values() for x in set(r['lager']))
    rapport = {'klipp': len(klipp), 'per_lager': dict(per), 'kombinationer': dict(komb.most_common()),
               'l3_och_l4': sum(1 for r in klipp.values() if 'l3' in r and 'l4' in r)}
    (UT / 'tackning.json').write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(rapport, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
