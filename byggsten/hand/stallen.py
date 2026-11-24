"""Ställen: scenografi på taktnivå, utvunnen ur taktbeskrivningarna i formatkorten.

Kortens fält krav.lokal säger bara vilket slags rum klippet behöver. Men varje takt har en mening
(skriven av Gemini) som ofta säger var den utspelas, hur personen håller sig och vad hen gör med
händerna. Här plockas det ut med ordlistor. Det är ord i en beskrivning, inte en läsning av bilden.

Ger: per takt (stalle, hallning, hantering), och per typ och taktfunktion hur vanligt varje ställe är.
Skriver ut/stallen.json (per klipp) och ut/stallen_typ.json. Kör efter samla.py.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from ryggrad import typ, typnamn

UT = Path(__file__).resolve().parent / 'ut'

STALLE = [
    ('bakom_disk', r'bakom (disken|kassan|baren|bardisken)'),
    ('utanfor', r'utanför|entrén|\bentré|på gatan|trottoar|på stan|i dörren|dörröppning|skylten utanför|hållplats|torg'),
    ('uteservering', r'uteservering|terrass'),
    ('kok', r'\bkök|spis|grill|ugn|stekbord|fritös|bakom kulisserna|köksluck'),
    ('bar', r'\bbaren\b|bardisk|\bbar\b'),
    ('disk', r'disken|kassan|\bdisk\b|kassa'),
    ('bord', r'bordet|\bbord\b|uppdukat|sitter ner|sätter sig'),
    ('lager', r'lagret|förråd|kylrum|frys'),
    ('bil', r'\bbil(en)?\b|fordon|baksäte'),
    ('lokalen', r'genom lokalen|i lokalen|runt i lokalen|matsalen'),
]
HALLNING = [('gar', r'\bgår\b|promenerar|kliver|rusar|springer|vandrar|kommer in'), ('sitter', r'sitter|sätter sig'),
            ('ligger', r'ligger|lägger sig'), ('star', r'\bstår\b|ställer sig')]
HANTERING = [
    ('ater', r'\bäter|smakar|tuggar|dricker|sveper|tar en tugga|provsmak'),
    ('visar_upp', r'visar upp|håller upp|lyfter fram|presenterar|pekar på|visas upp'),
    ('racker', r'räcker|lämnar över|serverar|ställer fram|ger\b'),
    ('tillagar', r'tillagar|lagar|steker|grillar|häller|ringlar|lägger upp|bygger ihop|monterar|skär|skopar|spritsar'),
    ('betalar', r'betalar|blippar|kort(et|terminal)|notan'),
    ('talar', r'säger|frågar|ställer (en |samma )?fråga|svarar|ropar|berättar|förklarar|pratar|uppmanar|läser upp|annonserar'),
    ('text', r'text(en)?\b|skylt|skärmtext'),
]


def forsta(lista, s):
    for namn, mon in lista:
        if re.search(mon, s):
            return namn
    return None


def las(vad):
    s = (vad or '').lower()
    return {'stalle': forsta(STALLE, s), 'hallning': forsta(HALLNING, s),
            'hantering': [n for n, m in HANTERING if re.search(m, s)]}


def main():
    per_klipp, typ_st = {}, defaultdict(lambda: defaultdict(Counter))
    n = tr = 0
    for line in open(UT / 'klipp.jsonl', encoding='utf-8'):
        r = json.loads(line)
        if 'l4' not in r:
            continue
        ty = typnamn(typ(r['l4']))
        rader = []
        for b in r['l4'].get('beats') or []:
            x = las(b.get('vad'))
            rader.append(x)
            n += 1
            tr += x['stalle'] is not None
            typ_st[ty][b.get('funktion')][x['stalle'] or 'osagt'] += 1
        per_klipp[r['id']] = rader
    (UT / 'stallen.json').write_text(json.dumps(per_klipp, ensure_ascii=False), encoding='utf-8')
    ut = {t: {f: dict(c.most_common()) for f, c in d.items()} for t, d in typ_st.items()}
    (UT / 'stallen_typ.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{n} takter, ställe utsagt i {tr} ({100 * tr // n} %)')
    for t in ('tilltal, till kameran, med visning av produkt', 'sketch, spelad scen, utan visning av produkt'):
        print(t)
        for f, c in ut[t].items():
            tot = sum(c.values())
            sagt = {k: v for k, v in c.items() if k != 'osagt'}
            print(f'   {f} ({tot}): ' + ', '.join(f'{k} {v}' for k, v in list(sagt.items())[:5]))


if __name__ == '__main__':
    main()
