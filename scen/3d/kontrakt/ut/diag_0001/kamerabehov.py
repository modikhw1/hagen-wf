"""Uppdrag 0001, del B steg 3: omvänd fråga. Om disk_C / vågen står där planen har dem, hur långt längs sin blickriktning
måste tagningens kamera flyttas för att boxens kanter ska stämma? (pitch, yaw, lins, höjd hålls som lösta.)
Körs: scen/.venv/Scripts/python.exe -B -I kamerabehov.py [variant=fler]   Skriver kamerabehov_<variant>.json."""
import copy, json, os, sys
import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
UT = os.path.dirname(HERE); KONTRAKT = os.path.dirname(UT)
sys.path.insert(0, KONTRAKT); sys.path.insert(0, os.path.dirname(KONTRAKT))
import boxpassning as bp, foremallyft as fl  # noqa: E402

variant = sys.argv[1] if len(sys.argv) > 1 else 'fler'
plan = json.load(open(f'{UT}/b-tilltal-ravara_n06-{variant}/narvaro/plan.json', encoding='utf8'))
pl = plan['plats'][0]; obj = {o['id']: o for o in plan['objekt']}
mobler = pl['deklarerat']['mobler']; foremal = pl['deklarerat']['foremal']
person = next(a for a in pl.get('uppmatta_ankare', []) + pl.get('ankare', []) if a['id'] == 'staplats_C')['pos_m']


def med_skift(key, f, s):
    k = copy.deepcopy(key); M = np.asarray(k['matris'], float); M[:2, 3] += s * f; k['matris'] = M.tolist(); return k


def behov(objekt, bild):
    box, key, ruta = bp.bilddata(plan, bild); mal = bp.anvanda_kanter(plan, box)
    M = np.asarray(key['matris'], float); f = (M[:3, :3] @ [0, 0, -1.])[:2]; f /= np.linalg.norm(f)

    def rest(p):
        try:
            pr = bp.projicerade_kanter(plan, objekt, objekt['pos_m'][:2], med_skift(key, f, p[0]))
            return np.array([pr[k] - v for k, v in mal.items()])
        except ValueError:
            return np.full(len(mal), 1000.)
    kand = []
    for s0 in np.arange(-3, 3.01, .5):                      # rastrera: kantresidualen är inte konvex i skiftet
        try: kand.append((float(np.sum(np.square(rest([s0])))), s0))
        except Exception: pass
    s0 = min(kand)[1]
    fit = least_squares(rest, [s0], bounds=([-4.], [4.]), loss='soft_l1', f_scale=20.)
    s = float(fit.x[0]); r = rest([s]); r0 = rest([0.])
    return dict(kanter=list(mal), skift_langs_blick_m=round(s, 3), kamera_xy_lost=[round(float(v), 3) for v in M[:2, 3]],
                kamera_xy_behovd=[round(float(v), 3) for v in (M[:2, 3] + s * f)],
                rms_px_fore=round(float(np.sqrt(np.mean(r0 ** 2))), 1), rms_px_efter=round(float(np.sqrt(np.mean(r ** 2))), 1),
                kamera_till_person_lost_m=round(float((np.asarray(person[:2]) - M[:2, 3]) @ f), 2),
                kamera_till_person_behovd_m=round(float((np.asarray(person[:2]) - M[:2, 3]) @ f - s), 2))


ut = {}
for namn, o, bilder in (('disk_C', obj['disk_C'], mobler['disk_C'].get('bilder') or []),
                         ('vag', None, foremal['vag'].get('bilder') or [])):
    if o is None:
        v = foremal['vag']; o = dict(obj[v['objekt_id']]); st = obj[v['pa']]
        o['pos_m'] = [o['pos_m'][0], o['pos_m'][1], st['pos_m'][2] + st['matt_m'][2] / 2. + o['matt_m'][2] / 2.]
    ut[namn] = {}
    for b in bilder:
        try: ut[namn][b['tagning']] = behov(o, b)
        except ValueError as ex: ut[namn][b['tagning']] = dict(orsak=str(ex))
# disk_A: bara den gamla enskilda rutan (detektionen gav tom lista)
a = mobler['disk_A'].get('bild')
if a:
    try: ut['disk_A_gamla_bilden'] = {a['tagning']: behov(obj['disk_A'], a)}
    except ValueError as ex: ut['disk_A_gamla_bilden'] = {a['tagning']: dict(orsak=str(ex))}
json.dump(ut, open(f'{HERE}/kamerabehov_{variant}.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('person staplats_C', person)
for n, d in ut.items():
    print('==', n, 'pos', obj[n]['pos_m'] if n in obj else '')
    for t, r in d.items():
        print(f'  {t:4}', r)
