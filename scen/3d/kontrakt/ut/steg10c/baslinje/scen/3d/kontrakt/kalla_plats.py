"""Delen av kalla.json som beskriver platsen, byggd ur plats.json (ingest/plats.py). Delas av kalla_bygg.py och kalla_flera.py.

plats.json läggs som hashlåst pekare i matning.platser[].fil. Allt annat här är en kopia av det som redan står i plats.json,
uppdelat enligt kontraktets två lager: betydelse i semantik.platser, siffror i matning.platser.
"""
import hashlib
from pathlib import Path
from gemensamt import ladda


def plats_delar(platsfil, scener, pek_fil, personer_i_scen):
    """platsfil: sökväg till plats.json.
    scener: lista (scen_id, kamera_id, tagning_id) i klippets ordning.
    pek_fil: funktion(Path, roll) -> filref-dict (sökväg relativ kalla, sha256 ...).
    personer_i_scen: dict scen_id -> lista person-id som kalla anger för scenen.
    Returnerar (semantik_platser, matning_platser, per_scen, props) där per_scen[scen_id] = (plats_id, bindningar)."""
    platsfil = Path(platsfil); P = ladda(platsfil); pid = P['id']
    # Semantiska platstyper (butik_eller_disk, ...) ryms inte i schemats enum inomhus/utomhus/okand; den exakta typen står i beskrivningen.
    inne = ('restaurang_matsal', 'bar', 'butik_eller_disk', 'cafe', 'kok', 'hem', 'kontor')
    styp = P.get('typ', 'okand'); typ = styp if styp in ('inomhus', 'utomhus') else 'inomhus' if styp in inne else 'utomhus' if styp == 'utomhus' else 'okand'
    beskr = P['beskrivning'] + (f' Platstyp enligt semantiken: {styp} (modellbedömd).' if P.get('semantik') else '')
    sem = dict(id=pid, typ=typ, beskrivning=beskr,
               ankare=[dict(id=a['id'], typ=a['typ'], etikett=a['etikett']) for a in P['ankare']],
               objekt=[dict(id=o['id'], etikett=o['etikett']) for o in P['objekt']])
    reg = {t['id']: t for t in P['tagningar']}; saknas = [t for _, _, t in scener if t not in reg]
    if saknas: raise ValueError(f'plats.json saknar tagningarna {saknas}.')
    mat = dict(id=pid, fil=pek_fil(platsfil, 'Platsen: golv, sammanslagna objekt, ankare, tagningarnas transform (ingest/plats.py).'),
               koordinater=dict(enhet=P['ramar']['enhet'], upp=P['ramar']['upp'], origo=P['ramar']['origo'], axlar=P['ramar']['axlar']),
               golv=dict(hojd_m=P['golv']['hojd_m'], status=P['golv']['status'], kalla=P['golv']['kalla']),
               ankare=[dict(id=a['id'], pos_m=a['pos_m'], riktning_rad=a['riktning_rad'], hojd_m=a.get('hojd_m'), status=a['status'],
                            osakerhet_m=a.get('osakerhet_m'), metod=a['metod']) for a in P['ankare']],
               registreringar=[dict(scen=sid, kamera=kam, tagning=tg, till_plats=reg[tg]['till_plats'], metod=reg[tg]['kvalitet']['metod'],
                                    status=reg[tg]['kvalitet']['status'], skala_status=reg[tg]['kvalitet']['skala_status'],
                                    residual_m=reg[tg]['kvalitet']['residual_m'], kommentar=reg[tg]['kvalitet']['kommentar']) for sid, kam, tg in scener])
    per_scen = {}
    if P.get('rumsmall'):
        r=P['rumsmall']; sem['rumsmall_id']=r['id']
        mat['rumsmall']=dict(id=r['id'],sha256=r['sha256'],rms_m=r['passning']['rms_m'],status='mall')
    for sid, _, tg in scener:
        bind = [dict(person=b['roll'], ankare=b['ankare'], hallning=b['hallning'], status=b['status'])
                for b in P['bindningar'] if b['tagning'] == tg and b['roll'] in personer_i_scen.get(sid, [])]
        per_scen[sid] = (pid, sorted(bind, key=lambda b: b['person']))
    props = [dict(id=o['id'], typ=o['etikett'].replace(' ', '_'), etikett=o['etikett'], agare=None, stod=None, faste=None, rum_ref=o['id'],
                  kalla='plats.json', plats_id=pid) for o in P['objekt']]
    return sem, mat, per_scen, props
