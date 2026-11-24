"""Typernas fingrar: i vilka riktningar skiljer sig klipp av samma typ mest, och vad ligger still?

Spridningen inom typen (p10 till p90) delas med spridningen i hela banken. Över 1 = typen rör sig
mer än banken i stort på det fingret. Nära 0 = fingret är låst, det hör till vad typen är.
Skriver ut/typer.json och ut/typer.md. Kör efter samla.py.
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from ryggrad import FINGRAR, typ, typnamn

UT = Path(__file__).resolve().parent / 'ut'


def main():
    R = [json.loads(l) for l in open(UT / 'klipp.jsonl', encoding='utf-8')]
    R = [r for r in R if 'l4' in r]
    varden = {n: [(typ(r['l4']), f[2](r)) for r in R] for n, f in FINGRAR.items()}
    hela = {}
    for n, v in varden.items():
        x = np.array([b for _, b in v if b is not None], float)
        hela[n] = (float(np.percentile(x, 10)), float(np.percentile(x, 90)))
    grupper = defaultdict(int)
    for r in R:
        grupper[typ(r['l4'])] += 1
    ut, L = [], ['# Typernas fingrar', '',
                 'Spridning inom typen delad med spridning i hela banken (p10 till p90). Minst 20 klipp med underlag per finger.', '',
                 '| typ | klipp | rör sig mest | ligger still |', '|---|---|---|---|']
    for t, n in sorted(grupper.items(), key=lambda z: -z[1]):
        if n < 25:
            continue
        rad = {}
        for namn, v in varden.items():
            x = np.array([b for a, b in v if a == t and b is not None], float)
            lo, hi = hela[namn]
            if len(x) < 20 or hi - lo <= 0:
                continue
            rad[namn] = {'n': int(len(x)), 'p10': round(float(np.percentile(x, 10)), 2), 'median': round(float(np.median(x)), 2),
                         'p90': round(float(np.percentile(x, 90)), 2),
                         'relativ_spridning': round(float((np.percentile(x, 90) - np.percentile(x, 10)) / (hi - lo)), 2)}
        o = sorted(rad, key=lambda k: -rad[k]['relativ_spridning'])
        ut.append({'typ': typnamn(t), 'klipp': n, 'fingrar': rad})
        fmt = lambda k: f"{FINGRAR[k][0]} ({rad[k]['relativ_spridning']})"
        L.append(f"| {typnamn(t)} | {n} | {', '.join(fmt(k) for k in o[:4])} | {', '.join(fmt(k) for k in o[::-1][:3])} |")
    (UT / 'typer.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
    (UT / 'typer.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
