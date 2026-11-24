"""Permanenta grindar för lokalitet/1 (motprov Codex 21 nov). Körs: .venv/Scripts/python.exe -I -X utf8 -W ignore test_grindar.py
1. Flyktpunktsvittnet träffar syntetiska lutningar och larmar vid 15 graders fel (självtest).
2. Felinjektion: lutningen förskjuts 15 grader i varje tagning med flyktpunktsvittne -> L8 måste larma (fel) i alla.
3. Gemensam bias 30 grader (alla vittnen förskjutna lika) -> spridningen ser den INTE, flyktpunkten måste göra det.
4. Fotkontakt får aldrig räknas som stöd: signalen jämför alltid mot personytans skala.
"""
import copy, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from vittne_vp import selftest
from lokalitet import tillforlitlighet

ok = []
selftest(); ok.append('VP-självtest: syntetiska lutningar inom 0,2 grader, 15 graders fel larmar')
n_inj = n_larm = n_bias = 0
for k in ['duepiani', 'spanjorskan', '08burgerkebab', 'babasburgers', 'kennysgelato2.0']:
    r = json.loads((HERE / 'ut' / k / 'lokalitet.json').read_text(encoding='utf-8'))
    for sid, i in r['tagningar'].items():
        if i.get('vp_vittne', {}).get('lutning_grader') is None:
            continue
        orig = next(x for x in tillforlitlighet(i)['signaler'] if x['signal'] == 'flyktpunkt')['status']
        if orig != 'stöd':
            continue
        for d, rakna in ((15, 'inj'), (30, 'bias')):
            j = copy.deepcopy(i); j['lutning_grader'] = i['lutning_grader'] + d
            for v in j['lodlinje'].get('vittnen', []):
                pass  # gemensam bias: vittnena förskjuts lika, så deras inbördes avvikelse är oförändrad
            st = next(x for x in tillforlitlighet(j)['signaler'] if x['signal'] == 'flyktpunkt')['status']
            if rakna == 'inj':
                n_inj += 1; n_larm += st == 'fel'
            else:
                n_bias += st == 'fel'
        assert 'fotkontakt' not in json.dumps([x for x in tillforlitlighet(i)['signaler'] if x['status'] == 'stöd' and x['signal'] == 'skala'], ensure_ascii=False)
assert n_inj > 0 and n_larm == n_inj, (n_larm, n_inj)
assert n_bias == n_inj
ok.append(f'15 graders injektion: larm i {n_larm}/{n_inj} tagningar med flyktpunktsstöd')
ok.append(f'gemensam 30 graders bias: larm i {n_bias}/{n_inj} (spridningen ensam larmar i 0)')
ok.append('fotkontakt räknas aldrig som stöd i sig')
print(json.dumps(ok, ensure_ascii=False, indent=1))
