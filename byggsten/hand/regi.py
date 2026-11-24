"""Regi: slingan på ryggradens nivå. CM skriver, Jev väljer drag, draget utförs, bilden ritas om.

  mening → Jev (ett Choice bland lagliga drag i det aktuella tillståndet)
         → spärrar (marginal, ryggrad)
         → vid byt_lokal eller byt_upplagg: ett andra Choice om vart
         → tillampa() ändrar tillståndet och säger vad som följde med
         → blockout: en rad bilder per tillstånd

Jev väljer bara. Allt som ändras görs av tillstand.py, och det som kräver text märks som manus.
Tak: 30 Jev-anrop per körning. Nyckeln läses ur app/.env.local och skrivs aldrig ut.

Kör: python regi.py <klipp-id> [--kund <konto>] [--session <namn>] "mening" "mening" ...
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import tillstand as ts

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'
BLENDER = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
TROSKEL = 0.4       # under den marginalen utförs inget: CM får välja. 0,25 släppte igenom ett fel ("gör honom gladare" → byt_produkt, marginal 0,25)
TAK, PRIS = 30, 0.04 / 1e6
anrop = {'n': 0, 'tokens': 0}


def nyckel():
    for rad in (HERE.parents[1] / 'app' / '.env.local').read_text(encoding='utf-8').splitlines():
        if rad.startswith('TYPESAFE_API_KEY='):
            return rad.split('=', 1)[1].strip()
    raise SystemExit('ingen nyckel')


def jev(key, state, instr, kriterier, fler=None):
    """Ett Choice. 'fler' är extra frågor i samma anrop: {namn: (instruktion, kriterier)}."""
    anrop['n'] += 1
    if anrop['n'] > TAK:
        raise SystemExit('tak för Jev-anrop nått')
    fragor = {'q': {'type': 'choice', 'instructions': instr, 'criteria': kriterier}}
    for namn, (i2, k2) in (fler or {}).items():
        fragor[namn] = {'type': 'choice', 'instructions': i2, 'criteria': k2}
    body = json.dumps({'model': 'jev-latest', 'state': state, 'questions': fragor}).encode()
    req = urllib.request.Request('https://api.typesafe.ai/v1/systemone', data=body,
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
                                          'User-Agent': 'regi/0'})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.loads(r.read())
    ms = round((time.perf_counter() - t0) * 1000)
    a = j['answers']['q']
    anrop['tokens'] += (j.get('usage') or {}).get('input_tokens', 0)
    pr = a.get('probabilities') or {}
    p = sorted(pr.items(), key=lambda z: -z[1])
    # marginalen räknas från det valda draget till det starkaste andra (kan bli negativ)
    andra = [(k, v) for k, v in p if k != a['choice']]
    ut = {'val': a['choice'], 'marginal': round(pr.get(a['choice'], 0) - andra[0][1], 2) if andra else None,
          'nast': andra[0][0] if andra else None, 'topp': [[k, round(v, 2)] for k, v in p[:3]], 'ms': ms}
    for namn in (fler or {}):
        ut[namn] = j['answers'][namn]['choice']
    return ut


def main():
    arg = sys.argv[1:]
    kid = arg.pop(0)
    kund, session = None, 'prov'
    while arg and arg[0].startswith('--'):
        flagga = arg.pop(0)
        if flagga == '--kund':
            kund = arg.pop(0)
        elif flagga == '--session':
            session = arg.pop(0)
    meningar = arg
    mapp = UT / 'regi' / session
    mapp.mkdir(parents=True, exist_ok=True)
    ryggrad = json.loads((UT / f'ryggrad_{kid}.json').read_text(encoding='utf-8'))
    kundinfo = None
    if kund:
        a = json.loads((UT / f'anpassa_{kid}__{kund}.json').read_text(encoding='utf-8'))
        kundinfo = {'konto': kund, 'produkt': (a['kundens_linje']['produkter'] or [None])[0],
                    'rum': next(iter(a['kundens_linje']['rum']), None)}
    key = nyckel()
    s = ts.fran_ryggrad(kid)
    lagen = [('original', s)]
    L = [f'# Regi: {kid}' + (f' för @{kund}' if kund else ''), '', f"Typ: {s['typ']}. Start: {ts.langd(s)} s, {len(s['takter'])} takter.", '']
    steg = []
    for i, m in enumerate(meningar, 1):
        drag = ts.lagliga_drag(s, ryggrad)
        state = ts.tillstandstext(s) + (f"\nKunden är @{kund}: filmar oftast i {kundinfo['rum']}, visar {kundinfo['produkt']}." if kundinfo else '') \
            + f'\n\nCM skriver: "{m}"'
        j = jev(key, state, 'En content manager vill ändra klippet. Välj det enda drag som bäst gör det meningen ber om. '
                            'Välj ingen_passar om inget drag gör det.', drag)
        rad = {'nr': i, 'mening': m, 'jev': j, 'antal_drag': len(drag)}
        ut = [f'## {i}. "{m}"', '', f"Jev: **{j['val']}** (marginal {j['marginal']}, {j['ms']} ms). Näst: {j['nast']}."]
        val, param = j['val'], None
        UTGANG = ('manus', 'scenlagret', 'ingen_passar')
        osaker = j['marginal'] is not None and j['marginal'] < TROSKEL
        if osaker and val not in UTGANG and j['nast'] not in UTGANG + ('byt_lokal', 'byt_upplagg', 'byt_produkt') \
                and val not in ('byt_lokal', 'byt_upplagg', 'byt_produkt'):
            # två drag som ger samma ändring är ingen osäkerhet
            a1, _ = ts.tillampa(s, val, ryggrad, kund=kundinfo)
            a2, _ = ts.tillampa(s, j['nast'], ryggrad, kund=kundinfo)
            if a1['takter'] == a2['takter'] and a1['klipptakt'] == a2['klipptakt']:
                osaker = False
                ut.append(f"(Marginalen är liten, men {val} och {j['nast']} ger samma ändring här.)")
        if osaker and val in UTGANG and j['nast'] in UTGANG:
            rad['utfall'] = 'utanfor'
            ut.append(f"Utanför ryggraden ({val} eller {j['nast']}): ingen ändring av uppställningen.")
        elif osaker:
            rad['utfall'] = 'osaker'
            ut.append(f"Inte utfört: för liten marginal. CM får välja mellan: {drag[val]} / {drag[j['nast']]}")
        elif val in UTGANG:
            rad['utfall'] = val
            ut.append({'manus': 'Skickas till manus (långsam väg): ingen ändring av uppställningen.',
                       'scenlagret': 'Hör till scenlagret (liggaren): kropp, föremål i handen eller kamera inom en scen. Ingen ändring här.',
                       'ingen_passar': 'Inget drag passar. Ingen ändring.'}[val])
        elif val == 'byt_upplagg':
            alt = {x.get('grepp') or x.get('mekanik'): x for x in ryggrad['byta_grepp']}
            j2 = jev(key, state, 'Vilket upplägg ber meningen om?', {k: k.replace('_', ' ') for k in alt} | {'oklart': 'Meningen säger inte vilket.'})
            rad['jev2'] = j2
            rad['utfall'] = 'hanvisning'
            if j2['val'] in alt:
                e = alt[j2['val']]
                ut.append(f"Nytt upplägg: **{j2['val'].replace('_', ' ')}**. Det är ett annat klipp, inte ett drag. Närmaste i tema: [{e['id']}]({e['url']}). {e['karna']}")
            else:
                ut.append('Nytt upplägg, men oklart vilket. CM får välja bland: ' + ', '.join(k.replace('_', ' ') for k in alt))
        else:
            if val == 'byt_lokal':
                j2 = jev(key, state, 'Vart ska scenen flyttas?', ts.STALLEN | {'oklart': 'Meningen säger inte vart.'},
                         fler={'vilka': ('Vilka takter ska flyttas?', {
                             'forsta': 'Bara den första takten, början av klippet.', 'sista': 'Bara den sista takten, slutet.',
                             'alla_fria': 'Alla takter som inte är bundna till produkten, eller meningen säger inte vilka.',
                             'alla': 'Hela klippet, alla takter.'})})
                rad['jev2'] = j2
                vart = j2['val'] if j2['val'] in ts.STALLEN else (ts.RUM_TILL_STALLE.get(kundinfo['rum']) if kundinfo else None)
                param = (vart, j2['vilka'])
                ut.append(f"Vart: **{vart}**, vilka takter: **{j2['vilka']}** (marginal {j2['marginal']}).")
            if val == 'byt_produkt':
                # nämner CM en produkt själv går den före kundens vanliga
                alt = {'ur_meningen': 'Meningen nämner själv vilken produkt det ska vara.',
                       'kundens': 'Meningen nämner ingen produkt: ta den kunden brukar visa.'}
                j2 = jev(key, state, 'Vilken produkt ska in?', alt)
                rad['jev2'] = j2
                param = f'ur CM:s mening: "{m}"' if j2['val'] == 'ur_meningen' else None
                ut.append(f"Produkt: **{'ur meningen' if param else 'kundens vanliga'}** (marginal {j2['marginal']}).")
            ny, logg = ts.tillampa(s, val, ryggrad, param=param, kund=kundinfo)
            rad['logg'] = logg
            if logg['utfort']:
                rad['utfall'] = 'utfort'
                ut.append('Ändrat: ' + '; '.join(logg['andrat']) + '.')
                ut += [f'- följd: {x}' for x in logg['foljder']]
                ut.append(f"Nu: {ts.langd(ny)} s, {len(ny['takter'])} takter.")
                s = ny
                lagen.append((f'{i}. {m}', s))
            else:
                rad['utfall'] = 'stoppat'
                ut.append(f"Stoppat: {logg['stopp']}.")
        steg.append(rad)
        L += [x for x in ut if x] + ['']
        print('\n'.join(x for x in ut if x), '\n')

    kost = round(anrop['tokens'] * PRIS, 5)
    L += [f"Jev: {anrop['n']} anrop, {anrop['tokens']} tokens in, {kost} dollar."]
    (mapp / 'logg.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    (mapp / 'steg.json').write_text(json.dumps({'klipp': kid, 'kund': kund, 'steg': steg, 'jev_anrop': anrop['n'], 'usd': kost,
                                                'slut': s}, ensure_ascii=False, indent=1), encoding='utf-8')

    # bilder: en rad per tillstånd
    bro = {'bro': 'regi/0', 'steg': [], 'rader': []}
    for rubrik, lage in lagen:
        bilder = ts.till_steg(lage, rubrik[:38] + ' ·')
        bro['steg'] += bilder
        bro['rader'].append(len(bilder))
    (mapp / 'bilder.json').write_text(json.dumps(bro, ensure_ascii=False, indent=1), encoding='utf-8')
    subprocess.run([BLENDER, '-b', '--factory-startup', '--python-exit-code', '1', '--python', str(HERE / 'blockout.py'), '--',
                    str(mapp / 'bilder.json'), str(mapp / 'bild'), 'r'], check=True, capture_output=True)
    subprocess.run([sys.executable, '-X', 'utf8', str(HERE / 'kontaktblad.py'), str(mapp / 'bilder.json'), str(mapp / 'bild'), 'r',
                    str(mapp / 'kontaktblad.png')], check=True, capture_output=True)
    print(f"Jev: {anrop['n']} anrop, {kost} dollar. Bild: {mapp / 'kontaktblad.png'}")


if __name__ == '__main__':
    main()
