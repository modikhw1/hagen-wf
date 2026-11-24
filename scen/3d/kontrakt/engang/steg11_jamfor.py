"""Jämför två körningar av steg11_mata.py fall för fall: hela planen, och skymningsbesluten för sig.
  scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg11_jamfor.py fore efter [fält ...]
Fält som får skilja (punktsökväg, t.ex. kvalitet.byggunderlag) anges efter etiketterna."""
import json, sys
from pathlib import Path
UT = Path(__file__).resolve().parents[1] / 'ut/steg11'
a, b = sys.argv[1], sys.argv[2]; tillat = set(sys.argv[3:])
def ta(p, s):
    for k in s.split('.'):
        if isinstance(p, dict) and k in p: p = p[k]
        else: return None
    return p
def skillnad(x, y, v=''):
    if type(x) != type(y): return [v]
    if isinstance(x, dict):
        ut = []
        for k in sorted(set(x) | set(y)):
            if k not in x or k not in y: ut.append(v + '.' + k)
            else: ut += skillnad(x[k], y[k], v + '.' + k)
        return ut
    if isinstance(x, list):
        if len(x) != len(y): return [v + f'[len {len(x)}!={len(y)}]']
        ut = []
        for i, (p, q) in enumerate(zip(x, y)): ut += skillnad(p, q, f'{v}[{i}]')
        return ut[:20]
    return [] if x == y else [v]
bra = True
for fa in sorted((UT / a).glob('[0-9]*.json')):
    fb = UT / b / fa.name
    if not fb.exists(): print(fa.name, 'saknas i', b); bra = False; continue
    pa, pb = json.loads(fa.read_text(encoding='utf-8')), json.loads(fb.read_text(encoding='utf-8'))
    sk = [x for x in skillnad(pa, pb) if not any(x.startswith('.' + t) for t in tillat)]
    sky = skillnad(ta(pa, 'kvalitet.skymning'), ta(pb, 'kvalitet.skymning')); obj = skillnad(pa['objekt'], pb['objekt'])
    nsk = len(ta(pa, 'kvalitet.skymning')['atgarder'])
    print(f'{fa.name:34s} plan {"LIK" if not sk else "SKILJER " + str(sk[:4])}  skymning {"LIK" if not sky else "SKILJER"}  objekt {"LIK" if not obj else "SKILJER"}  (skymningsåtgärder: {nsk})')
    bra &= not sk
print('ALLA LIKA' if bra else 'SKILLNADER FINNS')
