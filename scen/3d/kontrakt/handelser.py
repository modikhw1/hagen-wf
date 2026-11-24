"""Händelseankare på källklockan och deras förekomster på utdataklockan.

En tidpunkt har start_s == slut_s. Ett spann kräver att CM väljer start
eller slut uttryckligen; ett osäkert spann görs aldrig till en exakt tid.
"""
import copy


def tidpunkt(ref, events):
    event = next((x for x in events if x['id'] == ref['handelse']), None)
    if event is None:
        raise ValueError('Okänd händelse: ' + ref['handelse'])
    kant = ref.get('kant')
    if kant is None and event['start_s'] != event['slut_s']:
        raise ValueError('Händelsen är ett spann; ange kant=start eller slut: ' + event['id'])
    return event['slut_s' if kant == 'slut' else 'start_s'] + ref.get('offset_s', 0)


def los_edit(edit, events, langd):
    """Kopia; numeriska tider och händelseankare får inte ange samma gräns."""
    e = copy.deepcopy(edit)
    if 'tid' not in e:
        return e, None
    resolved = {}
    for key, field in (('fran', 'start_s'), ('till', 'slut_s')):
        if key in e['tid']:
            if field in e:
                raise ValueError('Ange antingen ' + field + ' eller tid.' + key + ', inte båda.')
            resolved[field] = tidpunkt(e['tid'][key], events)
            if not 0 <= resolved[field] <= langd:
                raise ValueError('Händelseankaret ligger utanför klippet: ' + key)
    if resolved.get('start_s', 0) >= resolved.get('slut_s', langd):
        raise ValueError('Händelseintervallet är tomt eller omvänt.')
    if e['op'] in ('trimma_scen', 'skarmtext'):
        e.update(resolved)
    return e, dict(ankare=copy.deepcopy(e['tid']), kalla_s=resolved)


def intervall_ut(a, b, scener, karta, fps):
    """Halvöppna spann; samma källhändelse kan förekomma flera gånger."""
    result = []
    for scene, iv in zip(scener, karta):
        sa, sb = iv['kalla']
        if a == b:
            if not sa <= a < sb:
                continue
            ua = iv['ut'][0] + a - sa
            ub = ua
        else:
            ca, cb = max(a, sa), min(b, sb)
            if ca >= cb:
                continue
            ua, ub = iv['ut'][0] + ca - sa, iv['ut'][0] + cb - sa
        result.append(dict(scen=scene['id'], ut=[ua, ub], ut_s=[ua / fps, ub / fps]))
    return result


def till_plan(events, scener, karta, fps, ruta):
    result = []
    for event in events:
        e = copy.deepcopy(event)
        # En punkt vid scenens slut tillhör den scenen (t.ex. spårslut),
        # även om källrutan sammanfaller med nästa scens start.
        occurrences = intervall_ut(ruta(e['start_s']), ruta(e['slut_s']), scener, karta, fps)
        e['forekomster'] = [x for x in occurrences if next(s for s in scener if s['id'] == x['scen'])['ursprung'] == e['scen']]
        if e['start_s'] == e['slut_s'] and not e['forekomster']:
            for s, iv in zip(scener, karta):
                if s['ursprung'] == e['scen'] and ruta(e['start_s']) == iv['kalla'][1]:
                    u = iv['ut'][1]
                    e['forekomster'].append(dict(scen=s['id'], ut=[u, u], ut_s=[u / fps, u / fps]))
        result.append(e)
    return result
