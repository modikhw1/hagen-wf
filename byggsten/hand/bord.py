"""Regibordet: en lokal yta för slingan. Ladda in ett klipp ur banken, välj kund, skriv vad som ska ändras.

Servern binder bara 127.0.0.1. Jev-nyckeln stannar här och når aldrig webbläsaren.
Uppställningen ritas i webbläsaren (three.js ur scen/3d/vendor, läses bara), så inget Blender behövs.
Ryggrad och kundanpassning räknas fram första gången ett klipp eller en kund väljs (några sekunder).
Varje pass loggas under ut/regi/bord-<tid>/.

Kör: python -X utf8 bord.py [port]      Öppna http://127.0.0.1:5197
"""
import json
import re
import subprocess
import sys
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import forstand as fs
import slinga
import tillstand as ts
from ryggrad import typ, typnamn

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'
THREE = HERE.parents[1] / 'scen' / '3d' / 'vendor' / 'three.module.js'
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5197

jev = slinga.Jev(tak=300)
forstand = fs.Forstand(tak=60)
pass_ = {'s': None, 'historik': [], 'ryggrad': None, 'kund': None, 'anpassa': None, 'logg': [], 'mapp': None,
         'avsikt': '', 'sista_jev': None}

# Banken i minnet: det som behövs för att söka.
KORT, KONTON = [], Counter()
for _rad in open(UT / 'klipp.jsonl', encoding='utf-8'):
    _r = json.loads(_rad)
    if 'l4' in _r:
        _l4 = _r['l4']
        KORT.append({'id': _r['id'], 'konto': _r.get('konto') or _r['id'].rsplit('-', 1)[0], 'karna': _l4.get('karna') or '',
                     'typ': typnamn(typ(_l4)), 'hylla': (_l4.get('grundvarde') or {}).get('hylla'),
                     'sok': ((_l4.get('karna') or '') + ' ' + (_l4.get('handling') or '')).lower()})
        KONTON[KORT[-1]['konto']] += 1
RANG = {'karna': 0, 'mitten': 1, 'situation': 2}

# Fingrar som går att nå med ett drag, och vilket drag det är åt varje håll.
FINGERDRAG = {'langd': ('langd_ned', 'langd_upp'), 'takter': ('takter_ned', 'takter_upp'), 'klipptakt': ('klipptakt_ned', 'klipptakt_upp'),
              'person': ('person_ned', 'person_upp'), 'mat': ('mat_ned', 'mat_upp'), 'lokal': ('lokal_ned', 'lokal_upp'),
              'text': ('text_ned', 'text_upp'), 'promo': ('promo_ned', 'promo_upp'), 'personer': ('personer_ned', 'personer_upp'),
              'produktion': ('produktion_ned', None)}


def sok(q, typfilter):
    ord_ = [w for w in q.lower().split() if w]
    tr = [k for k in KORT if all(w in k['sok'] or w in k['konto'] for w in ord_) and (not typfilter or k['typ'] == typfilter)]
    tr.sort(key=lambda k: (RANG.get(k['hylla'], 3), k['id']))
    return [{x: k[x] for x in ('id', 'konto', 'karna', 'typ', 'hylla')} for k in tr[:40]]


def forbered(kid, konto):
    """Räknar fram ryggrad och anpassning om de saknas. Tar några sekunder första gången."""
    if not (UT / f'ryggrad_{kid}.json').exists():
        subprocess.run([sys.executable, '-X', 'utf8', str(HERE / 'ryggrad.py'), kid], check=True, capture_output=True, cwd=HERE)
    if konto and not (UT / f'anpassa_{kid}__{konto}.json').exists():
        subprocess.run([sys.executable, '-X', 'utf8', str(HERE / 'anpassa.py'), kid, konto], check=True, capture_output=True, cwd=HERE)


def plan():
    """Dragen som flyttar klippet mot kunden, ur anpassa. Bara det som återstår och går att göra nu."""
    a, s, r = pass_['anpassa'], pass_['s'], pass_['ryggrad']
    if not a:
        return []
    lagliga = ts.lagliga_drag(s, r)
    nu = ts.nu_varden(s, r)
    ut = []
    if 'byt_produkt' in lagliga and a['kundens_linje']['produkter'] and not any('var' in p for p in s['platser'] if p['typ'] == 'produkt'):
        ut.append({'drag': 'byt_produkt', 'text': f"Byt produkten till kundens: {a['kundens_linje']['produkter'][0]}",
                   'skal': 'kunden visar det i sina egna klipp'})
    kst = ts.RUM_TILL_STALLE.get(next(iter(a['kundens_linje']['rum']), None))
    if kst and s['takter'] and all(t['stalle'] != kst for t in s['takter']) and 'byt_lokal' not in s['historik']:
        ut.append({'drag': 'byt_lokal', 'param': [kst, 'forsta'], 'text': f'Flytta första takten till {kst}',
                   'skal': f"kunden filmar oftast i {next(iter(a['kundens_linje']['rum']))}"})
    for f in a['fingrar']:
        d = FINGERDRAG.get(f['finger'])
        if not d or not f['riktning']:
            continue
        v = nu.get(f['finger'], f['klippet'])
        kvar = f['forslag'] - v
        spann = max(f['typen'][1] - f['typen'][0], 1e-9)
        if abs(kvar) < 0.15 * spann:
            continue
        drag = d[1] if kvar > 0 else d[0]
        if not drag or drag not in lagliga or (drag == 'produktion_ned' and 'produktion_ned' in s['historik']):
            continue
        if f['finger'] in ('person', 'mat', 'lokal', 'text', 'promo') and drag in s['historik']:
            continue   # går inte att läsa av tillståndet: föreslås en gång
        ut.append({'drag': drag, 'text': lagliga[drag].rstrip('.'),
                   'skal': f"{f['etikett']}: klippet {round(v, 2)}, kunden brukar {f['kunden']}"
                           + (' (längre än typen tål, stannar vid %s)' % f['forslag'] if f['stoppad_av_typen'] else '')})
    return ut


def vy():
    s, r, a = pass_['s'], pass_['ryggrad'], pass_['anpassa']
    drag = ts.lagliga_drag(s, r)
    takter = []
    for t, b in zip(s['takter'], ts.till_steg(s)):
        takter.append({'nr': t['nr'], 'vad': t['vad'], 'funktion': t['funktion'], 'bar': t['bar'], 'bunden': t['bunden'],
                       'sek': t['sek'], 'stalle': t['stalle'], 'markning': t['markning'], 'scen': b['scen']})
    nu = ts.nu_varden(s, r)
    kundv = {f['finger']: f['kunden'] for f in (a or {}).get('fingrar', [])}
    hand = []
    for f in r['fingrar']:
        if 'saknas' in f:
            continue
        d = FINGERDRAG.get(f['finger'], (None, None))
        hand.append({'finger': f['finger'], 'etikett': f['etikett'], 'original': f['varde'], 'nu': nu.get(f['finger'], f['varde']),
                     'p10': f['typen']['p10'], 'median': f['typen']['median'], 'p90': f['typen']['p90'], 'kunden': kundv.get(f['finger']),
                     'ned': d[0] if d[0] in drag else None, 'upp': d[1] if d[1] in drag else None,
                     'ned_text': f['ned']['vad'], 'upp_text': f['upp']['vad']})
    kl = (a or {}).get('kundens_linje')
    return {'klipp': s['klipp'], 'typ': s['typ'], 'karna': s['karna'], 'langd': ts.langd(s), 'takter': takter,
            'kontrast': s.get('kontrast'), 'kund': pass_['kund'], 'hand': hand, 'plan': plan(),
            'mall': r.get('mall'), 'platser': s['platser'],
            'kundens_linje': kl and {'kort': kl['kort_i_banken'], 'andel_typ': kl['andel_av_samma_typ'], 'rum': kl['rum'],
                                     'produkter': kl['produkter'][:4]},
            'kunden_har_redan': (a or {}).get('kunden_har_redan', [])[:2],
            'drag': [{'drag': k, 'text': v} for k, v in drag.items()
                     if k.startswith('takt') and not k.endswith('_skyddad') or k.startswith('kontrast')],
            'kan_angra': bool(pass_['historik']), 'jev': {'anrop': jev.n, 'usd': jev.usd},
            'avsikt': pass_['avsikt'], 'har_kropp': fs.har_kropp(s['klipp']), 'forstand': {'anrop': forstand.n, 's': round(forstand.ms / 1000, 1), 'modell': fs.MODELL},
            'larda': [{'namn': d['namn'], 'fras': d['fras'], 'galler': d['galler'], 'anvant': d.get('anvant', 0), 'mening': d['mening']}
                      for d in fs.larda_for(s).values()]}


def spara():
    if pass_['mapp']:
        (pass_['mapp'] / 'logg.json').write_text(json.dumps({'klipp': pass_['s']['klipp'], 'kund': pass_['kund'], 'avsikt': pass_['avsikt'], 'logg': pass_['logg'],
                                                             'slut': pass_['s'], 'jev_anrop': jev.n, 'usd': jev.usd},
                                                            ensure_ascii=False, indent=1), encoding='utf-8')


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def svar(self, kod, kropp, typ_='application/json; charset=utf-8'):
        b = kropp if isinstance(kropp, bytes) else json.dumps(kropp, ensure_ascii=False).encode()
        self.send_response(kod)
        self.send_header('Content-Type', typ_)
        self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == '/':
            return self.svar(200, (HERE / 'bord' / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        if u.path == '/three.module.js':
            return self.svar(200, THREE.read_bytes(), 'text/javascript; charset=utf-8')
        if u.path.startswith('/kropp/'):   # bild och film ur kroppsvägen: /kropp/<namn>/streck_blad.png eller streck.mp4
            d = u.path.split('/')
            if len(d) == 4 and d[2].startswith('bord_') and d[2][5:].isdigit() and re.fullmatch(r'(streck_blad[.]png|streck[.]mp4|forvarld[.]mp4|forvarld_r[0-9]+[.]png)', d[3]):
                f = fs.KROPPSVAG / 'ut' / f'mening_{d[2]}' / d[3]
                if f.exists():
                    return self.svar(200, f.read_bytes(), 'image/png' if d[3].endswith('.png') else 'video/mp4')
            return self.svar(404, {'fel': 'finns inte'})
        if u.path == '/favicon.ico':
            return self.svar(204, b'', 'image/x-icon')
        if u.path == '/api/sok':
            return self.svar(200, sok(q.get('q', [''])[0], q.get('typ', [''])[0]))
        if u.path == '/api/tagningar':
            return self.svar(200, [{'id': k, 'namn': v['namn']} for k, v in fs.TAGNINGAR.items()])
        if u.path == '/api/scenstatus':
            n = q.get('namn', [''])[0]
            return self.svar(200, fs.scenstatus(n) if n.startswith('bord_') and n[5:].isdigit() else {'fel': 'okänt namn'})
        if u.path == '/api/bank':
            typer = Counter(k['typ'] for k in KORT)
            return self.svar(200, {'kort': len(KORT), 'typer': [t for t, n in typer.most_common() if n >= 25],
                                   'konton': [k for k, n in sorted(KONTON.items()) if n >= 8]})
        self.svar(404, {'fel': 'finns inte'})

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        d = json.loads(self.rfile.read(n) or b'{}')
        p = self.path
        try:
            if p == '/api/start':
                t0 = time.perf_counter()
                forbered(d['klipp'], d.get('kund'))
                r, k = slinga.ladda(d['klipp'], d.get('kund'))
                af = UT / f"anpassa_{d['klipp']}__{d.get('kund')}.json"
                pass_.update(s=ts.fran_ryggrad(d['klipp']), historik=[], ryggrad=r, kund=k, logg=[], sista_jev=None,
                             avsikt=(d.get('avsikt') or '').strip(),
                             anpassa=json.loads(af.read_text(encoding='utf-8')) if d.get('kund') and af.exists() else None,
                             mapp=UT / 'regi' / time.strftime('bord-%Y%m%d-%H%M%S'))
                pass_['mapp'].mkdir(parents=True, exist_ok=True)
                return self.svar(200, {'vy': vy(), 'forberett_ms': round((time.perf_counter() - t0) * 1000)})
            if p == '/api/kropp' and d.get('tagning') in fs.TAGNINGAR:   # kroppen direkt, utan pass
                return self.svar(200, {'svar': fs.kropp(d['tagning'], d['text'].strip())})
            if p == '/api/scen':
                n = d.get('namn', '')
                return self.svar(200, {'startad': bool(n.startswith('bord_') and n[5:].isdigit() and fs.scen(n))})
            if pass_['s'] is None:
                return self.svar(400, {'fel': 'inget pass startat'})
            fore = pass_['s']
            if p == '/api/avsikt':
                pass_['avsikt'] = (d.get('text') or '').strip()
                pass_['logg'].append({'avsikt': pass_['avsikt']})
                spara()
                return self.svar(200, {'vy': vy()})
            if p == '/api/glom':
                fs.glom(d['namn'])
                return self.svar(200, {'vy': vy(), 'svar': {'utfall': 'angrat', 'rader': [f"Glömt: {d['namn']}."]}})
            if p == '/api/mening':
                ny, sv = slinga.steg(fore, d['text'].strip(), pass_['ryggrad'], pass_['kund'], jev, avsikt=pass_['avsikt'])
                pass_['sista_jev'] = sv.get('jev')
            elif p == '/api/forstand':
                ny, sv = fs.steg(fore, d['text'].strip(), pass_['ryggrad'], pass_['kund'], pass_['anpassa'], pass_['avsikt'],
                                 forstand, jevsvar=pass_['sista_jev'])
            elif p == '/api/kropp':
                if not fs.har_kropp(fore['klipp']):
                    return self.svar(400, {'fel': 'klippet har ingen läst kropp'})
                ny, sv = fore, fs.kropp(fs.KROPP[fore['klipp']], d['text'].strip())
            elif p == '/api/val':
                param = tuple(d['param']) if isinstance(d.get('param'), list) else d.get('param')
                ny, sv = slinga.utfor(fore, d['drag'], pass_['ryggrad'], pass_['kund'], param=param)
                sv.update(mening=d.get('text') or d['drag'], klick=True)
            elif p == '/api/plats':
                ny = ts.satt_plats(fore, d['plats'], d['har'])
                sv = {'utfall': 'utfort', 'rader': [f"Platsen {d['plats']} = {d['har']}."], 'mening': f"{d['plats']}: {d['har']}", 'klick': True}
            elif p == '/api/angra':
                if pass_['historik']:
                    pass_['s'] = pass_['historik'].pop()
                pass_['logg'].append({'angra': True})
                spara()
                return self.svar(200, {'vy': vy(), 'svar': {'utfall': 'angrat', 'rader': ['Ångrat.']}})
            else:
                return self.svar(404, {'fel': 'finns inte'})
            if ny is not fore:
                pass_['historik'].append(fore)
                pass_['s'] = ny
            pass_['logg'].append(sv)
            spara()
            self.svar(200, {'vy': vy(), 'svar': sv})
        except Exception as e:  # visa felet i ytan i stället för att tappa passet
            self.svar(500, {'fel': f'{type(e).__name__}: {e}'})


if __name__ == '__main__':
    print(f'Regibordet: http://127.0.0.1:{PORT}  ({len(KORT)} kort, {len(KONTON)} konton)', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
