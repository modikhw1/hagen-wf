"""Spela upp en ryggrad som blockout: en bild per takt, och samma klipp flyttat mot en kund.

Uppställningen per takt kommer i den här ordningen:
  1. stället som taktens egen beskrivning nämner (stallen.py)
  2. annars samma ställe som takten före
  3. annars det ställe som typen oftast har för taktens funktion
  4. annars klippets rum ur kortet
Hållning och hantering kommer ur taktens beskrivning. Måtten är schabloner.

Kundversionen följer anpassa.py: antal takter mot kundens vanliga (stryker det som får strykas),
taktens ställe byts till kundens vanligaste rum där takten inte är bunden till produkten,
och en kollega läggs till om kunden brukar ha fler i bild. Det är ett utkast ur siffror, inget manus.

Kör: python spela.py <klipp-id> [<konto>]   Skriver ut/spela_<...>.json i brons format (för blockout.py).
"""
import json
import sys
from pathlib import Path

from stallen import las

UT = Path(__file__).resolve().parent / 'ut'
RUM_TILL_STALLE = {'disk_kassa': 'disk', 'matsal': 'bord', 'kok': 'kok', 'bar': 'bar', 'entre': 'utanfor',
                   'uteservering': 'uteservering', 'butik_hylla': 'disk', 'ingen_sarskild': 'lokalen'}


def scen(stalle, hallning, hantering, kollega=False, skylt=None):
    """Uppställning för ett ställe. Personen P är vänd mot kameran (vand 180)."""
    arm, haller = None, None
    if 'ater' in hantering:
        arm, haller = 'mun', 'lada'
    elif 'visar_upp' in hantering or 'racker' in hantering:
        arm, haller = 'fram', 'lada'
    elif 'tillagar' in hantering:
        arm = 'fram'
    elif 'talar' in hantering:
        arm = 'fram'
    p = {'id': 'P', 'roll': 'personal', 'pos': [0.0, 0.75], 'vand': 180, 'pose': 'star', 'arm': arm, 'haller': haller}
    saker, kamera = [], 'rak'
    if stalle in ('disk', 'bakom_disk', 'bar'):
        saker = [{'typ': 'disk'}, {'typ': 'bricka', 'pos': [0.55, 0.1], 'z': 0.93, 'skala': 0.8}]
        if stalle == 'bar':
            saker += [{'typ': 'hylla'}]
    elif stalle == 'kok':
        saker = [{'typ': 'disk'}, {'typ': 'spis'}, {'typ': 'trag', 'pos': [-0.5, 0.1], 'z': 0.93}]
    elif stalle in ('bord', 'uteservering'):
        p.update(pose='sitter', pos=[0.0, 0.55])
        saker = [{'typ': 'bord', 'pos': [0.0, -0.1]}, {'typ': 'bricka', 'pos': [0.0, -0.1], 'z': 0.75, 'skala': 1.0}]
        kamera = 'bordet'
    elif stalle == 'utanfor':
        p.update(pos=[0.0, 0.2])
        saker = [{'typ': 'dorr'}]
        kamera = 'ute'
    else:  # lokalen eller okänt
        p.update(pos=[0.0, 0.0])
        saker = [{'typ': 'bord', 'pos': [-1.3, 1.2]}, {'typ': 'bord', 'pos': [1.3, 1.2]}]
        kamera = 'ute'
    if hallning == 'gar':
        p['pos'] = [p['pos'][0] - 0.25, p['pos'][1] - 0.3]
        p['vand'] = 165
    personer = [p]
    if kollega:
        personer.append({'id': 'K', 'roll': 'gast_b', 'pos': [p['pos'][0] + 0.75, p['pos'][1] + 0.05], 'vand': 195, 'pose': p['pose']})
    return {'rum': stalle, 'kamera': kamera, 'personer': personer, 'saker': saker, **({'skylt': skylt} if skylt else {})}


def main():
    kid = sys.argv[1]
    konto = sys.argv[2] if len(sys.argv) > 2 else None
    r = json.loads((UT / f'ryggrad_{kid}.json').read_text(encoding='utf-8'))
    typst = json.loads((UT / 'stallen_typ.json').read_text(encoding='utf-8')).get(r['typ'], {})
    rum = None
    for line in open(UT / 'klipp.jsonl', encoding='utf-8'):
        k = json.loads(line)
        if k['id'] == kid:
            rum = ((k['l4'].get('krav') or {}).get('lokal') or [None])[0]
            break

    forra = {}

    def stalle_for(t):
        x = las(t['vad'])
        if x['stalle']:
            forra['st'] = x['stalle']
            return x, x['stalle'], 'taktens beskrivning'
        if forra.get('st'):
            return x, forra['st'], 'samma ställe som takten före'
        c = {a: b for a, b in (typst.get(t['funktion']) or {}).items() if a != 'osagt'}
        if c and max(c.values()) >= 5:
            return x, max(c, key=c.get), f"typens vanligaste ställe för {t['funktion']}"
        return x, RUM_TILL_STALLE.get(rum, 'lokalen'), 'klippets rum ur kortet'

    steg = []
    for t in r['takter']:
        x, st, kalla = stalle_for(t)
        steg.append({'t': t['nr'], 'finger': f"{t['funktion']} · {t['bar']} · bunden till {t['bunden']}", 'premiss': t['vad'],
                     'bevis': f'ställe: {st} ({kalla})', 'sprang': False, 'scen': scen(st, x['hallning'], x['hantering'])})
    namn = f'spela_{kid}'
    ut = {'bro': 'spela/0', 'klipp': kid, 'typ': r['typ'], 'steg': steg}

    if konto:
        a = json.loads((UT / f'anpassa_{kid}__{konto}.json').read_text(encoding='utf-8'))
        f = {x['finger']: x for x in a['fingrar']}
        kundrum = next(iter(a['kundens_linje']['rum']), None)
        kst = RUM_TILL_STALLE.get(kundrum, 'lokalen')
        mal_takter = round(f['takter']['forslag']) if 'takter' in f else len(r['takter'])
        kvar = list(r['takter'])
        for bar in ('kan strykas', 'kan kortas'):
            for t in reversed(list(kvar)):
                if len(kvar) > mal_takter and t['bar'] == bar:
                    kvar.remove(t)
        kollega = 'personer' in f and f['personer']['forslag'] - f['personer']['klippet'] >= 0.75
        prod = (a['kundens_linje']['produkter'] or ['kundens produkt'])[0]
        ksteg = []
        forra.clear()
        for i, t in enumerate(kvar):
            x, st, kalla = stalle_for(t)
            if t['bunden'] != 'produkt' or st in ('utanfor', 'lokalen'):
                st, kalla = kst, f'kundens vanligaste rum ({kundrum})'
            elif t['bunden'] == 'produkt':
                kalla += ', produkten byts'
            vad = t['vad'] + (f' [produkt: {prod}]' if t['bunden'] == 'produkt' else '') + (f' [flyttad till: {kundrum}]' if 'kundens' in kalla else '')
            ksteg.append({'t': i + 1, 'finger': f"{t['funktion']} · {t['bar']} · var takt {t['nr']}", 'premiss': vad,
                          'bevis': f'ställe: {st} ({kalla})', 'sprang': False,
                          'scen': scen(st, x['hallning'], x['hantering'], kollega=kollega and i == 0)})
        ut = {'bro': 'spela/0', 'klipp': kid, 'kund': konto, 'typ': r['typ'], 'steg': steg + ksteg,
              'rader': [len(steg), len(ksteg)], 'strukna_takter': [t['nr'] for t in r['takter'] if t not in kvar]}
        namn = 'spela_' + kid + '__' + konto
    (UT / (namn + '.json')).write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
    print(namn, len(ut['steg']), 'bilder')
    for s in ut['steg']:
        print('  ', s['t'], s['bevis'], '|', s['scen']['personer'][0].get('pose'), s['scen']['personer'][0].get('arm'))


if __name__ == '__main__':
    main()

