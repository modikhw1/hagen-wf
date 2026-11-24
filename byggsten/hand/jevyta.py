"""Jev-ytan: ryggraden som tillstånd plus en sluten lista av lagliga drag.

Jev väljer ett drag per CM-mening (Choice bland hela drag, det som fungerade bäst i forvarld/jevprov).
Dragen kommer ur ryggraden: fingrar med räckvidd åt ett håll, takter som får strykas eller kortas,
takter som är bundna till produkt eller lokal, byte av grepp, och två utgångar:
  manus         meningen kräver ny text, det är den långsamma vägens sak
  scenlagret    meningen gäller kropp, föremål i handen eller kamera inom en scen: liggarens och förvärldens sak
  ingen_passar  inget drag här gör det CM ber om
Kör: python jevyta.py <id>      Skriver ut/jev_<id>.json
"""
import json
import sys
from pathlib import Path

UT = Path(__file__).resolve().parent / 'ut'

FRAS = {'langd': ('Gör klippet kortare.', 'Gör klippet längre.'),
        'takter': ('Färre scener.', 'Fler scener.'),
        'klipptakt': ('Lugnare klippning, färre klipp.', 'Tätare klippning, fler klipp.'),
        'person': ('Mindre av personen i bild.', 'Mer av personen i bild.'),
        'mat': ('Mindre mat och dryck i bild.', 'Mer mat och dryck i bild.'),
        'lokal': ('Tätare bild, mindre av lokalen.', 'Visa mer av lokalen.'),
        'text': ('Mindre text på skärmen.', 'Mer text på skärmen.'),
        'promo': ('Mindre säljande: tona ned erbjudande och uppmaning.', 'Mer säljande: lyft erbjudande och uppmaning.'),
        'personer': ('Färre personer i bild.', 'Fler personer i bild.'),
        'skadespel': ('Lättare att spela för personalen.', None),
        'produktion': ('Enklare att spela in och klippa.', None)}


def main():
    kid = sys.argv[1]
    r = json.loads((UT / f'ryggrad_{kid}.json').read_text(encoding='utf-8'))
    drag = {}
    for f in r['fingrar']:
        if 'saknas' in f or f['finger'] not in FRAS:
            continue
        for h, fras in zip(('ned', 'upp'), FRAS[f['finger']]):
            alltid = f['finger'] == 'langd' and h == 'ned' and r['golv']['takter_min'] < r['golv']['takter_nu']
            if fras and (alltid or f[h]['rackvidd'] >= 0.25 * f['spann']):
                drag[f"{f['finger']}_{h}"] = fras
    for t in r['takter']:
        if t['bar'] == 'kan strykas':
            drag[f"takt{t['nr']}_stryk"] = f"Ta bort takt {t['nr']}: {t['vad']}"
        if t['bar'] == 'kan kortas':
            drag[f"takt{t['nr']}_korta"] = f"Korta takt {t['nr']}: {t['vad']}"
    if any(t['bunden'] == 'produkt' for t in r['takter']) or any(p['typ'] == 'produkt' for p in r['platser']):
        drag['byt_produkt'] = 'Byt produkten som visas mot kundens egen, filmad på samma sätt.'
    drag['byt_lokal'] = 'Flytta scenen till en annan plats eller ett annat rum.'
    if r.get('byta_grepp'):
        drag['byt_upplagg'] = 'Behåll ämnet men byt upplägg för hela klippet, till exempel provsmakning, tillagning eller en utmaning i stället.'
    drag['manus'] = 'Skriv om vad som sägs eller står i text (pris, replik, erbjudande), utan att ändra upplägget.'
    drag['scenlagret'] = 'Ändra hur en person rör sig, håller något eller ser ut, eller hur kameran rör sig, inom en scen. Det hör till scenlagret och inte hit.'
    drag['ingen_passar'] = 'Inget av dragen gör det som efterfrågas.'

    rader = [f"Klipp av typen: {r['typ']}.", f"Kärna: {r['karna']}", f"Mall: {r['mall']}", 'Takter:']
    rader += [f"  takt {t['nr']} ({t['funktion']}, {t['bar']}, bunden till {t['bunden']}): {t['vad']}" for t in r['takter']]
    rader += ['Platser i mallen: ' + '; '.join(f"{p['plats']} = {p['har']} ({p['typ']})" for p in r['platser'])]
    rader += ['Läge: ' + '; '.join(f"{f['etikett']} {f['varde']}" for f in r['fingrar'] if 'saknas' not in f)]
    ut = {'id': kid, 'state': '\n'.join(rader),
          'questions': {'drag': {'type': 'choice',
                                 'instructions': 'En content manager vill ändra klippet. Välj det enda drag som bäst gör det meningen ber om. '
                                                 'Välj ingen_passar om inget drag gör det.',
                                 'criteria': drag}}}
    (UT / f'jev_{kid}.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(ut['state']), 'tecken tillstånd,', len(drag), 'drag')
    for k, v in drag.items():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
