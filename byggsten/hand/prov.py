"""Prov på fingrarna: håller de som mått?

1. Täckning per finger.
2. Två läsare, samma sak: där L3 (Flash Lite 3.1, 42 lager) och L4 (Flash 3.8, formatkort)
   eller den mätta tidslinjen (L5, ffmpeg) beskriver samma konstrukt, hur ofta är de överens?
3. Ortogonalitet: korrelation mellan fingrarna (Spearman).
4. Proxy: hur mycket av varje meningsfinger förklaras av yt-fingrarna (R2, linjär)?
   Plus hårda motexempel: klipp där ytan säger en sak och meningen en annan.

Inga modellanrop. Kör efter samla.py.
"""
import json
from pathlib import Path

import numpy as np

from fingrar import FINGRAR, las

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'


def rang(x):
    o = np.argsort(x, kind='stable')
    r = np.empty(len(x))
    r[o] = np.arange(len(x))
    # medelrang för lika värden
    _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
    s = np.zeros(len(cnt))
    np.add.at(s, inv, r)
    return (s / cnt)[inv]


def spearman(a, b):
    a, b = rang(np.asarray(a, float)), rang(np.asarray(b, float))
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def kappa(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    po = float((a == b).mean())
    pe = float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()))
    return {'n': int(len(a)), 'overens': round(po, 3), 'kappa': round((po - pe) / (1 - pe), 3) if pe < 1 else None,
            'andel_a': round(float(a.mean()), 3), 'andel_b': round(float(b.mean()), 3)}


def main():
    R = [json.loads(l) for l in open(UT / 'klipp.jsonl', encoding='utf-8')]
    for r in R:
        r['f'] = las(r)
    rapport = {}

    # 1. täckning
    rapport['tackning'] = {n: sum(1 for r in R if r['f'][n] is not None) for n in FINGRAR}

    # 2. två läsare
    B = [r for r in R if 'l3' in r and 'l4' in r]
    g = lambda r, *k: __import__('functools').reduce(lambda o, x: (o or {}).get(x), k, r)
    par = {
        'vändning (L3 vandning / L4 grundvarde.vandning)':
            ([r['l3']['vandning'] for r in B], [bool(g(r, 'l4', 'grundvarde', 'vandning')) for r in B]),
        'krok (L3 krok / L4 krok stark)':
            ([r['l3']['krok'] for r in B], [g(r, 'l4', 'grundvarde', 'krok') == 'stark' for r in B]),
        'till kameran (L3 tilltal / L4 sprak.tilltal)':
            ([r['l3']['tilltal'] for r in B], [g(r, 'l4', 'sprak', 'tilltal') == 'till_kamera' for r in B]),
        'spelad scen (L3 roll / L4 sprak.tilltal)':
            ([r['l3']['roll'] for r in B], [g(r, 'l4', 'sprak', 'tilltal') == 'spelad_scen' for r in B]),
        'eget tal (L3 tal repliker / L4 krav.ljud)':
            ([r['l3']['tal'] in ('repliker', 'bada') for r in B], [g(r, 'l4', 'krav', 'ljud') == 'eget_tal' for r in B]),
        'trendljud (L3 trendljud / L4 krav.ljud)':
            ([r['l3']['trendljud'] for r in B], [g(r, 'l4', 'krav', 'ljud') == 'trendljud' for r in B]),
        'redigeringsskämt (L3 / L4 redigeringsskamt != inget)':
            ([r['l3']['redigeringsskamt'] for r in B],
             [str(g(r, 'l4', 'redigeringsskamt') or 'inget').lower().strip('.') != 'inget' for r in B]),
        'poäng i texten (L3 text_poang / L4 plats av typen text)':
            ([r['l3']['text_poang'] for r in B],
             ['text' in {p.get('typ') for p in (r['l4'].get('platser') or [])} for r in B]),
        'sketch (L3 roll / L4 strategi sketchvarld)':
            ([r['l3']['roll'] for r in B], [g(r, 'l4', 'sprak', 'strategi') == 'sketchvarld' for r in B]),
    }
    rapport['tva_lasare'] = {k: kappa(a, b) for k, (a, b) in par.items()}
    # Gemini mot mätning: klipp-skalan mot ffmpegs scenbyten
    M = [r for r in R if 'l3' in r and 'l5' in r and r['l5'].get('byten') is not None]

    def skala(b):
        return 0 if b == 0 else (1 if b <= 3 else (2 if b <= 9 else 3))  # byten+1 = antal bildklipp
    rapport['last_mot_matt'] = {
        'klipp (L3 skala 0-3 / L5 mätta byten)': {
            'n': len(M),
            'spearman': round(spearman([r['l3']['klipp'] for r in M], [r['l5']['byten'] for r in M]), 3),
            'samma_steg': round(float(np.mean([r['l3']['klipp'] == skala(r['l5']['byten']) for r in M])), 3),
            'en_tagning_last_men_matt_flera': int(sum(r['l3']['klipp'] == 0 and r['l5']['byten'] > 0 for r in M)),
            'flera_lasta_men_matt_noll': int(sum(r['l3']['klipp'] >= 2 and r['l5']['byten'] == 0 for r in M)),
        }}

    # 3. ortogonalitet
    namn = list(FINGRAR)
    X = np.array([[r['f'][n] for n in namn] for r in B if all(r['f'][n] is not None for n in namn)], float)
    C = np.array([[spearman(X[:, i], X[:, j]) or 0 for j in range(len(namn))] for i in range(len(namn))])
    rapport['ortogonalitet'] = {'n': int(len(X)), 'namn': namn, 'rho': [[round(float(v), 2) for v in row] for row in C]}
    tunga = sorted(((abs(C[i, j]), namn[i], namn[j], float(C[i, j])) for i in range(len(namn)) for j in range(i)),
                   reverse=True)
    rapport['starkast_bundna'] = [{'a': a, 'b': b, 'rho': round(v, 2)} for _, a, b, v in tunga[:12]]
    ev = np.linalg.eigvalsh(np.corrcoef(X.T))[::-1]
    rapport['effektiva_dimensioner'] = {
        'egenvarden': [round(float(v), 2) for v in ev],
        'deltagandekvot': round(float(ev.sum() ** 2 / (ev ** 2).sum()), 2),
        'antal_for_80_procent': int(np.searchsorted(np.cumsum(ev) / ev.sum(), 0.8) + 1)}

    # 4. proxy: mening ur yta
    yta = [n for n in namn if FINGRAR[n][0] == 'yta']
    men = [n for n in namn if FINGRAR[n][0] == 'mening']
    A = np.column_stack([X[:, [namn.index(n) for n in yta]], np.ones(len(X))])
    rapport['proxy'] = {}
    rng = np.random.default_rng(0)
    idx = rng.permutation(len(X))
    delar = np.array_split(idx, 5)
    for m in men:
        y = X[:, namn.index(m)]
        pred = np.zeros(len(y))
        for d in delar:  # femdelad korsvalidering
            tr = np.setdiff1d(idx, d)
            w, *_ = np.linalg.lstsq(A[tr], y[tr], rcond=None)
            pred[d] = A[d] @ w
        r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        w, *_ = np.linalg.lstsq(A, y, rcond=None)
        rapport['proxy'][m] = {'r2_korsvaliderad': round(float(r2), 3),
                               'tyngst': [{'yta': yta[i], 'vikt': round(float(w[i]), 2)}
                                          for i in np.argsort(-np.abs(w[:-1]))[:3]]}

    # hårda motexempel: ytan säger A, meningen säger B
    def ex(test, n=6):
        ks = [r for r in B if all(r['f'][x] is not None for x in namn) and test(r)]
        ks.sort(key=lambda r: -(r['l3'].get('fristaende_ide') or 0))
        return {'antal': len(ks), 'exempel': [{'id': r['id'], 'karna': r['l4'].get('karna')} for r in ks[:n]]}
    rapport['motexempel'] = {
        'tal finns men poängen är inte en replik (ord högt, poang_i_ord 0)':
            ex(lambda r: r['f']['ord'] == 1 and r['f']['poang_i_ord'] == 0),
        'inget tal men poängen är en mening (ord 0, poang_i_ord >= 0.5)':
            ex(lambda r: r['f']['ord'] == 0 and r['f']['poang_i_ord'] >= 0.5),
        'mat i fokus hela tiden men poängen ligger inte i saken (produkt >= 0.75, poang_i_sak 0)':
            ex(lambda r: r['f']['produkt'] >= 0.75 and r['f']['poang_i_sak'] == 0),
        'ingen mat i fokus men poängen ligger i en sak (produkt 0, poang_i_sak >= 0.5)':
            ex(lambda r: r['f']['produkt'] == 0 and r['f']['poang_i_sak'] >= 0.5),
        'en tagning men poängen finns i klippet (klippning 0, poang_i_klipp >= 0.5)':
            ex(lambda r: r['f']['klippning'] == 0 and r['f']['poang_i_klipp'] >= 0.5),
        'montage men tål vilken klippning som helst (klippning >= 0.8, poang_i_klipp 0)':
            ex(lambda r: r['f']['klippning'] >= 0.8 and r['f']['poang_i_klipp'] == 0),
    }

    (UT / 'prov.json').write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding='utf-8')
    with open(UT / 'fingrar.jsonl', 'w', encoding='utf-8') as f:
        for r in R:
            if any(v is not None for v in r['f'].values()):
                f.write(json.dumps({'id': r['id'], 'f': r['f']}, ensure_ascii=False) + '\n')

    print('täckning', rapport['tackning'])
    for k, v in rapport['tva_lasare'].items():
        print(f"  {v['kappa']:>6}  {v['overens']:.2f}  {k}")
    print(rapport['last_mot_matt'])
    print('starkast bundna', rapport['starkast_bundna'])
    print('dimensioner', rapport['effektiva_dimensioner'])
    for m, v in rapport['proxy'].items():
        print('proxy', m, v)
    for k, v in rapport['motexempel'].items():
        print(v['antal'], k)


if __name__ == '__main__':
    main()
