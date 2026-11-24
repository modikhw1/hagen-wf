"""Jämför två deklarationers topologi par för par: samma person, samma plats och samma kamerauppställning per par av tagningar.

    python rum_jamfor.py <facit.json> <forslag.json> [...]

Etiketterna behöver inte heta lika; bara om två tagningar delar etikett jämförs. Platser jämförs på person_plats, uppställningar på kamera_vid.
"""
import itertools, json, sys
from pathlib import Path


def etiketter(D):
    k = {t: c for t, c in (D.get('kameror') or {}).items() if isinstance(c, dict)}
    ut = {n: {t: c.get(n) for t, c in k.items() if c.get(n)} for n in ('huvudroll', 'person_plats', 'kamera_vid')}
    # Äldre format saknar huvudroll i kameror: ta den ur rollernas tagningar (första rollen som har tagningen).
    for r, v in (D.get('roller') or {}).items():
        for t in (v.get('tagningar') or []) if isinstance(v, dict) else []: ut['huvudroll'].setdefault(t, r)
    return ut


if __name__ == '__main__':
    F = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')); EF = etiketter(F)
    for fil in sys.argv[2:]:
        D = json.loads(Path(fil).read_text(encoding='utf-8')); D = D.get('svar', D); ED = etiketter(D); rad = []
        for n in EF:
            skott = sorted(set(EF[n]) & set(ED[n]), key=lambda s: int(''.join(c for c in s if c.isdigit()) or 0))
            par = list(itertools.combinations(skott, 2)); lika = [(EF[n][a] == EF[n][b]) == (ED[n][a] == ED[n][b]) for a, b in par]
            fel = [f'{a}-{b}' for (a, b), l in zip(par, lika) if not l]
            rad.append(f"{n} {sum(lika)}/{len(par)}" + (f" (fel: {', '.join(fel[:6])})" if fel else ''))
        print(Path(fil).parent.name + '/' + Path(fil).name, '|', ' | '.join(rad))
