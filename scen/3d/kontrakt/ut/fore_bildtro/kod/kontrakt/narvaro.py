"""Närvaro: roller som finns i rummet under en scen utan att vara lästa där.

    python narvaro.py <plan.json> <deklaration.json> <ut plan.json>

Regeln kommer ur deklarationens block `narvaro` (vilka roller som finns i vilka tagningar, vilken roll kameran står hos,
vilka tagningar som bryter rummet). Steget arbetar på den färdiga planen och är inte knutet till något klipp:

  - För varje scen och varje deklarerad roll som saknas bland scenens personer väljs en givarscen: den scen närmast i tid
    där rollen är läst och som inte bryter rummet.
  - Rollen läggs in i scenen med givarens rörelse, värld och plats-transform. Eftersom alla tagningar redan ligger i samma
    plats hamnar rollen på sin egen plats i rummet utan ny placering.
  - Rörelsen spelas fram och tillbaka över givarens lästa rutor (pingpong), så att den inte hoppar när scenen är längre.
  - En roll som kameran står hos (kamerabärare) märks; byggaren behåller den i rummet men renderar den inte i den scenen.

Allt som läggs till är märkt `narvaro` med status antagen. Scenens lästa personer ändras inte."""
import copy, json, sys
from pathlib import Path
import numpy as np


def tagning(scen): return Path(scen['varld']).parent.name


def pingpong(giltiga, n):
    v = list(map(int, giltiga)); bana = v + v[-2:0:-1] if len(v) > 2 else v
    return [bana[i % len(bana)] for i in range(n)]


def lagg_narvaro(plan, D):
    N = D['narvaro']; bryter = set(N.get('bryter_rummet', [])); logg = []
    last = {}        # roll -> [(scen, personpost)] där rollen är läst
    for s in plan['scener']:
        for p in s['personer']:
            if not p.get('narvaro') and tagning(s) not in bryter: last.setdefault(p['id'], []).append((s, p))
    for s in plan['scener']:
        t = tagning(s); a, b = s['ut']; finns = {p['id'] for p in s['personer']}
        for roll in N.get('tagningar', {}).get(t, []):
            if roll in finns: continue
            if roll not in last: logg.append(dict(scen=s['id'], roll=roll, status='saknas', orsak='rollen är inte läst i någon tagning som håller rummet')); continue
            g, gp = min(last[roll], key=lambda x: (abs(x[0]['ut'][0] - a), x[0]['ut'][0]))
            ga, gb = g['ut']; lokal = np.arange(g['lokal_start'], g['lokal_start'] + (gb - ga))
            with np.load(gp['rorelse']) as S: giltiga = lokal[np.asarray(S['inom'])[lokal].astype(bool)]
            if not len(giltiga): logg.append(dict(scen=s['id'], roll=roll, status='saknas', orsak='givarscenen har inga lästa rutor')); continue
            barare = N.get('kamerabarare', {}).get(t) == roll
            ny = {k: copy.deepcopy(v) for k, v in gp.items() if k != 'skyddade_knan'}
            ny.update(varld=g['varld'], till_plats=gp.get('till_plats', g.get('till_plats')), rutor=pingpong(giltiga, b - a),
                      narvaro=dict(givarscen=g['id'], givartagning=tagning(g), metod='lånad rörelse, pingpong över givarens lästa rutor', status='antagen',
                                   kamerabarare=barare, kalla='deklaration.narvaro'))
            s['personer'].append(ny)
            logg.append(dict(scen=s['id'], roll=roll, status='tillagd', givarscen=g['id'], rutor_i_givaren=int(len(giltiga)), kamerabarare=barare))
    plan['narvaro'] = dict(regel=N['regel'], status=N.get('status', 'antagen'), poster=logg)
    return logg


if __name__ == '__main__':
    planfil, dekl, ut = map(Path, sys.argv[1:4])
    plan = json.loads(planfil.read_text(encoding='utf-8')); D = json.loads(dekl.read_text(encoding='utf-8'))
    logg = lagg_narvaro(plan, D); ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')
    for x in logg: print(x)
