"""Uppdrag 0012: b-tilltal n06-grupp mot n06-matt. Per tagning S6–S11: diskens och vågens låda projicerad i slutkameran (den kopia som syns i
tagningens mittruta) mot segmenterarens ruta i nyckelbilden (n06-grupps rutor), alla fyra kanter i promille (x mot bredd, y mot höjd; projicerat minus ruta).
Kanterna mäts på den del av lådan som ligger i bild (boxpassning.projicerade_kanter efter 0012), som rutan. Kontrollerar också möbler mot väggarna och kameror i möbler.
Körs (från scen/): .venv/Scripts/python.exe -B 3d/kontrakt/ut/fore_sidled_0012/jamfor_grupp.py [klipp-variant ...]"""
import json, math, os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); UT = os.path.dirname(HERE); KON = os.path.dirname(UT)
sys.path.insert(0, KON); sys.path.insert(1, os.path.join(os.path.dirname(KON), 'ingest'))
import boxpassning as bp  # noqa: E402
from foremallyft import _scen  # noqa: E402

VARIANTER = sys.argv[1:] or ['b-tilltal-ravara_n06-matt', 'b-tilltal-ravara_n06-grupp']
REF = json.load(open(f'{HERE}/deklaration_n06_grupp.json', encoding='utf8'))
REFRUTOR = {'disk_C': {b['tagning']: b['box_2d'] for b in REF['platser']['disk_C']['bilder']},
            'vag': {b['tagning']: b['box_2d'] for b in REF['foremal']['vag']['bilder']}}
ID = {'disk_C': 'disk_C', 'vag': 'disk_C:pa:vag'}


def synlig(p, oid, u):
    N = len(p['kallrutor'])
    return next((o for o in p['objekt'] if o['id'] == oid and o.get('synlig_ut', [0, N])[0] <= u < o.get('synlig_ut', [0, N])[1]), None)


def i_lada(o, P):
    yaw = float((o.get('rotation_rad') or [0, 0, 0])[2]); c, s = math.cos(yaw), math.sin(yaw)
    lok = np.array([[c, s], [-s, c]]) @ (np.asarray(P[:2]) - np.asarray(o['pos_m'][:2]))
    m = np.asarray(o['matt_m']) / 2.
    return abs(lok[0]) <= m[0] and abs(lok[1]) <= m[1] and abs(P[2] - o['pos_m'][2]) <= m[2]


ut = {}
for v in VARIANTER:
    p = json.load(open(f'{UT}/{v}/narvaro/plan.json', encoding='utf8')); W, H = float(p['utdata']['bredd']), float(p['utdata']['hojd']); res = {}
    for t in ('S6', 'S7', 'S8', 'S9', 'S10', 'S11'):
        sc = _scen(p, t); u = (sc['ut'][0] + sc['ut'][1] - 1) // 2; key = p['renderkamera']['nycklar'][u]; rad = {}
        for el in ('disk_C', 'vag'):
            o = synlig(p, ID[el], u); box = REFRUTOR[el].get(t)
            if o is None: rad[el] = 'syns inte i planen'; continue
            if box is None: rad[el] = dict(ingen_referensruta=True, pos=[round(x, 2) for x in o['pos_m'][:2]]); continue
            try: k = bp.projicerade_kanter(p, o, o['pos_m'][:2], key)
            except ValueError as ex: rad[el] = str(ex); continue
            c = lambda v, s: min(1000., max(0., v / s * 1000.))          # som rutan: kanten klipps mot bilden
            rad[el] = dict(topp=round(c(k['topp'], H) - box[0]), vanster=round(c(k['vanster'], W) - box[1]),
                           botten=round(c(k['botten'], H) - box[2]), hoger=round(c(k['hoger'], W) - box[3]),
                           ruta=box, pos=[round(x, 2) for x in o['pos_m'][:2]], matt=[round(x, 2) for x in o['matt_m']])
        res[t] = rad
    vaggar = {o['id']: o for o in p['objekt'] if o['id'] in ('vagg_bak', 'vagg_sida')}
    mob = [o for o in p['objekt'] if o['id'].split(':')[0] in ('disk_A', 'disk_C') and ':pa:' not in o['id']]
    utanfor = []
    for o in mob:
        for vid, vg in vaggar.items():
            axel = 0 if vg['matt_m'][0] <= vg['matt_m'][1] else 1; inre_sida = np.sign(np.mean([q['pos_m'][axel] for q in mob]) - vg['pos_m'][axel])
            kant = o['pos_m'][axel] + inre_sida * -1 * o['matt_m'][axel] / 2.; yta = vg['pos_m'][axel] + inre_sida * vg['matt_m'][axel] / 2.
            if (kant - yta) * inre_sida < -1e-6: utanfor.append(dict(mobel=o['id'], synlig_ut=o.get('synlig_ut'), vagg=vid, med_m=round(float(abs(kant - yta)), 3)))
    kamera_i = []
    for u, key in enumerate(p['renderkamera']['nycklar']):
        C = np.asarray(key['matris'], float)[:3, 3]
        for o in p['objekt']:
            if o['id'].startswith(('vagg', 'golv')) or not (o.get('synlig_ut', [0, 10 ** 9])[0] <= u < o.get('synlig_ut', [0, 10 ** 9])[1]): continue
            if i_lada(o, C): kamera_i.append((u, o['id']))
    ml = {r['mobel']: r for r in p['kvalitet'].get('mobel_lyft', [])}.get('disk_C', {})
    fl = {r['foremal']: r for r in p['kvalitet'].get('foremal_lyft', [])}.get('vag', {})
    ut[v] = dict(per_tagning=res, mobel_utanfor_vagg=utanfor, kamera_i_objekt=kamera_i[:20], antal_kamera_i_objekt=len(kamera_i),
                 vaggar={k: dict(pos=[round(x, 2) for x in w['pos_m'][:2]], matt=[round(x, 2) for x in w['matt_m'][:2]]) for k, w in vaggar.items()},
                 disk_C_grupper=[dict(grupp=g['grupp'], pos=[round(x, 2) for x in g['pos_m'][:2]], kvalitet=g['kvalitet'], kanter=g['kanter_per_koordinat'],
                                      synlig_ut=g['synlig_ut'], bilder=g['bilder']) for g in ml.get('grupper', [])] or dict(pos=ml.get('slutlig_pos_m')),
                 vag_bredd=fl.get('bredd'), vag_kopior=[dict(synlig_ut=k['synlig_ut'], bilder=k['bilder'], kallor=k['kallor'], pos=[round(x, 2) for x in k['efter_pos_m']])
                                                       for k in fl.get('kopior', [])])
json.dump(ut, open(f'{HERE}/jamfor_grupp.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1, default=float)
for v, r in ut.items():
    print('==', v)
    for t, rad in r['per_tagning'].items(): print(' ', t, json.dumps({k: ({q: x[q] for q in ('topp', 'vanster', 'botten', 'hoger')} if isinstance(x, dict) and 'topp' in x else x) for k, x in rad.items()}, ensure_ascii=False))
    print('  utanför vägg:', r['mobel_utanfor_vagg'], '| kamera i objekt:', r['antal_kamera_i_objekt'], r['kamera_i_objekt'][:5])
    print('  disk_C:', json.dumps(r['disk_C_grupper'], ensure_ascii=False)); print('  våg:', json.dumps(r['vag_kopior'], ensure_ascii=False), json.dumps(r['vag_bredd'], ensure_ascii=False, default=float)[:300])
