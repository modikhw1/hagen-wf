"""Anpassa: flytta ett klipp mot en kund, längs ryggradens fingrar.

Kunden är ett konto i banken. Kundens egna klipp säger var kunden brukar ligga på varje finger,
i vilka rum kunden filmar, vad kunden visar och vilka grepp kunden redan använder.
Förslaget per finger är kundens vanliga värde, men aldrig längre än vad klipp av samma typ går
(p10..p90). Då byter klippet inte typ på vägen.

Ingenting här säger att anpassningen blir bra. Det säger vart den går och vad som måste bytas.
Kör: python anpassa.py <klipp-id> <konto>      Skriver ut/anpassa_<klipp>__<konto>.json och .md
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from ryggrad import BAR, BUNDEN, FINGRAR, typ, typnamn

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'


def lasningstext(l):
    return ', '.join(f"{k} {str(v).replace('_', ' ')}" for k, v in (l or {}).items()) or 'ingen läsning'


def main():
    kid, konto = sys.argv[1], sys.argv[2]
    R = {}
    for line in open(UT / 'klipp.jsonl', encoding='utf-8'):
        r = json.loads(line)
        if 'l4' in r:
            R[r['id']] = r
    las = json.loads((UT / 'lasning.json').read_text(encoding='utf-8'))
    t = np.load(UT / 'tema.npz')
    tix = {str(x): i for i, x in enumerate(t['ids'])}
    V = t['V']
    nar = lambda a, b: float(V[tix[a]] @ V[tix[b]])
    alla = np.sort((V @ V.T)[np.triu_indices(len(V), 1)])
    rang = lambda s: float(np.searchsorted(alla, s) / len(alla))

    k = R[kid]
    l4 = k['l4']
    ty = typ(l4)
    kohort = [r for r in R.values() if typ(r['l4']) == ty and r['id'] != kid]
    kund = [r for r in R.values() if r.get('konto') == konto and r['id'] != kid]
    if not kund:
        sys.exit(f'Kontot {konto} har inga kort i banken.')

    # kundens linje
    typer = Counter(typnamn(typ(r['l4'])) for r in kund)
    rum = Counter(x for r in kund for x in ((r['l4'].get('krav') or {}).get('lokal') or []))
    produkter = Counter(p['har'].strip().lower() for r in kund for p in (r['l4'].get('platser') or [])
                        if p.get('typ') == 'produkt' and p.get('har'))
    grepp = Counter((las.get(r['id']) or {}).get('grepp') or (las.get(r['id']) or {}).get('mekanik') for r in kund)
    grepp.pop(None, None)
    samma_typ = [r for r in kund if typ(r['l4']) == ty]

    fingrar = []
    for namn, (etikett, enhet, f, ned, upp, hur) in FINGRAR.items():
        v = f(k)
        kv = [x for x in (f(r) for r in kund) if x is not None]
        tv = [x for x in (f(r) for r in kohort) if x is not None]
        if v is None or len(kv) < 4 or len(tv) < 15:
            continue
        p10, p90 = float(np.percentile(tv, 10)), float(np.percentile(tv, 90))
        km = float(np.median(kv))
        mal = min(max(km, min(p10, v)), max(p90, v))      # kundens värde, hållet inom typen
        d = mal - float(v)
        sp = max(p90 - p10, 1e-9)
        fingrar.append({'finger': namn, 'etikett': etikett, 'klippet': round(float(v), 2), 'kunden': round(km, 2),
                        'kundens_klipp': len(kv), 'typen': [round(p10, 2), round(p90, 2)], 'forslag': round(mal, 2),
                        'flytt': round(d, 2), 'riktning': None if abs(d) < 0.15 * sp else (upp if d > 0 else ned),
                        'stoppad_av_typen': abs(mal - km) > 1e-6, 'hur': hur})

    # takterna
    kundrum = [x for x, _ in rum.most_common(2)]
    kundprod = [x for x, _ in produkter.most_common(6)]
    takter = []
    for i, b in enumerate(l4.get('beats') or []):
        bu = b.get('bunden')
        rad = {'nr': i + 1, 'vad': b.get('vad'), 'funktion': b.get('funktion'), 'bar': BAR.get(b.get('bar'), b.get('bar')),
               'bunden': bu, 'cm': BUNDEN.get(bu, '?')}
        if bu == 'produkt':
            rad['kundens'] = 'produkter kunden redan visar: ' + ', '.join(kundprod[:4]) if kundprod else 'kunden har inga produkter i banken'
        elif bu == 'lokal':
            rad['kundens'] = 'kunden filmar oftast i: ' + ', '.join(kundrum)
        takter.append(rad)
    platser = [{'plats': p.get('plats'), 'har': p.get('har'), 'typ': p.get('typ'),
                'kundens': (', '.join(kundprod[:3]) if p.get('typ') == 'produkt' else
                            ', '.join(kundrum) if p.get('typ') == 'lokal' else 'skrivs av CM')} for p in l4.get('platser') or []]

    # har kunden gjort något liknande, och hur ser idén ut i kundens sorts rum?
    egna = sorted(((rang(nar(kid, r['id'])), r) for r in kund), key=lambda z: -z[0])[:3]
    kallrum = set((l4.get('krav') or {}).get('lokal') or [])
    annan_scen = sorted(((rang(nar(kid, r['id'])), r) for r in R.values()
                         if r['id'] != kid and r.get('konto') not in (konto, k.get('konto'))
                         and set((r['l4'].get('krav') or {}).get('lokal') or []) & set(kundrum[:1])
                         and not set((r['l4'].get('krav') or {}).get('lokal') or []) & kallrum
                         and (typ(r['l4']) == ty or ((las.get(r['id']) or {}).get('grepp') or 0) == (las.get(kid) or {}).get('grepp'))
                         and ((r['l4'].get('grundvarde') or {}).get('hylla')) in ('karna', 'mitten')),
                        key=lambda z: -z[0])[:4]
    kort = lambda s, r: {'tema': round(s, 2), 'id': r['id'], 'url': r['l4'].get('url'), 'karna': r['l4'].get('karna'),
                         'rum': (r['l4'].get('krav') or {}).get('lokal'), 'typ': typnamn(typ(r['l4'])),
                         'lasning': las.get(r['id'])}

    ut = {'anpassa': 'anpassa/0', 'klipp': kid, 'kund': konto, 'karna': l4.get('karna'), 'mall': l4.get('mall'),
          'typ': typnamn(ty), 'lasning': las.get(kid),
          'kundens_linje': {'kort_i_banken': len(kund), 'typer': dict(typer.most_common(5)),
                            'andel_av_samma_typ': round(len(samma_typ) / len(kund), 2), 'rum': dict(rum.most_common(4)),
                            'produkter': kundprod, 'grepp_och_mekanik': dict(grepp.most_common(5))},
          'fingrar': fingrar, 'takter': takter, 'platser': platser,
          'kunden_har_redan': [kort(s, r) for s, r in egna],
          'iden_i_kundens_sorts_rum': [kort(s, r) for s, r in annan_scen],
          'kallans_rum': sorted(kallrum), 'anpassningsrisk': l4.get('anpassningsrisk')}
    namn = f'anpassa_{kid}__{konto}'
    (UT / f'{namn}.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')

    L = [f'# Anpassa: {kid} → @{konto}', '', f"**Klippet:** {l4.get('karna')}", '',
         f"**Typ:** {ut['typ']}. **Läsning:** {lasningstext(las.get(kid))}.", '',
         '## Kundens linje (ur kundens egna klipp i banken)', '',
         f"- {len(kund)} kort. {int(round(100 * len(samma_typ) / len(kund)))} % är av samma typ som klippet.",
         '- Vanligaste typer: ' + '; '.join(f'{a} ({n})' for a, n in typer.most_common(3)) + '.',
         '- Rum: ' + ', '.join(f'{a} ({n})' for a, n in rum.most_common(4)) + '.',
         '- Visar: ' + (', '.join(kundprod) or '–') + '.',
         '- Grepp och skämt kunden använt: ' + (', '.join(f"{str(a).replace('_', ' ')} ({n})" for a, n in grepp.most_common(5)) or '–') + '.', '',
         '## Fingrarna: härifrån, dit', '',
         '| finger | klippet | kunden brukar | typen tål | förslag | riktning |', '|---|---|---|---|---|---|']
    for x in fingrar:
        L.append(f"| {x['etikett']} | {x['klippet']} | {x['kunden']} | {x['typen'][0]} – {x['typen'][1]} | {x['forslag']}"
                 f"{' (stoppad av typen)' if x['stoppad_av_typen'] else ''} | {x['riktning'] or 'ligger rätt'} |")
    L += ['', '## Takterna', '', '| nr | takt | bär | bunden till | CM | kundens |', '|---|---|---|---|---|---|']
    for x in takter:
        L.append(f"| {x['nr']} | {x['vad']} | {x['bar']} | {x['bunden']} | {x['cm']} | {x.get('kundens', '')} |")
    if platser:
        L += ['', '## Platserna i mallen', '', '| plats | har nu | sort | kundens |', '|---|---|---|---|']
        L += [f"| {p['plats']} | {p['har']} | {p['typ']} | {p['kundens']} |" for p in platser]
    L += ['', '## Har kunden redan gjort något liknande?', '']
    L += [f"- tema {x['tema']}: [{x['id']}]({x['url']}). {x['karna']} ({x['typ']})" for x in ut['kunden_har_redan']]
    L += ['', f"## Samma idé i kundens sorts rum ({', '.join(kundrum[:1])} i stället för {', '.join(sorted(kallrum)) or '–'})", '',
          'Klipp från andra konton av samma typ eller med samma grepp, nära i tema, men inspelade i ett sådant rum som kunden har och inte i källans. De visar hur idén har burits där.', '']
    L += [f"- tema {x['tema']}: [{x['id']}]({x['url']}). {x['karna']} (rum: {', '.join(x['rum'] or [])})" for x in ut['iden_i_kundens_sorts_rum']]
    if l4.get('anpassningsrisk'):
        L += ['', f"**Risk vid anpassning (ur kortet):** {l4['anpassningsrisk']}"]
    (UT / f'{namn}.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
