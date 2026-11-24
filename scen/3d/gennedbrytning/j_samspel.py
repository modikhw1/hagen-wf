"""0024 punkt 3: samspelet kropp och disk, per ruta, och tre mått på rummet ur kroppen mot dagens plan.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/j_samspel.py <samspel/variant.json> [...]
Indata ur j_samspel_blender.py. Allt räknas i diskens egen ram: x längs disken, y djup (positiv mot hennes sida, staplatsen), z upp.
Bakkanten (hennes sida) ligger vid y = +djup/2, framkanten (kundens sida) vid y = -djup/2, ovankanten vid z = höjd.
Per ruta:
  hoft_bakom_bakkant_m: höftmittens avstånd bakom bakkanten (positivt = på hennes sida)
  hand: fingertoppen (r_middle3, svans) i diskens ram, och läget: 'i_traget' (inom diskens yta och under ovankanten),
        'over_disken' (inom ytan, över ovankanten), 'framfor_disken' (förbi framkanten), 'bakom_disken'
Tre mått på rummet ur kroppen:
  tragdjup_m: ovankanten minus handens lägsta punkt medan handen är i tråget (hur djupt hon når ned)
  avstand_till_disk_m: höftens median bakom bakkanten (hur nära disken hon står)
  djup_naas_m: hur långt in över disken fingertoppen når, mätt från bakkanten (en nedre gräns för diskens djup om hon når framkanten)
--fotter-last: antagandet "hon står still" (antagen). Varje ruta flyttas (bara förskjutning) så att fotledernas mitt ligger på sin median
  i golvplanet och på 0,065 m över golvet (planens fotled_over_golv_m). Kroppens form ändras inte.
"""
import json, sys
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent


def ram(disk):
    c = np.array(disk['mitt']); th = disk['rotation_z']; L, D, Hh = disk['matt']
    R = np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]])
    golv = min(h[2] for h in disk['horn'])
    def lok(p): return R.T @ (np.array(p) - np.array([c[0], c[1], golv]))
    return lok, L, D, Hh


def fotter_last(d):
    fm = lambda le: (np.array(le['l_foot']['huvud']) + np.array(le['r_foot']['huvud'])) / 2
    F = np.array([fm(r['leder']) for r in d['rutor']]); mal = np.r_[np.median(F[:, :2], 0), 0.065]
    for r, f in zip(d['rutor'], F):
        dv = mal - f
        for le in r['leder'].values(): le['huvud'] = list(np.array(le['huvud']) + dv); le['svans'] = list(np.array(le['svans']) + dv)
    return d


def samspel(f, last=False):
    d = json.loads(Path(f).read_text())
    if last: d = fotter_last(d)
    lok, L, D, Hh = ram(d['disk']); bak, fram = D / 2, -D / 2
    rader = []
    for r in d['rutor']:
        le = r['leder']
        hoft = lok((np.array(le['l_upleg']['huvud']) + np.array(le['r_upleg']['huvud'])) / 2)
        tf = lok(le['r_middle3']['svans']); hl = lok(le['r_wrist']['huvud'])
        inom_x = abs(tf[0]) <= L / 2
        if tf[1] > bak or not inom_x: lage = 'bakom_disken'
        elif tf[1] < fram: lage = 'framfor_disken'
        elif tf[2] < Hh: lage = 'i_traget'
        else: lage = 'over_disken'
        rader.append(dict(ruta=r['ruta'], hoft_bakom_bakkant_m=round(float(hoft[1] - bak), 3), hoft_hojd_m=round(float(hoft[2]), 3),
                          fingertopp_lok=[round(float(x), 3) for x in tf], handled_lok=[round(float(x), 3) for x in hl], hand=lage))
    i_trag = [x for x in rader if x['hand'] == 'i_traget']; over = [x for x in rader if x['hand'] in ('over_disken', 'framfor_disken', 'i_traget')]
    matt = dict(tragdjup_m=round(Hh - min(x['fingertopp_lok'][2] for x in i_trag), 3) if i_trag else None,
                avstand_till_disk_m=round(float(np.median([x['hoft_bakom_bakkant_m'] for x in rader])), 3),
                djup_naas_m=round(float(bak - min(x['fingertopp_lok'][1] for x in over)), 3) if over else None)
    seg = []
    for x in rader:
        if seg and seg[-1]['hand'] == x['hand']: seg[-1]['rutor'][1] = x['ruta']
        else: seg.append(dict(hand=x['hand'], rutor=[x['ruta'], x['ruta']]))
    return dict(kalla=f, fotter_last=last, plan_disk=dict(langd_m=L, djup_m=D, hojd_m=Hh), matt=matt, handlagen=seg, rutor=rader)


def main():
    last = '--fotter-last' in sys.argv
    for f in [x for x in sys.argv[1:] if not x.startswith('--')]:
        s = samspel(f, last); ut = Path(f).with_name(Path(f).stem + ('_samspel_last.json' if last else '_samspel.json'))
        ut.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding='utf-8')
        print(Path(f).stem, 'plan', s['plan_disk'], 'mått', s['matt'])
        print('   handlägen', [(x['hand'], x['rutor']) for x in s['handlagen']])
        h = [x['hoft_bakom_bakkant_m'] for x in s['rutor']]; print('   höft bakom bakkant min/median/max', min(h), np.median(h), max(h))


if __name__ == '__main__': main()
