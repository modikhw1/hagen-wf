"""Kontrollinkoppling och läsbara fel för inaktuella källmanifest."""
from steg10_filer import andra
from steg10_koppla import ersatt


def kontroller(s):
    s = ersatt(s, "    if isinstance(v, dict):\n        for k in s.get('required', []):", "    if isinstance(v, dict):\n        if 'minProperties' in s and len(v) < s['minProperties']: fel.append(f'{sokv}: för få egenskaper')\n        for k in s.get('required', []):")
    s = ersatt(s, "     minLength, minimum, maximum, pattern", "     minLength, minProperties, minimum, maximum, pattern")
    marker = "    n = K['tidsbas']['antal_rutor']; fps = K['tidsbas']['fps_taljare'] / K['tidsbas']['fps_namnare']"
    s = ersatt(s, marker, '''    events = sem.get('handelser', [])
    event_ids = {e['id'] for e in events}
    if len(event_ids) != len(events): fel_lista.append('kalla: dubblerade händelse-id')
    for event in events:
        label = 'händelse ' + event['id']
        id_ok(event['scen'], scener, label + '.scen')
        id_ok(event['vem'], pers, label + '.vem'); id_ok(event['till_vem'], pers, label + '.till_vem')
        id_ok(event['prop'], props, label + '.prop')
        scene = next((s for s in sem['scener'] if s['id'] == event['scen']), None)
        if event['start_s'] > event['slut_s']: fel_lista.append(label + ': omvänt tidsintervall')
        if scene and not scene['start_s'] - 1e-4 <= event['start_s'] <= event['slut_s'] <= scene['slut_s'] + 1e-4:
            fel_lista.append(label + ': tid utanför scenen')
        if event['ursprung']['typ'] == 'modellbedomd' and not event['ursprung']['modell']:
            fel_lista.append(label + ': modell saknas för modellbedömning')
    for proof in mat.get('handelsebevis', []): id_ok(proof['handelse'], event_ids, 'matning.handelsebevis.handelse')
''' + marker)
    s = ersatt(s, "        if e['op'] == 'trimma_scen' and 'start_s' not in e and 'slut_s' not in e:", "        if e['op'] == 'trimma_scen' and 'start_s' not in e and 'slut_s' not in e and not e.get('tid'):")
    marker = "        if e['op'] == 'renderkamera' and e.get('mal')"
    pos = s.index(marker)
    s = s[:pos] + '''        if 'tid' in e:
            from handelser import los_edit
            try: los_edit(e, events, K['tidsbas']['langd_s'])
            except ValueError as ex: fel_lista.append(v + ': ' + str(ex))
''' + s[pos:]
    s = ersatt(s, 'def hashar(K, mapp):', 'def hashar(K, mapp, kallfil=None):\n    stale = []')
    s = ersatt(s, "                    if h != o['sha256']: fel_lista.append(f'{v}: sha256 stämmer inte för {o[\"sokvag\"]}')", "                    if h != o['sha256']:\n                        fel_lista.append(f'{v}: sha256 stämmer inte för {o[\"sokvag\"]}'); stale.append(o['sokvag'])")
    s = ersatt(s, "    return pek.n\n", '''    if stale:
        source = Path(kallfil) if kallfil else Path(mapp) / 'kalla.json'
        if any(x['sokvag'] in stale for x in K['matning'].get('handelsekallor', [])):
            fel_lista.append('Händelseunderlaget har ändrats. Mät om med scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_handelser.py <aktuell kalla_prop.json> <semantik.json> <ny kalla_handelser.json>; uppdatera regins revision. Hasha inte om gamla händelser.')
        else:
            fel_lista.append('Ingest har ändrat mätfiler efter källmanifestet. Granska ändringen och uppdatera uttryckligen: scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_omhasha.py "' + str(source.resolve()) + '" --uppdatera')
    return pek.n
''')
    return s


def gemensamt(s):
    # Anropskontraktet lämnas oförändrat; exakt källfil förs från kompilatorn.
    s = ersatt(s, 'def kontrollera(k, r, mapp):', 'def kontrollera(k, r, mapp, kallfil=None):')
    return ersatt(s, 'mod.hashar(k, Path(mapp))', 'mod.hashar(k, Path(mapp), kallfil)')


andra('scen/3d/kontrakt/kontrollera.py', kontroller)
andra('scen/3d/kontrakt/gemensamt.py', gemensamt)
andra('scen/3d/kontrakt/kompilera.py', lambda s: ersatt(s, 'kontrollera(K, R, kallfil.parent)', 'kontrollera(K, R, kallfil.parent, kallfil)'))
andra('scen/3d/kontrakt/kalla_handelser.py', lambda s: ersatt(s, "    k['semantik']['handelser'] = events", "    k['matning']['handelsebevis'] = [dict(handelse=e['id'], **e.pop('bevis')) for e in events]\n    k['semantik']['handelser'] = events"))
