"""För handsynen (ingest/handsyn.py) in i en färdig plan, så att byggaren kan lugna händer utan bildstöd.

    python handsyn_plan.py <plan.json> [<ut plan.json>]

Varje person i varje scen får `handsyn` = {h: {dold: [...], stord: [...]}, v: {...}} med en post per utdataruta i scenen.
Källrutorna är scenens egna (lokal_start och framåt) eller, för en närvaroperson (kontrakt/narvaro.py), personens lånade rutor.
Personer vars tagning saknar handsyn-fil lämnas orörda. Steget ändrar inga rörelsedata."""
import json, sys
from pathlib import Path


def lagg_handsyn(plan):
    logg = []
    for s in plan['scener']:
        a, b = s['ut']
        for p in s['personer']:
            fil = Path(p['rorelse']).parent / f"handsyn_{p['ingest_id']}.json"
            if not fil.exists(): logg.append(dict(scen=s['id'], person=p['id'], status='saknas')); continue
            H = json.loads(fil.read_text(encoding='utf-8')); rutor = p['rutor'] if p.get('narvaro') else list(range(s['lokal_start'], s['lokal_start'] + (b - a)))
            p['handsyn'] = {k: dict(dold=[not H[k]['synlig'][i] for i in rutor], stord=[bool(H[k].get('stord', [False] * H['N'])[i]) for i in rutor]) for k in ('h', 'v')}
            logg.append(dict(scen=s['id'], person=p['id'], narvaro=bool(p.get('narvaro')), dolda_hoger=sum(p['handsyn']['h']['dold']), dolda_vanster=sum(p['handsyn']['v']['dold']),
                             storda_hoger=sum(p['handsyn']['h']['stord']), storda_vanster=sum(p['handsyn']['v']['stord']), rutor=len(rutor)))
    plan['handsyn'] = dict(regel='Händer utan bildstöd hålls lugna i bygget; störda händer jämnas ut.', status='modellbedomd', poster=logg)
    return logg


if __name__ == '__main__':
    planfil = Path(sys.argv[1]); ut = Path(sys.argv[2]) if len(sys.argv) > 2 else planfil
    plan = json.loads(planfil.read_text(encoding='utf-8'))
    for x in lagg_handsyn(plan): print(x)
    ut.write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')
