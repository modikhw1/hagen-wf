"""Ett steg i slingan: mening → Jev → spärrar → drag → följder. Används av regibordet (bord.py).

Samma regler som regi.py, men som en funktion per steg, så att en yta kan anropa den och svara på motfrågor.
"""
import json
import time
import urllib.request
from pathlib import Path

import forstand as fs
import tillstand as ts

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'
TROSKEL = 0.4
PRIS = 0.04 / 1e6
UTGANG = ('manus', 'scenlagret', 'ingen_passar')
PARAMDRAG = ('byt_lokal', 'byt_upplagg', 'byt_produkt')
UTGANGSTEXT = {'manus': 'Det här är manus: vad som sägs eller står i text. Uppställningen ändras inte.',
               'scenlagret': 'Det här hör till scenlagret: kropp, föremål i handen eller kamera inom en scen. Ingen ändring här.',
               'ingen_passar': 'Inget drag gör det. Ingen ändring.'}


class Jev:
    def __init__(self, tak=200):
        self.n, self.tokens, self.tak, self.key = 0, 0, tak, None
        for rad in (HERE.parents[1] / 'app' / '.env.local').read_text(encoding='utf-8').splitlines():
            if rad.startswith('TYPESAFE_API_KEY='):
                self.key = rad.split('=', 1)[1].strip()

    @property
    def usd(self):
        return round(self.tokens * PRIS, 5)

    def fraga(self, state, fragor):
        """fragor: {namn: (instruktion, kriterier)}. Ger {namn: {val, marginal, nast, topp}} och ms."""
        if not self.key:
            raise RuntimeError('ingen nyckel')
        self.n += 1
        if self.n > self.tak:
            raise RuntimeError('tak för Jev-anrop nått')
        q = {n: {'type': 'choice', 'instructions': i, 'criteria': k} for n, (i, k) in fragor.items()}
        req = urllib.request.Request('https://api.typesafe.ai/v1/systemone',
                                     data=json.dumps({'model': 'jev-latest', 'state': state, 'questions': q}).encode(),
                                     headers={'Authorization': f'Bearer {self.key}', 'Content-Type': 'application/json',
                                              'User-Agent': 'regi/0'})
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.loads(r.read())
        ms = round((time.perf_counter() - t0) * 1000)
        self.tokens += (j.get('usage') or {}).get('input_tokens', 0)
        ut = {'ms': ms}
        for n in fragor:
            a = j['answers'][n]
            pr = a.get('probabilities') or {}
            andra = sorted(((k, v) for k, v in pr.items() if k != a['choice']), key=lambda z: -z[1])
            ut[n] = {'val': a['choice'], 'marginal': round(pr.get(a['choice'], 0) - andra[0][1], 2) if andra else None,
                     'nast': andra[0][0] if andra else None}
        return ut


def ladda(kid, kund=None):
    ryggrad = json.loads((UT / f'ryggrad_{kid}.json').read_text(encoding='utf-8'))
    kundinfo = None
    f = UT / f'anpassa_{kid}__{kund}.json'
    if kund and f.exists():
        a = json.loads(f.read_text(encoding='utf-8'))
        kundinfo = {'konto': kund, 'produkt': (a['kundens_linje']['produkter'] or [None])[0],
                    'rum': next(iter(a['kundens_linje']['rum']), None)}
    return ryggrad, kundinfo


def utfor(s, drag, ryggrad, kundinfo, param=None):
    """Utför ett drag utan att fråga Jev (svar på en motfråga, eller ett klick)."""
    if drag in UTGANG:
        return s, {'utfall': drag, 'rader': [UTGANGSTEXT[drag]], 'langsam': 'auto' if drag == 'ingen_passar' else 'knapp'}
    larda = fs.larda_for(s)
    if drag in larda:
        return fs.utfor_lart(s, larda[drag], ryggrad, kundinfo)
    ny, logg = ts.tillampa(s, drag, ryggrad, param=param, kund=kundinfo)
    if not logg['utfort']:
        return s, {'utfall': 'stoppat', 'rader': ['Stoppat: ' + logg['stopp'] + '.']}
    return ny, {'utfall': 'utfort', 'rader': ['Ändrat: ' + '; '.join(logg['andrat']) + '.'], 'foljder': logg['foljder']}


def _langsam(svar, vag):
    """Märker svaret: den långsamma vägen (förståndet) tar vid, direkt ('auto') eller om CM ber om det ('knapp')."""
    svar['langsam'] = vag
    return svar


def steg(s, mening, ryggrad, kundinfo, jev, avsikt=None):
    """Ger (nytt tillstånd, svar). svar har utfall, rader, foljder, jev och ibland val (motfråga).

    Lärda drag (forstand.py) står bland valen. När inget drag passar märks svaret 'langsam', och ytan
    skickar meningen vidare till förståndet.
    """
    larda = fs.larda_for(s)
    drag = ts.lagliga_drag(s, ryggrad)
    sist = {k: drag.pop(k) for k in UTGANG}
    drag = drag | {k: v['fras'] for k, v in larda.items()} | sist
    state = ts.tillstandstext(s)
    if kundinfo:
        state += f"\nKunden är @{kundinfo['konto']}: filmar oftast i {kundinfo['rum']}, visar {kundinfo['produkt']}."
    if avsikt:
        state += f'\nCM:s avsikt med passet: {avsikt}'
    state += f'\n\nCM skriver: "{mening}"'
    j = jev.fraga(state, {'q': ('En content manager vill ändra klippet. Välj det enda drag som bäst gör det meningen ber om. '
                                'Välj ingen_passar om inget drag gör det.', drag)})
    a = j['q']
    val, nast = a['val'], a['nast']
    svar = {'mening': mening, 'jev': {'val': val, 'marginal': a['marginal'], 'nast': nast, 'ms': j['ms'], 'antal_drag': len(drag)},
            'rader': [], 'foljder': []}
    osaker = a['marginal'] is not None and a['marginal'] < TROSKEL
    if osaker and val not in UTGANG + PARAMDRAG and nast not in UTGANG + PARAMDRAG and not (val in larda or nast in larda):
        a1, _ = ts.tillampa(s, val, ryggrad, kund=kundinfo)
        a2, _ = ts.tillampa(s, nast, ryggrad, kund=kundinfo)
        if a1['takter'] == a2['takter'] and a1['klipptakt'] == a2['klipptakt'] and a1.get('kontrast') == a2.get('kontrast'):
            osaker = False
            svar['rader'].append(f'Liten marginal, men {val} och {nast} ger samma ändring här.')
    if osaker and val in UTGANG and nast in UTGANG:
        svar['utfall'] = 'utanfor'
        svar['rader'].append('Utanför ryggraden (manus eller scenlagret). Uppställningen ändras inte.')
        return s, _langsam(svar, 'knapp')
    if osaker:
        svar['utfall'] = 'osaker'
        svar['rader'].append('Jag är inte säker. Vilket menar du?')
        svar['val'] = [{'drag': d, 'text': drag[d]} for d in (val, nast)] + [{'drag': 'ingen_passar', 'text': 'Inget av dem.'}]
        return s, _langsam(svar, 'knapp')
    if val in UTGANG:
        svar['utfall'] = val
        svar['rader'].append(UTGANGSTEXT[val])
        return s, _langsam(svar, 'auto' if val == 'ingen_passar' else 'knapp')
    if val in larda:
        ny, u = fs.utfor_lart(s, larda[val], ryggrad, kundinfo)
        svar.update(utfall=u['utfall'], foljder=u['foljder'], lart=u.get('lart'))
        svar['rader'] += u['rader']
        return ny, svar
    param = None
    if val == 'byt_upplagg':
        alt = {x.get('grepp') or x.get('mekanik'): x for x in ryggrad['byta_grepp']}
        j2 = jev.fraga(state, {'q': ('Vilket upplägg ber meningen om?',
                                     {k: k.replace('_', ' ') for k in alt} | {'oklart': 'Meningen säger inte vilket.'})})
        svar['jev']['ms'] += j2['ms']
        svar['utfall'] = 'hanvisning'
        v = j2['q']['val']
        if v in alt:
            e = alt[v]
            svar['rader'].append(f"Nytt upplägg ({v.replace('_', ' ')}) är ett annat klipp, inte ett drag. Närmaste i tema:")
            svar['lank'] = {'id': e['id'], 'url': e['url'], 'karna': e['karna']}
        else:
            svar['rader'].append('Nytt upplägg, men oklart vilket: ' + ', '.join(k.replace('_', ' ') for k in alt) + '.')
        return s, svar
    if val == 'byt_lokal':
        j2 = jev.fraga(state, {'q': ('Vart ska scenen flyttas?', ts.STALLEN | {'oklart': 'Meningen säger inte vart.'}),
                               'vilka': ('Vilka takter ska flyttas?', {
                                   'forsta': 'Bara den första takten, början av klippet.', 'sista': 'Bara den sista takten, slutet.',
                                   'alla_fria': 'Alla takter som inte är bundna till produkten, eller meningen säger inte vilka.',
                                   'alla': 'Hela klippet, alla takter.'})})
        svar['jev']['ms'] += j2['ms']
        vart = j2['q']['val'] if j2['q']['val'] in ts.STALLEN else (ts.RUM_TILL_STALLE.get(kundinfo['rum']) if kundinfo else None)
        if not vart:
            svar['utfall'] = 'osaker'
            svar['rader'].append('Vart ska det flyttas?')
            svar['val'] = [{'drag': 'byt_lokal', 'param': [k, j2['vilka']['val']], 'text': v} for k, v in ts.STALLEN.items()]
            return s, svar
        param = (vart, j2['vilka']['val'])
    if val == 'byt_produkt':
        j2 = jev.fraga(state, {'q': ('Vilken produkt ska in?', {
            'ur_meningen': 'Meningen nämner själv vilken produkt det ska vara.',
            'kundens': 'Meningen nämner ingen produkt: ta den kunden brukar visa.'})})
        svar['jev']['ms'] += j2['ms']
        param = f'ur meningen: "{mening}"' if j2['q']['val'] == 'ur_meningen' else None
    ny, u = utfor(s, val, ryggrad, kundinfo, param=param)
    svar.update(utfall=u['utfall'], foljder=u.get('foljder', []))
    svar['rader'] += u['rader']
    return ny, svar
