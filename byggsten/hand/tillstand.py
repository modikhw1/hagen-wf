"""Klippets tillstånd på ryggradens nivå, och dragen som ändrar det.

tillstand/0 är en lista takter med uppställning (ställe, hållning, hantering, personer, skylt, utsnitt)
plus klippets platser och några tal (klipptakt, ton i säljandet). Det byggs ur ryggraden och ställena.

Ett drag är en liten, bestämd ändring. Varje drag:
  - kontrollerar att det får göras (ryggradstakter stryks aldrig),
  - ändrar tillståndet,
  - säger vad som ändrades och vad som följde med.
Inget drag skriver manus. Det som kräver ny text märks 'manus_behovs' på takten.
"""
import copy
import json
from pathlib import Path

from jevyta import FRAS
from spela import RUM_TILL_STALLE, scen
from stallen import las

UT = Path(__file__).resolve().parent / 'ut'
STALLEN = {'utanfor': 'Utanför, vid entrén eller på gatan.', 'bar': 'Vid bardisken.', 'disk': 'Vid disken eller kassan.',
           'kok': 'I köket.', 'bord': 'Sittande vid ett bord.', 'uteservering': 'På uteserveringen.', 'lokalen': 'Stående ute i lokalen.'}


def fran_ryggrad(kid):
    r = json.loads((UT / f'ryggrad_{kid}.json').read_text(encoding='utf-8'))
    typst = json.loads((UT / 'stallen_typ.json').read_text(encoding='utf-8')).get(r['typ'], {})
    rum = None
    for line in open(UT / 'klipp.jsonl', encoding='utf-8'):
        k = json.loads(line)
        if k['id'] == kid:
            rum = ((k['l4'].get('krav') or {}).get('lokal') or [None])[0]
            break
    f = {x['finger']: x for x in r['fingrar'] if 'saknas' not in x}
    langd = (f.get('langd') or {}).get('varde') or 20.0
    takter, forra = [], None
    for t in r['takter']:
        x = las(t['vad'])
        st = x['stalle'] or forra
        if not st:
            c = {a: b for a, b in (typst.get(t['funktion']) or {}).items() if a != 'osagt'}
            st = max(c, key=c.get) if c and max(c.values()) >= 5 else RUM_TILL_STALLE.get(rum, 'lokalen')
        forra = st
        takter.append({'nr': t['nr'], 'vad': t['vad'], 'funktion': t['funktion'], 'bar': t['bar'], 'bunden': t['bunden'],
                       'stalle': st, 'hallning': x['hallning'], 'hantering': x['hantering'], 'kollega': False,
                       'skylt': None, 'zoom': 1.0, 'sek': round(langd / len(r['takter']), 1), 'markning': []})
    # Kontrastratten finns bara för klipp som bygger på en kontrast: läst mekanik, eller två rekvisitaplatser i mallen.
    kontrast = 1.0 if ((r.get('lasning') or {}).get('mekanik') == 'kontrast'
                       or sum(p['typ'] == 'rekvisita' for p in r['platser']) >= 2) else None
    return {'tillstand': 'tillstand/0', 'klipp': kid, 'typ': r['typ'], 'karna': r['karna'], 'takter': takter,
            'kontrast': kontrast, 'risk': r.get('anpassningsrisk'),
            'platser': [dict(p) for p in r['platser']], 'klipptakt': (f.get('klipptakt') or {}).get('varde'),
            'saljande': (f.get('promo') or {}).get('varde'), 'historik': []}


def langd(s):
    return round(sum(t['sek'] for t in s['takter']), 1)


def satt_plats(s, plats, har):
    """CM fyller en plats i mallen för hand. Det är manus, och det görs utan modell."""
    n = copy.deepcopy(s)
    for p in n['platser']:
        if p['plats'] == plats:
            p.setdefault('var', p['har'])
            p['har'] = har
            p.pop('inaktuell', None)
            n['historik'] = s['historik'] + [f'plats:{plats}']
            return n
    return s


def nu_varden(s, ryggrad):
    """Fingervärden som går att läsa av tillståndet. Övriga står kvar som i originalet."""
    f = {x['finger']: x['varde'] for x in ryggrad['fingrar'] if 'saknas' not in x}
    T = s['takter']
    f['langd'] = langd(s)
    f['takter'] = float(len(T))
    if s.get('klipptakt') is not None:
        f['klipptakt'] = s['klipptakt']
    if 'personer' in f and any(t['kollega'] for t in T):
        f['personer'] = max(f['personer'], 1.0) + 1.0
    if T:
        f['bundet_produkt'] = round(sum(t['bunden'] == 'produkt' and not t.get('utan_mat') for t in T) / len(T), 2)
        f['bundet_lokal'] = round(sum(t['bunden'] == 'lokal' for t in T) / len(T), 2)
    return f


def till_steg(s, rubrik=''):
    """Tillståndet som bilder i brons format (för blockout.py och kontaktblad.py)."""
    ut = []
    for i, t in enumerate(s['takter']):
        sc = scen(t['stalle'], t['hallning'], t['hantering'], kollega=t['kollega'], skylt=t['skylt'])
        sc['zoom'] = t['zoom']
        if t.get('utan_mat'):
            sc['saker'] = [x for x in sc['saker'] if x['typ'] not in ('bricka', 'trag')]
            for p in sc['personer']:
                p['haller'] = None
        if s.get('kontrast') and t['bar'] == 'ryggrad':
            # kontrastklipp: första ryggradstakten bär den lilla sidan, sista den stora
            rygg = [x for x in s['takter'] if x['bar'] == 'ryggrad']
            stor = t is rygg[-1] and len(rygg) > 1
            p = sc['personer'][0]
            p['haller'], p['arm'] = 'lada', ('mun' if stor else 'fram')
            p['haller_skala'] = round(1.3 * s['kontrast'], 2) if stor else round(0.55 / s['kontrast'], 2)
        mark = (' [' + '; '.join(t['markning']) + ']') if t['markning'] else ''
        ut.append({'t': i + 1, 'finger': f"{t['funktion']} · {t['bar']} · {t['sek']} s", 'premiss': t['vad'] + mark,
                   'bevis': f"{rubrik} ställe: {t['stalle']}", 'sprang': False, 'scen': sc})
    return ut


def lagliga_drag(s, ryggrad):
    """Dragen som går att göra från det här tillståndet, med formulering för Jev."""
    f = {x['finger']: x for x in ryggrad['fingrar'] if 'saknas' not in x}
    d = {}
    kan_stryka = [t for t in s['takter'] if t['bar'] == 'kan strykas']
    kan_korta = [t for t in s['takter'] if t['bar'] == 'kan kortas' and t['sek'] > 1.5]
    # Kortare erbjuds alltid, så att Jev kan välja det. Är bara ryggraden kvar stoppar tillampa() med ett skäl.
    d['langd_ned'] = FRAS['langd'][0]
    d['langd_upp'] = FRAS['langd'][1]
    if kan_stryka or [t for t in s['takter'] if t['bar'] == 'kan kortas']:
        d['takter_ned'] = FRAS['takter'][0]
    d['takter_upp'] = FRAS['takter'][1]
    for namn in ('klipptakt', 'person', 'mat', 'lokal', 'text', 'promo', 'personer'):
        if namn in f or namn in ('personer', 'text', 'lokal'):
            d[f'{namn}_ned'], d[f'{namn}_upp'] = FRAS[namn]
    if not any(t['kollega'] for t in s['takter']):
        d.pop('personer_ned', None)
    if not any(t['skylt'] for t in s['takter']):
        d.pop('text_ned', None)
    d['produktion_ned'] = FRAS['produktion'][0]
    for t in s['takter']:
        if t['bar'] == 'kan strykas':
            d[f"takt{t['nr']}_stryk"] = f"Ta bort takt {t['nr']}: {t['vad']}"
        if t['bar'] == 'kan kortas' and t['sek'] > 1.5:
            d[f"takt{t['nr']}_korta"] = f"Korta takt {t['nr']}: {t['vad']}"
        if t['bar'] == 'kan kortas':
            d[f"takt{t['nr']}_stryk"] = f"Ta bort takt {t['nr']} helt: {t['vad']}"
        if t['bar'] == 'ryggrad':
            # Ryggradstakter erbjuds som ett eget val, så att Jev kan peka på rätt takt i stället för på grannen.
            d[f"takt{t['nr']}_skyddad"] = f"Ta bort eller hoppa över takt {t['nr']}: {t['vad']}"
    if s.get('kontrast'):
        d['kontrast_upp'] = 'Gör skillnaden mellan de två sidorna som ställs mot varandra större, mer överdriven.'
        d['kontrast_ned'] = 'Gör skillnaden mellan de två sidorna mindre, mer återhållen.'
    if any(t['bunden'] == 'produkt' for t in s['takter']) or any(p['typ'] == 'produkt' for p in s['platser']):
        d['byt_produkt'] = 'Byt produkten som visas mot kundens egen, filmad på samma sätt.'
    d['byt_lokal'] = 'Flytta en eller flera scener till en annan plats eller ett annat rum.'
    if ryggrad.get('byta_grepp'):
        d['byt_upplagg'] = 'Behåll ämnet men byt upplägg för hela klippet, till exempel provsmakning, tillagning eller en utmaning i stället.'
    d['manus'] = 'Skriv om vad som sägs eller står i text (pris, replik, erbjudande), utan att ändra upplägget.'
    d['scenlagret'] = 'Ändra hur en person rör sig, håller något eller ser ut, eller hur kameran rör sig, inom en scen. Det hör till scenlagret och inte hit.'
    d['ingen_passar'] = 'Inget av dragen gör det som efterfrågas.'
    return d


def tillstandstext(s):
    rader = [f"Klipp av typen: {s['typ']}.", f"Kärna: {s['karna']}", f"Längd nu: {langd(s)} s, {len(s['takter'])} takter.", 'Takter:']
    for t in s['takter']:
        extra = (', med kollega' if t['kollega'] else '') + (f", skylt: {t['skylt']}" if t['skylt'] else '')
        rader.append(f"  takt {t['nr']} ({t['funktion']}, {t['bar']}, bunden till {t['bunden']}, {t['sek']} s, ställe {t['stalle']}{extra}): {t['vad']}")
    rader.append('Platser i mallen: ' + '; '.join(f"{p['plats']} = {p['har']} ({p['typ']})" for p in s['platser']))
    return '\n'.join(rader)


def tillampa(s, drag, ryggrad, param=None, kund=None):
    """Utför ett drag. Ger (nytt tillstånd, logg). Loggen har 'utfort', 'andrat', 'foljder' och ibland 'stopp'."""
    n = copy.deepcopy(s)
    T = n['takter']
    logg = {'drag': drag, 'utfort': True, 'andrat': [], 'foljder': []}
    f = {x['finger']: x for x in ryggrad['fingrar'] if 'saknas' not in x}

    def stopp(varfor):
        logg.update(utfort=False, stopp=varfor)
        return s, logg

    def stryk(t):
        if t['bar'] == 'ryggrad':
            return False
        T.remove(t)
        logg['andrat'].append(f"takt {t['nr']} struken ({t['funktion']}, {t['sek']} s)")
        if t['funktion'] == 'avslut':
            logg['foljder'].append('klippet slutar nu på takten före: kontrollera att den håller som slutbild')
        if t['funktion'] == 'vandning':
            logg['foljder'].append('vändningen är borta: ryggradstakterna möts nu utan markering, kontrasten måste synas i bilden själv')
        if t['bunden'] == 'redigering':
            logg['foljder'].append('takten var bunden till redigeringen (klipp, text, ljud): mallen ändras')
        return True

    def korta(t):
        gammal = t['sek']
        t['sek'] = round(max(1.0, t['sek'] / 2), 1)
        logg['andrat'].append(f"takt {t['nr']} kortad {gammal} → {t['sek']} s")
        if 'visar_upp' in t['hantering'] or t['funktion'] == 'visning':
            logg['foljder'].append(f"takt {t['nr']} hinner visa färre saker: uppräkningen måste kortas i manus")
            t['markning'].append('manus: korta uppräkningen')

    if drag.endswith('_skyddad'):
        t = next((t for t in T if t['nr'] == int(drag[4:-8])), None)
        return stopp(f"takt {t['nr'] if t else '?'} är ryggrad: utan den är det ett annat klipp. Vill CM det ändå är det ett byte av upplägg")
    if drag in ('langd_ned', 'takter_ned'):
        fria =[t for t in T if t['bar'] == 'kan strykas']
        korts = [t for t in T if t['bar'] == 'kan kortas']
        if fria:
            stryk(fria[-1])
        elif drag == 'takter_ned' and korts:
            stryk(korts[-1])
        elif korts and korts[-1]['sek'] > 1.5:
            korta(korts[-1])
        else:
            return stopp('bara ryggraden är kvar: kortare än så går inte utan att klippet blir ett annat')
    elif drag.startswith('takt') and drag.endswith('_stryk'):
        t = next((t for t in T if t['nr'] == int(drag[4:-6])), None)
        if not t or not stryk(t):
            return stopp('takten är ryggrad eller finns inte')
    elif drag.startswith('takt') and drag.endswith('_korta'):
        t = next((t for t in T if t['nr'] == int(drag[4:-6])), None)
        if not t:
            return stopp('takten finns inte')
        korta(t)
    elif drag in ('langd_upp', 'takter_upp'):
        vis = [t for t in T if t['funktion'] == 'visning'] or [t for t in T if t['bar'] != 'ryggrad'] or T
        k = copy.deepcopy(vis[-1])
        k['nr'] = max(t['nr'] for t in T) + 1
        k['bar'] = 'kan strykas'
        k['vad'] = 'Ny takt, samma upplägg som takt %d.' % vis[-1]['nr']
        k['markning'] = ['manus: vad visas här?']
        T.insert(T.index(vis[-1]) + 1, k)
        logg['andrat'].append(f"ny takt efter takt {vis[-1]['nr']} ({k['sek']} s)")
        logg['foljder'].append('den nya takten har inget innehåll än: manus behövs')
        tak = (f.get('langd') or {}).get('typen', {}).get('p90')
        if tak and langd(n) > tak:
            logg['foljder'].append(f'klippet är nu {langd(n)} s, längre än 9 av 10 klipp av typen ({tak} s)')
    elif drag in ('klipptakt_ned', 'klipptakt_upp'):
        g = n['klipptakt'] or 0
        steg = 1.0 if drag.endswith('upp') else -1.0
        n['klipptakt'] = round(max(0.0, g + steg), 2)
        logg['andrat'].append(f"klipp per 10 s {g} → {n['klipptakt']}")
        logg['foljder'].append('klippningen är mallens sak: uppställningen i scenerna ändras inte')
    elif drag in ('personer_upp', 'personer_ned'):
        if drag.endswith('upp'):
            t = next((t for t in T if not t['kollega']), None)
            if not t:
                return stopp('alla takter har redan en kollega')
            t['kollega'] = True
            t['markning'].append('manus: vad gör kollegan?')
            logg['andrat'].append(f"kollega i takt {t['nr']}")
            logg['foljder'].append('kravet på personer går från 1 till 2')
        else:
            for t in T:
                t['kollega'] = False
            logg['andrat'].append('kollegan borttagen')
    elif drag in ('person_upp', 'mat_ned'):
        t = next((t for t in T if t['bunden'] == 'produkt' and not t.get('utan_mat') and t['bar'] != 'ryggrad'), None) \
            or next((t for t in T if t['bunden'] == 'produkt' and not t.get('utan_mat')), None)
        if not t:
            return stopp('ingen takt visar mat')
        t['utan_mat'] = True
        t['zoom'] = min(t['zoom'], 0.75)
        logg['andrat'].append(f"takt {t['nr']}: personen i stället för maten, tätare bild")
        if t['bar'] == 'ryggrad':
            logg['foljder'].append(f"takt {t['nr']} är ryggrad och bunden till produkten: visningen bär klippet, det här kan ta bort poängen")
    elif drag in ('mat_upp', 'person_ned'):
        t = next((t for t in T if t.get('utan_mat')), None) or next((t for t in T if t['bunden'] != 'produkt' and t['bar'] != 'ryggrad'), None)
        if not t:
            return stopp('alla fria takter visar redan mat')
        t['utan_mat'] = False
        if 'visar_upp' not in t['hantering']:
            t['hantering'] = t['hantering'] + ['visar_upp']
        logg['andrat'].append(f"takt {t['nr']}: maten i bild")
    elif drag in ('lokal_ned', 'lokal_upp'):
        for t in T:
            t['zoom'] = round(min(1.4, max(0.6, t['zoom'] * (0.75 if drag.endswith('ned') else 1.3))), 2)
        logg['andrat'].append('tätare bild i alla takter' if drag.endswith('ned') else 'vidare bild i alla takter')
    elif drag in ('text_upp', 'text_ned'):
        if drag.endswith('upp'):
            t = T[0]
            t['skylt'] = 'TEXT'
            t['markning'].append('manus: vad står det?')
            logg['andrat'].append(f"skylt i takt {t['nr']}")
        else:
            for t in T:
                t['skylt'] = None
            logg['andrat'].append('skyltarna borttagna')
    elif drag in ('promo_ned', 'promo_upp'):
        if drag.endswith('ned'):
            av = [t for t in T if t['funktion'] == 'avslut' and t['bar'] != 'ryggrad']
            if av:
                stryk(av[-1])
            else:
                for t in T:
                    if 'pris' in t['vad'].lower() or 'erbjud' in t['vad'].lower():
                        t['markning'].append('manus: tona ned pris och erbjudande')
                logg['andrat'].append('ingen fri säljtakt att stryka: tonen måste ändras i manus')
        else:
            T[-1]['markning'].append('manus: lägg in erbjudande och uppmaning')
            logg['andrat'].append(f"erbjudande och uppmaning i takt {T[-1]['nr']} (manus)")
    elif drag == 'produktion_ned':
        n['klipptakt'] = 0.0 if n['klipptakt'] is None else round(n['klipptakt'] / 2, 2)
        for t in T:
            t['skylt'] = None
        st = [t['stalle'] for t in T]
        vanligast = max(set(st), key=st.count)
        # takter som CM själv har flyttat (var_stalle) rörs inte
        flyttade = [t['nr'] for t in T if t['stalle'] != vanligast and t['bunden'] != 'lokal' and 'var_stalle' not in t]
        for t in T:
            if t['nr'] in flyttade:
                t['stalle'] = vanligast
        logg['andrat'].append(f'färre klipp, inga skyltar, allt på ett ställe ({vanligast})')
        if flyttade:
            logg['foljder'].append(f"takt {', '.join(map(str, flyttade))} flyttades till {vanligast}: kroken tappar sitt eget ställe")
    elif drag in ('kontrast_upp', 'kontrast_ned'):
        g = n['kontrast']
        n['kontrast'] = round(min(2.5, max(0.5, g * (1.4 if drag.endswith('upp') else 1 / 1.4))), 2)
        logg['andrat'].append(f"kontrasten {g} → {n['kontrast']} (den stora sidan större, den lilla mindre)")
        if drag.endswith('ned') and n.get('risk'):
            logg['foljder'].append('kortets risk går åt det här hållet: ' + n['risk'])
        if drag.endswith('upp'):
            logg['foljder'].append('större föremål kräver större rörelse: hur hon håller och äter är scenlagrets sak')
    elif drag == 'byt_produkt':
        ny = param or (kund or {}).get('produkt') or 'kundens produkt'
        gamla = [p['har'].lower() for p in n['platser'] if p['typ'] == 'produkt']
        for p in n['platser']:
            if p['typ'] == 'produkt':
                p['var'] = p['har']
                p['har'] = ny
        ber = [t for t in T if t['bunden'] == 'produkt'] or [t for t in T if any(g in t['vad'].lower() for g in gamla)] \
            or [t for t in T if t['bar'] == 'ryggrad']
        for t in ber:
            t['markning'].append(f'produkt: {ny}')
        logg['andrat'].append(f"produkten bytt till '{ny}' i takt {', '.join(str(t['nr']) for t in ber) or '–'}")
        for p in n['platser']:
            if p['typ'] in ('replik', 'text', 'situation'):
                p['inaktuell'] = True
                logg['foljder'].append(f"platsen {p['plats']} = '{p['har']}' gällde den gamla produkten: manus")
    elif drag == 'byt_lokal':
        vilka = 'alla_fria'
        if isinstance(param, (list, tuple)):
            param, vilka = param
        if param not in STALLEN:
            return stopp('inget ställe valt')
        ber = [t for t in T if t['bunden'] != 'produkt'] or T
        if vilka == 'forsta':
            ber = T[:1]
        elif vilka == 'sista':
            ber = T[-1:]
        elif vilka == 'alla':
            ber = list(T)
        for t in ber:
            t['var_stalle'] = t['stalle']
            t['stalle'] = param
            if param not in ('bord', 'uteservering') and t['hallning'] == 'sitter':
                t['hallning'] = 'star'
        logg['andrat'].append(f"takt {', '.join(str(t['nr']) for t in ber)} flyttad till {param}")
        nam = [t['nr'] for t in ber if las(t['vad'])['stalle'] not in (None, param)]
        if nam:
            logg['foljder'].append(f"takt {', '.join(map(str, nam))} nämner sitt gamla ställe i beskrivningen: manus")
            for t in ber:
                if t['nr'] in nam:
                    t['markning'].append('manus: nytt ställe')
        kvar = [t['nr'] for t in T if t not in ber]
        if kvar:
            logg['foljder'].append(f"takt {', '.join(map(str, kvar))} är bunden till produkten och står kvar där den filmas bäst")
    else:
        return stopp('draget utförs inte här')
    for t in T:
        t['markning'] = list(dict.fromkeys(t['markning']))   # samma markering en gång
    n['historik'] = s['historik'] + [drag]
    return n, logg
