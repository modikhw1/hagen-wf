"""Uppdrag 0003: summerar Geminis svar (arm A/B): spridning mellan körningarna och avstånd till dagens lösta läge. Skriver summering.md/json."""
import json, os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); D3 = os.path.dirname(os.path.dirname(HERE))
PLAN = json.load(open(f'{D3}/kontrakt/ut/b-tilltal-ravara_n06-fler/narvaro/plan.json', encoding='utf8'))
OBJ = {}
for o in PLAN['objekt']: OBJ.setdefault(o['id'], o)
PL = PLAN['plats'][0]; ANK = {a['id']: np.array(a['pos_m'][:2], float) for a in PL['uppmatta_ankare']}
MAL = {}                                                     # dagens lösta läge per element (x, y)
for s in range(1, 12):
    disk = OBJ['disk_A'] if s <= 4 else OBJ['disk_C']
    MAL[f'S{s}'] = dict(disk=np.array([disk['pos_m'][0], disk['pos_m'][1] - disk['matt_m'][1] / 2.]), vag=np.array(OBJ['disk_C:pa:vag']['pos_m'][:2]),
                        fot=ANK['staplats_' + ({1: 'A', 2: 'A', 3: 'B', 4: 'B'}.get(s, 'C'))])
ut = {}; SUFF = sys.argv[1] if len(sys.argv) > 1 else ''


def xy(d):
    try: return np.array([float(d['x']), float(d['y'])])
    except (TypeError, KeyError, ValueError): return None


def spr(punkter):
    p = [q for q in punkter if q is not None]
    if len(p) < 2: return None, None, len(p)
    med = np.median(np.array(p), axis=0); return float(np.sqrt(np.mean([np.sum((q - med) ** 2) for q in p]))), med, len(p)


for arm in ('A', 'B'):
    f = f'{HERE}/svar/arm{arm}{SUFF}.json'
    if not os.path.exists(f): continue
    R = json.load(open(f, encoding='utf8')); per = {}
    for r in R:
        if r.get('svar'): per.setdefault(r['tagning'], []).append(r['svar'])
    rader = []; kost = sum(r.get('kostnad', 0) for r in R)
    for s in [f'S{i}' for i in range(1, 12)]:
        sv = per.get(s, []); n = len(sv); post = dict(tagning=s, svar_ok=n, antal=len([r for r in R if r['tagning'] == s]))
        for nyckel, falt, mal in (('disk', 'counter_front_edge_center', MAL[s]['disk']), ('vag', 'scale' if arm == 'A' else 'scale_base', MAL[s]['vag']),
                                  ('fot', 'person_feet', MAL[s]['fot'])):
            if arm == 'A' and nyckel == 'fot': continue
            sp, med, k = spr([xy(x.get(falt)) for x in sv])
            post[nyckel] = dict(antal=k, spridning_m=None if sp is None else round(sp, 2), median=None if med is None else [round(float(v), 2) for v in med],
                                avstand_till_losta_m=None if med is None else round(float(np.hypot(*(med - mal))), 2))
        if arm == 'A':
            post['pil_ratt'] = round(sum(1 for x in sv if str(x.get('camera_arrow')) == s[1:]) / max(n, 1), 2)
            post['riktning_stammer'] = round(sum(1 for x in sv if x.get('arrow_direction_matches_view') is True) / max(n, 1), 2)
        else:
            post['rutnat_ok_andel'] = round(sum(1 for x in sv if x.get('grid_aligned') in ('yes', 'aligned')) / max(n, 1), 2)
            post['rutnat_svar'] = {k: sum(1 for x in sv if x.get('grid_aligned') == k) for k in ('yes', 'shifted', 'tilted', 'unclear')}
            post['rutnat_problem'] = [x.get('grid_problem') for x in sv if x.get('grid_problem')][:3]
        rader.append(post)
    ut[arm] = dict(kostnad_usd=round(kost, 4), anrop=len(R), tagningar=rader)
    for nyckel in ('disk', 'vag', 'fot'):
        sp = [r[nyckel]['spridning_m'] for r in rader if nyckel in r and r[nyckel]['spridning_m'] is not None]
        av = [r[nyckel]['avstand_till_losta_m'] for r in rader if nyckel in r and r[nyckel]['avstand_till_losta_m'] is not None]
        if sp: ut[arm][f'{nyckel}_median_spridning_m'] = round(float(np.median(sp)), 2); ut[arm][f'{nyckel}_median_avstand_m'] = round(float(np.median(av)), 2)
json.dump(ut, open(f'{HERE}/summering{SUFF}.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
with open(f'{HERE}/summering{SUFF}.md', 'w', encoding='utf8') as f:
    for arm, d in ut.items():
        f.write(f'## Arm {arm}: {d["anrop"]} anrop, {d["kostnad_usd"]} USD\n')
        f.write('Median över tagningar: ' + ', '.join(f'{k}={v}' for k, v in d.items() if k.endswith('_m')) + '\n\n')
        f.write('| tagn | ok/antal | ' + ('pil rätt | riktning | ' if arm == 'A' else 'rutnät ok | ') + 'bord: spridn. / avst. m | våg: spridn. / avst. m | ' + ('' if arm == 'A' else 'fötter: spridn. / avst. m |') + '\n|---|---|' + '---|' * (7 if arm == 'B' else 5) + '\n')
        for r in d['tagningar']:
            f.write(f"| {r['tagning']} | {r['svar_ok']}/{r['antal']} | " + (f"{r['pil_ratt']} | {r['riktning_stammer']} | " if arm == 'A' else f"{r['rutnat_ok_andel']} {r['rutnat_svar']} | ")
                    + f"{r['disk']['spridning_m']} / {r['disk']['avstand_till_losta_m']} | {r['vag']['spridning_m']} / {r['vag']['avstand_till_losta_m']} |"
                    + ('' if arm == 'A' else f" {r['fot']['spridning_m']} / {r['fot']['avstand_till_losta_m']} |") + '\n')
        f.write('\n')
print(open(f'{HERE}/summering{SUFF}.md', encoding='utf8').read())
