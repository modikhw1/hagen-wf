"""0012: minsta avstånd från varje möbelkopia (fotavtryckets hörn) till väggarnas insida längs väggnormalen, och kameror inne i objekt. Från scen/."""
import json, math, sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
for v in sys.argv[1:]:
    p = json.load(open(f'3d/kontrakt/ut/{v}/narvaro/plan.json', encoding='utf8')); N = len(p['kallrutor'])
    V = [o for o in p['objekt'] if o['id'].startswith('vagg')]
    M = [o for o in p['objekt'] if not o['id'].startswith(('vagg', 'golv')) and ':' not in o['id']]
    mitt = np.mean([o['pos_m'][:2] for o in M], axis=0); minst = []
    for o in M:
        y = (o.get('rotation_rad') or [0, 0, 0])[2]; R = np.array([[math.cos(y), -math.sin(y)], [math.sin(y), math.cos(y)]])
        H = [np.asarray(o['pos_m'][:2]) + R @ np.array([sx * o['matt_m'][0] / 2, sy * o['matt_m'][1] / 2]) for sx in (-1, 1) for sy in (-1, 1)]
        for w in V:
            yw = (w.get('rotation_rad') or [0, 0, 0])[2]; t = 0 if w['matt_m'][0] <= w['matt_m'][1] else 1
            n = np.array([math.cos(yw), math.sin(yw)]) if t == 0 else np.array([-math.sin(yw), math.cos(yw)])
            if n @ (mitt - np.asarray(w['pos_m'][:2])) < 0: n = -n
            inre = np.asarray(w['pos_m'][:2]) + n * w['matt_m'][t] / 2
            minst.append((round(float(min(n @ (h - inre) for h in H)), 3), o['id'], o.get('synlig_ut'), w['id']))
    kam = 0
    for u, k in enumerate(p['renderkamera']['nycklar']):
        C = np.asarray(k['matris'], float)[:3, 3]
        for o in p['objekt']:
            s = o.get('synlig_ut') or [0, N]
            if o['id'].startswith(('vagg', 'golv')) or not s[0] <= u < s[1]: continue
            y = (o.get('rotation_rad') or [0, 0, 0])[2]; c, si = math.cos(y), math.sin(y)
            lok = np.array([[c, si], [-si, c]]) @ (C[:2] - np.asarray(o['pos_m'][:2]))
            if abs(lok[0]) <= o['matt_m'][0] / 2 and abs(lok[1]) <= o['matt_m'][1] / 2 and abs(C[2] - o['pos_m'][2]) <= o['matt_m'][2] / 2: kam += 1
    minst.sort()
    print(v, '| minsta väggmarginal (m):', minst[:3], '| utanför (<0):', sum(m[0] < 0 for m in minst), '| kamerarutor i objekt:', kam)
