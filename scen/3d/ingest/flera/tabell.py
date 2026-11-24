"""Skriver en rad per tagning ur status.json + tagningar.json. Kör: scen/.venv/Scripts/python.exe scen/3d/ingest/flera/tabell.py <utmapp>"""
import json, sys
U = sys.argv[1].rstrip('/') + '/'
s = json.load(open(U + 'status.json')); p = json.load(open(U + 'tagningar.json'))
for t in p['tagningar']:
    k = t['id']; v = s.get(k)
    if not v: print(k, t['start'], t['slut'], 'ej körd'); continue
    print(k, t['start'], t['slut'], t['gransscore'], v['status'], v.get('orsak') or '', 'pers', v.get('personer', v.get('personer_spårade')), v.get('person_ruta'), 'cam', v.get('kamera_registrerade'), '/', v.get('kamera_av'), 'stat', v.get('kamera_statisk'),
          'golv', (v.get('golv_kalla') or '')[:12], 'ben', {a: (b['synliga'], b['skymda']) for a, b in v.get('ben', {}).items()}, 'rum', v.get('rum'), 'jobb', v.get('kropp_jobb'), 'kr_s', v.get('kropp_s'), 'vagg', v.get('vagg_s'),
          'otf', {a: b['otillforlitliga'] for a, b in v.get('ben', {}).items()})
