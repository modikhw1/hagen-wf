"""Ryggraden: ett klipp i mitten, fingrar utåt.

Ingen linje mellan två klipp. Frågan är: vilken typ av innehåll är klippet, vad i det är ryggrad
(ska stå kvar), och i vilka riktningar brukar klipp av samma typ skilja sig åt? Skillnaderna inom
typen är det ändringsrum en CM kan röra sig i. Varje finger har en räckvidd 0..x åt varje håll,
mätt i bankens klipp av samma typ, och ett riktigt klipp som visar hur det ser ut där.

Typen sätts ur formatkortet: strategi + tilltal + om produkten visas.
Kör: python ryggrad.py <id> [<id> ...]      Skriver ut/ryggrad_<id>.json och .md
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'

STRATEGI = {'tilltal': 'tilltal', 'sketchvarld': 'sketch', 'visning': 'visning', 'kampanj': 'kampanj',
            'trend': 'trend', 'premium_stamning': 'stämning'}
TILLTAL = {'till_kamera': 'till kameran', 'spelad_scen': 'spelad scen', 'inget': 'utan tilltal', 'berattarrost': 'berättarröst'}

# Vad CM gör med en takt, efter vad den är bunden till och vad den bär.
BUNDEN = {
    'produkt': 'byt till kundens produkt, filma på samma sätt',
    'lokal': 'placera i kundens lokal (här går lokalens mått in)',
    'person': 'kräver rätt person: tillåt, tvinga inte',
    'redigering': 'behåll mallen: klipp, text och ljud',
    'trend': 'trendberoende: byt ljud eller stryk',
    'ingen': 'fritt: manus och bild kan skrivas om',
}
BAR = {'karna': 'ryggrad', 'stod': 'kan kortas', 'fri': 'kan strykas'}


def typ(l4):
    sp = l4.get('sprak') or {}
    b = l4.get('beats') or []
    vis = any(x.get('funktion') == 'visning' for x in b) or sum(x.get('bunden') == 'produkt' for x in b) / max(1, len(b)) >= 0.34
    return (sp.get('strategi'), sp.get('tilltal'), vis)


def typnamn(t):
    return f"{STRATEGI.get(t[0], t[0])}, {TILLTAL.get(t[1], t[1])}, {'med' if t[2] else 'utan'} visning av produkt"


def andel(b, nyckel, varde):
    return sum(x.get(nyckel) == varde for x in b) / max(1, len(b))


# finger: (etikett, enhet, funktion, lägre betyder, högre betyder, hur CM flyttar dit)
def _l3(k, d=1):
    return lambda r: None if 'l3' not in r else r['l3'][k] / d


FINGRAR = {
    'langd': ('längd', 's', lambda r: (r.get('l5') or {}).get('langd') or (r.get('l1') or {}).get('langd'),
              'kortare', 'längre', 'stryk eller lägg till takter som inte är ryggrad'),
    'takter': ('antal takter', 'st', lambda r: len(r['l4'].get('beats') or []) or None,
               'färre scener', 'fler scener', 'stryk stöd och fria takter, eller upprepa visningen'),
    'klipptakt': ('klipp per 10 s (mätt)', '', lambda r: None if not (r.get('l5') or {}).get('langd') else
                  r['l5']['byten'] / r['l5']['langd'] * 10, 'lugnare klippning', 'tätare klippning',
                  'slå ihop eller dela tagningar, mallen styr'),
    'person': ('person i bild', '0–1', _l3('andel_person', 4), 'mindre person', 'mer person', 'byt visning mot tilltal eller tvärtom'),
    'mat': ('mat i bild', '0–1', _l3('mat_andel', 4), 'mindre mat', 'mer mat', 'lägg till eller stryk visningstakter'),
    'lokal': ('lokalen i bild', '0–1', _l3('lokal', 3), 'tätare bild', 'mer av lokalen', 'ändra utsnitt, eller flytta scenen i rummet'),
    'text': ('skärmtext', '0–1', _l3('skarmtext', 3), 'mindre text', 'mer text', 'flytta poängen mellan replik och text'),
    'promo': ('erbjudande och uppmaning', '0–1', lambda r: None if 'l3' not in r else
              (r['l3']['erbjudande'] + r['l3']['uppmaning']) / 2, 'mindre säljande', 'mer säljande',
              'skriv in kundens promo i en fri takt, inte i ryggraden'),
    'personer': ('personer i bild', 'st', _l3('personer'), 'färre personer', 'fler personer', 'lägg till eller ta bort en roll'),
    'bundet_produkt': ('takter bundna till produkten', 'andel', lambda r: andel(r['l4'].get('beats') or [], 'bunden', 'produkt'),
                       'mindre produktbundet', 'mer produktbundet', 'byt vilka takter som visar produkten'),
    'bundet_lokal': ('takter bundna till lokalen', 'andel', lambda r: andel(r['l4'].get('beats') or [], 'bunden', 'lokal'),
                     'mindre platsbundet', 'mer platsbundet', 'knyt takter till kundens rum'),
    'skadespel': ('krav på skådespel', '1–5', lambda r: (r['l4'].get('krav') or {}).get('skadespel'),
                  'lättare att spela', 'svårare att spela', 'förenkla eller bygg ut repliker och reaktioner'),
    'produktion': ('krav på produktion', '1–5', lambda r: (r['l4'].get('krav') or {}).get('produktion'),
                   'enklare att göra', 'mer produktion', 'ta bort eller lägg till effekter och specialbilder'),
}


def main():
    R = {}
    for line in open(UT / 'klipp.jsonl', encoding='utf-8'):
        r = json.loads(line)
        if 'l4' in r:
            R[r['id']] = r
    t = np.load(UT / 'tema.npz')
    tix = {str(x): i for i, x in enumerate(t['ids'])}
    V = t['V']

    for kid in sys.argv[1:]:
        k = R[kid]
        l4 = k['l4']
        ty = typ(l4)
        kohort = [r for r in R.values() if typ(r['l4']) == ty and r['id'] != kid]
        beats = l4.get('beats') or []

        takter = [{'nr': i + 1, 'vad': b.get('vad'), 'funktion': b.get('funktion'), 'bar': BAR.get(b.get('bar'), b.get('bar')),
                   'bunden': b.get('bunden'), 'cm': BUNDEN.get(b.get('bunden'), '?')} for i, b in enumerate(beats)]
        ryggrad = [x['nr'] for x in takter if x['bar'] == 'ryggrad']
        platser = [{'plats': p.get('plats'), 'har': p.get('har'), 'typ': p.get('typ')} for p in l4.get('platser') or []]

        fingrar = []
        for namn, (etikett, enhet, f, ned, upp, hur) in FINGRAR.items():
            v = f(k)
            ks = [(f(r), r) for r in kohort]
            ks = [(x, r) for x, r in ks if x is not None]
            if v is None or len(ks) < 15:
                fingrar.append({'finger': namn, 'etikett': etikett, 'varde': v, 'saknas': 'klippet eller kohorten saknar underlag',
                                'n': len(ks)})
                continue
            xs = np.array([x for x, _ in ks], float)
            p10, p50, p90 = (float(np.percentile(xs, q)) for q in (10, 50, 90))
            karna = [x for x, r in ks if ((r['l4'].get('grundvarde') or {}).get('hylla')) == 'karna']
            ovr = [x for x, r in ks if ((r['l4'].get('grundvarde') or {}).get('hylla')) in ('ute', 'mitten')]

            def exempel(test):
                c = [(float(V[tix[r['id']]] @ V[tix[kid]]), r) for x, r in ks if test(x)
                     and ((r['l4'].get('grundvarde') or {}).get('hylla')) in ('karna', 'mitten')]
                if not c:
                    return None
                s, r = max(c, key=lambda z: z[0])
                return {'id': r['id'], 'url': r['l4'].get('url'), 'varde': round(float(f(r)), 2), 'karna': r['l4'].get('karna')}

            sp = max(p90 - p10, 1e-9)
            fingrar.append({
                'finger': namn, 'etikett': etikett, 'enhet': enhet, 'varde': round(float(v), 2), 'n': len(ks),
                'typen': {'p10': round(p10, 2), 'median': round(p50, 2), 'p90': round(p90, 2)},
                'plats_i_typen': round(float((xs < v).mean()), 2),
                'ned': {'vad': ned, 'rackvidd': round(max(0.0, float(v) - p10), 2), 'exempel': exempel(lambda x: x <= min(p10 + 0.25 * sp, v - 1e-9))},
                'upp': {'vad': upp, 'rackvidd': round(max(0.0, p90 - float(v)), 2), 'exempel': exempel(lambda x: x >= max(p90 - 0.25 * sp, v + 1e-9))},
                'hur': hur,
                'karnklippen': None if len(karna) < 8 or len(ovr) < 8 else
                {'median_karna': round(float(np.median(karna)), 2), 'median_ovriga': round(float(np.median(ovr)), 2)},
                'spann': round(sp, 2)})

        # golv för längd och takter ur klippet självt: bara ryggraden kvar
        golv = {'takter_min': len(ryggrad), 'takter_nu': len(beats),
                'kan_strykas': [x['nr'] for x in takter if x['bar'] == 'kan strykas'],
                'kan_kortas': [x['nr'] for x in takter if x['bar'] == 'kan kortas']}

        ut = {'ryggrad': 'ryggrad/0', 'id': kid, 'url': l4.get('url'), 'karna': l4.get('karna'), 'mall': l4.get('mall'),
              'typ': typnamn(ty), 'kohort': len(kohort), 'takter': takter, 'ryggradstakter': ryggrad, 'golv': golv,
              'platser': platser, 'fingrar': fingrar,
              'forlaga': l4.get('forlaga'), 'anpassningsrisk': l4.get('anpassningsrisk')}
        # byta grepp: samma ämne, annat sätt att bära det (ur läsningen, där den finns)
        las = json.loads((UT / 'lasning.json').read_text(encoding='utf-8')) if (UT / 'lasning.json').exists() else {}
        egen = las.get(kid) or {}
        falt = 'grepp' if 'grepp' in egen else ('mekanik' if 'mekanik' in egen else None)
        byten = []
        if falt:
            gr = sorted(((float(V[tix[r['id']]] @ V[tix[kid]]), r) for r in R.values()
                         if r['id'] != kid and (las.get(r['id']) or {}).get(falt) not in (None, egen[falt])
                         and ((r['l4'].get('grundvarde') or {}).get('hylla')) in ('karna', 'mitten')), key=lambda z: -z[0])
            sedda = set()
            for s_, r in gr:
                g = las[r['id']][falt]
                if g in sedda:
                    continue
                sedda.add(g)
                byten.append({falt: g, 'id': r['id'], 'url': r['l4'].get('url'), 'karna': r['l4'].get('karna'), 'cos': round(s_, 3)})
                if len(byten) == 9:   # alla andra värden, så att inget upplägg saknas när CM frågar efter det
                    break
        ut['lasning'] = egen
        ut['byta_grepp'] = byten
        (UT / f'ryggrad_{kid}.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')

        # läsbar rapport
        L = [f"# Ryggrad: {kid}", '', f"**Typ:** {ut['typ']} ({len(kohort)} andra klipp av samma typ i banken)", '',
             f"**Kärna:** {l4.get('karna')}", '', f"**Mall:** {l4.get('mall')}", '', '## Takterna: vad som står kvar och vad CM gör', '',
             '| nr | takt | funktion | bär | bunden till | CM |', '|---|---|---|---|---|---|']
        for x in takter:
            L.append(f"| {x['nr']} | {x['vad']} | {x['funktion']} | {x['bar']} | {x['bunden']} | {x['cm']} |")
        L += ['', f"Ryggraden är takt {', '.join(map(str, ryggrad)) or '–'}. Kortaste versionen har {golv['takter_min']} av {golv['takter_nu']} takter.", '']
        if platser:
            L += ['## Platserna i mallen: det som byts mot kundens', '', '| plats | har nu | sort |', '|---|---|---|']
            L += [f"| {p['plats']} | {p['har']} | {p['typ']} |" for p in platser] + ['']
        L += ['## Fingrarna: hur långt klipp av samma typ går åt varje håll', '',
              '| finger | klippet | typen (p10 – median – p90) | ned: räckvidd | upp: räckvidd | kärnklippen ligger |', '|---|---|---|---|---|---|']
        for x in fingrar:
            if 'saknas' in x:
                continue
            kk = x['karnklippen']
            kt = '–' if not kk else ('högre' if kk['median_karna'] > kk['median_ovriga'] + 0.1 * x['spann'] else
                                     'lägre' if kk['median_karna'] < kk['median_ovriga'] - 0.1 * x['spann'] else 'lika')
            L.append(f"| {x['etikett']} | {x['varde']} | {x['typen']['p10']} – {x['typen']['median']} – {x['typen']['p90']} | "
                     f"{x['ned']['vad']}: {x['ned']['rackvidd']} | {x['upp']['vad']}: {x['upp']['rackvidd']} | {kt} |")
        sakn = [x['etikett'] for x in fingrar if 'saknas' in x]
        if sakn:
            L += ['', 'Utan underlag för det här klippet eller den här typen: ' + ', '.join(sakn) + '.']
        L += ['', '## Dit kan det gå: närmaste klipp i tema som redan ligger där', '']
        for x in fingrar:
            if 'saknas' in x:
                continue
            for h in ('ned', 'upp'):
                e = x[h]['exempel']
                if e and x[h]['rackvidd'] >= 0.25 * x['spann']:
                    L.append(f"- **{x[h]['vad']}** ({x['etikett']} {x['varde']} → {e['varde']}): [{e['id']}]({e['url']}). {e['karna']} *Så flyttar man: {x['hur']}.*")
        if byten:
            L += ['', f"## Samma ämne, annat {falt}", '',
                  f"Klippet är läst som: {', '.join(f'{a} {str(b).replace(chr(95), chr(32))}' for a, b in egen.items())}. "
                  f"Närmaste klipp i tema för varje annat {falt}:", '']
            L += [f"- **{str(x[falt]).replace('_', ' ')}**: [{x['id']}]({x['url']}). {x['karna']}" for x in byten]
        if l4.get('anpassningsrisk'):
            L += ['', f"**Risk vid anpassning (ur kortet):** {l4['anpassningsrisk']}"]
        (UT / f'ryggrad_{kid}.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
        print(kid, '|', ut['typ'], '| kohort', len(kohort), '| fingrar med underlag', sum('saknas' not in x for x in fingrar))


if __name__ == '__main__':
    main()
